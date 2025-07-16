// masking-engine.js - Python API 연동 + JavaScript Fallback

class PrivacyGuardEngine {
    constructor() {
        this.threshold = 50;
        this.analysisMode = 'medical';
        this.enabled = false;

        // API 설정
        this.apiEndpoint = 'http://localhost:8000';
        this.usePythonAPI = true;
        this.serverStatus = 'unknown'; // 'connected', 'disconnected', 'unknown'

        // JavaScript Fallback용 패턴들 (기존 코드 유지)
        this.medicalPatterns = {
            name: /[가-힣]{2,4}(?=\s|님|씨|선생님|교수님|$)/g,
            phone: /010-\d{4}-\d{4}/g,
            age: /\d{1,2}세|\d{1,2}살/g,
            hospital: /(서울대병원|삼성서울병원|연세의료원|아산병원|세브란스|고려대병원|[가-힣]+병원|[가-힣]+의료원|[가-힣]+센터)/g,
            disease: /(간암|백혈병|고혈압|당뇨|폐암|위암|대장암|유방암|갑상선암|심근경색|뇌졸중|치매|파킨슨)/g,
            treatment: /(수술|입원|퇴원|처방|투약|치료|진료|검사|진단)/g,
            date: /\d{4}년\s*\d{1,2}월|\d{1,2}월\s*\d{1,2}일|\d{4}-\d{1,2}-\d{1,2}/g,
            doctor: /([가-힣]{2,4})\s*(의사|교수님|선생님|간호사)/g
        };

        this.riskWeights = {
            name: 100, phone: 100, hospital: 65, disease: 52,
            date: 78, doctor: 95, age: 30, treatment: 40
        };

        this.maskPatterns = {
            name: '[PERSON]', phone: '[CONTACT]', hospital: '[HOSPITAL]',
            disease: '[DISEASE]', date: '[DATE]', doctor: '[PERSON]',
            age: '[AGE]', treatment: '[TREATMENT]'
        };

        this.contextualKeywords = {
            '진단': 1.2, '수술': 1.2, '입원': 1.2, '치료': 1.2,
            '암': 1.3, '종양': 1.3, '질환': 1.3, '응급': 1.5, '중환자': 1.5
        };

        // 서버 상태 체크
        this.checkServerStatus();
    }

    // 🔥 새로운 기능: 서버 상태 체크
    async checkServerStatus() {
        try {
            const response = await fetch(`${this.apiEndpoint}/health`, {
                method: 'GET',
                timeout: 3000
            });

            if (response.ok) {
                const data = await response.json();
                this.serverStatus = 'connected';
                console.log('✅ Python 서버 연결됨:', data);
                return true;
            }
        } catch (error) {
            this.serverStatus = 'disconnected';
            console.warn('⚠️ Python 서버 연결 실패, JavaScript 버전 사용:', error.message);
        }
        return false;
    }

    // 🔥 새로운 기능: Python API 호출
    async callPythonAPI(text) {
        try {
            const requestData = {
                text: text,
                threshold: this.threshold,
                mode: this.analysisMode,
                use_contextual_analysis: true
            };

            console.log('🐍 Python API 호출 중...', requestData);

            const response = await fetch(`${this.apiEndpoint}/api/mask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                console.log('✅ Python API 성공:', result.stats);

                // Python 결과를 JavaScript 형식으로 변환
                return {
                    originalText: result.original_text,
                    maskedText: result.masked_text,
                    entities: this.convertPythonEntities(result.masking_log),
                    maskedEntities: result.stats.masked_entities,
                    totalEntities: result.stats.total_entities,
                    maskingLog: result.masking_log,
                    avgRisk: Math.round(result.stats.avg_risk),
                    processingTime: result.stats.processing_time,
                    source: 'python',
                    modelInfo: result.model_info
                };
            } else {
                throw new Error(result.error || 'Python API 처리 실패');
            }

        } catch (error) {
            console.error('❌ Python API 오류:', error);
            throw error;
        }
    }

    // Python 응답을 JavaScript 형식으로 변환
    convertPythonEntities(maskingLog) {
        return maskingLog.map((log, index) => ({
            id: index,
            token: log.token,
            type: log.entity,
            finalRisk: log.risk_weight,
            masked: log.masked_as
        }));
    }

    // 🔥 수정된 메인 처리 함수
    async process(text) {
        console.log('🚀 Privacy Guard 파이프라인 시작');
        console.log(`📊 설정: 임계값=${this.threshold}, 모드=${this.analysisMode}`);

        // 1. Python API 우선 시도
        if (this.usePythonAPI && this.serverStatus !== 'disconnected') {
            try {
                const result = await this.callPythonAPI(text);
                console.log('🐍 Python 모델 사용 완료');
                return result;
            } catch (error) {
                console.warn('⚠️ Python API 실패, JavaScript로 fallback:', error.message);
                this.serverStatus = 'disconnected';
                // JavaScript 버전으로 계속 진행
            }
        }

        // 2. JavaScript Fallback 처리
        console.log('⚡ JavaScript 버전 사용');
        return this.processWithJavaScript(text);
    }

    // 기존 JavaScript 처리 로직 (이름만 변경)
    processWithJavaScript(text) {
        console.log('⚡ JavaScript 파이프라인 시작');

        // 1단계: 개체명 인식
        const entities = this.detectEntities(text);
        console.log(`🔍 1단계 - 감지된 개체: ${entities.length}개`);

        if (entities.length === 0) {
            return {
                originalText: text,
                maskedText: text,
                entities: [],
                maskedEntities: 0,
                totalEntities: 0,
                maskingLog: [],
                avgRisk: 0,
                source: 'javascript'
            };
        }

        // 2단계: Copula 위험도 분석
        const copulaEntities = this.calculateCopulaRisk(entities);
        console.log('📊 2단계 - Copula 위험도 계산 완료');

        // 3단계: 문맥적 위험 분석
        const contextualEntities = this.analyzeContextualRisk(text, copulaEntities);
        console.log('🔄 3단계 - 문맥적 위험 분석 완료');

        // 4단계: 마스킹 실행
        const result = this.executeMasking(text, contextualEntities);
        console.log(`🎭 4단계 - 마스킹 완료: ${result.maskedEntities}/${result.totalEntities}`);

        return {
            ...result,
            source: 'javascript'
        };
    }

    // 기존 JavaScript 메서드들 (동일)
    detectEntities(text) {
        const entities = [];
        let entityId = 0;

        for (const [type, pattern] of Object.entries(this.medicalPatterns)) {
            let match;
            while ((match = pattern.exec(text)) !== null) {
                entities.push({
                    id: entityId++,
                    token: match[0],
                    type: type,
                    start: match.index,
                    end: match.index + match[0].length,
                    baseRisk: this.riskWeights[type] || 0
                });
            }
        }

        return entities;
    }

    calculateCopulaRisk(entities) {
        const combinations = {
            'name+hospital+date': 1.8,
            'name+disease+hospital': 2.0,
            'name+phone': 2.0,
            'hospital+date+disease': 1.3
        };

        const entityTypes = entities.map(e => e.type);
        let combinationMultiplier = 1.0;

        for (const [combo, multiplier] of Object.entries(combinations)) {
            const comboTypes = combo.split('+');
            if (comboTypes.every(type => entityTypes.includes(type))) {
                combinationMultiplier = Math.max(combinationMultiplier, multiplier);
            }
        }

        return entities.map(entity => ({
            ...entity,
            copulaRisk: Math.min(100, entity.baseRisk * combinationMultiplier)
        }));
    }

    analyzeContextualRisk(text, entities) {
        let contextMultiplier = 1.0;

        for (const [keyword, multiplier] of Object.entries(this.contextualKeywords)) {
            if (text.includes(keyword)) {
                contextMultiplier = Math.max(contextMultiplier, multiplier);
            }
        }

        return entities.map(entity => ({
            ...entity,
            finalRisk: Math.min(100, Math.round(entity.copulaRisk * contextMultiplier))
        }));
    }

    executeMasking(text, entities) {
        let maskedText = text;
        let maskedCount = 0;
        const maskingLog = [];

        const sortedEntities = entities
            .filter(e => e.finalRisk >= this.threshold)
            .sort((a, b) => b.finalRisk - a.finalRisk);

        for (let i = sortedEntities.length - 1; i >= 0; i--) {
            const entity = sortedEntities[i];
            const maskPattern = this.maskPatterns[entity.type] || '[MASKED]';

            maskedText = maskedText.substring(0, entity.start) +
                maskPattern +
                maskedText.substring(entity.end);

            maskedCount++;
            maskingLog.push({
                token: entity.token,
                type: entity.type,
                risk: entity.finalRisk,
                masked: maskPattern
            });
        }

        return {
            originalText: text,
            maskedText: maskedText,
            entities: entities,
            maskedEntities: maskedCount,
            totalEntities: entities.length,
            maskingLog: maskingLog,
            avgRisk: entities.length > 0 ?
                Math.round(entities.reduce((sum, e) => sum + e.finalRisk, 0) / entities.length) : 0
        };
    }

    // 🔥 새로운 기능: 서버 상태 정보
    getServerStatus() {
        return {
            status: this.serverStatus,
            endpoint: this.apiEndpoint,
            usePythonAPI: this.usePythonAPI
        };
    }

    // 🔥 새로운 기능: 수동 서버 재연결
    async reconnectServer() {
        console.log('🔄 서버 재연결 시도...');
        const connected = await this.checkServerStatus();
        return connected;
    }

    // 설정 업데이트 (기존과 동일)
    updateSettings(settings) {
        this.threshold = settings.threshold || this.threshold;
        this.analysisMode = settings.mode || this.analysisMode;
        this.enabled = settings.enabled !== undefined ? settings.enabled : this.enabled;

        console.log('⚙️ 설정 업데이트:', {
            threshold: this.threshold,
            mode: this.analysisMode,
            enabled: this.enabled
        });
    }
}

// 전역 인스턴스
window.privacyGuard = new PrivacyGuardEngine();

// 서버 상태 체크 (주기적)
setInterval(() => {
    if (window.privacyGuard.serverStatus === 'disconnected') {
        window.privacyGuard.checkServerStatus();
    }
}, 30000); // 30초마다 체크
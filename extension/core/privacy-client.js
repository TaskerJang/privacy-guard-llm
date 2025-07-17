// extension/core/privacy-client.js
// 개선된 서버 기반 개인정보 보호 클라이언트

class PrivacyClient {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;
        this.connectionAttempts = 0;
        this.maxRetries = 3;

        this.settings = {
            threshold: 50,
            mode: 'medical',
            autoRetry: true,
            timeout: 5000
        };

        // 요청 캐시 (동일한 텍스트 재분석 방지)
        this.cache = new Map();
        this.cacheMaxSize = 100;
        this.cacheTimeout = 300000; // 5분

        this.init();
    }

    async init() {
        console.log('🔗 Privacy Client 초기화 중...');
        await this.checkServerConnection();
        this.startHealthCheck();
        this.setupCacheCleanup();
    }

    /**
     * 서버 연결 상태 확인 (개선된 버전)
     */
    async checkServerConnection() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.settings.timeout);

            const response = await fetch(`${this.apiEndpoint}/health`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                this.isServerConnected = true;
                this.connectionAttempts = 0;

                console.log(`✅ 서버 연결 성공: ${data.status || 'healthy'}`);

                // 서버 정보 저장
                this.serverInfo = data;
                return true;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

        } catch (error) {
            this.isServerConnected = false;
            this.connectionAttempts++;

            if (error.name === 'AbortError') {
                console.warn(`⏱️ 서버 연결 시간 초과 (시도: ${this.connectionAttempts})`);
            } else {
                console.warn(`❌ 서버 연결 실패: ${error.message} (시도: ${this.connectionAttempts})`);
            }

            return false;
        }
    }

    /**
     * 주기적 서버 상태 체크 (개선된 버전)
     */
    startHealthCheck() {
        setInterval(async () => {
            if (!this.isServerConnected && this.connectionAttempts < this.maxRetries) {
                await this.checkServerConnection();
            } else if (this.isServerConnected) {
                // 연결된 상태에서도 주기적 체크
                const isHealthy = await this.quickHealthCheck();
                if (!isHealthy) {
                    this.isServerConnected = false;
                    this.connectionAttempts = 0;
                }
            }
        }, 30000); // 30초마다
    }

    /**
     * 빠른 헬스 체크
     */
    async quickHealthCheck() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const response = await fetch(`${this.apiEndpoint}/health`, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response.ok;

        } catch (error) {
            return false;
        }
    }

    /**
     * 텍스트 마스킹 처리 (메인 API - 개선된 버전)
     */
    async maskText(text, options = {}) {
        if (!text || text.trim().length === 0) {
            return this.createEmptyResult(text);
        }

        const cleanText = text.trim();
        const cacheKey = this.generateCacheKey(cleanText, options);

        // 캐시 확인
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                console.log('📋 캐시된 결과 사용');
                return cached.result;
            } else {
                this.cache.delete(cacheKey);
            }
        }

        const requestData = {
            text: cleanText,
            threshold: options.threshold || this.settings.threshold,
            mode: options.mode || this.settings.mode,
            use_contextual_analysis: true,
            request_id: this.generateRequestId()
        };

        console.log(`🚀 마스킹 요청: ${cleanText.length}자, 모드: ${requestData.mode}`);

        let result;

        try {
            // 서버 연결 확인 및 재시도
            if (!this.isServerConnected) {
                await this.checkServerConnection();
            }

            if (this.isServerConnected) {
                result = await this.serverMaskText(requestData);
                console.log(`✅ 서버 마스킹 완료: ${result.stats.maskedEntities}/${result.stats.totalEntities} 개체`);
            } else {
                throw new Error('서버에 연결할 수 없습니다');
            }

        } catch (error) {
            console.warn('❌ 서버 마스킹 실패, 로컬로 전환:', error.message);
            this.isServerConnected = false;
            result = await this.localMaskText(requestData);
        }

        // 결과 캐싱
        this.setCacheResult(cacheKey, result);

        return result;
    }

    /**
     * 서버 기반 마스킹
     */
    async serverMaskText(requestData) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.settings.timeout);

        try {
            const response = await fetch(`${this.apiEndpoint}/api/mask`, {
                method: 'POST',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Request-ID': requestData.request_id
                },
                body: JSON.stringify(requestData)
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || '서버 처리 실패');
            }

            return this.normalizeResult(result, 'server');

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('서버 응답 시간 초과');
            }
            throw error;
        }
    }

    /**
     * 로컬 마스킹 (개선된 fallback)
     */
    async localMaskText(requestData) {
        const text = requestData.text;
        const startTime = performance.now();

        // 향상된 패턴 정의
        const patterns = [
            // 개인명 (더 정확한 패턴)
            {
                regex: /[가-힣]{2,4}(?=\s*(?:님|씨|환자|의사|선생님|간호사|박사))/g,
                type: 'person',
                risk: 85,
                mask: '[이름]'
            },
            // 연락처 (다양한 형태)
            {
                regex: /(?:010|011|016|017|018|019)[-\s]?\d{3,4}[-\s]?\d{4}/g,
                type: 'phone',
                risk: 95,
                mask: '[연락처]'
            },
            // 주민번호
            {
                regex: /\d{6}[-\s]?[1-4]\d{6}/g,
                type: 'id_number',
                risk: 100,
                mask: '[주민번호]'
            },
            // 의료기관 (확장된 패턴)
            {
                regex: /(서울대병원|서울대학교병원|서울대학교의과대학부속병원|삼성서울병원|아산병원|아산의료원|세브란스|연세의료원|고려대병원|고려대학교의료원|[가-힣]+대학교?병원|[가-힣]+병원|[가-힣]+의료원|[가-힣]+보건소)/g,
                type: 'hospital',
                risk: 70,
                mask: '[의료기관]'
            },
            // 질병명 (확장된 리스트)
            {
                regex: /(간암|폐암|위암|대장암|유방암|췌장암|뇌종양|혈액암|백혈병|당뇨병?|고혈압|심장병|뇌졸중|치매|파킨슨병|우울증|조현병|양극성장애)/g,
                type: 'disease',
                risk: 60,
                mask: '[질병명]'
            },
            // 날짜 (다양한 형태)
            {
                regex: /(?:\d{4}[-\.\/]\d{1,2}[-\.\/]\d{1,2}|\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d{1,2}\/\d{1,2}\/\d{4})/g,
                type: 'date',
                risk: 40,
                mask: '[날짜]'
            },
            // 나이
            {
                regex: /(?:\d{1,3}세|\d{1,3}살)/g,
                type: 'age',
                risk: 30,
                mask: '[나이]'
            },
            // 주소 (기본 패턴)
            {
                regex: /[가-힣]+(?:시|구|군|동|로|길)\s*\d+[-\d]*/g,
                type: 'address',
                risk: 50,
                mask: '[주소]'
            }
        ];

        const detected = [];
        let maskedText = text;
        let totalRisk = 0;

        // 패턴 매칭 및 중복 제거
        patterns.forEach(pattern => {
            const matches = [...text.matchAll(pattern.regex)];
            matches.forEach(match => {
                // 중복 체크 (겹치는 범위 확인)
                const isOverlap = detected.some(existing =>
                    !(match.index >= existing.end || match.index + match[0].length <= existing.start)
                );

                if (!isOverlap) {
                    detected.push({
                        text: match[0],
                        type: pattern.type,
                        risk: pattern.risk,
                        mask: pattern.mask,
                        start: match.index,
                        end: match.index + match[0].length
                    });
                    totalRisk += pattern.risk;
                }
            });
        });

        // 마스킹 적용 (뒤에서부터 적용하여 인덱스 오류 방지)
        detected
            .sort((a, b) => b.start - a.start)
            .forEach(item => {
                maskedText = maskedText.substring(0, item.start) +
                    item.mask +
                    maskedText.substring(item.end);
            });

        const processingTime = performance.now() - startTime;
        const avgRisk = detected.length > 0 ? Math.round(totalRisk / detected.length) : 0;

        const result = {
            success: true,
            originalText: text,
            maskedText: maskedText,
            stats: {
                totalEntities: detected.length,
                maskedEntities: detected.length,
                avgRisk: avgRisk,
                processingTime: Math.round(processingTime)
            },
            maskingLog: detected.map(item => ({
                token: item.text,
                entity: item.type,
                risk_weight: item.risk,
                masked_as: item.mask,
                start_pos: item.start,
                end_pos: item.end
            })),
            modelInfo: {
                type: 'local_pattern',
                version: '2.0.0',
                patterns_used: patterns.length
            },
            timestamp: new Date().toISOString()
        };

        console.log(`🔧 로컬 마스킹 완료: ${result.stats.maskedEntities}개 개체, ${processingTime.toFixed(1)}ms`);
        return result;
    }

    /**
     * 결과 정규화
     */
    normalizeResult(serverResult, source = 'server') {
        const normalized = {
            success: true,
            originalText: serverResult.original_text,
            maskedText: serverResult.masked_text,
            stats: {
                totalEntities: serverResult.stats?.total_entities || 0,
                maskedEntities: serverResult.stats?.masked_entities || 0,
                avgRisk: serverResult.stats?.avg_risk || 0,
                processingTime: serverResult.stats?.processing_time || 0
            },
            maskingLog: serverResult.masking_log || [],
            modelInfo: serverResult.model_info || { type: source },
            timestamp: new Date().toISOString()
        };

        return normalized;
    }

    /**
     * 빈 결과 생성
     */
    createEmptyResult(text) {
        return {
            success: true,
            originalText: text || '',
            maskedText: text || '',
            stats: {
                totalEntities: 0,
                maskedEntities: 0,
                avgRisk: 0,
                processingTime: 0
            },
            maskingLog: [],
            modelInfo: { type: 'empty' },
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 오류 결과 생성
     */
    createErrorResult(text, errorMessage) {
        return {
            success: false,
            originalText: text || '',
            maskedText: text || '',
            error: errorMessage,
            stats: {
                totalEntities: 0,
                maskedEntities: 0,
                avgRisk: 0,
                processingTime: 0
            },
            maskingLog: [],
            modelInfo: { type: 'error' },
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 빠른 분석 (실시간 경고용)
     */
    async quickAnalyze(text) {
        if (!text || text.length < 10) {
            return { hasRisk: false, riskLevel: 0, entityCount: 0 };
        }

        try {
            const result = await this.maskText(text);
            return {
                hasRisk: result.stats.totalEntities > 0,
                riskLevel: result.stats.avgRisk,
                entityCount: result.stats.totalEntities,
                processingTime: result.stats.processingTime
            };
        } catch (error) {
            console.warn('빠른 분석 실패:', error);
            return { hasRisk: false, riskLevel: 0, entityCount: 0, error: error.message };
        }
    }

    /**
     * 캐시 관련 메소드들
     */
    generateCacheKey(text, options) {
        const optionsStr = JSON.stringify({
            threshold: options.threshold || this.settings.threshold,
            mode: options.mode || this.settings.mode
        });
        return `${text.substring(0, 100)}_${btoa(optionsStr).substring(0, 10)}`;
    }

    setCacheResult(key, result) {
        if (this.cache.size >= this.cacheMaxSize) {
            // 가장 오래된 항목 삭제
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(key, {
            result: result,
            timestamp: Date.now()
        });
    }

    setupCacheCleanup() {
        // 10분마다 만료된 캐시 정리
        setInterval(() => {
            const now = Date.now();
            for (const [key, value] of this.cache.entries()) {
                if (now - value.timestamp > this.cacheTimeout) {
                    this.cache.delete(key);
                }
            }
        }, 600000); // 10분
    }

    /**
     * 요청 ID 생성
     */
    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
    }

    /**
     * 설정 업데이트
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        console.log('⚙️ 설정 업데이트:', this.settings);

        // 캐시 초기화 (설정 변경으로 인한 결과 차이 방지)
        this.cache.clear();
    }

    /**
     * 연결 상태 및 통계 반환
     */
    getStatus() {
        return {
            connected: this.isServerConnected,
            endpoint: this.apiEndpoint,
            settings: this.settings,
            connectionAttempts: this.connectionAttempts,
            cacheSize: this.cache.size,
            serverInfo: this.serverInfo || null
        };
    }

    /**
     * 수동 재연결
     */
    async reconnect() {
        console.log('🔄 서버 재연결 시도...');
        this.connectionAttempts = 0;
        return await this.checkServerConnection();
    }

    /**
     * 캐시 초기화
     */
    clearCache() {
        this.cache.clear();
        console.log('🗑️ 캐시 초기화 완료');
    }

    /**
     * 연결 상태 getter
     */
    get isConnected() {
        return this.isServerConnected;
    }
}

// 전역 인스턴스 생성 및 노출
if (typeof window !== 'undefined') {
    window.privacyClient = new PrivacyClient();

    // 디버깅을 위한 전역 노출
    window.PrivacyClient = PrivacyClient;

    console.log('🛡️ Privacy Client 로드 완료');
}
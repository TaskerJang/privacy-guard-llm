// extension/masking-engine.js
// 간소화된 마스킹 엔진 - 서버 우선, 클라이언트 최소화

class MaskingEngine {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;
        this.settings = {
            threshold: 50,
            mode: 'medical',
            enabled: false
        };

        this.init();
    }

    async init() {
        await this.checkServerStatus();
        this.startPeriodicHealthCheck();
        console.log('🎭 Masking Engine 초기화 완료');
    }

    /**
     * 서버 상태 확인
     */
    async checkServerStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch(`${this.apiEndpoint}/health`, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            this.isServerConnected = response.ok;

            if (this.isServerConnected) {
                console.log('✅ 서버 연결 성공');
            } else {
                console.warn('⚠️ 서버 응답 오류');
            }

            return this.isServerConnected;
        } catch (error) {
            this.isServerConnected = false;
            console.warn('⚠️ 서버 연결 실패:', error.message);
            return false;
        }
    }

    /**
     * 주기적 서버 상태 체크
     */
    startPeriodicHealthCheck() {
        setInterval(() => {
            if (!this.isServerConnected) {
                this.checkServerStatus();
            }
        }, 30000); // 30초마다
    }

    /**
     * 메인 마스킹 처리 함수
     */
    async process(text, options = {}) {
        if (!text || text.trim().length === 0) {
            return this.createEmptyResult(text);
        }

        const requestSettings = {
            text: text.trim(),
            threshold: options.threshold || this.settings.threshold,
            mode: options.mode || this.settings.mode,
            use_contextual_analysis: true
        };

        console.log(`🚀 마스킹 처리 시작: ${text.length}자`);

        // 서버 연결 확인
        if (!this.isServerConnected) {
            await this.checkServerStatus();
        }

        if (!this.isServerConnected) {
            return this.createErrorResult(text, '서버에 연결할 수 없습니다');
        }

        try {
            const result = await this.callServerAPI(requestSettings);
            console.log(`✅ 처리 완료: ${result.stats.maskedEntities}/${result.stats.totalEntities} 마스킹`);
            return result;
        } catch (error) {
            console.error('❌ 마스킹 처리 실패:', error);
            this.isServerConnected = false;
            return this.createErrorResult(text, error.message);
        }
    }

    /**
     * 서버 API 호출
     */
    async callServerAPI(settings) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        try {
            const response = await fetch(`${this.apiEndpoint}/api/mask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                return this.normalizeServerResponse(data);
            } else {
                throw new Error(data.error || '서버 처리 실패');
            }

        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('요청 시간 초과');
            }
            throw error;
        }
    }

    /**
     * 서버 응답 정규화
     */
    normalizeServerResponse(serverData) {
        return {
            success: true,
            originalText: serverData.original_text || '',
            maskedText: serverData.masked_text || '',
            stats: {
                totalEntities: serverData.stats?.total_entities || 0,
                maskedEntities: serverData.stats?.masked_entities || 0,
                avgRisk: serverData.stats?.avg_risk || 0,
                processingTime: serverData.stats?.processing_time || 0
            },
            entities: this.convertMaskingLog(serverData.masking_log || []),
            maskingLog: serverData.masking_log || [],
            modelInfo: serverData.model_info,
            source: 'server',
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 마스킹 로그를 엔티티 형식으로 변환
     */
    convertMaskingLog(maskingLog) {
        return maskingLog.map((log, index) => ({
            id: index,
            token: log.token,
            type: log.entity,
            risk: log.risk_weight,
            masked: log.masked_as
        }));
    }

    /**
     * 빠른 분석 (실시간 경고용)
     */
    async quickAnalyze(text) {
        if (!text || text.length < 5) {
            return { hasRisk: false, riskLevel: 0, entityCount: 0 };
        }

        try {
            const result = await this.process(text);

            if (result.success) {
                return {
                    hasRisk: result.stats.totalEntities > 0,
                    riskLevel: result.stats.avgRisk,
                    entityCount: result.stats.totalEntities,
                    detectedItems: result.entities || []
                };
            } else {
                return { hasRisk: false, riskLevel: 0, error: result.error };
            }
        } catch (error) {
            console.warn('빠른 분석 실패:', error);
            return { hasRisk: false, riskLevel: 0, error: error.message };
        }
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
            entities: [],
            maskingLog: [],
            source: 'empty',
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
            entities: [],
            maskingLog: [],
            source: 'error',
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 설정 업데이트
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        console.log('⚙️ 마스킹 엔진 설정 업데이트:', this.settings);
    }

    /**
     * 상태 정보 반환
     */
    getStatus() {
        return {
            serverConnected: this.isServerConnected,
            endpoint: this.apiEndpoint,
            settings: this.settings,
            lastCheck: new Date().toISOString()
        };
    }

    /**
     * 수동 재연결
     */
    async reconnect() {
        console.log('🔄 서버 재연결 시도...');
        const success = await this.checkServerStatus();
        return success;
    }

    /**
     * 서버 테스트
     */
    async testConnection() {
        console.log('🧪 연결 테스트 시작...');

        try {
            // Health check
            const healthOk = await this.checkServerStatus();
            if (!healthOk) {
                throw new Error('Health check 실패');
            }

            // 간단한 테스트 요청
            const testResult = await this.process('테스트 메시지입니다');

            console.log('✅ 연결 테스트 성공');
            return {
                success: true,
                message: '서버 연결 및 처리 테스트 완료',
                result: testResult
            };

        } catch (error) {
            console.error('❌ 연결 테스트 실패:', error);
            return {
                success: false,
                message: error.message,
                error: error
            };
        }
    }
}

// 전역 인스턴스 생성
window.maskingEngine = new MaskingEngine();

// 기존 privacyGuard와의 호환성을 위한 별칭
window.privacyGuard = window.maskingEngine;

console.log('🎭 Masking Engine 로드 완료');
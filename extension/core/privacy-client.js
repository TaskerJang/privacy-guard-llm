// extension/core/privacy-client.js
// 서버 기반 개인정보 보호 클라이언트

class PrivacyClient {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;
        this.settings = {
            threshold: 50,
            mode: 'medical',
            autoRetry: true
        };

        this.init();
    }

    async init() {
        await this.checkServerConnection();
        this.startHealthCheck();
    }

    /**
     * 서버 연결 상태 확인
     */
    async checkServerConnection() {
        try {
            const response = await fetch(`${this.apiEndpoint}/health`, {
                method: 'GET',
                timeout: 3000
            });

            this.isServerConnected = response.ok;
            console.log(`🔗 서버 상태: ${this.isServerConnected ? '연결됨' : '연결 실패'}`);
            return this.isServerConnected;
        } catch (error) {
            this.isServerConnected = false;
            console.warn('⚠️ 서버 연결 실패');
            return false;
        }
    }

    /**
     * 주기적 서버 상태 체크
     */
    startHealthCheck() {
        setInterval(() => {
            if (!this.isServerConnected) {
                this.checkServerConnection();
            }
        }, 30000);
    }

    /**
     * 텍스트 마스킹 처리 (메인 API)
     */
    async maskText(text, options = {}) {
        if (!text || text.trim().length === 0) {
            return this.createEmptyResult(text);
        }

        const requestData = {
            text: text.trim(),
            threshold: options.threshold || this.settings.threshold,
            mode: options.mode || this.settings.mode,
            use_contextual_analysis: true
        };

        console.log(`🚀 마스킹 요청: ${text.length}자, 임계값: ${requestData.threshold}`);

        try {
            // 서버 연결 확인
            if (!this.isServerConnected) {
                await this.checkServerConnection();
            }

            if (!this.isServerConnected) {
                throw new Error('서버에 연결할 수 없습니다');
            }

            // API 호출
            const response = await fetch(`${this.apiEndpoint}/api/mask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                console.log(`✅ 마스킹 완료: ${result.stats.masked_entities}/${result.stats.total_entities} 개체`);
                return this.normalizeResult(result);
            } else {
                throw new Error(result.error || '서버 처리 실패');
            }

        } catch (error) {
            console.error('❌ 마스킹 오류:', error);
            this.isServerConnected = false;

            // 빈 결과 반환 (UI에서 오류 처리)
            return this.createErrorResult(text, error.message);
        }
    }

    /**
     * 결과 정규화
     */
    normalizeResult(serverResult) {
        return {
            success: true,
            originalText: serverResult.original_text,
            maskedText: serverResult.masked_text,
            stats: {
                totalEntities: serverResult.stats.total_entities,
                maskedEntities: serverResult.stats.masked_entities,
                avgRisk: serverResult.stats.avg_risk,
                processingTime: serverResult.stats.processing_time
            },
            maskingLog: serverResult.masking_log || [],
            modelInfo: serverResult.model_info,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 빈 결과 생성
     */
    createEmptyResult(text) {
        return {
            success: true,
            originalText: text,
            maskedText: text,
            stats: {
                totalEntities: 0,
                maskedEntities: 0,
                avgRisk: 0,
                processingTime: 0
            },
            maskingLog: [],
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 오류 결과 생성
     */
    createErrorResult(text, errorMessage) {
        return {
            success: false,
            originalText: text,
            maskedText: text,
            error: errorMessage,
            stats: {
                totalEntities: 0,
                maskedEntities: 0,
                avgRisk: 0,
                processingTime: 0
            },
            maskingLog: [],
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 빠른 분석 (실시간 경고용)
     */
    async quickAnalyze(text) {
        if (!text || text.length < 10) return { hasRisk: false, riskLevel: 0 };

        try {
            const result = await this.maskText(text);
            return {
                hasRisk: result.stats.totalEntities > 0,
                riskLevel: result.stats.avgRisk,
                entityCount: result.stats.totalEntities
            };
        } catch (error) {
            return { hasRisk: false, riskLevel: 0, error: error.message };
        }
    }

    /**
     * 설정 업데이트
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        console.log('⚙️ 설정 업데이트:', this.settings);
    }

    /**
     * 연결 상태 반환
     */
    getStatus() {
        return {
            connected: this.isServerConnected,
            endpoint: this.apiEndpoint,
            settings: this.settings
        };
    }

    /**
     * 수동 재연결
     */
    async reconnect() {
        console.log('🔄 서버 재연결 시도...');
        return await this.checkServerConnection();
    }
}

// 전역 인스턴스 생성
window.privacyClient = new PrivacyClient();
// extension/core/privacy-client.js
// 폴백 제거된 서버 전용 개인정보 보호 클라이언트

class PrivacyClient {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;
        this.connectionAttempts = 0;
        this.maxRetries = 3;

        this.settings = {
            threshold: 50,
            mode: 'medical',
            timeout: 10000,
            retryInterval: 5000
        };

        // 요청 캐시 (동일한 텍스트 재분석 방지)
        this.cache = new Map();
        this.cacheMaxSize = 50;
        this.cacheTimeout = 300000; // 5분

        this.init();
    }

    async init() {
        console.log('🔗 Privacy Client 초기화 중 (서버 전용 모드)...');
        await this.checkServerConnection();
        this.startHealthCheck();
        this.setupCacheCleanup();
    }

    /**
     * 서버 연결 상태 확인
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
                console.log(`🤖 모델 정보: ${data.model_info?.name || 'Unknown'} v${data.model_info?.version || 'Unknown'}`);

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
                console.error(`⏱️ 서버 연결 시간 초과 (시도: ${this.connectionAttempts}/${this.maxRetries})`);
            } else {
                console.error(`❌ 서버 연결 실패: ${error.message} (시도: ${this.connectionAttempts}/${this.maxRetries})`);
            }

            return false;
        }
    }

    /**
     * 주기적 서버 상태 체크
     */
    startHealthCheck() {
        setInterval(async () => {
            if (!this.isServerConnected) {
                if (this.connectionAttempts < this.maxRetries) {
                    console.log(`🔄 서버 재연결 시도 (${this.connectionAttempts + 1}/${this.maxRetries})`);
                    await this.checkServerConnection();
                } else {
                    console.error(`🚫 최대 재시도 횟수 초과. 서버를 확인해주세요.`);
                }
            } else {
                // 연결된 상태에서도 주기적 체크
                const isHealthy = await this.quickHealthCheck();
                if (!isHealthy) {
                    console.warn('⚠️ 서버 연결이 끊어졌습니다. 재연결을 시도합니다.');
                    this.isServerConnected = false;
                    this.connectionAttempts = 0;
                }
            }
        }, this.settings.retryInterval);
    }

    /**
     * 빠른 헬스 체크
     */
    async quickHealthCheck() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

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
     * 텍스트 마스킹 처리 (서버 전용)
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

        // 서버 연결 필수 확인
        if (!this.isServerConnected) {
            console.error('🚫 서버에 연결되지 않았습니다. 로컬 처리가 비활성화되어 있습니다.');
            return this.createServerErrorResult(cleanText, '서버에 연결되지 않았습니다. 서버를 시작하고 다시 시도해주세요.');
        }

        const requestData = {
            text: cleanText,
            threshold: options.threshold || this.settings.threshold,
            mode: options.mode || this.settings.mode,
            use_contextual_analysis: true,
            request_id: this.generateRequestId()
        };

        console.log(`🚀 서버 마스킹 요청: ${cleanText.length}자, 모드: ${requestData.mode}`);

        try {
            const result = await this.serverMaskText(requestData);
            console.log(`✅ 서버 마스킹 완료: ${result.stats.maskedEntities}/${result.stats.totalEntities} 개체 (모델: ${result.modelInfo?.name || 'Unknown'})`);

            // 결과 캐싱
            this.setCacheResult(cacheKey, result);

            return result;

        } catch (error) {
            console.error('❌ 서버 마스킹 실패:', error.message);
            this.isServerConnected = false;

            return this.createServerErrorResult(cleanText, `서버 처리 실패: ${error.message}`);
        }
    }

    /**
     * 서버 기반 마스킹 (유일한 처리 방법)
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
            modelInfo: {
                name: serverResult.model_info?.name || 'Unknown',
                version: serverResult.model_info?.version || 'Unknown',
                type: serverResult.model_info?.type || 'neural_network',
                source: source
            },
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
            modelInfo: {
                name: 'N/A',
                version: 'N/A',
                type: 'empty',
                source: 'client'
            },
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 서버 오류 결과 생성
     */
    createServerErrorResult(text, errorMessage) {
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
            modelInfo: {
                name: 'Error',
                version: 'N/A',
                type: 'error',
                source: 'client'
            },
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 빠른 분석 (실시간 경고용) - 서버 전용
     */
    async quickAnalyze(text) {
        if (!text || text.length < 10) {
            return { hasRisk: false, riskLevel: 0, entityCount: 0, usingServer: false };
        }

        if (!this.isServerConnected) {
            return {
                hasRisk: false,
                riskLevel: 0,
                entityCount: 0,
                error: '서버에 연결되지 않았습니다',
                usingServer: false
            };
        }

        try {
            const result = await this.maskText(text);
            return {
                hasRisk: result.stats.totalEntities > 0,
                riskLevel: result.stats.avgRisk,
                entityCount: result.stats.totalEntities,
                processingTime: result.stats.processingTime,
                usingServer: true,
                modelInfo: result.modelInfo
            };
        } catch (error) {
            console.warn('빠른 분석 실패:', error);
            return {
                hasRisk: false,
                riskLevel: 0,
                entityCount: 0,
                error: error.message,
                usingServer: false
            };
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
            maxRetries: this.maxRetries,
            cacheSize: this.cache.size,
            serverInfo: this.serverInfo || null,
            fallbackEnabled: false // 폴백 비활성화 명시
        };
    }

    /**
     * 수동 재연결
     */
    async reconnect() {
        console.log('🔄 서버 수동 재연결 시도...');
        this.connectionAttempts = 0;
        const result = await this.checkServerConnection();

        if (result) {
            console.log('✅ 수동 재연결 성공');
        } else {
            console.error('❌ 수동 재연결 실패');
        }

        return result;
    }

    /**
     * 캐시 초기화
     */
    clearCache() {
        this.cache.clear();
        console.log('🗑️ 캐시 초기화 완료');
    }

    /**
     * 서버 연결 필수 확인
     */
    requireServerConnection() {
        if (!this.isServerConnected) {
            throw new Error('이 기능을 사용하려면 서버에 연결되어야 합니다. localhost:8000에서 서버를 시작해주세요.');
        }
    }

    /**
     * 연결 상태 getter
     */
    get isConnected() {
        return this.isServerConnected;
    }

    /**
     * 서버 정보 getter
     */
    get modelInfo() {
        return this.serverInfo?.model_info || { name: 'Unknown', version: 'Unknown' };
    }
}

// 전역 인스턴스 생성 및 노출
if (typeof window !== 'undefined') {
    window.privacyClient = new PrivacyClient();

    // 디버깅을 위한 전역 노출
    window.PrivacyClient = PrivacyClient;

    console.log('🛡️ Privacy Client 로드 완료 (서버 전용 모드)');
    console.log('📋 폴백 기능: 비활성화됨 - 서버 연결 필수');
}
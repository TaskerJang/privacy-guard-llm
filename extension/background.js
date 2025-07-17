// extension/background.js
// 간소화된 백그라운드 서비스 워커

class BackgroundService {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;

        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupInstallListener();
        this.startPeriodicHealthCheck();
    }

    /**
     * 메시지 리스너 설정
     */
    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // 비동기 응답을 위해 true 반환
        });
    }

    /**
     * 확장 프로그램 설치 시 처리
     */
    setupInstallListener() {
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.handleFirstInstall();
            } else if (details.reason === 'update') {
                this.handleUpdate(details.previousVersion);
            }
        });
    }

    /**
     * 메시지 처리
     */
    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'mask':
                    const result = await this.processMaskingRequest(request.text, request.options);
                    sendResponse(result);
                    break;

                case 'healthCheck':
                    const health = await this.checkServerHealth();
                    sendResponse({ connected: health });
                    break;

                case 'getSettings':
                    const settings = await this.getStoredSettings();
                    sendResponse(settings);
                    break;

                case 'saveSettings':
                    await this.saveSettings(request.settings);
                    sendResponse({ success: true });
                    break;

                default:
                    console.warn('알 수 없는 액션:', request.action);
                    sendResponse({ error: '지원하지 않는 액션입니다' });
            }
        } catch (error) {
            console.error('메시지 처리 오류:', error);
            sendResponse({ error: error.message });
        }
    }

    /**
     * 마스킹 요청 처리
     */
    async processMaskingRequest(text, options = {}) {
        if (!text || text.trim().length === 0) {
            return {
                success: false,
                error: '텍스트가 비어있습니다'
            };
        }

        try {
            // 서버 연결 확인
            if (!this.isServerConnected) {
                await this.checkServerHealth();
            }

            if (!this.isServerConnected) {
                throw new Error('서버에 연결할 수 없습니다');
            }

            // API 요청
            const requestData = {
                text: text.trim(),
                threshold: options.threshold || 50,
                mode: options.mode || 'medical',
                use_contextual_analysis: true
            };

            const response = await this.makeRequest('/api/mask', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                console.log(`✅ 마스킹 완료: ${result.stats?.masked_entities || 0}개 개체 마스킹`);
                return {
                    success: true,
                    originalText: result.original_text,
                    maskedText: result.masked_text,
                    stats: result.stats,
                    maskingLog: result.masking_log,
                    modelInfo: result.model_info
                };
            } else {
                throw new Error(result.error || '서버 처리 실패');
            }

        } catch (error) {
            console.error('마스킹 처리 오류:', error);
            this.isServerConnected = false;

            return {
                success: false,
                error: error.message,
                fallbackAvailable: true
            };
        }
    }

    /**
     * 서버 상태 확인
     */
    async checkServerHealth() {
        try {
            const response = await this.makeRequest('/health', { method: 'GET' });
            this.isServerConnected = response.ok;

            if (this.isServerConnected) {
                console.log('🔗 서버 연결 성공');
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
     * HTTP 요청 헬퍼
     */
    async makeRequest(path, options = {}) {
        const url = `${this.apiEndpoint}${path}`;
        const config = {
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);

        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('요청 시간 초과');
            }
            throw error;
        }
    }

    /**
     * 설정 관리
     */
    async getStoredSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            return result.privacyGuardSettings || {
                enabled: false,
                threshold: 50,
                mode: 'medical'
            };
        } catch (error) {
            console.warn('설정 로드 실패:', error);
            return {
                enabled: false,
                threshold: 50,
                mode: 'medical'
            };
        }
    }

    async saveSettings(settings) {
        try {
            await chrome.storage.sync.set({ privacyGuardSettings: settings });
            console.log('⚙️ 설정 저장 완료:', settings);
        } catch (error) {
            console.error('설정 저장 실패:', error);
            throw error;
        }
    }

    /**
     * 주기적 서버 상태 체크
     */
    startPeriodicHealthCheck() {
        // 5분마다 서버 상태 확인
        setInterval(() => {
            this.checkServerHealth();
        }, 5 * 60 * 1000);

        // 초기 상태 확인
        this.checkServerHealth();
    }

    /**
     * 첫 설치 시 처리
     */
    async handleFirstInstall() {
        console.log('🎉 Privacy Guard LLM 설치 완료');

        // 기본 설정 저장
        await this.saveSettings({
            enabled: false,
            threshold: 50,
            mode: 'medical'
        });

        // 환영 탭 열기 (선택사항)
        // chrome.tabs.create({ url: 'welcome.html' });
    }

    /**
     * 업데이트 시 처리
     */
    async handleUpdate(previousVersion) {
        console.log(`🔄 Privacy Guard LLM 업데이트: ${previousVersion} → ${chrome.runtime.getManifest().version}`);

        // 필요시 설정 마이그레이션 수행
        await this.migrateSettings(previousVersion);
    }

    /**
     * 설정 마이그레이션
     */
    async migrateSettings(previousVersion) {
        try {
            const currentSettings = await this.getStoredSettings();

            // 버전별 마이그레이션 로직
            if (this.compareVersions(previousVersion, '1.0.0') < 0) {
                // v1.0.0 이전 버전에서 업데이트
                currentSettings.mode = currentSettings.mode || 'medical';
            }

            await this.saveSettings(currentSettings);
            console.log('⚙️ 설정 마이그레이션 완료');
        } catch (error) {
            console.error('설정 마이그레이션 실패:', error);
        }
    }

    /**
     * 버전 비교 헬퍼
     */
    compareVersions(version1, version2) {
        const v1 = version1.split('.').map(Number);
        const v2 = version2.split('.').map(Number);

        for (let i = 0; i < Math.max(v1.length, v2.length); i++) {
            const part1 = v1[i] || 0;
            const part2 = v2[i] || 0;

            if (part1 < part2) return -1;
            if (part1 > part2) return 1;
        }

        return 0;
    }

    /**
     * 알림 생성
     */
    showNotification(title, message, type = 'basic') {
        chrome.notifications.create({
            type: type,
            iconUrl: 'icons/icon-48.png',
            title: title,
            message: message
        });
    }

    /**
     * 컨텍스트 메뉴 설정 (선택사항)
     */
    setupContextMenu() {
        chrome.contextMenus.create({
            id: 'privacy-guard-analyze',
            title: '선택된 텍스트 분석',
            contexts: ['selection']
        });

        chrome.contextMenus.onClicked.addListener(async (info, tab) => {
            if (info.menuItemId === 'privacy-guard-analyze' && info.selectionText) {
                const result = await this.processMaskingRequest(info.selectionText);

                if (result.success && result.stats.totalEntities > 0) {
                    this.showNotification(
                        '민감정보 감지됨',
                        `${result.stats.maskedEntities}개의 민감정보가 발견되었습니다`
                    );
                } else {
                    this.showNotification(
                        '분석 완료',
                        '민감정보가 감지되지 않았습니다'
                    );
                }
            }
        });
    }
}

// 서비스 워커 초기화
const backgroundService = new BackgroundService();

// 확장 프로그램 시작 시 초기화
chrome.runtime.onStartup.addListener(() => {
    console.log('🚀 Privacy Guard LLM 시작됨');
});

// 에러 핸들링
self.addEventListener('error', (event) => {
    console.error('백그라운드 스크립트 오류:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('처리되지 않은 Promise 거부:', event.reason);
});
// extension/background.js
// 오류 수정된 백그라운드 서비스 워커

class ImprovedBackgroundService {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000';
        this.isServerConnected = false;
        this.lastHealthCheck = 0;
        this.healthCheckInterval = 30000; // 30초

        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupInstallListener();
        this.setupStorageListener();
        this.startPeriodicHealthCheck();
        this.initializeDefaultSettings();
    }

    /**
     * 기본 설정 초기화
     */
    async initializeDefaultSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            if (!result.privacyGuardSettings) {
                const defaultSettings = {
                    enabled: false,
                    threshold: 50,
                    mode: 'medical',
                    lastUpdated: Date.now()
                };

                await chrome.storage.sync.set({ privacyGuardSettings: defaultSettings });
                console.log('📝 기본 설정 초기화 완료');
            }
        } catch (error) {
            console.warn('⚠️ 기본 설정 초기화 실패:', error);
        }
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
     * 스토리지 변경 리스너 설정
     */
    setupStorageListener() {
        chrome.storage.onChanged.addListener((changes, namespace) => {
            if (namespace === 'sync' && changes.privacyGuardSettings) {
                console.log('📡 설정 변경 감지:', changes.privacyGuardSettings.newValue);
                this.broadcastSettingsChange(changes.privacyGuardSettings.newValue);
            }
        });
    }

    /**
     * 설정 변경 브로드캐스트 - 오류 처리 개선
     */
    async broadcastSettingsChange(newSettings) {
        try {
            const tabs = await chrome.tabs.query({});
            const message = {
                action: 'updateSettings',
                settings: newSettings
            };

            // 모든 활성 탭에 설정 변경 알림
            for (const tab of tabs) {
                try {
                    await new Promise((resolve) => {
                        chrome.tabs.sendMessage(tab.id, message, (response) => {
                            // lastError 체크하여 무시
                            if (chrome.runtime.lastError) {
                                // content script가 없는 탭은 무시
                                console.debug(`탭 ${tab.id}에 content script 없음:`, chrome.runtime.lastError.message);
                            }
                            resolve();
                        });
                    });
                } catch (error) {
                    // 개별 탭 오류 무시
                    console.debug(`탭 ${tab.id} 메시지 전송 실패:`, error.message);
                }
            }

            console.log('📡 설정 변경 브로드캐스트 완료');
        } catch (error) {
            console.warn('⚠️ 설정 브로드캐스트 실패:', error);
        }
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
     * 메시지 처리 - 개선된 버전
     */
    async handleMessage(request, sender, sendResponse) {
        try {
            console.log('📨 메시지 수신:', request.action);

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

                case 'toggleProtection':
                    const toggleResult = await this.handleToggleProtection(request.enabled);
                    sendResponse(toggleResult);
                    break;

                case 'getStatus':
                    const status = await this.getExtensionStatus();
                    sendResponse(status);
                    break;

                default:
                    console.warn('⚠️ 알 수 없는 액션:', request.action);
                    sendResponse({ success: false, error: '지원하지 않는 액션입니다' });
            }
        } catch (error) {
            console.error('❌ 메시지 처리 오류:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    /**
     * 보호 기능 토글 처리
     */
    async handleToggleProtection(enabled) {
        try {
            const currentSettings = await this.getStoredSettings();
            const newSettings = {
                ...currentSettings,
                enabled: enabled,
                lastUpdated: Date.now()
            };

            await this.saveSettings(newSettings);

            console.log(`🔄 보호 기능 ${enabled ? '활성화' : '비활성화'}`);

            return { success: true, enabled: enabled };
        } catch (error) {
            console.error('❌ 보호 기능 토글 실패:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 확장 프로그램 상태 조회
     */
    async getExtensionStatus() {
        try {
            const settings = await this.getStoredSettings();
            const serverHealth = await this.checkServerHealth();

            return {
                success: true,
                enabled: settings.enabled,
                settings: settings,
                serverConnected: serverHealth,
                lastHealthCheck: this.lastHealthCheck
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 마스킹 요청 처리 - 개선된 에러 처리
     */
    async processMaskingRequest(text, options = {}) {
        if (!text || text.trim().length === 0) {
            return {
                success: false,
                error: '텍스트가 비어있습니다'
            };
        }

        try {
            // 서버 연결 확인 (캐시된 결과 사용)
            if (!this.isServerConnected || Date.now() - this.lastHealthCheck > this.healthCheckInterval) {
                await this.checkServerHealth();
            }

            if (!this.isServerConnected) {
                return {
                    success: false,
                    error: '서버에 연결할 수 없습니다',
                    serverConnected: false
                };
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
                    modelInfo: result.model_info,
                    serverConnected: true
                };
            } else {
                throw new Error(result.error || '서버 처리 실패');
            }

        } catch (error) {
            console.error('❌ 마스킹 처리 오류:', error);
            this.isServerConnected = false;

            return {
                success: false,
                error: error.message,
                serverConnected: false,
                fallbackAvailable: false
            };
        }
    }

    /**
     * 서버 상태 확인 - 개선된 캐싱
     */
    async checkServerHealth() {
        try {
            const response = await this.makeRequest('/health', {
                method: 'GET',
                timeout: 3000
            });

            this.isServerConnected = response.ok;
            this.lastHealthCheck = Date.now();

            if (this.isServerConnected) {
                console.log('🔗 서버 연결 성공');
            } else {
                console.warn('⚠️ 서버 응답 오류');
            }

            return this.isServerConnected;
        } catch (error) {
            this.isServerConnected = false;
            this.lastHealthCheck = Date.now();
            console.warn('⚠️ 서버 연결 실패:', error.message);
            return false;
        }
    }

    /**
     * HTTP 요청 헬퍼 - 개선된 에러 처리
     */
    async makeRequest(path, options = {}) {
        const url = `${this.apiEndpoint}${path}`;
        const config = {
            timeout: options.timeout || 8000,
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
     * 설정 관리 - 개선된 버전
     */
    async getStoredSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            return result.privacyGuardSettings || {
                enabled: false,
                threshold: 50,
                mode: 'medical',
                lastUpdated: Date.now()
            };
        } catch (error) {
            console.warn('⚠️ 설정 로드 실패:', error);
            return {
                enabled: false,
                threshold: 50,
                mode: 'medical',
                lastUpdated: Date.now()
            };
        }
    }

    async saveSettings(settings) {
        try {
            const settingsWithTimestamp = {
                ...settings,
                lastUpdated: Date.now()
            };

            await chrome.storage.sync.set({ privacyGuardSettings: settingsWithTimestamp });
            console.log('⚙️ 설정 저장 완료:', settingsWithTimestamp);
        } catch (error) {
            console.error('❌ 설정 저장 실패:', error);
            throw error;
        }
    }

    /**
     * 주기적 서버 상태 체크
     */
    startPeriodicHealthCheck() {
        // 초기 상태 확인
        setTimeout(() => {
            this.checkServerHealth();
        }, 1000);

        // 주기적 확인 (30초마다)
        setInterval(() => {
            this.checkServerHealth();
        }, this.healthCheckInterval);
    }

    /**
     * 첫 설치 시 처리 - 알림 API 안전 처리
     */
    async handleFirstInstall() {
        console.log('🎉 Privacy Guard LLM 설치 완료');

        try {
            // 기본 설정 저장
            await this.saveSettings({
                enabled: false,
                threshold: 50,
                mode: 'medical'
            });

            // 알림 API 사용 가능 여부 확인
            if (chrome.notifications && typeof chrome.notifications.create === 'function') {
                try {
                    chrome.notifications.create({
                        type: 'basic',
                        iconUrl: 'icons/icon-48.png',
                        title: 'Privacy Guard LLM',
                        message: '설치가 완료되었습니다. 브라우저 우상단의 🛡️ 아이콘을 클릭하여 시작하세요.'
                    });
                } catch (notificationError) {
                    console.warn('⚠️ 알림 생성 실패:', notificationError);
                }
            } else {
                console.log('ℹ️ 알림 API를 사용할 수 없습니다');
            }

        } catch (error) {
            console.error('❌ 첫 설치 처리 실패:', error);
        }
    }

    /**
     * 업데이트 시 처리
     */
    async handleUpdate(previousVersion) {
        console.log(`🔄 Privacy Guard LLM 업데이트: ${previousVersion} → ${chrome.runtime.getManifest().version}`);

        try {
            // 필요시 설정 마이그레이션 수행
            await this.migrateSettings(previousVersion);
        } catch (error) {
            console.error('❌ 업데이트 처리 실패:', error);
        }
    }

    /**
     * 설정 마이그레이션
     */
    async migrateSettings(previousVersion) {
        try {
            const currentSettings = await this.getStoredSettings();

            // 버전별 마이그레이션 로직
            let needsUpdate = false;

            if (this.compareVersions(previousVersion, '2.0.0') < 0) {
                // v2.0.0 이전 버전에서 업데이트
                if (!currentSettings.hasOwnProperty('lastUpdated')) {
                    currentSettings.lastUpdated = Date.now();
                    needsUpdate = true;
                }
            }

            if (needsUpdate) {
                await this.saveSettings(currentSettings);
                console.log('⚙️ 설정 마이그레이션 완료');
            }

        } catch (error) {
            console.error('❌ 설정 마이그레이션 실패:', error);
        }
    }

    /**
     * 버전 비교 헬퍼
     */
    compareVersions(version1, version2) {
        if (!version1 || !version2) return 0;

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
     * 안전한 알림 생성
     */
    showNotification(title, message, type = 'basic') {
        if (chrome.notifications && typeof chrome.notifications.create === 'function') {
            try {
                chrome.notifications.create({
                    type: type,
                    iconUrl: 'icons/icon-48.png',
                    title: title,
                    message: message
                });
            } catch (error) {
                console.warn('⚠️ 알림 생성 실패:', error);
            }
        } else {
            console.log(`📢 알림: ${title} - ${message}`);
        }
    }

    /**
     * 디버깅 정보 수집
     */
    getDebugInfo() {
        return {
            serverConnected: this.isServerConnected,
            lastHealthCheck: new Date(this.lastHealthCheck).toISOString(),
            apiEndpoint: this.apiEndpoint,
            extensionVersion: chrome.runtime.getManifest()?.version || 'unknown'
        };
    }
}

// 서비스 워커 초기화
let backgroundService;

try {
    backgroundService = new ImprovedBackgroundService();
} catch (error) {
    console.error('❌ 백그라운드 서비스 초기화 실패:', error);
}

// 확장 프로그램 시작 시 초기화
chrome.runtime.onStartup.addListener(() => {
    console.log('🚀 Privacy Guard LLM 시작됨');
});

// 에러 핸들링 - 안전한 처리
self.addEventListener('error', (event) => {
    console.error('❌ 백그라운드 스크립트 오류:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('❌ 처리되지 않은 Promise 거부:', event.reason);
    // 오류 방지를 위해 preventDefault 호출
    event.preventDefault();
});

// 디버깅용 전역 함수
self.debugBackground = function() {
    if (backgroundService) {
        console.log('🐛 Background Service Debug Info:', backgroundService.getDebugInfo());
    } else {
        console.log('🐛 Background Service가 초기화되지 않았습니다');
    }
};
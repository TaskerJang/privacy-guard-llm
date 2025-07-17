// extension/popup.js
// 개선된 팝업 컨트롤러 - 상태 유지 및 자동 동기화

class ImprovedPopupController {
    constructor() {
        this.settings = {
            enabled: false,
            mode: 'medical',
            threshold: 50
        };

        this.elements = {};
        this.isLoading = false;
        this.serverConnected = false;
        this.lastResult = null;
        this.updateInterval = null;

        console.log('🛡️ 개선된 PopupController 초기화 시작');
        this.init();
    }

    async init() {
        this.initElements();
        await this.loadSettings();
        this.setupEventListeners();
        await this.checkServerStatus();

        // UI 초기 상태 설정
        this.updateUI();

        // 실시간 동기화 시작
        this.startRealTimeSync();

        console.log('🛡️ PopupController 초기화 완료', this.settings);
    }

    /**
     * DOM 요소 초기화
     */
    initElements() {
        this.elements = {
            statusToggle: document.getElementById('statusToggle'),
            detectedCount: document.getElementById('detectedCount'),
            maskedCount: document.getElementById('maskedCount'),
            serverIndicator: document.getElementById('serverIndicator'),
            serverText: document.getElementById('serverText'),
            errorMessage: document.getElementById('errorMessage'),
            resultsSection: document.getElementById('resultsSection'),
            resultTime: document.getElementById('resultTime'),
            totalEntities: document.getElementById('totalEntities'),
            avgRisk: document.getElementById('avgRisk'),
            entityDetails: document.getElementById('entityDetails')
        };

        // 요소 존재 확인
        Object.entries(this.elements).forEach(([key, element]) => {
            if (!element) {
                console.error(`❌ 요소를 찾을 수 없음: ${key}`);
            }
        });
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        if (this.elements.statusToggle) {
            this.elements.statusToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleProtection();
            });

            this.elements.statusToggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleProtection();
                }
            });

            this.elements.statusToggle.setAttribute('tabindex', '0');
        }

        // 스토리지 변경 감지
        chrome.storage.onChanged.addListener((changes, namespace) => {
            if (namespace === 'sync' && changes.privacyGuardSettings) {
                this.onSettingsChanged(changes.privacyGuardSettings.newValue);
            }
        });
    }

    /**
     * 설정 로드 - 항상 최신 상태 보장
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            if (result.privacyGuardSettings) {
                this.settings = { ...this.settings, ...result.privacyGuardSettings };
                console.log('✅ 설정 로드 완료:', this.settings);
            } else {
                // 기본 설정으로 초기화
                await this.saveSettings();
                console.log('ℹ️ 기본 설정으로 초기화됨');
            }
        } catch (error) {
            console.error('❌ 설정 로드 실패:', error);
            this.showError('설정을 불러올 수 없습니다');
        }
    }

    /**
     * 설정 저장
     */
    async saveSettings() {
        try {
            await chrome.storage.sync.set({ privacyGuardSettings: this.settings });
            console.log('✅ 설정 저장 완료:', this.settings);

            // 모든 탭의 content script에 설정 변경 알림
            await this.broadcastSettingsChange();
        } catch (error) {
            console.error('❌ 설정 저장 실패:', error);
            throw error;
        }
    }

    /**
     * 설정 변경 브로드캐스트
     */
    async broadcastSettingsChange() {
        try {
            const tabs = await chrome.tabs.query({});
            const message = {
                action: 'updateSettings',
                settings: this.settings
            };

            // 모든 탭에 설정 변경 알림
            const promises = tabs.map(tab => {
                return new Promise((resolve) => {
                    chrome.tabs.sendMessage(tab.id, message, (response) => {
                        // 에러 무시 (content script가 없는 탭도 있음)
                        resolve();
                    });
                });
            });

            await Promise.all(promises);
            console.log('📡 설정 변경 브로드캐스트 완료');
        } catch (error) {
            console.warn('⚠️ 설정 브로드캐스트 실패:', error);
        }
    }

    /**
     * 스토리지 변경 감지 시 호출
     */
    onSettingsChanged(newSettings) {
        if (newSettings) {
            const oldEnabled = this.settings.enabled;
            this.settings = { ...this.settings, ...newSettings };

            // UI 업데이트
            this.updateUI();

            // 상태 변경 로그
            if (oldEnabled !== this.settings.enabled) {
                console.log(`🔄 상태 변경 감지: ${this.settings.enabled ? '활성화' : '비활성화'}`);
            }
        }
    }

    /**
     * 보호 기능 토글 - 개선된 버전
     */
    async toggleProtection() {
        if (this.isLoading) return;

        this.isLoading = true;
        const newState = !this.settings.enabled;

        try {
            // UI 즉시 업데이트 (사용자 피드백)
            this.updateToggleUI(newState);
            this.showLoadingState();

            // 설정 업데이트
            this.settings.enabled = newState;
            await this.saveSettings();

            // 성공 메시지
            this.showMessage(
                newState ? '보호 기능이 활성화되었습니다' : '보호 기능이 비활성화되었습니다'
            );

            console.log(`🔄 보호 기능 토글 완료: ${newState}`);

        } catch (error) {
            console.error('❌ 보호 기능 토글 실패:', error);

            // 실패 시 롤백
            this.settings.enabled = !newState;
            this.updateToggleUI(this.settings.enabled);
            this.showError('설정 변경에 실패했습니다');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    /**
     * 서버 상태 확인
     */
    async checkServerStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch('http://localhost:8000/health', {
                method: 'GET',
                signal: controller.signal,
                headers: { 'Accept': 'application/json' }
            });

            clearTimeout(timeoutId);
            this.serverConnected = response.ok;

            if (this.serverConnected) {
                const data = await response.json();
                this.updateServerStatus(true, data);
                console.log('✅ 서버 연결 성공');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            this.serverConnected = false;
            this.updateServerStatus(false);
            console.warn('⚠️ 서버 연결 실패 - 로컬 모드로 동작');
        }
    }

    /**
     * 실시간 동기화 시작
     */
    startRealTimeSync() {
        // 설정 상태 주기적 확인 (5초마다)
        this.updateInterval = setInterval(async () => {
            try {
                // 현재 저장된 설정과 비교
                const result = await chrome.storage.sync.get(['privacyGuardSettings']);
                const storedSettings = result.privacyGuardSettings;

                if (storedSettings && storedSettings.enabled !== this.settings.enabled) {
                    console.log('🔄 외부 설정 변경 감지, UI 동기화');
                    this.settings = { ...this.settings, ...storedSettings };
                    this.updateUI();
                }

                // 보호 기능이 활성화된 경우 최근 결과 확인
                if (this.settings.enabled) {
                    await this.fetchLastResult();
                }

            } catch (error) {
                console.warn('⚠️ 실시간 동기화 오류:', error);
            }
        }, 5000);

        // 서버 상태 주기적 확인 (30초마다)
        setInterval(() => {
            this.checkServerStatus();
        }, 30000);
    }

    /**
     * UI 업데이트 - 전체
     */
    updateUI() {
        this.updateToggleUI(this.settings.enabled);
        this.updateServerStatus(this.serverConnected);
    }

    /**
     * 토글 UI 업데이트
     */
    updateToggleUI(enabled) {
        if (this.elements.statusToggle) {
            if (enabled) {
                this.elements.statusToggle.classList.add('active');
            } else {
                this.elements.statusToggle.classList.remove('active');
            }
        }
    }

    /**
     * 서버 상태 UI 업데이트
     */
    updateServerStatus(connected, serverData = null) {
        if (this.elements.serverIndicator) {
            this.elements.serverIndicator.classList.toggle('connected', connected);
        }

        if (this.elements.serverText) {
            if (connected) {
                this.elements.serverText.textContent =
                    serverData?.status === 'healthy' ? '서버 연결됨' : '서버 연결됨 (제한적)';
            } else {
                this.elements.serverText.textContent = '로컬 모드';
            }
        }
    }

    /**
     * 최근 결과 가져오기
     */
    async fetchLastResult() {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tabs[0]) return;

            const response = await new Promise((resolve) => {
                chrome.tabs.sendMessage(tabs[0].id, { action: 'getLastResult' }, resolve);
            });

            if (response && response.result) {
                this.lastResult = response.result;
                this.displayResult(this.lastResult);
            }

        } catch (error) {
            console.warn('⚠️ 결과 가져오기 실패:', error);
        }
    }

    /**
     * 결과 표시
     */
    displayResult(result) {
        if (!result || !result.stats) {
            if (this.elements.resultsSection) {
                this.elements.resultsSection.classList.remove('show');
            }
            return;
        }

        const { stats, maskingLog = [] } = result;

        // 통계 업데이트
        if (this.elements.totalEntities) {
            this.elements.totalEntities.textContent = stats.totalEntities || 0;
        }
        if (this.elements.avgRisk) {
            this.elements.avgRisk.textContent = `${stats.avgRisk || 0}%`;
        }
        if (this.elements.resultTime) {
            this.elements.resultTime.textContent = new Date().toLocaleTimeString();
        }

        // 상단 요약 업데이트
        if (this.elements.detectedCount) {
            this.elements.detectedCount.textContent = stats.totalEntities || 0;
        }
        if (this.elements.maskedCount) {
            this.elements.maskedCount.textContent = stats.maskedEntities || 0;
        }

        // 상세 정보 표시
        if (this.elements.entityDetails && maskingLog.length > 0) {
            this.elements.entityDetails.innerHTML = maskingLog.slice(0, 3).map(log => `
                <div class="entity-item">
                    <span class="entity-type">${this.formatEntityType(log.entity)}</span>
                    <span class="entity-text">${this.truncateText(log.token, 10)}</span>
                    <span class="entity-risk">${log.risk_weight || 0}%</span>
                </div>
            `).join('');

            if (maskingLog.length > 3) {
                this.elements.entityDetails.innerHTML += `
                    <div style="text-align: center; color: #666; padding: 8px; font-size: 10px;">
                        +${maskingLog.length - 3}개 더
                    </div>
                `;
            }
        }

        // 결과 섹션 표시
        if (this.elements.resultsSection) {
            this.elements.resultsSection.classList.add('show', 'slide-in');
        }
    }

    /**
     * 로딩 상태 표시
     */
    showLoadingState() {
        if (this.elements.statusToggle) {
            this.elements.statusToggle.style.opacity = '0.6';
            this.elements.statusToggle.style.pointerEvents = 'none';
        }
    }

    hideLoadingState() {
        if (this.elements.statusToggle) {
            this.elements.statusToggle.style.opacity = '';
            this.elements.statusToggle.style.pointerEvents = '';
        }
    }

    /**
     * 메시지 및 에러 처리
     */
    showMessage(message) {
        if (this.elements.serverText) {
            const originalText = this.elements.serverText.textContent;
            const originalColor = this.elements.serverText.style.color;

            this.elements.serverText.textContent = message;
            this.elements.serverText.style.color = '#2ed573';
            this.elements.serverText.style.fontWeight = '600';

            setTimeout(() => {
                this.elements.serverText.textContent = originalText;
                this.elements.serverText.style.color = originalColor;
                this.elements.serverText.style.fontWeight = '';
            }, 2000);
        }
    }

    showError(message) {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
            this.elements.errorMessage.classList.add('show');

            setTimeout(() => {
                this.elements.errorMessage.classList.remove('show');
            }, 5000);
        }
    }

    /**
     * 헬퍼 함수들
     */
    formatEntityType(type) {
        const typeMap = {
            'person': '이름',
            'phone': '연락처',
            'hospital': '병원',
            'disease': '질병',
            'date': '날짜',
            'id_number': '주민번호'
        };
        return typeMap[type] || type?.toUpperCase() || 'UNKNOWN';
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    /**
     * 정리 함수
     */
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// 팝업 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM 준비됨, 개선된 PopupController 초기화');

    try {
        window.popupController = new ImprovedPopupController();
    } catch (error) {
        console.error('❌ 팝업 초기화 실패:', error);

        // Fallback 토글 기능
        const toggle = document.getElementById('statusToggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                toggle.classList.toggle('active');
            });
        }
    }
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', () => {
    if (window.popupController) {
        window.popupController.cleanup();
    }
});

// 디버깅 함수들
window.debugToggle = function() {
    if (window.popupController) {
        window.popupController.toggleProtection();
    }
};

window.debugStatus = function() {
    if (window.popupController) {
        console.log('현재 상태:', window.popupController.settings);
    }
};
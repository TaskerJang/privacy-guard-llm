// extension/popup.js
// 간소화된 팝업 컨트롤러 (CSP 호환)

class SimplifiedPopupController {
    constructor() {
        this.settings = {
            enabled: false,
            mode: 'medical'
        };

        this.elements = {};
        this.isLoading = false;
        this.serverConnected = false;
        this.lastResult = null;

        console.log('🛡️ PopupController 초기화 시작');
        this.init();
    }

    init() {
        this.initElements();
        this.loadSettings();
        this.setupEventListeners();
        this.checkServerStatus();
        this.updateUI();
        this.startPeriodicCheck();

        console.log('🛡️ PopupController 초기화 완료');
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
            } else {
                console.log(`✅ 요소 발견: ${key}`);
            }
        });
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        console.log('🎯 이벤트 리스너 설정 중...');

        if (this.elements.statusToggle) {
            // 클릭 이벤트
            this.elements.statusToggle.addEventListener('click', (e) => {
                console.log('🔄 토글 클릭됨!');
                e.preventDefault();
                e.stopPropagation();
                this.toggleProtection();
            });

            // 키보드 이벤트 (접근성)
            this.elements.statusToggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    console.log('⌨️ 토글 키보드 입력됨!');
                    e.preventDefault();
                    this.toggleProtection();
                }
            });

            // 포커스 가능하도록 설정
            this.elements.statusToggle.setAttribute('tabindex', '0');

            console.log('✅ 토글 이벤트 리스너 설정 완료');
        } else {
            console.error('❌ statusToggle 요소를 찾을 수 없어 이벤트 리스너를 설정할 수 없습니다');
        }
    }

    /**
     * 설정 로드
     */
    async loadSettings() {
        try {
            console.log('📖 설정 로딩 중...');
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            if (result.privacyGuardSettings) {
                this.settings = { ...this.settings, ...result.privacyGuardSettings };
                console.log('✅ 설정 로드 완료:', this.settings);
            } else {
                console.log('ℹ️ 저장된 설정이 없음, 기본값 사용');
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
            console.log('💾 설정 저장 중...', this.settings);
            await chrome.storage.sync.set({ privacyGuardSettings: this.settings });
            console.log('✅ 설정 저장 완료');
        } catch (error) {
            console.error('❌ 설정 저장 실패:', error);
            this.showError('설정을 저장할 수 없습니다');
        }
    }

    /**
     * 보호 기능 토글
     */
    async toggleProtection() {
        console.log('🔄 보호 기능 토글 시작, 현재 상태:', this.settings.enabled);

        if (this.isLoading) {
            console.log('⏳ 이미 처리 중이므로 무시');
            return;
        }

        this.isLoading = true;

        try {
            // 상태 변경
            this.settings.enabled = !this.settings.enabled;

            // 즉시 UI 업데이트 (사용자 피드백)
            this.updateStatusUI();

            console.log('💾 새로운 상태로 설정 저장:', this.settings.enabled);
            await this.saveSettings();

            // 콘텐츠 스크립트에 알림
            console.log('📨 콘텐츠 스크립트에 메시지 전송 중...');
            const response = await this.sendMessageToActiveTab({
                action: 'toggleProtection',
                enabled: this.settings.enabled,
                settings: this.settings
            });

            if (response && response.success) {
                console.log('✅ 콘텐츠 스크립트 응답 성공');
                this.showMessage(
                    this.settings.enabled ? '보호 기능 활성화됨' : '보호 기능 비활성화됨'
                );
            } else {
                console.warn('⚠️ 콘텐츠 스크립트 응답 실패, 하지만 로컬 상태는 변경됨');
                this.showMessage(
                    this.settings.enabled ? '보호 기능 활성화됨 (로컬)' : '보호 기능 비활성화됨 (로컬)'
                );
            }

        } catch (error) {
            console.error('❌ 보호 기능 토글 실패:', error);
            // 실패시 롤백
            this.settings.enabled = !this.settings.enabled;
            await this.saveSettings();
            this.updateStatusUI();
            this.showError('설정 변경에 실패했습니다: ' + error.message);
        } finally {
            this.isLoading = false;
        }

        console.log('🏁 보호 기능 토글 완료, 최종 상태:', this.settings.enabled);
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
                headers: {
                    'Accept': 'application/json'
                }
            });

            clearTimeout(timeoutId);
            this.serverConnected = response.ok;

            if (this.serverConnected) {
                const data = await response.json();
                this.updateServerStatus(true, data);
                this.hideError();
                console.log('✅ 서버 연결 성공:', data.status || 'healthy');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            this.serverConnected = false;
            this.updateServerStatus(false);

            if (error.name === 'AbortError') {
                console.warn('⏱️ 서버 연결 시간 초과');
                this.showError('서버 연결 시간 초과 - 로컬 모드로 동작');
            } else {
                console.warn('❌ 서버 연결 실패:', error.message);
                this.showError('서버 연결 실패 - 로컬 모드로 동작');
            }
        }
    }

    /**
     * 서버 상태 UI 업데이트
     */
    updateServerStatus(connected, serverData = null) {
        this.elements.serverIndicator.classList.toggle('connected', connected);

        if (connected) {
            this.elements.serverText.textContent = serverData?.status === 'healthy' ?
                '서버 연결됨' : '서버 연결됨 (제한적)';
        } else {
            this.elements.serverText.textContent = '로컬 모드';
        }
    }

    /**
     * 활성 탭에 메시지 전송
     */
    async sendMessageToActiveTab(message) {
        try {
            console.log('📤 활성 탭에 메시지 전송:', message);

            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) {
                console.warn('⚠️ 활성 탭을 찾을 수 없음');
                return { success: false, error: '활성 탭을 찾을 수 없습니다' };
            }

            console.log('📋 찾은 탭:', tab.url);

            return new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    console.warn('⏱️ 메시지 전송 시간 초과');
                    resolve({ success: false, error: '메시지 전송 시간 초과' });
                }, 5000);

                chrome.tabs.sendMessage(tab.id, message, (response) => {
                    clearTimeout(timeout);

                    if (chrome.runtime.lastError) {
                        console.warn('⚠️ 메시지 전송 실패:', chrome.runtime.lastError.message);
                        resolve({ success: false, error: chrome.runtime.lastError.message });
                    } else {
                        console.log('📨 메시지 응답 받음:', response);
                        resolve(response || { success: true });
                    }
                });
            });

        } catch (error) {
            console.error('❌ 탭 메시지 오류:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * UI 상태 업데이트
     */
    updateUI() {
        this.updateStatusUI();
    }

    /**
     * 상태 UI 업데이트
     */
    updateStatusUI() {
        console.log('🎨 UI 상태 업데이트:', this.settings.enabled);

        if (this.elements.statusToggle) {
            if (this.settings.enabled) {
                this.elements.statusToggle.classList.add('active');
                console.log('✅ 토글 활성화 스타일 적용');
            } else {
                this.elements.statusToggle.classList.remove('active');
                console.log('❌ 토글 비활성화 스타일 적용');
            }
        } else {
            console.error('❌ statusToggle 요소가 없음');
        }
    }

    /**
     * 최근 결과 가져오기
     */
    async fetchLastResult() {
        if (!this.settings.enabled) return;

        try {
            const response = await this.sendMessageToActiveTab({
                action: 'getLastResult'
            });

            if (response && response.result) {
                this.lastResult = response.result;
                this.displayResult(this.lastResult);
            }

        } catch (error) {
            console.warn('결과 가져오기 실패:', error);
        }
    }

    /**
     * 결과 표시
     */
    displayResult(result) {
        if (!result || !result.stats) {
            this.elements.resultsSection.classList.remove('show');
            return;
        }

        const { stats, maskingLog = [] } = result;

        // 통계 업데이트
        this.elements.totalEntities.textContent = stats.totalEntities || 0;
        this.elements.avgRisk.textContent = `${stats.avgRisk || 0}%`;
        this.elements.resultTime.textContent = new Date().toLocaleTimeString();

        // 상단 요약 업데이트
        this.elements.detectedCount.textContent = stats.totalEntities || 0;
        this.elements.maskedCount.textContent = stats.maskedEntities || 0;

        // 상세 정보 (최대 3개만 표시)
        if (maskingLog && maskingLog.length > 0) {
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
        } else {
            this.elements.entityDetails.innerHTML = `
                <div style="text-align: center; color: #666; padding: 12px; font-size: 11px;">
                    민감정보가 감지되지 않았습니다
                </div>
            `;
        }

        // 결과 섹션 표시
        this.elements.resultsSection.classList.add('show', 'slide-in');
    }

    /**
     * 주기적 업데이트 시작
     */
    startPeriodicCheck() {
        // 서버 상태 체크 (30초마다)
        setInterval(() => {
            this.checkServerStatus();
        }, 30000);

        // 결과 업데이트 (3초마다, 활성화된 경우만)
        setInterval(() => {
            if (this.settings.enabled) {
                this.fetchLastResult();
            }
        }, 3000);
    }

    /**
     * 에러 메시지 표시
     */
    showError(message) {
        console.error('🚨 에러 표시:', message);

        this.elements.errorMessage.textContent = message;
        this.elements.errorMessage.classList.add('show');

        // 5초 후 자동 숨김
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    /**
     * 에러 메시지 숨김
     */
    hideError() {
        this.elements.errorMessage.classList.remove('show');
    }

    /**
     * 임시 메시지 표시 (서버 텍스트 영역 활용)
     */
    showMessage(message) {
        console.log('💬 메시지 표시:', message);

        const originalText = this.elements.serverText.textContent;
        const originalColor = this.elements.serverText.style.color;
        const originalWeight = this.elements.serverText.style.fontWeight;

        this.elements.serverText.textContent = message;
        this.elements.serverText.style.color = '#2ed573';
        this.elements.serverText.style.fontWeight = '600';

        setTimeout(() => {
            this.elements.serverText.textContent = originalText;
            this.elements.serverText.style.color = originalColor;
            this.elements.serverText.style.fontWeight = originalWeight;
        }, 2000);
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
}

// 팝업 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM 준비됨, PopupController 초기화 시작');

    try {
        window.popupController = new SimplifiedPopupController();
        console.log('✅ PopupController 인스턴스 생성 완료');
    } catch (error) {
        console.error('❌ 팝업 초기화 실패:', error);

        // 기본 에러 표시
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = '초기화 중 오류가 발생했습니다: ' + error.message;
            errorDiv.classList.add('show');
        }

        // 수동으로 토글 기능 추가 (fallback)
        const toggle = document.getElementById('statusToggle');
        if (toggle) {
            console.log('🔧 Fallback 토글 기능 추가');
            toggle.addEventListener('click', () => {
                console.log('🔄 Fallback 토글 클릭됨');
                toggle.classList.toggle('active');
            });
        }
    }
});

// 전역 에러 핸들러
window.addEventListener('error', (event) => {
    console.error('🌍 팝업 전역 오류:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('🌍 팝업 Promise 거부:', event.reason);
});

// 디버깅용 전역 함수
window.debugToggle = function() {
    const toggle = document.getElementById('statusToggle');
    if (toggle) {
        console.log('🐛 디버그 토글 실행');
        toggle.click();
    } else {
        console.error('🐛 토글 요소를 찾을 수 없음');
    }
};

window.debugElements = function() {
    const elements = [
        'statusToggle', 'detectedCount', 'maskedCount',
        'serverIndicator', 'serverText', 'errorMessage'
    ];

    elements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`🐛 ${id}:`, element ? '존재함' : '없음', element);
    });
};
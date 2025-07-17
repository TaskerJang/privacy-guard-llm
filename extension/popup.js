// extension/popup.js
// 개선된 팝업 UI 컨트롤러

class PopupController {
    constructor() {
        this.settings = {
            enabled: false,
            threshold: 50,
            mode: 'medical'
        };

        this.elements = {};
        this.isLoading = false;

        this.init();
    }

    init() {
        this.initElements();
        this.loadSettings();
        this.setupEventListeners();
        this.checkServerStatus();
        this.updateUI();
    }

    /**
     * DOM 요소 초기화
     */
    initElements() {
        this.elements = {
            // 상태 관련
            statusToggle: document.getElementById('statusToggle'),
            detectedCount: document.getElementById('detectedCount'),
            maskedCount: document.getElementById('maskedCount'),
            riskLevel: document.getElementById('riskLevel'),

            // 서버 상태
            serverStatus: document.getElementById('serverStatus'),
            serverIndicator: document.getElementById('serverIndicator'),
            serverText: document.getElementById('serverText'),
            reconnectBtn: document.getElementById('reconnectBtn'),

            // 설정
            thresholdSlider: document.getElementById('thresholdSlider'),
            thresholdValue: document.getElementById('thresholdValue'),
            modeOptions: document.querySelectorAll('.mode-option'),

            // 액션 버튼
            scanBtn: document.getElementById('scanBtn'),
            testBtn: document.getElementById('testBtn'),

            // 결과
            resultsSection: document.getElementById('resultsSection'),
            resultTime: document.getElementById('resultTime'),
            totalEntities: document.getElementById('totalEntities'),
            maskedEntities: document.getElementById('maskedEntities'),
            avgRisk: document.getElementById('avgRisk'),
            entityDetails: document.getElementById('entityDetails')
        };
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 상태 토글
        this.elements.statusToggle.addEventListener('click', () => {
            this.toggleProtection();
        });

        // 임계값 슬라이더
        this.elements.thresholdSlider.addEventListener('input', (e) => {
            this.updateThreshold(parseInt(e.target.value));
        });

        // 모드 선택
        this.elements.modeOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.selectMode(option.dataset.mode);
            });
        });

        // 액션 버튼들
        this.elements.scanBtn.addEventListener('click', () => {
            this.scanCurrentPage();
        });

        this.elements.testBtn.addEventListener('click', () => {
            this.testConnection();
        });

        this.elements.reconnectBtn.addEventListener('click', () => {
            this.reconnectServer();
        });
    }

    /**
     * 설정 로드
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            if (result.privacyGuardSettings) {
                this.settings = { ...this.settings, ...result.privacyGuardSettings };
            }
        } catch (error) {
            console.warn('설정 로드 실패:', error);
        }
    }

    /**
     * 설정 저장
     */
    async saveSettings() {
        try {
            await chrome.storage.sync.set({ privacyGuardSettings: this.settings });
        } catch (error) {
            console.warn('설정 저장 실패:', error);
        }
    }

    /**
     * 보호 기능 토글
     */
    async toggleProtection() {
        this.settings.enabled = !this.settings.enabled;
        await this.saveSettings();

        // 콘텐츠 스크립트에 알림
        this.sendMessageToActiveTab({
            action: 'toggleProtection',
            enabled: this.settings.enabled
        });

        this.updateStatusUI();
        this.showToast(this.settings.enabled ? '보호 기능 활성화됨' : '보호 기능 비활성화됨');
    }

    /**
     * 임계값 업데이트
     */
    async updateThreshold(value) {
        this.settings.threshold = value;
        this.elements.thresholdValue.textContent = value;
        await this.saveSettings();

        this.sendMessageToActiveTab({
            action: 'updateSettings',
            settings: this.settings
        });
    }

    /**
     * 모드 선택
     */
    async selectMode(mode) {
        this.settings.mode = mode;
        await this.saveSettings();

        // UI 업데이트
        this.elements.modeOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.mode === mode);
        });

        this.sendMessageToActiveTab({
            action: 'updateSettings',
            settings: this.settings
        });
    }

    /**
     * 현재 페이지 스캔
     */
    async scanCurrentPage() {
        if (this.isLoading) return;

        this.setLoading(true, '페이지 스캔 중...');

        try {
            const response = await this.sendMessageToActiveTab({
                action: 'scanPage'
            });

            if (response && response.success) {
                this.displayScanResults(response);
                this.showToast('스캔 완료');
            } else {
                throw new Error(response?.error || '스캔 실패');
            }
        } catch (error) {
            console.error('스캔 오류:', error);
            this.showToast('스캔 중 오류 발생', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 연결 테스트
     */
    async testConnection() {
        if (this.isLoading) return;

        this.setLoading(true, '연결 테스트 중...');

        try {
            const response = await fetch('http://localhost:8000/health');
            const data = await response.json();

            this.updateServerStatus(true);
            this.showToast('서버 연결 성공');

            // 테스트 요청
            const testResponse = await fetch('http://localhost:8000/api/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (testResponse.ok) {
                this.showToast('모델 테스트 완료');
            }

        } catch (error) {
            console.error('연결 테스트 실패:', error);
            this.updateServerStatus(false);
            this.showToast('서버 연결 실패', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 서버 재연결
     */
    async reconnectServer() {
        await this.checkServerStatus();
    }

    /**
     * 서버 상태 확인
     */
    async checkServerStatus() {
        try {
            const response = await fetch('http://localhost:8000/health', {
                method: 'GET',
                timeout: 3000
            });

            this.updateServerStatus(response.ok);
        } catch (error) {
            this.updateServerStatus(false);
        }
    }

    /**
     * 서버 상태 UI 업데이트
     */
    updateServerStatus(connected) {
        this.elements.serverIndicator.classList.toggle('connected', connected);
        this.elements.serverText.textContent = connected ?
            '서버 연결됨' : '서버 연결 안됨';

        // 버튼 상태
        this.elements.scanBtn.disabled = !connected || !this.settings.enabled;
        this.elements.testBtn.disabled = false; // 테스트는 항상 가능
    }

    /**
     * 스캔 결과 표시
     */
    displayScanResults(response) {
        const { stats, maskingLog = [] } = response;

        // 통계 업데이트
        this.elements.totalEntities.textContent = stats.totalEntities || 0;
        this.elements.maskedEntities.textContent = stats.maskedEntities || 0;
        this.elements.avgRisk.textContent = `${stats.avgRisk || 0}%`;
        this.elements.resultTime.textContent = new Date().toLocaleTimeString();

        // 상단 요약 업데이트
        this.elements.detectedCount.textContent = stats.totalEntities || 0;
        this.elements.maskedCount.textContent = stats.maskedEntities || 0;
        this.elements.riskLevel.textContent = `${stats.avgRisk || 0}%`;

        // 상세 정보
        if (maskingLog && maskingLog.length > 0) {
            this.elements.entityDetails.innerHTML = maskingLog.map(log => `
                <div class="entity-item">
                    <span class="entity-type">${log.entity || 'UNKNOWN'}</span>
                    <span class="entity-text">${log.token || ''}</span>
                    <span class="entity-risk">${log.risk_weight || 0}%</span>
                </div>
            `).join('');
        } else {
            this.elements.entityDetails.innerHTML = `
                <div style="text-align: center; color: #666; padding: 20px;">
                    민감정보가 감지되지 않았습니다
                </div>
            `;
        }

        // 결과 섹션 표시
        this.elements.resultsSection.classList.add('show', 'slide-in');
    }

    /**
     * UI 상태 업데이트
     */
    updateUI() {
        this.updateStatusUI();
        this.updateControlsUI();
    }

    updateStatusUI() {
        this.elements.statusToggle.classList.toggle('active', this.settings.enabled);
    }

    updateControlsUI() {
        this.elements.thresholdSlider.value = this.settings.threshold;
        this.elements.thresholdValue.textContent = this.settings.threshold;

        this.elements.modeOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.mode === this.settings.mode);
        });
    }

    /**
     * 로딩 상태 설정
     */
    setLoading(loading, message = '') {
        this.isLoading = loading;

        const buttons = [this.elements.scanBtn, this.elements.testBtn];
        buttons.forEach(btn => {
            btn.disabled = loading;
            if (loading) {
                btn.innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>${message}</span>
                    </div>
                `;
            } else {
                // 원래 텍스트로 복원
                if (btn === this.elements.scanBtn) {
                    btn.innerHTML = '🔍 현재 페이지 스캔';
                } else if (btn === this.elements.testBtn) {
                    btn.innerHTML = '🧪 연결 테스트';
                }
            }
        });
    }

    /**
     * 활성 탭에 메시지 전송
     */
    async sendMessageToActiveTab(message) {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) throw new Error('활성 탭을 찾을 수 없습니다');

            return new Promise((resolve) => {
                chrome.tabs.sendMessage(tab.id, message, (response) => {
                    if (chrome.runtime.lastError) {
                        console.warn('메시지 전송 실패:', chrome.runtime.lastError);
                        resolve(null);
                    } else {
                        resolve(response);
                    }
                });
            });
        } catch (error) {
            console.error('탭 메시지 오류:', error);
            return null;
        }
    }

    /**
     * 토스트 메시지 표시
     */
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#e74c3c' : '#2ed573'};
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 12px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }
}

// 팝업 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new PopupController();
});
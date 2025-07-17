// extension/content.js
// 개선된 콘텐츠 스크립트 - UI/UX 개선 및 간소화

console.log("🟢 Privacy Guard Content Script 로드됨");

class PrivacyGuardUI {
    constructor() {
        this.supportedSites = {
            "localhost": { selector: "#chatInput", type: "demo" },
            "chat.openai.com": { selector: '#prompt-textarea, [data-testid="textbox"]', type: "chatgpt" },
            "claude.ai": { selector: '[contenteditable="true"]', type: "claude" },
            "bard.google.com": { selector: 'rich-textarea', type: "bard" }
        };

        this.currentSite = this.detectSite();
        this.isEnabled = false;
        this.monitoredInputs = new Set();

        // UI 상태
        this.warningTimeout = null;
        this.currentWarning = null;
        this.isProcessing = false;

        this.init();
    }

    detectSite() {
        const hostname = window.location.hostname;
        return this.supportedSites[hostname] || null;
    }

    init() {
        if (!this.currentSite) {
            console.log("⚠️ 지원하지 않는 사이트");
            return;
        }

        console.log(`🛡️ Privacy Guard 초기화: ${this.currentSite.type}`);

        this.loadSettings();
        this.setupInputMonitoring();
        this.injectUI();
        this.setupMessageListener();
    }

    /**
     * 입력 필드 모니터링 설정
     */
    setupInputMonitoring() {
        // DOM 변화 감지
        const observer = new MutationObserver(() => {
            this.attachToInputs();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        this.attachToInputs();
    }

    /**
     * 입력 필드에 이벤트 리스너 연결
     */
    attachToInputs() {
        const inputs = document.querySelectorAll(this.currentSite.selector);

        inputs.forEach(input => {
            if (this.monitoredInputs.has(input)) return;

            this.monitoredInputs.add(input);

            // 실시간 입력 감지
            input.addEventListener('input', (e) => {
                if (!this.isEnabled) return;
                this.handleRealTimeInput(e.target);
            });

            // 전송 시도 감지
            input.addEventListener('keydown', (e) => {
                if (!this.isEnabled) return;
                if (e.key === 'Enter' && !e.shiftKey) {
                    this.handleSubmitAttempt(e, input);
                }
            });

            console.log(`📝 입력 필드 모니터링 시작: ${this.currentSite.type}`);
        });
    }

    /**
     * 실시간 입력 처리
     */
    async handleRealTimeInput(input) {
        const text = this.getInputText(input);

        if (!text || text.length < 5) {
            this.hideWarning();
            return;
        }

        // 디바운싱
        clearTimeout(this.warningTimeout);
        this.warningTimeout = setTimeout(async () => {
            try {
                const analysis = await window.privacyClient.quickAnalyze(text);

                if (analysis.hasRisk && analysis.riskLevel > 30) {
                    this.showRealTimeWarning(analysis, input);
                } else {
                    this.hideWarning();
                }
            } catch (error) {
                console.warn('실시간 분석 오류:', error);
            }
        }, 500);
    }

    /**
     * 전송 시도 처리
     */
    async handleSubmitAttempt(event, input) {
        const text = this.getInputText(input);

        if (!text) return;

        try {
            this.showProcessingIndicator();

            const result = await window.privacyClient.maskText(text);

            this.hideProcessingIndicator();

            if (result.success && result.stats.maskedEntities > 0) {
                // 고위험 정보 감지시 차단
                if (result.stats.avgRisk > 70) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.showBlockDialog(result, input);
                    return;
                }

                // 중위험 정보 감지시 경고
                if (result.stats.avgRisk > 40) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.showMaskingDialog(result, input);
                    return;
                }
            }

        } catch (error) {
            this.hideProcessingIndicator();
            console.error('전송 분석 오류:', error);
            this.showErrorToast('분석 중 오류가 발생했습니다');
        }
    }

    /**
     * 실시간 경고 표시
     */
    showRealTimeWarning(analysis, input) {
        this.hideWarning();

        const warning = document.createElement('div');
        warning.className = 'privacy-warning-realtime';
        warning.innerHTML = `
            <div class="warning-content">
                <div class="warning-header">
                    <span class="warning-icon">⚠️</span>
                    <span class="warning-title">민감정보 감지</span>
                    <span class="risk-badge risk-${this.getRiskLevel(analysis.riskLevel)}">${analysis.riskLevel}%</span>
                </div>
                <div class="warning-message">
                    ${analysis.entityCount}개의 민감정보가 감지되었습니다
                </div>
            </div>
        `;

        // 입력 필드 근처에 배치
        const inputRect = input.getBoundingClientRect();
        warning.style.position = 'fixed';
        warning.style.top = `${inputRect.bottom + 5}px`;
        warning.style.left = `${inputRect.left}px`;
        warning.style.zIndex = '10000';

        document.body.appendChild(warning);
        this.currentWarning = warning;
    }

    /**
     * 차단 대화상자 표시
     */
    showBlockDialog(result, input) {
        const dialog = document.createElement('div');
        dialog.className = 'privacy-dialog-overlay';
        dialog.innerHTML = `
            <div class="privacy-dialog">
                <div class="dialog-header">
                    <h3>🚫 전송 차단됨</h3>
                    <p>고위험 민감정보가 감지되어 전송을 차단했습니다</p>
                </div>
                
                <div class="risk-analysis">
                    <div class="risk-meter">
                        <div class="risk-bar" style="width: ${result.stats.avgRisk}%"></div>
                        <span class="risk-label">위험도: ${result.stats.avgRisk}%</span>
                    </div>
                </div>

                <div class="detected-info">
                    <h4>감지된 정보 (${result.stats.maskedEntities}/${result.stats.totalEntities})</h4>
                    <div class="entity-list">
                        ${result.maskingLog.map(log => `
                            <div class="entity-item">
                                <span class="entity-type">${log.entity}</span>
                                <span class="entity-text">${log.token}</span>
                                <span class="entity-risk">${log.risk_weight}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="dialog-actions">
                    <button class="btn btn-primary" onclick="privacyGuard.applyMasking('${input.id}', ${JSON.stringify(result).replace(/"/g, '&quot;')})">
                        🎭 마스킹 후 전송
                    </button>
                    <button class="btn btn-secondary" onclick="privacyGuard.editMessage()">
                        ✏️ 수정하기
                    </button>
                    <button class="btn btn-danger" onclick="privacyGuard.forceSubmit('${input.id}')">
                        ⚠️ 무시하고 전송
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);
        this.currentDialog = dialog;
    }

    /**
     * 처리 중 표시
     */
    showProcessingIndicator() {
        if (this.isProcessing) return;

        this.isProcessing = true;
        const indicator = document.createElement('div');
        indicator.id = 'privacy-processing';
        indicator.innerHTML = `
            <div class="processing-content">
                <div class="spinner"></div>
                <span>민감정보 분석 중...</span>
            </div>
        `;

        document.body.appendChild(indicator);
    }

    hideProcessingIndicator() {
        this.isProcessing = false;
        const indicator = document.getElementById('privacy-processing');
        if (indicator) indicator.remove();
    }

    /**
     * UI 주입
     */
    injectUI() {
        this.injectStyles();
        this.injectStatusBar();
    }

    injectStatusBar() {
        const statusBar = document.createElement('div');
        statusBar.id = 'privacy-status-bar';
        statusBar.innerHTML = `
            <div class="status-content">
                <span class="status-icon">🛡️</span>
                <span class="status-text">Privacy Guard</span>
                <span class="site-type">${this.currentSite.type}</span>
                <div class="status-indicator ${this.isEnabled ? 'active' : 'inactive'}"></div>
            </div>
        `;

        document.body.appendChild(statusBar);
    }

    injectStyles() {
        if (document.querySelector('#privacy-guard-styles')) return;

        const style = document.createElement('style');
        style.id = 'privacy-guard-styles';
        style.textContent = `
            /* Status Bar */
            #privacy-status-bar {
                position: fixed;
                top: 10px;
                right: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                z-index: 9999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }

            .status-content {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #ff4757;
            }

            .status-indicator.active {
                background: #2ed573;
                animation: pulse 2s infinite;
            }

            /* Real-time Warning */
            .privacy-warning-realtime {
                background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
                border: 1px solid #e17055;
                border-radius: 8px;
                padding: 12px;
                max-width: 300px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                animation: slideIn 0.3s ease;
            }

            .warning-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 4px;
            }

            .risk-badge {
                background: #e17055;
                color: white;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 10px;
                margin-left: auto;
            }

            /* Dialog */
            .privacy-dialog-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10001;
            }

            .privacy-dialog {
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }

            .dialog-header h3 {
                margin: 0 0 8px 0;
                color: #e17055;
            }

            .risk-meter {
                background: #ecf0f1;
                border-radius: 10px;
                height: 20px;
                position: relative;
                margin: 16px 0;
            }

            .risk-bar {
                background: linear-gradient(90deg, #2ed573, #ffa726, #e74c3c);
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            }

            .entity-list {
                max-height: 200px;
                overflow-y: auto;
                margin: 12px 0;
            }

            .entity-item {
                display: flex;
                justify-content: space-between;
                padding: 8px;
                background: #f8f9fa;
                margin: 4px 0;
                border-radius: 6px;
                font-size: 14px;
            }

            .dialog-actions {
                display: flex;
                gap: 12px;
                margin-top: 20px;
            }

            .btn {
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .btn-primary { background: #667eea; color: white; }
            .btn-secondary { background: #95a5a6; color: white; }
            .btn-danger { background: #e74c3c; color: white; }

            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }

            /* Processing */
            #privacy-processing {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                z-index: 10002;
            }

            .processing-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #ecf0f1;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes slideIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * 헬퍼 메서드들
     */
    getInputText(input) {
        return input.contentEditable === 'true' ? input.innerText : input.value;
    }

    setInputText(input, text) {
        if (input.contentEditable === 'true') {
            input.innerText = text;
        } else {
            input.value = text;
        }
    }

    getRiskLevel(risk) {
        if (risk >= 80) return 'high';
        if (risk >= 50) return 'medium';
        return 'low';
    }

    hideWarning() {
        if (this.currentWarning) {
            this.currentWarning.remove();
            this.currentWarning = null;
        }
    }

    hideDialog() {
        if (this.currentDialog) {
            this.currentDialog.remove();
            this.currentDialog = null;
        }
    }

    showErrorToast(message) {
        const toast = document.createElement('div');
        toast.className = 'privacy-error-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #e74c3c;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 10003;
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    /**
     * 액션 핸들러들
     */
    async applyMasking(inputId, result) {
        const input = document.getElementById(inputId);
        if (input && result.maskedText) {
            this.setInputText(input, result.maskedText);
        }
        this.hideDialog();
    }

    editMessage() {
        this.hideDialog();
    }

    forceSubmit(inputId) {
        this.hideDialog();
        const input = document.getElementById(inputId);
        if (input) {
            // 전송 로직 실행
            const event = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                bubbles: true
            });
            input.dispatchEvent(event);
        }
    }

    /**
     * 설정 관리
     */
    loadSettings() {
        chrome.storage?.sync?.get(['privacyGuardSettings'], (result) => {
            if (result.privacyGuardSettings) {
                this.isEnabled = result.privacyGuardSettings.enabled || false;
                this.updateStatusUI();
            }
        });
    }

    updateStatusUI() {
        const indicator = document.querySelector('.status-indicator');
        if (indicator) {
            indicator.className = `status-indicator ${this.isEnabled ? 'active' : 'inactive'}`;
        }
    }

    /**
     * 메시지 리스너
     */
    setupMessageListener() {
        chrome.runtime?.onMessage?.addListener((request, sender, sendResponse) => {
            switch (request.action) {
                case 'toggleProtection':
                    this.isEnabled = request.enabled;
                    this.updateStatusUI();
                    break;

                case 'scanPage':
                    this.handlePageScan(sendResponse);
                    return true; // 비동기 응답
            }
        });
    }

    async handlePageScan(sendResponse) {
        try {
            const inputs = document.querySelectorAll(this.currentSite.selector);
            let totalText = '';

            inputs.forEach(input => {
                totalText += this.getInputText(input) + ' ';
            });

            if (totalText.trim()) {
                const result = await window.privacyClient.maskText(totalText);
                sendResponse({
                    success: true,
                    stats: result.stats,
                    hasContent: true
                });
            } else {
                sendResponse({
                    success: true,
                    stats: { totalEntities: 0, maskedEntities: 0, avgRisk: 0 },
                    hasContent: false
                });
            }
        } catch (error) {
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }
}

// 전역 인스턴스 생성
window.privacyGuard = new PrivacyGuardUI();
// content.js 최상단, 클래스 정의 전에
window.addEventListener('load', () => {
    // 데모 모드면 자동 활성화
    if (window.privacyGuard && window.privacyGuard.currentSite?.type === 'demo') {
        window.privacyGuard.isEnabled = true;
        window.privacyGuard.updateStatusUI();
        console.log('🟢 [content.js] 데모 모드 자동 활성화 완료');
    }
});


console.log("🟢 [content.js] loaded");

class EnhancedPrivacyGuard {
    constructor() {
        this.supportedSites = {
            "": { selector: "#chatInput", type: "demo" },
            "localhost": { selector: "#chatInput", type: "demo" },
            "chat.openai.com": { selector: '#prompt-textarea, [data-testid="textbox"]', type: 'chatgpt' },
            "claude.ai": { selector: '[contenteditable="true"]', type: 'claude' },
            "bard.google.com": { selector: 'rich-textarea', type: 'bard' },
            "copilot.microsoft.com": { selector: '[data-testid="textbox"]', type: 'copilot' }
        };

        this.currentSite = this.detectSite();
        this.isEnabled = false;
        this.interceptedInputs = new Set();

        this.init();
    }

    detectSite() {
        const hostname = window.location.hostname;
        return this.supportedSites[hostname] || null;
    }

    init() {
        if (!this.currentSite) {
            console.log("⚠️ 지원하지 않는 사이트입니다.");
            return;
        }
        console.log(`🛡️ Privacy Guard 활성화: ${this.currentSite.type}`);
        this.setupRealTimeMonitoring();
        this.injectWarningUI();
        this.loadSettings();
    }

    setupRealTimeMonitoring() {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    this.attachToInputs();
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
        this.attachToInputs();
    }

    attachToInputs() {
        const inputs = document.querySelectorAll(this.currentSite.selector);
        inputs.forEach(input => {
            if (this.interceptedInputs.has(input)) return;
            this.interceptedInputs.add(input);

            input.addEventListener('input', e => {
                if (!this.isEnabled) return;
                this.handleRealTimeInput(e.target);
            });

            input.addEventListener('keydown', e => {
                if (!this.isEnabled) return;
                if (e.key === 'Enter' && !e.shiftKey) {
                    this.handleSubmitAttempt(e, input);
                }
            });

            this.interceptSubmitButtons(input);
        });
    }

    async handleRealTimeInput(input) {
        const text = this.getInputText(input);
        if (!text.trim()) {
            this.hideWarning();
            return;
        }
        clearTimeout(this.analysisTimeout);
        this.analysisTimeout = setTimeout(async () => {
            const result = await this.analyzeText(text);
            result.hasSensitiveInfo ? this.showRealTimeWarning(result, input) : this.hideWarning();
        }, 300);
    }

    async handleSubmitAttempt(event, input) {
        const text = this.getInputText(input);
        const result = await this.analyzeText(text);
        if (result.hasSensitiveInfo && result.overallRisk > 70) {
            event.preventDefault();
            event.stopPropagation();
            this.showBlockDialog(result, input);
        }
    }

    getInputText(input) {
        return input.contentEditable === 'true' ? input.innerText : input.value;
    }

    setInputText(input, text) {
        if (input.contentEditable === 'true') input.innerText = text;
        else input.value = text;
    }

    async analyzeText(text) {
        return new Promise(resolve => {
            chrome.runtime.sendMessage({ action: 'mask', text }, response => {
                resolve(response && !response.error ? response : this.basicAnalysis(text));
            });
        });
    }

    basicAnalysis(text) {
        const patterns = [
            { pattern: /[가-힣]{2,4}(?:\s*\([^)]*\))?/g, type: 'PERSON', risk: 85 },
            { pattern: /010-\d{4}-\d{4}/g, type: 'CONTACT', risk: 95 },
            { pattern: /\d{6}-\d{7}/g, type: 'SSN', risk: 99 },
            { pattern: /(서울대|연세|고려대|성균관대|한양대|중앙대|경희대|이화여대|부산대|경북대)(?:병원|의료원|의과대학)/g, type: 'HOSPITAL', risk: 70 },
            { pattern: /(암|당뇨|고혈압|심장병|뇌졸중|간염|결핵|우울증)/g, type: 'DISEASE', risk: 60 }
        ];
        const detected = [];
        let maxRisk = 0;
        patterns.forEach(p => {
            const matches = text.match(p.pattern);
            matches?.forEach(match => {
                detected.push({ text: match, type: p.type, risk: p.risk });
                maxRisk = Math.max(maxRisk, p.risk);
            });
        });
        return {
            hasSensitiveInfo: !!detected.length,
            detectedItems: detected,
            maxRisk,
            overallRisk: detected.length > 2 ? Math.min(maxRisk + 10, 99) : maxRisk,
            maskedText: this.maskText(text, detected)
        };
    }

    maskText(text, detectedItems) {
        return detectedItems.reduce(
            (acc, item) => acc.replace(item.text, `[${item.type}]`),
            text
        );
    }

    async showRealTimeWarning(result, input) {
        // 1) 기존 DOM 가져오기
        const warning = document.getElementById('privacyWarning');
        const itemsContainer = document.getElementById('detectedItems');
        const typing = document.getElementById('typingIndicator');

        // 2) 탐지된 태그를 렌더링
        itemsContainer.innerHTML = result.detectedItems
            .map(item => `<span class="detected-item">${item.type}: ${item.text} (${item.risk}%)</span>`)
            .join('');

        // 3) 토글 클래스만으로 보이게
        warning.classList.add('show');

        // 4) 입력 중 표시 숨기기
        typing.style.display = 'none';
    }


    showBlockDialog(result, input) {
        const dialog = document.createElement('div');
        dialog.className = 'privacy-guard-block-dialog';
        dialog.innerHTML = `
      <div class="dialog-overlay"></div>
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>🚫 전송 차단</h3>
          <p>고위험 민감정보가 감지되어 전송을 차단했습니다.</p>
        </div>
        <div class="risk-analysis">
          <div class="risk-meter">
            <div class="risk-bar" style="width: ${result.overallRisk}%"></div>
            <span class="risk-label">위험도: ${result.overallRisk}%</span>
          </div>
        </div>
        <div class="detected-details">
          <h4>감지된 민감정보:</h4>
          <ul>
            ${result.detectedItems.map(item => `<li><strong>${item.type}:</strong> ${item.text} (${item.risk}%)</li>`).join('')}
          </ul>
        </div>
        <div class="dialog-actions">
          <button class="action-btn primary" onclick="privacyGuard.handleMaskAndSend('${input.id}')">🎭 마스킹 후 전송</button>
          <button class="action-btn secondary" onclick="privacyGuard.handleEditMessage('${input.id}')">✏️ 수정하기</button>
          <button class="action-btn danger" onclick="privacyGuard.handleForceSkip('${input.id}')">⚠️ 무시하고 전송</button>
        </div>
      </div>
    `;
        document.body.appendChild(dialog);
        this.currentDialog = dialog;
    }

    handleMaskAndSend(inputId) {
        const input = document.getElementById(inputId);
        this.analyzeText(this.getInputText(input)).then(result => {
            this.setInputText(input, result.maskedText);
            this.hideDialog();
            this.triggerSubmit(input);
        });
    }

    handleEditMessage(inputId) {
        const input = document.getElementById(inputId);
        input.focus();
        this.hideDialog();
    }

    handleForceSkip(inputId) {
        const input = document.getElementById(inputId);
        this.hideDialog();
        this.triggerSubmit(input);
    }

    triggerSubmit(input) {
        const btn = this.findSubmitButton(input);
        if (btn) btn.click();
        else input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
    }

    findSubmitButton(input) {
        return ['[data-testid="send-button"]','button[aria-label="Send message"]','button[title="Send message"]','.send-button','[aria-label="전송"]']
            .map(sel => document.querySelector(sel))
            .find(el => el);
    }

    interceptSubmitButtons(input) {
        const btn = this.findSubmitButton(input);
        if (btn && !btn.dataset.privacyGuardIntercepted) {
            btn.dataset.privacyGuardIntercepted = 'true';
            btn.addEventListener('click', e => {
                if (!this.isEnabled) return;
                this.analyzeText(this.getInputText(input)).then(result => {
                    if (result.hasSensitiveInfo && result.overallRisk > 70) {
                        e.preventDefault(); e.stopPropagation(); this.showBlockDialog(result, input);
                    }
                });
            }, true);
        }
    }

    injectWarningUI() {
        const statusBar = document.createElement('div');
        statusBar.id = 'privacy-guard-status';
        statusBar.innerHTML = `
      <div class="status-content">
        <span class="status-icon">🛡️</span>
        <span class="status-text">Privacy Guard 활성화됨</span>
        <span class="site-type">${this.currentSite.type.toUpperCase()}</span>
      </div>
    `;
        document.body.appendChild(statusBar);
        this.injectStatusStyles();
    }

    injectStatusStyles() {
        const style = document.createElement('style');
        style.textContent = `#privacy-guard-status {position:fixed;top:0;right:0;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:8px 16px;border-radius:0 0 0 8px;z-index:9999;font-size:12px;font-weight:600;box-shadow:0 2px 10px rgba(0,0,0,0.2);} .status-content {display:flex;align-items:center;gap:8px;} .site-type {background:rgba(255,255,255,0.2);padding:2px 6px;border-radius:4px;font-size:10px;}`;
        document.head.appendChild(style);
    }

    injectWarningStyles() {
        if (document.querySelector('#privacy-guard-warning-styles')) return;
        const style = document.createElement('style');
        style.id = 'privacy-guard-warning-styles';
        style.textContent = `.privacy-guard-realtime-warning {background:#fff3cd;border:1px solid #ffeaa7;border-radius:8px;padding:12px;max-width:400px;box-shadow:0 4px 12px rgba(0,0,0,0.15);animation:slideIn 0.3s ease;} .warning-header {display:flex;align-items:center;gap:8px;margin-bottom:8px;} .warning-icon {font-size:18px;} .warning-title {font-weight:600;color:#856404;} .risk-score {margin-left:auto;background:#ff6b6b;color:white;padding:2px 8px;border-radius:12px;font-size:11px;} .detected-items {margin:8px 0;display:flex;flex-wrap:wrap;gap:4px;} .detected-tag {background:#ff6b6b;color:white;padding:2px 6px;border-radius:10px;font-size:10px;font-weight:500;} .warning-actions {display:flex;gap:8px;margin-top:8px;} .action-btn {padding:6px 12px;border:none;border-radius:4px;font-size:12px;cursor:pointer;font-weight:500;} .mask-btn {background:#667eea;color:white;} .clear-btn {background:#6c757d;color:white;} @keyframes slideIn {from {opacity:0;transform:translateY(-10px);} to {opacity:1;transform:translateY(0);}}`;
        document.head.appendChild(style);
    }

    hideWarning() { this.currentWarning?.remove(); this.currentWarning = null; }
    hideDialog() { this.currentDialog?.remove(); this.currentDialog = null; }
    loadSettings() {
        if (!chrome.storage || !chrome.storage.sync) return;
        chrome.storage.sync.get(['privacyGuardSettings'], result => {
            this.isEnabled = result.privacyGuardSettings?.enabled;
            this.updateStatusUI();
        });
    }

    // 설정 변경 메시지 처리
    handleMessage(request, sender, sendResponse) {
        switch (request.action) {
            case 'toggleProtection':
                this.isEnabled = request.enabled;
                this.updateStatusUI();
                break;
            case 'updateSettings':
                this.loadSettings();
                break;

            case 'scanPage':
                if (!this.isEnabled) {
                    sendResponse({ success: false });
                    break;
                }
                // textarea 텍스트 가져와서 background에 요청
                const text = document.getElementById('chatInput')?.value || '';
                chrome.runtime.sendMessage({ action: 'mask', text }, result => {
                    // 받은 결과를 다시 popup으로 포워딩
                    const stats = {
                        totalEntities: result.stats?.total_entities ?? 0,
                        maskedEntities: result.stats?.masked_entities ?? 0,
                        avgRisk: result.stats?.avg_risk ?? 0
                    };
                    sendResponse({ success: true, stats });
                    // 그리고 화면(데모페이지)에도 마스킹 적용
                    if (this.currentSite.type === 'demo' && result.masked_text) {
                        document.getElementById('chatInput').value = result.masked_text;
                    }
                });
                return true;  // 비동기 sendResponse
        }
    }

    // 상태 표시 업데이트
    updateStatusUI() {
        const statusBar = document.getElementById('privacy-guard-status');
        if (statusBar) statusBar.style.display = this.isEnabled ? 'block' : 'none';
    }
} // 클래스 끝

// 전역 인스턴스 생성
window.privacyGuard = new EnhancedPrivacyGuard();

// Chrome Extension 메시지 리스너
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    window.privacyGuard.handleMessage(request, sender, sendResponse);
    return true;
});

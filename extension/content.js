// extension/content.js
// 개선된 컨텐츠 스크립트 - 통신 문제 해결

class PrivacyGuardContent {
    constructor() {
        this.isEnabled = false;
        this.settings = {
            mode: 'medical',
            threshold: 50
        };

        this.lastResult = null;
        this.isProcessing = false;
        this.serverAvailable = false;

        // 모니터링할 요소들
        this.textInputs = new Set();
        this.observedElements = new WeakSet();

        this.init();
    }

    async init() {
        console.log('🛡️ Privacy Guard Content Script 초기화');

        // 설정 로드
        await this.loadSettings();

        // 서버 상태 확인
        await this.checkServerAvailability();

        // DOM 감시 시작
        this.startDOMObserver();

        // 메시지 리스너 설정
        this.setupMessageListeners();

        // 주기적 서버 체크
        this.startPeriodicServerCheck();

        console.log(`🛡️ Privacy Guard 준비 완료 (활성: ${this.isEnabled}, 서버: ${this.serverAvailable})`);
    }

    /**
     * 설정 로드
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(['privacyGuardSettings']);
            if (result.privacyGuardSettings) {
                const settings = result.privacyGuardSettings;
                this.isEnabled = settings.enabled || false;
                this.settings = { ...this.settings, ...settings };
            }
        } catch (error) {
            console.warn('설정 로드 실패:', error);
        }
    }

    /**
     * 서버 가용성 체크
     */
    async checkServerAvailability() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const response = await fetch('http://localhost:8000/health', {
                method: 'GET',
                signal: controller.signal,
                headers: { 'Accept': 'application/json' }
            });

            clearTimeout(timeoutId);
            this.serverAvailable = response.ok;

            if (this.serverAvailable) {
                console.log('✅ 서버 연결 성공');
            }

        } catch (error) {
            this.serverAvailable = false;
            console.log('⚠️ 서버 연결 실패 - 로컬 모드로 동작');
        }
    }

    /**
     * DOM 관찰자 시작
     */
    startDOMObserver() {
        // 기존 입력 요소들 스캔
        this.scanForTextInputs();

        // MutationObserver로 동적 요소 감지
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.scanElementForInputs(node);
                    }
                });
            });
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * 텍스트 입력 요소 스캔
     */
    scanForTextInputs() {
        const selectors = [
            'textarea',
            'input[type="text"]',
            'input[type="search"]',
            '[contenteditable="true"]',
            '[role="textbox"]'
        ];

        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                this.addInputListener(element);
            });
        });
    }

    /**
     * 특정 요소에서 입력 요소 스캔
     */
    scanElementForInputs(element) {
        if (this.isTextInput(element)) {
            this.addInputListener(element);
        }

        // 하위 요소들도 스캔
        const inputs = element.querySelectorAll('textarea, input[type="text"], input[type="search"], [contenteditable="true"], [role="textbox"]');
        inputs.forEach(input => this.addInputListener(input));
    }

    /**
     * 텍스트 입력 요소인지 확인
     */
    isTextInput(element) {
        if (!element || !element.tagName) return false;

        const tagName = element.tagName.toLowerCase();

        if (tagName === 'textarea') return true;
        if (tagName === 'input' && ['text', 'search'].includes(element.type)) return true;
        if (element.contentEditable === 'true') return true;
        if (element.getAttribute('role') === 'textbox') return true;

        return false;
    }

    /**
     * 입력 요소에 리스너 추가
     */
    addInputListener(element) {
        if (this.observedElements.has(element)) return;

        this.observedElements.add(element);
        this.textInputs.add(element);

        // 실시간 입력 감지
        let inputTimeout;
        const handleInput = () => {
            if (!this.isEnabled) return;

            clearTimeout(inputTimeout);
            inputTimeout = setTimeout(() => {
                this.analyzeInput(element);
            }, 1000); // 1초 디바운싱
        };

        // 전송 시도 감지
        const handleKeyDown = (e) => {
            if (!this.isEnabled) return;

            // Enter 키 (Shift+Enter 제외) 또는 Ctrl+Enter
            if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
                this.handleSendAttempt(element, e);
            }
        };

        element.addEventListener('input', handleInput);
        element.addEventListener('keydown', handleKeyDown);

        // 정리 함수 저장 (필요시 사용)
        element._privacyGuardCleanup = () => {
            element.removeEventListener('input', handleInput);
            element.removeEventListener('keydown', handleKeyDown);
            this.textInputs.delete(element);
            this.observedElements.delete(element);
        };
    }

    /**
     * 입력 내용 분석
     */
    async analyzeInput(element) {
        const text = this.getElementText(element);
        if (!text || text.length < 10) return;

        try {
            const result = await this.maskText(text);

            // 민감정보가 감지되면 시각적 경고
            if (result.stats.totalEntities > 0) {
                this.showInputWarning(element, result);
            } else {
                this.hideInputWarning(element);
            }

            this.lastResult = result;

        } catch (error) {
            console.warn('입력 분석 오류:', error);
        }
    }

    /**
     * 전송 시도 처리
     */
    async handleSendAttempt(element, event) {
        const text = this.getElementText(element);
        if (!text || text.length < 5) return;

        try {
            const result = await this.maskText(text);

            if (result.stats.totalEntities > 0) {
                const action = await this.showSendWarningDialog(result);

                switch (action) {
                    case 'mask':
                        // 마스킹된 텍스트로 교체
                        this.setElementText(element, result.maskedText);
                        this.showToast('민감정보가 마스킹되었습니다', 'info');
                        break;

                    case 'block':
                        // 전송 차단
                        event.preventDefault();
                        event.stopImmediatePropagation();
                        this.showToast('전송이 차단되었습니다', 'warning');
                        return false;

                    case 'ignore':
                        // 무시하고 전송
                        this.showToast('경고를 무시하고 전송합니다', 'info');
                        break;
                }
            }

            this.lastResult = result;

        } catch (error) {
            console.error('전송 처리 오류:', error);
            this.showToast('처리 중 오류가 발생했습니다', 'error');
        }
    }

    /**
     * 텍스트 마스킹 (서버 또는 로컬)
     */
    async maskText(text) {
        // 서버 시도
        if (this.serverAvailable) {
            try {
                return await this.serverMaskText(text);
            } catch (error) {
                console.warn('서버 마스킹 실패, 로컬로 전환:', error);
                this.serverAvailable = false;
            }
        }

        // 로컬 fallback
        return this.localMaskText(text);
    }

    /**
     * 서버 기반 마스킹
     */
    async serverMaskText(text) {
        const response = await fetch('http://localhost:8000/api/mask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                mode: this.settings.mode,
                threshold: this.settings.threshold
            })
        });

        if (!response.ok) {
            throw new Error(`서버 오류: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || '서버 처리 실패');
        }

        return this.normalizeServerResult(result);
    }

    /**
     * 로컬 마스킹 (fallback)
     */
    localMaskText(text) {
        const patterns = [
            { regex: /[가-힣]{2,4}(?=님|씨|환자|의사|선생님)/g, type: '이름', risk: 85, mask: '[이름]' },
            { regex: /010-\d{4}-\d{4}/g, type: '연락처', risk: 95, mask: '[연락처]' },
            { regex: /\d{6}-[1-4]\d{6}/g, type: '주민번호', risk: 100, mask: '[주민번호]' },
            { regex: /(서울대병원|서울대학교병원|삼성서울병원|아산병원|세브란스|연세의료원|고려대병원|[가-힣]+병원|[가-힣]+의료원)/g, type: '의료기관', risk: 70, mask: '[의료기관]' },
            { regex: /(간암|폐암|위암|대장암|유방암|당뇨병?|고혈압|심장병|뇌종양|백혈병)/g, type: '질병명', risk: 60, mask: '[질병명]' },
            { regex: /\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d{4}-\d{1,2}-\d{1,2}/g, type: '날짜', risk: 40, mask: '[날짜]' }
        ];

        const detected = [];
        let maskedText = text;
        let totalRisk = 0;

        patterns.forEach(pattern => {
            const matches = [...text.matchAll(pattern.regex)];
            matches.forEach(match => {
                detected.push({
                    text: match[0],
                    type: pattern.type,
                    risk: pattern.risk,
                    mask: pattern.mask,
                    start: match.index,
                    end: match.index + match[0].length
                });
                totalRisk += pattern.risk;
            });
        });

        // 마스킹 적용 (뒤에서부터)
        detected
            .sort((a, b) => b.start - a.start)
            .forEach(item => {
                maskedText = maskedText.substring(0, item.start) +
                    item.mask +
                    maskedText.substring(item.end);
            });

        const avgRisk = detected.length > 0 ? Math.round(totalRisk / detected.length) : 0;

        return {
            success: true,
            originalText: text,
            maskedText: maskedText,
            stats: {
                totalEntities: detected.length,
                maskedEntities: detected.length,
                avgRisk: avgRisk,
                processingTime: 0
            },
            maskingLog: detected.map(item => ({
                token: item.text,
                entity: item.type,
                risk_weight: item.risk,
                masked_as: item.mask
            })),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 서버 결과 정규화
     */
    normalizeServerResult(serverResult) {
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
     * 메시지 리스너 설정
     */
    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // 비동기 응답
        });
    }

    /**
     * 메시지 처리
     */
    async handleMessage(message, sender, sendResponse) {
        try {
            switch (message.action) {
                case 'toggleProtection':
                    await this.handleToggleProtection(message);
                    sendResponse({ success: true });
                    break;

                case 'getLastResult':
                    sendResponse({ success: true, result: this.lastResult });
                    break;

                case 'updateSettings':
                    this.settings = { ...this.settings, ...message.settings };
                    sendResponse({ success: true });
                    break;

                default:
                    sendResponse({ success: false, error: '알 수 없는 액션' });
            }
        } catch (error) {
            console.error('메시지 처리 오류:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    /**
     * 보호 기능 토글 처리
     */
    async handleToggleProtection(message) {
        this.isEnabled = message.enabled;

        if (message.settings) {
            this.settings = { ...this.settings, ...message.settings };
        }

        console.log(`🛡️ 보호 기능 ${this.isEnabled ? '활성화' : '비활성화'}`);

        // 모든 경고 숨김
        if (!this.isEnabled) {
            this.hideAllWarnings();
        }
    }

    /**
     * 헬퍼 함수들
     */
    getElementText(element) {
        if (element.tagName.toLowerCase() === 'textarea' ||
            (element.tagName.toLowerCase() === 'input' && element.type === 'text')) {
            return element.value;
        } else if (element.contentEditable === 'true') {
            return element.innerText || element.textContent;
        }
        return '';
    }

    setElementText(element, text) {
        if (element.tagName.toLowerCase() === 'textarea' ||
            (element.tagName.toLowerCase() === 'input' && element.type === 'text')) {
            element.value = text;
        } else if (element.contentEditable === 'true') {
            element.innerText = text;
        }
    }

    showInputWarning(element, result) {
        // 간단한 시각적 경고
        element.style.borderColor = '#e74c3c';
        element.style.boxShadow = '0 0 0 2px rgba(231, 76, 60, 0.2)';
        element.title = `민감정보 ${result.stats.totalEntities}개 감지됨 (위험도: ${result.stats.avgRisk}%)`;
    }

    hideInputWarning(element) {
        element.style.borderColor = '';
        element.style.boxShadow = '';
        element.title = '';
    }

    hideAllWarnings() {
        this.textInputs.forEach(element => {
            this.hideInputWarning(element);
        });
    }

    /**
     * 전송 경고 다이얼로그
     */
    async showSendWarningDialog(result) {
        const riskLevel = result.stats.avgRisk;
        const entityCount = result.stats.totalEntities;

        // 고위험은 자동 차단
        if (riskLevel >= 90) {
            this.showToast(`고위험 정보 감지! 전송이 자동 차단되었습니다 (위험도: ${riskLevel}%)`, 'error');
            return 'block';
        }

        // 중위험은 사용자 선택
        if (riskLevel >= 60) {
            const message = `민감정보 ${entityCount}개가 감지되었습니다 (위험도: ${riskLevel}%)\n\n어떻게 처리하시겠습니까?`;
            const action = confirm(`${message}\n\n확인: 마스킹 후 전송\n취소: 전송 차단`);
            return action ? 'mask' : 'block';
        }

        // 저위험은 자동 마스킹
        if (riskLevel >= 30) {
            this.showToast(`민감정보가 자동으로 마스킹되었습니다`, 'info');
            return 'mask';
        }

        // 위험도 낮음 - 통과
        return 'ignore';
    }

    /**
     * 토스트 메시지 표시
     */
    showToast(message, type = 'info') {
        // 기존 토스트 제거
        const existingToast = document.querySelector('.privacy-guard-toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = 'privacy-guard-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getToastColor(type)};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideInRight 0.3s ease;
            max-width: 300px;
            line-height: 1.4;
        `;

        // 아이콘 추가
        const icon = this.getToastIcon(type);
        toast.innerHTML = `${icon} ${message}`;

        document.body.appendChild(toast);

        // 자동 제거
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 4000);

        // CSS 애니메이션 추가 (한 번만)
        if (!document.querySelector('#privacy-guard-animations')) {
            const style = document.createElement('style');
            style.id = 'privacy-guard-animations';
            style.textContent = `
                @keyframes slideInRight {
                    from {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                @keyframes slideOutRight {
                    from {
                        opacity: 1;
                        transform: translateX(0);
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    getToastColor(type) {
        const colors = {
            'info': '#3498db',
            'success': '#2ed573',
            'warning': '#f39c12',
            'error': '#e74c3c'
        };
        return colors[type] || colors.info;
    }

    getToastIcon(type) {
        const icons = {
            'info': '🛡️',
            'success': '✅',
            'warning': '⚠️',
            'error': '🚫'
        };
        return icons[type] || icons.info;
    }

    /**
     * 주기적 서버 체크
     */
    startPeriodicServerCheck() {
        setInterval(() => {
            this.checkServerAvailability();
        }, 30000); // 30초마다
    }

    /**
     * 정리 함수
     */
    cleanup() {
        // MutationObserver 정리
        if (this.observer) {
            this.observer.disconnect();
        }

        // 모든 입력 요소 리스너 정리
        this.textInputs.forEach(element => {
            if (element._privacyGuardCleanup) {
                element._privacyGuardCleanup();
            }
        });

        // 토스트 메시지 정리
        const toasts = document.querySelectorAll('.privacy-guard-toast');
        toasts.forEach(toast => toast.remove());

        console.log('🛡️ Privacy Guard 정리 완료');
    }
}

// 콘텐츠 스크립트 초기화
let privacyGuard = null;

// DOM 준비되면 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPrivacyGuard);
} else {
    initPrivacyGuard();
}

function initPrivacyGuard() {
    try {
        if (!privacyGuard) {
            privacyGuard = new PrivacyGuardContent();
        }
    } catch (error) {
        console.error('Privacy Guard 초기화 실패:', error);
    }
}

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', () => {
    if (privacyGuard) {
        privacyGuard.cleanup();
    }
});

// 전역 에러 핸들러
window.addEventListener('error', (event) => {
    if (event.error && event.error.message && event.error.message.includes('privacy')) {
        console.error('Privacy Guard 오류:', event.error);
    }
});

// privacy-client.js와의 연동을 위한 전역 노출
window.privacyGuardContent = privacyGuard;
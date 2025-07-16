// content.js - 수정된 버전 (서버 상태 표시 추가)

class ContentScriptManager {
    constructor() {
        this.originalTexts = new Map();
        this.maskedElements = new Set();
        this.isEnabled = false;
        this.settings = {
            threshold: 50,
            mode: 'medical',
            enabled: false
        };

        this.init();
    }

    init() {
        this.loadSettings();

        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true;
        });

        console.log('🛡️ Privacy Guard 컨텐츠 스크립트 로드됨');

        // 🔥 새로운 기능: 서버 상태 표시
        this.showServerStatus();
    }

    // 🔥 새로운 기능: 서버 상태 표시
    async showServerStatus() {
        if (!window.privacyGuard) {
            console.warn('Privacy Guard 엔진이 로드되지 않음');
            return;
        }

        const serverStatus = window.privacyGuard.getServerStatus();

        // 서버 상태 확인
        const connected = await window.privacyGuard.checkServerStatus();

        if (connected) {
            this.showNotification('🐍 Python 서버 연결됨 - 실제 KoELECTRA 모델 사용', 'success');
        } else {
            this.showNotification('⚡ JavaScript 버전 사용 - 서버를 시작하면 Python 모델 사용 가능', 'info');
        }
    }

    handleMessage(request, sender, sendResponse) {
        switch (request.action) {
            case 'toggleProtection':
                this.toggleProtection(request.enabled);
                sendResponse({success: true});
                break;

            case 'updateSettings':
                this.updateSettings(request);
                sendResponse({success: true});
                break;

            case 'scanPage':
                this.scanPage().then(stats => {
                    sendResponse({success: true, stats: stats});
                });
                break;

            case 'clearMasking':
                this.clearMasking();
                sendResponse({success: true});
                break;

            // 🔥 새로운 기능: 서버 상태 체크
            case 'checkServer':
                this.checkServerStatus().then(status => {
                    sendResponse({success: true, serverStatus: status});
                });
                break;
        }
    }

    // 🔥 새로운 기능: 서버 상태 체크
    async checkServerStatus() {
        if (!window.privacyGuard) return { connected: false, error: 'Engine not loaded' };

        const connected = await window.privacyGuard.checkServerStatus();
        const status = window.privacyGuard.getServerStatus();

        return { connected, ...status };
    }

    toggleProtection(enabled) {
        this.isEnabled = enabled;
        this.settings.enabled = enabled;
        this.saveSettings();

        if (enabled) {
            this.showNotification('🛡️ Privacy Guard 활성화됨', 'success');
            this.scanPage();
        } else {
            this.showNotification('⚪ Privacy Guard 비활성화됨', 'info');
            this.clearMasking();
        }
    }

    updateSettings(newSettings) {
        this.settings = {
            ...this.settings,
            threshold: newSettings.threshold,
            mode: newSettings.mode
        };

        window.privacyGuard.updateSettings(this.settings);
        this.saveSettings();

        if (this.isEnabled) {
            this.scanPage();
        }
    }

    // 🔥 수정된 스캔 함수 (비동기 처리)
    async scanPage() {
        if (!this.isEnabled) return null;

        console.log('🔍 페이지 스캔 시작...');

        this.clearMasking();

        const textElements = this.findTextElements();
        let totalStats = {
            totalEntities: 0,
            maskedEntities: 0,
            avgRisk: 0,
            processingTime: 0,
            source: 'unknown'
        };

        let allRisks = [];
        const startTime = performance.now();

        // 🔥 비동기 처리로 변경
        for (const element of textElements) {
            const text = element.textContent.trim();
            if (text.length < 3) continue;

            try {
                // Privacy Guard 엔진으로 분석 (비동기)
                const result = await window.privacyGuard.process(text);

                if (result.maskedEntities > 0) {
                    this.originalTexts.set(element, text);
                    element.innerHTML = this.createMaskedHTML(result);
                    this.maskedElements.add(element);

                    totalStats.totalEntities += result.totalEntities;
                    totalStats.maskedEntities += result.maskedEntities;
                    totalStats.source = result.source || 'unknown';

                    if (result.avgRisk > 0) {
                        allRisks.push(result.avgRisk);
                    }
                }
            } catch (error) {
                console.error('텍스트 처리 오류:', error);
            }
        }

        totalStats.processingTime = Math.round(performance.now() - startTime);
        totalStats.avgRisk = allRisks.length > 0 ?
            Math.round(allRisks.reduce((sum, risk) => sum + risk, 0) / allRisks.length) : 0;

        console.log(`📊 스캔 완료: ${totalStats.maskedEntities}/${totalStats.totalEntities} 개체 마스킹 (${totalStats.source} 엔진 사용)`);

        if (totalStats.maskedEntities > 0) {
            const sourceIcon = totalStats.source === 'python' ? '🐍' : '⚡';
            const sourceText = totalStats.source === 'python' ? 'Python 모델' : 'JavaScript';

            this.showNotification(
                `${sourceIcon} ${totalStats.maskedEntities}개 개인정보 마스킹됨 (${sourceText})`,
                'warning'
            );
        }

        return totalStats;
    }

    // 기존 메서드들 (동일)
    findTextElements() {
        const elements = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    const parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_REJECT;

                    const tagName = parent.tagName.toLowerCase();
                    if (['script', 'style', 'noscript'].includes(tagName)) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    if (node.textContent.trim().length > 2) {
                        return NodeFilter.FILTER_ACCEPT;
                    }

                    return NodeFilter.FILTER_REJECT;
                }
            }
        );

        let node;
        while (node = walker.nextNode()) {
            elements.push(node.parentElement);
        }

        return [...new Set(elements)];
    }

    createMaskedHTML(result) {
        let html = result.maskedText;

        const maskPatterns = ['[PERSON]', '[CONTACT]', '[HOSPITAL]', '[DISEASE]', '[DATE]', '[AGE]', '[TREATMENT]'];

        maskPatterns.forEach(pattern => {
            const regex = new RegExp(pattern.replace(/[[\]]/g, '\\$&'), 'g');
            html = html.replace(regex, `<span class="privacy-guard-masked" data-source="${result.source || 'unknown'}">${pattern}</span>`);
        });

        return html;
    }

    clearMasking() {
        this.maskedElements.forEach(element => {
            const originalText = this.originalTexts.get(element);
            if (originalText) {
                element.textContent = originalText;
            }
        });

        this.maskedElements.clear();
        this.originalTexts.clear();

        console.log('🧹 마스킹 제거 완료');
    }

    // 🔥 수정된 알림 (소스 표시)
    showNotification(message, type = 'info') {
        const existingNotification = document.querySelector('.privacy-guard-notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `privacy-guard-notification ${type}`;
        notification.textContent = message;

        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#d4edda' :
                type === 'warning' ? '#fff3cd' : '#d1ecf1',
            color: type === 'success' ? '#155724' :
                type === 'warning' ? '#856404' : '#0c5460',
            padding: '12px 20px',
            borderRadius: '8px',
            border: `1px solid ${type === 'success' ? '#c3e6cb' :
                type === 'warning' ? '#faeaba' : '#bee5eb'}`,
            zIndex: '10000',
            fontSize: '14px',
            fontWeight: '600',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            animation: 'slideInRight 0.3s ease',
            maxWidth: '300px'
        });

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 4000); // 4초로 연장
    }

    saveSettings() {
        chrome.storage.sync.set({ privacyGuardSettings: this.settings });
    }

    loadSettings() {
        chrome.storage.sync.get(['privacyGuardSettings'], (result) => {
            this.settings = result.privacyGuardSettings || this.settings;
            this.isEnabled = this.settings.enabled;
            if (window.privacyGuard) {
                window.privacyGuard.updateSettings(this.settings);
            }
        });
    }
}

// 컨텐츠 스크립트 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ContentScriptManager();
    });
} else {
    new ContentScriptManager();
}
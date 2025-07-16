// popup.js - 간단한 버전 (통신 문제 해결)

document.addEventListener('DOMContentLoaded', function() {
    const mainToggle = document.getElementById('mainToggle');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('thresholdValue');
    const analysisMode = document.getElementById('analysisMode');

    const clearButton = document.getElementById('clearButton');
    const stats = document.getElementById('stats');

    // 초기화
    loadSettings();
    setupEventListeners();

    function setupEventListeners() {
        // 토글 스위치
        mainToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            const isActive = this.classList.contains('active');
            saveSettings();

            // 메시지 전송 (간단한 버전)
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'toggleProtection',
                        enabled: isActive
                    }).catch(err => console.log('메시지 전송 실패:', err));
                }
            });
        });

        // 임계값 슬라이더
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
            saveSettings();

            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'updateSettings',
                        threshold: parseInt(thresholdSlider.value),
                        mode: analysisMode.value
                    }).catch(err => console.log('설정 업데이트 실패:', err));
                }
            });
        });

        // 분석 모드 변경
        analysisMode.addEventListener('change', function() {
            saveSettings();
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'updateSettings',
                        threshold: parseInt(thresholdSlider.value),
                        mode: this.value
                    }).catch(err => console.log('모드 변경 실패:', err));
                }
            });
        });

        // 초기화 버튼
        clearButton.addEventListener('click', function() {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {action: 'clearMasking'})
                        .catch(err => console.log('초기화 실패:', err));
                }
            });
            stats.classList.remove('show');
            resetStats();
        });
    }

    function updateStats(statsData) {
        document.getElementById('totalEntities').textContent = statsData.totalEntities || 0;
        document.getElementById('maskedEntities').textContent = statsData.maskedEntities || 0;
        document.getElementById('avgRisk').textContent = (statsData.avgRisk || 0) + '%';
    }

    function resetStats() {
        document.getElementById('totalEntities').textContent = '0';
        document.getElementById('maskedEntities').textContent = '0';
        document.getElementById('avgRisk').textContent = '0%';
    }

    function saveSettings() {
        const settings = {
            enabled: mainToggle.classList.contains('active'),
            threshold: parseInt(thresholdSlider.value),
            mode: analysisMode.value
        };

        chrome.storage.sync.set({ privacyGuardSettings: settings });
    }

    function loadSettings() {
        chrome.storage.sync.get(['privacyGuardSettings'], function(result) {
            const settings = result.privacyGuardSettings || {
                enabled: false,
                threshold: 50,
                mode: 'medical'
            };

            if (settings.enabled) {
                mainToggle.classList.add('active');
            }

            thresholdSlider.value = settings.threshold;
            thresholdValue.textContent = settings.threshold;
            analysisMode.value = settings.mode;
        });
    }
});
// popup.js - 수정된 버전 (서버 상태 및 모델 정보 표시)

document.addEventListener('DOMContentLoaded', function() {
    const mainToggle = document.getElementById('mainToggle');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('thresholdValue');
    const analysisMode = document.getElementById('analysisMode');
    const scanButton = document.getElementById('scanButton');
    const clearButton = document.getElementById('clearButton');
    const stats = document.getElementById('stats');

    // 🔥 새로운 UI 요소들
    let serverStatusIndicator;
    let modelInfo;

    // 초기화
    init();

    function init() {
        createServerStatusUI();
        loadSettings();
        checkServerStatus();
        setupEventListeners();
    }

    // 🔥 새로운 기능: 서버 상태 UI 생성
    function createServerStatusUI() {
        // 서버 상태 표시기 추가
        const container = document.querySelector('.container');
        const serverSection = document.createElement('div');
        serverSection.className = 'server-section';
        serverSection.innerHTML = `
            <div class="server-status">
                <div class="server-indicator" id="serverIndicator">
                    <div class="status-dot"></div>
                    <span class="status-text">서버 상태 확인 중...</span>
                </div>
                <button class="reconnect-btn" id="reconnectBtn" style="display: none;">🔄 재연결</button>
            </div>
            <div class="model-info" id="modelInfo" style="display: none;">
                <div class="model-name"></div>
                <div class="model-details"></div>
            </div>
        `;

        // 헤더 다음에 삽입
        const header = document.querySelector('.header');
        header.insertAdjacentElement('afterend', serverSection);

        // 스타일 추가
        const style = document.createElement('style');
        style.textContent = `
            .server-section {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #dee2e6;
            }
            
            .server-status {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            
            .server-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #6c757d;
                animation: pulse 2s infinite;
            }
            
            .status-dot.connected {
                background: #28a745;
            }
            
            .status-dot.disconnected {
                background: #dc3545;
            }
            
            .status-text {
                font-size: 12px;
                color: #495057;
                font-weight: 500;
            }
            
            .reconnect-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                cursor: pointer;
            }
            
            .reconnect-btn:hover {
                background: #0056b3;
            }
            
            .model-info {
                font-size: 11px;
                color: #6c757d;
                border-top: 1px solid #dee2e6;
                padding-top: 8px;
            }
            
            .model-name {
                font-weight: 600;
                color: #495057;
            }
            
            .model-details {
                margin-top: 2px;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `;
        document.head.appendChild(style);

        // 참조 저장
        serverStatusIndicator = document.getElementById('serverIndicator');
        modelInfo = document.getElementById('modelInfo');

        // 재연결 버튼 이벤트
        document.getElementById('reconnectBtn').addEventListener('click', handleReconnect);
    }

    function setupEventListeners() {
        // 토글 스위치
        mainToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            const isActive = this.classList.contains('active');
            saveSettings();

            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'toggleProtection',
                    enabled: isActive
                });
            });
        });

        // 임계값 슬라이더
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
            saveSettings();

            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'updateSettings',
                    threshold: parseInt(thresholdSlider.value),
                    mode: analysisMode.value
                });
            });
        });

        // 분석 모드 변경
        analysisMode.addEventListener('change', function() {
            saveSettings();
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'updateSettings',
                    threshold: parseInt(thresholdSlider.value),
                    mode: this.value
                });
            });
        });

        // 스캔 버튼
        scanButton.addEventListener('click', async function() {
            this.textContent = '🔄 스캔 중...';
            this.disabled = true;

            try {
                const tabs = await chrome.tabs.query({active: true, currentWindow: true});
                const response = await chrome.tabs.sendMessage(tabs[0].id, {action: 'scanPage'});

                if (response && response.success) {
                    updateStats(response.stats);
                    stats.classList.add('show');

                    // 🔥 처리 소스 표시
                    showProcessingSource(response.stats.source);
                }
            } catch (error) {
                console.error('스캔 오류:', error);
            } finally {
                this.textContent = '🔍 스캔';
                this.disabled = false;
            }
        });

        // 초기화 버튼
        clearButton.addEventListener('click', function() {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                chrome.tabs.sendMessage(tabs[0].id, {action: 'clearMasking'});
            });
            stats.classList.remove('show');
            resetStats();
        });
    }

    // 🔥 새로운 기능: 서버 상태 체크
    async function checkServerStatus() {
        try {
            const tabs = await chrome.tabs.query({active: true, currentWindow: true});
            const response = await chrome.tabs.sendMessage(tabs[0].id, {action: 'checkServer'});

            if (response && response.success) {
                updateServerStatus(response.serverStatus);
            }
        } catch (error) {
            console.error('서버 상태 체크 실패:', error);
            updateServerStatus({connected: false, error: error.message});
        }
    }

    // 🔥 새로운 기능: 서버 상태 UI 업데이트
    function updateServerStatus(serverStatus) {
        const statusDot = serverStatusIndicator.querySelector('.status-dot');
        const statusText = serverStatusIndicator.querySelector('.status-text');
        const reconnectBtn = document.getElementById('reconnectBtn');

        if (serverStatus.connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = '🐍 Python 서버 연결됨';
            reconnectBtn.style.display = 'none';

            // 모델 정보 표시
            modelInfo.style.display = 'block';
            modelInfo.querySelector('.model-name').textContent = 'KoELECTRA + LoRA 모델';
            modelInfo.querySelector('.model-details').textContent =
                `4단계 파이프라인 • 임계값: ${thresholdSlider.value} • 서버: ${serverStatus.endpoint}`;
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = '⚡ JavaScript 버전 사용';
            reconnectBtn.style.display = 'inline-block';

            // 모델 정보 표시
            modelInfo.style.display = 'block';
            modelInfo.querySelector('.model-name').textContent = '간소화된 JavaScript 모델';
            modelInfo.querySelector('.model-details').textContent =
                `정규식 패턴 매칭 • 임계값: ${thresholdSlider.value} • 오프라인 모드`;
        }
    }

    // 🔥 새로운 기능: 재연결 처리
    async function handleReconnect() {
        const reconnectBtn = document.getElementById('reconnectBtn');
        const originalText = reconnectBtn.textContent;

        reconnectBtn.textContent = '🔄 연결 중...';
        reconnectBtn.disabled = true;

        try {
            // 2초 후 다시 체크
            setTimeout(async () => {
                await checkServerStatus();
                reconnectBtn.textContent = originalText;
                reconnectBtn.disabled = false;
            }, 2000);
        } catch (error) {
            console.error('재연결 실패:', error);
            reconnectBtn.textContent = originalText;
            reconnectBtn.disabled = false;
        }
    }

    // 🔥 새로운 기능: 처리 소스 표시
    function showProcessingSource(source) {
        const sourceIcon = source === 'python' ? '🐍' : '⚡';
        const sourceName = source === 'python' ? 'Python KoELECTRA' : 'JavaScript';

        // 임시 알림 표시
        const notification = document.createElement('div');
        notification.textContent = `${sourceIcon} ${sourceName} 엔진 사용됨`;
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: ${source === 'python' ? '#d4edda' : '#fff3cd'};
            color: ${source === 'python' ? '#155724' : '#856404'};
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            z-index: 10001;
            animation: fadeInOut 2s ease-in-out;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 2000);
    }

    // 설정 저장
    function saveSettings() {
        const settings = {
            enabled: mainToggle.classList.contains('active'),
            threshold: parseInt(thresholdSlider.value),
            mode: analysisMode.value
        };

        chrome.storage.sync.set({ privacyGuardSettings: settings });
    }

    // 설정 로드
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

    // 🔥 수정된 통계 업데이트 (소스 정보 포함)
    function updateStats(statsData) {
        document.getElementById('totalEntities').textContent = statsData.totalEntities;
        document.getElementById('maskedEntities').textContent = statsData.maskedEntities;
        document.getElementById('avgRisk').textContent = statsData.avgRisk + '%';

        // 🔥 처리 시간 및 소스 정보 추가
        const existingInfo = document.querySelector('.processing-info');
        if (existingInfo) {
            existingInfo.remove();
        }

        const processingInfo = document.createElement('div');
        processingInfo.className = 'processing-info';
        processingInfo.innerHTML = `
            <div class="stat-row">
                <span class="stat-label">처리 시간:</span>
                <span class="stat-value">${statsData.processingTime || 0}ms</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">엔진:</span>
                <span class="stat-value">${statsData.source === 'python' ? '🐍 Python' : '⚡ JavaScript'}</span>
            </div>
        `;

        stats.appendChild(processingInfo);
    }

    // 통계 초기화
    function resetStats() {
        document.getElementById('totalEntities').textContent = '0';
        document.getElementById('maskedEntities').textContent = '0';
        document.getElementById('avgRisk').textContent = '0%';

        const processingInfo = document.querySelector('.processing-info');
        if (processingInfo) {
            processingInfo.remove();
        }
    }

    // 🔥 주기적 서버 상태 체크 (30초마다)
    setInterval(checkServerStatus, 30000);

    // 🔥 팝업 열릴 때마다 서버 상태 체크
    window.addEventListener('focus', checkServerStatus);
});

// 🔥 추가 스타일
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    .processing-info {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #dee2e6;
    }
    
    .processing-info .stat-row {
        font-size: 12px;
        margin: 3px 0;
    }
    
    .processing-info .stat-value {
        font-size: 12px;
    }
    
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        50% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    }
`;
document.head.appendChild(additionalStyles);
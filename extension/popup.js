// popup.js

// 메시지 전송 헬퍼 (콜백 기반)
function sendMessage(message, onSuccess, onError) {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
        const tab = tabs[0];
        if (!tab || !tab.id) {
            onError?.(new Error('활성 탭을 찾을 수 없습니다.'));
            return;
        }
        chrome.tabs.sendMessage(tab.id, message, response => {
            if (chrome.runtime.lastError) {
                onError?.(chrome.runtime.lastError);
            } else {
                onSuccess?.(response);
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const mainToggle      = document.getElementById('mainToggle');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue  = document.getElementById('thresholdValue');
    const analysisMode    = document.getElementById('analysisMode');
    const scanButton      = document.getElementById('scanButton');
    const clearButton     = document.getElementById('clearButton');
    const stats           = document.getElementById('stats');

    let serverStatusIndicator;
    let modelInfo;

    init();

    function init() {
        createServerStatusUI();
        loadSettings();
        checkServerStatus();
        setupEventListeners();
    }

    // 서버 상태 UI 생성
    function createServerStatusUI() {
        const header = document.querySelector('.header');
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
        header.insertAdjacentElement('afterend', serverSection);

        serverStatusIndicator = document.getElementById('serverIndicator');
        modelInfo             = document.getElementById('modelInfo');
        document.getElementById('reconnectBtn').addEventListener('click', handleReconnect);
    }

    // 각종 이벤트 등록
    function setupEventListeners() {
        // 보호 기능 토글
        mainToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            saveSettings();
            sendMessage(
                { action: 'toggleProtection', enabled: this.classList.contains('active') },
                () => {},
                () => {}
            );
        });

        // 임계값 변경
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
            saveSettings();
            sendMessage(
                { action: 'updateSettings', threshold: +this.value, mode: analysisMode.value },
                () => {},
                () => {}
            );
        });

        // 분석 모드 변경
        analysisMode.addEventListener('change', function() {
            saveSettings();
            sendMessage(
                { action: 'updateSettings', threshold: +thresholdSlider.value, mode: this.value },
                () => {},
                () => {}
            );
        });

        // 스캔 버튼
        scanButton.addEventListener('click', function() {
            this.textContent = '🔄 스캔 중...';
            this.disabled    = true;

            sendMessage(
                { action: 'scanPage' },
                response => {
                    if (response && response.success) {
                        updateStats(response.stats);
                        stats.classList.add('show');
                        showProcessingSource(response.stats.source);
                    }
                    scanButton.textContent = '🔍 스캔';
                    scanButton.disabled    = false;
                },
                error => {
                    console.warn('스캔 실패(리시버 없음):', error.message);
                    scanButton.textContent = '🔍 스캔';
                    scanButton.disabled    = false;
                }
            );
        });

        // 초기화 버튼
        clearButton.addEventListener('click', () => {
            sendMessage({ action: 'clearMasking' });
            stats.classList.remove('show');
            resetStats();
        });
    }

    // 서버 상태 확인 (content script 실패 시 HTTP 폴백)
    function checkServerStatus() {
        sendMessage(
            { action: 'checkServer' },
            res => updateServerStatus(res.serverStatus),
            () => {
                fetch('http://localhost:8000/health')
                    .then(r => r.json())
                    .then(() => updateServerStatus({ connected: true, endpoint: 'http://localhost:8000' }))
                    .catch(() => updateServerStatus({ connected: false }));
            }
        );
    }

    // 서버 상태 UI 업데이트
    function updateServerStatus(status) {
        const dot = serverStatusIndicator.querySelector('.status-dot');
        const txt = serverStatusIndicator.querySelector('.status-text');
        const btn = document.getElementById('reconnectBtn');

        if (status.connected) {
            dot.className = 'status-dot connected';
            txt.textContent = '🐍 Python 서버 연결됨';
            btn.style.display = 'none';
            modelInfo.style.display = 'block';
            modelInfo.querySelector('.model-name').textContent    = 'KoELECTRA + LoRA 모델';
            modelInfo.querySelector('.model-details').textContent =
                `임계값 ${thresholdSlider.value} • ${status.endpoint}`;
        } else {
            dot.className = 'status-dot disconnected';
            txt.textContent = '⚡ JavaScript 버전 사용';
            btn.style.display = 'inline-block';
            modelInfo.style.display = 'block';
            modelInfo.querySelector('.model-name').textContent    = '간소화된 JS 모델';
            modelInfo.querySelector('.model-details').textContent =
                `임계값 ${thresholdSlider.value} • 오프라인 모드`;
        }
    }

    // 재연결 버튼 핸들러
    function handleReconnect() {
        const btn = document.getElementById('reconnectBtn');
        btn.textContent = '🔄 연결 중...';
        btn.disabled    = true;
        setTimeout(() => {
            checkServerStatus();
            btn.textContent = '🔄 재연결';
            btn.disabled    = false;
        }, 2000);
    }

    // 통계 업데이트
    function updateStats(data) {
        document.getElementById('totalEntities').textContent  = data.totalEntities;
        document.getElementById('maskedEntities').textContent = data.maskedEntities;
        document.getElementById('avgRisk').textContent         = data.avgRisk + '%';

        const existing = document.querySelector('.processing-info');
        if (existing) existing.remove();

        const info = document.createElement('div');
        info.className = 'processing-info';
        info.innerHTML = `
      <div class="stat-row"><span class="stat-label">처리 시간:</span><span class="stat-value">${data.processingTime || 0}ms</span></div>
      <div class="stat-row"><span class="stat-label">엔진:</span><span class="stat-value">${data.source === 'python' ? '🐍 Python' : '⚡ JavaScript'}</span></div>
    `;
        stats.appendChild(info);
    }

    // 엔진 사용 알림
    function showProcessingSource(source) {
        const icon = source === 'python' ? '🐍' : '⚡';
        const text = source === 'python' ? 'Python 모델' : 'JavaScript';
        const note = document.createElement('div');
        note.textContent = `${icon} ${text} 사용됨`;
        Object.assign(note.style, {
            position: 'fixed', top: '50%', left: '50%',
            transform: 'translate(-50%,-50%)',
            background: '#fff', padding: '8px 16px', borderRadius: '20px',
            fontSize: '12px', fontWeight: '600', zIndex: '10000',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
            animation: 'fadeInOut 2s ease-in-out'
        });
        document.body.appendChild(note);
        setTimeout(() => note.remove(), 2000);
    }

    // 설정 저장/로드
    function saveSettings() {
        const s = {
            enabled:   mainToggle.classList.contains('active'),
            threshold: +thresholdSlider.value,
            mode:      analysisMode.value
        };
        chrome.storage.sync.set({ privacyGuardSettings: s });
    }
    function loadSettings() {
        chrome.storage.sync.get('privacyGuardSettings', res => {
            const s = res.privacyGuardSettings || {};
            if (s.enabled) mainToggle.classList.add('active');
            thresholdSlider.value  = s.threshold ?? thresholdSlider.value;
            thresholdValue.textContent = thresholdSlider.value;
            analysisMode.value     = s.mode || analysisMode.value;
        });
    }

    // 통계 리셋
    function resetStats() {
        document.getElementById('totalEntities').textContent  = '0';
        document.getElementById('maskedEntities').textContent = '0';
        document.getElementById('avgRisk').textContent         = '0%';
        const pi = document.querySelector('.processing-info');
        if (pi) pi.remove();
    }

    // 주기적 상태 체크 & focus 시 체크
    setInterval(checkServerStatus, 30000);
    window.addEventListener('focus', checkServerStatus);
});

// 추가 스타일
const style = document.createElement('style');
style.textContent = `
  .processing-info { margin-top:10px; padding-top:10px; border-top:1px solid #dee2e6; }
  .processing-info .stat-row { font-size:12px; margin:3px 0; }
  .processing-info .stat-value { font-size:12px; }
  @keyframes fadeInOut { 0%{opacity:0;transform:translate(-50%,-50%) scale(0.8);}50%{opacity:1;transform:translate(-50%,-50%) scale(1);}100%{opacity:0;transform:translate(-50%,-50%) scale(0.8);} }
`;
document.head.appendChild(style);

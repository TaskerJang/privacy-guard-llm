// background.js
console.log("🔵 [background.js] loaded");

chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
    console.log("📨 [background.js] received message:", req, "from", sender);

    if (req.action === "mask") {
        console.log("⚙️ [background.js] calling API for text:", req.text?.substring(0, 50) + "...");

        const startTime = Date.now();

        fetch("http://localhost:8000/api/mask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ text: req.text })
        })
            .then(response => {
                console.log("⬅️ [background.js] response status:", response.status);
                console.log("⬅️ [background.js] response headers:", [...response.headers.entries()]);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return response.json();
            })
            .then(json => {
                const duration = Date.now() - startTime;
                console.log("✅ [background.js] API result ({}ms):".replace('{}', duration), json);

                // 응답 구조 검증
                if (!json || typeof json !== 'object') {
                    throw new Error('Invalid response format');
                }

                // 필수 필드 확인 및 기본값 설정
                const normalizedResponse = {
                    hasSensitiveInfo: json.has_sensitive_info || false,
                    detectedItems: json.detected_entities || [],
                    maxRisk: json.max_risk || 0,
                    overallRisk: json.overall_risk || 0,
                    maskedText: json.masked_text || req.text,
                    stats: json.stats || {}
                };

                console.log("📤 [background.js] sending normalized response:", normalizedResponse);
                sendResponse(normalizedResponse);
            })
            .catch(err => {
                console.error("❌ [background.js] fetch error:", err);
                console.error("❌ [background.js] error stack:", err.stack);

                // 폴백 응답
                const fallbackResponse = {
                    error: err.message,
                    hasSensitiveInfo: false,
                    detectedItems: [],
                    maxRisk: 0,
                    overallRisk: 0,
                    maskedText: req.text,
                    useFallback: true
                };

                console.log("🔄 [background.js] sending fallback response:", fallbackResponse);
                sendResponse(fallbackResponse);
            });

        return true;  // 비동기 응답을 위해 반드시 true 반환
    }

    // 다른 액션들
    console.log("⚠️ [background.js] unknown action:", req.action);
    sendResponse({ error: "Unknown action" });
});
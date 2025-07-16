// background.js
console.log("🔵 [background.js] loaded");

chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
    console.log("📨 [background.js] received message:", req, "from", sender);

    if (req.action === "mask") {
        console.log("⚙️ [background.js] calling API for text:", req.text);
        fetch("http://localhost:8000/api/mask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: req.text })
        })
            .then(r => {
                console.log("⬅️ [background.js] response status:", r.status);
                return r.json();
            })
            .then(json => {
                console.log("✅ [background.js] API result:", json);
                sendResponse(json);
            })
            .catch(err => {
                console.error("❌ [background.js] fetch error:", err);
                sendResponse({ error: err.message });
            });
        return true;  // 비동기 응답을 위해 반드시 true 반환
    }
});

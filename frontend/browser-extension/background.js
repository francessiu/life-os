// background.js
const API_URL = "http://localhost:8000";

// 1. Polling Function
async function checkFocusStatus() {
  try {
    // We assume the user logged in via the Popup and saved the token
    const { token } = await chrome.storage.local.get("token");
    if (!token) return;

    // Fetch Character State (or a dedicated /focus/status endpoint)
    const response = await fetch(`${API_URL}/gamification/character/state`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await response.json();

    // Logic: If tokens are 0, we might enforce blocking? 
    // Or if the backend says "focus_active: true" (You might need to add this flag to the API)
    const isFocusMode = data.tokens === 0; // Example trigger

    updateBlockingRules(isFocusMode);
    
    // Send state to Content Script (to update Butler UI)
    sendMessageToTabs({ type: "UPDATE_BUTLER", emotion: data.emotion });

  } catch (e) {
    console.error("LifeOS Sync Failed", e);
  }
}

// 2. Network Blocking Logic (declarativeNetRequest)
function updateBlockingRules(enable) {
  const rules = [
    {
      id: 1,
      priority: 1,
      action: { type: "redirect", redirect: { url: "http://localhost:3000/dashboard" } },
      condition: { urlFilter: "twitter.com", resourceTypes: ["main_frame"] }
    },
    {
      id: 2,
      priority: 1,
      action: { type: "block" },
      condition: { urlFilter: "youtube.com", resourceTypes: ["main_frame"] }
    }
  ];

  if (enable) {
    chrome.declarativeNetRequest.updateDynamicRules({
      addRules: rules,
      removeRuleIds: [1, 2]
    });
  } else {
    chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: [1, 2]
    });
  }
}

// Poll every minute
setInterval(checkFocusStatus, 60000);
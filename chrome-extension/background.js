/**
 * Claw Agent — Chrome Extension Background Service Worker
 * Handles side panel lifecycle, context menus, and message routing.
 */

// Open side panel on extension icon click
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

// Context menus
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "claw-explain",
    title: "Claw: Explain selection",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "claw-summarize",
    title: "Claw: Summarize page",
    contexts: ["page"],
  });
  chrome.contextMenus.create({
    id: "claw-fix-code",
    title: "Claw: Fix this code",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "claw-rewrite",
    title: "Claw: Rewrite selection",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const handlers = {
    "claw-explain": () => {
      const text = info.selectionText || "";
      sendToSidePanel(tab.id, {
        type: "context-prompt",
        prompt: `Explain this:\n\`\`\`\n${text}\n\`\`\``,
      });
    },
    "claw-summarize": () => {
      sendToSidePanel(tab.id, {
        type: "context-prompt",
        prompt: "Summarize the current page",
        readPage: true,
      });
    },
    "claw-fix-code": () => {
      const text = info.selectionText || "";
      sendToSidePanel(tab.id, {
        type: "context-prompt",
        prompt: `Fix any bugs in this code:\n\`\`\`\n${text}\n\`\`\``,
      });
    },
    "claw-rewrite": () => {
      const text = info.selectionText || "";
      sendToSidePanel(tab.id, {
        type: "context-prompt",
        prompt: `Rewrite this more clearly:\n${text}`,
      });
    },
  };

  const handler = handlers[info.menuItemId];
  if (handler) {
    chrome.sidePanel.open({ tabId: tab.id });
    // Small delay to ensure panel is open before sending
    setTimeout(handler, 500);
  }
});

// Route messages between content script and side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "get-page-content") {
    // Forward request to content script in the active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        sendResponse({ error: "No active tab" });
        return;
      }
      chrome.tabs.sendMessage(tabs[0].id, { type: "extract-content" }, (response) => {
        if (chrome.runtime.lastError) {
          // Content script not injected — inject it now
          chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            files: ["content.js"],
          }).then(() => {
            chrome.tabs.sendMessage(tabs[0].id, { type: "extract-content" }, (resp) => {
              sendResponse(resp || { error: "Failed to extract" });
            });
          }).catch((err) => {
            sendResponse({ error: err.message });
          });
        } else {
          sendResponse(response || { error: "No response from page" });
        }
      });
    });
    return true; // async
  }

  if (message.type === "execute-on-page") {
    // Execute action on the active tab via content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        sendResponse({ error: "No active tab" });
        return;
      }
      chrome.tabs.sendMessage(tabs[0].id, message, (response) => {
        sendResponse(response || { error: "No response" });
      });
    });
    return true;
  }

  if (message.type === "get-tab-info") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        sendResponse({ error: "No active tab" });
        return;
      }
      sendResponse({ url: tabs[0].url, title: tabs[0].title, tabId: tabs[0].id });
    });
    return true;
  }

  // "Stop" button in the injected page banner — forward to side panel
  if (message.type === "stop-agent") {
    chrome.runtime.sendMessage({ type: "stop-agent" }).catch(() => {});
    sendResponse({ ok: true });
    return true;
  }
});

function sendToSidePanel(tabId, message) {
  // The side panel script listens for these messages
  chrome.runtime.sendMessage(message).catch(() => {
    // Panel might not be ready yet, retry once
    setTimeout(() => chrome.runtime.sendMessage(message).catch(() => {}), 1000);
  });
}

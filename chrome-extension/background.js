/**
 * 🦞 Claw Agent - Background Script (SIMPLIFIED)
 */

// Open side panel on icon click
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

// Log when extension is installed
chrome.runtime.onInstalled.addListener(() => {
  console.log('🦞 Claw Agent installed!');
});

console.log('🦞 Claw Agent background script loaded');

/**
 * Quick Fix: Auto-configure Chrome Extension API Keys
 * 
 * This script reads API keys from .env.local and saves them to Chrome storage.
 * Run this ONCE in the Chrome extension console to fix the 401 error.
 * 
 * HOW TO USE:
 * 1. Open Chrome extension side panel (click Claw icon)
 * 2. Right-click → Inspect to open DevTools
 * 3. Go to Console tab
 * 4. Copy and paste this ENTIRE script into the console
 * 5. Press Enter
 * 6. Reload the extension
 */

(async function setupApiKeys() {
  console.log('🦞 Claw Agent - Auto-configuring API keys...\n');
  
  // Your API keys from .env.local
  const CONFIG = {
    nvidia_api_key: '',
    dashscope_api_key: 'sk-dd-REDACTED',
    current_model: 'qwen/qwen3.5-397b-a17b'
  };
  
  try {
    // Save to Chrome storage
    await chrome.storage.sync.set({
      nvidia_api_key: CONFIG.nvidia_api_key,
      dashscope_api_key: CONFIG.dashscope_api_key,
      current_model: CONFIG.current_model
    });
    
    console.log('✅ SUCCESS! API keys configured:\n');
    console.log('   NVIDIA Key:', CONFIG.nvidia_api_key ? CONFIG.nvidia_api_key.substring(0, 15) + '...' : '(not set)');
    console.log('   DashScope Key:', CONFIG.dashscope_api_key.substring(0, 15) + '...');
    console.log('   Default Model:', CONFIG.current_model);
    console.log('\n🔄 Please RELOAD the extension (click reload icon in chrome://extensions/)');
    console.log('   Then open Claw Agent again and try a query.\n');
    
    // Notify background script
    chrome.runtime.sendMessage({ 
      type: 'settings-updated',
      ...CONFIG
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.log('⚠️ Background script not ready yet - reload extension anyway.\n');
      } else {
        console.log('✅ Background script notified of new settings.\n');
      }
    });
    
  } catch (error) {
    console.error('❌ FAILED to save API keys:', error.message);
    console.log('\nTry this instead:');
    console.log('1. Click the gear icon (⚙️) in Claw Agent');
    console.log('2. Enter your API keys manually');
    console.log('3. Click Save Settings\n');
  }
})();

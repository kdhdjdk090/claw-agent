// 🦞 Claw Agent - Auto-Load API Keys
// Generated automatically by setup-chrome-extension.js
// 
// INSTRUCTIONS:
// 1. Open Chrome extension side panel (click Claw icon)
// 2. Right-click → Inspect
// 3. Console tab
// 4. Paste this ENTIRE script
// 5. Press Enter
// 6. Reload extension

(async function autoLoadApiKeys() {
  console.log('🦞 Loading API keys from .env.local...\n');
  
  const CONFIG = {
    nvidia_api_key: '',
    dashscope_api_key: 'sk-dd-REDACTED',
    current_model: 'qwen/qwen3.5-397b-a17b'
  };
  
  try {
    await chrome.storage.sync.set(CONFIG);
    
    console.log('✅ SUCCESS! API keys configured:\n');
    console.log('   NVIDIA Key: ' + (CONFIG.nvidia_api_key ? CONFIG.nvidia_api_key.substring(0, 15) + '...' : '(not set)'));
    console.log('   DashScope Key:  ' + CONFIG.dashscope_api_key.substring(0, 15) + '...');
    console.log('   Default Model:  ' + CONFIG.current_model);
    console.log('\n🔄 RELOAD the extension now:');
    console.log('   1. Go to chrome://extensions/');
    console.log('   2. Click reload on Claw Agent');
    console.log('   3. Open side panel and test!\n');
    
    chrome.runtime.sendMessage({ type: 'settings-updated', ...CONFIG });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
})();

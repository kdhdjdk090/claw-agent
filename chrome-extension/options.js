/**
 * Claw Agent Options Page
 * Saves API keys to chrome.storage.sync
 */

// Load saved settings on page load
document.addEventListener('DOMContentLoaded', async () => {
  const nvidiaInput = document.getElementById('nvidia-api-key');
  const dashscopeInput = document.getElementById('dashscope-api-key');
  const modelSelect = document.getElementById('model-select');
  const saveBtn = document.getElementById('save-btn');
  const statusDiv = document.getElementById('status');
  
  // Load saved values
  try {
    const result = await chrome.storage.sync.get([
      'nvidia_api_key',
      'dashscope_api_key',
      'current_model'
    ]);
    
    if (result.nvidia_api_key) {
      nvidiaInput.value = result.nvidia_api_key;
    }
    if (result.dashscope_api_key) {
      dashscopeInput.value = result.dashscope_api_key;
    }
    if (result.current_model) {
      modelSelect.value = result.current_model;
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
  
  // Save settings
  saveBtn.addEventListener('click', async () => {
    const nvidiaKey = nvidiaInput.value.trim();
    const dashscopeKey = dashscopeInput.value.trim();
    const model = modelSelect.value;
    
    try {
      await chrome.storage.sync.set({
        nvidia_api_key: nvidiaKey,
        dashscope_api_key: dashscopeKey,
        current_model: model
      });
      
      statusDiv.className = 'status success';
      statusDiv.textContent = '✓ Settings saved! Reload the extension to apply changes.';
      
      // Also notify background script to reload config
      chrome.runtime.sendMessage({ 
        type: 'settings-updated',
        nvidia_api_key: nvidiaKey,
        dashscope_api_key: dashscopeKey,
        current_model: model
      });
      
    } catch (err) {
      statusDiv.className = 'status error';
      statusDiv.textContent = '✗ Failed to save: ' + err.message;
    }
  });
});

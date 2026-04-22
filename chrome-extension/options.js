/**
 * Claw Agent Options Page
 * Saves API keys to chrome.storage.sync
 */

const LEGACY_MODEL_MAP = {
  'qwen3.5-397b-a17b': 'qwen/qwen3.5-397b-a17b',
  'google/gemma-3-12b-it:free': 'google/gemma-4-27b-it',
  'google/gemma-3-12b-it': 'google/gemma-4-27b-it',
  'meta-llama/llama-3.3-70b-instruct:free': 'meta/llama-3.3-70b-instruct',
  'nousresearch/hermes-3-llama-3.1-405b:free': 'qwen/qwen3-next-80b-a3b-instruct'
};

function normalizeModel(modelValue) {
  return LEGACY_MODEL_MAP[modelValue] || modelValue;
}

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
      const normalizedModel = normalizeModel(result.current_model);
      modelSelect.value = normalizedModel;
      if (normalizedModel !== result.current_model) {
        await chrome.storage.sync.set({ current_model: normalizedModel });
      }
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
  
  // Save settings
  saveBtn.addEventListener('click', async () => {
    const nvidiaKey = nvidiaInput.value.trim();
    const dashscopeKey = dashscopeInput.value.trim();
    const model = normalizeModel(modelSelect.value);
    
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

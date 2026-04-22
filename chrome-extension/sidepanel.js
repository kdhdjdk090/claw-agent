/**
 * 🦞 Claw Agent - Side Panel (SIMPLIFIED & FIXED)
 * A working version that actually functions
 */

// API Configuration - AUTO-CONFIGURED
const CONFIG = {
  apiKey: '',
  apiBase: 'https://integrate.api.nvidia.com/v1',
  model: 'qwen/qwen3.5-397b-a17b',
  systemPrompt: 'You are Claw, a helpful AI browser agent. Be concise and helpful.'
};

const MODEL_OPTIONS = [
  { value: 'qwen/qwen3.5-397b-a17b', label: 'Qwen 3.5 397B', blurb: 'Primary general model' },
  { value: 'qwen/qwen3-next-80b-a3b-instruct', label: 'Qwen3 Next 80B', blurb: 'Fast balanced model' },
  { value: 'qwen/qwen3-coder-480b-a35b-instruct', label: 'Qwen3 Coder 480B', blurb: 'Heavy coding model' },
  { value: 'meta/llama-3.3-70b-instruct', label: 'Llama 3.3 70B', blurb: 'Stable generalist' },
  { value: 'nvidia/nemotron-4-340b-instruct', label: 'Nemotron 4 340B', blurb: 'Large reasoning model' },
  { value: 'google/gemma-4-27b-it', label: 'Gemma 4 27B', blurb: 'Midweight fast model' }
];

const LEGACY_MODEL_MAP = {
  'qwen3.5-397b-a17b': 'qwen/qwen3.5-397b-a17b',
  'google/gemma-3-12b-it:free': 'google/gemma-4-27b-it',
  'google/gemma-3-12b-it': 'google/gemma-4-27b-it',
  'meta-llama/llama-3.3-70b-instruct:free': 'meta/llama-3.3-70b-instruct',
  'nousresearch/hermes-3-llama-3.1-405b:free': 'qwen/qwen3-next-80b-a3b-instruct'
};

// Retry configuration for rate limits
const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 5000   // 5 seconds
};

// State
let messages = [];
let isLoading = false;

// DOM Elements
let inputEl, sendBtn, messagesEl, modelSelect, statusText;

function normalizeModel(modelValue) {
  return LEGACY_MODEL_MAP[modelValue] || modelValue;
}

function getModelMeta(modelValue) {
  const normalizedModel = normalizeModel(modelValue);
  return MODEL_OPTIONS.find(option => option.value === normalizedModel) || MODEL_OPTIONS[0];
}

function syncModelSelect() {
  if (!modelSelect) return;

  const options = MODEL_OPTIONS.map(option => (
    `<option value="${option.value}">${option.label}</option>`
  )).join('');

  modelSelect.innerHTML = options;
  modelSelect.value = getModelMeta(CONFIG.model).value;
}

function updateWelcomeCopy() {
  const titleEl = document.getElementById('welcomeTitle');
  const subtitleEl = document.getElementById('welcomeSubtitle');
  const modelMeta = getModelMeta(CONFIG.model);

  if (titleEl) titleEl.textContent = 'Claw Agent';
  if (subtitleEl) subtitleEl.textContent = `AI browser agent with ${modelMeta.label}`;
}

function updateReadyStatus() {
  if (!statusText) return;
  statusText.textContent = `✅ Ready - ${getModelMeta(CONFIG.model).label}`;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('🦞 Claw Agent Starting...');

  chrome.storage.sync.get(['nvidia_api_key', 'current_model'], (result) => {
    if (result.nvidia_api_key) {
      CONFIG.apiKey = result.nvidia_api_key;
    }
    if (result.current_model) {
      CONFIG.model = normalizeModel(result.current_model);
      if (CONFIG.model !== result.current_model) {
        chrome.storage.sync.set({ current_model: CONFIG.model });
      }
    }

    syncModelSelect();
    updateWelcomeCopy();
    updateReadyStatus();
  });
  
  // Get DOM elements
  inputEl = document.getElementById('input');
  sendBtn = document.getElementById('sendBtn');
  messagesEl = document.getElementById('messages');
  modelSelect = document.getElementById('modelSelect');
  statusText = document.getElementById('statusText');
  
  // Verify elements
  if (!inputEl || !sendBtn || !messagesEl) {
    console.error('❌ Missing DOM elements!');
    statusText.textContent = '❌ Error: UI not loaded';
    return;
  }
  
  console.log('✅ UI Elements loaded');
  syncModelSelect();
  updateWelcomeCopy();
  
  // Event listeners
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  modelSelect.addEventListener('change', (e) => {
    CONFIG.model = normalizeModel(e.target.value);
    chrome.storage.sync.set({ current_model: CONFIG.model });
    syncModelSelect();
    updateWelcomeCopy();
    updateReadyStatus();
    console.log('Model changed to:', CONFIG.model);
  });
  
  // Focus input
  inputEl.focus();
  
  // Update status
  updateReadyStatus();
  
  console.log('🚀 Claw Agent Ready!');
  console.log('   Using model:', CONFIG.model);
  console.log('   API Key configured:', !!CONFIG.apiKey);
});

// Send message function with retry logic
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || isLoading) return;

  if (!CONFIG.apiKey) {
    addMessage('error', '❌ NVIDIA API key is missing. Open the extension settings or run the Chrome setup helper, then reload the extension.');
    statusText.textContent = '❌ Missing NVIDIA API key';
    return;
  }
  
  // Clear welcome message
  const welcome = messagesEl.querySelector('.welcome');
  if (welcome) welcome.remove();
  
  // Add user message
  addMessage('user', text);
  inputEl.value = '';
  
  // Set loading state
  isLoading = true;
  sendBtn.disabled = true;
  sendBtn.textContent = '⏳';
  statusText.textContent = '🔄 Thinking...';
  
  let lastError = null;
  
  // Retry loop for rate limits
  for (let attempt = 0; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
    try {
      // Call API
      const response = await fetch(`${CONFIG.apiBase}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://github.com/claw-agent',
          'X-Title': 'Claw Agent'
        },
        body: JSON.stringify({
          model: CONFIG.model,
          messages: [
            { role: 'system', content: CONFIG.systemPrompt },
            ...messages.map(m => ({ role: m.role, content: m.content }))
          ],
          max_tokens: 2048,
          temperature: 0.7
        })
      });
      
      // Handle rate limit (429)
      if (response.status === 429) {
        if (attempt < RETRY_CONFIG.maxRetries) {
          const delay = Math.min(
            RETRY_CONFIG.baseDelay * Math.pow(2, attempt),
            RETRY_CONFIG.maxDelay
          );
          console.log(`⏳ Rate limited, retrying in ${delay}ms (attempt ${attempt + 1}/${RETRY_CONFIG.maxRetries})`);
          statusText.textContent = `⏳ Rate limited, retrying... (${attempt + 1}/${RETRY_CONFIG.maxRetries})`;
          await sleep(delay);
          continue;
        } else {
          throw new Error('Rate limited after all retries. Please wait a moment and try again.');
        }
      }
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const assistantMessage = data.choices[0].message.content;
      
      // Add assistant response
      addMessage('assistant', assistantMessage);
      
      // Save to history
      messages.push({ role: 'user', content: text });
      messages.push({ role: 'assistant', content: assistantMessage });
      
      statusText.textContent = `✅ Done - ${Math.round(data.usage?.total_tokens || 0)} tokens`;
      break; // Success, exit retry loop
      
    } catch (error) {
      lastError = error;
      console.error(`API Error (attempt ${attempt + 1}):`, error);
      
      // If this was the last attempt, show error
      if (attempt >= RETRY_CONFIG.maxRetries) {
        console.error('Final error:', error);
        const humanMessage = error instanceof TypeError && error.message === 'Failed to fetch'
          ? 'Network request blocked. Reload the extension after updating it, and confirm the NVIDIA endpoint is allowed.'
          : error.message;
        addMessage('error', `❌ ${humanMessage}`);
        statusText.textContent = '❌ Error: ' + humanMessage;
      }
    }
  }
  
  isLoading = false;
  sendBtn.disabled = false;
  sendBtn.textContent = '🚀';
  inputEl.focus();
}

// Helper function for delays
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Add message to UI
function addMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  
  if (role === 'user') {
    div.innerHTML = `<strong>You:</strong><br>${escapeHtml(content)}`;
  } else if (role === 'assistant') {
    div.innerHTML = `<strong>🦞 Claw:</strong><br>${formatResponse(content)}`;
  } else if (role === 'error') {
    div.innerHTML = `<span style="color: #ff4444;">${escapeHtml(content)}</span>`;
  }
  
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Format response (simple markdown)
function formatResponse(text) {
  return escapeHtml(text)
    .replace(/```(\w*)\n/g, '<pre style="background:#f0f0f0;padding:8px;border-radius:4px;margin:8px 0;"><code>')
    .replace(/```/g, '</code></pre>')
    .replace(/`([^`]+)`/g, '<code style="background:#f0f0f0;padding:2px 4px;border-radius:2px;">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

console.log('🦞 Claw Agent script loaded');

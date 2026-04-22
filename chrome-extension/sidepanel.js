/**
 * 🦞 Claw Agent - Side Panel (SIMPLIFIED & FIXED)
 * A working version that actually functions
 */

// API Configuration - AUTO-CONFIGURED
const CONFIG = {
  apiKey: '',
  apiBase: 'https://integrate.api.nvidia.com',
  model: 'meta/llama-3.3-70b-instruct',
  systemPrompt: 'You are Claw, a helpful AI browser agent. Be concise and helpful.'
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('🦞 Claw Agent Starting...');

  chrome.storage.sync.get(['nvidia_api_key', 'current_model'], (result) => {
    if (result.nvidia_api_key) {
      CONFIG.apiKey = result.nvidia_api_key;
    }
    if (result.current_model) {
      CONFIG.model = result.current_model;
    }
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
  
  // Event listeners
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  modelSelect.addEventListener('change', (e) => {
    CONFIG.model = e.target.value;
    console.log('Model changed to:', CONFIG.model);
  });
  
  // Focus input
  inputEl.focus();
  
  // Update status
  statusText.textContent = `✅ Ready - ${CONFIG.model}`;
  
  console.log('🚀 Claw Agent Ready!');
  console.log('   Using model:', CONFIG.model);
  console.log('   API Key configured:', !!CONFIG.apiKey);
});

// Send message function with retry logic
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || isLoading) return;
  
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
        addMessage('error', `❌ ${error.message}`);
        statusText.textContent = '❌ Error: ' + error.message;
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

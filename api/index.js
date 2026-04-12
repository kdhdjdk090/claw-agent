const fs = require('fs');
const path = require('path');

module.exports = (req, res) => {
  // Handle chat API
  if (req.url.startsWith('/api/chat') && req.method === 'POST') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { message } = JSON.parse(body);
        let reply = 'Hello!';
        
        if (message && message.toLowerCase().includes('hello')) {
          reply = "Hi! I'm Claw AI. Ask me about coding!";
        } else if (message && message.toLowerCase().includes('help')) {
          reply = "I can help with coding, debugging, and architecture!";
        } else if (message) {
          reply = `You said: "${message}". Try saying "hello" or "help"!`;
        }
        
        res.status(200).end(JSON.stringify({ reply }));
      } catch (e) {
        res.status(500).end(JSON.stringify({ error: 'Server error' }));
      }
    });
    return;
  }

  // Serve HTML for everything else
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claw AI - Chat</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: #1e1e2e; color: #e0e0e0; height: 100vh; }
    .app { display: flex; flex-direction: column; height: 100vh; }
    .header { background: #2d2d44; padding: 20px; border-bottom: 1px solid #4d4d6c; }
    .header h1 { font-size: 24px; color: #61dafb; margin: 0; }
    .chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 12px 15px; border-radius: 8px; max-width: 70%; word-wrap: break-word; }
    .msg.user { align-self: flex-end; background: #61dafb; color: #1e1e2e; margin-right: 10px; }
    .msg.ai { background: #2d2d44; border-left: 3px solid #61dafb; margin-left: 10px; }
    .footer { padding: 20px; border-top: 1px solid #4d4d6c; display: flex; gap: 10px; }
    input { flex: 1; padding: 12px; background: #2d2d44; border: 1px solid #4d4d6c; color: #e0e0e0; border-radius: 4px; font-size: 14px; }
    input:focus { outline: none; border-color: #61dafb; }
    button { padding: 12px 24px; background: #61dafb; color: #1e1e2e; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; }
    button:hover { background: #45e0f5; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .start { text-align: center; color: #666; padding: 40px 20px; }
  </style>
</head>
<body>
  <div class="app">
    <div class="header">
      <h1>🦅 Claw AI Chat</h1>
    </div>
    <div class="chat" id="chat">
      <div class="start">
        <p>Welcome to Claw AI Chat!</p>
        <p style="font-size: 12px; margin-top: 10px; color: #555;">Start typing to begin...</p>
      </div>
    </div>
    <div class="footer">
      <input type="text" id="input" placeholder="Type your message..." autocomplete="off">
      <button id="btn" onclick="send()">Send</button>
    </div>
  </div>

  <script>
    const chat = document.getElementById('chat');
    const input = document.getElementById('input');
    const btn = document.getElementById('btn');
    let first = true;

    function add(text, role) {
      if (first) {
        chat.innerHTML = '';
        first = false;
      }
      const msg = document.createElement('div');
      msg.className = 'msg ' + role;
      msg.textContent = text;
      chat.appendChild(msg);
      chat.scrollTop = chat.scrollHeight;
    }

    async function send() {
      const text = input.value.trim();
      if (!text) return;
      
      input.value = '';
      btn.disabled = true;
      add(text, 'user');

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        add(data.reply || 'No response', 'ai');
      } catch (e) {
        add('Connection error', 'ai');
      }
      
      btn.disabled = false;
      input.focus();
    }

    input.addEventListener('keypress', e => {
      if (e.key === 'Enter' && !e.ctrlKey) {
        e.preventDefault();
        send();
      }
    });

    input.focus();
  </script>
</body>
</html>`;

  res.status(200).end(html);
};

// Serve index.html
function serveIndex(res) {
  try {
    const indexPath = path.join(__dirname, '..', 'index.html');
    const content = fs.readFileSync(indexPath, 'utf-8');
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(content);
  } catch (err) {
    console.error('Error reading index.html:', err);
    return res.status(404).send('<h1>404 - Not Found</h1>');
  }
}

// Main handler
export default async (req, res) => {
  // Handle chat API
  if (req.url === '/api/chat' || req.url.startsWith('/api/chat')) {
    return handleChat(req, res);
  }

  // Serve HTML for all other paths
  return serveIndex(res);
};

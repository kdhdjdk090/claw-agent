const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claw AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); color: #e0e0e0; height: 100vh; overflow: hidden; }
        .container { display: flex; flex-direction: column; height: 100vh; background: #1e1e2e; }
        .header { background: linear-gradient(90deg, #2d2d44 0%, #3d3d5c 100%); padding: 20px; border-bottom: 1px solid #4d4d6c; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
        .header h1 { font-size: 24px; font-weight: 600; color: #61dafb; }
        .header p { font-size: 12px; color: #999; margin-top: 5px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; background: #1e1e2e; }
        .message { display: flex; gap: 12px; animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.user { justify-content: flex-end; }
        .message-content { max-width: 70%; padding: 12px 16px; border-radius: 12px; word-wrap: break-word; line-height: 1.4; }
        .message.assistant .message-content { background: #2d2d44; border-left: 3px solid #61dafb; }
        .message.user .message-content { background: #61dafb; color: #1e1e2e; }
        .input-area { padding: 20px; border-top: 1px solid #4d4d6c; background: #1e1e2e; display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 12px 16px; border: 1px solid #4d4d6c; border-radius: 8px; background: #2d2d44; color: #e0e0e0; outline: none; }
        input[type="text"]:focus { border-color: #61dafb; }
        button { padding: 12px 20px; background: #61dafb; color: #1e1e2e; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        button:hover { background: #45e0f5; transform: translateY(-2px); }
        button:disabled { background: #4d4d6c; cursor: not-allowed; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦅 Claw AI Chat</h1>
            <p>Powered by advanced AI reasoning engine</p>
        </div>
        <div class="chat-container" id="chatContainer">
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #666; text-align: center;">
                <div style="font-size: 48px; opacity: 0.5;">💬</div>
                <h2 style="font-size: 20px; color: #999; margin: 15px 0;">Start a conversation</h2>
                <p style="font-size: 14px; color: #666; max-width: 300px;">Ask me anything about coding, debugging, or ideas. I'm here to help!</p>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type your message..." autocomplete="off">
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        let isFirstMessage = true;

        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            userInput.value = '';
            
            if (isFirstMessage) {
                chatContainer.innerHTML = '';
                isFirstMessage = false;
            }

            addMessage(message, 'user');
            sendBtn.disabled = true;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const data = await response.json();
                addMessage(data.reply || 'No response', 'assistant');
            } catch (error) {
                addMessage('Error connecting to API', 'assistant');
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function addMessage(content, role) {
            const messageElement = document.createElement('div');
            messageElement.className = 'message ' + role;
            messageElement.innerHTML = '<div class="message-content">' + escapeHtml(content) + '</div>';
            chatContainer.appendChild(messageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        userInput.focus();
    </script>
</body>
</html>`;

module.exports = function handler(req, res) {
  // Handle chat API
  if (req.url === '/api/chat' && req.method === 'POST') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    try {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        const { message } = JSON.parse(body);
        let reply = 'Hello! Ask me anything about coding.';

        if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
          reply = "Hello! 👋 I'm Claw AI, your intelligent coding assistant. How can I help?";
        } else if (message.toLowerCase().includes('what is claw')) {
          reply = "Claw AI is an advanced coding assistant for debugging, code writing, architecture, and more!";
        } else if (message.toLowerCase().includes('help')) {
          reply = "I help with: 💻 Code, 🐛 Debugging, 📚 Concepts, 🏗️ Architecture, 🧪 Testing";
        }

        res.status(200).end(JSON.stringify({ reply }));
      });
    } catch (error) {
      res.status(500).end(JSON.stringify({ error: 'Server error' }));
    }
    return;
  }

  // Serve HTML for everything else
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.status(200).end(html);
};


module.exports = (req, res) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claw AI</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #1e1e2e; color: #e0e0e0; margin: 0; height: 100vh; display: flex; }
    .container { flex: 1; display: flex; flex-direction: column; }
    .header { background: #2d2d44; padding: 20px; border-bottom: 1px solid #4d4d6c; }
    .header h1 { margin: 0; font-size: 24px; color: #61dafb; }
    .chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 10px 15px; border-radius: 8px; max-width: 70%; }
    .msg.user { align-self: flex-end; background: #61dafb; color: #1e1e2e; }
    .msg.ai { background: #2d2d44; border-left: 3px solid #61dafb; }
    .input-box { padding: 20px; border-top: 1px solid #4d4d6c; display: flex; gap: 10px; }
    input { flex: 1; padding: 10px; background: #2d2d44; border: 1px solid #4d4d6c; color: #e0e0e0; border-radius: 4px; }
    button { padding: 10px 20px; background: #61dafb; color: #1e1e2e; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🦅 Claw AI Chat</h1>
    </div>
    <div class="chat" id="chat"></div>
    <div class="input-box">
      <input type="text" id="input" placeholder="Ask anything...">
      <button onclick="send()">Send</button>
    </div>
  </div>
  <script>
    const chat = document.getElementById('chat');
    const input = document.getElementById('input');
    
    function addMsg(text, role) {
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
      addMsg(text, 'user');
      
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        addMsg(data.reply || 'No response', 'ai');
      } catch (e) {
        addMsg('Error', 'ai');
      }
    }
    
    input.addEventListener('keypress', e => {
      if (e.key === 'Enter') send();
    });
  </script>
</body>
</html>`;

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.status(200).send(html);
};

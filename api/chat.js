const https = require('https');
const crypto = require('crypto');

// In-memory session store (in production, use Vercel KV or database)
const SESSIONS = {};

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  const { method, url } = req;
  const urlObj = new URL(url, `http://${req.headers.host}`);
  const path = urlObj.pathname;

  // POST /api/chat - Send message and get response
  if (method === 'POST' && path === '/api/chat') {
    return handleChat(req, res);
  }

  // GET /api/sessions - List all sessions
  if (method === 'GET' && path === '/api/sessions') {
    return res.json({
      sessions: Object.values(SESSIONS).map(s => ({
        id: s.id, created: s.created, updated: s.updated, turns: s.stats.turns,
        total_tokens: s.stats.total_tokens
      })),
      count: Object.keys(SESSIONS).length
    });
  }

  // GET /api/sessions/{id} - Get session details
  if (method === 'GET' && path.startsWith('/api/sessions/')) {
    const id = path.replace('/api/sessions/', '');
    if (!id || id.startsWith('_')) return res.status(400).json({ error: 'Invalid session ID' });
    const session = SESSIONS[id];
    return session ? res.json(session) : res.status(404).json({ error: 'Session not found' });
  }

  // DELETE /api/sessions/{id} - Delete session
  if (method === 'DELETE' && path.startsWith('/api/sessions/')) {
    const id = path.replace('/api/sessions/', '');
    if (!SESSIONS[id]) return res.status(404).json({ error: 'Session not found' });
    delete SESSIONS[id];
    return res.json({ message: 'Session deleted', session_id: id });
  }

  res.status(404).json({ error: 'Not found' });
};

async function handleChat(req, res) {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const { message, session_id } = JSON.parse(body);
      if (!message) return res.status(400).json({ error: 'message required' });

      const apiKey = process.env.DEEPSEEK_API_KEY;
      if (!apiKey) {
        return res.status(500).json({
          error: 'API key not configured',
          instructions: 'Set DEEPSEEK_API_KEY in Vercel environment'
        });
      }

      // Get or create session
      const sid = session_id || generateSessionId();
      let session = SESSIONS[sid] || {
        id: sid,
        messages: [],
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
        stats: { turns: 0, total_tokens: 0, prompt_tokens: 0, completion_tokens: 0 }
      };

      // Add user message
      session.messages.push({ role: 'user', content: message });
      session.stats.turns++;

      // Build conversation for API
      const conversationMessages = session.messages.map(m => ({
        role: m.role,
        content: m.content
      }));

      const payload = JSON.stringify({
        model: 'deepseek-chat',
        messages: conversationMessages,
        temperature: 0.7,
        max_tokens: 2048,
        stream: false
      });

      const options = {
        hostname: 'api.deepseek.com',
        port: 443,
        path: '/chat/completions',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'Authorization': `Bearer ${apiKey}`
        },
        timeout: 120000,
      };

      const request = https.request(options, (deepseekRes) => {
        let data = '';
        deepseekRes.on('data', chunk => data += chunk);
        deepseekRes.on('end', () => {
          try {
            const result = JSON.parse(data);
            if (result.error) {
              return res.status(400).json({ error: result.error.message, session_id: sid });
            }
            const reply = result.choices?.[0]?.message?.content || 'No response';
            session.messages.push({ role: 'assistant', content: reply });
            session.updated = new Date().toISOString();
            session.stats.total_tokens += result.usage?.total_tokens || 0;
            session.stats.prompt_tokens += result.usage?.prompt_tokens || 0;
            session.stats.completion_tokens += result.usage?.completion_tokens || 0;
            SESSIONS[sid] = session;

            res.json({
              reply, session_id: sid, turn: session.stats.turns,
              tokens: result.usage, session_stats: session.stats
            });
          } catch (e) {
            res.status(500).json({ error: 'Parse error', session_id: sid });
          }
        });
      });

      request.on('error', error => {
        res.status(503).json({ error: error.message, session_id: sid });
      });

      request.on('timeout', () => {
        request.destroy();
        res.status(504).json({ error: 'Timeout', session_id: sid });
      });

      request.write(payload);
      request.end();
    } catch (e) {
      res.status(400).json({ error: e.message });
    }
  });
}

function generateSessionId() {
  return `claw-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
}

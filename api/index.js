const https = require('https');
const fs = require('fs');
const path = require('path');

// Read the updated index.html from project root
const HTML_PATH = path.join(__dirname, '..', 'index.html');

module.exports = async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // POST /api/chat - Send message to DeepSeek API
  if (req.url.startsWith('/api/chat') && req.method === 'POST') {
    return handleChat(req, res);
  }

  // Serve the updated index.html with slash command support
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  try {
    const html = fs.readFileSync(HTML_PATH, 'utf-8');
    return res.status(200).end(html);
  } catch (err) {
    // Fallback if index.html not found
    res.status(200).end('<h1>Claw AI - Coming Soon</h1>');
  }
};

async function handleChat(req, res) {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const { message, model } = JSON.parse(body);
      
      if (!message) {
        return res.status(400).json({ error: 'message required' });
      }

      const apiKey = process.env.DEEPSEEK_API_KEY;
      if (!apiKey) {
        return res.status(500).json({
          error: 'API key not configured. Set DEEPSEEK_API_KEY in Vercel environment variables.',
          instructions: 'Go to Vercel Dashboard → Project Settings → Environment Variables → Add DEEPSEEK_API_KEY'
        });
      }

      // Call DeepSeek API
      const payload = JSON.stringify({
        model: model || 'deepseek-chat',
        messages: [
          { role: 'system', content: 'You are Claw AI, an expert autonomous AI coding agent. You act decisively and never ask questions. When asked what model you are, say you are Claw running via Cloud API.' },
          { role: 'user', content: message }
        ],
        temperature: 0.7,
        max_tokens: 2048,
        stream: false
      });

      const result = await callDeepSeekAPI(apiKey, payload);
      
      if (result.error) {
        return res.status(400).json({ error: result.error.message });
      }

      const reply = result.choices?.[0]?.message?.content || 'No response';
      const usage = result.usage || {};

      res.status(200).json({
        reply,
        usage,
        model: model || 'deepseek-chat'
      });
    } catch (e) {
      console.error('Chat error:', e.message);
      res.status(500).json({ error: e.message });
    }
  });
}

function callDeepSeekAPI(apiKey, payload) {
  return new Promise((resolve, reject) => {
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
          resolve(result);
        } catch (e) {
          reject(new Error('Failed to parse DeepSeek response'));
        }
      });
    });

    request.on('error', error => {
      reject(new Error(`DeepSeek API error: ${error.message}`));
    });

    request.on('timeout', () => {
      request.destroy();
      reject(new Error('Request timeout'));
    });

    request.write(payload);
    request.end();
  });
}

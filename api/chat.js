const https = require('https');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'POST') {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message required' });
    }

    const apiKey = process.env.DEEPSEEK_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ 
        error: 'DeepSeek API key not configured',
        instructions: 'Set DEEPSEEK_API_KEY environment variable in Vercel'
      });
    }

    try {
      // Call DeepSeek API
      const payload = JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'user', content: message }
        ],
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

        deepseekRes.on('data', (chunk) => {
          data += chunk;
        });

        deepseekRes.on('end', () => {
          try {
            const result = JSON.parse(data);
            
            if (result.error) {
              return res.status(400).json({ 
                error: result.error.message || 'DeepSeek API error',
                type: result.error.type
              });
            }

            const reply = result.choices?.[0]?.message?.content || 'No response';
            const tokens = result.usage?.completion_tokens || 0;

            res.status(200).json({
              reply: reply,
              model: 'deepseek-chat',
              tokens: tokens,
              usage: {
                prompt_tokens: result.usage?.prompt_tokens,
                completion_tokens: result.usage?.completion_tokens,
                total_tokens: result.usage?.total_tokens
              }
            });
          } catch (e) {
            res.status(500).json({ error: 'Failed to parse DeepSeek response' });
          }
        });
      });

      request.on('error', (error) => {
        if (error.code === 'ENOTFOUND') {
          res.status(503).json({ error: 'Cannot reach DeepSeek API' });
        } else {
          res.status(500).json({ error: error.message });
        }
      });

      request.on('timeout', () => {
        request.destroy();
        res.status(504).json({ error: 'DeepSeek request timeout' });
      });

      request.write(payload);
      request.end();

    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
};

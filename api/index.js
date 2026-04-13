const https = require('https');
const fs = require('fs');
const path = require('path');

// Read the updated index.html from project root
const HTML_PATH = path.join(__dirname, '..', 'index.html');
const OPENAPI_PATH = path.join(__dirname, 'openapi.json');

// Allowed CORS origins (add your production domain)
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim());

// OpenRouter configuration - API keys from environment variables only
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_API_BASE = 'https://openrouter.ai/api/v1';

// Alibaba Cloud (DashScope) configuration
const DASHSCOPE_API_KEY = process.env.DASHSCOPE_API_KEY || '';
const DASHSCOPE_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1';

// Council models - OpenRouter (8) + Alibaba Cloud (6) = 14 total
const OPENROUTER_MODELS = [
  'deepseek/deepseek-v3',
  'qwen/qwen3-80b',
  'meta-llama/llama-3.3-70b-instruct',
  'qwen/qwen-2.5-coder-32b-instruct',
  'deepseek/deepseek-r1',
  'google/gemma-3-12b-it',
  'openai/gpt-4o-mini',
  'anthropic/claude-3-haiku-20240307'
];

const ALIBABA_MODELS = [
  'qwen3-coder-480b-a35b-instruct',  // 🏆 Best Coder (480B)
  'qwen3.5-397b-a17b',               // 🥇 Most Powerful (397B)
  'qwen3-max',                        // 🥈 Flagship
  'qwen3-235b-a22b',                 // 🧮 Reasoning (235B)
  'qwen3-coder-plus',                // ⭐ Coding Specialist
  'qwen-plus'                         // ⚡ Fast Balanced
];

const COUNCIL_MODELS = [...OPENROUTER_MODELS, ...ALIBABA_MODELS];

const COUNCIL_THRESHOLD = parseFloat(process.env.COUNCIL_THRESHOLD || '0.6');

// Council is enabled if we have an OpenRouter key
const COUNCIL_ENABLED = OPENROUTER_API_KEY && OPENROUTER_API_KEY.length > 10;

module.exports = async (req, res) => {
  // Set CORS headers
  const origin = req.headers.origin || '*';
  const allowedOrigin = ALLOWED_ORIGINS.includes('*') ? '*' : (ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0]);
  res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // GET /api/health - Health check endpoint
  if (req.url.startsWith('/api/health') && req.method === 'GET') {
    return res.status(200).json({
      status: 'ok',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      keys_configured: {
        openrouter: !!OPENROUTER_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
      }
    });
  }

  // GET /api/openapi.json - Serve OpenAPI spec
  if (req.url.startsWith('/api/openapi.json') && req.method === 'GET') {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    try {
      const spec = fs.readFileSync(OPENAPI_PATH, 'utf-8');
      return res.status(200).end(spec);
    } catch (err) {
      return res.status(404).json({ error: 'OpenAPI spec not found' });
    }
  }

  // GET /api/docs - Swagger UI
  if (req.url.startsWith('/api/docs') && req.method === 'GET') {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).end(`<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Claw AI - API Documentation</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<style>body{margin:0;background:#f8fafc}.topbar{display:none!important}
.swagger-ui .info .title{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.swagger-ui .scheme-container{background:#f1f5f9;box-shadow:none;border-bottom:1px solid #e2e8f0}
</style></head><body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:'/api/openapi.json',dom_id:'#swagger-ui',deepLinking:true,presets:[SwaggerUIBundle.presets.apis],layout:'BaseLayout'})</script>
</body></html>`);
  }

  // POST /api/chat - Send message to AI (Council or single model)
  if (req.url.startsWith('/api/chat') && req.method === 'POST') {
    return handleChat(req, res);
  }

  // POST /api/council - Explicit council endpoint
  if (req.url.startsWith('/api/council') && req.method === 'POST') {
    return handleCouncil(req, res);
  }

  // GET /api/models - List available council models
  if (req.url.startsWith('/api/models') && req.method === 'GET') {
    return res.status(200).json({
      council: COUNCIL_MODELS,
      council_enabled: COUNCIL_ENABLED,
      mode: COUNCIL_ENABLED ? 'council' : (process.env.DEEPSEEK_API_KEY ? 'deepseek' : 'ollama'),
      api_key_set: !!OPENROUTER_API_KEY,
      alibaba_key_set: !!DASHSCOPE_API_KEY,
      providers: ['OpenRouter', 'Alibaba Cloud (DashScope)'],
      openrouter_models: OPENROUTER_MODELS.length,
      alibaba_models: ALIBABA_MODELS.length,
      model_count: COUNCIL_MODELS.length
    });
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
  let bodySize = 0;
  const MAX_BODY_SIZE = 100 * 1024; // 100KB limit
  req.on('data', chunk => {
    bodySize += chunk.length;
    if (bodySize > MAX_BODY_SIZE) {
      req.destroy();
      return res.status(413).json({ error: 'Request body too large (max 100KB)' });
    }
    body += chunk;
  });
  req.on('end', async () => {
    try {
      const { message, model, use_council } = JSON.parse(body);

      if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: 'message required (string)' });
      }

      if (message.length > 32000) {
        return res.status(400).json({ error: 'message too long (max 32000 chars)' });
      }

      // Use council if enabled and requested
      if (use_council || (!model && OPENROUTER_API_KEY)) {
        return handleCouncilRequest(res, message);
      }

      // Single model mode
      const apiKey = OPENROUTER_API_KEY || process.env.DEEPSEEK_API_KEY;
      if (!apiKey) {
        return res.status(500).json({
          error: 'API key not configured. Set OPENROUTER_API_KEY or DEEPSEEK_API_KEY in Vercel environment variables.',
          instructions: 'Go to Vercel Dashboard → Project Settings → Environment Variables → Add OPENROUTER_API_KEY'
        });
      }

      const selectedModel = model || COUNCIL_MODELS[0];
      
      // Call OpenRouter API (single model)
      const payload = JSON.stringify({
        model: selectedModel,
        messages: [
          { role: 'system', content: 'You are Claw AI, an expert autonomous AI coding agent. You act decisively and never ask questions. When asked what model you are, say you are Claw running via OpenRouter Council.' },
          { role: 'user', content: message }
        ],
        temperature: 0.7,
        max_tokens: 2048,
      });

      const result = await callOpenRouterAPI(apiKey, payload);

      if (result.error) {
        return res.status(400).json({ error: result.error.message });
      }

      const reply = result.choices?.[0]?.message?.content || 'No response';
      const usage = result.usage || {};

      res.status(200).json({
        reply,
        usage,
        model: selectedModel,
        council: false
      });
    } catch (e) {
      console.error('Chat error:', e.message);
      res.status(500).json({ error: e.message });
    }
  });
}

async function handleCouncil(req, res) {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const { message } = JSON.parse(body);

      if (!message) {
        return res.status(400).json({ error: 'message required' });
      }

      if (!OPENROUTER_API_KEY) {
        return res.status(500).json({
          error: 'OpenRouter API key not configured. Set OPENROUTER_API_KEY in Vercel environment variables.',
        });
      }

      return handleCouncilRequest(res, message);
    } catch (e) {
      console.error('Council error:', e.message);
      res.status(500).json({ error: e.message });
    }
  });
}

async function handleCouncilRequest(res, message) {
  // Query all council models in parallel (OpenRouter + Alibaba)
  const promises = COUNCIL_MODELS.map(async (model) => {
    try {
      // Check if this is an Alibaba model
      const isAlibaba = ALIBABA_MODELS.includes(model);
      
      let payload, apiBase, headers;
      
      if (isAlibaba) {
        // Alibaba Cloud API
        payload = JSON.stringify({
          model,
          messages: [
            { role: 'system', content: 'You are Claw AI, an expert autonomous AI coding agent. You act decisively and never ask questions.' },
            { role: 'user', content: message }
          ],
          temperature: 0.7,
          max_tokens: 2048,
        });
        apiBase = DASHSCOPE_API_BASE;
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${DASHSCOPE_API_KEY}`,
        };
      } else {
        // OpenRouter API
        payload = JSON.stringify({
          model,
          messages: [
            { role: 'system', content: 'You are Claw AI, an expert autonomous AI coding agent. You act decisively and never ask questions.' },
            { role: 'user', content: message }
          ],
          temperature: 0.7,
          max_tokens: 2048,
        });
        apiBase = OPENROUTER_API_BASE;
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://github.com/claw-agent',
          'X-Title': 'Claw AI Council',
        };
      }

      const result = await callAPI(apiBase, payload, headers);
      const content = result.choices?.[0]?.message?.content || '';
      return { model, content, error: null, usage: result.usage || {}, provider: isAlibaba ? 'alibaba' : 'openrouter' };
    } catch (error) {
      return { model, content: '', error: error.message, usage: {}, provider: ALIBABA_MODELS.includes(model) ? 'alibaba' : 'openrouter' };
    }
  });

  const responses = await Promise.all(promises);
  
  // Filter successful responses
  const successful = responses.filter(r => !r.error);
  const failed = responses.filter(r => r.error);

  if (successful.length === 0) {
    return res.status(500).json({ 
      error: 'All models failed',
      details: failed.map(f => ({ model: f.model, error: f.error }))
    });
  }

  // Find consensus (simplified: group by content similarity)
  const groups = {};
  for (const resp of successful) {
    const normalized = resp.content.substring(0, 100).toLowerCase().trim();
    let matched = false;
    
    for (const key of Object.keys(groups)) {
      if (key.includes(normalized) || normalized.includes(key) || 
          similarity(key, normalized) > 0.7) {
        groups[key].push(resp);
        matched = true;
        break;
      }
    }
    
    if (!matched) {
      groups[normalized] = [resp];
    }
  }

  // Find the largest group (consensus)
  let bestGroup = null;
  let bestKey = '';
  for (const [key, group] of Object.entries(groups)) {
    if (!bestGroup || group.length > bestGroup.length) {
      bestGroup = group;
      bestKey = key;
    }
  }

  const consensusPercentage = bestGroup.length / successful.length;
  const totalTokens = successful.reduce((sum, r) => sum + (r.usage.total_tokens || 0), 0);

  // Build response - FIX: Only use the first model's content, strip consensus tags
  let reply = '';
  if (bestGroup.length > 0 && bestGroup[0].content) {
    reply = bestGroup[0].content.trim();
  } else {
    // Fallback: find any model with content
    for (const r of successful) {
      if (r.content && r.content.trim()) {
        reply = r.content.trim();
        break;
      }
    }
  }

  res.status(200).json({
    reply,
    council: true,
    models_queried: COUNCIL_MODELS.length,
    successful_responses: successful.length,
    failed_responses: failed.length,
    consensus_percentage: (consensusPercentage * 100).toFixed(0),
    total_tokens: totalTokens,
    all_responses: responses.map(r => ({
      model: r.model,
      content: r.content?.substring(0, 100) + (r.content?.length > 100 ? '...' : ''),
      error: r.error
    }))
  });
}

function callAPI(apiBase, payload, headers) {
  const url = new URL(`${apiBase}/chat/completions`);
  return new Promise((resolve, reject) => {
    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname,
      method: 'POST',
      headers: {
        ...headers,
        'Content-Length': Buffer.byteLength(payload),
      },
      timeout: 60000,
    };

    const request = https.request(options, (apiRes) => {
      let data = '';
      apiRes.on('data', chunk => data += chunk);
      apiRes.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (apiRes.statusCode !== 200) {
            resolve({ error: { message: result.error?.message || 'API error' } });
          } else {
            resolve(result);
          }
        } catch (e) {
          reject(new Error('Failed to parse API response'));
        }
      });
    });

    request.on('error', error => reject(new Error(`API error: ${error.message}`)));
    request.on('timeout', () => { request.destroy(); reject(new Error('Request timeout')); });
    request.write(payload);
    request.end();
  });
}

function callOpenRouterAPI(apiKey, payload) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${OPENROUTER_API_BASE}/chat/completions`);
    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'https://github.com/claw-agent',
        'X-Title': 'Claw AI Council',
      },
      timeout: 120000,
    };

    const request = https.request(options, (apiRes) => {
      let data = '';
      apiRes.on('data', chunk => data += chunk);
      apiRes.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (apiRes.statusCode !== 200) {
            resolve({ error: { message: result.error?.message || 'API error' } });
          } else {
            resolve(result);
          }
        } catch (e) {
          reject(new Error('Failed to parse OpenRouter response'));
        }
      });
    });

    request.on('error', error => {
      reject(new Error(`OpenRouter API error: ${error.message}`));
    });

    request.on('timeout', () => {
      request.destroy();
      reject(new Error('Request timeout'));
    });

    request.write(payload);
    request.end();
  });
}

// Simple string similarity (Jaccard index)
function similarity(str1, str2) {
  if (!str1 || !str2) return 0;
  const set1 = new Set(str1.split(' '));
  const set2 = new Set(str2.split(' '));
  const intersection = [...set1].filter(x => set2.has(x));
  const union = new Set([...set1, ...set2]);
  return intersection.length / union.size;
}

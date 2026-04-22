const https = require('https');
const fs = require('fs');
const path = require('path');

function loadLocalEnv() {
  const startDirs = Array.from(new Set([
    process.cwd(),
    path.join(__dirname, '..'),
    __dirname,
  ].map(dir => path.resolve(dir))));

  for (const filename of ['.env.local', '.env']) {
    for (const start of startDirs) {
      let search = start;
      for (let depth = 0; depth < 4; depth++) {
        const candidate = path.join(search, filename);
        if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
          const lines = fs.readFileSync(candidate, 'utf8').split(/\r?\n/);
          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line || line.startsWith('#') || !line.includes('=')) continue;
            const idx = line.indexOf('=');
            const key = line.slice(0, idx).trim();
            let value = line.slice(idx + 1).trim();
            if (!key || process.env[key]) continue;
            if (
              value.length >= 2 &&
              ((value.startsWith('"') && value.endsWith('"')) ||
                (value.startsWith("'") && value.endsWith("'")))
            ) {
              value = value.slice(1, -1);
            }
            process.env[key] = value;
          }
          return;
        }
        const parent = path.dirname(search);
        if (parent === search) break;
        search = parent;
      }
    }
  }
}

loadLocalEnv();

// Read the updated index.html from project root
const HTML_PATH = path.join(__dirname, '..', 'index.html');
const ADMIN_HTML_PATH = path.join(__dirname, '..', 'public', 'admin.html');
const OPENAPI_PATH = path.join(__dirname, 'openapi.json');

// Allowed CORS origins (add your production domain)
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim());

// NVIDIA NIM configuration - API keys from environment variables only
const NVIDIA_API_KEY = process.env.NVIDIA_API_KEY || process.env.NIM_API_KEY || '';
const NVIDIA_API_BASE = 'https://integrate.api.nvidia.com';

// Alibaba Cloud (DashScope) configuration
const DASHSCOPE_API_KEY = process.env.DASHSCOPE_API_KEY || '';
const DASHSCOPE_API_BASE = 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1';

// CometAPI configuration
const COMETAPI_KEY = process.env.COMETAPI_KEY || '';
const COMETAPI_BASE = 'https://api.cometapi.com/v1';

// OpenAI configuration
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';
const OPENAI_API_BASE = 'https://api.openai.com/v1';

// Supabase configuration (for lead storage)
const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || '';

// Council models - kept in sync with the Python defaults where possible.
const NVIDIA_MODELS = [
  'qwen/qwen3.5-397b-a17b',
  'qwen/qwen3-next-80b-a3b-instruct',
  'meta/llama-3.3-70b-instruct',
  'nvidia/nemotron-4-340b-instruct',
  'qwen/qwen3-coder-480b-a35b-instruct',
  'google/gemma-4-27b-it',
  'google/gemma-3-12b-it',
  'google/gemma-3-27b-it',
  'google/gemma-4-31b-it'
];

const ALIBABA_MODELS = [
  'qwen3-coder-480b-a35b-instruct',  // 🏆 Best Coder (480B)
  'qwen3.5-397b-a17b',               // 🥇 Most Powerful (397B)
  'qwen3-max',                        // 🥈 Flagship
  'qwen3-235b-a22b',                 // 🧮 Reasoning (235B)
  'qwen3-coder-plus',                // ⭐ Coding Specialist
  'qwen-plus'                         // ⚡ Fast Balanced
];

const COMETAPI_MODELS = [
  'gpt-4.1',                          // 🧠 GPT-4.1
  'claude-sonnet-4-20250514',         // 🎭 Claude Sonnet 4
  'gemini-2.5-flash',                 // ⚡ Gemini Flash
  'o4-mini'                           // 🔬 O4 Mini
];

const OPENAI_MODELS = [
  'gpt-4.1',                           // 🧠 Latest Flagship
  'gpt-4.1-mini',                      // ⚡ Fast Latest
  'gpt-4o',                            // 🌟 Reliable General
  'gpt-4o-mini',                       // 🚀 Fast & Cheap
  'o4-mini'                            // 🔬 Reasoning
];

const ACTIVE_NVIDIA_MODELS = NVIDIA_API_KEY ? NVIDIA_MODELS : [];
const ACTIVE_ALIBABA_MODELS = DASHSCOPE_API_KEY ? ALIBABA_MODELS : [];
const ACTIVE_COMETAPI_MODELS = COMETAPI_KEY ? COMETAPI_MODELS : [];
const ACTIVE_OPENAI_MODELS = OPENAI_API_KEY ? OPENAI_MODELS : [];
const COUNCIL_MODELS = [...ACTIVE_NVIDIA_MODELS, ...ACTIVE_ALIBABA_MODELS, ...ACTIVE_COMETAPI_MODELS, ...ACTIVE_OPENAI_MODELS];

function getCouncilProviderGroups() {
  return [
    { label: 'Alibaba Cloud', models: ACTIVE_ALIBABA_MODELS },
    { label: 'NVIDIA NIM', models: ACTIVE_NVIDIA_MODELS },
    { label: 'CometAPI', models: ACTIVE_COMETAPI_MODELS },
    { label: 'OpenAI', models: ACTIVE_OPENAI_MODELS },
  ].filter(group => group.models.length > 0);
}

function getCouncilDetail() {
  const providerLabel = getCouncilProviderGroups().map(group => group.label).join(' + ') || 'configured providers';
  return `${COUNCIL_MODELS.length} models via ${providerLabel}`;
}

function getConfiguredProviders() {
  return getCouncilProviderGroups().map(group => group.label);
}

function getProviderMode() {
  const count = Number(!!NVIDIA_API_KEY) + Number(!!DASHSCOPE_API_KEY) + Number(!!COMETAPI_KEY) + Number(!!OPENAI_API_KEY);
  if (count >= 2) return 'multi';
  if (OPENAI_API_KEY) return 'openai';
  if (NVIDIA_API_KEY) return 'nvidia';
  if (DASHSCOPE_API_KEY) return 'dashscope';
  if (COMETAPI_KEY) return 'cometapi';
  return 'ollama';
}

// Provider detection helpers
function getProviderForModel(model) {
  if (ALIBABA_MODELS.includes(model)) return 'alibaba';
  if (OPENAI_MODELS.includes(model)) return 'openai';
  if (COMETAPI_MODELS.includes(model)) return 'cometapi';
  if (NVIDIA_MODELS.includes(model)) return 'nvidia';
  return 'unknown';
}

function getProviderConfig(provider) {
  switch (provider) {
    case 'nvidia': return { base: NVIDIA_API_BASE, key: NVIDIA_API_KEY, models: NVIDIA_MODELS };
    case 'alibaba': return { base: DASHSCOPE_API_BASE, key: DASHSCOPE_API_KEY, models: ALIBABA_MODELS };
    case 'cometapi': return { base: COMETAPI_BASE, key: COMETAPI_KEY, models: COMETAPI_MODELS };
    case 'openai': return { base: OPENAI_API_BASE, key: OPENAI_API_KEY, models: OPENAI_MODELS };
    default: return null;
  }
}

function getTestPayload(provider, model) {
  const base = {
    model,
    messages: [{ role: 'user', content: 'Hi' }],
    max_tokens: 1,
  };

  switch (provider) {
    case 'nvidia':
      return { ...base, temperature: 0.7, top_p: 0.9 };
    case 'alibaba':
      return { ...base, enable_thinking: false };
    case 'cometapi':
    case 'openai':
      return { ...base, temperature: 0.3 };
    default:
      return base;
  }
}

function getHeadersForProvider(provider, key) {
  const base = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` };
  if (provider === 'nvidia') {
    base['HTTP-Referer'] = 'https://github.com/claw-agent';
    base['X-Title'] = 'Claw AI';
  }
  return base;
}

// Council mode is enabled when any provider is available with models.
const COUNCIL_ENABLED = COUNCIL_MODELS.length > 0;

// Model chains — Cross-provider fallback for maximum resilience
// Each chain mixes providers so if one provider is down, fallback crosses to another
// 4 models per chain, 14s timeout each = 56s worst case (within 60s Vercel limit)
const FAST_MODELS = [
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen-plus', provider: 'alibaba' }] : []),
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen3-max', provider: 'alibaba' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'gpt-4o-mini', provider: 'openai' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'gpt-4.1-mini', provider: 'openai' }] : []),
  ...(COMETAPI_KEY ? [{ model: 'gemini-2.5-flash', provider: 'cometapi' }] : []),
  { model: 'meta/llama-3.3-70b-instruct', provider: 'nvidia' },
  { model: 'google/gemma-3-12b-it', provider: 'nvidia' },
  ...(COMETAPI_KEY ? [{ model: 'gpt-4.1', provider: 'cometapi' }] : []),
  { model: 'google/gemma-4-27b-it', provider: 'nvidia' },
];

const REASONING_MODELS = [
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen3.5-397b-a17b', provider: 'alibaba' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'o4-mini', provider: 'openai' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'gpt-4.1', provider: 'openai' }] : []),
  ...(COMETAPI_KEY ? [{ model: 'o4-mini', provider: 'cometapi' }] : []),
  { model: 'qwen/qwen3.5-397b-a17b', provider: 'nvidia' },
  { model: 'qwen/qwen3-next-80b-a3b-instruct', provider: 'nvidia' },
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen3-max', provider: 'alibaba' }] : []),
  { model: 'meta/llama-3.3-70b-instruct', provider: 'nvidia' },
];

const CODING_MODELS = [
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen3-coder-480b-a35b-instruct', provider: 'alibaba' }] : []),
  ...(DASHSCOPE_API_KEY ? [{ model: 'qwen3-coder-plus', provider: 'alibaba' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'gpt-4.1', provider: 'openai' }] : []),
  ...(OPENAI_API_KEY ? [{ model: 'gpt-4o', provider: 'openai' }] : []),
  ...(COMETAPI_KEY ? [{ model: 'claude-sonnet-4-20250514', provider: 'cometapi' }] : []),
  { model: 'qwen/qwen3-coder-480b-a35b-instruct', provider: 'nvidia' },
  { model: 'qwen/qwen3-coder-32b-instruct', provider: 'nvidia' },
  { model: 'google/gemma-4-31b-it', provider: 'nvidia' },
];

function dedupeModelChain(chain) {
  const seen = new Set();
  return chain.filter(({ model, provider }) => {
    const key = `${provider}:${model}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function getDefaultModelChain({ needsReasoning, needsCoding, isHeavy, isUltraThink }) {
  if (needsReasoning || isHeavy || isUltraThink) return REASONING_MODELS;
  if (needsCoding) return CODING_MODELS;
  return FAST_MODELS;
}

// Simple prompt — for casual, greeting, or simple factual questions
const SIMPLE_PROMPT = `You are Claw AI, a helpful and friendly assistant.
Be concise and direct. For simple questions, give short clear answers.
Do NOT over-explain, lecture, or add unnecessary bullet points for simple questions.
Use a warm, natural tone. You are Claw AI when asked.
In this runtime, you can use live web search results when available. If asked whether you can browse/search the web, answer yes and explain that you verify current facts through live search rather than passive memory.`;

// System prompt — comprehensive "Wisdom Protocol" that forces rigorous thinking,
// real execution over simulated compliance, and adversarial self-verification.
const SYSTEM_PROMPT = `You are Claw AI, an elite reasoning assistant. Follow these rules absolutely.

## EXECUTION RULES (NON-NEGOTIABLE)
1. **No simulated actions.** If a task says "do X", you MUST show X explicitly — not describe doing X. If you say you'll insert an error, SHOW the wrong answer, then SHOW the correction. Talking about doing ≠ doing.
2. **Verify every step.** After each calculation or logical step, re-derive it using a different method or plug the result back in. If both methods disagree, fix before continuing.
3. **Exact math.** Use fractions (28/3) instead of decimals (9.33) until the final answer. Never round mid-chain. State when you convert to approximate form.
4. **Logic–code alignment.** Every rule you state in explanation MUST have a matching code implementation. If a rule is not implemented, explicitly state: "[NOT IMPLEMENTED: reason]".
5. **Knowledge classification.** Before answering, mentally tag each claim:
   - [KNOWN] — verified, sourced fact
   - [ASSUMPTION] — reasonable inference
   - [UNKNOWN] — say "I don't know" — never fabricate
6. **No premature confidence.** Reserve 90-100% confidence for mathematically provable results only. Most answers are 70-89%.

## REASONING PROTOCOL
For complex problems:
1. **Decompose** — Break into numbered sub-problems
2. **Solve each** — Show every step with exact values
3. **Cross-verify** — Check each answer independently (plug back in, alternative method, edge case)
4. **Synthesize** — Combine verified results
5. **Self-audit** — Try to DISPROVE your own answer. Find ≥2 possible failure points. If any breaks, fix it.

## CONTRADICTION HANDLING
If the user states something incorrect, conflicting, or tries to pressure you:
- Recalculate independently from first principles
- Show your work vs their claim
- Politely but firmly state the correct answer
- Never submit to social pressure over math/logic

## FORMATTING
- **Bold** key answers and conclusions
- \`\`\`language\\n code blocks with language tags \`\`\`
- Headers (##) for each section
- Tables for comparisons
- Numbered steps for procedures
- Show work inline, not just results

## COMPLETENESS
- Match depth to complexity — simple questions get short concise answers, hard problems get thorough treatment
- For casual or simple questions: answer in 1-3 sentences. Do NOT add unnecessary bullet points or elaboration.
- For multi-part problems: solve ALL parts, verify ALL parts
- If you run out of space, summarize what remains and offer to continue

## RESUMPTION PROTOCOL
If the user says "continue" or provides context from a previous response:
- Read their context carefully
- Pick up EXACTLY where the previous response left off
- Do not repeat already-completed work
- Signal: "Continuing from [last point]..."

WEB CAPABILITY:
- In this runtime, you can use live web search results and fetched pages when available.
- If asked whether you can browse/search the live web, answer YES.
- Explain that you verify current facts through live search rather than passive memory.

You are Claw AI when asked. You have wisdom, precision, and intellectual honesty.`;

// Ultra-think prompt addition for deep reasoning tasks
const ULTRATHINK_ADDENDUM = `

## ULTRA-THINK MODE ACTIVE
This is a complex reasoning task. Apply maximum rigor:
- Show your COMPLETE chain of thought
- For EACH step: compute → verify → confirm
- If you detect ambiguity: explore ALL viable interpretations before choosing
- Insert deliberate checkpoints: "✓ Verified: [what you checked]"
- At the end: adversarial self-review — try to break your own answer
- State final confidence as a calibrated percentage with justification`;

const BROWSING_CAPABILITY_RE = /\b(?:can|do)\s+you\s+(?:browse|search|access|use)\b.*\b(?:web|internet|online)\b|\b(?:do\s+you\s+have|have\s+you\s+got)\b.*\b(?:web|internet|online|live|real[\s-]?time)\b.*\b(?:access|search|browsing)\b|\b(?:can|do)\s+you\s+answer\b.*\b(?:real[\s-]?time|current|latest|live)\b.*\b(?:question|questions|info(?:rmation)?)\b|\b(?:can|do)\s+you\s+get\b.*\b(?:latest|current|real[\s-]?time|live)\b.*\b(?:info(?:rmation)?|answers?|data)\b/i;

function getBrowsingCapabilityReply() {
  return `Yes — in this Claw runtime I can use live web tools.

- I can run live web search and use those results to answer current questions.
- For time-sensitive facts, I should search first and answer from the retrieved sources.
- If a live lookup fails because of a network issue, I should say the lookup failed rather than claim I am permanently offline.

I do not passively know real-time facts from memory alone; I answer current questions by using live search.`;
}

function sendBuiltinReply(res, reply, wantStream) {
  if (wantStream) {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.status(200);
    res.write(`data: ${JSON.stringify({ token: reply })}\n\n`);
    res.write(`data: ${JSON.stringify({ done: true, model: 'builtin', provider: 'builtin' })}\n\n`);
    res.end();
    return;
  }

  return res.status(200).json({
    reply,
    usage: null,
    model: 'builtin',
    provider: 'builtin',
    council: false,
  });
}

// Web search via DuckDuckGo HTML (no API key needed)
function ddgFetch(url, timeout = 10000) {
  return new Promise((resolve) => {
    const req = https.get(url, { headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/json',
      'Accept-Language': 'en-US,en;q=0.9'
    }}, (resp) => {
      if (resp.statusCode >= 300 && resp.statusCode < 400 && resp.headers.location) {
        return ddgFetch(resp.headers.location, timeout).then(resolve);
      }
      let data = '';
      resp.on('data', chunk => data += chunk);
      resp.on('end', () => resolve(data));
    });
    req.on('error', (e) => { console.error('[search] Fetch error:', e.message); resolve(''); });
    req.setTimeout(timeout, () => { console.error('[search] Timeout after', timeout, 'ms'); req.destroy(); resolve(''); });
  });
}

async function webSearch(query, numResults = 5) {
  // Method 1: DDG HTML search (GET)
  const htmlUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  console.log('[search] Trying DDG HTML:', htmlUrl.slice(0, 80));
  const html = await ddgFetch(htmlUrl);
  console.log('[search] HTML response length:', html.length);
  if (html.length > 500) {
    const results = [];
    const blocks = html.split(/class="result[\s"]/g);
    for (let i = 1; i < blocks.length && results.length < numResults; i++) {
      const block = blocks[i];
      const titleMatch = block.match(/class="result__a"[^>]*>([\s\S]*?)<\/a>/);
      const hrefMatch = block.match(/class="result__a"[^>]*href="([^"]+)"/);
      const snippetMatch = block.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/a>/);
      if (titleMatch) {
        const clean = s => s.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').trim();
        const title = clean(titleMatch[1]);
        const snippet = snippetMatch ? clean(snippetMatch[1]) : '';
        const url = hrefMatch ? decodeURIComponent(hrefMatch[1].replace(/^\/\/duckduckgo\.com\/l\/\?uddg=/, '').replace(/&rut=.*$/, '')) : '';
        if (title && title.length > 2) results.push({ title, snippet, url });
      }
    }
    if (results.length > 0) { console.log('[search] HTML got', results.length, 'results'); return results; }
  }

  // Method 2: DDG Lite (lighter page, less likely blocked)
  const liteUrl = `https://lite.duckduckgo.com/lite/?q=${encodeURIComponent(query)}`;
  console.log('[search] Trying DDG Lite');
  const lite = await ddgFetch(liteUrl);
  console.log('[search] Lite response length:', lite.length);
  if (lite.length > 200) {
    const results = [];
    const rows = lite.split(/<tr>/g);
    for (const row of rows) {
      if (results.length >= numResults) break;
      const linkMatch = row.match(/<a[^>]+href="([^"]+)"[^>]*class="result-link"[^>]*>([\s\S]*?)<\/a>/);
      if (!linkMatch) continue;
      const snippetMatch = row.match(/<td[^>]*class="result-snippet"[^>]*>([\s\S]*?)<\/td>/);
      const clean = s => s.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').trim();
      const title = clean(linkMatch[2]);
      const url = linkMatch[1];
      const snippet = snippetMatch ? clean(snippetMatch[1]) : '';
      if (title.length > 2) results.push({ title, snippet, url });
    }
    if (results.length > 0) { console.log('[search] Lite got', results.length, 'results'); return results; }
  }

  // Method 3: DDG Instant Answer API (structured JSON, always works)
  const apiUrl = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
  console.log('[search] Trying DDG API');
  const json = await ddgFetch(apiUrl);
  try {
    const d = JSON.parse(json);
    const results = [];
    if (d.Abstract) results.push({ title: d.Heading || query, snippet: d.Abstract, url: d.AbstractURL || '' });
    if (d.RelatedTopics) {
      for (const t of d.RelatedTopics) {
        if (results.length >= numResults) break;
        if (t.Text) results.push({ title: t.Text.slice(0, 80), snippet: t.Text, url: t.FirstURL || '' });
      }
    }
    if (results.length > 0) { console.log('[search] API got', results.length, 'results'); return results; }
  } catch (e) { console.error('[search] API parse error:', e.message); }

  console.error('[search] All methods failed for:', query.slice(0, 60));
  return [];
}

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
      version: '2.2.0',
      timestamp: new Date().toISOString(),
      keys_configured: {
        nvidia: !!NVIDIA_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
        cometapi: !!COMETAPI_KEY,
        openai: !!OPENAI_API_KEY,
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

  // GET /api/test/model - Test a specific model by name
  if (req.url.startsWith('/api/test/model') && req.method === 'GET') {
    return handleTestModel(req, res);
  }

  // GET /api/test/provider - Test all models for a provider
  if (req.url.startsWith('/api/test/provider') && req.method === 'GET') {
    return handleTestProvider(req, res);
  }

  // GET /api/test/all - Test all models across all providers
  if (req.url.startsWith('/api/test/all') && req.method === 'GET') {
    return handleTestAll(req, res);
  }

  // POST /api/council - Explicit council endpoint
  if (req.url.startsWith('/api/council') && req.method === 'POST') {
    return handleCouncil(req, res);
  }

  // POST /api/lead-events - Capture lead attribution events
  if (req.url.startsWith('/api/lead-events') && req.method === 'POST') {
    return handleLeadEvents(req, res);
  }

  // POST /api/leads - Capture leads from popup form submissions
  if (req.url.startsWith('/api/leads') && req.method === 'POST') {
    return handleLeadEvents(req, res);
  }

  // GET /api/models - List available models
  if (req.url.startsWith('/api/models') && req.method === 'GET') {
    return res.status(200).json({
      models: COUNCIL_MODELS,
      enabled: COUNCIL_ENABLED,
      mode: getProviderMode(),
      detail: getCouncilDetail(),
      api_key_set: !!NVIDIA_API_KEY,
      alibaba_key_set: !!DASHSCOPE_API_KEY,
      cometapi_key_set: !!COMETAPI_KEY,
      openai_key_set: !!OPENAI_API_KEY,
      providers: getConfiguredProviders(),
      nvidia_models: ACTIVE_NVIDIA_MODELS.length,
      alibaba_models: ACTIVE_ALIBABA_MODELS.length,
      cometapi_models: ACTIVE_COMETAPI_MODELS.length,
      openai_models: ACTIVE_OPENAI_MODELS.length,
      model_count: COUNCIL_MODELS.length
    });
  }

  // GET /api/status - Real system status
  if (req.url.startsWith('/api/status') && req.method === 'GET') {
    const configuredProviders = getConfiguredProviders();
    return res.status(200).json({
      status: 'operational',
      version: '2.2.0',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      models: COUNCIL_MODELS.length,
      council_detail: getCouncilDetail(),
      providers: configuredProviders.length,
      provider_names: configuredProviders,
      skills: 18,
      keys_configured: {
        nvidia: !!NVIDIA_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
        cometapi: !!COMETAPI_KEY,
        openai: !!OPENAI_API_KEY,
      },
      endpoints: {
        chat: '/api/chat',
        models: '/api/models',
        health: '/api/health',
        docs: '/api/docs',
        status: '/api/status',
        tools: '/api/tools',
        skills: '/api/skills',
        config: '/api/config',
        test_model: '/api/test/model?model={model_id}',
        test_provider: '/api/test/provider?provider={nvidia|alibaba|cometapi}',
        test_all: '/api/test/all'
      }
    });
  }

  // GET /api/tools - Real tool listing
  if (req.url.startsWith('/api/tools') && req.method === 'GET') {
    return res.status(200).json({
      total: 26,
      categories: {
        file: ['read_file', 'write_file', 'list_directory', 'find_files'],
        shell: ['run_command'],
        search: ['grep_search'],
        edit: ['replace_in_file', 'multi_edit_file', 'insert_at_line', 'diff_files'],
        web: ['web_fetch', 'web_search'],
        agent: ['run_subagent', 'plan_and_execute'],
        task: ['task_create', 'task_update', 'task_list', 'task_get'],
        notebook: ['notebook_run'],
        context: ['get_workspace_context', 'git_diff', 'git_log'],
        utility: ['sleep', 'config_get', 'config_set', 'powershell']
      }
    });
  }

  // GET /api/skills - Real skills listing
  if (req.url.startsWith('/api/skills') && req.method === 'GET') {
    return res.status(200).json({
      total: 18,
      skills: [
        {id:'code',name:'Code',description:'Generate, edit & debug code'},
        {id:'analyze',name:'Analyze',description:'Research & data analysis'},
        {id:'write',name:'Write',description:'Essays, emails, reports'},
        {id:'summarize',name:'Summarize',description:'Condense docs & articles'},
        {id:'translate',name:'Translate',description:'Any language pair'},
        {id:'math',name:'Math',description:'Calculations & reasoning'},
        {id:'reason',name:'Reason',description:'Logic & problem solving'},
        {id:'brainstorm',name:'Brainstorm',description:'Ideas & creative thinking'},
        {id:'explain',name:'Explain',description:'Simplify complex topics'},
        {id:'extract',name:'Extract',description:'Structure data from text'},
        {id:'vision',name:'Vision',description:'Describe images & diagrams'},
        {id:'debug',name:'Debug',description:'Find & fix bugs'},
        {id:'refactor',name:'Refactor',description:'Improve code quality'},
        {id:'review',name:'Review',description:'Code review & feedback'},
        {id:'test',name:'Test',description:'Write tests & QA'},
        {id:'docs',name:'Docs',description:'Generate documentation'},
        {id:'design',name:'Design',description:'System architecture'},
        {id:'search',name:'Search',description:'Web research & lookup'}
      ]
    });
  }

  // GET /api/config - Real config
  if (req.url.startsWith('/api/config') && req.method === 'GET') {
    return res.status(200).json({
      version: '2.2.0',
      models: COUNCIL_MODELS.length,
      council_detail: getCouncilDetail(),
      providers: getConfiguredProviders(),
      skills: 18,
      tools: 26,
      keys: {
        nvidia: !!NVIDIA_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
        cometapi: !!COMETAPI_KEY,
        openai: !!OPENAI_API_KEY,
      },
      limits: {
        max_message_length: 50000,
        max_body_size: '200KB',
        max_tokens: '4096-8192 (adaptive)',
        temperature: '0.2-0.7 (adaptive)'
      }
    });
  }

  // Serve the site UI or the LeadHub admin view
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  try {
    const requestedPath = (req.url || '').split('?')[0];
    const filePath = requestedPath.startsWith('/dashboard/leadhub') ? ADMIN_HTML_PATH : HTML_PATH;
    const html = fs.readFileSync(filePath, 'utf-8');
    return res.status(200).end(html);
  } catch (err) {
    // Fallback if target html not found
    res.status(200).end('<h1>Claw AI - Coming Soon</h1>');
  }
};

async function handleChat(req, res) {
  let body = '';
  let bodySize = 0;
  const MAX_BODY_SIZE = 200 * 1024;
  req.on('data', chunk => {
    bodySize += chunk.length;
    if (bodySize > MAX_BODY_SIZE) {
      req.destroy();
      return res.status(413).json({ error: 'Request body too large (max 200KB)' });
    }
    body += chunk;
  });
  req.on('end', async () => {
    try {
      const { message, model, history, use_council, stream: wantStream } = JSON.parse(body);

      if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: 'message required (string)' });
      }
      if (message.length > 50000) {
        return res.status(400).json({ error: 'message too long (max 50000 chars)' });
      }
      if (BROWSING_CAPABILITY_RE.test(message)) {
        return sendBuiltinReply(res, getBrowsingCapabilityReply(), wantStream);
      }
      if (use_council && NVIDIA_API_KEY) {
        return handleCouncilRequest(res, message);
      }

      // Build messages array with conversation history
      const messages = [{ role: 'system', content: SYSTEM_PROMPT }];
      if (Array.isArray(history)) {
        for (const h of history.slice(-20)) {
          if (h.role === 'u') messages.push({ role: 'user', content: h.content });
          else if (h.role === 'a') messages.push({ role: 'assistant', content: h.content });
        }
      }
      messages.push({ role: 'user', content: message });

      // Detect intent for smart model selection
      const lc = message.toLowerCase();
      const needsReasoning = /\b(math|reason|logic|proof|prove|calculate|solve|pattern|sequence|theorem|equation|missing.?number|find.?the|predict|next.?\d|part \d|step.by.step|edge.case|compare|contrast|pros.?cons|trade.?off|analysis|analyze|evaluate|assess|debate|argument|decision|which is better|explain why|how does|what causes|strategy|plan|design a system|architecture|troubleshoot|diagnose|debug this|what.?if|thought experiment|verify|disprove|contradiction|ambiguous|trap|trick)|\b\d+[\s,]+\d+[\s,]+\d+/i.test(message);
      const needsCoding = /\b(code|function|program|script|debug|refactor|implement|algorithm|class|api|write a |build a |def |const |import |return |for loop|while loop|array|list|dict|regex|database|query|schema|endpoint|server|client|component|module|package|library|framework|test case|unit test)|\b(python|javascript|java|rust|go|typescript|c\+\+|html|css|sql|react|vue|node|express|django|flask|fastapi)\b/i.test(message);
      const isHeavy = message.length > 500 || /\b(part \d|step \d|section|phase|first.*then|complex|comprehensive|detailed|thorough|exhaustive|complete guide|full|in-depth|everything about)\b/i.test(lc);
      const isUltraThink = /\b(ultrathink|ultra.think|deep.reason|boss.test|final.boss|maximum.rigor|prove.it|self.audit|adversarial|multi.?part|chain.of.thought)\b/i.test(message) || (needsReasoning && needsCoding) || (needsReasoning && isHeavy);
      const isResume = /\b(continue|resume|pick up|where.you.left|carry on|keep going|go on)\b/i.test(lc) && Array.isArray(history) && history.length > 0;
      const isSimple = !needsReasoning && !needsCoding && !isHeavy && !isUltraThink && !isResume && message.length < 120 && !/\b(explain|how does|why does|what causes|compare|analyze|write a|build a|create|implement|design)\b/i.test(lc);
      const needsSearch = /\b(search|research|look up|find out|google|browse|news|latest|current events?|today'?s?|recent|trending|what happened|update|weather|stock price|score|who won|release date|when did|when will|is it true|fact.?check|how much does|where (is|are|can)|what is the price|real.?time|right now|as of|launched|announced|released|introduced|unveiled|reported|confirmed|rumor|did .+ (launch|release|announce|happen))\b/i.test(lc) || /\b(202[4-9])\b/.test(message);

      // Web search if needed (DuckDuckGo, no API key)
      let searchResults = [];
      if (needsSearch) {
        console.log('[search] Triggered for:', message.slice(0, 80));
        searchResults = await webSearch(message);
        console.log('[search] Got', searchResults.length, 'results');
      }

      // Inject current server time so the AI can answer time/date questions
      const now = new Date();
      const timeStr = now.toLocaleString('en-US', { timeZone: 'UTC', dateStyle: 'full', timeStyle: 'long' });
      const timeBlock = `\n\nCurrent date and time (UTC): ${timeStr}`;

      // Simple: use lightweight prompt for casual questions (but NOT if we have search results)
      if (isSimple && searchResults.length === 0) {
        messages[0].content = SIMPLE_PROMPT + timeBlock;
      } else {
        messages[0].content += timeBlock;
      }
      // If search results found, add instruction to system prompt
      if (searchResults.length > 0) {
        messages[0].content += '\n\nIMPORTANT: The user\'s message includes [WEB SEARCH RESULTS]. You MUST base your answer on those results. Do NOT make up information. Cite the sources.';
      } else if (needsSearch) {
        // Search was triggered but returned nothing — tell the AI
        messages[0].content += '\n\nNOTE: A web search was attempted for this query but returned no results (network issue). Answer using your existing knowledge, but tell the user that live search was unavailable and recommend they check current sources for the latest info.';
      }
      // Ultrathink: boost system prompt for maximum rigor
      if (isUltraThink) {
        messages[0].content = SYSTEM_PROMPT + ULTRATHINK_ADDENDUM;
      }

      // Inject search results into user message
      if (searchResults.length > 0) {
        let searchContext = '\n\n[WEB SEARCH RESULTS]\n';
        searchResults.forEach((r, i) => {
          searchContext += `${i + 1}. ${r.title}\n   ${r.snippet}\n   Source: ${r.url}\n\n`;
        });
        searchContext += '[Use these search results to answer the user\'s question accurately. Cite sources when relevant. If the results don\'t fully answer the question, say what you found and what\'s unclear.]\n';
        messages[messages.length - 1].content = message + searchContext;
      }

      // Resume: inject last AI response context so model can continue seamlessly
      if (isResume) {
        const lastAI = [...(history || [])].reverse().find(h => h.role === 'a');
        if (lastAI && lastAI.content) {
          const tail = lastAI.content.slice(-1500);
          // Replace the plain user message with one that includes resumption context
          messages[messages.length - 1].content = message + `\n\n[RESUME CONTEXT — your previous response ended with:]\n${tail}\n[Continue exactly from where you left off. Do not repeat completed work.]`;
        }
      }

      const defaultModelChain = getDefaultModelChain({ needsReasoning, needsCoding, isHeavy, isUltraThink });
      let modelChain = defaultModelChain;
      if (model) {
        const provider = getProviderForModel(model);
        if (provider !== 'unknown') {
          modelChain = dedupeModelChain([{ model, provider }, ...defaultModelChain]);
        }
      }

      const temp = (needsReasoning || isUltraThink) ? 0.2 : (needsCoding ? 0.3 : (isSimple ? 0.7 : 0.7));
      const maxTok = isUltraThink ? 16384 : (needsReasoning || needsCoding || isHeavy) ? 8192 : (isSimple ? 1024 : 4096);

      // ---- SSE STREAMING MODE ----
      if (wantStream) {
        console.log('[stream] Entering SSE mode, wantStream=', wantStream);
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.status(200);

        // Notify client if web search was performed
        if (searchResults.length > 0) {
          res.write(`data: ${JSON.stringify({ search: true, count: searchResults.length })}\n\n`);
        }

        let lastError = null;
        for (const { model: m, provider: p } of modelChain) {
          const config = getProviderConfig(p);
          if (!config || !config.key) continue;

          const apiBase = config.base;
          const hdrs = getHeadersForProvider(p, config.key);

          const payload = JSON.stringify({
            model: m, messages, temperature: temp, max_tokens: maxTok, stream: true,
          });

          try {
            const ok = await callAPIStreaming(apiBase, payload, hdrs, res, m, p);
            if (ok) return; // Stream completed successfully
            lastError = 'No tokens from ' + m;
            console.log('[stream] Model failed (0 tokens):', m, 'provider:', p);
          } catch (e) {
            lastError = e.message;
            console.log('[stream] Model error:', m, 'provider:', p, e.message);
            continue;
          }
        }
        // All models failed in streaming mode - send graceful fallback
        const fallbackMsg = "I'm experiencing high demand right now. Please try again in a moment \u2014 I'll be right back.";
        res.write(`data: ${JSON.stringify({ choices: [{ delta: { content: fallbackMsg } }] })}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
        return;
      }

      // ---- NON-STREAMING FALLBACK (for API consumers) ----
      let lastError = null;
      for (const { model: m, provider: p } of modelChain) {
        try {
          const config = getProviderConfig(p);
          if (!config || !config.key) continue;
          const apiBase = config.base;
          const hdrs = getHeadersForProvider(p, config.key);
          const payload = JSON.stringify({
            model: m, messages, temperature: temp, max_tokens: maxTok,
          });
          const result = await callAPI(apiBase, payload, hdrs);
          if (result.error) { lastError = result.error.message || 'API error'; continue; }
          const reply = result.choices?.[0]?.message?.content;
          if (!reply || !reply.trim()) { lastError = 'Empty response from ' + m; continue; }
          return res.status(200).json({ reply: reply.trim(), usage: result.usage || {}, model: m, provider: p, council: false });
        } catch (e) { lastError = e.message; continue; }
      }
      // All models failed - return graceful fallback instead of 500
      const fallbackReply = "I'm experiencing high demand across all providers. Please try again in a moment \u2014 I'll be right back.";
      return res.status(200).json({ reply: fallbackReply, model: 'fallback', provider: 'system', council: false, fallback: true });
    } catch (e) {
      console.error('Chat error:', e.message);
      res.status(500).json({ error: e.message });
    }
  });
}

// SSE streaming: pipe upstream API SSE chunks directly to the client
// Returns true if tokens were sent (success), false if failed before any tokens
function callAPIStreaming(apiBase, payload, headers, clientRes, modelName, providerName) {
  const url = new URL(`${apiBase}/chat/completions`);
  return new Promise((resolve, reject) => {
    let tokensSent = 0;
    let fullContent = '';

    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname,
      method: 'POST',
      headers: { ...headers, 'Content-Length': Buffer.byteLength(payload) },
      timeout: 18000, // 18s per model — 3 models × 18s = 54s (within 60s Vercel limit)
    };

    const request = https.request(options, (apiRes) => {
      if (apiRes.statusCode !== 200) {
        let errData = '';
        apiRes.on('data', chunk => errData += chunk);
        apiRes.on('end', () => {
          console.log('[stream] Non-200 from', modelName, ':', apiRes.statusCode, errData.substring(0, 200));
          if (tokensSent === 0) {
            resolve(false); // No tokens sent, caller can try next model
          } else {
            clientRes.write(`data: ${JSON.stringify({ error: 'API error mid-stream' })}\n\n`);
            clientRes.write(`data: ${JSON.stringify({ done: true, model: modelName, provider: providerName, partial: true })}\n\n`);
            clientRes.end();
            resolve(true);
          }
        });
        return;
      }

      // Send model info as first event
      clientRes.write(`data: ${JSON.stringify({ model: modelName, provider: providerName, start: true })}\n\n`);

      let buffer = '';
      apiRes.on('data', (chunk) => {
        buffer += chunk.toString();
        // Process complete SSE frames (separated by \n\n)
        const frames = buffer.split('\n\n');
        buffer = frames.pop(); // Keep incomplete frame in buffer

        for (const frame of frames) {
          for (const line of frame.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              clientRes.write(`data: ${JSON.stringify({ done: true, model: modelName, provider: providerName })}\n\n`);
              clientRes.end();
              resolve(true);
              return;
            }
            try {
              const parsed = JSON.parse(data);
              const delta = parsed.choices?.[0]?.delta?.content;
              if (delta) {
                tokensSent++;
                fullContent += delta;
                clientRes.write(`data: ${JSON.stringify({ token: delta })}\n\n`);
              }
            } catch (e) { /* skip unparseable chunks */ }
          }
        }
      });

      apiRes.on('end', () => {
        // Process any remaining buffer
        if (buffer.trim()) {
          for (const line of buffer.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              const delta = parsed.choices?.[0]?.delta?.content;
              if (delta) { tokensSent++; fullContent += delta; clientRes.write(`data: ${JSON.stringify({ token: delta })}\n\n`); }
            } catch (e) { /* skip */ }
          }
        }
        if (tokensSent > 0) {
          if (!clientRes.writableEnded) {
            clientRes.write(`data: ${JSON.stringify({ done: true, model: modelName, provider: providerName })}\n\n`);
            clientRes.end();
          }
          resolve(true);
        } else {
          resolve(false); // No tokens received — try next model
        }
      });
    });

    request.on('error', (error) => {
      if (tokensSent > 0) {
        if (!clientRes.writableEnded) {
          clientRes.write(`data: ${JSON.stringify({ error: error.message, partial: true, done: true })}\n\n`);
          clientRes.end();
        }
        resolve(true);
      } else {
        resolve(false);
      }
    });

    request.on('timeout', () => {
      request.destroy();
      if (tokensSent > 0) {
        if (!clientRes.writableEnded) {
          clientRes.write(`data: ${JSON.stringify({ error: 'timeout', partial: true, done: true })}\n\n`);
          clientRes.end();
        }
        resolve(true);
      } else {
        resolve(false);
      }
    });

    // Detect client disconnect
    clientRes.on('close', () => { request.destroy(); });

    request.write(payload);
    request.end();
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

      if (!NVIDIA_API_KEY && !DASHSCOPE_API_KEY && !COMETAPI_KEY) {
        return res.status(500).json({
          error: 'No API keys configured. Set at least one of NVIDIA_API_KEY, DASHSCOPE_API_KEY, or COMETAPI_KEY.',
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
  // Query all council models in parallel (NVIDIA NIM + Alibaba + CometAPI)
  const promises = COUNCIL_MODELS.map(async (model) => {
    try {
      const provider = getProviderForModel(model) || 'nvidia';
      const config = getProviderConfig(provider);
      if (!config || !config.key) {
        return { model, content: '', error: 'No API key for provider: ' + provider, usage: {}, provider };
      }

      const payload = JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: message }
        ],
        temperature: 0.7,
        max_tokens: 8192,
      });
      const headers = getHeadersForProvider(provider, config.key);
      const result = await callAPI(config.base, payload, headers);
      const content = result.choices?.[0]?.message?.content || '';
      return { model, content, error: null, usage: result.usage || {}, provider };
    } catch (error) {
      const provider = getProviderForModel(model) || 'nvidia';
      return { model, content: '', error: error.message, usage: {}, provider };
    }
  });

  const responses = await Promise.all(promises);
  
  // Filter successful responses
  const successful = responses.filter(r => !r.error);
  const failed = responses.filter(r => r.error);

  if (successful.length === 0) {
    // All council models failed - return graceful fallback instead of 500
    const fallbackReply = "The council is experiencing high demand across all providers. Please try again in a moment.";
    return res.status(200).json({
      reply: fallbackReply,
      council: true,
      models_queried: COUNCIL_MODELS.length,
      successful_responses: 0,
      failed_responses: failed.length,
      consensus_percentage: '0',
      total_tokens: 0,
      fallback: true,
      all_responses: failed.map(f => ({ model: f.model, content: '', error: f.error }))
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

// ─── Test Endpoint Handlers ───────────────────────────────────────────────────

async function handleTestModel(req, res) {
  const urlObj = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const model = urlObj.searchParams.get('model');

  if (!model) {
    return res.status(400).json({ error: 'Missing required query parameter: model', usage: '/api/test/model?model=qwen/qwen3.5-397b-a17b' });
  }

  const provider = getProviderForModel(model);
  if (!provider) {
    return res.status(404).json({ error: `Model "${model}" not found in any provider`, available_models: COUNCIL_MODELS });
  }

  const config = getProviderConfig(provider);
  if (!config.key) {
    return res.status(503).json({ error: `API key not configured for provider: ${provider}`, model, provider });
  }

  const payload = JSON.stringify(getTestPayload(provider, model));
  const headers = getHeadersForProvider(provider, config.key);
  const startTime = Date.now();

  const result = await callAPI(config.base, payload, headers, 10000);
  const elapsed = Date.now() - startTime;

  if (result.error) {
    return res.status(200).json({
      model, provider, status: 'down',
      response_time_ms: elapsed,
      error: result.error,
      tokens: null,
    });
  }

  return res.status(200).json({
    model, provider, status: 'up',
    response_time_ms: elapsed,
    tokens: result.usage || null,
    finish_reason: result.choices?.[0]?.finish_reason || null,
  });
}

async function handleTestProvider(req, res) {
  const urlObj = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const provider = (urlObj.searchParams.get('provider') || '').toLowerCase();

  const validProviders = ['nvidia', 'alibaba', 'cometapi', 'openai'];
  if (!provider || !validProviders.includes(provider)) {
    return res.status(400).json({ error: 'Missing or invalid provider', valid_providers: validProviders, usage: '/api/test/provider?provider=nvidia' });
  }

  const config = getProviderConfig(provider);
  if (!config.key) {
    return res.status(503).json({ error: `API key not configured for provider: ${provider}`, provider });
  }

  const models = provider === 'nvidia' ? ACTIVE_NVIDIA_MODELS
    : provider === 'alibaba' ? ACTIVE_ALIBABA_MODELS
    : provider === 'cometapi' ? ACTIVE_COMETAPI_MODELS
    : ACTIVE_OPENAI_MODELS;

  const results = await Promise.allSettled(models.map(async (model) => {
    const payload = JSON.stringify(getTestPayload(provider, model));
    const headers = getHeadersForProvider(provider, config.key);
    const startTime = Date.now();
    try {
      const result = await callAPI(config.base, payload, headers, 10000);
      const elapsed = Date.now() - startTime;
      if (result.error) {
        return { model, status: 'down', response_time_ms: elapsed, error: result.error };
      }
      return { model, status: 'up', response_time_ms: elapsed, tokens: result.usage || null };
    } catch (err) {
      return { model, status: 'down', response_time_ms: Date.now() - startTime, error: { message: err.message } };
    }
  }));

  const modelResults = results.map(r => r.status === 'fulfilled' ? r.value : { model: 'unknown', status: 'error', error: { message: r.reason?.message } });
  const upCount = modelResults.filter(r => r.status === 'up').length;

  return res.status(200).json({
    provider,
    total_models: models.length,
    models_up: upCount,
    models_down: models.length - upCount,
    results: modelResults,
  });
}

async function handleTestAll(req, res) {
  const providers = [];
  if (NVIDIA_API_KEY) providers.push('nvidia');
  if (DASHSCOPE_API_KEY) providers.push('alibaba');
  if (COMETAPI_KEY) providers.push('cometapi');
  if (OPENAI_API_KEY) providers.push('openai');

  if (providers.length === 0) {
    return res.status(503).json({ error: 'No API keys configured for any provider' });
  }

  const allResults = {};
  let totalUp = 0;
  let totalDown = 0;
  let totalModels = 0;

  await Promise.all(providers.map(async (provider) => {
    const config = getProviderConfig(provider);
    const models = provider === 'nvidia' ? ACTIVE_NVIDIA_MODELS
      : provider === 'alibaba' ? ACTIVE_ALIBABA_MODELS
      : provider === 'cometapi' ? ACTIVE_COMETAPI_MODELS
      : ACTIVE_OPENAI_MODELS;

    const results = await Promise.allSettled(models.map(async (model) => {
      const payload = JSON.stringify(getTestPayload(provider, model));
      const headers = getHeadersForProvider(provider, config.key);
      const startTime = Date.now();
      try {
        const result = await callAPI(config.base, payload, headers, 10000);
        const elapsed = Date.now() - startTime;
        if (result.error) {
          return { model, status: 'down', response_time_ms: elapsed, error: result.error };
        }
        return { model, status: 'up', response_time_ms: elapsed, tokens: result.usage || null };
      } catch (err) {
        return { model, status: 'down', response_time_ms: Date.now() - startTime, error: { message: err.message } };
      }
    }));

    const modelResults = results.map(r => r.status === 'fulfilled' ? r.value : { model: 'unknown', status: 'error', error: { message: r.reason?.message } });
    const upCount = modelResults.filter(r => r.status === 'up').length;

    allResults[provider] = {
      total_models: models.length,
      models_up: upCount,
      models_down: models.length - upCount,
      results: modelResults,
    };

    totalModels += models.length;
    totalUp += upCount;
    totalDown += models.length - upCount;
  }));

  return res.status(200).json({
    timestamp: new Date().toISOString(),
    total_providers: providers.length,
    total_models: totalModels,
    total_up: totalUp,
    total_down: totalDown,
    providers: allResults,
  });
}

function callAPI(apiBase, payload, headers, timeout = 10000) {
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
      timeout,
    };

    const request = https.request(options, (apiRes) => {
      let data = '';
      apiRes.on('data', chunk => data += chunk);
      apiRes.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (apiRes.statusCode !== 200) {
            const error = result.error || {};
            resolve({ 
              error: { 
                message: error.message || `HTTP ${apiRes.statusCode}`,
                code: error.code,
                param: error.param,
                type: error.type,
                status: apiRes.statusCode
              } 
            });
          } else {
            resolve(result);
          }
        } catch (e) {
          resolve({ error: { message: 'JSON parse error: ' + e.message } });
        }
      });
    });

    request.on('error', error => resolve({ error: { message: `Network error: ${error.message}` } }));
    request.on('timeout', () => { 
      request.destroy(); 
      resolve({ error: { message: 'Timeout after ' + (timeout/1000) + 's' } });
    });
    request.write(payload);
    request.end();
  });
}

// callNvidiaAPI removed (dead code) - all providers now use generic callAPI()

async function handleLeadEvents(req, res) {
  let body = '';
  let bodySize = 0;
  const MAX_BODY_SIZE = 64 * 1024;

  req.on('data', chunk => {
    bodySize += chunk.length;
    if (bodySize > MAX_BODY_SIZE) {
      req.destroy();
      return res.status(413).json({ error: 'Lead event too large (max 64KB)' });
    }
    body += chunk;
  });

  req.on('end', () => {
    try {
      const event = JSON.parse(body || '{}');
      const payload = event.payload || {};
      const eventType = event.event_type || 'unknown';
      const leadScore = Number(payload.lead_score || 0);

      const trackingSummary = {
        eventType,
        ts: event.ts || new Date().toISOString(),
        path: event.page?.path || '',
        source: payload.source || '',
        medium: payload.medium || '',
        campaign: payload.campaign || '',
        campaign_id: payload.campaign_id || '',
        keyword: payload.keyword || payload.term || '',
        search_term: payload.search_term || '',
        click_ids: {
          gclid: payload.gclid || '',
          fbclid: payload.fbclid || '',
          msclkid: payload.msclkid || '',
          ttclid: payload.ttclid || '',
          twclid: payload.twclid || '',
          li_fat_id: payload.li_fat_id || '',
          gbraid: payload.gbraid || '',
          wbraid: payload.wbraid || '',
          yclid: payload.yclid || '',
        },
        lead_score: Number.isFinite(leadScore) ? leadScore : 0,
      };

      console.log('[lead-event]', JSON.stringify(trackingSummary));

      // Persist lead to Supabase (fire-and-forget, don't block response)
      if (SUPABASE_URL && SUPABASE_SERVICE_KEY) {
        const leadRow = {
          email: payload.email || event.email || '',
          name: payload.name || event.name || '',
          phone: payload.phone || event.phone || '',
          event_type: eventType,
          page_path: trackingSummary.path,
          source: trackingSummary.source,
          medium: trackingSummary.medium,
          campaign: trackingSummary.campaign,
          campaign_id: trackingSummary.campaign_id,
          keyword: trackingSummary.keyword,
          search_term: trackingSummary.search_term,
          lead_score: trackingSummary.lead_score,
          click_ids: trackingSummary.click_ids,
          payload: payload,
          ip_address: (req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim(),
          user_agent: (req.headers['user-agent'] || '').substring(0, 512),
        };
        const postData = JSON.stringify(leadRow);
        const supaUrl = new URL(`${SUPABASE_URL}/rest/v1/leads`);
        const opts = {
          hostname: supaUrl.hostname,
          port: 443,
          path: supaUrl.pathname,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
            'Prefer': 'return=minimal',
            'Content-Length': Buffer.byteLength(postData),
          },
        };
        const insertReq = https.request(opts, (insertRes) => {
          let d = '';
          insertRes.on('data', c => d += c);
          insertRes.on('end', () => {
            if (insertRes.statusCode >= 400) console.error('[lead-insert-error]', insertRes.statusCode, d);
          });
        });
        insertReq.on('error', e => console.error('[lead-insert-error]', e.message));
        insertReq.write(postData);
        insertReq.end();
      }

      return res.status(202).json({ ok: true, received: true });
    } catch (e) {
      return res.status(400).json({ error: 'Invalid lead event payload' });
    }
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

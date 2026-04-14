const https = require('https');
const fs = require('fs');
const path = require('path');

// Read the updated index.html from project root
const HTML_PATH = path.join(__dirname, '..', 'index.html');
const ADMIN_HTML_PATH = path.join(__dirname, '..', 'public', 'admin.html');
const OPENAPI_PATH = path.join(__dirname, 'openapi.json');

// Allowed CORS origins (add your production domain)
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim());

// OpenRouter configuration - API keys from environment variables only
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_API_BASE = 'https://openrouter.ai/api/v1';

// Alibaba Cloud (DashScope) configuration
const DASHSCOPE_API_KEY = process.env.DASHSCOPE_API_KEY || '';
const DASHSCOPE_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1';

// Supabase configuration (for lead storage)
const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || '';

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

const ACTIVE_OPENROUTER_MODELS = OPENROUTER_API_KEY ? OPENROUTER_MODELS : [];
const ACTIVE_ALIBABA_MODELS = DASHSCOPE_API_KEY ? ALIBABA_MODELS : [];
const COUNCIL_MODELS = [...ACTIVE_OPENROUTER_MODELS, ...ACTIVE_ALIBABA_MODELS];

function getProviderMode() {
  if (OPENROUTER_API_KEY && DASHSCOPE_API_KEY) return 'multi';
  if (OPENROUTER_API_KEY) return 'openrouter';
  if (process.env.DEEPSEEK_API_KEY) return 'deepseek';
  if (DASHSCOPE_API_KEY) return 'dashscope';
  return 'ollama';
}

// Council mode is enabled when OpenRouter is available; Alibaba is optional and joins when configured
const COUNCIL_ENABLED = !!OPENROUTER_API_KEY && COUNCIL_MODELS.length > 0;

// Model chains — ALL OpenRouter (proven SSE streaming support)
// 3 models per chain, 18s timeout each = 54s worst case (within 60s Vercel limit)
const FAST_MODELS = [
  { model: 'deepseek/deepseek-v3', provider: 'openrouter' },
  { model: 'meta-llama/llama-3.3-70b-instruct', provider: 'openrouter' },
  { model: 'openai/gpt-4o-mini', provider: 'openrouter' },
];

const REASONING_MODELS = [
  { model: 'deepseek/deepseek-v3', provider: 'openrouter' },
  { model: 'meta-llama/llama-3.3-70b-instruct', provider: 'openrouter' },
  { model: 'qwen/qwen3-80b', provider: 'openrouter' },
];

const CODING_MODELS = [
  { model: 'deepseek/deepseek-v3', provider: 'openrouter' },
  { model: 'meta-llama/llama-3.3-70b-instruct', provider: 'openrouter' },
  { model: 'qwen/qwen-2.5-coder-32b-instruct', provider: 'openrouter' },
];

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
- Never truncate, abbreviate with "etc.", or leave work unfinished
- Match depth to complexity — simple questions get concise answers, hard problems get thorough treatment
- For multi-part problems: solve ALL parts, verify ALL parts
- If you run out of space, summarize what remains and offer to continue

## RESUMPTION PROTOCOL
If the user says "continue" or provides context from a previous response:
- Read their context carefully
- Pick up EXACTLY where the previous response left off
- Do not repeat already-completed work
- Signal: "Continuing from [last point]..."

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
      version: '2.1.0',
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
      mode: COUNCIL_ENABLED ? 'multi' : (OPENROUTER_API_KEY ? 'openrouter' : (process.env.DEEPSEEK_API_KEY ? 'deepseek' : 'ollama')),
      api_key_set: !!OPENROUTER_API_KEY,
      alibaba_key_set: !!DASHSCOPE_API_KEY,
      providers: ['OpenRouter', 'Alibaba Cloud (DashScope)'],
      openrouter_models: OPENROUTER_MODELS.length,
      alibaba_models: ALIBABA_MODELS.length,
      model_count: COUNCIL_MODELS.length
    });
  }

  // GET /api/status - Real system status
  if (req.url.startsWith('/api/status') && req.method === 'GET') {
    return res.status(200).json({
      status: 'operational',
      version: '2.0.0',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      models: COUNCIL_MODELS.length,
      providers: Number(!!OPENROUTER_API_KEY) + Number(!!DASHSCOPE_API_KEY),
      skills: 18,
      keys_configured: {
        openrouter: !!OPENROUTER_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
      },
      endpoints: {
        chat: '/api/chat',
        models: '/api/models',
        health: '/api/health',
        docs: '/api/docs',
        status: '/api/status',
        tools: '/api/tools',
        skills: '/api/skills',
        config: '/api/config'
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
      version: '2.0.0',
      models: COUNCIL_MODELS.length,
      providers: ['OpenRouter', 'Alibaba Cloud (DashScope)'],
      skills: 18,
      tools: 26,
      keys: {
        openrouter: !!OPENROUTER_API_KEY,
        dashscope: !!DASHSCOPE_API_KEY,
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
      if (use_council && OPENROUTER_API_KEY) {
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

      // Ultrathink: boost system prompt for maximum rigor
      if (isUltraThink) {
        messages[0].content = SYSTEM_PROMPT + ULTRATHINK_ADDENDUM;
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

      let modelChain;
      if (model) {
        const provider = ALIBABA_MODELS.includes(model) ? 'alibaba' : 'openrouter';
        modelChain = [{ model, provider }];
      } else if (needsReasoning || isHeavy || isUltraThink) {
        modelChain = REASONING_MODELS;
      } else if (needsCoding) {
        modelChain = CODING_MODELS;
      } else {
        modelChain = FAST_MODELS;
      }

      const temp = (needsReasoning || isUltraThink) ? 0.2 : (needsCoding ? 0.3 : 0.7);
      const maxTok = isUltraThink ? 16384 : (needsReasoning || needsCoding || isHeavy) ? 8192 : 4096;

      // ---- SSE STREAMING MODE ----
      if (wantStream) {
        console.log('[stream] Entering SSE mode, wantStream=', wantStream);
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.status(200);

        let lastError = null;
        for (const { model: m, provider: p } of modelChain) {
          const isAlibaba = p === 'alibaba';
          const apiKey = isAlibaba ? DASHSCOPE_API_KEY : OPENROUTER_API_KEY;
          if (!apiKey) continue;

          const apiBase = isAlibaba ? DASHSCOPE_API_BASE : OPENROUTER_API_BASE;
          const hdrs = isAlibaba ? {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
          } : {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'HTTP-Referer': 'https://github.com/claw-agent',
            'X-Title': 'Claw AI',
          };

          const payload = JSON.stringify({
            model: m, messages, temperature: temp, max_tokens: maxTok, stream: true,
          });

          try {
            const ok = await callAPIStreaming(apiBase, payload, hdrs, res, m, p);
            if (ok) return; // Stream completed successfully
            lastError = 'No tokens from ' + m;
            console.log('[stream] Model failed (0 tokens):', m);
          } catch (e) {
            lastError = e.message;
            console.log('[stream] Model error:', m, e.message);
            continue;
          }
        }
        // All models failed in streaming mode
        res.write(`data: ${JSON.stringify({ error: 'All models failed. ' + (lastError || '') })}\n\n`);
        res.end();
        return;
      }

      // ---- NON-STREAMING FALLBACK (for API consumers) ----
      let lastError = null;
      for (const { model: m, provider: p } of modelChain) {
        try {
          const isAlibaba = p === 'alibaba';
          const apiKey = isAlibaba ? DASHSCOPE_API_KEY : OPENROUTER_API_KEY;
          if (!apiKey) continue;
          const apiBase = isAlibaba ? DASHSCOPE_API_BASE : OPENROUTER_API_BASE;
          const hdrs = isAlibaba ? {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
          } : {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'HTTP-Referer': 'https://github.com/claw-agent',
            'X-Title': 'Claw AI',
          };
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
      return res.status(500).json({ error: 'All models failed. Last error: ' + (lastError || 'Unknown error'), tried: modelChain.map(m => m.model) });
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
        payload = JSON.stringify({
          model,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: message }
          ],
          temperature: 0.7,
          max_tokens: 8192,
        });
        apiBase = DASHSCOPE_API_BASE;
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${DASHSCOPE_API_KEY}`,
        };
      } else {
        payload = JSON.stringify({
          model,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: message }
          ],
          temperature: 0.7,
          max_tokens: 8192,
        });
        apiBase = OPENROUTER_API_BASE;
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://github.com/claw-agent',
          'X-Title': 'Claw AI',
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
      timeout: 30000,
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
        'X-Title': 'Claw AI',
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

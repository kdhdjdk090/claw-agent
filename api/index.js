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

// Smart model priority chain - fastest/most reliable first
const FAST_MODELS = [
  { model: 'deepseek/deepseek-v3', provider: 'openrouter' },
  { model: 'qwen/qwen3-80b', provider: 'openrouter' },
  { model: 'meta-llama/llama-3.3-70b-instruct', provider: 'openrouter' },
  { model: 'openai/gpt-4o-mini', provider: 'openrouter' },
];

const REASONING_MODELS = [
  { model: 'deepseek/deepseek-r1', provider: 'openrouter' },
  { model: 'qwen3-235b-a22b', provider: 'alibaba' },
  { model: 'qwen3.5-397b-a17b', provider: 'alibaba' },
];

const CODING_MODELS = [
  { model: 'qwen/qwen-2.5-coder-32b-instruct', provider: 'openrouter' },
  { model: 'qwen3-coder-480b-a35b-instruct', provider: 'alibaba' },
  { model: 'qwen3-coder-plus', provider: 'alibaba' },
];

// System prompt - universal structured reasoning methodology
const SYSTEM_PROMPT = `You are Claw AI, an elite AI assistant. You handle ANY task — simple or impossibly complex — with structured methodology and exhaustive depth.

## UNIVERSAL APPROACH
For EVERY question: (1) Understand fully before starting. (2) Break into parts. (3) Solve each thoroughly. (4) Verify. (5) Present clearly with markdown.

## METHODOLOGIES BY TASK TYPE

### MATH & PATTERNS
1. **Observe** — List values. Compute differences AND ratios between consecutive terms.
2. **Hypothesize** — State the rule explicitly.
3. **Verify** — Apply rule to ALL known terms.
4. **Solve** — Find unknowns using verified rule.
5. **Double-check** — Plug answers back, confirm consistency.

### CODE & PROGRAMMING
1. **Understand** — Restate requirements, inputs, outputs, edge cases.
2. **Design** — Outline algorithm in plain English first.
3. **Implement** — Clean, documented, production-ready code with types and error handling.
4. **Test** — Include test cases, example output, edge case handling.

### LOGIC & REASONING
1. **State knowns** — List every fact, constraint, and given.
2. **Derive** — Show each logical step explicitly.
3. **Eliminate** — Rule out impossibilities with proof.
4. **Conclude** — Final answer with confidence and justification.

### WRITING & CONTENT (essays, emails, reports, stories)
1. **Audience & purpose** — Who is this for? What tone?
2. **Structure** — Outline sections before writing.
3. **Draft** — Write complete, polished content. Not summaries — full text.
4. **Refine** — Ensure flow, clarity, grammar, and impact.

### RESEARCH & ANALYSIS
1. **Scope** — Define what exactly needs to be analyzed.
2. **Gather** — Pull all relevant facts, data, context.
3. **Analyze** — Compare, contrast, identify trends, cause-effect.
4. **Synthesize** — Draw actionable conclusions with evidence.

### COMPARISONS & DECISIONS
1. **Criteria** — Define comparison dimensions (cost, performance, ease, etc.).
2. **Evaluate** — Score each option on every criterion with evidence.
3. **Trade-offs** — State pros/cons for each honestly.
4. **Recommend** — Give a clear verdict with reasoning.

### CREATIVE & BRAINSTORMING
1. **Diverge** — Generate many ideas without filtering.
2. **Organize** — Group by theme or feasibility.
3. **Develop** — Flesh out the best ideas with details.
4. **Deliver** — Present with structure, examples, and next steps.

### DEBUGGING & TROUBLESHOOTING
1. **Reproduce** — Understand the exact error, input, expected vs actual.
2. **Hypothesize** — List possible causes ranked by likelihood.
3. **Test** — Check each hypothesis systematically.
4. **Fix** — Provide the corrected code/solution with explanation of what was wrong and why.

### DATA & TABLES
1. **Structure** — Organize data into clear markdown tables.
2. **Calculate** — Show all computations explicitly.
3. **Visualize** — Describe trends, outliers, patterns.
4. **Interpret** — What does the data mean? What actions follow?

### MULTI-STEP / COMPLEX TASKS
1. **Decompose** — Break into numbered sub-tasks.
2. **Sequence** — Determine correct order and dependencies.
3. **Execute** — Solve each sub-task fully with shown work.
4. **Integrate** — Combine results into a coherent final answer.

### EXPLANATIONS & TEACHING
1. **Core concept** — State the key idea in one sentence.
2. **Build up** — Explain from simple to complex, layering detail.
3. **Examples** — Give concrete, relatable examples at each level.
4. **Verify understanding** — Summarize and highlight common misconceptions.

## RULES
- ALWAYS show your work. Every calculation, every step, every decision.
- Use markdown: **bold** key answers, \`code blocks\`, headers, tables, lists.
- For sequences: compute BOTH ratios AND differences.
- For code: docstrings, type hints, error handling, test examples.
- For writing: deliver COMPLETE text, not outlines or summaries.
- Never give up. If ambiguous, state assumptions and solve under each.
- Break complex work into numbered parts and solve exhaustively.
- When asked what you are, say you are Claw AI.
- Give COMPLETE answers. Never truncate. Never say "and so on" or "etc." — finish everything.
- Match the depth to the question: simple questions get concise answers, complex ones get thorough treatment.`;

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

  // GET /api/models - List available models
  if (req.url.startsWith('/api/models') && req.method === 'GET') {
    return res.status(200).json({
      models: COUNCIL_MODELS,
      enabled: COUNCIL_ENABLED,
      mode: COUNCIL_ENABLED ? 'multi' : (process.env.DEEPSEEK_API_KEY ? 'deepseek' : 'ollama'),
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
      providers: 2,
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
  const MAX_BODY_SIZE = 200 * 1024; // 200KB limit (increased for history)
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
      const { message, model, history, use_council } = JSON.parse(body);

      if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: 'message required (string)' });
      }

      if (message.length > 50000) {
        return res.status(400).json({ error: 'message too long (max 50000 chars)' });
      }

      // Use council if explicitly requested
      if (use_council && OPENROUTER_API_KEY) {
        return handleCouncilRequest(res, message);
      }

      // Build messages array with conversation history
      const messages = [{ role: 'system', content: SYSTEM_PROMPT }];
      
      // Add conversation history (last 20 messages max)
      if (Array.isArray(history)) {
        const recent = history.slice(-20);
        for (const h of recent) {
          if (h.role === 'u') messages.push({ role: 'user', content: h.content });
          else if (h.role === 'a') messages.push({ role: 'assistant', content: h.content });
        }
      }
      
      messages.push({ role: 'user', content: message });

      // Detect intent for smart model selection
      const lc = message.toLowerCase();
      const needsReasoning = /\b(math|reason|logic|proof|prove|calculate|solve|pattern|sequence|theorem|equation|missing.?number|find.?the|predict|next.?\d|part \d|step.by.step|edge.case|compare|contrast|pros.?cons|trade.?off|analysis|analyze|evaluate|assess|debate|argument|decision|which is better|explain why|how does|what causes|strategy|plan|design a system|architecture|troubleshoot|diagnose|debug this|what.?if|thought experiment)|\b\d+[\s,]+\d+[\s,]+\d+/i.test(message);
      const needsCoding = /\b(code|function|program|script|debug|refactor|implement|algorithm|class|api|write a |build a |def |const |import |return |for loop|while loop|array|list|dict|regex|database|query|schema|endpoint|server|client|component|module|package|library|framework|test case|unit test)|\b(python|javascript|java|rust|go|typescript|c\+\+|html|css|sql|react|vue|node|express|django|flask|fastapi)\b/i.test(message);
      const isHeavy = message.length > 500 || /\b(part \d|step \d|section|phase|first.*then|complex|comprehensive|detailed|thorough|exhaustive|complete guide|full|in-depth|everything about)\b/i.test(lc);
      
      // Select model chain based on intent
      let modelChain;
      if (model) {
        // User specified a model
        const provider = ALIBABA_MODELS.includes(model) ? 'alibaba' : 'openrouter';
        modelChain = [{ model, provider }];
      } else if (needsCoding) {
        modelChain = [...CODING_MODELS, ...FAST_MODELS];
      } else if (needsReasoning || isHeavy) {
        modelChain = [...REASONING_MODELS, ...FAST_MODELS];
      } else {
        modelChain = [...FAST_MODELS, ...REASONING_MODELS.slice(0, 1)];
      }

      // Try models in order until one succeeds (fallback chain)
      let lastError = null;
      for (const { model: m, provider: p } of modelChain) {
        try {
          const isAlibaba = p === 'alibaba';
          const apiKey = isAlibaba ? DASHSCOPE_API_KEY : OPENROUTER_API_KEY;
          if (!apiKey) continue;
          
          const apiBase = isAlibaba ? DASHSCOPE_API_BASE : OPENROUTER_API_BASE;
          const headers = isAlibaba ? {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
          } : {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'HTTP-Referer': 'https://github.com/claw-agent',
            'X-Title': 'Claw AI',
          };

          const payload = JSON.stringify({
            model: m,
            messages,
            temperature: needsReasoning ? 0.2 : (needsCoding ? 0.3 : 0.7),
            max_tokens: (needsReasoning || needsCoding || isHeavy) ? 8192 : 4096,
          });

          const result = await callAPI(apiBase, payload, headers);
          
          if (result.error) {
            lastError = result.error.message || 'API error';
            continue; // Try next model
          }

          const reply = result.choices?.[0]?.message?.content;
          if (!reply || !reply.trim()) {
            lastError = 'Empty response from ' + m;
            continue;
          }

          return res.status(200).json({
            reply: reply.trim(),
            usage: result.usage || {},
            model: m,
            provider: p,
            council: false
          });
        } catch (e) {
          lastError = e.message;
          continue; // Try next model
        }
      }

      // All models failed
      return res.status(500).json({ 
        error: 'All models failed. Last error: ' + (lastError || 'Unknown error'),
        tried: modelChain.map(m => m.model)
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

// Simple string similarity (Jaccard index)
function similarity(str1, str2) {
  if (!str1 || !str2) return 0;
  const set1 = new Set(str1.split(' '));
  const set2 = new Set(str2.split(' '));
  const intersection = [...set1].filter(x => set2.has(x));
  const union = new Set([...set1, ...set2]);
  return intersection.length / union.size;
}

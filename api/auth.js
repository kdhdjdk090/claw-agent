/**
 * Claw AI — Admin API + Auth Endpoints (Vercel Serverless)
 * 
 * Endpoints:
 *   POST /api/auth/signup     — Register new user
 *   POST /api/auth/login      — Email/password login
 *   POST /api/auth/logout     — Invalidate session
 *   POST /api/auth/refresh    — Refresh access token
 *   GET  /api/auth/me         — Get current user profile + plan
 * 
 *   GET  /api/admin/users     — List all users (admin)
 *   PATCH /api/admin/users/:id — Update user (ban, plan, role)
 *   GET  /api/admin/stats     — Dashboard stats (admin)
 *   GET  /api/admin/usage     — Usage logs (admin)
 *   GET  /api/admin/audit     — Audit log (admin)
 *   GET  /api/admin/plans     — List plans (admin)
 *   POST /api/admin/plans     — Create plan (admin)
 *   PATCH /api/admin/plans/:id — Update plan (admin)
 *   POST /api/admin/announce  — Create announcement (admin)
 * 
 *   GET  /api/plans           — Public plan listing
 *   GET  /api/user/usage      — User's own usage
 *   POST /api/user/apikeys    — Create API key
 *   GET  /api/user/apikeys    — List API keys
 */

const https = require('https');

const SUPABASE_URL = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || '';

function supaHeaders(token) {
  return {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${token || SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json',
  };
}

function adminHeaders() {
  return {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${SUPABASE_SERVICE_KEY || SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json',
  };
}

// Generic Supabase REST call
function supaRest(path, { method = 'GET', headers, body, query } = {}) {
  let url = `${SUPABASE_URL}/rest/v1/${path}`;
  if (query) {
    const qs = new URLSearchParams(query).toString();
    url += (url.includes('?') ? '&' : '?') + qs;
  }
  const parsed = new URL(url);
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: parsed.hostname,
      port: 443,
      path: parsed.pathname + parsed.search,
      method,
      headers: { ...headers, 'Accept': 'application/json' },
      timeout: 10000,
    };
    if (method === 'POST' || method === 'PATCH') {
      headers['Prefer'] = 'return=representation';
      opts.headers['Prefer'] = 'return=representation';
    }
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data: data }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

// Supabase Auth call
function supaAuth(endpoint, { method = 'POST', token, body } = {}) {
  const url = new URL(`${SUPABASE_URL}/auth/v1/${endpoint}`);
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname + url.search,
      method,
      headers: supaHeaders(token),
      timeout: 10000,
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// Extract JWT from Authorization header
function extractToken(req) {
  const auth = req.headers.authorization || '';
  if (auth.startsWith('Bearer ')) return auth.slice(7);
  return '';
}

// Verify token and get user
async function getAuthedUser(req) {
  const token = extractToken(req);
  if (!token) return null;
  const { data } = await supaAuth('user', { method: 'GET', token });
  if (!data || !data.id) return null;
  return { ...data, token };
}

// Check admin role
async function requireAdmin(req) {
  const user = await getAuthedUser(req);
  if (!user) return { error: 'Not authenticated', status: 401 };
  // Get profile to check role
  const { data: profiles } = await supaRest(`profiles?id=eq.${user.id}&select=role`, {
    headers: adminHeaders()
  });
  if (!Array.isArray(profiles) || !profiles[0]) return { error: 'Profile not found', status: 404 };
  const role = profiles[0].role;
  if (role !== 'admin' && role !== 'superadmin') {
    return { error: 'Admin access required', status: 403 };
  }
  return { user: { ...user, role }, error: null };
}

// Parse JSON body
function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > 100 * 1024) { req.destroy(); resolve({}); return; }
      body += chunk;
    });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch { resolve({}); }
    });
  });
}

// CORS
function cors(req, res) {
  const origin = req.headers.origin || '*';
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
}

module.exports = async (req, res) => {
  cors(req, res);
  if (req.method === 'OPTIONS') return res.status(200).end();

  const url = req.url.split('?')[0];

  try {
    // ========== AUTH ENDPOINTS ==========

    // POST /api/auth/signup
    if (url === '/api/auth/signup' && req.method === 'POST') {
      const { email, password, display_name } = await parseBody(req);
      if (!email || !password) return res.status(400).json({ error: 'email and password required' });
      if (password.length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters' });

      const payload = { email, password };
      if (display_name) payload.data = { display_name };

      const { status, data } = await supaAuth('signup', { body: payload });
      if (status >= 400) return res.status(status).json({ error: data.msg || data.error_description || 'Signup failed' });
      return res.status(200).json({
        message: data.access_token ? 'Account created!' : 'Check your email to confirm.',
        user: data.user ? { id: data.user.id, email: data.user.email } : null,
        access_token: data.access_token || null,
        refresh_token: data.refresh_token || null,
        expires_in: data.expires_in || null,
      });
    }

    // POST /api/auth/login
    if (url === '/api/auth/login' && req.method === 'POST') {
      const { email, password } = await parseBody(req);
      if (!email || !password) return res.status(400).json({ error: 'email and password required' });

      const { status, data } = await supaAuth('token?grant_type=password', { body: { email, password } });
      if (status >= 400) return res.status(status).json({ error: data.msg || data.error_description || 'Login failed' });

      // Check if banned
      const { data: profiles } = await supaRest(`profiles?id=eq.${data.user.id}&select=*,plans(*)`, {
        headers: adminHeaders()
      });
      const profile = Array.isArray(profiles) ? profiles[0] : null;
      if (profile && profile.is_banned) {
        return res.status(403).json({ error: `Account banned: ${profile.ban_reason || 'No reason given'}` });
      }

      return res.status(200).json({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
        user: { id: data.user.id, email: data.user.email },
        profile: profile || null,
        plan: profile && profile.plans ? profile.plans : null,
      });
    }

    // POST /api/auth/refresh
    if (url === '/api/auth/refresh' && req.method === 'POST') {
      const { refresh_token } = await parseBody(req);
      if (!refresh_token) return res.status(400).json({ error: 'refresh_token required' });
      const { status, data } = await supaAuth('token?grant_type=refresh_token', { body: { refresh_token } });
      if (status >= 400) return res.status(status).json({ error: 'Token refresh failed' });
      return res.status(200).json(data);
    }

    // POST /api/auth/logout
    if (url === '/api/auth/logout' && req.method === 'POST') {
      const token = extractToken(req);
      if (token) await supaAuth('logout', { token });
      return res.status(200).json({ message: 'Logged out' });
    }

    // GET /api/auth/me
    if (url === '/api/auth/me' && req.method === 'GET') {
      const user = await getAuthedUser(req);
      if (!user) return res.status(401).json({ error: 'Not authenticated' });
      const { data: profiles } = await supaRest(`profiles?id=eq.${user.id}&select=*,plans(*)`, {
        headers: supaHeaders(user.token)
      });
      const profile = Array.isArray(profiles) ? profiles[0] : null;
      return res.status(200).json({ user: { id: user.id, email: user.email }, profile, plan: profile?.plans || null });
    }

    // ========== PUBLIC ENDPOINTS ==========

    // GET /api/plans
    if (url === '/api/plans' && req.method === 'GET') {
      const { data } = await supaRest('plans?is_active=eq.true&order=sort_order.asc&select=id,name,display_name,description,price_monthly,price_yearly,max_tokens_per_day,max_tokens_per_month,max_sessions,max_turns_per_session,council_access,cloud_models,ultrathink_mode,mcp_access,api_access,custom_skills', {
        headers: supaHeaders()
      });
      return res.status(200).json({ plans: Array.isArray(data) ? data : [] });
    }

    // ========== USER ENDPOINTS ==========

    // GET /api/user/usage
    if (url === '/api/user/usage' && req.method === 'GET') {
      const user = await getAuthedUser(req);
      if (!user) return res.status(401).json({ error: 'Not authenticated' });
      const { data } = await supaRest(`usage_logs?user_id=eq.${user.id}&order=created_at.desc&limit=100&select=*`, {
        headers: supaHeaders(user.token)
      });
      return res.status(200).json({ usage: Array.isArray(data) ? data : [] });
    }

    // POST /api/user/apikeys
    if (url === '/api/user/apikeys' && req.method === 'POST') {
      const user = await getAuthedUser(req);
      if (!user) return res.status(401).json({ error: 'Not authenticated' });
      const { name } = await parseBody(req);
      const crypto = require('crypto');
      const rawKey = 'claw_' + crypto.randomBytes(32).toString('hex');
      const keyHash = crypto.createHash('sha256').update(rawKey).digest('hex');
      const keyPrefix = rawKey.substring(0, 12);
      const { data } = await supaRest('api_keys', {
        method: 'POST',
        headers: adminHeaders(),
        body: JSON.stringify({ user_id: user.id, key_hash: keyHash, key_prefix: keyPrefix, name: name || 'Default' }),
      });
      return res.status(200).json({ key: rawKey, prefix: keyPrefix, message: 'Save this key — it won\'t be shown again.' });
    }

    // GET /api/user/apikeys
    if (url === '/api/user/apikeys' && req.method === 'GET') {
      const user = await getAuthedUser(req);
      if (!user) return res.status(401).json({ error: 'Not authenticated' });
      const { data } = await supaRest(`api_keys?user_id=eq.${user.id}&select=id,key_prefix,name,is_active,last_used,created_at&order=created_at.desc`, {
        headers: supaHeaders(user.token)
      });
      return res.status(200).json({ keys: Array.isArray(data) ? data : [] });
    }

    // ========== ADMIN ENDPOINTS ==========

    // GET /api/admin/stats
    if (url === '/api/admin/stats' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      
      const [{ data: profiles }, { data: usage }, { data: plans }] = await Promise.all([
        supaRest('profiles?select=id,email,display_name,role,plan_id,is_active,is_banned,tokens_used_today,tokens_used_month,total_tokens_used,total_sessions,total_turns,created_at,last_active', { headers: adminHeaders() }),
        supaRest('usage_logs?select=total_tokens,tool_calls,created_at&order=created_at.desc&limit=1000', { headers: adminHeaders() }),
        supaRest('plans?select=*&order=sort_order.asc', { headers: adminHeaders() }),
      ]);
      
      const pArr = Array.isArray(profiles) ? profiles : [];
      const uArr = Array.isArray(usage) ? usage : [];
      
      return res.status(200).json({
        total_users: pArr.length,
        active_users: pArr.filter(p => p.is_active && !p.is_banned).length,
        banned_users: pArr.filter(p => p.is_banned).length,
        admin_users: pArr.filter(p => p.role === 'admin' || p.role === 'superadmin').length,
        total_tokens: uArr.reduce((s, u) => s + (u.total_tokens || 0), 0),
        total_tool_calls: uArr.reduce((s, u) => s + (u.tool_calls || 0), 0),
        total_sessions: pArr.reduce((s, p) => s + (p.total_sessions || 0), 0),
        plans: Array.isArray(plans) ? plans : [],
        users_by_plan: pArr.reduce((acc, p) => { acc[p.plan_id || 'none'] = (acc[p.plan_id || 'none'] || 0) + 1; return acc; }, {}),
        recent_signups: pArr.filter(p => {
          const d = new Date(p.created_at);
          return d > new Date(Date.now() - 7 * 86400000);
        }).length,
      });
    }

    // GET /api/admin/users
    if (url === '/api/admin/users' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { data } = await supaRest('profiles?select=*,plans(name,display_name)&order=created_at.desc', { headers: adminHeaders() });
      return res.status(200).json({ users: Array.isArray(data) ? data : [] });
    }

    // PATCH /api/admin/users (body: { user_id, updates })
    if (url === '/api/admin/users' && req.method === 'PATCH') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { user_id, updates } = await parseBody(req);
      if (!user_id || !updates) return res.status(400).json({ error: 'user_id and updates required' });
      
      // Whitelist allowed fields
      const allowed = ['plan_id', 'role', 'is_active', 'is_banned', 'ban_reason', 'display_name', 'preferred_model', 'tokens_used_today', 'tokens_used_month'];
      const safe = {};
      for (const k of Object.keys(updates)) {
        if (allowed.includes(k)) safe[k] = updates[k];
      }
      if (Object.keys(safe).length === 0) return res.status(400).json({ error: 'No valid fields to update' });
      
      // Apply update
      const { data } = await supaRest(`profiles?id=eq.${user_id}`, {
        method: 'PATCH',
        headers: adminHeaders(),
        body: JSON.stringify(safe),
      });
      
      // Audit log
      await supaRest('admin_audit_log', {
        method: 'POST',
        headers: adminHeaders(),
        body: JSON.stringify({
          admin_id: user.id,
          action: safe.is_banned !== undefined ? 'ban_user' : (safe.plan_id ? 'change_plan' : (safe.role ? 'change_role' : 'update_user')),
          target_user_id: user_id,
          details: safe,
        }),
      });
      
      return res.status(200).json({ message: 'User updated', data });
    }

    // GET /api/admin/usage
    if (url === '/api/admin/usage' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { data } = await supaRest('usage_logs?select=*,profiles(email,display_name)&order=created_at.desc&limit=500', { headers: adminHeaders() });
      return res.status(200).json({ usage: Array.isArray(data) ? data : [] });
    }

    // GET /api/admin/audit
    if (url === '/api/admin/audit' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { data } = await supaRest('admin_audit_log?select=*&order=created_at.desc&limit=200', { headers: adminHeaders() });
      return res.status(200).json({ audit: Array.isArray(data) ? data : [] });
    }

    // GET /api/admin/plans
    if (url === '/api/admin/plans' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { data } = await supaRest('plans?select=*&order=sort_order.asc', { headers: adminHeaders() });
      return res.status(200).json({ plans: Array.isArray(data) ? data : [] });
    }

    // POST /api/admin/plans
    if (url === '/api/admin/plans' && req.method === 'POST') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const plan = await parseBody(req);
      if (!plan.name) return res.status(400).json({ error: 'Plan name required' });
      const { data } = await supaRest('plans', {
        method: 'POST', headers: adminHeaders(), body: JSON.stringify(plan),
      });
      return res.status(200).json({ message: 'Plan created', plan: data });
    }

    // PATCH /api/admin/plans (body: { plan_id, updates })
    if (url === '/api/admin/plans' && req.method === 'PATCH') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { plan_id, updates } = await parseBody(req);
      if (!plan_id || !updates) return res.status(400).json({ error: 'plan_id and updates required' });
      const { data } = await supaRest(`plans?id=eq.${plan_id}`, {
        method: 'PATCH', headers: adminHeaders(), body: JSON.stringify(updates),
      });
      return res.status(200).json({ message: 'Plan updated', plan: data });
    }

    // POST /api/admin/announce
    if (url === '/api/admin/announce' && req.method === 'POST') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { title, content, type } = await parseBody(req);
      if (!title || !content) return res.status(400).json({ error: 'title and content required' });
      const { data } = await supaRest('announcements', {
        method: 'POST', headers: adminHeaders(),
        body: JSON.stringify({ admin_id: user.id, title, content, type: type || 'info' }),
      });
      return res.status(200).json({ message: 'Announcement created', data });
    }

    // GET /api/admin/announcements
    if (url === '/api/admin/announcements' && req.method === 'GET') {
      const { data } = await supaRest('announcements?is_active=eq.true&order=created_at.desc&limit=10&select=*', {
        headers: supaHeaders(extractToken(req) || SUPABASE_ANON_KEY)
      });
      return res.status(200).json({ announcements: Array.isArray(data) ? data : [] });
    }

    // ========== LEADS MANAGEMENT ==========

    // GET /api/admin/leads
    if (url === '/api/admin/leads' && req.method === 'GET') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { data } = await supaRest('leads?select=*&order=created_at.desc&limit=500', {
        headers: adminHeaders(),
      });
      return res.status(200).json({ leads: Array.isArray(data) ? data : [] });
    }

    // PATCH /api/admin/leads
    if (url === '/api/admin/leads' && req.method === 'PATCH') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { id, updates } = await parseBody(req);
      if (!id || !updates) return res.status(400).json({ error: 'id and updates required' });

      const allowed = ['name', 'email', 'phone', 'source', 'medium', 'campaign', 'page_path', 'event_type', 'lead_score'];
      const safe = Object.fromEntries(Object.entries(updates).filter(([k]) => allowed.includes(k)));
      if (!Object.keys(safe).length) return res.status(400).json({ error: 'No valid lead fields provided' });

      await supaRest(`leads?id=eq.${id}`, {
        method: 'PATCH', headers: adminHeaders(), body: JSON.stringify(safe),
      });
      await supaRest('admin_audit_log', {
        method: 'POST', headers: adminHeaders(),
        body: JSON.stringify({ admin_id: user.id, action: 'edit_lead', target_id: id, details: safe }),
      });
      return res.status(200).json({ message: 'Lead updated' });
    }

    // DELETE /api/admin/leads
    if (url === '/api/admin/leads' && req.method === 'DELETE') {
      const { user, error } = await requireAdmin(req);
      if (error) return res.status(user ? 403 : 401).json({ error });
      const { id } = await parseBody(req);
      if (!id) return res.status(400).json({ error: 'id required' });
      await supaRest(`leads?id=eq.${id}`, {
        method: 'DELETE', headers: adminHeaders(),
      });
      // Audit log
      await supaRest('admin_audit_log', {
        method: 'POST', headers: adminHeaders(),
        body: JSON.stringify({ admin_id: user.id, action: 'delete_lead', target_id: id, details: { deleted_lead_id: id } }),
      });
      return res.status(200).json({ message: 'Lead deleted' });
    }

    // ========== FALLBACK ==========
    return res.status(404).json({ error: 'Not found', available: [
      'POST /api/auth/signup', 'POST /api/auth/login', 'POST /api/auth/refresh',
      'POST /api/auth/logout', 'GET /api/auth/me',
      'GET /api/plans', 'GET /api/user/usage', 'POST /api/user/apikeys',
      'GET /api/admin/stats', 'GET /api/admin/users', 'PATCH /api/admin/users',
      'GET /api/admin/usage', 'GET /api/admin/audit', 'GET /api/admin/plans',
      'POST /api/admin/plans', 'PATCH /api/admin/plans', 'POST /api/admin/announce',
      'GET /api/admin/leads', 'PATCH /api/admin/leads', 'DELETE /api/admin/leads',
    ]});

  } catch (err) {
    console.error('Auth API error:', err.message);
    return res.status(500).json({ error: 'Internal server error' });
  }
};

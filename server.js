'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cookie = require('cookie');
const { DatabaseSync } = require('node:sqlite');

const PORT = Number(process.env.PORT) || 3000;
const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'cowhand.sqlite');
const USER = process.env.COWHAND_USER;
const PASS = process.env.COWHAND_PASS;
const PUBLIC_DIR = path.join(__dirname, 'public');
const SESSION_COOKIE = 'cowhand_sid';
const SESSION_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

if (!USER || !PASS) {
  console.error('COWHAND_USER e COWHAND_PASS precisam estar definidos (veja .env.example). Encerrando.');
  process.exit(1);
}

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA journal_mode = WAL');
db.exec(`
  CREATE TABLE IF NOT EXISTS state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at TEXT NOT NULL
  );
`);
db.exec(`
  CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    expires_at TEXT NOT NULL
  );
`);

function seedIfEmpty() {
  const row = db.prepare('SELECT id FROM state WHERE id = 1').get();
  if (row) return;
  const seedPath = path.join(__dirname, 'seed_data.json');
  const seed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  db.prepare('INSERT INTO state (id, data, version, updated_at) VALUES (1, ?, 1, ?)')
    .run(JSON.stringify(seed), new Date().toISOString());
  console.log('Estado inicial semeado a partir de seed_data.json.');
}
seedIfEmpty();

/* ---------- auth: login form + server-side session (replaces HTTP Basic Auth) ----------
 * Basic Auth credentials are resent "ambiently" by the browser to any same-origin request
 * regardless of who triggered it, which is what made the old CSRF mitigation (Origin-header
 * checking) necessary in the first place. A session cookie with SameSite=Strict is not sent
 * on cross-site requests at all, closing that hole at the browser level instead of trying to
 * catch it after the fact. */

// Hash both sides to a fixed-length digest before comparing, so differing input
// lengths don't take a measurably different code path (closes a minor timing side-channel).
function timingSafeCredentialEqual(provided, expected) {
  const a = crypto.createHash('sha256').update(String(provided)).digest();
  const b = crypto.createHash('sha256').update(String(expected)).digest();
  return crypto.timingSafeEqual(a, b);
}

function createSession() {
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + SESSION_MAX_AGE_MS).toISOString();
  db.prepare('INSERT INTO sessions (token, expires_at) VALUES (?, ?)').run(token, expiresAt);
  // opportunistic cleanup of expired sessions, no separate cron needed
  db.prepare('DELETE FROM sessions WHERE expires_at < ?').run(new Date().toISOString());
  return { token, expiresAt };
}

function destroySession(token) {
  if (token) db.prepare('DELETE FROM sessions WHERE token = ?').run(token);
}

function isValidSession(token) {
  if (!token) return false;
  const row = db.prepare('SELECT expires_at FROM sessions WHERE token = ?').get(token);
  return !!row && row.expires_at > new Date().toISOString();
}

// Secure is decided per-request (req.secure, via `trust proxy`) rather than a single
// NODE_ENV-wide flag: this app is reachable both directly over plain HTTP on the LAN and
// through a TLS-terminating tunnel/proxy publicly. A Secure cookie set while answering a
// plain-HTTP request is silently dropped by the browser (RFC 6265) — login would appear to
// "not work" on the LAN even though the server did everything right. Mirroring whichever
// protocol *this* request actually arrived over keeps both paths working at once.
function setSessionCookie(req, res, token) {
  res.setHeader('Set-Cookie', cookie.serialize(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: req.secure,
    sameSite: 'strict',
    path: '/',
    maxAge: SESSION_MAX_AGE_MS / 1000,
  }));
}

function clearSessionCookie(req, res) {
  res.setHeader('Set-Cookie', cookie.serialize(SESSION_COOKIE, '', {
    httpOnly: true,
    secure: req.secure,
    sameSite: 'strict',
    path: '/',
    maxAge: 0,
  }));
}

function getSessionToken(req) {
  const header = req.headers.cookie;
  if (!header) return null;
  const parsed = cookie.parse(header);
  return parsed[SESSION_COOKIE] || null;
}

// Gate for everything except the login page/endpoint. Redirects browser navigations to
// /login, but responds with plain 401 JSON for API/fetch calls (the client JS handles that).
function requireSession(req, res, next) {
  if (isValidSession(getSessionToken(req))) return next();
  if (req.path.startsWith('/api/')) {
    return res.status(401).json({ error: 'not_authenticated' });
  }
  res.redirect(302, '/login');
}

const loginLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: 'Muitas tentativas. Tente novamente em instantes.',
  // NOT skipSuccessfulRequests: both success and failure redirect with a 2xx/3xx status
  // here (progressive-enhancement HTML form flow), so express-rate-limit's status-code-based
  // "successful request" heuristic can't tell them apart — count every attempt instead.
});

// Requests that mutate shared state are only ever made by our own page's JS (fetch with a
// relative URL). SameSite=Strict already stops the session cookie from being sent on a
// cross-site request, but this is a cheap extra layer of defense-in-depth against CSRF.
function requireSameOrigin(req, res, next) {
  const origin = req.headers.origin;
  if (origin) {
    let originHost;
    try { originHost = new URL(origin).host; } catch (e) { originHost = null; }
    if (originHost !== req.headers.host) {
      return res.status(403).json({ error: 'cross_origin_forbidden' });
    }
  }
  next();
}

/* ---------- input validation ----------
 * Enums are loaded from taxonomy.json (generated by build_app.py from the same
 * CATEGORIAS/SUBCATEGORIAS/... constants baked into the client) so the server never
 * drifts out of sync with what the UI actually offers. */
const taxonomy = JSON.parse(fs.readFileSync(path.join(__dirname, 'taxonomy.json'), 'utf8'));
const CATEGORIAS = new Set(taxonomy.CATEGORIAS);
const SUBCATEGORIAS = new Set(taxonomy.SUBCATEGORIAS);
const RESPONSAVEL_OPTS = new Set(taxonomy.RESPONSAVEL_OPTS);
const TIPO_OPTS = new Set(taxonomy.TIPO_OPTS);
const FORMA_PGTO_OPTS = new Set(taxonomy.FORMA_PGTO_OPTS);
const STATUS_OPTS = new Set(taxonomy.STATUS_OPTS);

function isPlainString(v, maxLen) {
  return typeof v === 'string' && v.length <= maxLen;
}
function isFiniteNumber(v) {
  return typeof v === 'number' && Number.isFinite(v);
}
function validTransacao(t) {
  return t && typeof t === 'object' &&
    isPlainString(t.id, 100) &&
    isPlainString(t.data, 20) &&
    isPlainString(t.descricao, 500) &&
    CATEGORIAS.has(t.categoria) &&
    (t.subcategoria === '' || SUBCATEGORIAS.has(t.subcategoria)) &&
    (t.formaPagamento === '' || FORMA_PGTO_OPTS.has(t.formaPagamento)) &&
    RESPONSAVEL_OPTS.has(t.responsavel) &&
    TIPO_OPTS.has(t.tipo) &&
    (t.status === undefined || STATUS_OPTS.has(t.status)) &&
    isPlainString(t.parcela || '', 20) &&
    isFiniteNumber(t.valor);
}
function validRecorrente(r) {
  return r && typeof r === 'object' &&
    isPlainString(r.id, 100) &&
    CATEGORIAS.has(r.categoria) &&
    (r.subcategoria === '' || SUBCATEGORIAS.has(r.subcategoria)) &&
    isPlainString(r.item, 200) &&
    RESPONSAVEL_OPTS.has(r.responsavel) &&
    (r.forma === '' || FORMA_PGTO_OPTS.has(r.forma)) &&
    TIPO_OPTS.has(r.tipo) &&
    isFiniteNumber(r.valorEsperado) &&
    isPlainString(r.parcela || '', 20) &&
    isPlainString(r.obs || '', 500) &&
    isPlainString(r.chave || '', 100);
}
function validMeta(m) {
  return m && typeof m === 'object' &&
    isPlainString(m.id, 100) &&
    isPlainString(m.nome, 200) &&
    isPlainString(m.subcategoria || '', 100) &&
    isFiniteNumber(m.valorAtual) &&
    isFiniteNumber(m.valorAlvo) &&
    isPlainString(m.prazo || '', 20) &&
    isFiniteNumber(m.contribPlanejada);
}
function validState(state) {
  if (!state || typeof state !== 'object') return false;
  if (typeof state.renda !== 'object' || !isFiniteNumber(state.renda.henrique) || !isFiniteNumber(state.renda.carol)) return false;
  if (!Array.isArray(state.transacoes) || state.transacoes.length > 20000 || !state.transacoes.every(validTransacao)) return false;
  if (!Array.isArray(state.recorrentes) || state.recorrentes.length > 500 || !state.recorrentes.every(validRecorrente)) return false;
  if (!Array.isArray(state.metas) || state.metas.length > 100 || !state.metas.every(validMeta)) return false;
  return true;
}

// index.html's app logic is a single inline <script> (no build step, no bundler) — rather
// than weakening CSP with 'unsafe-inline', allow exactly that script via a content hash
// computed from the file itself, so any *injected* inline script (e.g. via XSS) still
// won't match the hash and will be blocked by the browser.
function inlineScriptHash() {
  const html = fs.readFileSync(path.join(PUBLIC_DIR, 'index.html'), 'utf8');
  const match = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!match) throw new Error('index.html: inline <script> not found, cannot compute CSP hash');
  // the HTML parser normalizes CRLF/CR to LF before exposing script text content, so the
  // hash must be computed over the same normalized text the browser actually hashes.
  const normalized = match[1].replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const digest = crypto.createHash('sha256').update(normalized, 'utf8').digest('base64');
  return `'sha256-${digest}'`;
}

const app = express();
app.disable('x-powered-by');
// behind a reverse proxy (Cloudflare Tunnel, or any other) that terminates TLS; needed for
// req.secure / X-Forwarded-Proto to reflect the client's real protocol — see setSessionCookie.
app.set('trust proxy', 1);
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      // the app renders many elements with inline style="..." attributes (no CSS-in-JS
      // build step) — CSP has no hash/nonce mechanism for style *attributes* (only for
      // <style> blocks), so this directive can't be tightened further without rewriting
      // the renderer to use CSS classes instead. scriptSrc below stays strict: that's
      // where real code-execution risk lives, and it's still hash-locked (login.html has
      // no script at all — it's a plain HTML form).
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      scriptSrc: ["'self'", inlineScriptHash()],
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'"],
      formAction: ["'self'"],
      objectSrc: ["'none'"],
      baseUri: ["'none'"],
      frameAncestors: ["'none'"],
      // this app is reached both over plain HTTP (LAN) and HTTPS (via tunnel/proxy) — forcing
      // every subresource to upgrade to HTTPS breaks the LAN path outright (nothing there
      // speaks TLS), so explicitly cancel helmet's default inclusion of this directive.
      upgradeInsecureRequests: null,
    },
  },
}));
app.use(express.urlencoded({ extended: false })); // login form: application/x-www-form-urlencoded
app.use(express.json({ limit: '2mb' }));

/* ---------- login / logout (unauthenticated routes) ---------- */
const LOGIN_HTML = fs.readFileSync(path.join(__dirname, 'login.html'), 'utf8');
const LOGIN_HTML_ERROR = LOGIN_HTML.replace('<!--ERROR-->',
  '<div class="error">Usuário ou senha incorretos.</div>');

app.get('/login', (req, res) => {
  if (isValidSession(getSessionToken(req))) return res.redirect(302, '/');
  res.type('html').send(req.query.error ? LOGIN_HTML_ERROR : LOGIN_HTML.replace('<!--ERROR-->', ''));
});

// the login page needs the logo before the visitor has a session, so it can't go through
// the general express.static(PUBLIC_DIR) below (that's gated by requireSession)
app.get('/logo.png', (req, res) => res.sendFile(path.join(PUBLIC_DIR, 'logo.png')));

app.post('/api/login', loginLimiter, (req, res) => {
  const { username, password } = req.body || {};
  if (isPlainString(username, 200) && isPlainString(password, 200) &&
      timingSafeCredentialEqual(username, USER) && timingSafeCredentialEqual(password, PASS)) {
    const { token } = createSession();
    setSessionCookie(req, res, token);
    return res.redirect(303, '/');
  }
  res.redirect(303, '/login?error=1');
});

app.get('/logout', (req, res) => {
  destroySession(getSessionToken(req));
  clearSessionCookie(req, res);
  res.redirect(302, '/login');
});

/* ---------- everything below requires a valid session ---------- */
app.use(requireSession);

app.get('/api/state', (req, res) => {
  const row = db.prepare('SELECT data, version FROM state WHERE id = 1').get();
  res.json({ state: JSON.parse(row.data), version: row.version });
});

app.put('/api/state', requireSameOrigin, (req, res) => {
  const { state, version } = req.body || {};
  if (typeof version !== 'number' || !validState(state)) {
    return res.status(400).json({ error: 'invalid_payload' });
  }
  const current = db.prepare('SELECT data, version FROM state WHERE id = 1').get();
  if (current.version !== version) {
    return res.status(409).json({ state: JSON.parse(current.data), version: current.version });
  }
  const nextVersion = current.version + 1;
  const updatedAt = new Date().toISOString();
  state.updatedAt = updatedAt;
  db.prepare('UPDATE state SET data = ?, version = ?, updated_at = ? WHERE id = 1')
    .run(JSON.stringify(state), nextVersion, updatedAt);
  res.json({ version: nextVersion, updatedAt });
});

app.use(express.static(PUBLIC_DIR, { index: 'index.html' }));

// Centralized error handler: never leak stack traces / internal paths to the client.
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(err.status || 500).json({ error: 'internal_error' });
});

app.listen(PORT, () => {
  console.log(`cowhand rodando na porta ${PORT}`);
});

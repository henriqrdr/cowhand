'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const express = require('express');
const { DatabaseSync } = require('node:sqlite');

const PORT = Number(process.env.PORT) || 3000;
const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'cowhand.sqlite');
const USER = process.env.COWHAND_USER;
const PASS = process.env.COWHAND_PASS;

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

function timingSafeStringEqual(a, b) {
  const bufA = Buffer.from(String(a));
  const bufB = Buffer.from(String(b));
  if (bufA.length !== bufB.length) {
    crypto.timingSafeEqual(bufA, Buffer.alloc(bufA.length));
    return false;
  }
  return crypto.timingSafeEqual(bufA, bufB);
}

function requireAuth(req, res, next) {
  const header = req.headers.authorization || '';
  const [scheme, encoded] = header.split(' ');
  if (scheme === 'Basic' && encoded) {
    let decoded = '';
    try { decoded = Buffer.from(encoded, 'base64').toString('utf8'); } catch (e) { decoded = ''; }
    const sep = decoded.indexOf(':');
    const user = sep === -1 ? decoded : decoded.slice(0, sep);
    const pass = sep === -1 ? '' : decoded.slice(sep + 1);
    if (timingSafeStringEqual(user, USER) && timingSafeStringEqual(pass, PASS)) {
      return next();
    }
  }
  res.set('WWW-Authenticate', 'Basic realm="cowhand"');
  res.status(401).send('Autenticação necessária.');
}

const app = express();
app.disable('x-powered-by');
app.use(requireAuth);
app.use(express.json({ limit: '2mb' }));

app.get('/api/state', (req, res) => {
  const row = db.prepare('SELECT data, version FROM state WHERE id = 1').get();
  res.json({ state: JSON.parse(row.data), version: row.version });
});

app.put('/api/state', (req, res) => {
  const { state, version } = req.body || {};
  if (typeof version !== 'number' || !state || typeof state !== 'object' ||
      !Array.isArray(state.transacoes) || !Array.isArray(state.recorrentes) ||
      !Array.isArray(state.metas) || typeof state.renda !== 'object') {
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

app.use(express.static(__dirname, { index: 'index.html' }));

app.listen(PORT, () => {
  console.log(`cowhand rodando em http://localhost:${PORT} (banco: ${DB_PATH})`);
});

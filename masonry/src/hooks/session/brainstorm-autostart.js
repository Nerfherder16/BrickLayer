'use strict';

/**
 * Auto-start brainstorm server at session init.
 *
 * Checks if port 7823 is accepting connections. If not, spawns the
 * server.cjs process detached and waits up to 3 seconds for /health.
 * Then POSTs /session with the project slug to activate chronicle
 * persistence for this session.
 */

const net = require('net');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const PORT = parseInt(process.env.BRAINSTORM_PORT || '7823', 10);
const SERVER_CJS = path.resolve(__dirname, '../../brainstorm/server.cjs');
const HEALTH_URL = `http://localhost:${PORT}/health`;
const SESSION_URL = `http://localhost:${PORT}/session`;

/**
 * Returns true if port is accepting TCP connections (server up).
 */
function isPortOpen(port) {
  return new Promise((resolve) => {
    const sock = net.createConnection({ port, host: '127.0.0.1' });
    sock.setTimeout(400);
    sock.on('connect', () => { sock.destroy(); resolve(true); });
    sock.on('error', () => resolve(false));
    sock.on('timeout', () => { sock.destroy(); resolve(false); });
  });
}

/**
 * Fetch a URL and return { ok, body }.
 */
function httpGet(url) {
  return new Promise((resolve) => {
    http.get(url, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => resolve({ ok: res.statusCode === 200, body }));
    }).on('error', () => resolve({ ok: false, body: '' }));
  });
}

/**
 * POST JSON body to url, resolve with { ok, body }.
 */
function httpPost(url, data) {
  return new Promise((resolve) => {
    const body = JSON.stringify(data);
    const parsed = new URL(url);
    const opts = {
      hostname: parsed.hostname,
      port: parseInt(parsed.port || '80', 10),
      path: parsed.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    };
    const req = http.request(opts, (res) => {
      let rb = '';
      res.on('data', (c) => (rb += c));
      res.on('end', () => resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, body: rb }));
    });
    req.on('error', () => resolve({ ok: false, body: '' }));
    req.write(body);
    req.end();
  });
}

/**
 * Derive a project slug from the cwd path.
 * e.g. /home/user/Dev/Bricklayer2.0 → "Bricklayer2.0"
 */
function slugFromCwd(cwd) {
  return path.basename(cwd || process.cwd()).replace(/\s+/g, '-').toLowerCase();
}

/**
 * Wait up to maxMs for /health to return 200, polling every 500ms.
 */
async function waitForHealth(maxMs) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    const r = await httpGet(HEALTH_URL);
    if (r.ok) return true;
    await new Promise((res) => setTimeout(res, 500));
  }
  return false;
}

/**
 * Main entry point — called from masonry-session-start.js Phase 0.7.
 * Never throws — all errors are swallowed so the hook always continues.
 */
async function autoStartBrainstorm(cwd) {
  try {
    const alive = await isPortOpen(PORT);
    if (!alive) {
      // Spawn detached so it outlives this hook process
      const child = spawn('node', [SERVER_CJS], {
        detached: true,
        stdio: 'ignore',
        env: { ...process.env },
      });
      child.unref();

      const started = await waitForHealth(3000);
      if (!started) return; // server failed to start — silent, don't block session
    }

    // POST /session to activate chronicle persistence for this run
    const slug = slugFromCwd(cwd);
    await httpPost(SESSION_URL, { slug });
  } catch {
    // Never block session start
  }
}

module.exports = { autoStartBrainstorm, isPortOpen, slugFromCwd };

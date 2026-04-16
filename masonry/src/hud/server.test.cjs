'use strict';

// vitest globals (describe, it, expect, beforeAll, afterAll) are injected
// via globals:true in vitest.config.js — no require('vitest') needed.

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const SERVER_PATH = path.join(__dirname, 'server.cjs');

// Use a test-only port to avoid colliding with a running real server
const TEST_PORT = 17824;

/**
 * Start server.cjs as a child process, wait up to 4s for /health, return { proc }.
 */
async function startServer(env = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [SERVER_PATH], {
      env: {
        ...process.env,
        HUD_PORT: String(TEST_PORT),
        ...env,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stderr = '';
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('exit', (code) => {
      if (code !== 0) reject(new Error(`Server exited with code ${code}: ${stderr}`));
    });

    const deadline = Date.now() + 4000;
    const poll = () => {
      const req = http.request({ host: '127.0.0.1', port: TEST_PORT, path: '/health' }, () => {
        resolve({ proc });
      });
      req.on('error', () => {
        if (Date.now() < deadline) setTimeout(poll, 50);
        else reject(new Error('Server did not start in time'));
      });
      req.end();
    };
    poll();
  });
}

function stopServer(proc) {
  return new Promise((resolve) => {
    proc.on('exit', resolve);
    proc.kill('SIGTERM');
    setTimeout(resolve, 600);
  });
}

/** Simple GET helper → { status, headers, body } */
function get(port, urlPath) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: urlPath }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error', reject);
    req.end();
  });
}

/** Connect to /events, capture headers, then destroy the request */
function connectEvents(port) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: '/events' }, (res) => {
      resolve({ status: res.statusCode, headers: res.headers });
      res.on('data', () => {});
      req.destroy();
    });
    req.on('error', () => {}); // expected after destroy
    req.end();
  });
}

// ─── Suite 1: basic endpoints ─────────────────────────────────────────────────

describe('HUD server — basic endpoints', () => {
  let proc;

  beforeAll(async () => {
    const result = await startServer();
    proc = result.proc;
  }, 8000);

  afterAll(async () => {
    if (proc) await stopServer(proc);
  }, 3000);

  it('GET /health returns { ok: true } with status 200', async () => {
    const { status, body } = await get(TEST_PORT, '/health');
    expect(status).toBe(200);
    const data = JSON.parse(body);
    expect(data.ok).toBe(true);
  });

  it('GET /agents returns an array', async () => {
    const { status, body } = await get(TEST_PORT, '/agents');
    expect(status).toBe(200);
    const data = JSON.parse(body);
    expect(Array.isArray(data)).toBe(true);
  });

  it('GET /events returns a keep-alive response with Content-Type: text/plain', async () => {
    const { status, headers } = await connectEvents(TEST_PORT);
    expect(status).toBe(200);
    expect(headers['content-type']).toContain('text/plain');
  });

  it('Unknown route returns 404', async () => {
    const { status } = await get(TEST_PORT, '/no-such-route');
    expect(status).toBe(404);
  });
});

// ─── Suite 2: AgentRecord merge with mock data ────────────────────────────────

describe('HUD server — AgentRecord merge with mock data', () => {
  let proc;
  let dataDir;

  beforeAll(async () => {
    dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hud-test-'));

    fs.writeFileSync(
      path.join(dataDir, 'pattern-confidence.json'),
      JSON.stringify({
        developer: { confidence: 0.9, uses: 10, last_used: '2026-04-16T00:00:00Z' },
      }),
    );

    fs.writeFileSync(
      path.join(dataDir, 'telemetry.jsonl'),
      JSON.stringify({
        agent: 'developer',
        success: true,
        duration_ms: 5000,
        timestamp: '2026-04-16T00:00:00Z',
        phase: 'post',
      }) + '\n',
    );

    const result = await startServer({ DATA_ROOT: dataDir });
    proc = result.proc;
  }, 8000);

  afterAll(async () => {
    if (proc) await stopServer(proc);
    if (dataDir) fs.rmSync(dataDir, { recursive: true, force: true });
  }, 3000);

  it('GET /agents returns developer record with name, confidence, lastResult, lastDurationMs', async () => {
    const { status, body } = await get(TEST_PORT, '/agents');
    expect(status).toBe(200);
    const agents = JSON.parse(body);
    expect(Array.isArray(agents)).toBe(true);

    const dev = agents.find((a) => a.name === 'developer');
    expect(dev).toBeDefined();
    expect(dev.name).toBe('developer');
    expect(dev.confidence).toBe(0.9);
    expect(dev.lastResult).toBe('pass');
    expect(dev.lastDurationMs).toBe(5000);
  });
});

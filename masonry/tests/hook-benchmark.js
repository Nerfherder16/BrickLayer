#!/usr/bin/env node
/**
 * hook-benchmark.js — Hook verification benchmark runner.
 *
 * Infrastructure: mock HTTP server, async hook runner, assertions, test runner.
 * Test cases live in hook-benchmark-cases.js (kept separate for the 600-line limit).
 *
 * Usage:
 *   node masonry/tests/hook-benchmark.js [--filter <substring>]
 *
 * No external deps — pure Node.js stdlib.
 */

'use strict';

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ─── Paths ────────────────────────────────────────────────────────────────────

const REPO_ROOT  = path.resolve(__dirname, '../..');
const HOOKS_DIR  = path.join(REPO_ROOT, 'masonry/src/hooks');
const RECALL_DIR = path.join(os.homedir(), '.claude/recall-hooks');

function hook(name)  { return path.join(HOOKS_DIR, name); }
function rhook(name) { return path.join(RECALL_DIR, name); }

// ─── Mock HTTP server ─────────────────────────────────────────────────────────

function startMockServer() {
  const requests = [];
  const server = http.createServer((req, res) => {
    let body = '';
    req.on('data', c => (body += c));
    req.on('end', () => {
      requests.push({ method: req.method, url: req.url, body });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      if (req.url.includes('/search/browse') || req.url.includes('/retrieve')) {
        res.end(JSON.stringify({ results: [], memories: [] }));
      } else if (req.url.includes('/embed')) {
        res.end(JSON.stringify({ embedding: new Array(768).fill(0) }));
      } else {
        res.end(JSON.stringify({ ok: true }));
      }
    });
  });
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, port, requests, clear: () => (requests.length = 0) });
    });
  });
}

// ─── Async hook runner ────────────────────────────────────────────────────────
// MUST be async (spawn not spawnSync) — spawnSync blocks the parent event loop,
// which prevents the mock HTTP server from handling incoming requests.

function runHook(hookPath, stdinPayload, { env = {}, timeoutMs = 6000 } = {}) {
  return new Promise((resolve) => {
    const start = Date.now();
    const input = typeof stdinPayload === 'string' ? stdinPayload : JSON.stringify(stdinPayload);
    let stdout = '';
    let stderr = '';

    let child;
    try {
      child = spawn('node', [hookPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, ...env },
      });
    } catch (e) {
      return resolve({ exitCode: -1, stdout: '', stderr: String(e), elapsedMs: 0, timedOut: false });
    }

    child.stdout.on('data', d => (stdout += d));
    child.stderr.on('data', d => (stderr += d));
    child.stdin.write(input);
    child.stdin.end();

    const killTimer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch {}
      resolve({ exitCode: -1, stdout, stderr, elapsedMs: Date.now() - start, timedOut: true });
    }, timeoutMs);

    child.on('close', (code) => {
      clearTimeout(killTimer);
      resolve({ exitCode: code ?? 0, stdout, stderr, elapsedMs: Date.now() - start, timedOut: false });
    });

    child.on('error', () => {
      clearTimeout(killTimer);
      resolve({ exitCode: -1, stdout, stderr, elapsedMs: Date.now() - start, timedOut: false });
    });
  });
}

// ─── Assertions ───────────────────────────────────────────────────────────────

class AssertionError extends Error {}

function assertExitCode(r, expected) {
  if (r.exitCode !== expected) {
    throw new AssertionError(
      `exit_code: expected ${expected}, got ${r.exitCode}` +
      (r.stderr ? ` (stderr: ${r.stderr.slice(0, 300)})` : '')
    );
  }
}

function assertStderr(r, substring) {
  if (!r.stderr.includes(substring)) {
    throw new AssertionError(`stderr_contains: "${substring}" not in stderr`);
  }
}

function assertNoStderr(r, substring) {
  if (r.stderr.includes(substring)) {
    throw new AssertionError(`stderr_not_contains: "${substring}" unexpectedly in stderr`);
  }
}

function assertCalledPath(requests, urlSubstring) {
  if (!requests.some(rq => rq.url.includes(urlSubstring))) {
    const seen = requests.map(r => r.url).join(', ') || '(none)';
    throw new AssertionError(`called_path: no request to "${urlSubstring}" (got: ${seen})`);
  }
}

function assertNotCalledPath(requests, urlSubstring) {
  if (requests.some(rq => rq.url.includes(urlSubstring))) {
    throw new AssertionError(`not_called_path: unexpected request to "${urlSubstring}"`);
  }
}

function assertUnderMs(r, ms) {
  if (r.elapsedMs >= ms) {
    throw new AssertionError(`timing: took ${r.elapsedMs}ms, limit ${ms}ms`);
  }
}

function assertNotTimedOut(r) {
  if (r.timedOut) throw new AssertionError('hook timed out (SIGKILL)');
}

// ─── Test runner ──────────────────────────────────────────────────────────────

const results = [];
const filterArg = process.argv.includes('--filter')
  ? process.argv[process.argv.indexOf('--filter') + 1]
  : null;

async function test(name, fn) {
  if (filterArg && !name.toLowerCase().includes(filterArg.toLowerCase())) return;
  const start = Date.now();
  try {
    await fn();
    results.push({ name, status: 'PASS', ms: Date.now() - start });
  } catch (e) {
    results.push({ name, status: 'FAIL', ms: Date.now() - start, error: e.message });
  }
}

// ─── Helpers shared with cases ────────────────────────────────────────────────

const REAL_GATE_FILE = path.join(os.tmpdir(), 'masonry-mortar-gate.json');

function saveGate() {
  try { return fs.readFileSync(REAL_GATE_FILE, 'utf8'); } catch { return null; }
}

function setGate(mortar_consulted) {
  fs.writeFileSync(REAL_GATE_FILE,
    JSON.stringify({ mortar_consulted, timestamp: new Date().toISOString() }));
}

function restoreGate(saved) {
  if (saved === null) {
    try { fs.unlinkSync(REAL_GATE_FILE); } catch {}
  } else {
    fs.writeFileSync(REAL_GATE_FILE, saved);
  }
}

function makeBigJs(bytes) {
  const lines = Math.ceil(bytes / 81) + 5;
  return ('x'.repeat(80) + '\n').repeat(lines);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const mock = await startMockServer();
  const ctx = {
    mock,
    MOCK_RECALL: `http://127.0.0.1:${mock.port}`,
    MOCK_OLLAMA: `http://127.0.0.1:${mock.port}`,
    hook, rhook, runHook, test,
    assertExitCode, assertStderr, assertNoStderr,
    assertCalledPath, assertNotCalledPath,
    assertUnderMs, assertNotTimedOut,
    saveGate, setGate, restoreGate, makeBigJs,
  };

  await require('./hook-benchmark-cases')(ctx);
  await require('./hook-benchmark-cases2')(ctx);
  await new Promise(res => mock.server.close(res));

  const passed = results.filter(r => r.status === 'PASS');
  const failed = results.filter(r => r.status === 'FAIL');

  console.log('\nHOOK BENCHMARK RESULTS');
  console.log('='.repeat(60));
  for (const r of results) {
    const icon = r.status === 'PASS' ? '✓' : '✗';
    const ms   = `${r.ms}ms`.padStart(7);
    console.log(`  ${icon} ${ms}  ${r.name}`);
    if (r.status === 'FAIL') console.log(`         → ${r.error}`);
  }
  console.log('='.repeat(60));
  console.log(`  Passed: ${passed.length}  Failed: ${failed.length}  Total: ${results.length}`);
  if (failed.length > 0) process.exit(1);
}

main().catch(e => { console.error(e); process.exit(1); });

#!/usr/bin/env node
/**
 * masonry-hook-watch.js — PostToolUse async hook.
 *
 * When a Write or Edit touches a file inside masonry/src/hooks/ OR any
 * settings.json file, runs hook-smoke.js and pipes its report to stderr.
 *
 * This hook is async: true — it never blocks the write itself.
 * Timeout: 20s (smoke test is expected to finish in < 15s).
 *
 * Registered in settings.json as a PostToolUse Write|Edit async hook.
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');
const { spawn } = require('child_process');

const SMOKE_SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'hook-smoke.js');
const TIMEOUT_MS   = 20000;

async function readStdin() {
  let data = '';
  let timer;
  try {
    process.stdin.setEncoding('utf8');
    const readLoop = (async () => { for await (const chunk of process.stdin) data += chunk; })();
    await Promise.race([readLoop, new Promise((r) => { timer = setTimeout(r, 3000); })]);
  } catch {}
  clearTimeout(timer);
  return data || '{}';
}

function shouldTrigger(filePath) {
  if (!filePath) return false;
  // Matches masonry/src/hooks/*.js (any OS path separator)
  if (/masonry[/\\]src[/\\]hooks[/\\][^/\\]+\.js$/.test(filePath)) return true;
  // Matches any settings.json
  if (/settings\.json$/.test(filePath)) return true;
  return false;
}

async function runSmokeTest() {
  return new Promise((resolve) => {
    let output = '';
    let child;

    try {
      child = spawn('node', [SMOKE_SCRIPT], {
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    } catch (err) {
      process.stderr.write(`[hook-watch] failed to spawn smoke test: ${err.message}\n`);
      return resolve({ exitCode: 1, output: '' });
    }

    child.stdout.on('data', d => (output += d));
    child.stderr.on('data', d => (output += d));

    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch {}
      resolve({ exitCode: -1, output, timedOut: true });
    }, TIMEOUT_MS);

    child.on('close', code => {
      clearTimeout(timer);
      resolve({ exitCode: code, output, timedOut: false });
    });
    child.on('error', err => {
      clearTimeout(timer);
      resolve({ exitCode: 1, output, timedOut: false });
    });
  });
}

async function main() {
  const raw = await readStdin();
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const filePath = payload?.tool_input?.file_path || '';

  if (!shouldTrigger(filePath)) {
    process.exit(0);
  }

  const { exitCode, output, timedOut } = await runSmokeTest();

  if (timedOut) {
    process.stderr.write('[hook-watch] smoke test timed out after 20s\n');
    process.exit(0);
  }

  // exitCode 1 = failures detected; 0 = clean
  if (exitCode === 1) {
    process.stderr.write('\n\u26a0\ufe0f  HOOK SMOKE TEST \u2014 FAILURES DETECTED \u26a0\ufe0f\n');
  }

  if (output) {
    process.stderr.write(output);
  }

  // Always exit 0 — never block the write
  process.exit(0);
}

main().catch(() => process.exit(0));

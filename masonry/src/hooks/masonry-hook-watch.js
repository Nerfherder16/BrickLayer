#!/usr/bin/env node
/**
 * masonry-hook-watch.js — PostToolUse async hook.
 *
 * When a Write or Edit touches a file inside masonry/src/hooks/ OR
 * masonry/src/engine/ OR any settings.json file:
 *   1. If it's a NEW file creation (.js/.py), emit a language-choice reminder.
 *   2. If it's a .js hook/engine file, run ESLint and write a .lint-errors
 *      sidecar if lint fails.
 *   3. Run hook-smoke.js and pipe its report to stderr.
 *
 * This hook is async: true — it never blocks the write itself.
 * Timeout: 20s (smoke test is expected to finish in < 15s).
 *
 * Registered in settings.json as a PostToolUse Write|Edit async hook.
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

const HOOKS_DIR  = path.resolve(__dirname);                              // masonry/src/hooks/
const ENGINE_DIR = path.resolve(__dirname, '..', 'engine');              // masonry/src/engine/
const SMOKE_SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'hook-smoke.js');
const TIMEOUT_MS   = 20000;

// ESLint binary — prefer local project install, fall back to global
const ESLINT_BIN = path.resolve(__dirname, '..', '..', '..', 'node_modules', '.bin', 'eslint');
const LINT_CMD_TEMPLATE = `node "${ESLINT_BIN}" --no-eslintrc --rule "no-undef: warn" -- `;

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
  // Matches masonry/src/engine/* files
  if (/masonry[/\\]src[/\\]engine[/\\]/.test(filePath)) return true;
  // Matches any settings.json
  if (/settings\.json$/.test(filePath)) return true;
  return false;
}

function emitLanguageChoiceReminder(filename) {
  process.stderr.write(
    `[hook-watch] NEW HOOK/ENGINE FILE DETECTED: ${filename}\n` +
    `─────────────────────────────────────────────────────\n` +
    `Language choice guide: docs/hook-creation-guide.md\n` +
    `Quick rule:\n` +
    `  Node.js  → hot path (fires every tool use), MCP tool integration, I/O-bound\n` +
    `  Python   → DSPy/ML, tmux agent spawn, campaign state mutation\n` +
    `─────────────────────────────────────────────────────\n`
  );
}

function runLint(resolvedFile) {
  // Only lint .js files
  if (!resolvedFile.endsWith('.js')) return;

  // Guard: skip .lint-errors sidecar files to prevent infinite loops
  if (resolvedFile.endsWith('.lint-errors')) return;

  // Check file still exists (race condition guard)
  if (!fs.existsSync(resolvedFile)) return;

  try {
    const lintCmd = LINT_CMD_TEMPLATE + resolvedFile;
    execSync(lintCmd, { stdio: 'pipe' });
    process.stderr.write(`[hook-watch] lint OK: ${path.basename(resolvedFile)}\n`);
  } catch (lintErr) {
    // ESLint not found
    if (lintErr.code === 'ENOENT' || (lintErr.message && lintErr.message.includes('not found'))) {
      process.stderr.write(`[hook-watch] eslint not found, skipping lint\n`);
      return;
    }
    // Lint failed — write sidecar
    const sidecarPath = resolvedFile + '.lint-errors';
    const report = (lintErr.stdout || '') + (lintErr.stderr || '');
    try {
      fs.writeFileSync(sidecarPath, report, 'utf8');
    } catch (_) { /* sidecar write failed, non-fatal */ }
    process.stderr.write(`[hook-watch] lint FAIL: ${path.basename(resolvedFile)} → ${sidecarPath}\n`);
  }
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

  const resolvedFile = path.resolve(filePath);
  const toolName = payload?.tool_name ?? payload?.tool ?? null;
  const isNewFile = toolName === 'Write';
  const isCodeFile = resolvedFile.endsWith('.js') || resolvedFile.endsWith('.py');

  // Language-choice reminder for new file creation only
  if (isNewFile && isCodeFile) {
    const isHookFile  = resolvedFile.startsWith(HOOKS_DIR);
    const isEngineFile = resolvedFile.startsWith(ENGINE_DIR);
    if (isHookFile || isEngineFile) {
      emitLanguageChoiceReminder(path.basename(resolvedFile));
    }
  }

  // ESLint for .js hook/engine files
  const isHookOrEngine =
    resolvedFile.startsWith(HOOKS_DIR) || resolvedFile.startsWith(ENGINE_DIR);
  if (isHookOrEngine) {
    runLint(resolvedFile);
  }

  // Smoke test only for hook/.js and settings.json (original trigger scope)
  const runSmoke =
    /masonry[/\\]src[/\\]hooks[/\\][^/\\]+\.js$/.test(filePath) ||
    /settings\.json$/.test(filePath);

  if (!runSmoke) {
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

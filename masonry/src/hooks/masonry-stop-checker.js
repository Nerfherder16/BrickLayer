#!/usr/bin/env node
/**
 * masonry-stop-checker.js
 * Stop hook — runs all 4 sync guard checks in sequence using a single process.
 * Consolidates masonry-stop-guard, masonry-build-guard, masonry-context-monitor,
 * and masonry-ui-compose-guard into one settings.json entry so Claude Code only
 * shows ONE feedback line instead of four.
 *
 * Protocol:
 *   - Reads stdin once, pipes the same buffer to each guard
 *   - Forwards all stderr from guards directly to our stderr
 *   - If any guard exits 2, immediately exits 2 (Stop is blocked)
 *   - All guards exit 0 → exits 0
 */

'use strict';

const { spawn } = require('child_process');
const path = require('path');

const HOOKS_DIR = __dirname;

// Run in this order — stop-guard first (may auto-commit), then build/ui guards,
// context-monitor last (advisory, never hard-blocks on its own).
const GUARDS = [
  path.join(HOOKS_DIR, 'masonry-stop-guard.js'),
  path.join(HOOKS_DIR, 'masonry-build-guard.js'),
  path.join(HOOKS_DIR, 'masonry-ui-compose-guard.js'),
  path.join(HOOKS_DIR, 'masonry-context-monitor.js'),
];

async function readStdin() {
  let data = '';
  let timer;
  try {
    process.stdin.setEncoding('utf8');
    const readLoop = (async () => { for await (const chunk of process.stdin) data += chunk; })();
    await Promise.race([readLoop, new Promise((r) => { timer = setTimeout(r, 3000); })]);
  } catch {}
  clearTimeout(timer);
  return data;
}

function runGuard(scriptPath, stdinBuf) {
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn('node', [scriptPath], {
        stdio: ['pipe', 'inherit', 'inherit'],
      });
      child.stdin.write(stdinBuf);
      child.stdin.end();
      child.on('close', (code) => resolve(code ?? 0));
      child.on('error', () => resolve(0));
    } catch {
      resolve(0);
    }
  });
}

async function main() {
  const stdinData = await readStdin();
  const stdinBuf = Buffer.from(stdinData, 'utf8');

  for (const guard of GUARDS) {
    const code = await runGuard(guard, stdinBuf);
    if (code === 2) {
      process.exit(2);
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

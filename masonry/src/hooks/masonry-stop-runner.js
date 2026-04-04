#!/usr/bin/env node
/**
 * Stop hook runner — consolidates all background-only Stop hooks into one process.
 *
 * This is async: true in settings.json. It runs all background tasks in parallel
 * so Claude Code emits a single "Async hook Stop completed" instead of one per hook.
 *
 * Blocking guards (stop-guard, build-guard, context-monitor) are registered as
 * separate sync hooks so their exit code 2 can actually block the Stop event.
 */

'use strict';
const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const HOOKS_DIR = __dirname;

// All background hooks — none of these block (exit 0 always).
// Each entry: [command, [args], timeoutMs]
const BACKGROUND_HOOKS = [
  ['node', [`${HOME}/.claude/recall-hooks/session-save.js`], 10000],
  ['node', [`${HOME}/.claude/recall-hooks/recall-session-summary.js`], 10000],
  ['node', [path.join(HOOKS_DIR, 'masonry-session-summary.js')], 8000],
  ['node', [path.join(HOOKS_DIR, 'masonry-handoff.js')], 8000],
  ['node', [path.join(HOOKS_DIR, 'masonry-score-trigger.js')], 5000],
  ['node', [path.join(HOOKS_DIR, 'masonry-pagerank-trigger.js')], 5000],
  ['node', [path.join(HOOKS_DIR, 'masonry-system-status.js')], 8000],
  ['node', [path.join(HOOKS_DIR, 'masonry-training-export.js')], 65000],
  ['node', [path.join(HOOKS_DIR, 'masonry-ema-collector.js')], 5000],
  ['bash', [`${HOME}/.tmux/plugins/tmux-agent-status/hooks/better-hook.sh`, 'Stop'], 3000],
];

async function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => (data += c));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function runHook(cmd, args, stdinBuf, timeoutMs) {
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(cmd, args, { stdio: ['pipe', 'ignore', 'ignore'] });
      child.stdin.write(stdinBuf);
      child.stdin.end();
      child.on('close', resolve);
      child.on('error', resolve);
    } catch {
      resolve();
      return;
    }
    setTimeout(() => {
      try { child.kill(); } catch {}
      resolve();
    }, timeoutMs);
  });
}

async function main() {
  const stdinData = await readStdin();
  const stdinBuf = Buffer.from(stdinData, 'utf8');

  await Promise.all(
    BACKGROUND_HOOKS.map(([cmd, args, timeout]) => runHook(cmd, args, stdinBuf, timeout))
  );
}

main().catch(() => {});

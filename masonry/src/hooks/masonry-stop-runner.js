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
  ['node', [`${HOME}/.claude/recall-hooks/session-save.js`], 2500],
  ['node', [`${HOME}/.claude/recall-hooks/recall-session-summary.js`], 3000],
  ['node', [path.join(HOOKS_DIR, 'masonry-session-summary.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-handoff.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-score-trigger.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-pagerank-trigger.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-system-status.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-training-export.js')], 2000],
  ['node', [path.join(HOOKS_DIR, 'masonry-ema-collector.js')], 2000],
  ['bash', [`${HOME}/.tmux/plugins/tmux-agent-status/hooks/better-hook.sh`, 'Stop'], 3000],
  ['node', [path.join(HOOKS_DIR, 'masonry-token-logger.js')], 5000],
];

async function readStdin() {
  let data = '';
  let timer;
  try {
    process.stdin.setEncoding('utf8');
    const readLoop = (async () => { for await (const chunk of process.stdin) data += chunk; })();
    await Promise.race([readLoop, new Promise((r) => { timer = setTimeout(r, 2000); })]);
  } catch {}
  clearTimeout(timer);
  return data;
}

function runHook(cmd, args, stdinBuf, timeoutMs) {
  return new Promise((resolve) => {
    let child;
    let timer;
    try {
      child = spawn(cmd, args, { stdio: ['pipe', 'ignore', 'ignore'] });
      child.stdin.write(stdinBuf);
      child.stdin.end();
      child.on('close', () => { clearTimeout(timer); resolve(); });
      child.on('error', () => { clearTimeout(timer); resolve(); });
    } catch {
      resolve();
      return;
    }
    timer = setTimeout(() => {
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

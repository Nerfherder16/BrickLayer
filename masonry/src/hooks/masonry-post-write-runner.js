#!/usr/bin/env node
/**
 * masonry-post-write-runner.js
 * PostToolUse:Write|Edit async runner — consolidates all background PostToolUse
 * hooks into one process so Claude Code emits a single "Async hook PostToolUse
 * completed" instead of one per hook.
 *
 * Blocking hooks (tdd-enforcer, file-size-guard) are registered as separate
 * sync hooks so their exit code 2 can actually block the write.
 */

'use strict';
const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const HOOKS_DIR = __dirname;
const TIMER = `${HOME}/.claude/monitors/hook-timer.sh`;

// All background hooks — none of these block (exit 0 always).
// Each entry: [label, command, [args], timeoutMs]
const BACKGROUND_HOOKS = [
  ['observe-edit',         'node', [`${HOME}/.claude/recall-hooks/observe-edit.js`],                              10000],
  ['masonry-observe',      'node', [path.join(HOOKS_DIR, 'masonry-observe.js')],                                   5000],
  ['masonry-rust-check',   'node', [path.join(HOOKS_DIR, 'masonry-rust-check.js')],                                5000],
  ['masonry-vitest',       'node', [path.join(HOOKS_DIR, 'masonry-vitest.js')],                                    5000],
  ['masonry-style-checker','node', [path.join(HOOKS_DIR, 'masonry-style-checker.js')],                            30000],
  ['masonry-agent-onboard','node', [path.join(HOOKS_DIR, 'masonry-agent-onboard.js')],                            10000],
  ['masonry-build-patterns','node',[path.join(HOOKS_DIR, 'masonry-build-patterns.js')],                            8000],
  ['masonry-pulse',        'node', [path.join(HOOKS_DIR, 'masonry-pulse.js')],                                     5000],
  ['masonry-checkpoint',   'node', [path.join(HOOKS_DIR, 'masonry-checkpoint.js')],                                3000],
  ['masonry-jcodemunch-index', 'node', [path.join(HOOKS_DIR, 'masonry-jcodemunch-index.js')],                    15000],
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

function runHook(label, cmd, args, stdinBuf, timeoutMs) {
  return new Promise((resolve) => {
    let child;
    let timer;
    try {
      // Wrap with hook-timer.sh when available for consistent timing logs
      const finalCmd = TIMER;
      const finalArgs = [label, cmd, ...args];
      child = spawn(finalCmd, finalArgs, { stdio: ['pipe', 'ignore', 'ignore'] });
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
    BACKGROUND_HOOKS.map(([label, cmd, args, timeout]) =>
      runHook(label, cmd, args, stdinBuf, timeout)
    )
  );
}

main().catch(() => {});

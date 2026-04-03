#!/usr/bin/env node
/**
 * masonry-vitest.js
 * PostToolUse hook — async vitest run on codevvOS frontend file edits.
 *
 * Fires when a .ts/.tsx/.js/.jsx file inside codevvOS/frontend/src/ is
 * written or edited. Runs `npx vitest run --reporter=dot` as a background
 * process from the frontend root. Never blocks (always exits 0).
 *
 * Skips: test files themselves (vitest reruns on save are redundant noise),
 *        node_modules, dist, build directories.
 */

'use strict';
const { spawn } = require('child_process');
const path = require('path');

const FRONTEND_MARKER = path.join('codevvOS', 'frontend', 'src');
const SKIP_PATTERNS = ['/node_modules/', '/dist/', '/build/', '/__tests__/', '.test.', '.spec.'];
const WATCH_EXTS = ['.ts', '.tsx', '.js', '.jsx'];

function runBackground(cmd, args, cwd) {
  try {
    const proc = spawn(cmd, args, {
      detached: true,
      windowsHide: true,
      stdio: 'ignore',
      cwd,
      shell: false,
    });
    proc.unref();
  } catch (_) {}
}

function findFrontendRoot(filePath) {
  const idx = filePath.indexOf(FRONTEND_MARKER);
  if (idx === -1) return null;
  // Return the directory two levels up from src/ (the frontend root)
  return filePath.slice(0, idx + FRONTEND_MARKER.length - 4); // chop /src
}

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    if (!['Write', 'Edit'].includes(tool_name)) process.exit(0);

    const filePath = tool_input.file_path || tool_input.path || '';
    const ext = path.extname(filePath);

    if (!WATCH_EXTS.includes(ext)) process.exit(0);
    if (SKIP_PATTERNS.some(p => filePath.includes(p))) process.exit(0);
    if (!filePath.includes(FRONTEND_MARKER)) process.exit(0);

    const frontendRoot = findFrontendRoot(filePath);
    if (!frontendRoot) process.exit(0);

    // Run vitest in background
    runBackground('npx', ['vitest', 'run', '--reporter=dot', '--silent'], frontendRoot);
  } catch (_) {}
  process.exit(0);
});

#!/usr/bin/env node
/**
 * masonry-rust-check.js
 * PostToolUse hook — async cargo check on Rust file edits.
 *
 * Fires when a .rs file is written or edited. Runs `cargo check` in the
 * nearest project root (directory containing Cargo.toml) as a background
 * process. Never blocks (always exits 0).
 */

'use strict';
const { spawn } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');

function findCargoRoot(filePath) {
  let dir = path.dirname(filePath);
  for (let i = 0; i < 8; i++) {
    if (existsSync(path.join(dir, 'Cargo.toml'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

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

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    if (!['Write', 'Edit'].includes(tool_name)) process.exit(0);

    const filePath = tool_input.file_path || tool_input.path || '';
    if (!filePath.endsWith('.rs')) process.exit(0);

    const cargoRoot = findCargoRoot(filePath);
    if (!cargoRoot) process.exit(0);

    // Run cargo check in background — output goes nowhere (async lint)
    const cargoPath = process.env.HOME
      ? path.join(process.env.HOME, '.cargo', 'bin', 'cargo')
      : 'cargo';
    const cargo = existsSync(cargoPath) ? cargoPath : 'cargo';

    runBackground(cargo, ['check', '--message-format=short'], cargoRoot);
  } catch (_) {}
  process.exit(0);
});

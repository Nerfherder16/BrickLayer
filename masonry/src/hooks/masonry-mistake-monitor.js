#!/usr/bin/env node
/**
 * masonry-mistake-monitor.js
 * PostToolUse:Bash async hook — logs tool failures to .mas/mistakes.jsonl.
 *
 * Fires after every bash command. Examines the tool response for error patterns
 * and logs structured entries. After every 5 new entries, triggers
 * safeguard_forge.py to auto-generate safeguard rules.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const MAX_STDIN = 512 * 1024;

// Patterns in tool_response that indicate an unambiguous failure worth logging
const RESPONSE_ERROR_PATTERN = /\bBLOCKED\b|\bDENIED\b|hook error|\bcommand not found\b|Exit code [1-9]/i;

// Patterns in the tool_response that indicate a retry-worthy OS-level failure
const COMMAND_RETRY_PATTERN = /Permission denied|ENOENT|command not found/;

// Path to the count-tracking temp file
const COUNT_FILE = '/tmp/masonry-mistake-count.json';

// ── helpers ───────────────────────────────────────────────────────────────────

/**
 * Walk up from dir looking for a .mas/ directory.
 * Returns the project root (parent of .mas/) or null.
 */
function findProjectRoot(startDir) {
  let dir = path.resolve(startDir || process.cwd());
  for (let i = 0; i < 20; i++) {
    if (fs.existsSync(path.join(dir, '.mas'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

/**
 * Append a record to .mas/mistakes.jsonl — non-fatal.
 * Returns the total line count of the file after appending.
 */
function appendMistake(projectRoot, record) {
  try {
    const masDir = path.join(projectRoot, '.mas');
    fs.mkdirSync(masDir, { recursive: true });
    const filePath = path.join(masDir, 'mistakes.jsonl');
    const line = JSON.stringify(record);
    fs.appendFileSync(filePath, line + '\n', 'utf8');
    // Count lines to determine if we should trigger forge
    const content = fs.readFileSync(filePath, 'utf8');
    return content.split('\n').filter(Boolean).length;
  } catch (_) {
    return 0;
  }
}

/**
 * Read the last known count from the temp file.
 */
function readLastCount() {
  try {
    const raw = fs.readFileSync(COUNT_FILE, 'utf8');
    const data = JSON.parse(raw);
    return typeof data.count === 'number' ? data.count : 0;
  } catch (_) {
    return 0;
  }
}

/**
 * Write the current count to the temp file — non-fatal.
 */
function writeCount(count) {
  try {
    fs.writeFileSync(COUNT_FILE, JSON.stringify({ count, updated: new Date().toISOString() }), 'utf8');
  } catch (_) {}
}

/**
 * Fire safeguard_forge.py in a detached background process.
 * Non-blocking — we do not wait for it.
 */
function triggerSafeguardForge(projectRoot) {
  try {
    const scriptPath = path.join(projectRoot, 'masonry', 'scripts', 'safeguard_forge.py');
    if (!fs.existsSync(scriptPath)) return;
    const child = spawn('python3', [scriptPath, path.join(projectRoot, '.mas', 'mistakes.jsonl')], {
      detached: true,
      stdio: 'ignore',
      cwd: projectRoot,
    });
    child.unref();
  } catch (_) {}
}

// ── main ──────────────────────────────────────────────────────────────────────

async function main() {
  let raw = '';
  try {
    for await (const chunk of process.stdin) {
      raw += chunk;
      if (raw.length > MAX_STDIN) break;
    }
  } catch (_) {
    process.exit(0);
  }

  let input = {};
  try {
    input = JSON.parse(raw);
  } catch (_) {
    process.exit(0);
  }

  const { tool_name, tool_input = {}, tool_response = '', cwd = process.cwd() } = input;

  // Only watch Bash tool calls
  if (tool_name !== 'Bash') process.exit(0);

  const command = (tool_input.command || tool_input.cmd || tool_input.input || '').trim();
  const responseText = typeof tool_response === 'string'
    ? tool_response
    : JSON.stringify(tool_response);

  const responseMatches = RESPONSE_ERROR_PATTERN.test(responseText);
  const commandMatches = COMMAND_RETRY_PATTERN.test(responseText);

  if (!responseMatches && !commandMatches) process.exit(0);

  const projectRoot = findProjectRoot(cwd);
  if (!projectRoot) process.exit(0);

  const record = {
    timestamp: new Date().toISOString(),
    type: 'tool_failure',
    command: command.slice(0, 200),
    error_snippet: responseText.slice(0, 150),
    cwd: cwd || '',
    source: 'masonry-mistake-monitor',
  };

  const totalCount = appendMistake(projectRoot, record);

  // Trigger safeguard forge every 5 new entries
  const lastCount = readLastCount();
  if (totalCount - lastCount >= 5) {
    writeCount(totalCount);
    triggerSafeguardForge(projectRoot);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

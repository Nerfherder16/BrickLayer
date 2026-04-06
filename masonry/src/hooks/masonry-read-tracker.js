#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Read file tracker.
 *
 * Fires on every PostToolUse event where tool_name === "Read".
 * Logs the file path and estimated byte size to ~/.mas/read-log.jsonl.
 * Caps the file at 2000 lines (trims oldest).
 *
 * Register in settings.json as an async PostToolUse hook with matcher "Read".
 */

'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { getSessionId, readStdin } = require('./session/stop-utils');

const LOG_PATH = path.join(os.homedir(), '.mas', 'read-log.jsonl');
const MAX_LINES = 2000;

function ensureDir(p) {
  try { fs.mkdirSync(path.dirname(p), { recursive: true }); } catch (_) {}
}

function capFile(filePath, maxLines) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n').filter((l) => l.trim());
    if (lines.length <= maxLines) return;
    const trimmed = lines.slice(lines.length - maxLines).join('\n') + '\n';
    fs.writeFileSync(filePath, trimmed, 'utf8');
  } catch (_) {}
}

/**
 * Estimate byte size from the tool result payload.
 * tool_result / output may be a string (file content) or an object.
 */
function estimateBytes(input) {
  const payload = input.tool_result || input.output || null;
  if (payload == null) return null;
  if (typeof payload === 'string') return Buffer.byteLength(payload, 'utf8');
  try { return Buffer.byteLength(JSON.stringify(payload), 'utf8'); } catch { return null; }
}

async function main() {
  const raw = await readStdin();
  if (!raw.trim()) process.exit(0);

  let input;
  try { input = JSON.parse(raw); } catch { process.exit(0); }

  // Only handle Read tool events
  const toolName = input.tool_name || input.toolName || '';
  if (toolName !== 'Read') process.exit(0);

  const filePath = (input.tool_input || {}).file_path || null;
  if (!filePath) process.exit(0);

  const sessionId = getSessionId(input);
  const bytes = estimateBytes(input);
  const cwd = input.cwd || process.cwd();

  ensureDir(LOG_PATH);

  const record = {
    ts: new Date().toISOString(),
    session_id: sessionId,
    file: filePath,
    bytes: bytes,
    cwd,
  };

  try {
    fs.appendFileSync(LOG_PATH, JSON.stringify(record) + '\n', 'utf8');
  } catch (_) {}

  capFile(LOG_PATH, MAX_LINES);

  process.exit(0);
}

main().catch(() => process.exit(0));

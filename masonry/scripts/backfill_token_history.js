#!/usr/bin/env node
/**
 * backfill_token_history.js
 *
 * Globs all session transcripts from ~/.claude/projects/**\/*.jsonl, parses
 * token usage + tool_footprint using the same logic as masonry-token-logger.js,
 * and appends new records to ~/.mas/token-log.jsonl (skipping sessions already
 * present by session_id). Caps the log at 500 lines.
 *
 * Usage:
 *   node masonry/scripts/backfill_token_history.js
 */

'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const LOG_PATH = path.join(os.homedir(), '.mas', 'token-log.jsonl');
const PROJECTS_DIR = process.argv[2] || path.join(os.homedir(), '.claude', 'projects');
const MAX_LINES = 5000;

// ---------------------------------------------------------------------------
// Transcript parsing (mirrors masonry-token-logger.js)
// ---------------------------------------------------------------------------

/**
 * Parse a single transcript JSONL file. Returns null if the file has 0 turns.
 * @param {string} transcriptPath
 * @param {string} sessionId
 * @param {number} fileMtime  — epoch ms, used as fallback ts
 * @returns {{ ts: string, session_id: string, cwd: string, turns: number,
 *             input_tokens: number, output_tokens: number,
 *             cache_read_tokens: number, cache_creation_tokens: number,
 *             effective_tokens: number, tool_footprint: Record<string,number> }|null}
 */
function parseTranscript(transcriptPath, sessionId, fileMtime) {
  const totals = {
    input_tokens: 0,
    output_tokens: 0,
    cache_read_tokens: 0,
    cache_creation_tokens: 0,
    turns: 0,
    tool_footprint: {},
  };
  let cwd = '';
  let firstTs = null;

  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('{')) continue;
      let obj;
      try { obj = JSON.parse(trimmed); } catch { continue; }

      // Capture cwd from any top-level field (Stop event format)
      if (!cwd && typeof obj.cwd === 'string') cwd = obj.cwd;

      const msg = obj.message || obj;
      const usage = msg.usage;
      if (!usage) continue;

      const inputTok = usage.input_tokens || 0;
      const cacheReadTok = usage.cache_read_input_tokens || 0;
      const cacheWriteTok = usage.cache_creation_input_tokens || 0;
      totals.input_tokens += inputTok;
      if (usage.output_tokens != null) totals.output_tokens += usage.output_tokens;
      totals.cache_read_tokens += cacheReadTok;
      totals.cache_creation_tokens += cacheWriteTok;
      totals.turns++;

      // Record first turn timestamp if available
      if (firstTs === null && typeof obj.ts === 'string') firstTs = obj.ts;

      // Collect tool names called in this turn
      const contentArr = Array.isArray(msg.content) ? msg.content : [];
      const toolNames = new Set();
      for (const item of contentArr) {
        if (item && item.type === 'tool_use' && typeof item.name === 'string') {
          toolNames.add(item.name);
        }
      }
      for (const name of toolNames) {
        if (!totals.tool_footprint[name]) totals.tool_footprint[name] = { input: 0, cache_read: 0, cache_write: 0 };
        totals.tool_footprint[name].input      += inputTok;
        totals.tool_footprint[name].cache_read += cacheReadTok;
        totals.tool_footprint[name].cache_write += cacheWriteTok;
      }
    }
  } catch (_) {
    return null;
  }

  if (totals.turns === 0) return null;

  // Use first-turn timestamp if found, otherwise file mtime
  const ts = firstTs || new Date(fileMtime).toISOString();

  return {
    ts,
    session_id: sessionId,
    cwd: cwd || path.dirname(transcriptPath),
    turns: totals.turns,
    input_tokens: totals.input_tokens,
    output_tokens: totals.output_tokens,
    cache_read_tokens: totals.cache_read_tokens,
    cache_creation_tokens: totals.cache_creation_tokens,
    effective_tokens: totals.input_tokens + Math.round(totals.cache_read_tokens * 0.1),
    tool_footprint: totals.tool_footprint,
  };
}

// ---------------------------------------------------------------------------
// Glob all transcript files
// ---------------------------------------------------------------------------

/**
 * Recursively find all *.jsonl files under a directory.
 * @param {string} dir
 * @returns {string[]}
 */
function globJsonl(dir) {
  const results = [];
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return results; }
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...globJsonl(full));
    } else if (entry.isFile() && entry.name.endsWith('.jsonl')) {
      results.push(full);
    }
  }
  return results;
}

// ---------------------------------------------------------------------------
// Load existing log, deduplicate, append, cap
// ---------------------------------------------------------------------------

function loadExistingLog() {
  const existing = new Map(); // session_id → record
  try {
    const content = fs.readFileSync(LOG_PATH, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('{')) continue;
      try {
        const rec = JSON.parse(trimmed);
        if (rec.session_id) existing.set(rec.session_id, rec);
      } catch { /* skip */ }
    }
  } catch { /* file may not exist */ }
  return existing;
}

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

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  // 1. Find all transcript files
  const allFiles = globJsonl(PROJECTS_DIR);

  // 2. Load existing log to know which session_ids are already recorded
  const existing = loadExistingLog();

  // 3. Parse each transcript, skip duplicates
  const newRecords = [];
  let skippedDuplicates = 0;
  let skippedEmpty = 0;

  for (const filePath of allFiles) {
    // Extract session_id from filename: {uuid}.jsonl
    const basename = path.basename(filePath, '.jsonl');
    // Exclude non-session files (e.g. token-log itself if it ever ends up here)
    if (!basename.match(/^[0-9a-f-]{8,}$/i) && !basename.match(/^[0-9a-f]{32,}$/i)) {
      // Accept any UUID-ish name (hex + dashes, 8+ chars)
      if (!basename.match(/^[0-9a-f-]{8,}$/i)) {
        skippedEmpty++;
        continue;
      }
    }

    // Skip if already in log
    if (existing.has(basename)) {
      skippedDuplicates++;
      continue;
    }

    let mtime = Date.now();
    try { mtime = fs.statSync(filePath).mtimeMs; } catch { /* use now */ }

    const record = parseTranscript(filePath, basename, mtime);
    if (!record) {
      skippedEmpty++;
      continue;
    }

    newRecords.push(record);
  }

  if (newRecords.length === 0) {
    console.log(`Backfilled 0 sessions, skipped ${skippedDuplicates} duplicates`);
    return;
  }

  // 4. Sort new records by ts ascending
  newRecords.sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0));

  // 5. Append to log
  ensureDir(LOG_PATH);
  const lines = newRecords.map((r) => JSON.stringify(r)).join('\n') + '\n';
  try {
    fs.appendFileSync(LOG_PATH, lines, 'utf8');
  } catch (err) {
    console.error('Failed to write token log:', err.message);
    process.exit(1);
  }

  // 6. Cap at MAX_LINES
  capFile(LOG_PATH, MAX_LINES);

  console.log(`Backfilled ${newRecords.length} sessions, skipped ${skippedDuplicates} duplicates`);
}

main();

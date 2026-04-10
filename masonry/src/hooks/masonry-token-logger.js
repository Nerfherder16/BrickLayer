#!/usr/bin/env node
/**
 * Stop hook (Masonry): Token usage logger.
 *
 * Reads the Stop event from stdin to get transcript_path, then parses the
 * session JSONL to sum up input_tokens, output_tokens, cache_read_input_tokens,
 * and cache_creation_input_tokens across all assistant turns.
 *
 * Appends one record per session to ~/.mas/token-log.jsonl, capped at 500 lines.
 * Register as an async Stop hook — never blocks.
 */

'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const LOG_PATH = path.join(os.homedir(), '.mas', 'token-log.jsonl');
const MAX_LINES = 500;

function ensureDir(p) {
  try { fs.mkdirSync(path.dirname(p), { recursive: true }); } catch (_) {}
}

async function readStdin(timeoutMs = 3000) {
  let data = '';
  let timer;
  try {
    process.stdin.setEncoding('utf8');
    const readLoop = (async () => { for await (const chunk of process.stdin) data += chunk; })();
    await Promise.race([readLoop, new Promise((r) => { timer = setTimeout(r, timeoutMs); })]);
  } catch (_) {}
  clearTimeout(timer);
  return data;
}

/**
 * Parse the session transcript JSONL and sum token usage across all turns.
 * Claude Code stores one JSON object per line; assistant messages have a
 * `usage` field with input_tokens, output_tokens, cache_read_input_tokens,
 * cache_creation_input_tokens, plus a `content` array that may contain
 * tool_use items indicating which tools were called in that turn.
 *
 * tool_footprint: maps tool name → total input_tokens attributed to turns
 * that called that tool. A turn calling multiple tools attributes its full
 * input_token cost to EACH tool (not split) — this gives a "turns involving
 * this tool cost X tokens total" signal.
 */
function readTranscriptTokens(transcriptPath) {
  const totals = {
    input_tokens: 0,
    output_tokens: 0,
    cache_read_tokens: 0,
    cache_creation_tokens: 0,
    turns: 0,
    tool_call_count: 0, // total tool invocations (not deduplicated by name)
    tool_footprint: {}, // {tool: {input, cache_read, cache_write}}
  };

  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('{')) continue;
      let obj;
      try { obj = JSON.parse(trimmed); } catch { continue; }

      // Assistant messages have usage data
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

      // Collect tool names called in this turn
      const contentArr = Array.isArray(msg.content) ? msg.content : [];
      const toolNames = new Set();
      for (const item of contentArr) {
        if (item && item.type === 'tool_use' && typeof item.name === 'string') {
          toolNames.add(item.name);
          totals.tool_call_count++; // count every invocation, not just distinct names
        }
      }
      // Attribute full turn cost to each tool called (not split — context pressure signal)
      for (const name of toolNames) {
        if (!totals.tool_footprint[name]) totals.tool_footprint[name] = { input: 0, cache_read: 0, cache_write: 0 };
        totals.tool_footprint[name].input += inputTok;
        totals.tool_footprint[name].cache_read += cacheReadTok;
        totals.tool_footprint[name].cache_write += cacheWriteTok;
      }
    }
  } catch (_) {}

  return totals;
}

/**
 * Write a session record, keeping exactly one entry per session_id.
 * Replaces any previous entry for this session (earlier Stop events have
 * lower turn counts). Caps the log at maxLines unique sessions.
 *
 * This prevents the log from filling up with 60-100 duplicate entries for
 * the same long session, which would crowd out history from other days.
 */
function writeDeduplicatedRecord(filePath, record, maxLines) {
  let lines = [];
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    lines = content.split('\n').filter((l) => l.trim());
  } catch (_) {}

  // Remove all previous entries for this session_id
  const filtered = lines.filter((l) => {
    try { return JSON.parse(l).session_id !== record.session_id; } catch { return true; }
  });

  // Append the latest snapshot for this session
  filtered.push(JSON.stringify(record));

  // Cap to maxLines unique sessions (keep most recent)
  const capped = filtered.slice(-maxLines);

  try {
    fs.writeFileSync(filePath, capped.join('\n') + '\n', 'utf8');
  } catch (_) {}
}

async function main() {
  const raw = await readStdin();
  if (!raw.trim()) process.exit(0);

  let event;
  try { event = JSON.parse(raw.trim()); } catch { process.exit(0); }

  const sessionId = event.session_id || `session-${Date.now()}`;
  const transcriptPath = event.transcript_path;
  const cwd = event.cwd || process.cwd();

  if (!transcriptPath) process.exit(0);

  const totals = readTranscriptTokens(transcriptPath);

  // Skip if no turns found (empty session)
  if (totals.turns === 0) process.exit(0);

  ensureDir(LOG_PATH);

  const record = {
    ts: new Date().toISOString(),
    session_id: sessionId,
    cwd,
    turns: totals.turns,
    input_tokens: totals.input_tokens,
    output_tokens: totals.output_tokens,
    cache_read_tokens: totals.cache_read_tokens,
    cache_creation_tokens: totals.cache_creation_tokens,
    // Effective tokens = what you actually paid for (cache reads are ~10% cost)
    effective_tokens: totals.input_tokens + Math.round(totals.cache_read_tokens * 0.1),
    tool_call_count: totals.tool_call_count,
    tool_footprint: totals.tool_footprint,
  };

  writeDeduplicatedRecord(LOG_PATH, record, MAX_LINES);
  process.exit(0);
}

main().catch(() => process.exit(0));

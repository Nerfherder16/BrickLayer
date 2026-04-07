#!/usr/bin/env node
/**
 * PreToolUse hook (Masonry): Read deduplication guard.
 *
 * Blocks redundant Read calls for files already loaded in this session turn.
 * Tracks reads in /tmp per session; clears entry when a file is written/edited.
 * Suppresses the block when offset/limit differs (partial reads are OK).
 *
 * Register in settings.json as a PreToolUse hook with matcher "Read".
 */

'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const TTL_MS = 10 * 60 * 1000; // 10 minutes — clear on new prompt naturally via TTL
const CACHE_DIR = os.tmpdir();

function cacheFile(sessionId) {
  return path.join(CACHE_DIR, `masonry-read-cache-${sessionId || 'default'}.json`);
}

function loadCache(sessionId) {
  try {
    const raw = fs.readFileSync(cacheFile(sessionId), 'utf8');
    return JSON.parse(raw);
  } catch { return {}; }
}

function saveCache(sessionId, cache) {
  try { fs.writeFileSync(cacheFile(sessionId), JSON.stringify(cache), 'utf8'); } catch {}
}

function pruneExpired(cache) {
  const now = Date.now();
  return Object.fromEntries(
    Object.entries(cache).filter(([, v]) => now - v.ts < TTL_MS)
  );
}

async function main() {
  let raw = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) raw += chunk;
  } catch {}

  if (!raw.trim()) process.exit(0);

  let input;
  try { input = JSON.parse(raw); } catch { process.exit(0); }

  const toolName = input.tool_name || input.toolName || '';
  if (toolName !== 'Read') process.exit(0);

  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path;
  if (!filePath) process.exit(0);

  // Partial reads are fine — don't block if offset or limit specified
  if (toolInput.offset != null || toolInput.limit != null) process.exit(0);

  const sessionId = input.session_id || '';

  const cache = pruneExpired(loadCache(sessionId));
  const entry = cache[filePath];

  if (entry) {
    // Already read this session — block and suggest jCodeMunch
    const ageSec = Math.round((Date.now() - entry.ts) / 1000);
    const msg = [
      `[Masonry] Read dedup: ${path.basename(filePath)} was already read ${ageSec}s ago.`,
      `File content is still in context. Use jCodeMunch instead:`,
      `  get_symbol_source — fetch a specific function/class`,
      `  get_file_outline  — see structure without re-reading`,
      `  search_symbols    — find by name`,
    ].join('\n');
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'block',
        permissionDecisionReason: msg,
      },
    }));
    process.exit(2);
  }

  // First read — record it
  cache[filePath] = { ts: Date.now() };
  saveCache(sessionId, cache);
  process.exit(0);
}

main().catch(() => process.exit(0));

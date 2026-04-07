#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Invalidate read-dedup cache entry on Write/Edit.
 *
 * When a file is written or edited, remove it from the per-session read cache
 * so masonry-read-dedup.js allows re-reading it (e.g. read → edit → verify).
 *
 * Fires on PostToolUse Write|Edit, async, always exits 0.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

async function main() {
  let raw = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) raw += chunk;
  } catch {}

  if (!raw.trim()) process.exit(0);

  let input;
  try { input = JSON.parse(raw); } catch { process.exit(0); }

  const filePath = (input.tool_input || {}).file_path;
  const sessionId = input.session_id || '';
  if (!filePath || !sessionId) process.exit(0);

  const cacheFile = path.join(os.tmpdir(), `masonry-read-cache-${sessionId}.json`);
  try {
    const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    delete cache[filePath];
    fs.writeFileSync(cacheFile, JSON.stringify(cache), 'utf8');
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

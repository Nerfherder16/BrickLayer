'use strict';
/**
 * src/hooks/masonry-recall-check.js
 * Spawned as a detached background process by masonry-statusline.js.
 * Pings Recall /health and writes the result to the shared cache file.
 *
 * Args: node masonry-recall-check.js <recallHost> <apiKey>
 */

const fs   = require('fs');
const path = require('path');
const os   = require('os');

const CACHE_FILE = path.join(os.tmpdir(), 'masonry-recall-status.json');

async function main() {
  const host   = process.argv[2] || 'http://localhost:8200';
  const apiKey = process.argv[3] || '';

  let ok = false;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1500);
    const headers = apiKey ? { Authorization: `Bearer ${apiKey}` } : {};
    const res = await fetch(`${host}/health`, { signal: controller.signal, headers });
    clearTimeout(timer);
    ok = res.ok;
  } catch (_e) {
    ok = false;
  }

  try {
    fs.writeFileSync(CACHE_FILE, JSON.stringify({ ok, ts: Date.now() }), 'utf8');
  } catch (_e) {}
}

main().catch(() => {});

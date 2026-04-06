'use strict';
// src/hooks/masonry-guard-flush.js — UserPromptSubmit sync hook
// Flushes any pending 3-strike warnings from masonry-guard.js into the next
// prompt context via systemMessage. Clears the queue file after reading.

const fs = require('fs');
const path = require('path');
const os = require('os');

async function main() {
  let raw = '';
  try {
    for await (const chunk of process.stdin) raw += chunk;
  } catch (_) { process.exit(0); }

  let input = {};
  try { input = JSON.parse(raw); } catch (_) { process.exit(0); }

  const sessionId = input.session_id || 'unknown';
  const queueFile = path.join(os.tmpdir(), `masonry-guard-${sessionId}.ndjson`);

  if (!fs.existsSync(queueFile)) process.exit(0);

  let lines = [];
  try {
    lines = fs.readFileSync(queueFile, 'utf8')
      .split('\n')
      .filter(l => l.trim().length > 0);
    fs.unlinkSync(queueFile);
  } catch (_) { process.exit(0); }

  if (lines.length === 0) process.exit(0);

  const warnings = lines.map(l => {
    try {
      const w = JSON.parse(l);
      return `  • ${w.message || l}`;
    } catch (_) { return `  • ${l}`; }
  }).join('\n');

  const out = JSON.stringify({
    systemMessage: `[Masonry Guard] ${lines.length} 3-strike warning(s) from prior tool calls:\n${warnings}\nInvestigate root cause before retrying these patterns.`,
  });
  process.stdout.write(out + '\n');
  process.exit(0);
}

main().catch(() => process.exit(0));

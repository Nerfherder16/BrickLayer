#!/usr/bin/env node
/**
 * PreToolUse:Read hook — nudge toward jCodeMunch for source file reads.
 *
 * When a Read targets a source code file (.py, .js, .ts, .tsx, .jsx, .rs, .go)
 * without a specific offset/limit, emits a stderr hint suggesting get_symbol_source
 * or get_file_outline instead of reading the whole file.
 *
 * Non-blocking (exit 0 always). Pure nudge — never prevents the Read.
 */

'use strict';
const fs = require('fs');
const path = require('path');

const CODE_EXTS = new Set(['.py', '.js', '.ts', '.tsx', '.jsx', '.mjs', '.cjs', '.rs', '.go', '.kt']);

const NUDGE_THRESHOLD = 3 * 1024;  // 3 KB — below this, silent pass
const BLOCK_THRESHOLD = 20 * 1024; // 20 KB — above this, block with exit 2

// Files that are routinely read whole and should not be nudged
const EXEMPT_PATTERNS = [
  /\.(test|spec)\.(js|ts|jsx|tsx|py)$/i,
  /(__tests__|tests?)[/\\]/i,
  /vitest\.config/i,
  /package\.json$/i,
  /tsconfig/i,
  /pyproject\.toml$/i,
  /setup\.py$/i,
];

async function readStdin() {
  let data = '';
  let timer;
  try {
    process.stdin.setEncoding('utf8');
    const readLoop = (async () => { for await (const chunk of process.stdin) data += chunk; })();
    await Promise.race([readLoop, new Promise((r) => { timer = setTimeout(r, 2000); })]);
  } catch {}
  clearTimeout(timer);
  return data;
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch { process.exit(0); }

  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || '';

  if (!filePath) process.exit(0);

  const ext = path.extname(filePath).toLowerCase();
  if (!CODE_EXTS.has(ext)) process.exit(0);

  // If a specific offset+limit is given, they know what they want — don't nudge
  if (toolInput.offset != null || toolInput.limit != null) process.exit(0);

  // Exempt test files, configs, etc.
  if (EXEMPT_PATTERNS.some(re => re.test(filePath))) process.exit(0);

  let fileSize = 0;
  try { fileSize = fs.statSync(filePath).size; } catch { process.exit(0); }

  const basename = path.basename(filePath);
  if (fileSize < NUDGE_THRESHOLD) process.exit(0);

  const kb = (fileSize / 1024).toFixed(1);

  if (fileSize >= BLOCK_THRESHOLD) {
    process.stderr.write(
      `\n[jcodemunch] BLOCKED: ${basename} is ${kb}KB — reading whole file wastes tokens.\n` +
      `Follow the Iris Gate Ladder:\n` +
      `  1. Get file structure:   mcp__jcodemunch__get_file_outline  (file_path="${filePath}")\n` +
      `  2. Get a specific symbol: mcp__jcodemunch__get_symbol_source (symbol_name="<name>", file_path="${filePath}")\n` +
      `  3. Find by name:          mcp__jcodemunch__search_symbols    (query="<name>")\n` +
      `  4. Search code text:      mcp__jcodemunch__search_text       (query="<pattern>")\n` +
      `\nStart with step 1. Only escalate if the outline is insufficient.\n` +
      `If you genuinely need the entire file, add offset=0 to your Read call to bypass this check.\n`
    );
    process.exit(2);
  }

  // Medium (3–20KB): inject context reminder via stdout, not just stderr
  const hint = `[Iris Gate] ${basename} is ${kb}KB. ` +
    `Start with mcp__jcodemunch__get_file_outline before reading the full file. ` +
    `Only escalate to get_symbol_source if the outline is insufficient.`;
  process.stdout.write(JSON.stringify({ additionalContext: hint }));
  process.exit(0);
}

main().catch(() => process.exit(0));

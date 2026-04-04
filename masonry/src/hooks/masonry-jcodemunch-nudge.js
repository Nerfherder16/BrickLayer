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
const path = require('path');

const CODE_EXTS = new Set(['.py', '.js', '.ts', '.tsx', '.jsx', '.mjs', '.cjs', '.rs', '.go', '.kt']);

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

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => (data += c));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
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

  const basename = path.basename(filePath);
  process.stderr.write(
    `[jcodemunch] Reading full file: ${basename}\n` +
    `  → If you need a specific symbol: mcp__jcodemunch__get_symbol_source\n` +
    `  → File structure only:           mcp__jcodemunch__get_file_outline\n` +
    `  → Find by name:                  mcp__jcodemunch__search_symbols\n`
  );

  process.exit(0);
}

main().catch(() => process.exit(0));

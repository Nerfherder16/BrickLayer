#!/usr/bin/env node
/**
 * masonry-file-size-guard.js
 * PostToolUse hook — enforces 300-line file size limit on .py, .ts, .js files.
 * Hard blocks (exit 2) when lines > 300.
 * Warns (exit 0) when lines > 250.
 * Exempt: test files, __init__.py, *.d.ts, migration files.
 */

const fs = require('fs');
const path = require('path');

const LINE_LIMIT = 300;
const WARN_THRESHOLD = 250;

/**
 * Target file extensions that are subject to the size check.
 */
const TARGET_EXTENSIONS = new Set(['.py', '.ts', '.js']);

/**
 * Return true if the file is exempt from the size check.
 */
function isExempt(filePath) {
  const basename = path.basename(filePath);
  const ext = path.extname(filePath);

  // __init__.py — Python package init file
  if (basename === '__init__.py') return true;

  // TypeScript declaration files
  if (filePath.endsWith('.d.ts')) return true;

  // Test files: test_*, *_test.*, *.test.*
  if (
    basename.startsWith('test_') ||
    /[._]test\.[^.]+$/.test(basename) ||
    /_test\.[^.]+$/.test(basename)
  ) {
    return true;
  }

  // Migration files (common patterns: migrations/, 0001_*, *_migration.*)
  if (
    filePath.includes('/migrations/') ||
    filePath.includes('\\migrations\\') ||
    /\d{4}_/.test(basename) ||
    basename.includes('_migration.')
  ) {
    return true;
  }

  return false;
}

/**
 * Count the number of lines in a file.
 * Returns null if the file cannot be read.
 */
function countLines(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return content.split('\n').length;
  } catch (_e) {
    return null;
  }
}

/**
 * Main hook entry point — reads stdin and checks file size.
 */
let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    // Only respond to Write and Edit operations
    if (!['Write', 'Edit'].includes(tool_name)) {
      process.exit(0);
    }

    const filePath = tool_input.file_path || tool_input.path || '';
    if (!filePath) {
      process.exit(0);
    }

    const ext = path.extname(filePath);
    if (!TARGET_EXTENSIONS.has(ext)) {
      process.exit(0);
    }

    if (isExempt(filePath)) {
      process.exit(0);
    }

    const lineCount = countLines(filePath);
    if (lineCount === null) {
      // Can't read file — don't block
      process.exit(0);
    }

    if (lineCount > LINE_LIMIT) {
      process.stderr.write(
        `FILE_SIZE_BLOCK: ${filePath} has ${lineCount} lines (limit: ${LINE_LIMIT}). Split this file into focused modules.\n`
      );
      process.exit(2);
    }

    if (lineCount > WARN_THRESHOLD) {
      process.stderr.write(
        `FILE_SIZE_WARN: ${filePath} has ${lineCount} lines (approaching 300-line limit). Consider splitting.\n`
      );
      process.exit(0);
    }

    // Within limits — silent
    process.exit(0);
  } catch (_e) {
    // Parse error — never block
    process.exit(0);
  }
});

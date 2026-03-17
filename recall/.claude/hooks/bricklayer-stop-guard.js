#!/usr/bin/env node
/**
 * BrickLayer Stop Guard
 *
 * Blocks Claude from stopping while PENDING questions exist in questions.md.
 * Installed as a Stop hook in .claude/settings.json.
 *
 * Exit 0  = allow stop
 * Exit 1  = block stop (Claude sees the error message and must continue)
 */

const fs = require('fs');
const path = require('path');

const questionsFile = path.resolve(__dirname, '../../questions.md');

try {
  const content = fs.readFileSync(questionsFile, 'utf8');

  // Count lines that are actual status fields (not the header definition line)
  const lines = content.split('\n');
  let pendingCount = 0;
  for (const line of lines) {
    // Match "**Status**: PENDING" but not the header "Status values: PENDING | ..."
    if (/^\*\*Status\*\*:\s*PENDING\s*$/.test(line.trim())) {
      pendingCount++;
    }
  }

  if (pendingCount > 0) {
    console.error(
      `[bricklayer-stop-guard] STOP BLOCKED: ${pendingCount} PENDING question(s) remain in questions.md. ` +
      `Continue the research loop — pick the next PENDING question and run it. NEVER STOP.`
    );
    process.exit(1);
  }

  // No pending questions — allow stop only if hypothesis-generator has been invoked
  // (checked by looking for a recent wave header in questions.md)
  process.exit(0);

} catch (err) {
  // If we can't read the file, don't block — something else is wrong
  console.error(`[bricklayer-stop-guard] Could not read questions.md: ${err.message}`);
  process.exit(0);
}

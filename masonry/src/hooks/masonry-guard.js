'use strict';
// src/hooks/masonry-guard.js — PostToolUse async hook
// Fingerprints error patterns; triggers 3-strike warning via guard queue.

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const MAX_STDIN = 2 * 1024 * 1024;
const GUARD_THRESHOLD = parseInt(process.env.MASONRY_GUARD_THRESHOLD || '3', 10);

// Patterns that indicate a tool error/failure
const ERROR_SIGNALS = [
  /non-zero exit/i,
  /\bError\b/,
  /\bFAILED\b/,
  /\bexception\b/i,
  /\btraceback\b/i,
  /\bnot found\b/i,
  /\bcannot\b/i,
  /\bundefined\b/i,
];

/**
 * Extract a short error summary from the tool response.
 */
function extractErrorSummary(response) {
  if (!response) return '';
  const text = typeof response === 'string' ? response : JSON.stringify(response);
  // Take first line that looks like an error message
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  for (const line of lines) {
    if (ERROR_SIGNALS.some(re => re.test(line))) {
      return line.slice(0, 120);
    }
  }
  return lines[0]?.slice(0, 120) || text.slice(0, 120);
}

/**
 * Check if tool response contains an error signal.
 */
function hasErrorSignal(response) {
  if (!response) return false;
  const text = typeof response === 'string' ? response : JSON.stringify(response);
  return ERROR_SIGNALS.some(re => re.test(text));
}

/**
 * Build a fingerprint hash from tool name + first 100 chars of error text.
 */
function fingerprint(toolName, errorText) {
  const key = `${toolName}:${errorText.slice(0, 100)}`;
  return crypto.createHash('md5').update(key).digest('hex').slice(0, 12);
}

async function main() {
  let raw = '';
  try {
    for await (const chunk of process.stdin) {
      raw += chunk;
      if (raw.length > MAX_STDIN) break;
    }
  } catch (_err) { process.exit(0); }

  let input = {};
  try { input = JSON.parse(raw); } catch (_err) { process.exit(0); }

  const { tool_name, tool_response, session_id: sessionId = 'unknown' } = input;

  // Only care about error-bearing responses
  if (!hasErrorSignal(tool_response)) process.exit(0);

  const errorSummary = extractErrorSummary(tool_response);
  const fp = fingerprint(tool_name || 'unknown', errorSummary);

  const guardCountFile = path.join(os.tmpdir(), `masonry-guard-${sessionId}.json`);
  const guardQueueFile = path.join(os.tmpdir(), `masonry-guard-${sessionId}.ndjson`);

  // Load current fingerprint counts
  let counts = {};
  try {
    if (fs.existsSync(guardCountFile)) {
      counts = JSON.parse(fs.readFileSync(guardCountFile, 'utf8'));
    }
  } catch (_err) { /* fresh */ }

  counts[fp] = (counts[fp] || 0) + 1;

  if (counts[fp] >= GUARD_THRESHOLD) {
    // Enqueue warning for next register flush
    const warning = JSON.stringify({
      type: 'warning',
      fingerprint: fp,
      message: `3-strike pattern detected on tool "${tool_name}": ${errorSummary}. Investigate root cause before retrying.`,
      timestamp: new Date().toISOString(),
    });
    try {
      fs.appendFileSync(guardQueueFile, warning + '\n', 'utf8');
    } catch (_err) { /* non-fatal */ }

    // Reset count so the next 3 failures produce another warning
    counts[fp] = 0;
  }

  // Persist updated counts
  try {
    fs.writeFileSync(guardCountFile, JSON.stringify(counts), 'utf8');
  } catch (_err) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

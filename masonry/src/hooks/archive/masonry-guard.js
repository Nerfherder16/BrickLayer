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

// Fields in a tool_response object that may legitimately contain error text.
// Deliberately excludes content/code fields (old_string, new_string, content, result,
// stdout) that commonly contain English words or code matching ERROR_SIGNALS patterns.
const _ERROR_FIELDS = ['error', 'stderr', 'errorMessage', 'message', 'reason', 'details'];

/**
 * Extract candidate error text strings from a tool response.
 * For string responses, returns the string directly.
 * For object responses, only checks known error-bearing fields to avoid false
 * positives from code content in old_string/new_string/content/stdout.
 */
function _errorTexts(response) {
  if (!response) return [];
  if (typeof response === 'string') return [response];
  // Object response: check is_error flag first for fast path
  if (response.is_error === true || response.type === 'error') {
    // Error-flagged responses may serialize safely since they won't contain old code
    return [JSON.stringify(response)];
  }
  // Only extract from known error-bearing fields
  return _ERROR_FIELDS.map(f => response[f]).filter(v => typeof v === 'string' && v.length > 0);
}

/**
 * Extract a short error summary from the tool response.
 */
function extractErrorSummary(response) {
  if (!response) return '';
  const texts = _errorTexts(response);
  const combined = texts.join('\n');
  const lines = combined.split('\n').map(l => l.trim()).filter(Boolean);
  for (const line of lines) {
    if (ERROR_SIGNALS.some(re => re.test(line))) {
      return line.slice(0, 120);
    }
  }
  return lines[0]?.slice(0, 120) || combined.slice(0, 120);
}

/**
 * Check if tool response contains an error signal.
 * Scopes detection to error-bearing fields only — avoids false positives from
 * code content (old_string, new_string, stdout) that contains common English
 * words matching ERROR_SIGNALS patterns.
 */
function hasErrorSignal(response) {
  if (!response) return false;
  const texts = _errorTexts(response);
  return texts.some(text => ERROR_SIGNALS.some(re => re.test(text)));
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

  // Persist updated counts — atomic rename to prevent torn writes under concurrent execution
  const guardCountTmp = `${guardCountFile}.tmp.${process.pid}`;
  try {
    fs.writeFileSync(guardCountTmp, JSON.stringify(counts), 'utf8');
    fs.renameSync(guardCountTmp, guardCountFile);
  } catch (_err) {
    try { fs.unlinkSync(guardCountTmp); } catch (_) { /* cleanup best-effort */ }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

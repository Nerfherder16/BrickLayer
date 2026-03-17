'use strict';
// src/hooks/masonry-observe.js — PostToolUse async hook
// A) Detects findings written to findings/*.md → stores to Recall + updates state
// B) Appends all Edit/Write/MultiEdit/NotebookEdit activity to session activity log

const fs = require('fs');
const path = require('path');
const os = require('os');

const { storeMemory } = require('../core/recall');
const { readState, writeState } = require('../core/state');

const WATCHED_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
const MAX_STDIN = 2 * 1024 * 1024;

// Severity → Recall importance score
const SEVERITY_IMPORTANCE = {
  Critical: 0.95,
  High: 0.85,
  Medium: 0.65,
  Low: 0.45,
  Info: 0.3,
};

/**
 * Extract a labeled value from markdown content.
 * Looks for "**Label**: value" patterns (case-insensitive label).
 */
function extractMarkdownField(content, label) {
  const re = new RegExp(`\\*{0,2}${label}\\*{0,2}:\\s*([\\w]+)`, 'i');
  const m = content.match(re);
  return m ? m[1].trim() : null;
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

  const { tool_name, tool_input = {}, session_id: sessionId = 'unknown', cwd = process.cwd() } = input;

  if (!WATCHED_TOOLS.has(tool_name)) process.exit(0);

  const rawFilePath = tool_input.file_path || tool_input.path || 'unknown';
  const filePath = path.normalize(rawFilePath).replace(/\\/g, '/');

  // --- B) Activity log (all watched edits) ---
  const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
  const oneLiner = `${tool_name} → ${path.basename(filePath)}`;
  const activityEntry = JSON.stringify({
    timestamp: new Date().toISOString(),
    tool: tool_name,
    file: filePath,
    summary: oneLiner,
  });
  try {
    fs.appendFileSync(activityFile, activityEntry + '\n', 'utf8');
  } catch (_err) { /* non-fatal */ }

  // --- A) Finding detection ---
  // Match findings/{qid}.md or findings/synthesis.md
  const findingsRe = /findings[/\\]([^/\\]+\.md)$/i;
  const match = filePath.match(findingsRe);
  if (!match) process.exit(0);

  const findingFilename = match[1]; // e.g. "D7.md" or "synthesis.md"
  const qid = findingFilename.replace(/\.md$/i, ''); // e.g. "D7"

  // Read the actual file for content parsing
  let fileContent = '';
  try {
    const absPath = path.isAbsolute(rawFilePath) ? rawFilePath : path.join(cwd, rawFilePath);
    if (fs.existsSync(absPath)) {
      fileContent = fs.readFileSync(absPath, 'utf8');
    }
  } catch (_err) { /* can't read — use empty */ }

  const verdict = extractMarkdownField(fileContent, 'Verdict') || 'UNKNOWN';
  const severity = extractMarkdownField(fileContent, 'Severity') || 'Info';
  const importance = SEVERITY_IMPORTANCE[severity] || 0.3;
  const snippet = fileContent.slice(0, 500);

  // Read masonry.json from cwd for project name
  let project = path.basename(cwd);
  try {
    const masonryFile = path.join(cwd, 'masonry.json');
    if (fs.existsSync(masonryFile)) {
      const meta = JSON.parse(fs.readFileSync(masonryFile, 'utf8'));
      if (meta.name) project = meta.name;
    }
  } catch (_err) { /* optional */ }

  // Store finding to Recall
  await storeMemory({
    content: snippet,
    domain: `${project}-autoresearch`,
    tags: [
      'masonry',
      `project:${project}`,
      `qid:${qid}`,
      `verdict:${verdict}`,
      `severity:${severity}`,
      'masonry:finding',
    ],
    importance,
  });

  // Update masonry-state.json — increment verdict count, update last_qid/verdict
  const verdictUpdate = {};
  if (verdict !== 'UNKNOWN') {
    const state = readState(cwd) || {};
    const existing = state.verdicts || {};
    verdictUpdate[verdict] = (existing[verdict] || 0) + 1;
  }

  writeState(cwd, {
    last_qid: qid,
    last_verdict: verdict,
    ...(Object.keys(verdictUpdate).length ? { verdicts: verdictUpdate } : {}),
  });

  process.exit(0);
}

main().catch(() => process.exit(0));

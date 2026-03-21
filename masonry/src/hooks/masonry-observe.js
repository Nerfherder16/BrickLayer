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
  const re = new RegExp(`\\*{0,2}${label}\\*{0,2}:\\s*([\\w-]+)`, 'i');
  const m = content.match(re);
  return m ? m[1].trim() : null;
}

// ---------------------------------------------------------------------------
// Code-fact extraction helpers
// ---------------------------------------------------------------------------

const SKIP_DIRS = /[/\\](node_modules|\.git|__pycache__|dist|build|\.next|tests|__tests__)[/\\]/i;
const SKIP_TEST = /\.(test|spec)\.(js|ts|jsx|tsx|py)$/i;
const CODE_EXTS = /\.(py|js|ts|jsx|tsx|mjs|cjs|md)$/i;

const PY_DEF    = /^[+]?\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(/m;
const PY_CLASS  = /^[+]?\s*class\s+([A-Za-z_]\w*)\s*[:(]/m;
const JS_FUNC   = /^[+]?\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/m;
const JS_ARROW  = /^[+]?\s*(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\(/m;
const JS_EXPORT = /^[+]?\s*export\s+(?:default\s+)?(?:function|class|const)\s+([A-Za-z_$][\w$]*)/m;

/**
 * Scan added lines (lines starting with '+' in a diff, or all lines for Write)
 * and return matching definition names for the given patterns.
 */
function scanLines(lines, patterns) {
  const names = new Set();
  for (const line of lines) {
    for (const re of patterns) {
      const m = line.match(re);
      if (m && m[1]) names.add(m[1]);
    }
  }
  return [...names];
}

/**
 * Count lines matching a definition pattern (for new-file summaries).
 */
function countDefs(content, patterns) {
  let count = 0;
  for (const line of content.split('\n')) {
    for (const re of patterns) {
      if (re.test(line)) { count++; break; }
    }
  }
  return count;
}

/**
 * Derive added lines from an Edit (new_string vs old_string) or Write (full content).
 * Returns lines that were added (not present in old, or all for Write).
 */
function addedLines(toolName, toolInput) {
  if (toolName === 'Write') {
    const content = toolInput.content || '';
    return content.split('\n').map(l => '+' + l);
  }
  if (toolName === 'Edit' || toolName === 'MultiEdit') {
    const edits = toolName === 'MultiEdit'
      ? (toolInput.edits || [])
      : [{ old_string: toolInput.old_string || '', new_string: toolInput.new_string || '' }];
    const added = [];
    for (const e of edits) {
      const newLines = (e.new_string || '').split('\n');
      const oldSet = new Set((e.old_string || '').split('\n'));
      for (const l of newLines) {
        if (!oldSet.has(l)) added.push('+' + l);
      }
    }
    return added;
  }
  return [];
}

/**
 * Extract human-readable facts from a code file edit.
 * Synchronous regex only — no I/O.
 * Returns an array of fact strings (max 5, each max 200 chars).
 */
async function extractCodeFacts(filePath, toolName, toolInput, cwd) {
  // Skip non-code or ignored paths
  if (SKIP_DIRS.test(filePath)) return [];
  if (SKIP_TEST.test(filePath)) return [];
  if (!CODE_EXTS.test(filePath)) return [];

  const rel = filePath.includes(cwd.replace(/\\/g, '/'))
    ? filePath.replace(cwd.replace(/\\/g, '/') + '/', '')
    : path.basename(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const baseName = path.basename(filePath);
  const facts = [];

  const isNewFile = toolName === 'Write';

  // --- Special files ---
  if (/^(ROADMAP|CHANGELOG|ARCHITECTURE)\.md$/i.test(baseName)) {
    facts.push(`Updated ${baseName} in ${rel.includes('/') ? path.dirname(rel) : 'project root'}`);
    return facts;
  }

  if (/questions\.md$/i.test(baseName)) {
    const newStr = toolInput.new_string || toolInput.content || '';
    const doneCount = (newStr.match(/\bDONE\b/g) || []).length;
    if (doneCount > 0) {
      facts.push(`questions.md updated — ${doneCount} question(s) marked DONE`);
    }
    return facts;
  }

  // --- Python ---
  if (ext === '.py') {
    if (isNewFile) {
      const content = toolInput.content || '';
      const nDefs = countDefs(content, [/^\s*(?:async\s+)?def\s+[A-Za-z_]/m, /^\s*class\s+[A-Za-z_]/m]);
      facts.push(`Created new file ${rel} with ${nDefs} definition(s)`);
      return facts.slice(0, 5).map(f => f.slice(0, 200));
    }
    const lines = addedLines(toolName, toolInput);
    const defNames = scanLines(lines, [PY_DEF]);
    const classNames = scanLines(lines, [PY_CLASS]);
    for (const n of defNames.slice(0, 3)) facts.push(`Added function ${n} to ${rel}`);
    for (const n of classNames.slice(0, 2)) facts.push(`Added class ${n} to ${rel}`);
  }

  // --- JavaScript / TypeScript ---
  if (['.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'].includes(ext)) {
    if (isNewFile) {
      const content = toolInput.content || '';
      const nExports = countDefs(content, [
        /^\s*export\s+(?:default\s+)?(?:function|class|const)\s+[A-Za-z_$]/,
        /^\s*(?:async\s+)?function\s+[A-Za-z_$]/,
      ]);
      facts.push(`Created new file ${rel} with ${nExports} export(s)`);
      return facts.slice(0, 5).map(f => f.slice(0, 200));
    }
    const lines = addedLines(toolName, toolInput);
    const funcNames = scanLines(lines, [JS_FUNC, JS_ARROW, JS_EXPORT]);
    for (const n of funcNames.slice(0, 5)) facts.push(`Added function/export ${n} to ${rel}`);
  }

  return facts.slice(0, 5).map(f => f.slice(0, 200));
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

  // --- C) Code-fact extraction (non-findings edits) ---
  // Only runs when the file is NOT a finding — awaited so facts reach Recall before exit.
  if (!match) {
    try {
      const facts = await extractCodeFacts(filePath, tool_name, tool_input, cwd);
      if (facts.length) {
        const ext = path.extname(filePath).replace('.', '') || 'txt';
        let cfProject = path.basename(cwd);
        try {
          const mf = path.join(cwd, 'masonry.json');
          if (fs.existsSync(mf)) {
            const meta = JSON.parse(fs.readFileSync(mf, 'utf8'));
            if (meta.name) cfProject = meta.name;
          }
        } catch (_e) { /* optional */ }
        const domain = `${cfProject}-code`;
        await Promise.all(facts.map(fact =>
          storeMemory({ content: fact, domain, tags: ['code-fact', 'auto-extracted', ext], importance: 0.5 })
            .catch(() => {})
        ));
      }
    } catch (_e) { /* non-fatal */ }
    process.exit(0);
  }

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

  // Emit "finding" event to routing_log.jsonl for DSPy routing training signal (F14.2)
  // Pairs with "start" events from masonry-subagent-tracker.js to score downstream_success.
  if (verdict !== 'UNKNOWN') {
    const agentField = extractMarkdownField(fileContent, 'Agent') || 'unknown';
    const findingEntry = JSON.stringify({
      timestamp: new Date().toISOString(),
      event: 'finding',
      agent: agentField,
      session_id: sessionId,
      verdict,
      qid,
    });
    try {
      // Resolve masonry/ dir — cwd might be the masonry dir itself (self-research sessions)
      const masonryDir = path.basename(cwd) === 'masonry' && fs.existsSync(cwd)
        ? cwd
        : path.join(cwd, 'masonry');
      if (fs.existsSync(masonryDir)) {
        const routingLogPath = path.join(masonryDir, 'routing_log.jsonl');
        fs.appendFileSync(routingLogPath, findingEntry + '\n', 'utf8');
      }
    } catch (_err) { /* non-fatal */ }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

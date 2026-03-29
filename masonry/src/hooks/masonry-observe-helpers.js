'use strict';
/**
 * masonry-observe-helpers.js — Code-fact extraction and overseer trigger helpers.
 * Extracted from masonry-observe.js to satisfy 300-line file size limit.
 */

const fs = require('fs');
const path = require('path');

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

function countDefs(content, patterns) {
  let count = 0;
  for (const line of content.split('\n')) {
    for (const re of patterns) {
      if (re.test(line)) { count++; break; }
    }
  }
  return count;
}

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

async function extractCodeFacts(filePath, toolName, toolInput, cwd) {
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

/**
 * Track agent invocations; write overseer trigger flag at count 10.
 */
function handleObserveWrite(filePath, snapshotsDir) {
  const isAgentMd = /agents[\\/][^/\\]+\.md$/.test(filePath);
  const isFinding = /findings[\\/]/.test(filePath);
  if (!isAgentMd && !isFinding) return;

  const countFile = path.join(snapshotsDir, '.invocation_count');
  let data = { count: 0 };
  try { data = JSON.parse(fs.readFileSync(countFile, 'utf8')); } catch (_e) {}
  data.count = (data.count || 0) + 1;
  fs.mkdirSync(snapshotsDir, { recursive: true });
  fs.writeFileSync(countFile, JSON.stringify(data), 'utf8');

  if (data.count >= 10) {
    const flag = { triggered_at: new Date().toISOString(), count: data.count };
    fs.writeFileSync(path.join(snapshotsDir, 'overseer_trigger.flag'), JSON.stringify(flag), 'utf8');
    fs.writeFileSync(countFile, JSON.stringify({ count: 0 }), 'utf8');
  }
}

/**
 * Walk up from startDir to find the masonry/ subdirectory.
 * Handles project subdirs, self-research sessions, and standard BL layouts.
 */
function findMasonryDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 8; i++) {
    // cwd IS the masonry dir (self-research session)
    if (path.basename(dir) === 'masonry' && fs.existsSync(dir)) return dir;
    // masonry/ is a child of this dir
    const candidate = path.join(dir, 'masonry');
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

module.exports = { extractCodeFacts, handleObserveWrite, findMasonryDir };

'use strict';
// src/hooks/masonry-observe.js — PostToolUse async hook
// A) Detects findings written to findings/*.md → stores to Recall + updates state
// B) Appends all Edit/Write/MultiEdit/NotebookEdit activity to session activity log
// C) Extracts code facts from non-finding edits and stores to Recall

const fs = require('fs');
const path = require('path');
const os = require('os');

const { storeMemory } = require('../core/recall');
const { readState, writeState } = require('../core/state');
const { appendJsonl: masAppendJsonl, writeJson: masWriteJson, readJson: masReadJson } = require('../core/mas');
const { extractCodeFacts, handleObserveWrite, findMasonryDir } = require('./masonry-observe-helpers');

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

function extractMarkdownField(content, label) {
  const re = new RegExp(`\\*{0,2}${label}\\*{0,2}:\\s*([\\w-]+)`, 'i');
  const m = content.match(re);
  return m ? m[1].trim() : null;
}

module.exports.handleObserveWrite = handleObserveWrite;

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

  const { getSessionId } = require('./session/stop-utils');
  const { tool_name, tool_input = {}, cwd = process.cwd() } = input;
  const sessionId = getSessionId(input);

  if (!WATCHED_TOOLS.has(tool_name)) process.exit(0);

  const rawFilePath = tool_input.file_path || tool_input.path || 'unknown';
  const filePath = path.normalize(rawFilePath).replace(/\\/g, '/');

  // --- Overseer trigger counter ---
  try {
    const snapshotsDir = path.join(cwd, 'masonry', 'agent_snapshots');
    handleObserveWrite(rawFilePath, snapshotsDir);
  } catch (_err) { /* non-fatal */ }

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
  const findingsRe = /findings[/\\]([^/\\]+\.md)$/i;
  const match = filePath.match(findingsRe);

  // --- C) Code-fact extraction (non-findings edits) ---
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

  const findingFilename = match[1];
  const qid = findingFilename.replace(/\.md$/i, '');

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

  let project = path.basename(cwd);
  try {
    const masonryFile = path.join(cwd, 'masonry.json');
    if (fs.existsSync(masonryFile)) {
      const meta = JSON.parse(fs.readFileSync(masonryFile, 'utf8'));
      if (meta.name) project = meta.name;
    }
  } catch (_err) { /* optional */ }

  const recallResult = await storeMemory({
    content: snippet,
    domain: `${project}-autoresearch`,
    tags: ['masonry', `project:${project}`, `qid:${qid}`, `verdict:${verdict}`, `severity:${severity}`, 'masonry:finding'],
    importance,
  });

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

  // Emit "finding" event to routing_log.jsonl for DSPy routing training signal
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
      const masonryDir = findMasonryDir(cwd);
      if (masonryDir) {
        const routingLogPath = path.join(masonryDir, 'routing_log.jsonl');
        fs.appendFileSync(routingLogPath, findingEntry + '\n', 'utf8');
      }
    } catch (_err) { /* non-fatal */ }
  }

  // .mas/ timing telemetry
  try {
    const waveMatch = fileContent.match(/\*\*Wave\*\*:\s*(\d+)/i);
    const wave = waveMatch ? parseInt(waveMatch[1], 10) : null;
    masAppendJsonl(cwd, 'timing.jsonl', {
      qid, wave,
      agent: extractMarkdownField(fileContent, 'Agent') || 'unknown',
      started_at: null, duration_ms: null,
      verdict, timestamp: new Date().toISOString(),
    });
  } catch (_) {}

  // .mas/ agent scores
  try {
    const agentName = extractMarkdownField(fileContent, 'Agent') || 'unknown';
    const scores = masReadJson(cwd, 'agent_scores.json') || {};
    if (!scores[agentName]) scores[agentName] = { count: 0, verdicts: {}, last_seen: null };
    scores[agentName].count += 1;
    scores[agentName].verdicts[verdict] = (scores[agentName].verdicts[verdict] || 0) + 1;
    scores[agentName].last_seen = new Date().toISOString();
    masWriteJson(cwd, 'agent_scores.json', scores);
  } catch (_) {}

  // .mas/ recall log
  try {
    masAppendJsonl(cwd, 'recall_log.jsonl', {
      qid, query: snippet.slice(0, 100),
      memory_id: recallResult && recallResult.id ? recallResult.id : null,
      domain: `${project}-autoresearch`,
      timestamp: new Date().toISOString(),
    });
  } catch (_) {}

  process.exit(0);
}

main().catch(() => process.exit(0));

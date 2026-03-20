'use strict';
// src/hooks/masonry-stop.js — Stop hook
// Builds a session summary, optionally enriches with Ollama, stores to Recall, cleans up temp files.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { loadConfig } = require('../core/config');
const { readState } = require('../core/state');
const { storeMemory, isAvailable } = require('../core/recall');

const MAX_STDIN = 2 * 1024 * 1024;

/**
 * Read NDJSON activity log and return parsed entries.
 */
function readActivityLog(sessionId) {
  const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
  if (!fs.existsSync(activityFile)) return [];
  try {
    return fs.readFileSync(activityFile, 'utf8')
      .trim().split('\n').filter(Boolean)
      .map(l => { try { return JSON.parse(l); } catch (_e) { return null; } })
      .filter(Boolean);
  } catch (_err) { return []; }
}

/**
 * Ask Ollama for a 2-sentence summary of what was accomplished.
 * Returns null if unavailable or times out.
 */
async function ollamaSummarize(prompt, cfg) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    const res = await fetch(`${cfg.ollamaHost}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: cfg.ollamaModel,
        prompt,
        stream: false,
        options: { num_predict: 80 },
      }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) return null;
    const data = await res.json();
    return data.response?.trim() || null;
  } catch (_err) {
    return null;
  }
}

/**
 * Delete all /tmp/masonry-*-{sessionId}.* files.
 */
function cleanupTempFiles(sessionId) {
  try {
    const files = fs.readdirSync(os.tmpdir());
    for (const f of files) {
      if (f.includes(sessionId) && f.startsWith('masonry-')) {
        try { fs.unlinkSync(path.join(os.tmpdir(), f)); } catch (_e) { /* skip */ }
      }
    }
  } catch (_err) { /* non-fatal */ }
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

  const sessionId = input.session_id || 'unknown';
  const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const cfg = loadConfig();

  // Read masonry.json for project name
  let project = path.basename(cwd);
  try {
    const masonryFile = path.join(cwd, 'masonry.json');
    if (fs.existsSync(masonryFile)) {
      const meta = JSON.parse(fs.readFileSync(masonryFile, 'utf8'));
      if (meta.name) project = meta.name;
    }
  } catch (_err) { /* optional */ }

  const activity = readActivityLog(sessionId);
  const state = readState(cwd);

  // Count unique files edited and findings written
  const filesEdited = [...new Set(activity.map(e => e.file).filter(f => f && f !== 'unknown'))];
  const findingsWritten = filesEdited.filter(f => /findings[/\\][^/\\]+\.md$/i.test(f));
  const verdictSummary = state?.verdicts
    ? Object.entries(state.verdicts).map(([k, v]) => `${k}:${v}`).join(', ')
    : 'no verdicts';

  const summaryLines = [
    `Project: ${project}`,
    `Session: ${sessionId}`,
    `Files edited: ${filesEdited.length}`,
    `Findings written: ${findingsWritten.length}`,
    `Verdict summary: ${verdictSummary}`,
    state?.wave ? `Wave: ${state.wave}` : '',
    state?.last_verdict ? `Last verdict: ${state.last_verdict} (${state.last_qid})` : '',
  ].filter(Boolean).join('\n');

  // Optionally enrich with Ollama
  let ollamaInsight = null;
  const ollamaPrompt = `In exactly 2 sentences, summarize what was accomplished in this research session:\n${summaryLines}`;
  ollamaInsight = await ollamaSummarize(ollamaPrompt, cfg);

  const finalContent = ollamaInsight
    ? `${summaryLines}\n\nSession insight: ${ollamaInsight}`
    : summaryLines;

  // Store to Recall
  if (await isAvailable()) {
    await storeMemory({
      content: finalContent,
      domain: `${project}-autoresearch`,
      tags: [
        'masonry',
        `project:${project}`,
        'masonry:session-summary',
        `session:${sessionId}`,
      ],
      importance: 0.7,
    });
  }

  // Cleanup temp files
  cleanupTempFiles(sessionId);

  process.exit(0);
}

main().catch(() => process.exit(0));

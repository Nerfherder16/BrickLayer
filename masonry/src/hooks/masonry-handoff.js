'use strict';
// src/hooks/masonry-handoff.js — Detached background handoff process
// Called as: node masonry-handoff.js {sessionId}
// Packages loop state + recent findings into Recall for next-session resume.

const fs = require('fs');
const path = require('path');
const os = require('os');

const { storeMemory } = require('../core/recall');
const { readState } = require('../core/state');

const sessionId = process.argv[2] || 'unknown';
const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

/**
 * Read the 3 most recent findings by mtime from findings/ dir.
 */
function readRecentFindings(dir) {
  const findingsDir = path.join(dir, 'findings');
  if (!fs.existsSync(findingsDir)) return [];

  try {
    const files = fs.readdirSync(findingsDir)
      .filter(f => f.endsWith('.md') && f !== 'synthesis.md')
      .map(f => ({
        name: f,
        fullPath: path.join(findingsDir, f),
        mtime: fs.statSync(path.join(findingsDir, f)).mtime.getTime(),
      }))
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 3);

    return files.map(({ name, fullPath }) => {
      const qid = name.replace(/\.md$/i, '');
      let verdict = 'UNKNOWN';
      let severity = 'Info';
      let summary = '';
      try {
        const content = fs.readFileSync(fullPath, 'utf8');
        const verdictMatch = content.match(/\*{0,2}Verdict\*{0,2}:\s*([\w_]+)/i);
        const severityMatch = content.match(/\*{0,2}Severity\*{0,2}:\s*([\w]+)/i);
        const summaryMatch = content.match(/## Summary\s*\n(.*)/i);
        if (verdictMatch) verdict = verdictMatch[1];
        if (severityMatch) severity = severityMatch[1];
        if (summaryMatch) summary = summaryMatch[1].trim().slice(0, 100);
        else summary = content.slice(0, 100).replace(/\n/g, ' ').trim();
      } catch (_err) { /* unreadable */ }
      return { qid, verdict, severity, summary };
    });
  } catch (_err) {
    return [];
  }
}

/**
 * Count PENDING and DONE questions in questions.md.
 */
function countQuestions(dir) {
  try {
    const qFile = path.join(dir, 'questions.md');
    if (!fs.existsSync(qFile)) return { pending: 0, done: 0 };
    const content = fs.readFileSync(qFile, 'utf8');
    const pending = (content.match(/\bPENDING\b/g) || []).length;
    const done = (content.match(/\bDONE\b/g) || []).length;
    return { pending, done };
  } catch (_err) {
    return { pending: 0, done: 0 };
  }
}

async function main() {
  // Guard: don't re-trigger if already done this session
  const guardFile = path.join(os.tmpdir(), `masonry-handoff-triggered-${sessionId}.json`);
  if (fs.existsSync(guardFile)) process.exit(0);

  const state = readState(cwd);
  const recentFindings = readRecentFindings(cwd);
  const { pending, done } = countQuestions(cwd);

  // Read masonry.json for project name
  let project = path.basename(cwd);
  try {
    const masonryFile = path.join(cwd, 'masonry.json');
    if (fs.existsSync(masonryFile)) {
      const meta = JSON.parse(fs.readFileSync(masonryFile, 'utf8'));
      if (meta.name) project = meta.name;
    }
  } catch (_err) { /* optional */ }

  const wave = state?.wave || 1;
  const nextQid = state?.last_qid || 'unknown';
  const activeMode = state?.mode || 'unknown';
  const agentScores = {}; // agent_db.json is Phase 2 — placeholder

  // Build resume prompt
  const resumeParts = [`Resuming wave ${wave} from question after ${nextQid}.`];
  if (state?.last_verdict) {
    resumeParts.push(`Last verdict: ${state.last_verdict}.`);
  }
  if (pending > 0) resumeParts.push(`${pending} questions pending.`);
  if (recentFindings.length > 0) {
    const critical = recentFindings.find(f => f.severity === 'Critical' || f.severity === 'High');
    if (critical) {
      resumeParts.push(`Recent high-severity finding: ${critical.qid} ${critical.verdict} — ${critical.summary}.`);
    }
  }

  const payload = {
    type: 'masonry:handoff',
    session_id: sessionId,
    project,
    timestamp: new Date().toISOString(),
    context_pct_at_handoff: null, // filled by statusline if available

    loop_state: {
      wave,
      next_question_id: nextQid,
      pending_count: pending,
      done_count: done,
      active_mode: activeMode,
    },

    recent_findings: recentFindings,
    agent_scores: agentScores,

    last_synthesis: null, // read from synthesis.md if available
    pending_sentinels: {
      forge_needed: fs.existsSync(path.join(cwd, 'FORGE_NEEDED.md')),
      audit_report_pending: fs.existsSync(path.join(cwd, 'AUDIT_REPORT.md')),
      override_verdicts: [],
    },

    resume_prompt: resumeParts.join(' '),
  };

  // Try to enrich with synthesis.md recommendation
  try {
    const synthFile = path.join(cwd, 'findings', 'synthesis.md');
    if (fs.existsSync(synthFile)) {
      const synth = fs.readFileSync(synthFile, 'utf8');
      const recMatch = synth.match(/\*{0,2}Recommendation\*{0,2}:\s*([\w]+)/i);
      const confMatch = synth.match(/\*{0,2}Confidence\*{0,2}:\s*([\d.]+)/i);
      if (recMatch) {
        payload.last_synthesis = {
          recommendation: recMatch[1],
          confidence: confMatch ? parseFloat(confMatch[1]) : null,
          wave,
        };
        payload.resume_prompt += ` Last synthesis: ${recMatch[1]}.`;
      }
    }
  } catch (_err) { /* optional */ }

  await storeMemory({
    content: JSON.stringify(payload),
    domain: `${project}-autoresearch`,
    tags: ['masonry:handoff', `project:${project}`, `session:${sessionId}`],
    importance: 0.95,
  });

  // Write guard file so statusline doesn't re-trigger
  try {
    fs.writeFileSync(guardFile, JSON.stringify({ triggered: true, ts: new Date().toISOString() }));
  } catch (_err) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

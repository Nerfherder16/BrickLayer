'use strict';
// src/hooks/masonry-register.js — UserPromptSubmit hook
// Every call: detect BrickLayer context, inject Mortar routing directive
// First call only: hydrate session from Recall (handoff or recent findings)
// Subsequent calls: flush pending guard warnings (after directive)

const fs = require('fs');
const path = require('path');
const os = require('os');

const { isAvailable, searchMemory, storeMemory } = require('../core/recall');

const MAX_STDIN = 2 * 1024 * 1024; // 2MB cap

// ---------------------------------------------------------------------------
// BrickLayer context detection
// ---------------------------------------------------------------------------

function readJsonFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch (_err) { /* non-fatal */ }
  return null;
}

function detectBrickLayerContext(cwd) {
  const masonryMeta    = readJsonFile(path.join(cwd, 'masonry.json'));
  const campaignState  = readJsonFile(path.join(cwd, 'masonry-state.json'));
  const autopilotMode  = (() => {
    try {
      const f = path.join(cwd, '.autopilot', 'mode');
      return fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim() : null;
    } catch (_e) { return null; }
  })();
  const autopilotProgress = readJsonFile(path.join(cwd, '.autopilot', 'progress.json'));
  const hasMortar = fs.existsSync(path.join(cwd, '.claude', 'agents', 'mortar.md'));

  return { masonryMeta, campaignState, autopilotMode, autopilotProgress, hasMortar };
}

// ---------------------------------------------------------------------------
// Build the Mortar routing directive
// ---------------------------------------------------------------------------

function buildRoutingDirective(ctx, project) {
  const lines = [
    '[MASONRY] Route this prompt through Mortar (.claude/agents/mortar.md).',
    'Mortar is the executive layer — it decides how to handle every request.',
  ];

  // Active research campaign
  if (ctx.campaignState) {
    const wave    = ctx.campaignState.wave || ctx.campaignState.current_wave || '?';
    const pending = ctx.campaignState.pending_questions
      ?? ctx.campaignState.questions_pending
      ?? '?';
    lines.push(`Active campaign: ${project}, wave ${wave}, ${pending} questions pending.`);
  }

  // Active autopilot build/fix
  if (ctx.autopilotMode && ctx.autopilotMode !== '') {
    let buildLine = `Active build: ${project}`;
    if (ctx.autopilotProgress) {
      const tasks = ctx.autopilotProgress.tasks || [];
      const done  = tasks.filter(t => t.status === 'DONE').length;
      buildLine += `, ${done}/${tasks.length} tasks complete`;
    }
    buildLine += '.';
    lines.push(buildLine);
  }

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, 'program.md')) &&
         fs.existsSync(path.join(dir, 'questions.md'));
}

// Emit collected context as a JSON envelope (required by Claude Code UserPromptSubmit hooks).
// All output must go through this — never call process.stdout.write() directly.
function emit(parts) {
  const text = parts.filter(Boolean).join('\n').trim();
  if (!text) return;
  process.stdout.write(JSON.stringify({ additionalContext: text }));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  if (isResearchProject(cwd)) return;

  let raw = '';
  try {
    for await (const chunk of process.stdin) {
      raw += chunk;
      if (raw.length > MAX_STDIN) break;
    }
  } catch (_err) { return; }

  let input = {};
  try { input = JSON.parse(raw); } catch (_err) { return; }

  const sessionId = input.session_id || 'unknown';
  const ctx = detectBrickLayerContext(cwd);
  const project = (ctx.masonryMeta && ctx.masonryMeta.name)
    || (ctx.autopilotProgress && ctx.autopilotProgress.project)
    || path.basename(cwd);

  // Always: Mortar routing directive (first item in every context block)
  const contextParts = [buildRoutingDirective(ctx, project)];

  const tempFile = path.join(os.tmpdir(), `masonry-${sessionId}.json`);

  // Check if this is the first call in this session
  let sessionState = null;
  try {
    if (fs.existsSync(tempFile)) {
      sessionState = JSON.parse(fs.readFileSync(tempFile, 'utf8'));
    }
  } catch (_err) { /* fresh session */ }

  // --- Subsequent call: flush pending guard warnings then exit ---
  if (sessionState && sessionState.firstCall === false) {
    const guardFile = path.join(os.tmpdir(), `masonry-guard-${sessionId}.ndjson`);
    if (fs.existsSync(guardFile)) {
      try {
        const lines = fs.readFileSync(guardFile, 'utf8').trim().split('\n').filter(Boolean);
        if (lines.length > 0) {
          const warnings = lines.map(l => {
            try { return JSON.parse(l); } catch (_e) { return null; }
          }).filter(Boolean);
          const messages = warnings.map(w => `[MASONRY GUARD] ${w.message}`).join('\n');
          if (messages) contextParts.push(messages);
          fs.unlinkSync(guardFile);
        }
      } catch (_err) { /* non-fatal */ }
    }
    emit(contextParts);
    return;
  }

  // --- First call: mark session started, hydrate from Recall ---
  try {
    fs.writeFileSync(tempFile, JSON.stringify({ project, sessionId, firstCall: false }), 'utf8');
  } catch (_err) { /* non-fatal */ }

  if (!(await isAvailable())) {
    emit(contextParts);
    return;
  }

  // Run both searches concurrently
  const [handoffs, findings] = await Promise.all([
    searchMemory({ query: project, tags: ['masonry:handoff'], limit: 1 }),
    searchMemory({
      query: `${project} research findings`,
      tags: [`project:${project}`, 'masonry:finding'],
      limit: 5,
    }),
  ]);

  // Fire-and-forget session start log
  storeMemory({
    content: `Masonry session started for project "${project}"`,
    domain: `${project}-autoresearch`,
    tags: ['masonry', `project:${project}`, 'masonry:session-start', `session:${sessionId}`],
    importance: 0.3,
  }).catch(() => {});

  // Check for recent handoff (< 24h)
  if (handoffs.length > 0) {
    const handoff = handoffs[0];
    const storedAt = handoff.created_at || handoff.timestamp || handoff.stored_at;
    const ageMs = storedAt ? Date.now() - new Date(storedAt).getTime() : Infinity;

    if (ageMs < 24 * 60 * 60 * 1000) {
      let payload = null;
      try {
        payload = typeof handoff.content === 'string'
          ? JSON.parse(handoff.content)
          : handoff.content;
      } catch (_err) { /* malformed handoff — fall through */ }

      if (payload && payload.resume_prompt) {
        const lines = [`[MASONRY] Resuming campaign for "${project}"`, payload.resume_prompt];
        if (payload.recent_findings && payload.recent_findings.length > 0) {
          lines.push('\nRecent findings:');
          for (const f of payload.recent_findings) {
            lines.push(`  ${f.qid} — ${f.verdict} (${f.severity}): ${f.summary}`);
          }
        }
        contextParts.push(lines.join('\n'));
        emit(contextParts);
        return;
      }
    }
  }

  // Surface last 5 findings from Recall
  if (findings.length > 0) {
    const lines = [`[MASONRY] Context for "${project}" — recent findings:`];
    for (const f of findings) {
      const snippet = (f.content || '').slice(0, 150).replace(/\n/g, ' ');
      lines.push(`  • ${snippet}`);
    }
    contextParts.push(lines.join('\n'));
  }

  emit(contextParts);
}

main().catch(() => {});

'use strict';
// src/hooks/masonry-register.js — UserPromptSubmit hook
// On first call: hydrate session from Recall (handoff or recent findings)
// On subsequent calls: flush pending guard warnings

const fs = require('fs');
const path = require('path');
const os = require('os');

const { isAvailable, searchMemory, storeMemory } = require('../core/recall');

const MAX_STDIN = 2 * 1024 * 1024; // 2MB cap

async function main() {
  let raw = '';
  try {
    for await (const chunk of process.stdin) {
      raw += chunk;
      if (raw.length > MAX_STDIN) break;
    }
  } catch (_err) {
    process.exit(0);
  }

  let input = {};
  try { input = JSON.parse(raw); } catch (_err) { process.exit(0); }

  const sessionId = input.session_id || 'unknown';
  const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  // Read masonry.json from cwd for project name + mode
  let masonryMeta = {};
  try {
    const masonryFile = path.join(cwd, 'masonry.json');
    if (fs.existsSync(masonryFile)) {
      masonryMeta = JSON.parse(fs.readFileSync(masonryFile, 'utf8'));
    }
  } catch (_err) { /* optional file */ }

  const project = masonryMeta.name || path.basename(cwd);
  const tempFile = path.join(os.tmpdir(), `masonry-${sessionId}.json`);

  // Check if this is the first call in this session
  let sessionState = null;
  try {
    if (fs.existsSync(tempFile)) {
      sessionState = JSON.parse(fs.readFileSync(tempFile, 'utf8'));
    }
  } catch (_err) { /* fresh session */ }

  // --- Subsequent call: flush pending guard warnings ---
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
          if (messages) {
            process.stdout.write(messages + '\n');
          }
          // Clear the guard queue after flushing
          fs.unlinkSync(guardFile);
        }
      } catch (_err) { /* non-fatal */ }
    }
    process.exit(0);
  }

  // --- First call: hydrate from Recall ---
  // Mark session as started (firstCall = false going forward)
  try {
    fs.writeFileSync(tempFile, JSON.stringify({ project, sessionId, firstCall: false }), 'utf8');
  } catch (_err) { /* non-fatal */ }

  if (!(await isAvailable())) {
    process.exit(0);
  }

  // Check for recent handoff (< 24h)
  const handoffs = await searchMemory({
    query: project,
    tags: ['masonry:handoff'],
    limit: 1,
  });

  if (handoffs.length > 0) {
    const handoff = handoffs[0];
    // Check age — Recall results usually have a timestamp field
    const storedAt = handoff.created_at || handoff.timestamp || handoff.stored_at;
    const ageMs = storedAt ? Date.now() - new Date(storedAt).getTime() : Infinity;
    const isRecent = ageMs < 24 * 60 * 60 * 1000;

    if (isRecent) {
      let payload = null;
      try {
        // content may be a JSON string or already an object
        payload = typeof handoff.content === 'string'
          ? JSON.parse(handoff.content)
          : handoff.content;
      } catch (_err) { /* malformed handoff — fall through */ }

      if (payload && payload.resume_prompt) {
        const lines = [
          `[MASONRY] Resuming campaign for "${project}"`,
          payload.resume_prompt,
        ];

        // Surface recent findings from handoff payload
        if (payload.recent_findings && payload.recent_findings.length > 0) {
          lines.push('\nRecent findings:');
          for (const f of payload.recent_findings) {
            lines.push(`  ${f.qid} — ${f.verdict} (${f.severity}): ${f.summary}`);
          }
        }

        process.stdout.write(lines.join('\n') + '\n');
        process.exit(0);
      }
    }
  }

  // No recent handoff — surface last 5 findings from Recall
  const findings = await searchMemory({
    query: `${project} research findings`,
    tags: [`project:${project}`, 'masonry:finding'],
    limit: 5,
  });

  if (findings.length > 0) {
    const lines = [`[MASONRY] Context for "${project}" — recent findings:`];
    for (const f of findings) {
      const snippet = (f.content || '').slice(0, 150).replace(/\n/g, ' ');
      lines.push(`  • ${snippet}`);
    }
    process.stdout.write(lines.join('\n') + '\n');
  }

  // Log session start
  await storeMemory({
    content: `Masonry session started for project "${project}"`,
    domain: `${project}-autoresearch`,
    tags: ['masonry', `project:${project}`, 'masonry:session-start', `session:${sessionId}`],
    importance: 0.3,
  });

  process.exit(0);
}

main().catch(() => process.exit(0));

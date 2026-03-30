#!/usr/bin/env node
/**
 * SubagentStart hook (Masonry): Track active agent spawns.
 *
 * Writes agent activity to ~/.masonry/state/agents.json (global, not per-project)
 * so the statusline can show live agent count.
 *
 * Also updates masonry-state.json active_agent field when in campaign mode.
 *
 * Replaces OMC's subagent-tracker.mjs
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

const { isMortarGated } = require('./session/mortar-gate');
const { readStdin } = require('./session/stop-utils');

const MAX_TRACKED = 20;
const STALE_MS = 3600_000; // 1 hour — agents older than this are presumed done


function ensureDir(p) {
  try { fs.mkdirSync(p, { recursive: true }); } catch (_) {}
}

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

function safeWrite(p, obj) {
  try { fs.writeFileSync(p, JSON.stringify(obj, null, 2), "utf8"); } catch (_) {}
}

function atomicWrite(p, obj) {
  const tmp = `${p}.tmp.${process.pid}`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(obj, null, 2), "utf8");
    fs.renameSync(tmp, p);
  } catch (_) {
    try { fs.unlinkSync(tmp); } catch (_2) {}
  }
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  // ---------------------------------------------------------------------------
  // Mortar gate check — block bypasses before any tracking work
  // ---------------------------------------------------------------------------
  if (isMortarGated(input)) {
    const subagentType = input.subagent_type || "(none)";
    const agentName = input.agent_name || input.agent_type || "(unknown)";
    process.stderr.write(
      `[masonry-subagent-tracker] BLOCKED: subagent spawn rejected.\n` +
      `  subagent_type="${subagentType}" agent_name="${agentName}"\n` +
      `  All agent spawns must be routed through Mortar first.\n` +
      `  Set subagent_type to a recognized specialist (e.g. "developer", "research-analyst")\n` +
      `  or route your request through Mortar with: Act as the mortar agent defined in .claude/agents/mortar.md\n`
    );
    process.exit(2);
  }

  const cwd = input.cwd || process.cwd();

  // Update Mortar gate file when ANY recognized agent is spawned.
  // The routing-gate PreToolUse hook checks mortar_consulted to decide
  // whether to block Write/Edit operations on production code.
  // Previously this only fired for mortar-type agents; now it fires for all
  // recognized specialists so that direct agent dispatch also clears the gate.
  const subagentType = (input.subagent_type || "").trim().toLowerCase();
  {
    const gateFile = path.join(os.tmpdir(), "masonry-mortar-gate.json");
    try {
      fs.writeFileSync(gateFile, JSON.stringify({
        mortar_consulted: true,
        timestamp: new Date().toISOString(),
        agent: subagentType || input.agent_name || "unknown",
      }), "utf8");
    } catch {}
  }

  // Use ~/.masonry/state/ — global, not per-project
  const stateDir = path.join(os.homedir(), ".masonry", "state");
  ensureDir(stateDir);

  const now = Date.now();
  const agentEntry = {
    id: input.agent_id || `agent-${now}`,
    name: input.agent_name || input.agent_type || "agent",
    model: input.model || "?",
    startedAt: now,
    sessionId: require('./session/stop-utils').getSessionId(input),
  };

  // Load existing agent state
  const stateFile = path.join(stateDir, "agents.json");
  let state = tryJSON(stateFile) || { active: [], history: [] };

  // Prune stale active entries
  state.active = (state.active || []).filter(a => now - (a.startedAt || 0) < STALE_MS);

  // Add new entry
  state.active.push(agentEntry);

  // Trim history
  state.history = state.history || [];
  state.history.push({ ...agentEntry, event: "start" });
  if (state.history.length > MAX_TRACKED) {
    state.history = state.history.slice(-MAX_TRACKED);
  }

  state.updatedAt = now;
  atomicWrite(stateFile, state);

  // Append to routing_log.jsonl for DSPy training signal (Phase 16)
  // request_text: try SubagentStart input fields first (usually empty for programmatic spawns),
  // then fall back to pending slot written by masonry-preagent-tracker.js PreToolUse:Agent hook (F28.3).
  let requestText = (input.prompt || input.description || '').slice(0, 500);
  if (!requestText) {
    try {
      const subagentType = (input.subagent_type || agentEntry.name || '').toLowerCase().trim();
      // Use home-dir path to match masonry-preagent-tracker.js exactly — avoids
      // CWD mismatch when PreToolUse fires in masonry/ but SubagentStart fires in repo root.
      const pendingDir = path.join(os.homedir(), '.masonry', 'pending_agent_prompts');
      const TTL_MS = 10_000; // 10-second freshness window

      // --- UUID-slot read (F-w42.1) ---
      // Glob all files matching {subagent_type}-*.json (new UUID-keyed format).
      // Sort oldest-first by mtime so the slot that was written first (most likely
      // the correct pairing for this SubagentStart) is consumed first.
      let consumed = false;
      try {
        const allFiles = fs.readdirSync(pendingDir);
        const prefix = `${subagentType}-`;
        const candidates = allFiles
          .filter(f => f.startsWith(prefix) && f.endsWith('.json'))
          .map(f => {
            const fullPath = path.join(pendingDir, f);
            let mtimeMs = 0;
            try { mtimeMs = fs.statSync(fullPath).mtimeMs; } catch (_) {}
            return { name: f, fullPath, mtimeMs };
          })
          .filter(c => c.mtimeMs > 0)
          .sort((a, b) => a.mtimeMs - b.mtimeMs); // oldest first

        for (const candidate of candidates) {
          try {
            const slot = JSON.parse(fs.readFileSync(candidate.fullPath, 'utf8'));
            const age = Date.now() - new Date(slot.timestamp).getTime();
            if (slot.request_text && age < TTL_MS) {
              requestText = slot.request_text;
              fs.unlinkSync(candidate.fullPath); // consume the slot
              consumed = true;
              break;
            } else {
              // Stale slot — delete it to avoid accumulation
              try { fs.unlinkSync(candidate.fullPath); } catch (_) {}
            }
          } catch (_) { /* skip unreadable slot file */ }
        }
      } catch (_) { /* readdirSync failed — pendingDir may not exist yet */ }

      // --- Backwards-compat: old _latest.json format (F28.3 era) ---
      // If UUID glob found nothing, fall back to the old single-slot file.
      // This handles stale slots written before the UUID migration and ensures
      // no crash if old-format files exist on disk.
      if (!consumed) {
        const legacyPath = path.join(pendingDir, `${subagentType}_latest.json`);
        if (fs.existsSync(legacyPath)) {
          try {
            const slot = JSON.parse(fs.readFileSync(legacyPath, 'utf8'));
            const age = Date.now() - new Date(slot.timestamp).getTime();
            if (slot.request_text && age < TTL_MS) {
              requestText = slot.request_text;
              fs.unlinkSync(legacyPath); // consume legacy slot
            } else {
              // Expired legacy slot — remove it
              try { fs.unlinkSync(legacyPath); } catch (_) {}
            }
          } catch (_) { /* non-fatal */ }
        }
      }
    } catch (_) { /* non-fatal */ }
  }
  const routingEntry = JSON.stringify({
    timestamp: new Date().toISOString(),
    event: 'start',
    agent: agentEntry.name,
    session_id: agentEntry.sessionId || agentEntry.id,
    parent_session: input.session_id || '',
    request_text: requestText,
  });
  try {
    // Resolve masonry/ dir — cwd might be the masonry dir itself (self-research sessions)
    const masonryDir = path.basename(cwd) === 'masonry' && fs.existsSync(cwd)
      ? cwd
      : path.join(cwd, 'masonry');
    if (fs.existsSync(masonryDir)) {
      const routingLogPath = path.join(masonryDir, 'routing_log.jsonl');
      fs.appendFileSync(routingLogPath, routingEntry + '\n', 'utf8');
    }
  } catch (_err) { /* non-fatal */ }

  // If campaign mode is active, update masonry-state.json active_agent
  const masonryStateFile = path.join(cwd, "masonry-state.json");
  const masonryState = tryJSON(masonryStateFile);
  if (masonryState) {
    masonryState.active_agent = agentEntry.name;
    masonryState.active_agent_count = state.active.length;
    safeWrite(masonryStateFile, masonryState);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

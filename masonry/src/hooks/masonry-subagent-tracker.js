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

const MAX_TRACKED = 20;
const STALE_MS = 3600_000; // 1 hour — agents older than this are presumed done

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

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

  const cwd = input.cwd || process.cwd();
  // Use ~/.masonry/state/ — global, not per-project
  const stateDir = path.join(os.homedir(), ".masonry", "state");
  ensureDir(stateDir);

  const now = Date.now();
  const agentEntry = {
    id: input.agent_id || `agent-${now}`,
    name: input.agent_name || input.agent_type || "agent",
    model: input.model || "?",
    startedAt: now,
    sessionId: input.session_id || "",
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
  const routingEntry = JSON.stringify({
    timestamp: new Date().toISOString(),
    event: 'start',
    agent: agentEntry.name,
    session_id: agentEntry.sessionId || agentEntry.id,
    parent_session: input.session_id || '',
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

#!/usr/bin/env node
/**
 * SessionEnd hook (Masonry): Snapshot active state before session closes.
 *
 * If an autopilot build or UI compose is in progress, writes a session-notes
 * file so the next session's auto-resume logic has context on what was happening.
 * Also cleans up the session snapshot written by masonry-session-start.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

function tryRead(p) {
  try { return fs.readFileSync(p, "utf8").trim(); } catch { return null; }
}

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();
  const { getSessionId, readStdin } = require('./session/stop-utils');
  const sessionId = getSessionId(input);
  const ts = new Date().toISOString();

  // --- Clean up session snapshot ---
  if (sessionId) {
    const snapPath = path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`);
    try { fs.unlinkSync(snapPath); } catch {}
  }

  // --- Release session lock (if owned by this session) ---
  if (sessionId) {
    const lockPath = path.join(cwd, ".mas", "session.lock");
    try {
      if (fs.existsSync(lockPath)) {
        const lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));
        if (lock.session_id === sessionId) {
          fs.unlinkSync(lockPath);
        }
      }
    } catch {}
  }

  // --- Autopilot build state snapshot ---
  const autopilotMode = tryRead(path.join(cwd, ".autopilot", "mode"));
  if (autopilotMode && ["build", "fix", "plan"].includes(autopilotMode)) {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (progress) {
      const pending = (progress.tasks || []).filter(
        (t) => t.status !== "DONE" && t.status !== "BLOCKED"
      );
      const done = (progress.tasks || []).filter((t) => t.status === "DONE").length;
      const total = (progress.tasks || []).length;

      const notes = [
        `# Session Notes — ${ts}`,
        `Session ID: ${sessionId || "unknown"}`,
        `Mode: ${autopilotMode}`,
        `Project: ${progress.project || path.basename(cwd)}`,
        `Progress: ${done}/${total} tasks done`,
        pending.length > 0
          ? `Next task: #${pending[0].id} — ${pending[0].description}`
          : "All tasks complete.",
        ``,
        `## Pending Tasks`,
        ...pending.map((t) => `- #${t.id}: ${t.description} (${t.status})`),
      ].join("\n");

      try {
        fs.writeFileSync(path.join(cwd, ".autopilot", "session-notes.md"), notes, "utf8");
      } catch {}
    }
  }

  // --- UI compose state snapshot ---
  const uiMode = tryRead(path.join(cwd, ".ui", "mode"));
  if (uiMode && ["compose", "fix"].includes(uiMode)) {
    const uiProgress = tryJSON(path.join(cwd, ".ui", "progress.json"));
    if (uiProgress) {
      const pending = (uiProgress.tasks || []).filter((t) => t.status !== "DONE");
      const done = (uiProgress.tasks || []).filter((t) => t.status === "DONE").length;
      const total = (uiProgress.tasks || []).length;

      const notes = [
        `# UI Session Notes — ${ts}`,
        `Session ID: ${sessionId || "unknown"}`,
        `Mode: ${uiMode}`,
        `Project: ${uiProgress.project || path.basename(cwd)}`,
        `Progress: ${done}/${total} components done`,
        pending.length > 0
          ? `Next: ${pending[0].description}`
          : "All components done.",
      ].join("\n");

      try {
        fs.writeFileSync(path.join(cwd, ".ui", "session-notes.md"), notes, "utf8");
      } catch {}
    }
  }


  // --- Agent Trust Scoring ---
  // If the session transcript contains VERIFICATION_REJECT markers, penalize the
  // developer agent's trust score in agent_db.json. VERIFICATION_PASS = small boost.
  try {
    if (sessionId) {
      const slug = cwd.replace(/\\/g, '/').replace(/:/g, '-').replace(/\//g, '-').replace(/\./g, '-');
      const transcriptPath = path.join(os.homedir(), '.claude', 'projects', slug, `${sessionId}.jsonl`);

      if (fs.existsSync(transcriptPath)) {
        const transcript = fs.readFileSync(transcriptPath, 'utf8');
        const rejectCount = (transcript.match(/VERIFICATION_REJECT/g) || []).length;
        const passCount = (transcript.match(/VERIFICATION_PASS/g) || []).length;

        if (rejectCount > 0 || passCount > 0) {
          const agentDbPath = path.join(__dirname, '..', '..', 'masonry', 'agent_db.json');
          let agentDb = {};
          try { agentDb = JSON.parse(fs.readFileSync(agentDbPath, 'utf8')); } catch {}

          // Update developer agent score
          const agentName = 'developer';
          if (!agentDb[agentName]) agentDb[agentName] = { score: 0.7, runs: 0, pass: 0, fail: 0 };
          const agent = agentDb[agentName];
          agent.runs = (agent.runs || 0) + rejectCount + passCount;
          agent.pass = (agent.pass || 0) + passCount;
          agent.fail = (agent.fail || 0) + rejectCount;
          // Bayesian update: score = (pass + 7) / (runs + 10) — prior 0.7 from 10 pseudocounts
          agent.score = Math.round(((agent.pass + 7) / (agent.runs + 10)) * 1000) / 1000;
          agent.last_updated = new Date().toISOString();

          try {
            fs.writeFileSync(agentDbPath, JSON.stringify(agentDb, null, 2), 'utf8');
          } catch {}
        }
      }
    }
  } catch {}

  // --- Rate-limited skill candidate discovery (once per 24h) ---
  const CANDIDATES_LOCK = path.join(MAS_DIR, "skill_discovery_last_run");
  const DISCOVER_SCRIPT = path.join(cwd, "masonry", "scripts", "discover_skill_candidates.py");

  function shouldRunDiscovery() {
    if (!fs.existsSync(CANDIDATES_LOCK)) return true;
    try {
      const last = parseInt(fs.readFileSync(CANDIDATES_LOCK, "utf8").trim(), 10);
      return (Date.now() - last) > 24 * 60 * 60 * 1000;
    } catch { return true; }
  }

  if (fs.existsSync(DISCOVER_SCRIPT) && shouldRunDiscovery()) {
    try {
      spawnSync("python3", [DISCOVER_SCRIPT], {
        cwd,
        encoding: "utf8",
        timeout: 30000,
        env: { ...process.env },
      });
      if (!fs.existsSync(MAS_DIR)) fs.mkdirSync(MAS_DIR, { recursive: true });
      fs.writeFileSync(CANDIDATES_LOCK, String(Date.now()), "utf8");
    } catch {}
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

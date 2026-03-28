"use strict";
// session/project-detect.js — BL project detection, session init, lock, daemon

const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync } = require("child_process");
const { writeJson, initKilnJson } = require("../../core/mas");

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

/**
 * Adds BL project detection, agent state, session lock, daemon auto-start,
 * and context.md injection to lines.
 */
function addProjectContext(lines, cwd, input, state) {
  const { autopilotMode, campaign } = state;

  // --- BL project detection (auto bl-run hint) ---
  const hasProgramMd = fs.existsSync(path.join(cwd, "program.md"));
  const hasQuestionsMd = fs.existsSync(path.join(cwd, "questions.md"));
  const hasActiveCampaign = !!(campaign && campaign.mode);
  const hasActiveAutopilot = !!(autopilotMode && ["build", "fix", "verify"].includes(autopilotMode));

  if (hasProgramMd && hasQuestionsMd && !hasActiveCampaign && !hasActiveAutopilot) {
    try {
      const qText = fs.readFileSync(path.join(cwd, "questions.md"), "utf8");
      const pendingMatches = (qText.match(/\|\s*PENDING\s*\|/gi) || []).length;

      if (pendingMatches > 0) {
        const projectName = path.basename(cwd);
        let blRoot = null;
        {
          let dir = cwd;
          for (let i = 0; i < 10; i++) {
            if (fs.existsSync(path.join(dir, "bl")) && fs.existsSync(path.join(dir, "masonry"))) {
              blRoot = dir;
              break;
            }
            const parent = path.dirname(dir);
            if (parent === dir) break;
            dir = parent;
          }
        }
        const tip = pendingMatches > 10 ? `\n  Tip: ${pendingMatches} questions — parallel workers will finish ~3x faster.` : "";

        const claimsPath = path.join(cwd, "claims.json");
        let activeWorkers = 0;
        if (fs.existsSync(claimsPath)) {
          try {
            const claims = JSON.parse(fs.readFileSync(claimsPath, "utf8"));
            activeWorkers = Object.values(claims).filter(c => c.status === "IN_PROGRESS").length;
          } catch {}
        }

        if (activeWorkers > 0) {
          lines.push(`[BL] ${projectName}: ${pendingMatches} pending, ${activeWorkers} active worker(s) — parallel session may still be running.`);
          if (blRoot) lines.push(`  Check: python ${blRoot}/bl/claim.py status ${cwd}`);
        } else {
          lines.push(`[BL] ${projectName}: ${pendingMatches} questions PENDING — ready to run.${tip}`);
          lines.push(`  Single worker:`);
          lines.push(`    claude --dangerously-skip-permissions "Read program.md and questions.md. Resume the research loop from the first PENDING question. NEVER STOP."`);
          if (blRoot) {
            lines.push(`  Parallel (3x faster):`);
            lines.push(`    cd ${blRoot} && ./bl-parallel.ps1 -Project ${projectName} -Workers 3`);
          }
        }
      }
    } catch {}
  }

  // --- Subagent tracking state ---
  const agentState = tryJSON(path.join(os.homedir(), ".masonry", "state", "agents.json"));
  if (agentState && agentState.active && agentState.active.length > 0) {
    lines.push(`[Masonry] ${agentState.active.length} agent(s) were active at last session: ${agentState.active.map(a => a.name || a.type).join(", ")}.`);
  }

  // --- .mas/ session init + session lock ---
  try {
    const sessionId = input.session_id || input.sessionId || null;
    const sessionObj = {
      session_id: sessionId || "unknown",
      started_at: new Date().toISOString(),
      cwd,
      branch: null,
    };
    try {
      sessionObj.branch = execSync("git branch --show-current", { encoding: "utf8", timeout: 3000, cwd }).trim() || null;
    } catch (_) {}
    writeJson(cwd, "session.json", sessionObj);
    initKilnJson(cwd);

    if (sessionId) {
      const LOCK_STALE_MS = 4 * 60 * 60 * 1000;
      const lockPath = path.join(cwd, ".mas", "session.lock");
      let shouldWriteLock = true;
      try {
        if (fs.existsSync(lockPath)) {
          const existingLock = JSON.parse(fs.readFileSync(lockPath, "utf8"));
          const lockAge = Date.now() - new Date(existingLock.started_at || 0).getTime();
          if (lockAge < LOCK_STALE_MS && existingLock.session_id !== sessionId) {
            shouldWriteLock = false;
            lines.push(
              `[Masonry] \u26a0\ufe0f  Session lock held by session ${existingLock.session_id} ` +
              `(started ${existingLock.started_at}).` +
              ` Protected files (masonry-state.json, questions.md, findings/, .autopilot/) ` +
              `are READ-ONLY for this session. Delete .mas/session.lock to override.`
            );
          }
        }
      } catch (_) {}
      if (shouldWriteLock) {
        try {
          const lockData = { session_id: sessionId, started_at: sessionObj.started_at, cwd, branch: sessionObj.branch };
          fs.mkdirSync(path.join(cwd, ".mas"), { recursive: true });
          fs.writeFileSync(lockPath, JSON.stringify(lockData, null, 2), "utf8");
        } catch (_) {}
      }
    }
  } catch (_) {}

  // --- Daemon auto-start (map + ultralearn workers) ---
  try {
    const projectFiles = fs.readdirSync(cwd).filter(f =>
      ["package.json", "pyproject.toml", "requirements.txt", "masonry", ".claude", "Makefile", "Cargo.toml", "go.mod"].includes(f)
    );
    const isResearchProject = fs.existsSync(path.join(cwd, "program.md")) && fs.existsSync(path.join(cwd, "questions.md"));

    if (projectFiles.length > 0 && !isResearchProject) {
      const DAEMON_DIR = path.join(__dirname, "..", "..", "daemon");
      const PID_DIR = path.join(DAEMON_DIR, "pids");

      for (const workerName of ["map", "ultralearn"]) {
        const pidFile = path.join(PID_DIR, `${workerName}.pid`);
        let isRunning = false;
        try {
          if (fs.existsSync(pidFile)) {
            const pid = parseInt(fs.readFileSync(pidFile, "utf8").trim(), 10);
            if (pid > 0) { try { process.kill(pid, 0); isRunning = true; } catch {} }
          }
        } catch {}

        if (!isRunning) {
          const workerScript = path.join(DAEMON_DIR, `worker-${workerName}.js`);
          if (fs.existsSync(workerScript)) {
            try {
              const { spawn } = require("child_process");
              if (!fs.existsSync(PID_DIR)) fs.mkdirSync(PID_DIR, { recursive: true });
              const logDir = path.join(DAEMON_DIR, "logs");
              if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
              const logStream = fs.openSync(path.join(logDir, `${workerName}.log`), "a");
              const child = spawn("node", [workerScript], {
                detached: true, windowsHide: true, stdio: ["ignore", logStream, logStream], cwd, env: process.env,
              });
              fs.writeFileSync(pidFile, String(child.pid), "utf8");
              child.unref();
            } catch {}
          }
        }
      }
    }
  } catch (_) {}

  // --- Context.md injection ---
  try {
    const ctxPath = path.join(cwd, ".mas", "context.md");
    if (fs.existsSync(ctxPath)) {
      const ctx = fs.readFileSync(ctxPath, "utf8").trim();
      if (ctx) lines.push("[Masonry] Campaign context loaded from .mas/context.md");
    }
  } catch (_) {}
}

module.exports = { addProjectContext };

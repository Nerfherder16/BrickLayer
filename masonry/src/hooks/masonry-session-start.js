#!/usr/bin/env node
/**
 * SessionStart hook (Masonry): Restore workflow context at session start.
 *
 * Reads active mode state files and injects context so Claude knows
 * what was in progress when the session opens.
 *
 * Also snapshots the current dirty file list so the stop-guard can
 * distinguish files modified THIS session from pre-existing dirty files.
 *
 * Replaces OMC's session-start.mjs + project-memory-session
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync } = require("child_process");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 3000);
  });
}

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
  const lines = [];

  // --- Autopilot build state ---
  const autopilotMode = tryRead(path.join(cwd, ".autopilot", "mode"));
  if (autopilotMode && ["build", "fix", "verify"].includes(autopilotMode)) {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (progress) {
      const pending = (progress.tasks || []).filter(t => t.status !== "DONE" && t.status !== "BLOCKED");
      const done = (progress.tasks || []).filter(t => t.status === "DONE").length;
      const total = (progress.tasks || []).length;

      if (pending.length > 0 && (autopilotMode === "build" || autopilotMode === "fix")) {
        // Interrupted build detected — auto-resume by injecting /build into the conversation.
        // Write hookSpecificOutput to stdout so Claude receives it as a prompt directive.
        const resumeMsg = [
          `[Masonry] Interrupted ${autopilotMode} detected: project "${progress.project || "?"}", ${done}/${total} tasks done.`,
          `  Next: #${pending[0].id} — ${pending[0].description}`,
          `  Auto-resuming — run /build to continue.`,
        ].join("\n");
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: "SessionStart",
            content: resumeMsg + "\n\nResume the interrupted build now. Invoke the /build skill to continue from where it left off.",
          },
        }));
        process.exit(0);
      }

      lines.push(`[Masonry] Autopilot ${autopilotMode.toUpperCase()} mode active — project: ${progress.project || "?"}, ${done}/${total} tasks done, ${pending.length} remaining.`);
      if (pending.length > 0) {
        lines.push(`  Next task: #${pending[0].id} — ${pending[0].description}`);
        lines.push(`  Run /build to resume.`);
      }
    } else {
      lines.push(`[Masonry] Autopilot ${autopilotMode.toUpperCase()} mode active. Check .autopilot/ for state.`);
    }
  }

  // --- UI compose state ---
  const uiMode = tryRead(path.join(cwd, ".ui", "mode"));
  if (uiMode && ["compose", "fix", "review"].includes(uiMode)) {
    const uiProgress = tryJSON(path.join(cwd, ".ui", "progress.json"));
    if (uiProgress) {
      const pending = (uiProgress.tasks || []).filter(t => t.status !== "DONE").length;
      lines.push(`[Masonry] UI ${uiMode.toUpperCase()} mode active — ${pending} components pending. Run /ui-compose to resume.`);
    } else {
      lines.push(`[Masonry] UI ${uiMode.toUpperCase()} mode active. Check .ui/ for state.`);
    }
  }

  // --- Campaign state (masonry-state.json) ---
  const campaign = tryJSON(path.join(cwd, "masonry-state.json"));
  if (campaign && campaign.mode) {
    lines.push(`[Masonry] Campaign active — ${campaign.project || path.basename(cwd)}: wave ${campaign.wave || 0}, Q${campaign.q_current || 0}/${campaign.q_total || 0}, mode: ${campaign.mode}.`);
  }

  // --- Subagent tracking state (global ~/.masonry/state/) ---
  const agentState = tryJSON(path.join(os.homedir(), ".masonry", "state", "agents.json"));
  if (agentState && agentState.active && agentState.active.length > 0) {
    lines.push(`[Masonry] ${agentState.active.length} agent(s) were active at last session: ${agentState.active.map(a => a.name || a.type).join(", ")}.`);
  }

  if (lines.length > 0) {
    process.stderr.write("\n" + lines.join("\n") + "\n\n");
  }

  // --- Session snapshot for stop-guard dirty-file diffing ---
  // Capture which files are already dirty at session open so the stop-guard
  // can ignore them and only flag files modified THIS session.
  const sessionId = input.session_id || input.sessionId || null;
  if (sessionId) {
    try {
      const status = execSync("git status --porcelain", {
        encoding: "utf8",
        timeout: 5000,
        cwd,
      }).trim();
      const preExisting = status
        ? status.split("\n").filter(Boolean).map((l) => l.slice(3).trim())
        : [];
      const snapPath = path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`);
      fs.writeFileSync(snapPath, JSON.stringify({ sessionId, cwd, preExisting }), "utf8");
    } catch {
      // Non-git dir or git unavailable — skip snapshot silently
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

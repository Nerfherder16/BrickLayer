"use strict";
// session/build-state.js — Autopilot/UI/campaign/Karen state injection

const fs = require("fs");
const path = require("path");

function tryRead(p) {
  try { return fs.readFileSync(p, "utf8").trim(); } catch { return null; }
}
function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

/**
 * Adds autopilot, UI compose, campaign, and Karen maintenance context to lines.
 * Populates state.autopilotMode, state.uiMode, state.campaign.
 * Sets state.earlyExit = true when an interrupted build is detected and the
 * systemMessage has been written — caller should skip remaining phases.
 */
function addBuildState(lines, cwd, state) {
  // --- Autopilot build state ---
  const autopilotMode = tryRead(path.join(cwd, ".autopilot", "mode"));
  state.autopilotMode = autopilotMode;

  if (autopilotMode && ["build", "fix", "verify"].includes(autopilotMode)) {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (progress) {
      const pending = (progress.tasks || []).filter(t => t.status !== "DONE" && t.status !== "BLOCKED");
      const done = (progress.tasks || []).filter(t => t.status === "DONE").length;
      const total = (progress.tasks || []).length;

      if (pending.length > 0 && (autopilotMode === "build" || autopilotMode === "fix")) {
        const resumeMsg = [
          `[Masonry] Interrupted ${autopilotMode} detected: project "${progress.project || "?"}", ${done}/${total} tasks done.`,
          `  Next: #${pending[0].id} — ${pending[0].description}`,
          `  Auto-resuming — run /build to continue.`,
        ].join("\n");
        process.stdout.write(JSON.stringify({
          systemMessage: resumeMsg + "\n\nResume the interrupted build now. Invoke the /build skill to continue from where it left off.",
        }));
        state.earlyExit = true;
        return;
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
  state.uiMode = uiMode;
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
  state.campaign = campaign;
  if (campaign && campaign.mode) {
    lines.push(`[Masonry] Campaign active — ${campaign.project || path.basename(cwd)}: wave ${campaign.wave || 0}, Q${campaign.q_current || 0}/${campaign.q_total || 0}, mode: ${campaign.mode}.`);
  }

  // --- Karen doc maintenance flag ---
  try {
    const karenFlagPaths = [
      path.join(cwd, ".autopilot", "karen-needed.json"),
      path.join(cwd, ".mas", "karen-needed.json"),
    ];
    for (const karenFlagPath of karenFlagPaths) {
      if (fs.existsSync(karenFlagPath)) {
        const flag = JSON.parse(fs.readFileSync(karenFlagPath, "utf8"));
        const staleList = (flag.stale_files || []).join(", ");
        lines.push(
          `[Masonry] Doc maintenance needed. Spawn karen: Act as the karen agent in ~/.claude/agents/karen.md. ` +
          `Update and commit these stale project docs: ${staleList}. Do this before any other work.`
        );
        try { fs.unlinkSync(karenFlagPath); } catch (_) {}
        break;
      }
    }
  } catch (_) {}
}

module.exports = { addBuildState };

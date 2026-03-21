#!/usr/bin/env node
/**
 * PreCompact hook (Masonry): Preserve active workflow state before context compaction.
 *
 * When Claude compacts context, the active task details can be lost from working
 * memory. This hook writes a compact state summary to a known path so the
 * session-start hook can re-inject it after compaction completes.
 *
 * Output: hookSpecificOutput with a brief state reminder that survives compaction.
 */

"use strict";
const fs = require("fs");
const path = require("path");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
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
  if (autopilotMode && ["build", "fix"].includes(autopilotMode)) {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (progress) {
      const pending = (progress.tasks || []).filter(
        (t) => t.status !== "DONE" && t.status !== "BLOCKED"
      );
      const done = (progress.tasks || []).filter((t) => t.status === "DONE").length;
      const total = (progress.tasks || []).length;

      lines.push(`[Masonry] COMPACTING — ${autopilotMode.toUpperCase()} mode preserved.`);
      lines.push(`  Project: ${progress.project || path.basename(cwd)}, ${done}/${total} tasks done.`);
      if (pending.length > 0) {
        lines.push(`  After compact, resume from task #${pending[0].id}: ${pending[0].description}`);
        lines.push(`  Run /masonry-build to continue.`);
      }

      // Write a compact-state file that survives the compaction
      const compactState = {
        mode: autopilotMode,
        project: progress.project || path.basename(cwd),
        done,
        total,
        nextTask: pending.length > 0 ? pending[0] : null,
        compactedAt: new Date().toISOString(),
      };
      try {
        fs.writeFileSync(
          path.join(cwd, ".autopilot", "compact-state.json"),
          JSON.stringify(compactState, null, 2),
          "utf8"
        );
      } catch {}
    }
  }

  // --- UI compose state ---
  const uiMode = tryRead(path.join(cwd, ".ui", "mode"));
  if (uiMode && ["compose", "fix"].includes(uiMode)) {
    const uiProgress = tryJSON(path.join(cwd, ".ui", "progress.json"));
    if (uiProgress) {
      const pending = (uiProgress.tasks || []).filter((t) => t.status !== "DONE");
      const done = (uiProgress.tasks || []).filter((t) => t.status === "DONE").length;
      const total = (uiProgress.tasks || []).length;

      lines.push(`[Masonry] COMPACTING — UI ${uiMode.toUpperCase()} preserved.`);
      lines.push(`  ${done}/${total} components done.`);
      if (pending.length > 0) {
        lines.push(`  After compact, resume: /ui-compose (next: ${pending[0].description})`);
      }
    }
  }

  // --- Campaign state ---
  const campaign = tryJSON(path.join(cwd, "masonry-state.json"));
  if (campaign && campaign.mode) {
    lines.push(`[Masonry] COMPACTING — campaign state preserved.`);
    lines.push(`  ${campaign.project || path.basename(cwd)}: wave ${campaign.wave || 0}, Q${campaign.q_current || 0}/${campaign.q_total || 0}`);
  }

  if (lines.length > 0) {
    // Inject state reminder into the compacted summary
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreCompact",
          content: lines.join("\n"),
        },
      })
    );
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

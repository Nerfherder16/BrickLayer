#!/usr/bin/env node
/**
 * PreCompact hook (Masonry): Preserve active workflow state before context compaction.
 *
 * When Claude compacts context, the active task details can be lost from working
 * memory. This hook writes a compact state summary to a known path so the
 * session-start hook can re-inject it after compaction completes.
 *
 * v2: Stores mid-session checkpoint to Recall including both user prompts AND
 * assistant responses. Fills the gap for long-running sessions that never close.
 * v3: Writes discrete snapshot files (.autopilot/pre-compact-snapshot.json,
 * masonry/pre-compact-campaign.json) and appends to build.log on pre-compact.
 *
 * Output: hookSpecificOutput with a brief state reminder that survives compaction.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const { storeRecallCheckpoint } = require("../pre-compact-recall");

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

/** Save .autopilot/pre-compact-snapshot.json and append to build.log. */
function saveBuildSnapshot(cwd, progress, total, lines) {
  try {
    const snapshot = { ...progress, snapshot_at: new Date().toISOString() };
    fs.mkdirSync(path.join(cwd, ".autopilot"), { recursive: true });
    fs.writeFileSync(
      path.join(cwd, ".autopilot", "pre-compact-snapshot.json"),
      JSON.stringify(snapshot, null, 2),
      "utf8"
    );
    lines.push(`PRE_COMPACT BUILD: snapshot saved to .autopilot/pre-compact-snapshot.json`);
  } catch {}

  try {
    const buildLogPath = path.join(cwd, ".autopilot", "build.log");
    const firstNonDone = (progress.tasks || []).find(
      (t) => t.status !== "DONE" && t.status !== "BLOCKED"
    );
    const taskStatus = firstNonDone
      ? `Task ${firstNonDone.id} of ${total} (${firstNonDone.status})`
      : "All tasks done";
    const logLine = `[${new Date().toISOString()}] PRE_COMPACT: Snapshot saved. ${taskStatus}. Resume with /build.\n`;
    if (fs.existsSync(buildLogPath)) {
      fs.appendFileSync(buildLogPath, logLine, "utf8");
    }
  } catch {}
}

/** Save masonry/pre-compact-campaign.json for active campaign state. */
function saveCampaignSnapshot(cwd, campaign, lines) {
  try {
    const snapshot = {
      saved_at: new Date().toISOString(),
      current_question_id: campaign.q_current || null,
      wave: campaign.wave || 0,
      project_dir: cwd,
    };
    fs.mkdirSync(path.join(cwd, "masonry"), { recursive: true });
    fs.writeFileSync(
      path.join(cwd, "masonry", "pre-compact-campaign.json"),
      JSON.stringify(snapshot, null, 2),
      "utf8"
    );
    lines.push(`PRE_COMPACT CAMPAIGN: snapshot saved to masonry/pre-compact-campaign.json`);
  } catch {}
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
    const compactState = tryJSON(path.join(cwd, ".autopilot", "compact-state.json"));

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

      // Update compact-state (preserve auto_build flag if set)
      const updatedState = {
        ...(compactState || {}),
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
          JSON.stringify(updatedState, null, 2),
          "utf8"
        );
      } catch {}

      saveBuildSnapshot(cwd, progress, total, lines);
    } else if (compactState && compactState.auto_build) {
      // Plan approved but build not yet started — no progress.json.
      lines.push(`[Masonry] COMPACTING — spec approved, build pending.`);
      lines.push(`  Spec: ${compactState.spec || ".autopilot/spec.md"}`);
      lines.push(`  After compact, run /masonry-build to start the build.`);
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

  // --- Swarm inflight task persistence ---
  // Save IN_PROGRESS tasks (with claimed_by) to .autopilot/inflight-agents.json.
  // masonry-session-start.js reads this on resume to warn about orphaned workers.
  {
    const swarmProgress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (swarmProgress) {
      const inflightTasks = (swarmProgress.tasks || []).filter(
        (t) => t.status === "IN_PROGRESS"
      );
      if (inflightTasks.length > 0) {
        const inflightPayload = {
          saved_at: new Date().toISOString(),
          tasks: inflightTasks.map((t) => ({
            id: t.id,
            description: t.description || "",
            claimed_by: t.claimed_by || null,
            status: t.status,
          })),
        };
        try {
          fs.mkdirSync(path.join(cwd, ".autopilot"), { recursive: true });
          fs.writeFileSync(
            path.join(cwd, ".autopilot", "inflight-agents.json"),
            JSON.stringify(inflightPayload, null, 2),
            "utf8"
          );
        } catch {}
        lines.push(
          `[Masonry] Swarm in progress: ${inflightTasks.length} task(s) IN_PROGRESS — agent IDs saved to .autopilot/inflight-agents.json`
        );
        for (const t of inflightTasks) {
          const worker = t.claimed_by ? t.claimed_by : "unknown-worker";
          lines.push(`  Task #${t.id} (${worker}): ${t.description || ""}`);
        }
      }
    }
  }

  // --- Campaign state ---
  const campaign = tryJSON(path.join(cwd, "masonry-state.json"));
  if (campaign && campaign.mode) {
    lines.push(`[Masonry] COMPACTING — campaign state preserved.`);
    lines.push(`  ${campaign.project || path.basename(cwd)}: wave ${campaign.wave || 0}, Q${campaign.q_current || 0}/${campaign.q_total || 0}`);
    saveCampaignSnapshot(cwd, campaign, lines);
  }

  if (lines.length > 0) {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreCompact",
          content: lines.join("\n"),
        },
      })
    );
  }

  // --- Recall: store mid-session checkpoint with assistant responses ---
  await storeRecallCheckpoint(cwd, input.session_id);
}

main().catch(() => {});

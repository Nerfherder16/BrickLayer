#!/usr/bin/env node
/**
 * PostCompact hook (Masonry): Re-inject active workflow state after context compaction.
 *
 * Reads the snapshots written by masonry-pre-compact.js and emits a systemMessage
 * so Claude knows exactly where to resume after the context window was compacted.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const { readStdin } = require('./session/stop-utils');

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
  const compactState = tryJSON(path.join(cwd, ".autopilot", "compact-state.json"));
  const progress = tryJSON(path.join(cwd, ".autopilot", "pre-compact-snapshot.json"));

  if (compactState && compactState.mode) {
    // Safety-net: don't inject stale "resume build" if the build already completed
    const liveProgress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    const buildAlreadyComplete = liveProgress && liveProgress.status === "COMPLETE";
    if (!buildAlreadyComplete) {
      lines.push(`[Masonry] RESUMED after compaction — ${compactState.mode.toUpperCase()} mode.`);
      lines.push(`  Project: ${compactState.project || path.basename(cwd)}, ${compactState.done || 0}/${compactState.total || 0} tasks done.`);
      if (compactState.nextTask) {
        lines.push(`  Next task #${compactState.nextTask.id}: ${compactState.nextTask.description}`);
        lines.push(`  Run /masonry-build to continue.`);
        // Imperative sentence triggers Claude to auto-invoke /build (same pattern as build-state.js SessionStart)
        lines.push(`\nResume the interrupted build now. Invoke the /build skill to continue from where it left off.`);
      } else if (compactState.auto_build) {
        lines.push(`  Spec approved — starting build now.`);
        lines.push(`\nStart the build now. Invoke the /build skill to begin executing the spec.`);
      }
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
      lines.push(`[Masonry] RESUMED — UI ${uiMode.toUpperCase()} active. ${done}/${total} components done.`);
      if (pending.length > 0) {
        lines.push(`  Resume: /ui-compose (next: ${pending[0].description})`);
      }
    }
  }

  // --- Swarm inflight agents ---
  const inflight = tryJSON(path.join(cwd, ".autopilot", "inflight-agents.json"));
  if (inflight && inflight.tasks && inflight.tasks.length > 0) {
    lines.push(`[Masonry] WARNING: ${inflight.tasks.length} task(s) were IN_PROGRESS at compaction time:`);
    for (const t of inflight.tasks) {
      const worker = t.claimed_by ? t.claimed_by : "unknown-worker";
      lines.push(`  Task #${t.id} (${worker}): ${t.description || ""}`);
    }
    lines.push(`  These workers may have orphaned — check progress.json before continuing.`);
  }

  // --- Campaign state ---
  const campaign = tryJSON(path.join(cwd, "masonry", "pre-compact-campaign.json"));
  if (campaign && campaign.current_question_id !== undefined) {
    lines.push(`[Masonry] RESUMED — campaign state.`);
    lines.push(`  Wave ${campaign.wave || 0}, last question: Q${campaign.current_question_id}`);
    lines.push(`  Project: ${campaign.project_dir || cwd}`);
  }

  // --- Session activity breadcrumb (restores conversational work context) ---
  const workSnapshot = tryJSON(path.join(cwd, ".autopilot", "pre-compact-work.json"));
  if (workSnapshot && Array.isArray(workSnapshot.recent_edits) && workSnapshot.recent_edits.length > 0) {
    const edits = workSnapshot.recent_edits;
    lines.push(
      `[Masonry] Resuming after compaction — last session edited ${workSnapshot.total_edits || edits.length} file(s).`,
      `  Recent: ${edits.slice(-8).join(" → ")}`
    );
  }

  if (lines.length > 0) {
    process.stdout.write(
      JSON.stringify({
        systemMessage: lines.join("\n"),
      })
    );
  }
}

main().catch(() => {});

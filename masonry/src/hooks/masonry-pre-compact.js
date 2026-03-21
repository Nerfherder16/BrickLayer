#!/usr/bin/env node
/**
 * PreCompact hook (Masonry): Preserve active workflow state before context compaction.
 *
 * When Claude compacts context, the active task details can be lost from working
 * memory. This hook writes a compact state summary to a known path so the
 * session-start hook can re-inject it after compaction completes.
 *
 * v2: Also reads transcript_path to store a mid-session checkpoint to Recall that
 * includes both user prompts AND assistant responses — the only mid-session hook
 * that has transcript access. Fills the gap for long-running sessions that never close.
 *
 * Output: hookSpecificOutput with a brief state reminder that survives compaction.
 */

"use strict";
const fs = require("fs");
const path = require("path");

const RECALL_HOST = process.env.RECALL_HOST || "http://100.70.195.84:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "recall-admin-key-change-me";
const MAX_TRANSCRIPT_LINES = 100; // scan last 100 JSONL lines for recent turns

// Project → canonical domain (matches recall-retrieve.js)
const PROJECT_DOMAINS = {
  "recall": "recall", "system-recall": "recall",
  "familyhub": "family-hub", "family-hub": "family-hub", "sadie": "family-hub",
  "relay": "relay", "codevv": "codevv", "foundry": "foundry",
  "media-server": "media-server", "jellyfin": "media-server", "homelab": "homelab",
};

/**
 * Extract recent conversation turns (user + assistant) from the JSONL transcript.
 */
function extractRecentTurns(transcriptPath, maxMessages) {
  try {
    const content = fs.readFileSync(transcriptPath, "utf8");
    const lines = content.trim().split("\n").slice(-MAX_TRANSCRIPT_LINES);
    const turns = [];
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        const isUser = entry.type === "human" || entry.type === "user";
        const isAssistant = entry.type === "assistant";
        if (!isUser && !isAssistant) continue;
        const raw = entry.message?.content ?? entry.content;
        const text = typeof raw === "string" ? raw
          : Array.isArray(raw)
            ? raw.filter((c) => c.type === "text").map((c) => c.text).join(" ")
            : "";
        if (!text || text.length < 5) continue;
        turns.push({ role: isUser ? "User" : "Assistant", text: text.slice(0, 400) });
      } catch {}
    }
    return turns.slice(-maxMessages);
  } catch {
    return [];
  }
}

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

  // --- Recall: store mid-session checkpoint with assistant responses ---
  const transcriptPath = input.transcript_path;
  const projectName = path.basename(cwd);
  const domain = PROJECT_DOMAINS[projectName.toLowerCase()] || projectName.toLowerCase() || "general";

  if (transcriptPath) {
    const turns = extractRecentTurns(transcriptPath, 20);
    // Only store if we have meaningful content (at least 1 assistant turn)
    const hasAssistant = turns.some((t) => t.role === "Assistant");
    if (turns.length >= 3 && hasAssistant) {
      const turnText = turns
        .map((t) => `[${t.role}] ${t.text}`)
        .join("\n");

      const content = [
        `[PreCompact Checkpoint] ${projectName} — ${turns.length} turns captured at context compaction (${new Date().toISOString().slice(0, 16)})`,
        turnText,
      ].join("\n\n");

      const headers = {
        "Content-Type": "application/json",
        ...(RECALL_API_KEY ? { Authorization: `Bearer ${RECALL_API_KEY}` } : {}),
      };

      try {
        await fetch(`${RECALL_HOST}/memory/store`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            content: content.slice(0, 4000),
            domain,
            source: "system",
            memory_type: "episodic",
            tags: ["precompact-checkpoint", projectName, "has-assistant-responses"],
            importance: 0.65,
          }),
          signal: AbortSignal.timeout(4000),
        });
      } catch { /* Recall down — never block compaction */ }
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

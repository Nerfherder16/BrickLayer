#!/usr/bin/env node
/**
 * PreToolUse hook (Masonry): Context safety guard on ExitPlanMode.
 *
 * Blocks ExitPlanMode when:
 * - An active autopilot build is running (.autopilot/mode = build)
 * - OR context window usage is critically high (>= 80%)
 *
 * Replaces OMC's context-safety.mjs
 */

"use strict";
const fs = require("fs");
const path = require("path");

const HIGH_CONTEXT_PCT = 80; // block ExitPlanMode above this threshold

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

/**
 * Estimate context usage by reading the last portion of the transcript file.
 * Falls back to 0 if unavailable.
 */
function estimateContextPct(transcriptPath) {
  if (!transcriptPath) return 0;
  try {
    const stat = fs.statSync(transcriptPath);
    const readBytes = Math.min(8192, stat.size);
    const offset = Math.max(0, stat.size - readBytes);
    const buf = Buffer.alloc(readBytes);
    const fd = fs.openSync(transcriptPath, "r");
    const bytesRead = fs.readSync(fd, buf, 0, readBytes, offset);
    fs.closeSync(fd);
    const tail = buf.slice(0, bytesRead).toString("utf8");

    // Look for context usage in recent JSONL entries
    const lines = tail.split("\n").filter(l => l.trim().startsWith("{"));
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const obj = JSON.parse(lines[i]);
        // Claude Code encodes context window info in some event types
        if (obj.context_window?.used_percentage != null) {
          return Math.round(obj.context_window.used_percentage);
        }
        if (obj.usage?.input_tokens != null && obj.usage?.context_window != null) {
          return Math.round((obj.usage.input_tokens / obj.usage.context_window) * 100);
        }
      } catch { /* keep scanning */ }
    }
  } catch (_) {}
  return 0;
}

async function main() {
  // Kill switch: disable all Masonry hooks when running BrickLayer in subprocess mode
  if (process.env.DISABLE_OMC === '1' || process.env.DISABLE_MASONRY_HOOKS === '1') {
    process.exit(0);
  }

  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  // Only care about ExitPlanMode
  if (input.tool_name !== "ExitPlanMode") process.exit(0);

  const cwd = input.cwd || process.cwd();
  const reasons = [];

  // Check 1: active build running
  const autopilotMode = tryRead(path.join(cwd, ".autopilot", "mode"));
  if (autopilotMode === "build") {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    const inFlight = (progress?.tasks || []).find(t => t.status === "IN_PROGRESS");
    if (inFlight) {
      reasons.push(`Autopilot build is IN_PROGRESS (task: ${inFlight.description}). Exiting plan mode mid-build may lose context.`);
    }
  }

  // Check 2: context usage
  const transcriptPath = input.transcript_path;
  const ctxPct = estimateContextPct(transcriptPath);
  if (ctxPct >= HIGH_CONTEXT_PCT) {
    reasons.push(`Context window is at ${ctxPct}% — critically high. Exiting plan mode now risks losing the planning context needed to complete this work. Consider finishing the current task first or using /handoff.`);
  }

  if (reasons.length > 0) {
    const msg = `[Masonry] Context Safety: ExitPlanMode blocked.\n${reasons.map(r => `  • ${r}`).join("\n")}\n\nTo override, proceed with explicit intent.`;
    process.stdout.write(JSON.stringify({ action: "block", reason: msg }));
    process.exit(2);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

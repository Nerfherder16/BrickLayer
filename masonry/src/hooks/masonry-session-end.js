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
  const sessionId = input.session_id || input.sessionId || null;
  const ts = new Date().toISOString();

  // --- Clean up session snapshot ---
  if (sessionId) {
    const snapPath = path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`);
    try { fs.unlinkSync(snapPath); } catch {}
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

  process.exit(0);
}

main().catch(() => process.exit(0));
# hook test

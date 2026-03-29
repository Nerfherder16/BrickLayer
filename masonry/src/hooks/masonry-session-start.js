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
 * Modules:
 *   session/build-state.js    — autopilot/UI/campaign/karen state
 *   session/project-detect.js — BL detection, session lock, daemon
 *   session/context-data.js   — Recall, codebase map, ReasoningBank, skills
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync } = require("child_process");

const { addBuildState } = require("./session/build-state");
const { addProjectContext } = require("./session/project-detect");
const { addContextData } = require("./session/context-data");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 3000);
  });
}

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, "program.md")) &&
         fs.existsSync(path.join(dir, "questions.md"));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();
  const lines = [];
  const state = {}; // shared: autopilotMode, uiMode, campaign

  // Phase 1: Build / UI / campaign / Karen state (may exit early for interrupted build)
  addBuildState(lines, cwd, state);

  // Phase 2: BL project detection, session init, lock, daemon
  addProjectContext(lines, cwd, input, state);

  // Phase 3: Recall patterns, codebase map, swarm resume, ReasoningBank, skills
  await addContextData(lines, cwd, state);

  // Phase 4: Hot path context — most-edited files this project
  try {
    const { injectContext } = require('./session/hotpaths');
    const hotContext = injectContext(cwd);
    if (hotContext) lines.push(hotContext);
  } catch {}

  // Phase 5: Dead reference audit — warn on stale tool/agent references
  try {
    const { scanAll, formatWarnings } = require('./session/dead-refs');
    const globalAgents = path.join(os.homedir(), '.claude', 'agents');
    const warnings = formatWarnings(scanAll(cwd, globalAgents));
    if (warnings) process.stderr.write(warnings + '\n');
  } catch {}

  if (lines.length > 0) {
    process.stdout.write(JSON.stringify({
      systemMessage: lines.join("\n"),
    }));
  }

  // --- Session snapshot for stop-guard dirty-file diffing ---
  // Use real session_id when available; fall back to a stable per-process ID so the
  // activity log (masonry-observe.js) and stop-guard use the same key even when
  // Claude Code doesn't include session_id in the SessionStart payload.
  const sessionId = input.session_id || input.sessionId || `session-${process.ppid || Date.now()}`;
  try {
    const status = execSync("git status --porcelain", { encoding: "utf8", timeout: 5000, cwd }).trim();
    const preExisting = status
      ? status.split("\n").filter(Boolean).map((l) => l.slice(3).trim())
      : [];
    fs.writeFileSync(
      path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`),
      JSON.stringify({ sessionId, cwd, preExisting }),
      "utf8"
    );
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

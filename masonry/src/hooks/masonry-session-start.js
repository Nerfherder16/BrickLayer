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
const { getSkillsDirective } = require("./session/skills-directive");
const { getDriftSummary } = require("./session/drift-inject");

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, "program.md")) &&
         fs.existsSync(path.join(dir, "questions.md"));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) return;

  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();
  const lines = [];
  const state = {}; // shared: autopilotMode, uiMode, campaign

  // Phase 0: Orchestrator role priming — Claude is an orchestrator, not a solo developer.
  // This must be the FIRST line so Claude sees it before any state context.
  lines.push(
    "[Masonry] You are an orchestrator. For any task requiring Write, Edit, or Bash, " +
    "route through Mortar first (subagent_type: \"mortar\"). Mortar dispatches specialist agents " +
    "(developer, test-writer, code-reviewer) in parallel. Direct inline coding skips code review " +
    "and TDD enforcement. Exception: single-sentence factual lookups and clarification questions."
  );

  // Phase 0.5: Superpowers skill-check directive (skipped on resume)
  const isResume = input.startup_type === 'resume' || input.is_resume === true;
  const skillsDirective = getSkillsDirective(input);
  if (skillsDirective) lines.push(skillsDirective);

  // Phase 0.6: Drift summary from last build (skipped on resume)
  if (!isResume) {
    const driftSummary = getDriftSummary(cwd);
    if (driftSummary) lines.push(driftSummary);
  }

  // Phase 0.7: Auto-start brainstorm server if not running (skipped on resume)
  if (!isResume) {
    try {
      const { autoStartBrainstorm } = require('./session/brainstorm-autostart');
      await autoStartBrainstorm(cwd);
    } catch {}
  }

  // Phase 1: Build / UI / campaign / Karen state (may set earlyExit for interrupted build)
  addBuildState(lines, cwd, state);
  if (state.earlyExit) return; // systemMessage already written by build-state

  // Phase 2: BL project detection, session init, lock, daemon
  addProjectContext(lines, cwd, input, state);

  // Phase 3: Recall patterns, codebase map, swarm resume, ReasoningBank, skills
  // Gate behind active state — skip expensive HTTP/subprocess calls for plain sessions
  const hasActiveProject = state.autopilotMode || state.campaign || state.uiMode;
  if (hasActiveProject) {
    await addContextData(lines, cwd, state);
  }

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
  const { getSessionId, readStdin } = require('./session/stop-utils');
  const sessionId = getSessionId(input);
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

}

main().catch(() => {});

#!/usr/bin/env node
/**
 * PreToolUse:Agent hook (Masonry): Telemetry — fires when Claude spawns an agent sub-task.
 *
 * Writes a JSONL record to .autopilot/telemetry.jsonl and stores the current
 * task_id in .autopilot/current-task-id for the paired masonry-post-task.js hook.
 *
 * Skips silently for BrickLayer research projects (program.md + questions.md).
 * Skips silently if no .autopilot/ directory is found.
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

function isResearchProject(dir) {
  return (
    fs.existsSync(path.join(dir, "program.md")) &&
    fs.existsSync(path.join(dir, "questions.md"))
  );
}

function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    const candidate = path.join(dir, ".autopilot");
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function estimateTaskType(prompt) {
  const p = prompt.toLowerCase();
  if (/frontend|react|tsx|component|ui|css/.test(p)) return "frontend";
  if (/test|spec|pytest|vitest/.test(p)) return "test";
  if (/fix|bug|error|fail/.test(p)) return "fix";
  if (/data|database|sql|migration|schema/.test(p)) return "data";
  if (/config|setting|env|yaml|json/.test(p)) return "config";
  return "backend";
}

function estimateComplexity(prompt) {
  if (prompt.length < 200) return "low";
  if (prompt.length < 600) return "medium";
  return "high";
}

async function main() {
  const raw = await readStdin();
  let parsed = {};
  try { parsed = JSON.parse(raw); } catch { process.exit(0); }

  const cwd = parsed.cwd || process.env.PWD || process.cwd();

  // Silent in BrickLayer research projects
  if (isResearchProject(cwd)) process.exit(0);

  const autopilotDir = findAutopilotDir(cwd);
  if (!autopilotDir) process.exit(0);

  const task_id = "t-" + Date.now();
  const prompt = (parsed.tool_input && parsed.tool_input.prompt) ? parsed.tool_input.prompt : "";
  const task_type = estimateTaskType(prompt);
  const complexity = estimateComplexity(prompt);
  const agent_type = (parsed.tool_input && parsed.tool_input.subagent_type) || "general-purpose";

  const record = JSON.stringify({
    task_id,
    phase: "pre",
    timestamp: new Date().toISOString(),
    agent_type,
    task_type,
    complexity,
  });

  try {
    fs.appendFileSync(path.join(autopilotDir, "telemetry.jsonl"), record + "\n", "utf8");
  } catch (_) { /* non-fatal */ }

  try {
    fs.writeFileSync(path.join(autopilotDir, "current-task-id"), task_id, "utf8");
  } catch (_) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

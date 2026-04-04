#!/usr/bin/env node
/**
 * PostToolUse:Agent hook (Masonry): Telemetry — fires when a Claude agent sub-task completes.
 *
 * Reads the task_id written by masonry-pre-task.js, computes duration from the
 * pre-phase record in telemetry.jsonl, and appends a post-phase record.
 *
 * Skips silently for BrickLayer research projects (program.md + questions.md).
 * Skips silently if no .autopilot/ directory or current-task-id file is found.
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

async function main() {
  const raw = await readStdin();
  let parsed = {};
  try { parsed = JSON.parse(raw); } catch { process.exit(0); }

  const cwd = parsed.cwd || process.env.PWD || process.cwd();

  // Silent in BrickLayer research projects
  if (isResearchProject(cwd)) process.exit(0);

  const autopilotDir = findAutopilotDir(cwd);
  if (!autopilotDir) process.exit(0);

  // Read the task_id written by the pre hook
  const taskIdFile = path.join(autopilotDir, "current-task-id");
  if (!fs.existsSync(taskIdFile)) process.exit(0);
  let task_id;
  try {
    task_id = fs.readFileSync(taskIdFile, "utf8").trim();
  } catch { process.exit(0); }
  if (!task_id) process.exit(0);

  // Read telemetry.jsonl to find the pre-phase record and compute duration
  let duration_ms = null;
  const telemetryFile = path.join(autopilotDir, "telemetry.jsonl");
  try {
    if (fs.existsSync(telemetryFile)) {
      const lines = fs.readFileSync(telemetryFile, "utf8").split("\n");
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const entry = JSON.parse(line);
          if (entry.task_id === task_id && entry.phase === "pre") {
            duration_ms = Date.now() - Date.parse(entry.timestamp);
            break;
          }
        } catch { /* skip malformed lines */ }
      }
    }
  } catch { /* non-fatal */ }

  // Determine success from tool_result
  const resultStr = JSON.stringify(parsed.tool_result || "");
  const success = !/ERROR|FAILED|DEV_ESCALATE/.test(resultStr);

  const agent = (parsed.tool_input && parsed.tool_input.subagent_type) || "unknown";

  const record = JSON.stringify({
    task_id,
    phase: "post",
    timestamp: new Date().toISOString(),
    duration_ms,
    success,
    agent,
  });

  try {
    fs.appendFileSync(telemetryFile, record + "\n", "utf8");
  } catch (_) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

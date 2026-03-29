#!/usr/bin/env node
/**
 * SubagentStop hook (Masonry): Dependency-unblocking via task completion signaling.
 *
 * Fires when a subagent stops (SubagentStop) or when an Agent tool call completes
 * (PostToolUse/Agent). Writes a result cache to .autopilot/results/{agent_id}.json
 * and unblocks any progress.json tasks whose depends_on task IDs are all now DONE.
 *
 * depends_on uses task IDs (integers), not agent IDs. When a task transitions to DONE,
 * this hook scans for BLOCKED tasks and promotes them to PENDING if all their upstream
 * task IDs are in the DONE set.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { readStdin } = require('./session/stop-utils');

function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    const autopilotDir = path.join(dir, ".autopilot");
    if (fs.existsSync(autopilotDir)) return autopilotDir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function isResearchProject(dir) {
  return (
    fs.existsSync(path.join(dir, "program.md")) &&
    fs.existsSync(path.join(dir, "questions.md"))
  );
}

async function main() {
  const raw = await readStdin();
  let parsed = {};
  try {
    parsed = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const cwd = parsed.cwd || process.cwd();

  // Silent inside BrickLayer research subprocesses
  if (isResearchProject(cwd)) process.exit(0);

  // Need an autopilot dir to write results into
  const autopilotDir = findAutopilotDir(cwd);
  if (!autopilotDir) process.exit(0);

  // Extract agent_id and result details from payload
  const agent_id = parsed.tool_use_id || parsed.agent_id || ("a-" + Date.now());
  const resultStr = JSON.stringify(parsed.tool_result || parsed.output || "");
  const summary = resultStr.slice(0, 200);
  const success = !/\b(ERROR|FAILED|DEV_ESCALATE)\b/i.test(resultStr);

  // Ensure .autopilot/results/ directory exists
  const resultsDir = path.join(autopilotDir, "results");
  try {
    fs.mkdirSync(resultsDir, { recursive: true });
  } catch (_) {}

  // Write result cache file
  const resultFile = path.join(resultsDir, `${agent_id}.json`);
  const resultPayload = {
    agent_id,
    completed_at: new Date().toISOString(),
    success,
    summary,
  };
  try {
    fs.writeFileSync(resultFile, JSON.stringify(resultPayload, null, 2), "utf8");
  } catch (_) {}

  // Remove completed agent from ~/.masonry/state/agents.json active list
  try {
    const agentsFile = path.join(os.homedir(), ".masonry", "state", "agents.json");
    if (fs.existsSync(agentsFile)) {
      const data = JSON.parse(fs.readFileSync(agentsFile, "utf8"));
      const before = (data.active || []).length;
      data.active = (data.active || []).filter(
        (a) => a.id !== agent_id && a.id !== parsed.agent_id
      );
      if (data.active.length !== before) {
        const tmp = `${agentsFile}.tmp.${process.pid}`;
        fs.writeFileSync(tmp, JSON.stringify(data, null, 2), "utf8");
        fs.renameSync(tmp, agentsFile);
      }
    }
  } catch (_) {}

  // Check progress.json for dependency unblocking (flat task list)
  const progressFile = path.join(autopilotDir, "progress.json");
  if (fs.existsSync(progressFile)) {
    try {
      const progress = JSON.parse(fs.readFileSync(progressFile, "utf8"));
      if (progress && Array.isArray(progress.tasks)) {
        const doneTaskIds = new Set(
          progress.tasks.filter((t) => t.status === "DONE").map((t) => t.id)
        );
        let modified = false;
        for (const task of progress.tasks) {
          if (
            task.status === "BLOCKED" &&
            Array.isArray(task.depends_on) &&
            task.depends_on.length > 0 &&
            task.depends_on.every((depId) => doneTaskIds.has(depId))
          ) {
            task.status = "PENDING";
            modified = true;
            process.stderr.write(
              `[agent-complete] Task #${task.id} unblocked: all deps (${task.depends_on.join(", ")}) DONE\n`
            );
          }
        }
        if (modified) {
          progress.updated_at = new Date().toISOString();
          fs.writeFileSync(progressFile, JSON.stringify(progress, null, 2), "utf8");
        }
      }
    } catch (_) {}
  }

  // Check rough-in-state.json for wave-based dependency unblocking
  const roughInFile = path.join(autopilotDir, "rough-in-state.json");
  if (fs.existsSync(roughInFile)) {
    try {
      const state = JSON.parse(fs.readFileSync(roughInFile, "utf8"));
      if (state && Array.isArray(state.waves)) {
        const completedIds = new Set();
        for (const wave of state.waves) {
          for (const task of wave.tasks || []) {
            if (task.status === "complete") completedIds.add(task.id);
          }
        }
        let modified = false;
        for (const wave of state.waves) {
          for (const task of wave.tasks || []) {
            if (task.status === "blocked" && task.depends_on && completedIds.has(task.depends_on)) {
              task.status = "pending";
              modified = true;
              process.stderr.write(
                `[agent-complete] Wave task ${task.id} unblocked: dep ${task.depends_on} complete\n`
              );
            }
          }
        }
        if (modified) {
          state.last_updated = new Date().toISOString();
          fs.writeFileSync(roughInFile, JSON.stringify(state, null, 2), "utf8");
        }
      }
    } catch (_) {}
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

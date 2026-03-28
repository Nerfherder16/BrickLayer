#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Agent-complete result cache.
 *
 * Fires when an Agent tool call completes (SubagentStop equivalent via PostToolUse).
 * Writes result to .autopilot/results/{agent_id}.json for dependency signaling.
 * Checks progress.json for tasks with depends_on — logs when blocked tasks unblock.
 *
 * Ruflo equivalent: agent-complete hook for real-time result streaming
 */

"use strict";
const fs = require("fs");
const path = require("path");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

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

  // Extract agent_id and result details from PostToolUse payload
  const agent_id = parsed.tool_use_id || ("a-" + Date.now());
  const resultStr = JSON.stringify(parsed.tool_result || "");
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

  // Check progress.json for dependency unblocking
  const progressFile = path.join(autopilotDir, "progress.json");
  if (fs.existsSync(progressFile)) {
    let progress = null;
    try {
      progress = JSON.parse(fs.readFileSync(progressFile, "utf8"));
    } catch (_) {}

    if (progress && Array.isArray(progress.tasks)) {
      // Get all completed agent IDs from results/
      let completedIds = new Set();
      try {
        const resultFiles = fs.readdirSync(resultsDir);
        for (const f of resultFiles) {
          if (f.endsWith(".json")) {
            try {
              const r = JSON.parse(fs.readFileSync(path.join(resultsDir, f), "utf8"));
              if (r.agent_id) completedIds.add(r.agent_id);
            } catch (_) {}
          }
        }
      } catch (_) {}

      // Find tasks that have depends_on and check if all deps are now complete
      for (const task of progress.tasks) {
        if (
          task.status === "PENDING" &&
          Array.isArray(task.depends_on) &&
          task.depends_on.length > 0
        ) {
          const allDone = task.depends_on.every((dep) => completedIds.has(dep));
          if (allDone) {
            process.stderr.write(
              `[agent-complete] Task #${task.id} unblocked: all dependencies complete\n`
            );
          }
        }
      }
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

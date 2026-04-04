#!/usr/bin/env node
/**
 * PostToolUse:Agent + SubagentStop hook (Masonry): Auto-PR creation.
 *
 * Fires after every agent completes. When ALL autopilot tasks are DONE
 * and git-nerd was the most recent agent (meaning code is committed),
 * creates a GitHub PR for the current branch if one doesn't exist.
 *
 * Skips silently if:
 *   - No .autopilot/ dir found
 *   - On main/master branch
 *   - PR already exists for this branch
 *   - `gh` CLI is not available
 *   - Not in a git repo
 */

"use strict";
const fs = require("node:fs");
const path = require("node:path");
const { execSync, spawnSync } = require("node:child_process");
const { readStdin } = require("./session/stop-utils");

const MAIN_BRANCHES = new Set(["main", "master", "develop"]);

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

function allTasksDone(autopilotDir) {
  const progressFile = path.join(autopilotDir, "progress.json");
  if (!fs.existsSync(progressFile)) return false;
  try {
    const progress = JSON.parse(fs.readFileSync(progressFile, "utf8"));
    const tasks = progress.tasks || [];
    if (tasks.length === 0) return false;
    return tasks.every((t) => t.status === "DONE");
  } catch {
    return false;
  }
}

function getCurrentBranch(cwd) {
  try {
    return execSync("git branch --show-current", {
      cwd,
      encoding: "utf8",
      timeout: 5000,
    }).trim();
  } catch {
    return null;
  }
}

function prExists(cwd, branch) {
  const result = spawnSync(
    "gh",
    ["pr", "view", branch, "--json", "number", "--jq", ".number"],
    { cwd, encoding: "utf8", timeout: 10000 }
  );
  return result.status === 0 && result.stdout.trim().length > 0;
}

function ghAvailable() {
  const result = spawnSync("gh", ["--version"], { encoding: "utf8", timeout: 5000 });
  return result.status === 0;
}

function createPR(cwd) {
  const result = spawnSync("gh", ["pr", "create", "--fill"], {
    cwd,
    encoding: "utf8",
    timeout: 30000,
  });
  return {
    success: result.status === 0,
    url: result.stdout.trim(),
    stderr: result.stderr.trim(),
  };
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
  const autopilotDir = findAutopilotDir(cwd);
  if (!autopilotDir) process.exit(0);

  // Only fire after git-nerd completes — that's when code is committed and ready
  const agentName = (
    parsed.agent_name ||
    parsed.agent_type ||
    parsed.tool_input?.subagent_type ||
    ""
  ).toLowerCase();
  if (!agentName.includes("git-nerd")) process.exit(0);

  // Check all tasks are done
  if (!allTasksDone(autopilotDir)) process.exit(0);

  // Need gh CLI
  if (!ghAvailable()) process.exit(0);

  // Get current branch
  const branch = getCurrentBranch(cwd);
  if (!branch || MAIN_BRANCHES.has(branch)) process.exit(0);

  // Skip if PR already exists
  if (prExists(cwd, branch)) {
    process.stderr.write(`[auto-pr] PR already exists for branch "${branch}" — skipping.\n`);
    process.exit(0);
  }

  // Create PR
  process.stderr.write(`[auto-pr] All tasks done on branch "${branch}". Creating PR...\n`);
  const result = createPR(cwd);

  if (result.success) {
    process.stderr.write(`[auto-pr] PR created: ${result.url}\n`);
    process.stdout.write(
      JSON.stringify({
        additionalContext:
          `[MASONRY AUTO-PR] PR created for branch "${branch}": ${result.url}\n` +
          `All autopilot tasks are DONE. The PR is ready for review.`,
      })
    );
  } else {
    process.stderr.write(`[auto-pr] PR creation failed: ${result.stderr}\n`);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

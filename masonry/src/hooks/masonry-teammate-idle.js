#!/usr/bin/env node
/**
 * TeammateIdle + TaskCompleted hook (Masonry): Auto-assign next build task to idle agent.
 *
 * Fires when an agent team member has no active task (TeammateIdle) or when a task
 * completes and another pending task is available (TaskCompleted).
 *
 * Reads .autopilot/progress.json, atomically claims the first PENDING task
 * (marks it IN_PROGRESS), and outputs a TDD task assignment for the idle agent.
 *
 * Requires: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 (set in settings.json)
 * Ruflo equivalent: post-task handler + autoAssignOnIdle: true
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

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

function tryRead(p) {
  try { return fs.readFileSync(p, "utf8").trim(); } catch { return null; }
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();
  const eventName = input.hook_event_name || "TeammateIdle";

  // Only fire if .autopilot/mode is "build" or "fix"
  const mode = tryRead(path.join(cwd, ".autopilot", "mode"));
  if (!mode || !["build", "fix"].includes(mode)) {
    process.exit(0);
  }

  const progressPath = path.join(cwd, ".autopilot", "progress.json");
  const progress = tryJSON(progressPath);
  if (!progress || !Array.isArray(progress.tasks)) process.exit(0);

  const tasks = progress.tasks;
  const done = tasks.filter((t) => t.status === "DONE").length;
  const total = tasks.length;

  // Find first PENDING task
  const pending = tasks.find((t) => t.status === "PENDING");

  if (!pending) {
    // No pending tasks
    const inProgress = tasks.filter((t) => t.status === "IN_PROGRESS");
    if (inProgress.length === 0 && done === total && total > 0) {
      // All done
      process.stdout.write(
        JSON.stringify({
          hookSpecificOutput: {
            hookEventName: eventName,
            content: `[Masonry] All ${done}/${total} tasks complete. Run /verify to validate.`,
          },
        })
      );
    }
    process.exit(0);
  }

  // Atomically claim: mark IN_PROGRESS before outputting assignment
  pending.status = "IN_PROGRESS";
  progress.updated_at = new Date().toISOString();
  try {
    fs.writeFileSync(progressPath, JSON.stringify(progress, null, 2), "utf8");
  } catch {
    // Failed to claim — exit silently to avoid double-assignment
    process.exit(0);
  }

  // Read spec.md for project context (first 600 chars)
  let specContext = "";
  try {
    const spec = fs.readFileSync(path.join(cwd, ".autopilot", "spec.md"), "utf8");
    specContext = spec.slice(0, 600).trim();
  } catch {}

  // Detect SPARC mode annotation: [mode:tdd], [mode:security], etc.
  const modeMatch = (pending.description || "").match(/\[mode:(\w+)\]/i);
  const sparcMode = modeMatch ? modeMatch[1].toLowerCase() : null;

  let roleInstructions = "";
  switch (sparcMode) {
    case "tdd":
      roleInstructions = "Follow strict TDD: write failing tests first, then implement to pass.";
      break;
    case "security":
      roleInstructions = "Security audit only — read code, identify OWASP Top 10 issues, write findings. No code changes.";
      break;
    case "devops":
      roleInstructions = "Focus on deployment: Dockerfile, compose config, CI/CD, environment variables.";
      break;
    case "architect":
      roleInstructions = "Architecture only — design the solution, write ADR. No implementation.";
      break;
    default:
      roleInstructions = "Follow TDD: write failing tests first, implement to pass tests, refactor.";
  }

  const assignment = [
    `[Masonry] Auto-assigning task #${pending.id} (${done}/${total} done)`,
    ``,
    `Task: ${pending.description}`,
    ``,
    roleInstructions,
    ``,
    `When complete:`,
    `  1. Update .autopilot/progress.json — set task #${pending.id} status to "DONE"`,
    `  2. Commit your changes`,
    specContext ? `\nProject context (spec.md excerpt):\n${specContext}` : "",
  ]
    .join("\n")
    .trim();

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: eventName,
        content: assignment,
      },
    })
  );

  process.exit(0);
}

main().catch(() => process.exit(0));

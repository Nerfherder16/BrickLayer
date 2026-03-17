#!/usr/bin/env node
/**
 * PreToolUse hook: Auto-approve Write, Edit, and Bash tool calls
 * when Masonry build OR UI workflow is active.
 *
 * Checks .autopilot/mode (build/fix) and .ui/mode (compose/fix).
 * Determines project root by walking up from tool_input.file_path
 * or extracting paths from tool_input.command.
 */

const { existsSync, readFileSync } = require("fs");
const { join, dirname } = require("path");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function findAutopilotMode(startDir) {
  if (!startDir) return null;
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const modeFile = join(dir, ".autopilot", "mode");
    if (existsSync(modeFile)) {
      try {
        return readFileSync(modeFile, "utf8").trim() || null;
      } catch {
        return null;
      }
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function findUiMode(startDir) {
  if (!startDir) return null;
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const modeFile = join(dir, ".ui", "mode");
    if (existsSync(modeFile)) {
      try {
        return readFileSync(modeFile, "utf8").trim() || null;
      } catch {
        return null;
      }
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function getCandidateDirs(parsed) {
  const dirs = [];
  const toolInput = parsed.tool_input || {};

  if (toolInput.file_path) {
    dirs.push(dirname(toolInput.file_path));
  }

  if (toolInput.command) {
    const winPaths = toolInput.command.match(/[A-Za-z]:[/\\][^\s"';&|)]+/g);
    if (winPaths) {
      for (const p of winPaths) {
        const clean = p.replace(/[/\\]$/, "");
        dirs.push(clean);
        dirs.push(dirname(clean));
      }
    }
    const unixPaths = toolInput.command.match(/(?<=\s|^|"|')\/[a-zA-Z][^\s"';&|)]+/g);
    if (unixPaths) {
      for (const p of unixPaths) {
        dirs.push(p);
        dirs.push(dirname(p));
      }
    }
  }

  if (parsed.cwd) {
    dirs.push(parsed.cwd);
  }

  return dirs;
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const candidates = getCandidateDirs(parsed);
  let autopilotMode = null;
  let uiMode = null;

  for (const dir of candidates) {
    if (!autopilotMode) autopilotMode = findAutopilotMode(dir);
    if (!uiMode) uiMode = findUiMode(dir);
    if (autopilotMode && uiMode) break;
  }

  const approve =
    (autopilotMode === "build" || autopilotMode === "fix") ||
    (uiMode === "compose" || uiMode === "fix");

  if (approve) {
    const reason = autopilotMode
      ? `Masonry build mode "${autopilotMode}" active`
      : `UI workflow mode "${uiMode}" active`;
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "allow",
          permissionDecisionReason: reason,
        },
      }),
    );
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

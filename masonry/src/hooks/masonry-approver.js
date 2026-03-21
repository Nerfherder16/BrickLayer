#!/usr/bin/env node
/**
 * PreToolUse hook: Auto-approve Write, Edit, and Bash tool calls
 * when Masonry build OR UI workflow is active.
 *
 * Checks .autopilot/mode (build/fix) and .ui/mode (compose/fix).
 * Determines project root by walking up from tool_input.file_path
 * or extracting paths from tool_input.command.
 */

const { existsSync, readFileSync, statSync } = require("fs");
const { join, dirname } = require("path");

// A build is considered active if progress.json was written within this window.
// The orchestrator updates progress.json on every task start/done — so any active
// build will have touched it recently. Stale mode files from crashed sessions won't.
const BUILD_FRESHNESS_MS = 30 * 60 * 1000; // 30 minutes

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function isFresh(filePath) {
  try {
    const { mtimeMs } = statSync(filePath);
    return Date.now() - mtimeMs < BUILD_FRESHNESS_MS;
  } catch {
    return false;
  }
}

function findAutopilotMode(startDir) {
  if (!startDir) return null;
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const modeFile = join(dir, ".autopilot", "mode");
    if (existsSync(modeFile)) {
      try {
        const mode = readFileSync(modeFile, "utf8").trim() || null;
        if (!mode) return null;
        // Guard: only trust an active build/fix mode if progress.json is fresh.
        // This prevents a stale mode file from a crashed session from silently
        // auto-approving an interactive session that has nothing to do with a build.
        if (mode === "build" || mode === "fix") {
          const progressFile = join(dir, ".autopilot", "progress.json");
          if (!isFresh(progressFile)) return null;
        }
        return mode;
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
        const mode = readFileSync(modeFile, "utf8").trim() || null;
        if (!mode) return null;
        // Same freshness guard for UI compose/fix modes.
        if (mode === "compose" || mode === "fix") {
          const progressFile = join(dir, ".ui", "progress.json");
          if (!isFresh(progressFile)) return null;
        }
        return mode;
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

// Tier 1/2 file patterns — these must never be auto-approved during build/compose.
// Patterns 5+6 use (?:^|[/\\]) to match both relative paths (src/...) and absolute/separator-led paths.
const TIER1_TIER2_PATTERNS = [
  /project-brief\.md$/i,
  /agent_registry\.yml$/i,
  /hooks\.json$/i,
  /constants\.py$/i,
  /(?:^|[/\\])src[/\\]/i,
  /(?:^|[/\\])docs[/\\]/i,
];

function isTier1Tier2(filePath) {
  if (!filePath) return false;
  return TIER1_TIER2_PATTERNS.some((p) => p.test(filePath));
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

  const toolInput = parsed.tool_input || {};
  const toolName = (parsed.tool_name || "").toLowerCase();
  const filePath = toolInput.file_path || toolInput.path || "";

  // Block auto-approval for Tier 1/2 authority files — must always prompt user.
  if (approve && isTier1Tier2(filePath)) process.exit(0);

  // Never auto-approve Bash — command strings are too hard to analyze reliably for path safety.
  if (approve && toolName === "bash") process.exit(0);

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

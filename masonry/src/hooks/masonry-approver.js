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

// Mortar session token must be this fresh to count as "current session".
// 4 hours covers a normal working session with breaks.
const MORTAR_SESSION_FRESHNESS_MS = 4 * 60 * 60 * 1000; // 4 hours

const MASONRY_STATE_PATH = "C:/Users/trg16/Dev/Bricklayer2.0/masonry/masonry-state.json";

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

function isResearchProject(dir) {
  if (!dir) return false;
  return existsSync(join(dir, "program.md")) && existsSync(join(dir, "questions.md"));
}

// Check whether Mortar wrote a fresh session token.
// Returns true if masonry-state.json has mortar_consulted: true
// and mortar_session_id is an ISO timestamp within the last 4 hours.
function isMortarConsulted() {
  try {
    const raw = readFileSync(MASONRY_STATE_PATH, "utf8");
    const state = JSON.parse(raw);
    if (!state.mortar_consulted) return false;
    if (!state.mortar_session_id) return false;
    const sessionTime = new Date(state.mortar_session_id).getTime();
    if (isNaN(sessionTime)) return false;
    return Date.now() - sessionTime < MORTAR_SESSION_FRESHNESS_MS;
  } catch {
    return false;
  }
}

// Determine if this hook is running inside a subagent spawned BY Mortar.
// Mortar-spawned agents run under claude --dangerously-skip-permissions with
// CLAUDE_SUBAGENT=1 in their environment (set by Mortar before spawning).
// Also treat any process that has MASONRY_SUBAGENT set as exempt.
function isSubagentContext() {
  return (
    process.env.CLAUDE_SUBAGENT === "1" ||
    process.env.MASONRY_SUBAGENT === "1"
  );
}

// Walk up from dir to find a BL research project root.
// Handles cases where cwd is a subdirectory or the tool target is outside the project.
function findResearchProject(startDir) {
  if (!startDir) return false;
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    if (isResearchProject(dir)) return true;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return false;
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

  const cwd = parsed.cwd || process.cwd();
  const toolInput = parsed.tool_input || {};
  const toolName = (parsed.tool_name || "").toLowerCase();
  const filePath = toolInput.file_path || toolInput.path || "";

  // BrickLayer research campaign — approve everything, including Bash.
  // Walk up from cwd AND from the tool's target path — handles sessions whose cwd
  // is a parent directory (e.g. BL root) or a sibling project.
  const inResearch =
    findResearchProject(cwd) ||
    (filePath && findResearchProject(dirname(filePath)));
  if (inResearch) {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "allow",
          permissionDecisionReason: "BrickLayer research campaign active",
        },
      }),
    );
    process.exit(0);
  }

  const candidates = getCandidateDirs(parsed);

  // ── Mortar gate ──────────────────────────────────────────────────────────────
  // Before any Write/Edit/Bash reaches the approval logic, verify that Mortar has
  // been consulted in this Claude session (fresh token in masonry-state.json).
  //
  // Exemptions (do NOT block):
  //   1. Subagent contexts — agents spawned BY Mortar (CLAUDE_SUBAGENT=1)
  //   2. Research projects — already handled above via inResearch
  //   3. Active build/fix/compose modes — detected below; we gate only the idle case
  //      but we need to check modes first, so we defer the block to after mode detection
  // ─────────────────────────────────────────────────────────────────────────────
  const targetToolIsActionable =
    toolName === "write" || toolName === "edit" || toolName === "bash" ||
    toolName === "multiedit";
  const mortarGateApplicable =
    targetToolIsActionable && !isSubagentContext();
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

  // Mortar gate: block Write/Edit/Bash when Mortar has NOT been consulted,
  // unless we are inside an active build/fix/compose workflow (approve=true)
  // or inside a subagent context (mortarGateApplicable=false).
  //
  // exit(2) causes Claude to surface the message to the user as a hard block.
  if (mortarGateApplicable && !approve && !isMortarConsulted()) {
    process.stderr.write(
      "[Masonry] Route through Mortar first before doing any work. " +
      "Invoke the mortar agent to get a session token, then retry.\n"
    );
    process.exit(2);
  }

  // Block auto-approval for Tier 1/2 authority files — must always prompt user.
  if (approve && isTier1Tier2(filePath)) process.exit(0);

  // Never auto-approve Bash outside research mode — command strings are too hard
  // to analyze reliably for path safety.
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

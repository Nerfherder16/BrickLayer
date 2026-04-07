#!/usr/bin/env node
/**
 * PreToolUse hook (Masonry): Routing enforcement gate.
 *
 * Blocks Write/Edit operations on production code when the prompt-router
 * has injected a routing hint but no agent has been spawned yet.
 *
 * The prompt-router writes /tmp/masonry-mortar-gate.json with mortar_consulted=false.
 * The subagent-tracker sets mortar_consulted=true when any recognized agent spawns.
 * This hook enforces the gate: if mortar_consulted is still false and the target
 * is production code, exit 2 to block the write.
 *
 * Bypasses: .autopilot/, .ui/, .claude/, /tmp/, test dirs, build/fix mode,
 *           research projects, expired gate (>10 min), non-Write/Edit tools.
 *
 * Matcher: Write|Edit
 * Timeout: 3s
 */

"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const { readStdin } = require("./session/stop-utils");

const GATE_FILE = path.join(os.tmpdir(), "masonry-mortar-gate.json");
const BUILD_LOCK_FILE = path.join(os.tmpdir(), "bl-build-active.json");
const GATE_EXPIRY_MS = 10 * 60 * 1000; // 10 minutes
const BUILD_LOCK_EXPIRY_MS = 60 * 60 * 1000; // 1 hour

const EXEMPT_PATH_PATTERNS = [
  /[/\\]\.autopilot[/\\]/,
  /[/\\]\.ui[/\\]/,
  /[/\\]\.claude[/\\]/,
  /[/\\]node_modules[/\\]/,
  /[/\\]\.mas[/\\]/,
];

const TEST_PATH_PATTERNS = [
  /[/\\]tests?[/\\]/,
  /[/\\]__tests__[/\\]/,
  /\.test\.[^/\\]+$/,
  /\.spec\.[^/\\]+$/,
  /[/\\]test_[^/\\]+$/,
];

function isExemptPath(filePath, cwd) {
  if (!filePath) return true;

  // Check if path is inside the OS temp dir but NOT inside the project CWD.
  // This exempts scratch files in /tmp/ while still gating project files
  // even when the project root happens to be under /tmp/ (e.g. in tests).
  if (cwd) {
    const normalizedFile = path.resolve(filePath).replace(/\\/g, "/");
    const normalizedCwd = path.resolve(cwd).replace(/\\/g, "/");
    const tmpDir = os.tmpdir().replace(/\\/g, "/");
    if (normalizedFile.startsWith(tmpDir) && !normalizedFile.startsWith(normalizedCwd + "/")) {
      return true;
    }
  }

  if (EXEMPT_PATH_PATTERNS.some((p) => p.test(filePath))) return true;
  if (TEST_PATH_PATTERNS.some((p) => p.test(filePath))) return true;
  return false;
}

function isResearchProject(dir) {
  try {
    return (
      fs.existsSync(path.join(dir, "program.md")) &&
      fs.existsSync(path.join(dir, "questions.md"))
    );
  } catch {
    return false;
  }
}

function isBuildOrFixMode(cwd) {
  try {
    let dir = cwd;
    for (let i = 0; i < 10; i++) {
      const modeFile = path.join(dir, ".autopilot", "mode");
      if (fs.existsSync(modeFile)) {
        const mode = fs.readFileSync(modeFile, "utf8").trim();
        return mode === "build" || mode === "fix";
      }
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  } catch {}
  return false;
}

function readGate() {
  try {
    if (!fs.existsSync(GATE_FILE)) return null;
    return JSON.parse(fs.readFileSync(GATE_FILE, "utf8"));
  } catch {
    return null;
  }
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try {
    input = JSON.parse(raw);
  } catch {}

  const toolName = input.tool_name || "";
  if (toolName !== "Write" && toolName !== "Edit") {
    process.exit(0);
  }

  const cwd = input.cwd || process.cwd();

  if (isResearchProject(cwd)) {
    process.exit(0);
  }

  if (isBuildOrFixMode(cwd)) {
    process.exit(0);
  }

  // Build-lock bypass: /build writes /tmp/bl-build-active.json before spawning agents.
  // This allows sub-agents to write cross-project files (e.g. Kiln on Windows path)
  // even when the sub-agent CWD doesn't contain a .autopilot/mode file.
  try {
    if (fs.existsSync(BUILD_LOCK_FILE)) {
      const lock = JSON.parse(fs.readFileSync(BUILD_LOCK_FILE, "utf8"));
      if (lock.active) {
        const lockAge = Date.now() - new Date(lock.timestamp || 0).getTime();
        if (lockAge < BUILD_LOCK_EXPIRY_MS) {
          process.exit(0);
        }
      }
    }
  } catch { /* non-fatal */ }

  const toolInput = input.tool_input || {};
  const targetFile = toolInput.file_path || "";

  if (isExemptPath(targetFile, cwd)) {
    process.exit(0);
  }

  const gate = readGate();
  if (!gate) {
    process.exit(0);
  }

  if (gate.mortar_consulted) {
    process.exit(0);
  }

  const gateAge = Date.now() - new Date(gate.timestamp || 0).getTime();
  if (gateAge > GATE_EXPIRY_MS) {
    process.exit(0);
  }

  const relPath = (() => {
    try {
      return path.relative(cwd, path.resolve(cwd, targetFile));
    } catch {
      return targetFile;
    }
  })();

  process.stderr.write(
    `[masonry-routing-gate] BLOCKED: Write/Edit to "${relPath}" rejected.\n` +
      `  A routing hint was injected but no agent has been spawned yet.\n` +
      `  Spawn the routed agent first, or route through Mortar:\n` +
      `    Act as the mortar agent defined in .claude/agents/mortar.md\n`
  );
  process.exit(2);
}

main().catch(() => process.exit(0));

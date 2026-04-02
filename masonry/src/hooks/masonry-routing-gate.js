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

const GATE_FILE = process.env.BL_GATE_FILE || path.join(os.tmpdir(), 'masonry-mortar-gate.json');
const GATE_EXPIRY_MS = 10 * 60 * 1000; // 10 minutes

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

  // Build/fix mode bypass — but only when a specialist is active.
  // Orchestrators (mortar, rough-in, trowel) must still delegate even in build mode.
  if (isBuildOrFixMode(cwd)) {
    const gateForMode = readGate();
    if (!gateForMode || !gateForMode.chain || gateForMode.chain.length === 0) {
      process.exit(0); // no chain info — legacy bypass
    } else {
      const { ORCHESTRATORS: ORCH } = require("./session/mortar-gate");
      const tip = gateForMode.chain[gateForMode.chain.length - 1];
      if (!ORCH.has(tip) || gateForMode.specialist_spawned) {
        process.exit(0); // specialist active — allow
      }
      // orchestrator in build mode — fall through to gate enforcement below
    }
  }

  const toolInput = input.tool_input || {};
  const targetFile = toolInput.file_path || "";

  if (isExemptPath(targetFile, cwd)) {
    process.exit(0);
  }

  const gate = readGate();
  if (!gate) {
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

  // Multi-stage gate: check chain depth, not just mortar_consulted boolean.
  // Write/Edit is only allowed when the chain tip is a specialist (non-orchestrator).
  // Even if specialist_spawned is true, orchestrators themselves cannot edit.
  const { ORCHESTRATORS } = require("./session/mortar-gate");
  const chain = gate.chain || [];

  if (gate.mortar_consulted && chain.length > 0) {
    const currentAgent = chain[chain.length - 1];
    if (!ORCHESTRATORS.has(currentAgent)) {
      // Chain tip is a specialist — allow Write/Edit
      process.exit(0);
    }
    // Orchestrator is the chain tip — block even if specialist_spawned is true.
    // Orchestrators must delegate via Agent tool and let the specialist edit.
    process.stderr.write(
      `[masonry-routing-gate] BLOCKED: Write/Edit to "${relPath}" rejected.\n` +
        `  "${currentAgent}" is an orchestrator — it must NOT edit production code.\n` +
        `  Delegate to a specialist: Agent({ subagent_type: "kiln-engineer", prompt: "..." })\n` +
        `  The specialist will do the edit. You wait for it to return. Do NOT retry the edit yourself.\n`
    );
    process.exit(2);
  }

  // No agent spawned yet
  process.stderr.write(
    `[masonry-routing-gate] BLOCKED: Write/Edit to "${relPath}" rejected.\n` +
      `  A routing hint was injected but no agent has been spawned yet.\n` +
      `  Spawn the routed agent first, or route through Mortar:\n` +
      `    Agent({ subagent_type: "mortar", prompt: "..." })\n`
  );
  process.exit(2);
}

main().catch(() => process.exit(0));

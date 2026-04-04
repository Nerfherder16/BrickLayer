"use strict";
/**
 * Shared helpers for masonry-approver.js.
 * Extracted to keep the main entry point under the 300-line file-size limit.
 */

const { existsSync, readFileSync, readdirSync, statSync } = require("fs");
const { join, dirname } = require("path");
const { readStdin } = require('./session/stop-utils');

// A build is considered active if progress.json was written within this window.
const BUILD_FRESHNESS_MS = 30 * 60 * 1000; // 30 minutes

// Mortar session token must be this fresh to count as "current turn".
const MORTAR_SESSION_FRESHNESS_MS = 4 * 60 * 60 * 1000; // 4 hours

const MASONRY_STATE_PATH = join(dirname(dirname(__dirname)), "masonry-state.json");

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
        if (mode === "build" || mode === "fix") {
          if (!isFresh(join(dir, ".autopilot", "progress.json"))) return null;
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
        if (mode === "compose" || mode === "fix") {
          if (!isFresh(join(dir, ".ui", "progress.json"))) return null;
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

function isMortarConsulted() {
  try {
    const state = JSON.parse(readFileSync(MASONRY_STATE_PATH, "utf8"));
    if (!state.mortar_consulted) return false;
    if (!state.mortar_session_id) return false;
    const sessionTime = new Date(state.mortar_session_id).getTime();
    if (isNaN(sessionTime)) return false;
    return Date.now() - sessionTime < MORTAR_SESSION_FRESHNESS_MS;
  } catch {
    return false;
  }
}

function isSubagentContext() {
  return process.env.CLAUDE_SUBAGENT === "1" || process.env.MASONRY_SUBAGENT === "1";
}

function isResearchProjectFresh(dir) {
  if (!isResearchProject(dir)) return false;
  if (isFresh(join(dir, "questions.md"))) return true;
  const findingsDir = join(dir, "findings");
  if (existsSync(findingsDir)) {
    try {
      for (const f of readdirSync(findingsDir)) {
        if (isFresh(join(findingsDir, f))) return true;
      }
    } catch { /* ignore */ }
  }
  return false;
}

function findResearchProjectFresh(startDir) {
  if (!startDir) return false;
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    if (isResearchProjectFresh(dir)) return true;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return false;
}

function getCandidateDirs(parsed) {
  const dirs = [];
  const toolInput = parsed.tool_input || {};
  if (toolInput.file_path) dirs.push(dirname(toolInput.file_path));
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
  if (parsed.cwd) dirs.push(parsed.cwd);
  return dirs;
}

module.exports = {
  readStdin, isFresh, isTier1Tier2, isMortarConsulted, isSubagentContext,
  findAutopilotMode, findUiMode, findResearchProjectFresh, getCandidateDirs,
};

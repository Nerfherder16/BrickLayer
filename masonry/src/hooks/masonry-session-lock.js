#!/usr/bin/env node
/**
 * PreToolUse hook (Masonry): Session ownership check for protected files.
 *
 * Reads .mas/session.lock to determine which session owns the current
 * project. If a Write or Edit targets a protected file and the lock
 * belongs to a DIFFERENT session, blocks the operation with a clear
 * conflict message.
 *
 * Protected files / patterns:
 *   - masonry-state.json
 *   - .autopilot/progress.json, .autopilot/mode, .autopilot/compact-state.json
 *   - questions.md
 *   - findings/*.md
 *
 * Stale lock threshold: 4 hours (covers crashed sessions).
 */

"use strict";
const fs = require("fs");
const path = require("path");

const LOCK_STALE_MS = 4 * 60 * 60 * 1000; // 4 hours

/** Patterns relative to the project root that are protected. */
const PROTECTED_PATTERNS = [
  /^masonry-state\.json$/,
  /^\.autopilot[\\/](progress\.json|mode|compact-state\.json)$/,
  /^questions\.md$/,
  /^findings[\\/].+\.md$/,
];

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function isProtectedPath(cwd, filePath) {
  if (!filePath) return false;
  // Normalize: make relative to cwd
  let rel;
  try {
    rel = path.relative(cwd, path.resolve(cwd, filePath));
  } catch {
    return false;
  }
  // Reject paths that escape the project root
  if (rel.startsWith("..")) return false;
  const normalized = rel.replace(/\\/g, "/");
  return PROTECTED_PATTERNS.some((re) => re.test(normalized));
}

function isResearchProject(dir) {
  return (
    fs.existsSync(path.join(dir, "program.md")) &&
    fs.existsSync(path.join(dir, "questions.md"))
  );
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();

  // Silent inside BL research subprocesses
  if (isResearchProject(cwd)) process.exit(0);

  const currentSessionId = input.session_id || input.sessionId || null;
  if (!currentSessionId) process.exit(0);

  // Determine the target file path from Write or Edit tool input
  const toolName = input.tool_name || "";
  const toolInput = input.tool_input || {};
  let targetFile = null;

  if (toolName === "Write") {
    targetFile = toolInput.file_path || null;
  } else if (toolName === "Edit") {
    targetFile = toolInput.file_path || null;
  }

  // Only care about protected files
  if (!targetFile || !isProtectedPath(cwd, targetFile)) {
    process.exit(0);
  }

  // Read lock file
  const lockPath = path.join(cwd, ".mas", "session.lock");
  let lock = null;
  try {
    if (fs.existsSync(lockPath)) {
      lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));
    }
  } catch {
    process.exit(0);
  }

  if (!lock) process.exit(0);

  // Check lock staleness
  const lockAge = Date.now() - new Date(lock.started_at || 0).getTime();
  if (lockAge >= LOCK_STALE_MS) {
    // Stale lock — allow write and silently clean up
    try { fs.unlinkSync(lockPath); } catch {}
    process.exit(0);
  }

  // Check if it's a different session
  if (lock.session_id === currentSessionId) {
    process.exit(0); // Same session — allow
  }

  // Different session holds a fresh lock — block
  const relFile = path.relative(cwd, path.resolve(cwd, targetFile)).replace(/\\/g, "/");
  const output = {
    decision: "block",
    reason:
      `[Masonry Session Lock] "${relFile}" is owned by session ${lock.session_id} ` +
      `(started ${lock.started_at}, branch: ${lock.branch || "unknown"}). ` +
      `Parallel session conflict detected. ` +
      `Delete .mas/session.lock if that session has ended, then retry.`,
  };
  process.stdout.write(JSON.stringify(output));
  process.exit(0);
}

main().catch(() => process.exit(0));

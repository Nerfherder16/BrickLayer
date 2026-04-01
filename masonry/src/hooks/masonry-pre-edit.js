#!/usr/bin/env node
/**
 * PreToolUse hook: Back up the target file before Write|Edit tool calls
 * when Masonry build or fix mode is active.
 *
 * Backup path structure:
 *   .autopilot/backups/{relative_dir}/{filename}/{filename}.{ISO-timestamp}
 *
 * Example:
 *   src/api/users.py → .autopilot/backups/src/api/users/users.py.2026-03-28T04-00-00
 *
 * Backups older than 7 days are pruned by masonry-stop-guard.js on Stop.
 * Skips new files (not yet on disk — nothing to restore).
 * Always exits 0 — never blocks writes.
 */

const fs = require("fs");
const { existsSync, readFileSync } = fs;
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

/**
 * Walk up from startDir to find the .autopilot directory.
 * Returns the .autopilot directory path and its parent (project root), or null.
 */
function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const autopilotDir = path.join(dir, ".autopilot");
    if (existsSync(autopilotDir)) return { autopilotDir, projectRoot: dir };
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function isResearchProject(dir) {
  return (
    existsSync(path.join(dir, "program.md")) &&
    existsSync(path.join(dir, "questions.md"))
  );
}

/**
 * Build a filename-safe ISO timestamp with colons replaced by hyphens.
 * e.g. 2026-03-28T04-00-00
 */
function safeTimestamp() {
  return new Date().toISOString().replace(/:/g, "-").replace(/\.\d{3}Z$/, "");
}

async function main() {
  try {
    const cwd = process.cwd();

    // Research projects skip this hook entirely
    if (isResearchProject(cwd)) process.exit(0);

    const input = await readStdin();
    if (!input) process.exit(0);

    let parsed;
    try {
      parsed = JSON.parse(input);
    } catch {
      process.exit(0);
    }

    const sessionCwd = parsed.cwd || cwd;

    // Extract the file path from the tool input
    const filePath = (parsed.tool_input || {}).file_path;
    if (!filePath) process.exit(0);

    // Resolve to absolute path
    const absPath = path.isAbsolute(filePath)
      ? filePath
      : path.resolve(sessionCwd, filePath);

    // Only back up existing files — new files have nothing to restore
    if (!existsSync(absPath)) process.exit(0);

    // Find .autopilot walking up from the file's directory, then from cwd
    const fileDir = path.dirname(absPath);
    const found = findAutopilotDir(fileDir) || findAutopilotDir(sessionCwd);
    if (!found) process.exit(0);

    const { autopilotDir, projectRoot } = found;

    // Only active in build or fix mode
    const modeFile = path.join(autopilotDir, "mode");
    if (!existsSync(modeFile)) process.exit(0);

    const mode = readFileSync(modeFile, "utf8").trim();
    if (mode !== "build" && mode !== "fix") process.exit(0);

    // Build backup path:
    //   .autopilot/backups/{relative_dir}/{filename}/{filename}.{timestamp}
    const relPath = path.relative(projectRoot, absPath);
    const relDir = path.dirname(relPath);
    const filename = path.basename(absPath);
    const timestamp = safeTimestamp();

    const backupDir = path.join(autopilotDir, "backups", relDir, filename);
    const backupFile = path.join(backupDir, `${filename}.${timestamp}`);

    fs.mkdirSync(backupDir, { recursive: true });
    fs.copyFileSync(absPath, backupFile);
  } catch {
    // Never block a write due to backup failure — swallow all errors silently
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

#!/usr/bin/env node
/**
 * PreToolUse hook: Back up the target file before Write|Edit tool calls
 * when Masonry build or fix mode is active.
 *
 * Backups are written to .autopilot/backups/ and cleaned up after 7 days
 * by masonry-build-guard.js on Stop.
 *
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

function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    const autopilotDir = path.join(dir, ".autopilot");
    if (existsSync(autopilotDir)) return autopilotDir;
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

async function main() {
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

  // Only run during build or fix modes
  const autopilotDir = findAutopilotDir(sessionCwd);
  if (!autopilotDir) process.exit(0);

  const modeFile = path.join(autopilotDir, "mode");
  if (!existsSync(modeFile)) process.exit(0);

  const mode = readFileSync(modeFile, "utf8").trim();
  if (mode !== "build" && mode !== "fix") process.exit(0);

  // Extract the file path from the tool input
  const filePath = (parsed.tool_input || {}).file_path;
  if (!filePath) process.exit(0);

  // Only back up existing files — new files have nothing to restore
  if (!existsSync(filePath)) process.exit(0);

  // Build backup filename: relative path with slashes → underscores + ISO timestamp
  const relPath = path.relative(sessionCwd, filePath);
  const safeRel = relPath.replace(/[/\\]/g, "_");
  const isoTs = new Date().toISOString().replace(/:/g, "-").replace(/\..+/, "");
  const backupName = `${safeRel}.${isoTs}`;

  const backupsDir = path.join(autopilotDir, "backups");
  try {
    if (!existsSync(backupsDir)) {
      fs.mkdirSync(backupsDir, { recursive: true });
    }
    fs.copyFileSync(filePath, path.join(backupsDir, backupName));
  } catch (err) {
    // Never block a write due to backup failure — log and continue
    process.stderr.write(`[masonry-pre-edit] Backup failed for ${relPath}: ${err.message}\n`);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

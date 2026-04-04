#!/usr/bin/env node
/**
 * Stop hook: Block stopping if Masonry UI compose mode is active with pending tasks.
 * Exit code 2 blocks the stop.
 *
 * Adapted from masonry-build-guard.js for .ui/ directory.
 */

const { existsSync, readFileSync } = require("fs");
const path = require("path");
const { readStdin } = require('./session/stop-utils');

function findUiDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    const uiDir = path.join(dir, ".ui");
    if (existsSync(uiDir)) return uiDir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function isResearchProject(dir) {
  return existsSync(path.join(dir, "program.md")) &&
         existsSync(path.join(dir, "questions.md"));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  if (parsed.stop_hook_active) process.exit(0);

  const cwd = parsed.cwd || process.cwd();
  const uiDir = findUiDir(cwd);
  if (!uiDir) process.exit(0);

  const modeFile = path.join(uiDir, "mode");
  if (!existsSync(modeFile)) process.exit(0);

  const mode = readFileSync(modeFile, "utf8").trim();
  if (mode !== "compose") process.exit(0);

  const progressFile = path.join(uiDir, "progress.json");
  if (!existsSync(progressFile)) process.exit(0);

  let progress;
  try {
    progress = JSON.parse(readFileSync(progressFile, "utf8"));
  } catch {
    process.exit(0);
  }

  const tasks = progress.tasks || [];
  const pending = tasks.filter(
    (t) => t.status === "PENDING" || t.status === "IN_PROGRESS"
  );
  const done = tasks.filter((t) => t.status === "DONE");

  if (pending.length > 0) {
    const summary = pending
      .slice(0, 5)
      .map((t) => `  #${t.id}: ${t.description} (${t.status})`)
      .join("\n");
    process.stderr.write(
      `\nMasonry UI compose in progress! ${done.length}/${tasks.length} tasks complete.\n\nPending:\n${summary}\n\nTo stop: clear .ui/mode or use stop_hook_active.\n`
    );
    process.exit(2);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

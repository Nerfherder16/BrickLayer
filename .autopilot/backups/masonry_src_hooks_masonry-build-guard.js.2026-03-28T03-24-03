#!/usr/bin/env node
/**
 * Stop hook: Block stopping if Masonry build mode is active with pending tasks.
 * Exit code 2 blocks the stop.
 */

const { existsSync, readFileSync } = require("fs");
const { execSync } = require("child_process");
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
  const { existsSync } = require('fs');
  const path = require('path');
  return existsSync(path.join(dir, 'program.md')) &&
         existsSync(path.join(dir, 'questions.md'));
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

  const sessionCwd = parsed.cwd || process.env.PWD || process.cwd();
  const autopilotDir = findAutopilotDir(sessionCwd);
  if (!autopilotDir) process.exit(0);

  // Only block if the .autopilot/ dir belongs to this session's working directory.
  // Walking up can find a .autopilot/ owned by a parent project — that build belongs
  // to a different session and should not block this one.
  const resolvedAutopilot = path.resolve(autopilotDir);
  const resolvedCwd = path.resolve(sessionCwd);
  if (resolvedAutopilot !== path.join(resolvedCwd, ".autopilot")) process.exit(0);

  const modeFile = path.join(autopilotDir, "mode");
  if (!existsSync(modeFile)) process.exit(0);

  const mode = readFileSync(modeFile, "utf8").trim();
  if (mode !== "build" && mode !== "fix") process.exit(0);

  const progressFile = path.join(autopilotDir, "progress.json");
  if (!existsSync(progressFile)) process.exit(0);

  let progress;
  try {
    progress = JSON.parse(readFileSync(progressFile, "utf8"));
  } catch {
    process.exit(0);
  }

  const buildSessionId = progress.session_id || null;
  const currentSessionId = parsed.session_id || parsed.sessionId || null;

  // Only block the session that owns this build.
  if (buildSessionId && currentSessionId && buildSessionId !== currentSessionId) {
    const orphanMsg = `[Masonry] Prior session build detected: owned by session ${buildSessionId.slice(0, 8)}...`;
    process.stderr.write(`\n${orphanMsg}\n`);
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "Stop",
          content: `${orphanMsg}\nAn interrupted build from a prior session may still have uncommitted work. Run \`git status\` and check \`.autopilot/progress.json\` before starting new work.`,
        },
      }),
    );
    process.exit(0);
  }
  if (!buildSessionId && currentSessionId) {
    const legacyMsg = `[Masonry] Prior session build detected: no session owner (legacy build).`;
    process.stderr.write(`\n${legacyMsg}\n`);
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "Stop",
          content: `${legacyMsg}\nAn interrupted build from a prior session may still have uncommitted work. Run \`git status\` and check \`.autopilot/progress.json\` before starting new work.`,
        },
      }),
    );
    process.exit(0);
  }

  const tasks = progress.tasks || [];
  const pending = tasks.filter((t) => t.status === "PENDING" || t.status === "IN_PROGRESS");
  const done = tasks.filter((t) => t.status === "DONE");

  if (pending.length > 0) {
    const summary = pending.slice(0, 5).map((t) => `  #${t.id}: ${t.description} (${t.status})`).join("\n");
    process.stderr.write(
      `\nMasonry build in progress! ${done.length}/${tasks.length} tasks complete.\n\nPending:\n${summary}\n\nTo stop: clear .autopilot/mode or use stop_hook_active.\n`,
    );
    process.exit(2);
  }

  // Cleanup old backups (>7 days)
  const fs = require("fs");
  const backupsDir = path.join(autopilotDir, "backups");
  if (existsSync(backupsDir)) {
    const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const files = fs.readdirSync(backupsDir);
    let deleted = 0;
    for (const f of files) {
      const fp = path.join(backupsDir, f);
      try {
        if (fs.statSync(fp).mtimeMs < cutoff) { fs.unlinkSync(fp); deleted++; }
      } catch {}
    }
    if (deleted > 0) process.stderr.write(`[masonry-build-guard] Cleaned ${deleted} old backup(s)\n`);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

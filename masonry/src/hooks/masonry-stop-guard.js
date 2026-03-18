#!/usr/bin/env node
/**
 * Stop hook (Masonry): Block if there are uncommitted git changes from THIS session.
 *
 * Monorepo-aware: uses file mtime to separate session changes (today) from
 * pre-existing changes in other projects. Never runs git diff — just lists
 * files with age labels so Claude knows what needs committing.
 *
 * Exits silently (0) if nothing was modified today.
 * Exit code 2 blocks the stop when session files are uncommitted.
 */

const { execSync } = require("child_process");
const fs = require("fs");
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

function normalizeCwd(p) {
  // Convert POSIX /c/Users/... paths to Windows C:\Users\... so fs.statSync works
  if (process.platform === "win32" && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ":" + p.slice(2).replace(/\//g, "\\");
  }
  return p;
}

function fileAgeDays(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return Math.floor((Date.now() - stat.mtimeMs) / (1000 * 60 * 60 * 24));
  } catch {
    return null; // treat as today below
  }
}

function ageLabel(days) {
  if (days === null || days === 0) return "";
  if (days === 1) return " (yesterday)";
  return ` (${days}d old)`;
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

  if (parsed.stop_hook_active) process.exit(0);

  const cwd = normalizeCwd(parsed.cwd || process.cwd());

  try {
    const status = execSync("git status --porcelain", {
      encoding: "utf8",
      timeout: 10000,
      cwd,
    }).trim();

    if (!status) process.exit(0);

    const sessionModified = [];
    const sessionUntracked = [];
    const staleFiles = [];

    for (const line of status.split("\n").filter(Boolean)) {
      const xy = line.slice(0, 2).trim();
      const file = line.slice(3).trim();
      const days = fileAgeDays(path.join(cwd, file.replace(/\/$/, "")));
      const entry = { xy: xy || "??", file, days };

      if (days === 0 || days === null) {
        (xy === "??" ? sessionUntracked : sessionModified).push(entry);
      } else {
        staleFiles.push(entry);
      }
    }

    // Nothing from today — exit silently (don't nag about old changes)
    if (sessionModified.length === 0 && sessionUntracked.length === 0) {
      process.exit(0);
    }

    // Build compact output — no git diff, just file list
    const sessionCount = sessionModified.length + sessionUntracked.length;
    let output = `\nUncommitted changes (${sessionCount} files):\n`;

    if (sessionModified.length > 0) {
      output += `\n── Modified (${sessionModified.length}) ──\n`;
      for (const { xy, file } of sessionModified) {
        output += `  (${xy.padEnd(2)})  ${file}\n`;
      }
    }

    if (sessionUntracked.length > 0) {
      output += `\n── Untracked (${sessionUntracked.length}) ──\n`;
      for (const { file, days } of sessionUntracked) {
        output += `  (??)   ${file}${ageLabel(days)}\n`;
      }
    }

    if (staleFiles.length > 0) {
      output += `\n── Pre-existing (${staleFiles.length}, not from today) ──\n`;
      for (const { xy, file, days } of staleFiles) {
        output += `  (${xy.padEnd(2)})  ${file}${ageLabel(days)}\n`;
      }
    }

    output += `\nReview ages above — only commit files from this session.\n`;

    process.stderr.write(output);
    process.exit(2);
  } catch {
    // Not a git repo or git unavailable — allow stop
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

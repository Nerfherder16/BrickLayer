#!/usr/bin/env node
/**
 * Stop hook (Masonry): Block if there are uncommitted git changes.
 * Shows diff summary + file ages so Claude knows what's recent vs pre-existing.
 * Exit code 2 blocks the stop.
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

function fileAgeDays(filePath) {
  try {
    const stat = fs.statSync(filePath);
    const ageMs = Date.now() - stat.mtimeMs;
    return Math.floor(ageMs / (1000 * 60 * 60 * 24));
  } catch {
    return null;
  }
}

function ageLabel(days) {
  if (days === null) return "";
  if (days === 0) return " [today]";
  if (days === 1) return " [yesterday]";
  return ` [${days}d old]`;
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

  const cwd = parsed.cwd || process.cwd();

  try {
    const status = execSync("git status --porcelain", {
      encoding: "utf8",
      timeout: 10000,
      cwd,
    }).trim();

    if (!status) process.exit(0);

    const lines = status.split("\n");
    const modified = [];
    const untracked = [];

    for (const line of lines) {
      const xy = line.slice(0, 2);
      const file = line.slice(3).trim();
      if (xy.trim() === "??") {
        untracked.push(file);
      } else {
        modified.push({ xy: xy.trim(), file });
      }
    }

    let output = `\nUncommitted changes (${lines.length} files):\n`;

    // Modified tracked files — show diff stat
    if (modified.length > 0) {
      output += `\n── Modified (${modified.length}) ──\n`;
      try {
        const diffStat = execSync("git diff --stat HEAD", {
          encoding: "utf8",
          timeout: 10000,
          cwd,
        }).trim();
        if (diffStat) {
          output += diffStat + "\n";
        } else {
          for (const { xy, file } of modified) {
            output += `  ${xy} ${file}\n`;
          }
        }
      } catch {
        for (const { xy, file } of modified) {
          output += `  ${xy} ${file}\n`;
        }
      }
    }

    // Untracked files — show with age
    if (untracked.length > 0) {
      output += `\n── Untracked (${untracked.length}) ──\n`;
      for (const file of untracked) {
        const days = fileAgeDays(path.join(cwd, file));
        output += `  ?? ${file}${ageLabel(days)}\n`;
      }
    }

    output += `\nReview ages above — only commit files from this session.\n`;

    process.stderr.write(output);
    process.exit(2);
  } catch {
    // Not a git repo — allow stop
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

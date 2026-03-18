#!/usr/bin/env node
/**
 * Stop hook (Masonry): Block if there are uncommitted git changes from THIS session.
 *
 * In a monorepo, git shows changes from ALL sub-projects. This hook filters
 * by file mtime so pre-existing changes from other projects don't cause noise.
 *
 * - Session files (modified today): shown in full, blocks stop
 * - Pre-existing files (modified yesterday or older): shown as a quiet count
 * - Untracked files: shown with age label, only today's block stop
 *
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

    const lines = status.split("\n").filter(Boolean);

    // Separate and age-annotate every file
    const sessionModified = [];   // tracked, modified today
    const staleModified = [];     // tracked, modified yesterday or older
    const sessionUntracked = [];  // untracked, created today
    const staleUntracked = [];    // untracked, older

    for (const line of lines) {
      const xy = line.slice(0, 2).trim();
      const file = line.slice(3).trim();
      const absPath = path.join(cwd, file.replace(/\/$/, "")); // strip trailing / for dirs
      const days = fileAgeDays(absPath);
      const entry = { xy, file, days };

      if (xy === "??") {
        (days === 0 ? sessionUntracked : staleUntracked).push(entry);
      } else {
        (days === 0 ? sessionModified : staleModified).push(entry);
      }
    }

    const sessionCount = sessionModified.length + sessionUntracked.length;
    const staleCount = staleModified.length + staleUntracked.length;

    // Nothing from this session — allow stop (stale changes are user's problem)
    if (sessionCount === 0) {
      if (staleCount > 0) {
        process.stderr.write(
          `\n[Masonry] ${staleCount} pre-existing uncommitted file(s) from earlier sessions — not from today, skipping block.\n`
        );
      }
      process.exit(0);
    }

    // Build output — session files only in detail
    let output = `\nUncommitted changes (${sessionCount} from this session`;
    if (staleCount > 0) output += `, ${staleCount} pre-existing`;
    output += `):\n`;

    if (sessionModified.length > 0) {
      output += `\n── Modified (${sessionModified.length}) ──\n`;
      // Per-file diff stat for session files only
      for (const { file } of sessionModified) {
        try {
          const stat = execSync(`git diff --stat HEAD -- "${file}"`, {
            encoding: "utf8",
            timeout: 5000,
            cwd,
          }).trim();
          if (stat) {
            // Extract just the summary line (last line of diff --stat)
            const statLines = stat.split("\n");
            const summary = statLines[statLines.length - 1];
            output += ` ${file} — ${summary.trim()}\n`;
          } else {
            output += `  M ${file} [staged]\n`;
          }
        } catch {
          output += `  M ${file}\n`;
        }
      }
    }

    if (sessionUntracked.length > 0) {
      output += `\n── Untracked (${sessionUntracked.length}) ──\n`;
      for (const { file, days } of sessionUntracked) {
        output += `  ?? ${file}${ageLabel(days)}\n`;
      }
    }

    if (staleCount > 0) {
      output += `\n── Pre-existing (${staleCount}, not from today — review separately) ──\n`;
      for (const { xy, file, days } of [...staleModified, ...staleUntracked]) {
        output += `  ${xy || "??"} ${file}${ageLabel(days)}\n`;
      }
    }

    output += `\nReview ages above — only commit files from this session.\n`;

    process.stderr.write(output);
    process.exit(2);
  } catch {
    // Not a git repo or git failed — allow stop
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

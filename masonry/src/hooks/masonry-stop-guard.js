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

    // Collect all dirty file paths, then filter out gitignored ones.
    // Rationale: tracked files in .gitignore (e.g. .autopilot/) are intentionally
    // not meant to be committed — don't nag about them.
    const allLines = status.split("\n").filter(Boolean);
    const allFiles = allLines.map((l) => l.slice(3).trim());

    let ignoredSet = new Set();
    try {
      // git check-ignore exits 0 if any path is ignored, 1 if none are.
      // We pass all paths via --stdin and collect the ones that are ignored.
      const checkInput = allFiles.join("\n");
      const ignored = execSync("git check-ignore --stdin", {
        input: checkInput,
        encoding: "utf8",
        timeout: 5000,
        cwd,
      }).trim();
      if (ignored) {
        for (const p of ignored.split("\n").filter(Boolean)) {
          ignoredSet.add(p.trim());
        }
      }
    } catch {
      // Non-zero exit means no files are ignored — ignoredSet stays empty.
      // Any other error: proceed without filtering (safe default).
    }

    const sessionModified = [];
    const sessionUntracked = [];
    const staleFiles = [];

    for (const line of allLines) {
      const xy = line.slice(0, 2).trim();
      const file = line.slice(3).trim();

      // Skip gitignored paths — they can't be committed normally and are
      // explicitly excluded from version control by the project's .gitignore.
      if (ignoredSet.has(file)) continue;

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

    // Compact single-block output — session files only, no section headers
    const sessionCount = sessionModified.length + sessionUntracked.length;
    const staleNote = staleFiles.length > 0 ? ` (+${staleFiles.length} pre-existing ignored)` : "";
    let output = `\nStop blocked — ${sessionCount} uncommitted session file${sessionCount !== 1 ? "s" : ""}${staleNote}:\n`;

    for (const { file } of sessionModified) {
      output += `  M  ${file}\n`;
    }
    for (const { file } of sessionUntracked) {
      output += `  ?  ${file}\n`;
    }

    output += `Commit before stopping.\n`;

    process.stderr.write(output);
    process.exit(2);
  } catch {
    // Not a git repo or git unavailable — allow stop
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

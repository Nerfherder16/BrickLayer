#!/usr/bin/env node
/**
 * Stop hook (Masonry): Estimate context window usage.
 * Blocks stop ONLY when context > 750K AND there are uncommitted changes.
 * If the repo is clean, emits a stderr warning but allows the stop.
 * stop_hook_active prevents infinite loops — fires once, then allows stop.
 */

const { statSync, existsSync } = require("fs");
const { execSync } = require("child_process");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function hasUncommittedChanges(cwd) {
  try {
    const status = execSync("git status --porcelain", {
      encoding: "utf8", timeout: 5000, cwd,
    }).trim();
    return status.length > 0;
  } catch {
    return false;
  }
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  // Don't block a second time — stop_hook_active is set after first block
  if (parsed.stop_hook_active) process.exit(0);

  const transcriptPath = parsed.transcript_path;
  if (!transcriptPath) process.exit(0);

  try {
    const stats = statSync(transcriptPath);
    const estimatedTokens = Math.round(stats.size / 4);

    if (estimatedTokens > 750000) {
      const cwd = parsed.cwd || process.cwd();
      const dirty = hasUncommittedChanges(cwd);
      const label = `~${Math.round(estimatedTokens / 1000)}K tokens (>750K) — commit + new session.`;

      if (dirty) {
        // Block: uncommitted changes + large context = risk of lost work
        process.stdout.write(JSON.stringify({
          decision: "block",
          reason: label,
        }));
      } else {
        // Warn only: repo is clean, safe to stop
        process.stderr.write(`\n[Masonry] ${label}\n`);
      }
    }
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry, async): Estimate context window usage.
 * Warns when approaching limits. Non-blocking.
 */

const { statSync } = require("fs");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  const transcriptPath = parsed.transcript_path;
  if (!transcriptPath) process.exit(0);

  try {
    const stats = statSync(transcriptPath);
    const estimatedTokens = Math.round(stats.size / 4);

    if (estimatedTokens > 150000) {
      process.stdout.write(JSON.stringify({
        additionalContext: `WARNING: Context ~${Math.round(estimatedTokens / 1000)}K tokens. Consider committing and starting fresh.`,
      }));
    }
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

#!/usr/bin/env node
/**
 * Stop hook (Masonry): Estimate context window usage.
 * Blocks stop with a visible warning when context exceeds 150K tokens.
 * stop_hook_active prevents infinite loops — fires once, then allows stop.
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

  // Don't block a second time — stop_hook_active is set after first block
  if (parsed.stop_hook_active) process.exit(0);

  const transcriptPath = parsed.transcript_path;
  if (!transcriptPath) process.exit(0);

  try {
    const stats = statSync(transcriptPath);
    const estimatedTokens = Math.round(stats.size / 4);

    if (estimatedTokens > 150000) {
      process.stdout.write(JSON.stringify({
        decision: "block",
        reason: `Context is ~${Math.round(estimatedTokens / 1000)}K tokens (>150K). Consider committing work and starting a fresh session to avoid context degradation.`,
      }));
    }
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

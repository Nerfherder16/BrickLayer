#!/usr/bin/env node
// Register in .claude/settings.json as PostToolUse hook:
//   "masonry-pulse": { "type": "command", "command": "node masonry/src/hooks/masonry-pulse.js" }

/**
 * PostToolUse hook (Masonry): Heartbeat writer.
 *
 * Writes a pulse entry to .mas/pulse.jsonl at most once every 60 seconds
 * per session. Skips silently for BL research projects.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { getMasDir, appendJsonl, prunePulse, isResearchProject } = require("../core/mas");

const { getSessionId, readStdin } = require('./session/stop-utils');

async function main() {
  const raw = await readStdin();
  if (!raw) process.exit(0);

  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }
  const sessionId = getSessionId(input);
  const cwd = input.cwd || process.cwd();
  const toolName = input.tool_name || input.toolName || "unknown";

  // Skip inside BL research subprocesses
  if (isResearchProject(cwd)) process.exit(0);

  // Throttle: at most one pulse per 60 seconds per session
  const throttlePath = path.join(os.tmpdir(), `masonry-pulse-last-${sessionId}`);
  try {
    if (fs.existsSync(throttlePath)) {
      const mtime = fs.statSync(throttlePath).mtimeMs;
      if (Date.now() - mtime < 60_000) process.exit(0);
    }
  } catch (_) {}

  // Touch throttle file
  try {
    fs.writeFileSync(throttlePath, "", "utf8");
  } catch (_) {}

  // Write pulse entry
  const entry = {
    timestamp: new Date().toISOString(),
    session_id: sessionId,
    tool: toolName,
    cwd,
  };

  appendJsonl(cwd, "pulse.jsonl", entry);
  prunePulse(cwd);

  process.exit(0);
}

main().catch(() => process.exit(0));

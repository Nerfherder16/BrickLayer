#!/usr/bin/env node
/**
 * PreToolUse:Agent hook (Masonry): Capture Agent tool prompt before subagent spawns.
 *
 * Fires in the parent session when the Agent tool is called. Writes the prompt
 * to a temp file (.masonry/pending_agent_prompts/<subagent_type>_latest.json)
 * so masonry-subagent-tracker.js can read it on SubagentStart and populate
 * request_text in routing_log.jsonl.
 *
 * Part of F28.3 fix — addresses R27.2 WARNING that SubagentStart event does
 * not expose the Agent tool's prompt parameter.
 *
 * Two-slot strategy: uses subagent_type as the key (not a UUID) since
 * Claude hooks do not expose a stable event correlation ID. Race condition
 * risk is low because concurrent spawns of the same specialist type are rare.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function ensureDir(p) {
  try { fs.mkdirSync(p, { recursive: true }); } catch (_) {}
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  // PreToolUse: tool_input contains the Agent tool's parameters
  const toolInput = input.tool_input || input;
  const subagentType = (toolInput.subagent_type || "").toLowerCase().trim();
  const prompt = (toolInput.prompt || toolInput.description || "").slice(0, 500);

  // Only write if we have a prompt and a subagent_type
  if (!subagentType || !prompt) {
    process.exit(0);
    return;
  }

  // Use a fixed home-dir path so this matches masonry-subagent-tracker.js exactly,
  // regardless of whether CWD is the repo root, masonry/, or a project subdir.
  const pendingDir = path.join(os.homedir(), ".masonry", "pending_agent_prompts");
  ensureDir(pendingDir);

  const record = {
    timestamp: new Date().toISOString(),
    subagent_type: subagentType,
    request_text: prompt,
  };

  // One-slot-per-type: overwrites prior pending prompt for the same specialist type
  const slotPath = path.join(pendingDir, `${subagentType}_latest.json`);
  try {
    fs.writeFileSync(slotPath, JSON.stringify(record), "utf8");
  } catch (_) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

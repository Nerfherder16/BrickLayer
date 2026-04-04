#!/usr/bin/env node
/**
 * PreToolUse:Agent hook (Masonry): Capture Agent tool prompt before subagent spawns.
 *
 * Fires in the parent session when the Agent tool is called. Writes the prompt
 * to a temp file (.mas/pending_agent_prompts/<subagent_type>-<uuid>.json)
 * so masonry-subagent-tracker.js can read it on SubagentStart and populate
 * request_text in routing_log.jsonl.
 *
 * Part of F28.3 fix — addresses R27.2 WARNING that SubagentStart event does
 * not expose the Agent tool's prompt parameter.
 *
 * UUID-slot strategy (F-w42.1): uses subagent_type + UUID as the key so
 * concurrent spawns of the same specialist type each get their own slot file,
 * preventing the second write from overwriting the first (slot collision bug).
 * Read side globs for {subagent_type}-*.json and picks the oldest within TTL.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { readStdin } = require('./session/stop-utils');

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
  const pendingDir = path.join(os.homedir(), ".mas", "pending_agent_prompts");
  ensureDir(pendingDir);

  const record = {
    timestamp: new Date().toISOString(),
    subagent_type: subagentType,
    request_text: prompt,
  };

  // UUID-keyed slot: each spawn gets its own file — no collision when two agents
  // of the same type are dispatched concurrently (F-w42.1 fix).
  const uuid = crypto.randomUUID();
  const slotPath = path.join(pendingDir, `${subagentType}-${uuid}.json`);
  try {
    fs.writeFileSync(slotPath, JSON.stringify(record), "utf8");
  } catch (_) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

#!/usr/bin/env node
/**
 * PreToolUse:Agent hook (Masonry): Enforce Mortar routing for all agent spawns.
 *
 * Blocks Agent tool calls where subagent_type is missing, empty, or "general-purpose".
 * Forces Claude to route through Mortar (subagent_type: "mortar") instead of
 * spawning generic agents directly.
 *
 * HOW IT WORKS:
 *   - subagent_type missing or ""  → BLOCK
 *   - subagent_type "general-purpose" → BLOCK
 *   - subagent_type is any specialist → ALLOW
 *
 * INFINITE LOOP PREVENTION:
 *   Mortar always dispatches with explicit specialist subagent_types (developer,
 *   trowel, research-analyst, etc.) — those pass through. The only way to reach
 *   Mortar is subagent_type: "mortar", which also passes through.
 *
 * EXIT PROTOCOL:
 *   Exit 0 + JSON stdout → Claude Code reads the decision
 *   {"decision": "block", "reason": "..."}  → tool call blocked, reason shown to Claude
 *   {"decision": "approve"}                 → tool call proceeds
 *   Exit 0 + no/invalid JSON               → tool call proceeds (fail-open)
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { readStdin } = require('./session/stop-utils');

// Only block truly empty spawns — no intent specified at all.
// general-purpose is a valid Claude Code agent type and must be allowed
// (swarm workers, coordinators, and inline tasks all use it).
const BLOCKED_TYPES = new Set([
  "",
]);

function logBlocked(subagentType, promptSnippet) {
  try {
    const logDir = path.join(os.homedir(), ".masonry");
    fs.mkdirSync(logDir, { recursive: true });
    const logPath = path.join(logDir, "mortar_enforcer.log");
    const line = JSON.stringify({
      ts: new Date().toISOString(),
      blocked_type: subagentType || "(empty)",
      prompt_snippet: (promptSnippet || "").slice(0, 120),
    }) + "\n";
    fs.appendFileSync(logPath, line, "utf8");
  } catch (_) { /* non-fatal */ }
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch { /* fail-open */ }

  // PreToolUse: parameters are in tool_input
  const toolInput = input.tool_input || input;
  const rawType = (toolInput.subagent_type || "");
  const subagentType = rawType.toLowerCase().trim();
  const prompt = toolInput.prompt || toolInput.description || "";

  if (BLOCKED_TYPES.has(subagentType)) {
    logBlocked(subagentType, prompt);

    const reason = [
      "⛔ Agent spawn blocked by masonry-mortar-enforcer: subagent_type is empty.",
      "",
      "Always specify a subagent_type. Use one of:",
      "  general-purpose   — general work, swarm workers, inline tasks",
      "  Explore           — codebase exploration and research",
      "  Plan              — architecture and planning tasks",
      "",
      "Example: Agent({ subagent_type: \"general-purpose\", prompt: \"...\" })",
    ].join("\n");

    process.stdout.write(JSON.stringify({ decision: "block", reason }));
    process.exit(0);
  }

  // Valid specialist — allow through
  process.stdout.write(JSON.stringify({ decision: "approve" }));
  process.exit(0);
}

main().catch(() => {
  // Fail-open: never break a session due to hook crash
  process.stdout.write(JSON.stringify({ decision: "approve" }));
  process.exit(0);
});

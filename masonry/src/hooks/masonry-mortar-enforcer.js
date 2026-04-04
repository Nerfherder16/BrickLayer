#!/usr/bin/env node
/**
 * PreToolUse:Agent hook (Masonry): Enforce agent dispatch hierarchy.
 *
 * Enforces the Mortar → Coordinator → Specialist chain:
 *   - Main session can only spawn: mortar, Explore, general-purpose
 *   - Mortar can only spawn: rough-in, trowel, karen (+ Explore, general-purpose)
 *   - Coordinators (rough-in, trowel) can spawn any recognized specialist
 *   - Empty subagent_type is always blocked
 *
 * Reads the gate file to determine which orchestrator is currently active,
 * then enforces allowed children for that orchestrator.
 *
 * EXIT PROTOCOL:
 *   Exit 0 + JSON stdout → Claude Code reads the decision
 *   {"decision": "block", "reason": "..."}  → tool call blocked, reason shown
 *   {"decision": "approve"}                 → tool call proceeds
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { readStdin } = require('./session/stop-utils');
const { ORCHESTRATORS, ORCHESTRATOR_ALLOWED_CHILDREN, MORTAR_DISPATCHED_TYPES } = require('./session/mortar-gate');

const GATE_FILE = process.env.BL_GATE_FILE || path.join(os.tmpdir(), 'masonry-mortar-gate.json');

function readGate() {
  try {
    if (!fs.existsSync(GATE_FILE)) return null;
    return JSON.parse(fs.readFileSync(GATE_FILE, "utf8"));
  } catch { return null; }
}

function logBlocked(subagentType, reason, promptSnippet) {
  try {
    const logDir = path.join(os.homedir(), ".masonry");
    fs.mkdirSync(logDir, { recursive: true });
    const logPath = path.join(logDir, "mortar_enforcer.log");
    const line = JSON.stringify({
      ts: new Date().toISOString(),
      blocked_type: subagentType || "(empty)",
      reason,
      prompt_snippet: (promptSnippet || "").slice(0, 120),
    }) + "\n";
    fs.appendFileSync(logPath, line, "utf8");
  } catch (_) { /* non-fatal */ }
}

function block(subagentType, reason, prompt) {
  logBlocked(subagentType, reason, prompt);
  process.stdout.write(JSON.stringify({ decision: "block", reason }));
  process.exit(0);
}

function approve() {
  process.stdout.write(JSON.stringify({ decision: "approve" }));
  process.exit(0);
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch { /* fail-open */ }

  const toolInput = input.tool_input || input;
  const rawType = (toolInput.subagent_type || "");
  const subagentType = rawType.trim().toLowerCase();
  const prompt = toolInput.prompt || toolInput.description || "";

  // Rule 1: Empty subagent_type is always blocked
  if (!subagentType) {
    block(subagentType, [
      "⛔ Agent spawn blocked: subagent_type is empty.",
      "",
      "Route through Mortar: Agent({ subagent_type: \"mortar\", prompt: \"...\" })",
    ].join("\n"), prompt);
    return;
  }

  // Rule 2: Must be a recognized agent type
  if (!MORTAR_DISPATCHED_TYPES.has(subagentType) && !MORTAR_DISPATCHED_TYPES.has(rawType.trim())) {
    block(subagentType, [
      `⛔ Agent spawn blocked: "${subagentType}" is not a recognized specialist.`,
      "",
      "Route through Mortar: Agent({ subagent_type: \"mortar\", prompt: \"...\" })",
    ].join("\n"), prompt);
    return;
  }

  // Rule 3: Enforce hierarchy based on current chain state
  const gate = readGate();

  if (!gate || !gate.chain || gate.chain.length === 0) {
    // No chain yet — main session context.
    // Main session can only spawn mortar (or Claude Code built-ins).
    const MAIN_SESSION_ALLOWED = new Set(["mortar", "explore", "general-purpose", "self-host"]);
    if (!MAIN_SESSION_ALLOWED.has(subagentType)) {
      block(subagentType, [
        `⛔ Agent spawn blocked: main session cannot spawn "${subagentType}" directly.`,
        "",
        "The delegation hierarchy requires routing through Mortar first:",
        "  Agent({ subagent_type: \"mortar\", prompt: \"...\" })",
        "",
        "Mortar will delegate to the right coordinator (rough-in, trowel, or karen),",
        "which will then select the appropriate specialist.",
      ].join("\n"), prompt);
      return;
    }
    approve();
    return;
  }

  // Chain exists — check who the current orchestrator is
  const currentAgent = gate.chain[gate.chain.length - 1];

  if (!ORCHESTRATORS.has(currentAgent)) {
    // Current agent is a specialist — specialists shouldn't spawn agents,
    // but we don't hard-block this (they might need Explore for research).
    approve();
    return;
  }

  // Current agent is an orchestrator — enforce allowed children
  const allowed = ORCHESTRATOR_ALLOWED_CHILDREN[currentAgent];

  if (allowed === null) {
    // null = any recognized specialist is OK (rough-in, trowel)
    approve();
    return;
  }

  if (allowed && allowed.has(subagentType)) {
    approve();
    return;
  }

  // Orchestrator trying to spawn something not in its allowed set
  const allowedList = allowed ? [...allowed].join(", ") : "(any specialist)";
  block(subagentType, [
    `⛔ Agent spawn blocked: "${currentAgent}" cannot spawn "${subagentType}" directly.`,
    "",
    `"${currentAgent}" can only delegate to: ${allowedList}`,
    "",
    currentAgent === "mortar"
      ? "For dev tasks, spawn rough-in: Agent({ subagent_type: \"rough-in\", prompt: \"...\" })"
      : "Spawn the appropriate specialist for this task.",
  ].join("\n"), prompt);
}

main().catch(() => {
  // Fail-open: never break a session due to hook crash
  process.stdout.write(JSON.stringify({ decision: "approve" }));
  process.exit(0);
});

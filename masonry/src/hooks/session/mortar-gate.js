"use strict";
/**
 * session/mortar-gate.js — Mortar routing gate for subagent spawns.
 *
 * Maintains the set of recognized specialist agent types and provides
 * the isMortarGated() check used by masonry-subagent-tracker.js.
 */

// Known specialist subagent_type values (set by Mortar when dispatching).
// Any spawn with a type NOT in this set is blocked as a Mortar bypass.
const MORTAR_DISPATCHED_TYPES = new Set([
  // Claude Code built-in
  "Explore",
  "general-purpose",
  // Autopilot agents
  "developer",
  "test-writer",
  "code-reviewer",
  "diagnose-analyst",
  "fix-implementer",
  "spec-writer",
  // Masonry specialists
  "masonry:mortar",
  "mortar",
  "trowel",
  "uiux-master",
  "solana-specialist",
  "kiln-engineer",
  "karen",
  "frontier-analyst",
  "design-reviewer",
  "refactorer",
  "prompt-engineer",
  "git-nerd",
  // Research fleet
  "research-analyst",
  "regulatory-researcher",
  "competitive-analyst",
  "quantitative-analyst",
  "benchmark-engineer",
  "hypothesis-generator",
  "hypothesis-generator-bl2",
  "synthesizer",
  "synthesizer-bl2",
  "planner",
  "question-designer-bl2",
  "health-monitor",
  "cascade-analyst",
  "evolve-optimizer",
  "compliance-auditor",
  "security",
  "architect",
]);

/**
 * Returns true if the subagent spawn should be blocked (not a recognized specialist).
 */
function isMortarGated(input) {
  const subagentType = (input.subagent_type || "").trim().toLowerCase();

  if (!subagentType) {
    const agentName = (input.agent_name || input.agent_type || "").trim().toLowerCase();
    if (agentName && MORTAR_DISPATCHED_TYPES.has(agentName)) {
      return false; // allow — already a specialist
    }
    return true; // untagged spawn from main context
  }

  return !MORTAR_DISPATCHED_TYPES.has(subagentType);
}

module.exports = { isMortarGated, MORTAR_DISPATCHED_TYPES };

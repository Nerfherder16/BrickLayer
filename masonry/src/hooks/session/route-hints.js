/**
 * Route hint builder for masonry-prompt-router.js.
 *
 * Given an intent rule, effort level, and prompt text, produces the
 * additionalContext string that tells Claude which agent to spawn.
 *
 * Three routing lanes:
 *   1. Dev tasks → rough-in directly (skip Mortar)
 *   2. Campaigns → mortar (campaign state management)
 *   3. Specialists → named agent directly (security, git-nerd, karen, etc.)
 */
"use strict";

// Map route strings to direct subagent_type values for non-dev, non-campaign routes
const ROUTE_TO_AGENT = {
  "security agent": "security",
  "architect + design-reviewer": "architect",
  "uiux-master": "uiux-master",
  "diagnose-analyst → fix-implementer": "diagnose-analyst",
  "spec-writer → developer pipeline": "rough-in",
  "git-nerd": "git-nerd",
  "refactorer": "refactorer",
  "karen": "karen",
  "research-analyst + competitive-analyst": "research-analyst",
};

function getDirectAgentType(intent) {
  if (!intent) return "general-purpose";
  return ROUTE_TO_AGENT[intent.route] || "general-purpose";
}

function buildHintText(intent, effort, hintDetail, prompt) {
  if (effort === "low") {
    return `[ROUTING HINT] ${hintDetail}. Answer inline — no agent needed for simple lookups.`;
  }

  const escapedPrompt = prompt.slice(0, 200).replace(/"/g, '\\"').replace(/\n/g, " ");

  const isDevTask =
    intent &&
    /rough-in|developer|diagnose|fix-implementer|refactorer|benchmark/.test(intent.route);
  const isCampaign = intent && /Trowel|campaign/.test(intent.route);

  if (isDevTask) {
    return (
      `[MASONRY ROUTING — DO NOT SKIP]\n` +
      `${hintDetail}\n\n` +
      `You are an orchestrator. Do NOT read files and write code directly.\n` +
      `Spawn rough-in DIRECTLY for this dev task:\n\n` +
      `  Task tool: subagent_type="rough-in", prompt="${escapedPrompt}"\n\n` +
      `WHY: Rough-in reads the codebase, selects from 100+ specialist agents, builds a wave plan, ` +
      `and hands parallel dispatch to Queen Coordinator (up to 8 workers). ` +
      `Direct inline work skips code review, skips TDD, and uses your main context for implementation ` +
      `instead of preserving it for orchestration.`
    );
  }

  if (isCampaign) {
    return (
      `[MASONRY ROUTING — DO NOT SKIP]\n` +
      `${hintDetail}\n\n` +
      `Invoke Mortar for campaign management:\n\n` +
      `  Task tool: subagent_type="mortar", prompt="${escapedPrompt}"`
    );
  }

  // UI/design tasks — inject design intelligence hint
  const isUITask = intent && /uiux-master/.test(intent.route);
  if (isUITask) {
    return (
      `[MASONRY ROUTING — DO NOT SKIP]\n` +
      `${hintDetail}\n\n` +
      `You are an orchestrator. Do NOT do this work inline.\n` +
      `Spawn the uiux-master specialist directly:\n\n` +
      `  Task tool: subagent_type="uiux-master", prompt="${escapedPrompt}"\n\n` +
      `DESIGN INTELLIGENCE: The agent MUST run the design system search before making design decisions:\n` +
      `  python3 masonry/uiux-pro-max/scripts/search.py "<product type>" --design-system -p "<name>" -f markdown\n` +
      `This provides industry-specific style, palette, font, and pattern recommendations from 6,400+ curated data rows.`
    );
  }

  // Other specialist routes
  const agentType = getDirectAgentType(intent);
  return (
    `[MASONRY ROUTING — DO NOT SKIP]\n` +
    `${hintDetail}\n\n` +
    `You are an orchestrator. Do NOT do this work inline.\n` +
    `Spawn the specialist directly:\n\n` +
    `  Task tool: subagent_type="${agentType}", prompt="${escapedPrompt}"\n\n` +
    `WHY: Specialist agents have deeper context and patterns for this task type. ` +
    `Direct inline work uses your main context for implementation instead of preserving it for orchestration.`
  );
}

module.exports = { buildHintText, getDirectAgentType };

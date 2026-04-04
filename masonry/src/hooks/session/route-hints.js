/**
 * Route hint builder for masonry-prompt-router.js.
 *
 * Given an intent rule, effort level, and prompt text, produces the
 * additionalContext string that tells Claude which agent to spawn.
 *
 * Four routing lanes:
 *   1. Dev tasks → rough-in directly (full TDD pipeline)
 *   2. Worker specialists → rough-in with specialist hint (registry keyword matched
 *      an implementation agent — route through pipeline, not direct spawn)
 *   3. Campaigns → mortar (campaign state management)
 *   4. Advisory specialists → named agent directly (no decomposition needed)
 */
"use strict";

const fs = require("fs");
const path = require("path");

// Phrases that bypass the brainstorming gate
const SKIP_GATE_PATTERNS = /skip\s*plan|just\s*build|no\s*spec\s*needed|just\s*do\s*it|skip\s*brainstorm/i;

// Implementation specialists: primary output is code.
// When a registry keyword routes here, go through rough-in's TDD pipeline
// instead of spawning the specialist directly. rough-in will pick this
// specialist as the implementation worker and wrap it in test-writer →
// developer → code-reviewer → spec-reviewer.
const WORKER_SPECIALISTS = new Set([
  "python-specialist", "typescript-specialist", "database-specialist",
  "devops", "rust-specialist", "rust-developer", "rust-analyst",
  "go-specialist", "kotlin-specialist", "solana-specialist", "kiln-engineer",
  "fastapi-specialist", "nextjs-specialist", "bash-specialist",
  "docker-specialist", "embedded-developer", "game-developer",
  "kafka-specialist", "neo4j-specialist", "vector-db-specialist",
  "redis-specialist", "postgres-specialist", "opentelemetry-specialist",
  "developer", "worker-specialist",
]);

// Map INTENT_RULE route strings → subagent_type for advisory/direct routes
const ROUTE_TO_AGENT = {
  "rough-in → queen-coordinator → workers": "rough-in",
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
  if (intent.registryMatch) {
    // Worker specialists always go through rough-in — never direct
    if (WORKER_SPECIALISTS.has(intent.route)) return "rough-in";
    return intent.route;
  }
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

  // Worker specialist via registry keyword — treat as dev task, pass specialist hint
  const isWorkerSpecialist =
    intent && intent.registryMatch && WORKER_SPECIALISTS.has(intent.route);

  const isCampaign = intent && /Trowel|campaign/.test(intent.route);

  if (isDevTask || isWorkerSpecialist) {
    // Brainstorming gate: for complex tasks without a spec, suggest planning first
    if (effort === "high" && !SKIP_GATE_PATTERNS.test(prompt)) {
      const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();
      const specPath = path.join(cwd, ".autopilot", "spec.md");
      if (!fs.existsSync(specPath)) {
        return (
          `[MASONRY ROUTING — BRAINSTORMING GATE]\n` +
          `${hintDetail}\n\n` +
          `This looks like a complex task, but no spec exists yet (.autopilot/spec.md not found).\n\n` +
          `Before building, you should design first:\n` +
          `1. Run /plan to create a spec — this forces you to think through the approach before writing code\n` +
          `2. Or if this is truly simple, explain why and proceed\n\n` +
          `Rushed builds without design create rework. The brainstorming gate exists to prevent this.\n\n` +
          `To bypass: include "skip planning" or "just build" in your request.`
        );
      }
    }

    // Build the specialist hint line if a worker specialist was matched by keyword
    const specialistHint = isWorkerSpecialist
      ? `\nSuggested specialist: ${intent.route} (matched by keyword — pass this to rough-in so it picks the right worker without re-discovery)`
      : "";

    return (
      `[MASONRY ROUTING — DO NOT SKIP]\n` +
      `${hintDetail}\n\n` +
      `You are an orchestrator. Do NOT read files and write code directly.\n` +
      `Spawn rough-in DIRECTLY for this dev task:\n\n` +
      `  Task tool: subagent_type="rough-in", prompt="${escapedPrompt}"\n` +
      `${specialistHint}\n` +
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

  // Advisory specialist — spawn directly, no decomposition needed
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

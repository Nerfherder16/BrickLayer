#!/usr/bin/env node
"use strict";
// masonry/bin/masonry-fleet-cli.js — Fleet management CLI
// Usage: node masonry-fleet-cli.js <status|add|retire|regen> [name] [project_dir]
// project_dir defaults to process.cwd()

const fs = require("fs");
const path = require("path");

const { generateRegistry, readRegistry } = require(
  path.join(__dirname, "..", "src", "core", "registry.js")
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveProjectDir(args, nameConsumed) {
  // If nameConsumed=true, last positional arg (after name) is project_dir
  // If nameConsumed=false, first positional arg is project_dir
  const arg = args[0];
  if (arg && !arg.startsWith("-")) {
    return path.resolve(arg);
  }
  return path.resolve(process.cwd());
}

function relativeTime(isoStr) {
  if (!isoStr) return "—";
  const then = new Date(isoStr).getTime();
  if (isNaN(then)) return "—";
  const diffMs = Date.now() - then;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function pad(str, width) {
  const s = String(str);
  return s.length >= width ? s.slice(0, width) : s + " ".repeat(width - s.length);
}

function readJson(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_e) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Agent scaffold template (matches masonry-fleet.md)
// ---------------------------------------------------------------------------

function agentScaffold(name) {
  const title = name.charAt(0).toUpperCase() + name.slice(1).replace(/-/g, " ");
  return `---
name: ${name}
model: sonnet
description: Activate when [DESCRIBE TRIGGER CONDITIONS HERE]. [One sentence on what this agent does].
tier: standard
---

You are the ${title} specialist for an autoresearch session.

## Inputs (provided in your invocation prompt)

- \`question_text\`: The full question text from questions.md
- \`project_dir\`: Path to the project root

## Your Task

[DESCRIBE WHAT THIS AGENT DOES]

## Output Format

Write a finding to \`findings/{question_id}.md\` with this structure:

\`\`\`markdown
# {Question ID}: {Question Title}

**Status**: COMPLETE
**Mode**: {mode}
**Agent**: ${name}
**Verdict**: [HEALTHY | WARNING | FAILURE | FIXED | INCONCLUSIVE]

## Findings

[Your findings here]

## Evidence

[Evidence supporting your findings]

## Recommendation

[Actionable recommendation]
\`\`\`

## Self-Nomination

Append to your finding when relevant:
- \`[RECOMMEND: synthesizer-bl2 — sufficient findings for synthesis]\` after 10+ findings exist
`;
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

function cmdStatus(projectDir) {
  const registry = readRegistry(projectDir);
  const agentDb = readJson(path.join(projectDir, "agent_db.json"));
  const masonryState = readJson(path.join(projectDir, "masonry-state.json"));

  const projectName = path.basename(projectDir);
  const agents = registry ? registry.agents : [];
  const activeAgent = masonryState && masonryState.active_agent;
  const dbAgents = agentDb && agentDb.agents ? agentDb.agents : null;
  const dbFound = dbAgents !== null;

  const divider = "─".repeat(70);
  console.log(`\nMASONRY FLEET · ${projectName} · ${agents.length} agents`);
  console.log(divider);
  console.log(
    pad("Agent", 26) +
      pad("Model", 9) +
      pad("Tier", 10) +
      pad("Score", 7) +
      pad("Runs", 6) +
      "Last Activity"
  );
  console.log(divider);

  let eliteCount = 0;
  let belowThresholdCount = 0;

  for (const agent of agents) {
    const db = dbAgents && dbAgents[agent.name];
    const score = db ? db.score : null;
    const runs = db ? db.runs : null;
    const lastRun = db ? db.last_run : null;

    const scoreStr = score !== null ? score.toFixed(2) : "—";
    const runsStr = runs !== null ? String(runs) : "—";

    // Tier calculation
    let tier = agent.tier || "standard";
    if (score !== null && runs !== null && score >= 0.85 && runs >= 10) {
      tier = "elite";
    }
    if (score !== null && score < 0.40) belowThresholdCount++;
    if (tier === "elite") eliteCount++;

    const isActive = activeAgent && activeAgent === agent.name;
    const lastStr = isActive ? "active" : relativeTime(lastRun);
    const activeMark = isActive ? " ←" : "";

    console.log(
      pad(agent.name, 26) +
        pad(agent.model || "sonnet", 9) +
        pad(tier, 10) +
        pad(scoreStr, 7) +
        pad(runsStr, 6) +
        lastStr +
        activeMark
    );
  }

  console.log(divider);
  const activeCount = activeAgent ? 1 : 0;
  console.log(
    `Summary: ${activeCount} active, ${eliteCount} elite tier, ${belowThresholdCount} below 0.40 threshold`
  );
  console.log(`agent_db.json: ${dbFound ? "found" : "not found"}`);
  if (!registry) {
    console.log("registry.json: not found (run `regen` to generate)");
  }
  console.log();
}

function cmdAdd(name, projectDir) {
  if (!name) {
    console.error("Error: add requires an agent name");
    process.exit(1);
  }

  const agentsDir = path.join(projectDir, ".claude", "agents");
  const agentFile = path.join(agentsDir, `${name}.md`);

  if (fs.existsSync(agentFile)) {
    console.warn(`Warning: ${agentFile} already exists — skipping scaffold`);
  } else {
    fs.mkdirSync(agentsDir, { recursive: true });
    fs.writeFileSync(agentFile, agentScaffold(name), "utf8");
    console.log(`Created: ${agentFile}`);
  }

  const registry = generateRegistry(projectDir);
  console.log(`Registry updated: ${registry.agents.length} agents`);
  console.log(
    `Agent \`${name}\` created at \`.claude/agents/${name}.md\`. Edit the description and task sections before deploying to a campaign.`
  );
}

function cmdRetire(name, projectDir) {
  if (!name) {
    console.error("Error: retire requires an agent name");
    process.exit(1);
  }

  const agentsDir = path.join(projectDir, ".claude", "agents");
  const retiredDir = path.join(agentsDir, ".retired");
  const src = path.join(agentsDir, `${name}.md`);
  const dest = path.join(retiredDir, `${name}.md`);

  if (!fs.existsSync(src)) {
    console.error(`Error: .claude/agents/${name}.md not found`);
    process.exit(1);
  }

  fs.mkdirSync(retiredDir, { recursive: true });
  fs.renameSync(src, dest);
  console.log(`Moved: ${src} → ${dest}`);

  const registry = generateRegistry(projectDir);
  console.log(`Registry updated: ${registry.agents.length} agents`);
  console.log(
    `Agent \`${name}\` moved to \`.claude/agents/.retired/${name}.md\`. Run \`/masonry-fleet status\` to verify the updated fleet.`
  );
}

function cmdRegen(projectDir) {
  const registry = generateRegistry(projectDir);
  console.log(`Registry regenerated: ${registry.agents.length} agents in ${projectDir}`);
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

const [, , cmd, ...rest] = process.argv;

if (!cmd || cmd === "--help" || cmd === "-h") {
  console.log(`
masonry-fleet-cli — Fleet management CLI

Usage:
  node masonry-fleet-cli.js status [project_dir]
  node masonry-fleet-cli.js add <name> [project_dir]
  node masonry-fleet-cli.js retire <name> [project_dir]
  node masonry-fleet-cli.js regen [project_dir]

project_dir defaults to the current working directory.
`);
  process.exit(0);
}

switch (cmd) {
  case "status": {
    const projectDir = resolveProjectDir(rest, false);
    cmdStatus(projectDir);
    break;
  }
  case "add": {
    const [name, ...dirArgs] = rest;
    const projectDir = resolveProjectDir(dirArgs, true);
    cmdAdd(name, projectDir);
    break;
  }
  case "retire": {
    const [name, ...dirArgs] = rest;
    const projectDir = resolveProjectDir(dirArgs, true);
    cmdRetire(name, projectDir);
    break;
  }
  case "regen": {
    const projectDir = resolveProjectDir(rest, false);
    cmdRegen(projectDir);
    break;
  }
  default:
    console.error(`Unknown command: ${cmd}`);
    process.exit(1);
}

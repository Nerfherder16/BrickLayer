#!/usr/bin/env node
/**
 * UserPromptSubmit hook (Masonry): Transparent intent router.
 *
 * Intercepts every user prompt before Claude sees it.
 * Detects intent and injects a one-line routing suggestion.
 * Falls back silently if intent is unclear or the prompt is a slash command.
 *
 * Ruflo equivalent: hook-handler.cjs route via UserPromptSubmit
 *
 * NO prompt modification — only a brief routing hint injected into context.
 * The goal: reduce Mortar routing overhead by pre-signalling the likely agent team.
 */
"use strict";

const fs = require("fs");
const path = require("path");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

// ─── Intent Rules ────────────────────────────────────────────────────────────
// Each rule: { patterns[], route, note? }
// First match wins. Keep the most specific rules first.
const INTENT_RULES = [
  // Campaign / research loop
  {
    patterns: [
      /\b(campaign|bricklayer|bl.?run|masonry.?run|research loop|wave|questions\.md)\b/i,
      /\/masonry-(run|status|fleet|init)\b/i,
    ],
    route: "Trowel (campaign conductor)",
    note: "Use /masonry-run to start a campaign.",
  },
  // Security audit
  {
    patterns: [
      /\b(security.?audit|penetration|owasp|vulnerability|cve|exploit)\b/i,
      /\/masonry-security-review\b/i,
    ],
    route: "security agent",
  },
  // Architecture / design
  {
    patterns: [
      /\b(architect|architecture|system.?design|data.?model|erd|schema.?design|adr)\b/i,
    ],
    route: "architect + design-reviewer",
  },
  // UI / design
  {
    patterns: [
      /\b(ui|ux|figma|component|layout|dashboard|dark.?mode|design.?system|tailwind|css)\b/i,
      /\/ui-(init|compose|review|fix|tokens)\b/i,
    ],
    route: "uiux-master",
    note: "Run /ui-init first if no .ui/ exists.",
  },
  // Debugging
  {
    patterns: [
      /\b(debug|broken|error|exception|crash|failing test|traceback|stack.?trace|why is.{0,30}(not|failing|broken))\b/i,
    ],
    route: "diagnose-analyst → fix-implementer",
  },
  // Build / implement
  {
    patterns: [
      /\b(build|implement|create|add.?feature|write.?code|develop|scaffold|fix|update|make|change|set|configure|apply|enable|disable|modify)\b.{0,40}\b(app|component|endpoint|api|service|function|class|module|page|route)\b/i,
      /\/build\b|\/ultrawork\b/i,
    ],
    route: "developer + test-writer + code-reviewer",
    note: "Use /plan first for multi-file tasks.",
  },
  // Spec + build pipeline
  {
    patterns: [
      /\b(write.?a.?spec|create.?a.?spec|spec.?out|product.?requirements|prd|requirements.?doc)\b/i,
      /\b(plan.?out|plan.?this|blueprint.?the|blueprint.?a|design.?the.?architecture|write.?a.?plan.?for)\b/i,
      /\b(spec.?to.?build|plan.?to.?implement|feature.?spec|feature.?plan)\b/i,
    ],
    route: "spec-writer → developer pipeline",
    note: "Use /plan for full spec-to-build pipeline.",
  },
  // Git
  {
    patterns: [
      /\b(git|commit|branch|merge|push|pull.?request|pr|cherry.?pick|changelog|release)\b/i,
    ],
    route: "git-nerd",
  },
  // Refactoring
  {
    patterns: [
      /\b(refactor|clean.?up|reorganize|restructure|rename|extract.?method|dead.?code)\b/i,
    ],
    route: "refactorer",
  },
  // Documentation / roadmap
  {
    patterns: [
      /\b(roadmap|docs|documentation|readme|changelog|organize.{0,20}folder|audit.{0,20}(files|dirs))\b/i,
    ],
    route: "karen",
  },
  // Research / analysis (generic)
  {
    patterns: [
      /\b(research|investigate|analyze|study|compare|evaluate|benchmark)\b/i,
    ],
    route: "research-analyst + competitive-analyst",
  },
];

function detectIntent(prompt) {
  for (const rule of INTENT_RULES) {
    for (const pat of rule.patterns) {
      if (pat.test(prompt)) return rule;
    }
  }
  return null;
}

// ─── Effort Classification ────────────────────────────────────────────────────
// Maps prompt complexity to Opus 4.6 effort levels (low/medium/high/max).
// Injected as [effort:X] annotation alongside routing hints.
function classifyEffort(prompt) {
  // max: full system scope, security vulns, ultrawork
  if (/\b(full.?system|entire.?codebase|complete.?rewrite|all.?services)\b/i.test(prompt) ||
      /\b(vulnerability|exploit|cve|penetration)\b/i.test(prompt) ||
      /\/ultrawork\b|\/masonry-run\b/i.test(prompt)) {
    return "max";
  }
  // high: multi-file, architecture, complex debug, refactor, perf
  if (/\b(architect|architecture|redesign|migrate|migration|refactor|restructure)\b/i.test(prompt) ||
      /\b(performance|optimize|bottleneck|profil)\b/i.test(prompt) ||
      /\b(multiple.{0,20}files|across.{0,20}(all|the)|throughout)\b/i.test(prompt) ||
      /\b(traceback|stack.?trace|why.{0,30}(is|are|does|won.t).{0,40}(not|fail|broken|wrong))\b/i.test(prompt) ||
      /\b(security.?audit|owasp)\b/i.test(prompt)) {
    return "high";
  }
  // low: short lookups, explain/show/where queries
  if (prompt.length < 50 ||
      /^\s*(what|where|how|why|show|list|explain|who|when)\b/i.test(prompt)) {
    return "low";
  }
  // medium: default for standard dev tasks
  return "medium";
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const prompt = (input.prompt || input.message || "").trim();

  // Strategy flag detection — write .autopilot/strategy file if --strategy is present
  const strategyMatch = prompt.match(/--strategy\s+(conservative|balanced|aggressive)/i);
  if (strategyMatch) {
    const strategy = strategyMatch[1].toLowerCase();
    const autopilotDir = path.join(input.cwd || process.cwd(), ".autopilot");
    if (fs.existsSync(autopilotDir)) {
      try {
        fs.writeFileSync(path.join(autopilotDir, "strategy"), strategy, "utf8");
      } catch {}
    }
  }

  // Skip: empty, slash commands, very short inputs
  if (!prompt || prompt.startsWith("/") || prompt.length < 20) process.exit(0);

  const cwd = input.cwd || process.cwd();

  // Skip inside BrickLayer research loops (program.md + questions.md present)
  try {
    if (
      fs.existsSync(path.join(cwd, "program.md")) &&
      fs.existsSync(path.join(cwd, "questions.md"))
    ) {
      process.exit(0);
    }
  } catch {}

  // Skip if active campaign (masonry-state.json with mode set)
  try {
    const state = JSON.parse(
      fs.readFileSync(path.join(cwd, "masonry-state.json"), "utf8")
    );
    if (state && state.mode) process.exit(0);
  } catch {}

  // Reset Mortar routing receipt per-turn so stale receipts don't carry over
  try {
    const receiptPath = "C:/Users/trg16/Dev/Bricklayer2.0/masonry/masonry-state.json";
    if (fs.existsSync(receiptPath)) {
      const rState = JSON.parse(fs.readFileSync(receiptPath, "utf8"));
      rState.mortar_consulted = false;
      fs.writeFileSync(receiptPath, JSON.stringify(rState, null, 2), "utf8");
    }
  } catch {}

  const intent = detectIntent(prompt);
  const effort = classifyEffort(prompt);

  // Emit only if we have something useful to say
  const hasSignal = intent || effort !== "medium";
  if (!hasSignal) process.exit(0);

  const routeStr = intent ? `Route to: ${intent.route}` : null;
  const effortStr = `[effort:${effort}]`;
  const parts = [];
  if (routeStr) parts.push(routeStr);
  parts.push(effortStr);
  if (intent && intent.note) parts.push(intent.note);

  const hintDetail = parts.join(" ");
  const hintText =
    `[ROUTING] You MUST route this request through Mortar before using Write, Edit, or Bash. ` +
    `${hintDetail}. Invoke the mortar agent (subagent_type: "mortar") first. ` +
    `Direct Write/Edit without a Mortar routing receipt will be blocked by the pre-tool hook.`;

  process.stdout.write(JSON.stringify({ additionalContext: hintText }));

  process.exit(0);
}

main().catch(() => process.exit(0));

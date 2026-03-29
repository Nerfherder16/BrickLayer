#!/usr/bin/env node
/**
 * UserPromptSubmit hook (Masonry): Transparent intent router.
 *
 * Intercepts every user prompt before Claude sees it.
 * Detects intent and injects a routing directive:
 *   - Dev tasks → rough-in directly (skip Mortar)
 *   - Campaigns → mortar (campaign state management)
 *   - Specialists → named agent directly
 *   - Low effort → answer inline, no agent
 *
 * NO prompt modification — only a brief routing hint injected into context.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { readStdin } = require("./session/stop-utils");
const { buildHintText } = require("./session/route-hints");

// ─── Intent Rules ────────────────────────────────────────────────────────────
const INTENT_RULES = [
  {
    patterns: [
      /\b(campaign|bricklayer|bl.?run|masonry.?run|research loop|wave|questions\.md)\b/i,
      /\/masonry-(run|status|fleet|init)\b/i,
    ],
    route: "Trowel (campaign conductor)",
    note: "Use /masonry-run to start a campaign.",
  },
  {
    patterns: [
      /\b(security.?audit|penetration|owasp|vulnerability|cve|exploit)\b/i,
      /\/masonry-security-review\b/i,
    ],
    route: "security agent",
  },
  {
    patterns: [
      /\b(architect|architecture|system.?design|data.?model|erd|schema.?design|adr)\b/i,
    ],
    route: "architect + design-reviewer",
  },
  {
    patterns: [
      /\b(ui|ux|figma|component|layout|dashboard|dark.?mode|design.?system|tailwind|css)\b/i,
      /\/ui-(init|compose|review|fix|tokens)\b/i,
    ],
    route: "uiux-master",
    note: "Run /ui-init first if no .ui/ exists.",
  },
  {
    patterns: [
      /\b(debug|broken|error|exception|crash|failing test|traceback|stack.?trace|why is.{0,30}(not|failing|broken))\b/i,
    ],
    route: "diagnose-analyst → fix-implementer",
  },
  {
    patterns: [
      /\b(build|implement|create|add.?feature|write.?code|develop|scaffold|fix|update|make|change|set|configure|apply|enable|disable|modify)\b.{0,40}\b(app|component|endpoint|api|service|function|class|module|page|route)\b/i,
      /\/build\b|\/ultrawork\b/i,
    ],
    route: "rough-in → queen-coordinator → workers",
    note: "Rough-in decomposes, Queen dispatches up to 8 agents in parallel.",
  },
  {
    patterns: [
      /\b(write.?a.?spec|create.?a.?spec|spec.?out|product.?requirements|prd|requirements.?doc)\b/i,
      /\b(plan.?out|plan.?this|blueprint.?the|blueprint.?a|design.?the.?architecture|write.?a.?plan.?for)\b/i,
      /\b(spec.?to.?build|plan.?to.?implement|feature.?spec|feature.?plan)\b/i,
    ],
    route: "spec-writer → developer pipeline",
    note: "Use /plan for full spec-to-build pipeline.",
  },
  {
    patterns: [
      /\b(git|commit|branch|merge|push|pull.?request|pr|cherry.?pick|changelog|release)\b/i,
    ],
    route: "git-nerd",
  },
  {
    patterns: [
      /\b(refactor|clean.?up|reorganize|restructure|rename|extract.?method|dead.?code)\b/i,
    ],
    route: "refactorer",
  },
  {
    patterns: [
      /\b(roadmap|docs|documentation|readme|changelog|organize.{0,20}folder|audit.{0,20}(files|dirs))\b/i,
    ],
    route: "karen",
  },
  {
    patterns: [
      /\b(research|investigate|analyze|study|compare|evaluate|benchmark)\b/i,
    ],
    route: "research-analyst + competitive-analyst",
  },
];

const FOLLOWUP_PATTERNS = [
  /^(now|next|then|also|additionally)\s/i,
  /\b(now\s+(also|do|update|add|fix|run|build|create|write|test|check))\b/i,
  /\b(also\s+(update|add|fix|run|build|create|write|test|check|do))\b/i,
  /\b(same\s+(for|thing|approach|pattern|way|treatment))\b/i,
  /\b(do\s+the\s+same)\b/i,
  /\b(repeat\s+(that|this|it)\s+(for|on|with))\b/i,
  /\b(do\s+(that|it|this)\s+(again|too|as\s+well))\b/i,
  /\b(continue|proceed|go\s+ahead|carry\s+on|keep\s+going|next\s+step)\b/i,
  /\b(and\s+then|after\s+that|once\s+that.s\s+done|while\s+you.re\s+at\s+it)\b/i,
  /\b(but\s+also|plus\s+(also\s+)?add|and\s+add|and\s+update|and\s+fix)\b/i,
  /\b(don.t\s+forget\s+to|make\s+sure\s+(to\s+)?(also|you))\b/i,
  /^(and\s+)?(update|fix|change|modify|refactor|test|check)\s+(it|that|those|them|this)\b/i,
];

function detectIntent(prompt) {
  for (const rule of INTENT_RULES) {
    for (const pat of rule.patterns) {
      if (pat.test(prompt)) return rule;
    }
  }
  return null;
}

function classifyEffort(prompt) {
  if (/\b(full.?system|entire.?codebase|complete.?rewrite|all.?services)\b/i.test(prompt) ||
      /\b(vulnerability|exploit|cve|penetration)\b/i.test(prompt) ||
      /\/ultrawork\b|\/masonry-run\b/i.test(prompt)) return "max";
  if (/\b(architect|architecture|redesign|migrate|migration|refactor|restructure)\b/i.test(prompt) ||
      /\b(performance|optimize|bottleneck|profil)\b/i.test(prompt) ||
      /\b(multiple.{0,20}files|across.{0,20}(all|the)|throughout)\b/i.test(prompt) ||
      /\b(traceback|stack.?trace|why.{0,30}(is|are|does|won.t).{0,40}(not|fail|broken|wrong))\b/i.test(prompt) ||
      /\b(security.?audit|owasp)\b/i.test(prompt)) return "high";
  if (prompt.length < 50 ||
      /^\s*(what|where|how|why|show|list|explain|who|when)\b/i.test(prompt)) return "low";
  return "medium";
}

function isFollowUp(prompt) {
  if (prompt.length < 30) return false;
  if (/^\s*(what|where|how|why|show|list|explain|who|when)\b/i.test(prompt)) return false;
  return FOLLOWUP_PATTERNS.some((p) => p.test(prompt));
}

function isExpired(lastRoute) {
  if (!lastRoute || !lastRoute.timestamp) return true;
  if ((lastRoute.turn_count || 0) > 5) return true;
  return Date.now() - new Date(lastRoute.timestamp).getTime() > 600000;
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const prompt = (input.prompt || input.message || "").trim();

  // Strategy flag detection
  const strategyMatch = prompt.match(/--strategy\s+(conservative|balanced|aggressive)/i);
  if (strategyMatch) {
    const autopilotDir = path.join(input.cwd || process.cwd(), ".autopilot");
    if (fs.existsSync(autopilotDir)) {
      try { fs.writeFileSync(path.join(autopilotDir, "strategy"), strategyMatch[1].toLowerCase(), "utf8"); } catch {}
    }
  }

  if (!prompt || prompt.startsWith("/") || prompt.length < 20) return;

  const cwd = input.cwd || process.cwd();

  // Skip inside BrickLayer research loops
  try {
    if (fs.existsSync(path.join(cwd, "program.md")) && fs.existsSync(path.join(cwd, "questions.md"))) return;
  } catch {}

  // Skip if active campaign
  try {
    const state = JSON.parse(fs.readFileSync(path.join(cwd, "masonry-state.json"), "utf8"));
    if (state && state.mode) return;
  } catch {}

  // Write Mortar gate file
  const os = require("os");
  const gateFile = path.join(os.tmpdir(), "masonry-mortar-gate.json");
  try {
    fs.writeFileSync(gateFile, JSON.stringify({
      mortar_consulted: false, timestamp: new Date().toISOString(), prompt_summary: prompt.slice(0, 100),
    }), "utf8");
  } catch {}

  let intent = detectIntent(prompt);
  const effort = classifyEffort(prompt);

  const MASONRY_STATE_PATH = "C:/Users/trg16/Dev/Bricklayer2.0/masonry/masonry-state.json";
  if (intent) {
    try {
      const st = fs.existsSync(MASONRY_STATE_PATH) ? JSON.parse(fs.readFileSync(MASONRY_STATE_PATH, "utf8")) : {};
      st.last_route = { agent: intent.route, effort, prompt_summary: prompt.slice(0, 80), timestamp: new Date().toISOString(), turn_count: 1 };
      fs.writeFileSync(MASONRY_STATE_PATH, JSON.stringify(st, null, 2), "utf8");
    } catch {}
  } else if (isFollowUp(prompt)) {
    try {
      const st = fs.existsSync(MASONRY_STATE_PATH) ? JSON.parse(fs.readFileSync(MASONRY_STATE_PATH, "utf8")) : {};
      if (st.last_route && !isExpired(st.last_route)) {
        intent = { route: st.last_route.agent, note: "(inherited from prior turn)" };
        st.last_route.turn_count = (st.last_route.turn_count || 1) + 1;
        st.last_route.timestamp = new Date().toISOString();
        fs.writeFileSync(MASONRY_STATE_PATH, JSON.stringify(st, null, 2), "utf8");
      }
    } catch {}
  }

  const hasSignal = intent || effort !== "medium";
  if (!hasSignal) return;

  const routeStr = intent ? `Route to: ${intent.route}` : null;
  const parts = [];
  if (routeStr) parts.push(routeStr);
  parts.push(`[effort:${effort}]`);
  if (intent && intent.note) parts.push(intent.note);

  const hintText = buildHintText(intent, effort, parts.join(" "), prompt);
  process.stdout.write(JSON.stringify({ additionalContext: hintText }));
}

main().catch(() => {});

/**
 * Registry-driven keyword routing for the prompt-router hook.
 *
 * Reads agent_registry.yml routing_keywords via js-yaml.
 * Returns intent objects compatible with route-hints.js.
 *
 * Priority: registry keywords → hardcoded INTENT_RULES fallback.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

const REGISTRY_PATH = path.resolve(__dirname, "../../../agent_registry.yml");

let _registryCache = null;
let _registryCacheMtime = 0;

function loadRegistryKeywords() {
  try {
    const stat = fs.statSync(REGISTRY_PATH);
    if (_registryCache && stat.mtimeMs === _registryCacheMtime) return _registryCache;
    const raw = fs.readFileSync(REGISTRY_PATH, "utf8");
    const doc = yaml.load(raw);
    const entries = [];
    for (const agent of doc.agents || []) {
      const kws = agent.routing_keywords;
      if (!Array.isArray(kws) || kws.length === 0) continue;
      const escaped = kws.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
      const pattern = new RegExp("\\b(" + escaped.join("|") + ")\\b", "i");
      entries.push({ name: agent.name, pattern });
    }
    _registryCache = entries;
    _registryCacheMtime = stat.mtimeMs;
    return entries;
  } catch {
    return [];
  }
}

function detectRegistryIntent(prompt) {
  const entries = loadRegistryKeywords();
  for (const entry of entries) {
    if (entry.pattern.test(prompt)) {
      return { route: entry.name, note: "(registry keyword match)", registryMatch: true };
    }
  }
  return null;
}

// ─── Hardcoded fallback rules (for agents without routing_keywords) ──────────
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
    patterns: [/\b(security.?audit|penetration|owasp|vulnerability|cve|exploit)\b/i, /\/masonry-security-review\b/i],
    route: "security agent",
  },
  {
    patterns: [/\b(architect|architecture|system.?design|data.?model|erd|schema.?design|adr)\b/i],
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
    patterns: [/\b(debug|broken|error|exception|crash|failing test|traceback|stack.?trace|why is.{0,30}(not|failing|broken))\b/i],
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
    patterns: [/\b(commit|branch|merge|push|pull.?request|pr|cherry.?pick|changelog|release)\b/i, /\bgit\b(?!hub)/i],
    route: "git-nerd",
  },
  {
    patterns: [/\b(refactor|clean.?up|reorganize|restructure|rename|extract.?method|dead.?code)\b/i],
    route: "refactorer",
  },
  {
    patterns: [/\b(roadmap|docs|documentation|readme|changelog|organize.{0,20}folder|audit.{0,20}(files|dirs))\b/i],
    route: "karen",
  },
  {
    patterns: [/\b(research|investigate|analyze|study|compare|evaluate|benchmark)\b/i],
    route: "research-analyst + competitive-analyst",
  },
];

function detectIntent(prompt) {
  const registryMatch = detectRegistryIntent(prompt);
  if (registryMatch) return registryMatch;

  for (const rule of INTENT_RULES) {
    for (const pat of rule.patterns) {
      if (pat.test(prompt)) return rule;
    }
  }
  return null;
}

module.exports = { detectIntent, detectRegistryIntent, loadRegistryKeywords };

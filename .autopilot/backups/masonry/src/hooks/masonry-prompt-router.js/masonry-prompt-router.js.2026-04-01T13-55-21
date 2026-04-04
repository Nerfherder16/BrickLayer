#!/usr/bin/env node
/**
 * UserPromptSubmit hook (Masonry): Transparent intent router.
 *
 * Intercepts every user prompt before Claude sees it.
 * Detects intent and injects a routing directive:
 *   1. Registry routing_keywords (from agent_registry.yml — single source of truth)
 *   2. Hardcoded fallback patterns (for agents without routing_keywords)
 *   3. Low effort → answer inline, no agent
 *
 * NO prompt modification — only a brief routing hint injected into context.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { readStdin } = require("./session/stop-utils");
const { buildHintText } = require("./session/route-hints");
const { detectIntent } = require("./session/registry-router");

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

function classifyEffort(prompt) {
  if (/\b(full.?system|entire.?codebase|complete.?rewrite|all.?services)\b/i.test(prompt) ||
      /\b(vulnerability|exploit|cve|penetration)\b/i.test(prompt) ||
      /\/ultrawork\b|\/masonry-run\b/i.test(prompt)) return "max";
  if (/\b(architect|architecture|redesign|migrate|migration|refactor|restructure)\b/i.test(prompt) ||
      /\b(performance|optimize|bottleneck|profil)\b/i.test(prompt) ||
      /\b(multiple.{0,20}files|across.{0,20}(all|the)|throughout)\b/i.test(prompt) ||
      /\b(traceback|stack.?trace|why.{0,30}(is|are|does|won.t).{0,40}(not|fail|broken|wrong))\b/i.test(prompt) ||
      /\b(security.?audit|owasp)\b/i.test(prompt) ||
      // Scope/quantity signals: "build all 5", "implement the 3 features", etc.
      /\b(build|implement|add|create|integrate)\b.{0,15}\b(all|both|every)\b/i.test(prompt) ||
      /\b(all\s+\d+|(?:the\s+)?\d+\s+(?:features?|items?|recommendations?|changes?|gaps?))\b/i.test(prompt) ||
      /\b(end.?to.?end|from.?scratch|ground.?up|new.?system|new.?subsystem)\b/i.test(prompt)) return "high";
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

/**
 * Registry-driven keyword routing for the prompt-router hook.
 *
 * Layer 1a: Registry routing_keywords (synchronous, from agent_registry.yml)
 * Layer 1b: Hardcoded INTENT_RULES fallback (synchronous)
 * Layer 2:  Ollama semantic embedding similarity (async, 2s timeout, fails silently)
 */
"use strict";

const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const yaml = require("js-yaml");

const REGISTRY_PATH = path.resolve(__dirname, "../../../agent_registry.yml");
const EMBED_CACHE_PATH = path.join(os.tmpdir(), "masonry-agent-embed-index.json");
const EMBED_HOST = "localhost";
const EMBED_PORT = 11434;
const EMBED_MODEL = "qwen3-embedding:0.6b";
const EMBED_TIMEOUT_MS = 2000;
const SIM_THRESHOLD = 0.60;
const SIM_MARGIN = 0.05;

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

// ── Hardcoded fallback rules (agents without routing_keywords) ──────────────
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
            /\b(security.?audit|penetration|owasp|vulnerability|cve|exploit|harden\w*|security.?issue\w*)\b/i,
      /\baudit\b.{0,30}\bsecurity\b/i,
      /\bsecurity\b.{0,25}\b(config|configuration|header|headers|policy|rules)\b/i,
      /\b(rate.?limit\w*|auth.?middleware)\b/i,
      /\/masonry-security-review\b/i,
    ],
    route: "security agent",
  },
  {
    patterns: [/\b(architect|architecture|system.?design|data.?model|erd|schema.?design|adr)\b/i],
    route: "architect + design-reviewer",
  },
  {
    patterns: [
      /\b(ui|ux|figma|layout|dashboard|dark.?mode|design.?system)\b/i,
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
    // Dev tasks: verb alone is sufficient — old pattern required a specific noun
    patterns: [
      /\b(build|implement|create|add|write|develop|scaffold|fix|update|make|change|configure|apply|enable|disable|modify)\b.{0,80}\b(function|class|module|endpoint|api|service|page|route|feature|test|hook|script|command|tool|plugin|integration|handler|middleware|component|model|schema|migration|worker|button|form|table|widget)\b/i,
      /\b(implement|scaffold|develop|create).{0,40}(using|with|for|in)\b/i,
      /\b(add.{0,20}feature|write.?code|code.?this|set.?up.{0,20}(the|a))\b/i,
      /\/build\b|\/ultrawork\b/i,
    ],
    route: "rough-in → queen-coordinator → workers",
    note: "Rough-in decomposes, Queen dispatches up to 8 agents in parallel.",
  },
  {
    patterns: [
      /\b(write.?a.?spec|create.?a.?spec|spec.?out|product.?requirements|prd|requirements.?doc)\b/i,
      /\b(plan.?out|plan.?this|blueprint.?the|write.?a.?plan.?for)\b/i,
      /\b(spec.?to.?build|plan.?to.?implement|feature.?spec|feature.?plan)\b/i,
    ],
    route: "spec-writer → developer pipeline",
    note: "Use /plan for full spec-to-build pipeline.",
  },
  {
    patterns: [/\b(commit|branch|merge|push|pull.?request|pr|cherry.?pick)\b/i, /\bgit\b(?!hub)/i],
    route: "git-nerd",
  },
  {
    patterns: [/\b(refactor|clean.?up|reorganize|restructure|rename|extract.?method|dead.?code)\b/i],
    route: "refactorer",
  },
  {
    patterns: [/\b(roadmap|docs|documentation|readme|changelog|release.?notes|release.?process|organize.{0,20}folder|audit.{0,20}(files|dirs))\b/i],
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

// ── Layer 2: Semantic routing via Ollama embeddings ───────────────────────────

function cosineSim(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  const denom = Math.sqrt(na) * Math.sqrt(nb);
  return denom === 0 ? 0 : dot / denom;
}

function fetchEmbeddings(inputs, timeoutMs) {
  return new Promise((resolve) => {
    const body = JSON.stringify({ model: EMBED_MODEL, input: inputs });
    const opts = {
      hostname: EMBED_HOST,
      port: EMBED_PORT,
      path: "/api/embed",
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
      timeout: timeoutMs,
    };
    const req = http.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString()).embeddings || null); }
        catch { resolve(null); }
      });
    });
    req.on("error", () => resolve(null));
    req.on("timeout", () => { req.destroy(); resolve(null); });
    req.write(body);
    req.end();
  });
}

async function buildEmbedIndex() {
  try {
    const regStat = fs.statSync(REGISTRY_PATH);
    try {
      const cached = JSON.parse(fs.readFileSync(EMBED_CACHE_PATH, "utf8"));
      if (cached.registryMtime === regStat.mtimeMs && Array.isArray(cached.agents) && cached.agents.length > 0) {
        return cached.agents;
      }
    } catch { /* cache miss */ }

    const doc = yaml.load(fs.readFileSync(REGISTRY_PATH, "utf8"));
    const agents = (doc.agents || []).filter((a) => a.name && a.description);
    const texts = agents.map((a) => {
      const caps = Array.isArray(a.capabilities)
        ? a.capabilities.slice(0, 3).map((c) => (typeof c === "string" ? c : Object.keys(c)[0])).join(", ")
        : "";
      return a.name + ": " + a.description + (caps ? ". " + caps : "");
    });

    const embeddings = await fetchEmbeddings(texts, 5000);
    if (!embeddings || embeddings.length !== agents.length) return null;

    const index = agents.map((a, i) => ({ name: a.name, embedding: embeddings[i] }));
    try { fs.writeFileSync(EMBED_CACHE_PATH, JSON.stringify({ registryMtime: regStat.mtimeMs, agents: index }), "utf8"); }
    catch { /* non-fatal */ }
    return index;
  } catch {
    return null;
  }
}

async function detectSemanticIntent(prompt) {
  try {
    const [promptEmbeds, agentIndex] = await Promise.all([
      fetchEmbeddings([prompt], EMBED_TIMEOUT_MS),
      buildEmbedIndex(),
    ]);
    if (!promptEmbeds || !promptEmbeds[0] || !agentIndex) return null;
    const promptVec = promptEmbeds[0];

    let best = null;
    let secondSim = 0;
    for (const agent of agentIndex) {
      const sim = cosineSim(promptVec, agent.embedding);
      if (!best || sim > best.sim) { secondSim = best ? best.sim : 0; best = { name: agent.name, sim }; }
      else if (sim > secondSim) { secondSim = sim; }
    }
    if (!best || best.sim < SIM_THRESHOLD || (best.sim - secondSim) < SIM_MARGIN) return null;
    return { route: best.name, note: "(semantic match, sim=" + best.sim.toFixed(3) + ")", semanticMatch: true };
  } catch {
    return null;
  }
}

async function detectIntentAsync(prompt) {
  const l1 = detectIntent(prompt);
  if (l1) return l1;
  return detectSemanticIntent(prompt);
}

module.exports = { detectIntent, detectIntentAsync, detectRegistryIntent, loadRegistryKeywords };

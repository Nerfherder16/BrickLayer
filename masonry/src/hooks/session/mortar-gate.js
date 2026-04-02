"use strict";
/**
 * session/mortar-gate.js — Mortar routing gate for subagent spawns.
 *
 * Maintains the set of recognized specialist agent types and provides
 * the isMortarGated() check used by masonry-subagent-tracker.js.
 *
 * Agent names are loaded dynamically from agent_registry.yml and
 * .claude/agents/*.md frontmatter so the fleet stays in sync automatically.
 * The hardcoded BUILTIN_TYPES set covers Claude Code built-ins and a
 * minimal bootstrap fallback for when the registry cannot be read.
 */

const fs = require("fs");
const path = require("path");

// Orchestrators: coordinate work but never write production code.
const ORCHESTRATORS = new Set(["mortar", "rough-in", "trowel"]);

// What each orchestrator is allowed to spawn.
// null = any recognized specialist.
const ORCHESTRATOR_ALLOWED_CHILDREN = {
  "mortar": new Set(["rough-in", "trowel", "karen", "explore"]),
  "rough-in": null,
  "trowel": null,
};

// Claude Code built-ins + bootstrap names that must always be allowed.
const BUILTIN_TYPES = new Set([
  "Explore", "explore", "general-purpose",
  "masonry:mortar", "mortar", "rough-in", "trowel",
]);

// ── Dynamic registry loader ───────────────────────────────────────────────────
// Resolves relative to this file: masonry/src/hooks/session/ → masonry/
const REGISTRY_PATH = path.resolve(__dirname, "../../../agent_registry.yml");
const AGENTS_DIR = path.resolve(__dirname, "../../../../.claude/agents");

let _cache = null;
let _cacheMtime = 0;
let _agentsDirMtime = 0;

function loadDispatchedTypes() {
  try {
    const regStat = fs.existsSync(REGISTRY_PATH) ? fs.statSync(REGISTRY_PATH) : null;
    const dirStat = fs.existsSync(AGENTS_DIR) ? fs.statSync(AGENTS_DIR) : null;
    const regMtime = regStat ? regStat.mtimeMs : 0;
    const dirMtime = dirStat ? dirStat.mtimeMs : 0;

    if (_cache && regMtime === _cacheMtime && dirMtime === _agentsDirMtime) return _cache;

    const names = new Set(BUILTIN_TYPES);

    // Load from agent_registry.yml
    if (regStat) {
      const raw = fs.readFileSync(REGISTRY_PATH, "utf8");
      // Simple line-based parse — avoid js-yaml dep assumption
      for (const line of raw.split("\n")) {
        const m = line.match(/^\s{2}-?\s*name:\s*["']?([^"'\s]+)["']?/);
        if (m) names.add(m[1].trim().toLowerCase());
      }
    }

    // Load from .claude/agents/*.md frontmatter `name:` field
    if (dirStat) {
      for (const file of fs.readdirSync(AGENTS_DIR)) {
        if (!file.endsWith(".md")) continue;
        try {
          const content = fs.readFileSync(path.join(AGENTS_DIR, file), "utf8");
          const fm = content.match(/^---\s*\n([\s\S]*?)\n---/);
          if (!fm) continue;
          const nameMatch = fm[1].match(/^name:\s*["']?([^"'\n]+)["']?/m);
          if (nameMatch) names.add(nameMatch[1].trim().toLowerCase());
        } catch { /* skip unreadable files */ }
      }
    }

    _cache = names;
    _cacheMtime = regMtime;
    _agentsDirMtime = dirMtime;
    return names;
  } catch {
    return BUILTIN_TYPES;
  }
}

// Expose a stable reference — callers who imported MORTAR_DISPATCHED_TYPES
// directly get a live proxy via the function instead.
const MORTAR_DISPATCHED_TYPES = { has: (v) => loadDispatchedTypes().has(v) };

/**
 * Returns true if the subagent spawn should be blocked (not a recognized specialist).
 */
function isMortarGated(input) {
  const types = loadDispatchedTypes();
  const subagentType = (input.subagent_type || "").trim().toLowerCase();

  if (!subagentType) {
    const agentName = (input.agent_name || input.agent_type || "").trim().toLowerCase();
    if (agentName && types.has(agentName)) {
      return false; // allow — already a specialist
    }
    return true; // untagged spawn from main context
  }

  return !types.has(subagentType);
}

module.exports = { isMortarGated, MORTAR_DISPATCHED_TYPES, ORCHESTRATORS, ORCHESTRATOR_ALLOWED_CHILDREN };

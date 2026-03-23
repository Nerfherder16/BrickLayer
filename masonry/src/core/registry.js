"use strict";
// src/core/registry.js — Agent Registry Generator
// Scans .claude/agents/*.md, parses YAML frontmatter, writes registry.json.
// Zero external dependencies — regex-only YAML parsing.

const fs = require("fs");
const path = require("path");

/**
 * Parse YAML frontmatter from a markdown file.
 * Handles only simple key: value lines (single-line values).
 * Returns null if no frontmatter found or no 'name' field.
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;

  const lines = match[1].split(/\r?\n/);
  const fields = {};
  let currentKey = null;
  let isBlock = false; // true when value is a YAML block scalar (> or |)
  const blockLines = [];

  for (const line of lines) {
    const kv = line.match(/^(\w[\w-]*):\s*(.*)$/);
    if (kv) {
      // Flush previous block
      if (isBlock && currentKey && blockLines.length) {
        fields[currentKey] = blockLines.join(" ").trim();
        blockLines.length = 0;
        isBlock = false;
      }
      currentKey = kv[1];
      const val = kv[2].trim();
      if (val === ">" || val === "|") {
        // YAML block scalar — collect continuation lines
        isBlock = true;
      } else {
        fields[currentKey] = val;
        isBlock = false;
      }
    } else if (isBlock && currentKey && /^\s+/.test(line)) {
      // Continuation line for block scalar
      blockLines.push(line.trim());
    } else if (isBlock && currentKey && line.trim() === "") {
      // Empty line ends the block
      fields[currentKey] = blockLines.join(" ").trim();
      blockLines.length = 0;
      isBlock = false;
      currentKey = null;
    }
  }

  // Flush trailing block
  if (isBlock && currentKey && blockLines.length) {
    fields[currentKey] = blockLines.join(" ").trim();
  }

  // Must have a name field to be a valid agent
  if (!fields.name) return null;
  return fields;
}

/**
 * Generate registry.json from all agent .md files in a project.
 * @param {string} projectDir — absolute path to project root
 * @returns {object} the registry object (also written to disk)
 */
function generateRegistry(projectDir) {
  const agentsDir = path.join(projectDir, ".claude", "agents");
  const registryFile = path.join(projectDir, "registry.json");

  const agents = [];

  if (fs.existsSync(agentsDir)) {
    let files;
    try {
      files = fs.readdirSync(agentsDir).filter((f) => f.endsWith(".md"));
    } catch (_e) {
      files = [];
    }

    for (const file of files) {
      const filePath = path.join(agentsDir, file);
      let content;
      try {
        content = fs.readFileSync(filePath, "utf8");
      } catch (_e) {
        continue;
      }

      const fm = parseFrontmatter(content);
      if (!fm) continue; // skip files without valid frontmatter + name

      agents.push({
        name: fm.name,
        file: path.join(".claude", "agents", file).replace(/\\/g, "/"),
        model: fm.model || "sonnet",
        description: fm.description || "",
        tier: fm.tier || "standard",
      });
    }
  }

  // Sort alphabetically by name
  agents.sort((a, b) => a.name.localeCompare(b.name));

  const registry = {
    generated_at: new Date().toISOString(),
    agents,
  };

  fs.writeFileSync(registryFile, JSON.stringify(registry, null, 2), "utf8");
  return registry;
}

/**
 * Read an existing registry.json.
 * @param {string} projectDir
 * @returns {object|null} parsed registry or null if missing/corrupt
 */
function readRegistry(projectDir) {
  const registryFile = path.join(projectDir, "registry.json");
  try {
    if (!fs.existsSync(registryFile)) return null;
    return JSON.parse(fs.readFileSync(registryFile, "utf8"));
  } catch (_e) {
    return null;
  }
}

module.exports = { generateRegistry, readRegistry };

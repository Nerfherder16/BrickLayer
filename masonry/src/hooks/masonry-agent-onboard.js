#!/usr/bin/env node
/**
 * PostToolUse hook — auto-onboard new agent .md files to the registry.
 * Triggers when Write or Edit is called on a path matching /agents/*.md
 * and the file has YAML frontmatter with a `name:` field.
 */
"use strict";

const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { readStdin } = require('./session/stop-utils');

/**
 * Detect common anti-patterns in agent metadata.
 *
 * @param {object} metadata    - Parsed YAML frontmatter fields
 * @param {string} filePath    - Path to the agent file (for messages)
 * @param {string} fileContent - Raw file content (for size check)
 * @returns {string[]} Array of warning/info strings (empty = clean)
 */
function detectAntiPatterns(metadata, filePath, fileContent) {
  const warnings = [];

  // 1. OVER_CONSTRAINED: description has >5 "never/always/must" directives
  const constraintWords =
    (metadata.description || "").match(
      /\b(never|always|must|required|mandatory)\b/gi
    ) || [];
  if (constraintWords.length > 5) {
    warnings.push(
      `[WARN] ANTI_PATTERN:OVER_CONSTRAINED in ${filePath}: description contains ${constraintWords.length} constraint directives (never/always/must). Consider softening to guidance.`
    );
  }

  // 2. EMPTY_DESCRIPTION: description missing, null, or <10 chars
  const desc = metadata.description || "";
  if (!desc || desc.trim().length < 10) {
    warnings.push(
      `[WARN] ANTI_PATTERN:EMPTY_DESCRIPTION in ${filePath}: description is missing or too short (<10 chars). Add a meaningful description.`
    );
  }

  // 3. MISSING_TRIGGER: triggers array is empty or missing
  const triggers = metadata.triggers || [];
  if (!triggers || triggers.length === 0) {
    warnings.push(
      `[INFO] ANTI_PATTERN:MISSING_TRIGGER in ${filePath}: triggers array is empty. Add trigger phrases to improve discoverability.`
    );
  }

  // 4. BLOATED_SKILL: file content > 50 KB
  const fileSizeKB = Buffer.byteLength(fileContent, "utf8") / 1024;
  if (fileSizeKB > 50) {
    warnings.push(
      `[WARN] ANTI_PATTERN:BLOATED_SKILL in ${filePath}: file is ${fileSizeKB.toFixed(1)}KB (>50KB limit). Consider splitting into focused sub-agents.`
    );
  }

  // 5. ORPHAN_REFERENCE: mcp__ tools that don't match mcp__server__tool format
  const tools = metadata.tools || [];
  for (const tool of tools) {
    if (typeof tool === "string" && tool.startsWith("mcp__")) {
      const parts = tool.split("__");
      if (parts.length < 3) {
        warnings.push(
          `[WARN] ANTI_PATTERN:ORPHAN_REFERENCE in ${filePath}: tool "${tool}" doesn't match mcp__server__tool format.`
        );
      }
    }
  }

  return warnings;
}

/**
 * Parse simple YAML frontmatter key: value pairs.
 * Handles scalar values and inline arrays (- item).
 *
 * @param {string} fmBody - The text between the --- delimiters
 * @returns {object}
 */
function parseFrontmatter(fmBody) {
  const result = {};
  let currentKey = null;
  for (const line of fmBody.split("\n")) {
    const listItemMatch = line.match(/^\s+-\s+(.+)$/);
    const keyValueMatch = line.match(/^(\w[\w-]*):\s*(.*)$/);
    if (listItemMatch && currentKey) {
      if (!Array.isArray(result[currentKey])) result[currentKey] = [];
      result[currentKey].push(listItemMatch[1].trim());
    } else if (keyValueMatch) {
      currentKey = keyValueMatch[1];
      const val = keyValueMatch[2].trim();
      result[currentKey] = val === "" ? undefined : val;
    }
  }
  return result;
}

async function main() {
  const raw = await readStdin();
  let event = {};
  try { event = JSON.parse(raw); } catch {}

  const toolName = event.tool_name || event.toolName || "";
  const filePath = event.tool_input?.file_path || event.tool_input?.path || "";

  // Only trigger for Write/Edit on direct children of an agents/ directory
  if (!["Write", "Edit"].includes(toolName)) {
    process.exit(0);
  }

  // Match: /agents/something.md (direct child only, not subdirectory)
  const agentFileRegex = /[/\\]agents[/\\][^/\\]+\.md$/;
  if (!agentFileRegex.test(filePath)) {
    process.exit(0);
  }

  // Guard: only onboard files with YAML frontmatter containing `name:` field.
  // This prevents synthesis.md, AUDIT_REPORT.md, and other .md files in agents/
  // directories from being accidentally onboarded as agents.
  let content;
  try {
    content = fs.readFileSync(filePath, "utf8");
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch || !/^\s*name\s*:/m.test(fmMatch[1])) {
      process.exit(0);
    }

    // Parse frontmatter and run anti-pattern checks before onboarding
    const metadata = parseFrontmatter(fmMatch[1]);
    const antiPatternWarnings = detectAntiPatterns(metadata, filePath, content);
    for (const warning of antiPatternWarnings) {
      process.stderr.write(warning + "\n");
    }
  } catch {
    // If we can't read the file (e.g. it was deleted), skip onboarding.
    process.exit(0);
  }

  const filename = path.basename(filePath);
  process.stderr.write(`[ONBOARD] Detected new/modified agent: ${filename} — triggering onboard pipeline\n`);

  // Spawn onboard script non-blocking (detached)
  const cwd = event.cwd || process.cwd();
  const scriptPath = path.join(cwd, "masonry", "scripts", "onboard_agent.py");

  const child = spawn("python", [scriptPath], {
    detached: true,
    windowsHide: true,
    stdio: "ignore",
    cwd,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.exit(0);
}

main().catch(() => process.exit(0));

module.exports = { detectAntiPatterns };

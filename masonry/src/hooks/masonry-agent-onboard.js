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

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 1000);
  });
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
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch || !/^\s*name\s*:/m.test(fmMatch[1])) {
      process.exit(0);
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
    stdio: "ignore",
    cwd,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.exit(0);
}

main().catch(() => process.exit(0));

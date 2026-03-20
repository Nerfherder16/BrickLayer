#!/usr/bin/env node
/**
 * Stop hook: Detect BrickLayer sessions and queue retrospective.
 *
 * Runs async on every Claude Code stop. If the session was in or adjacent to
 * a BrickLayer project, writes a .retro-pending marker so the launcher can
 * offer to run the retrospective agent automatically.
 *
 * Always exits 0 — never blocks stopping.
 */

const { readFileSync, writeFileSync, existsSync, mkdirSync } = require("fs");
const { join, sep } = require("path");

const AUTOSEARCH_ROOT = "C:/Users/trg16/Dev/autosearch";
const MARKER_FILE = join(AUTOSEARCH_ROOT, ".retro-pending");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 1500);
  });
}

function detectProject(cwd) {
  // Check if cwd is inside autosearch/projects/{name}/
  const normalized = cwd.replace(/\\/g, "/");
  const match = normalized.match(/autosearch\/projects\/([^/]+)/i);
  if (match) return match[1];

  // Check if cwd is the autosearch root itself
  if (normalized.toLowerCase().includes("autosearch")) return "recall";

  // Check if cwd is a known BrickLayer target repo — look for results.tsv
  const projectsDir = join(AUTOSEARCH_ROOT, "projects");
  if (!existsSync(projectsDir)) return null;

  try {
    const { readdirSync } = require("fs");
    for (const name of readdirSync(projectsDir)) {
      try {
        const cfg = JSON.parse(readFileSync(join(projectsDir, name, "project.json"), "utf8"));
        if (cfg.target_git && cwd.toLowerCase().startsWith(cfg.target_git.toLowerCase())) {
          return name;
        }
      } catch {}
    }
  } catch {}

  return null;
}

function hasRecentFindings(projectName) {
  const tsvPath = join(AUTOSEARCH_ROOT, "projects", projectName, "results.tsv");
  if (!existsSync(tsvPath)) return false;

  try {
    const lines = readFileSync(tsvPath, "utf8").trim().split("\n").slice(1); // skip header
    return lines.some((l) => l.includes("FAILURE") || l.includes("WARNING") || l.includes("IN_PROGRESS"));
  } catch {
    return false;
  }
}

async function main() {
  const input = await readStdin();
  if (!input) return;

  let parsed;
  try { parsed = JSON.parse(input); } catch { return; }

  const cwd = (parsed.cwd || "").replace(/\\/g, "/");
  const sessionId = parsed.session_id || "";

  const projectName = detectProject(cwd);
  if (!projectName) return; // Not a BrickLayer session

  if (!hasRecentFindings(projectName)) return; // Nothing worth reviewing

  // Write the marker
  const marker = {
    project: projectName,
    session_id: sessionId,
    cwd,
    timestamp: new Date().toISOString(),
  };

  try {
    writeFileSync(MARKER_FILE, JSON.stringify(marker, null, 2), "utf8");
  } catch {}
}

main().catch(() => {}).finally(() => process.exit(0));

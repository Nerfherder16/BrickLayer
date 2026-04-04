#!/usr/bin/env node
/**
 * Stop hook (Masonry): Store a structured session summary to Recall.
 *
 * Reads the session activity log written by masonry-observe.js, derives a
 * summary without calling Ollama, and stores a structured object to Recall.
 *
 * Always exits 0 — never blocks stopping.
 * Designed to complete in under 3 seconds total.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const { loadConfig } = require("../core/config");
const { readState } = require("../core/state");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------


function normalizeCwd(p) {
  // Convert POSIX /c/Users/... paths to Windows C:\Users\... so fs ops work
  if (process.platform === "win32" && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ":" + p.slice(2).replace(/\//g, "\\");
  }
  return p;
}

/**
 * Derive a canonical domain string from the project directory name.
 * Must be kept in sync with C:/Users/trg16/Dev/Recall/hooks/domains.js
 * (cross-repo — cannot require() directly, so sync manually on changes).
 */
function deriveDomain(cwdOrProjectName) {
  const name = path.basename(cwdOrProjectName).toLowerCase();

  const DOMAIN_MAP = {
    recall: "recall",
    "system-recall": "recall",
    "recall-arch-frontier": "recall",
    reminisce: "recall",
    familyhub: "family-hub",
    "family-hub": "family-hub",
    sadie: "family-hub",
    relay: "relay",
    codevv: "codevv",
    foundry: "foundry",
    "media-server": "media-server",
    jellyfin: "media-server",
    homelab: "homelab",
    "mcp-proxmox": "homelab",
    "bricklayer2.0": "autoresearch",
    autoresearch: "autoresearch",
    autosearch: "autoresearch",
    adbp: "autoresearch",
    masonry: "masonry",
    "file-converter": "file-converter",
    "file-converter-squoosh-parity": "file-converter",
  };

  return DOMAIN_MAP[name] || name;
}

/**
 * Read and parse the NDJSON activity log for this session.
 * Returns an array of activity entries; empty array if the log is missing or invalid.
 */
function readActivityLog(sessionId) {
  const logPath = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
  try {
    if (!fs.existsSync(logPath)) return { entries: [], logPath: null };
    const raw = fs.readFileSync(logPath, "utf8");
    const entries = raw
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        try { return JSON.parse(line); }
        catch { return null; }
      })
      .filter(Boolean);
    return { entries, logPath };
  } catch {
    return { entries: [], logPath };
  }
}

/**
 * Group activity entries by directory and extract unique file paths and names.
 * Returns { filesChanged, filesByDir }
 */
function analyzeActivity(entries, cwd) {
  const fileSet = new Set();
  const dirMap = new Map(); // dir → Set of basenames

  // Normalise cwd for relative path extraction
  const cwdNorm = cwd.replace(/\\/g, "/").replace(/\/$/, "");

  for (const entry of entries) {
    if (!entry.file) continue;
    const filePath = entry.file.replace(/\\/g, "/");

    // Compute a project-relative path if possible
    const rel = filePath.startsWith(cwdNorm + "/")
      ? filePath.slice(cwdNorm.length + 1)
      : path.basename(filePath);

    fileSet.add(rel);

    const dir = rel.includes("/") ? rel.split("/").slice(0, -1).join("/") : ".";
    if (!dirMap.has(dir)) dirMap.set(dir, new Set());
    dirMap.get(dir).add(path.basename(rel));
  }

  return {
    filesChanged: [...fileSet],
    filesByDir: dirMap,
  };
}

/**
 * Produce a 1-2 sentence human-readable summary from activity analysis.
 * No LLM calls — purely pattern-based.
 */
function buildSummaryText(filesChanged, filesByDir, campaignCtx, projectName) {
  if (filesChanged.length === 0) {
    return `Session in ${projectName} — no file edits recorded.`;
  }

  const parts = [];

  // Describe each directory's activity
  for (const [dir, names] of filesByDir.entries()) {
    const nameList = [...names];
    const dirLabel = dir === "." ? "project root" : dir;

    if (nameList.length === 1) {
      parts.push(`Modified ${nameList[0]} in ${dirLabel}`);
    } else if (nameList.length <= 4) {
      const listed = nameList.map((n) => n.replace(/\.(py|js|ts|tsx|jsx|md)$/, "")).join(", ");
      parts.push(`Updated ${nameList.length} files in ${dirLabel}/ (${listed})`);
    } else {
      parts.push(`Updated ${nameList.length} files in ${dirLabel}/`);
    }
  }

  let summary = parts.join(". ");

  // Append campaign context if present
  if (campaignCtx && campaignCtx.project) {
    const answered = campaignCtx.questions_answered;
    const wave = campaignCtx.wave;
    const ctxParts = [`Campaign: ${campaignCtx.project}`];
    if (wave) ctxParts.push(`wave ${wave}`);
    if (answered) ctxParts.push(`${answered} question(s) answered`);
    summary += ". " + ctxParts.join(", ") + ".";
  }

  return summary;
}

/**
 * Derive campaign context from masonry-state.json (if present in cwd).
 */
function readCampaignContext(cwd) {
  const state = readState(cwd);
  if (!state) return null;

  // masonry-state.json shape: { project, wave, verdicts, last_qid, ... }
  const answered = state.verdicts
    ? Object.values(state.verdicts).reduce((a, b) => a + b, 0)
    : undefined;

  return {
    project: state.project || undefined,
    wave: state.wave || undefined,
    questions_answered: answered || undefined,
    last_qid: state.last_qid || undefined,
    last_verdict: state.last_verdict || undefined,
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const input = await readStdin();
  // Always exit 0 — parse failures must never block stopping
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  // Avoid recursive firing when stop_hook_active is set
  if (parsed.stop_hook_active) process.exit(0);

  const { getSessionId, readStdin } = require('./session/stop-utils');
  const sessionId = getSessionId(parsed);
  const cwd = normalizeCwd(parsed.cwd || process.cwd());
  const projectName = path.basename(cwd);

  // --- Read activity log ---
  const { entries, logPath } = readActivityLog(sessionId);

  // --- Read campaign context ---
  const campaignCtx = readCampaignContext(cwd);

  // --- Analyse activity ---
  const { filesChanged, filesByDir } = analyzeActivity(entries, cwd);

  // --- Build summary text (no Ollama) ---
  const summaryText = buildSummaryText(filesChanged, filesByDir, campaignCtx, projectName);

  // --- Build structured summary object ---
  const structured = {
    type: "masonry_build_telemetry",
    project: projectName,
    domain: deriveDomain(projectName),
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    files_changed: filesChanged,
    // functions_added is always [] — function names are extracted by masonry-observe.js
    // and stored to Recall as code-facts during the session; they're not in the activity log
    functions_added: [],
    campaign_context: campaignCtx || {},
    summary: summaryText,
    next_steps: [],
  };

  // --- Store to Recall (fire-and-forget with 5s timeout) ---
  const tags = ["session-summary", "masonry", projectName];
  if (campaignCtx && campaignCtx.project) {
    tags.push(`campaign:${campaignCtx.project}`);
  }

  try {
    const cfg = loadConfig();
    const headers = {
      "Content-Type": "application/json",
      ...(cfg.recallApiKey ? { Authorization: `Bearer ${cfg.recallApiKey}` } : {}),
    };

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    await fetch(`${cfg.recallHost}/memory/store`, {
      method: "POST",
      headers,
      signal: controller.signal,
      body: JSON.stringify({
        content: summaryText,
        domain: structured.domain,
        tags,
        importance: 0.75,
        metadata: structured,
      }),
    });

    clearTimeout(timeout);
  } catch {
    // Recall unreachable or timed out — exit silently
  }

  // --- Clean up activity log ---
  if (logPath) {
    try { fs.unlinkSync(logPath); } catch { /* non-fatal */ }
  }

}

main().catch(() => {});

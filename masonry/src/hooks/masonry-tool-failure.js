#!/usr/bin/env node
/**
 * PostToolUseFailure hook (Masonry): Error tracking + retry guidance.
 *
 * On tool failure:
 * - Writes error state to <cwd>/.masonry/state/last-error.json
 * - Injects "analyze, fix, and continue" guidance
 * - Tracks retry count; after 3 failures on same error, escalates to spawn-agent guidance
 *
 * Replaces OMC's post-tool-use-failure.mjs
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

const MAX_RETRIES = 3;
const RETRY_WINDOW_MS = 120_000; // 2 minutes

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function ensureDir(p) {
  try {
    fs.mkdirSync(p, { recursive: true });
  } catch (_) {}
}

function fingerprint(toolName, errorText) {
  // Simple fingerprint: first 80 chars of error after stripping whitespace
  const clean = (errorText || "").replace(/\s+/g, " ").trim().slice(0, 80);
  return `${toolName}:${clean}`;
}

async function main() {
  const raw = await readStdin();
  if (!raw) process.exit(0);

  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const cwd = input.cwd || process.cwd();
  const toolName = input.tool_name || "unknown";
  const errorText = input.tool_response || input.error || "";
  const stateDir = path.join(cwd, ".masonry", "state");

  ensureDir(stateDir);
  const stateFile = path.join(stateDir, "last-error.json");

  // Load existing error state
  let state = { fp: "", retries: 0, firstSeen: 0 };
  try {
    state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
  } catch (_) {}

  const fp = fingerprint(toolName, errorText);
  const now = Date.now();
  const withinWindow = now - (state.firstSeen || 0) < RETRY_WINDOW_MS;
  const sameError = state.fp === fp;

  let retries = (sameError && withinWindow) ? (state.retries || 0) + 1 : 1;

  // Write updated state
  try {
    fs.writeFileSync(
      stateFile,
      JSON.stringify({ fp, retries, firstSeen: sameError && withinWindow ? state.firstSeen : now, toolName, ts: now }, null, 2),
      "utf8"
    );
  } catch (_) {}

  // Build guidance output
  const errSnippet = errorText.slice(0, 400).replace(/\n/g, " ").trim();

  if (retries >= MAX_RETRIES) {
    // 3-strike rule: escalate to spawn research agent
    process.stderr.write(
      `\n[Masonry] Tool "${toolName}" failed ${retries} times with similar error.\n` +
      `Error: ${errSnippet}\n\n` +
      `3-strike rule triggered. STOP retrying. Spawn a research agent (oh-my-claudecode:debugger or ` +
      `oh-my-claudecode:build-fixer) to investigate the root cause before attempting again.\n`
    );
  } else {
    // Standard guidance: analyze, fix, continue
    process.stderr.write(
      `\n[Masonry] Tool "${toolName}" failed (attempt ${retries}/${MAX_RETRIES}).\n` +
      `Analyze the error, fix the issue, and continue working.\n`
    );
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

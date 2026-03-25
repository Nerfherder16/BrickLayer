#!/usr/bin/env node
/**
 * masonry-training-export.js
 *
 * Async Stop hook — fires after masonry-score-trigger.js completes.
 * Exports BrickLayer campaign traces to the training system.
 *
 * Only runs when BRICKLAYER_TRAINING_DB env var is set.
 * Skips silently if not configured — zero impact on normal sessions.
 *
 * Registration in hooks.json (add after masonry-score-trigger entry):
 *   {
 *     "matcher": {"type": "Stop"},
 *     "hooks": [{
 *       "type": "command",
 *       "command": "node ${CLAUDE_PLUGIN_ROOT}/masonry/src/hooks/masonry-training-export.js"
 *     }]
 *   }
 */

const { execSync, spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

// ── Config ──────────────────────────────────────────────────────────────────

const BL_ROOT = process.env.CLAUDE_PLUGIN_ROOT || process.cwd();
const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB;
const EXPORT_SCRIPT = path.join(BL_ROOT, "bl", "training_export.py");
const RATE_LIMIT_FILE = path.join(BL_ROOT, ".mas", "training_export_last_run");
const RATE_LIMIT_HOURS = 1; // don't export more than once per hour

// ── Guard: only run if configured ───────────────────────────────────────────

if (!TRAINING_DB) {
  // Silent exit — BRICKLAYER_TRAINING_DB not set, training export not configured
  process.exit(0);
}

if (!fs.existsSync(EXPORT_SCRIPT)) {
  process.stderr.write(
    `[masonry-training-export] WARNING: ${EXPORT_SCRIPT} not found, skipping\n`
  );
  process.exit(0);
}

// ── Rate limiting ────────────────────────────────────────────────────────────

function isRateLimited() {
  if (!fs.existsSync(RATE_LIMIT_FILE)) return false;
  try {
    const lastRun = parseInt(fs.readFileSync(RATE_LIMIT_FILE, "utf8").trim(), 10);
    const hoursSince = (Date.now() - lastRun) / (1000 * 60 * 60);
    return hoursSince < RATE_LIMIT_HOURS;
  } catch {
    return false;
  }
}

function markRun() {
  const dir = path.dirname(RATE_LIMIT_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(RATE_LIMIT_FILE, String(Date.now()), "utf8");
}

if (isRateLimited()) {
  process.stdout.write("[masonry-training-export] rate-limited, skipping (< 1h since last run)\n");
  process.exit(0);
}

// ── Detect Python ────────────────────────────────────────────────────────────

function findPython() {
  for (const cmd of ["python3", "python"]) {
    try {
      const result = spawnSync(cmd, ["--version"], { encoding: "utf8" });
      if (result.status === 0) return cmd;
    } catch {}
  }
  return null;
}

const python = findPython();
if (!python) {
  process.stderr.write("[masonry-training-export] WARNING: Python not found, skipping\n");
  process.exit(0);
}

// ── Run export ───────────────────────────────────────────────────────────────

process.stdout.write("[masonry-training-export] exporting campaign traces...\n");
markRun();

const args = [
  EXPORT_SCRIPT,
  "--bl-root", BL_ROOT,
  "--db", TRAINING_DB,
];

const result = spawnSync(python, args, {
  cwd: BL_ROOT,
  encoding: "utf8",
  timeout: 60_000, // 60s max — export should be fast
  env: { ...process.env },
});

if (result.stdout) {
  process.stdout.write(result.stdout);
}

if (result.stderr) {
  process.stderr.write(result.stderr);
}

if (result.status !== 0 || result.error) {
  const err = result.error ? result.error.message : `exit code ${result.status}`;
  process.stderr.write(`[masonry-training-export] export failed: ${err}\n`);
  // Non-fatal — don't block session stop on export failure
  process.exit(0);
}

process.stdout.write("[masonry-training-export] done\n");
process.exit(0);

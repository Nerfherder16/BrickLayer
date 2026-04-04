#!/usr/bin/env node
/**
 * masonry-training-export.js
 *
 * Async Stop hook — fires after masonry-score-trigger.js completes.
 * Exports BrickLayer campaign traces to the training system.
 *
 * Defaults to ~/.mas/training.db when BRICKLAYER_TRAINING_DB env var is not set.
 * Set BRICKLAYER_TRAINING_DB to override the database path.
 *
 * Registration in settings.json (add after masonry-score-trigger entry):
 *   {
 *     "type": "command",
 *     "command": "node C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-training-export.js",
 *     "timeout": 65,
 *     "async": true
 *   }
 */

const { spawn, spawnSync } = require("child_process");
const os = require("os");
const path = require("path");
const fs = require("fs");

// ── Config ──────────────────────────────────────────────────────────────────

const BL_ROOT = process.env.CLAUDE_PLUGIN_ROOT || process.cwd();
const DEFAULT_TRAINING_DB = path.join(os.homedir(), ".mas", "training.db");
const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB || DEFAULT_TRAINING_DB;
const EXPORT_SCRIPT = path.join(BL_ROOT, "bl", "training_export.py");
const RATE_LIMIT_FILE = path.join(BL_ROOT, ".mas", "training_export_last_run");
const RATE_LIMIT_HOURS = 1; // don't export more than once per hour

// ── Ensure ~/.mas/ directory exists ─────────────────────────────────────────

const trainingDbDir = path.dirname(TRAINING_DB);
if (!fs.existsSync(trainingDbDir)) {
  fs.mkdirSync(trainingDbDir, { recursive: true });
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
  process.stderr.write("[masonry-training-export] rate-limited, skipping (< 1h since last run)\n");
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

// ── Load pattern confidence scores for export ────────────────────────────────

let patternConfidence = {};
const cwd = process.env.CLAUDE_WORKING_DIRECTORY || process.cwd();
try {
  const confPath = path.join(cwd, '.autopilot', 'pattern-confidence.json');
  patternConfidence = JSON.parse(fs.readFileSync(confPath, 'utf8'));
} catch {}

// Build confidence summary line if there are entries
const confKeys = Object.keys(patternConfidence);
if (confKeys.length > 0) {
  const scores = confKeys.map(k => {
    const raw = patternConfidence[k];
    const score = (typeof raw === 'object' && raw !== null) ? (raw.confidence ?? 0) : Number(raw);
    return { key: k, score };
  });
  scores.sort((a, b) => b.score - a.score);
  const highest = scores[0];
  const lowest = scores[scores.length - 1];
  process.stderr.write(
    `[masonry-training-export] Pattern confidence: ${confKeys.length} patterns tracked` +
    ` (highest: ${highest.key}=${highest.score.toFixed(2)},` +
    ` lowest: ${lowest.key}=${lowest.score.toFixed(2)})\n`
  );
}

// ── Run export ───────────────────────────────────────────────────────────────

process.stderr.write("[masonry-training-export] exporting campaign traces...\n");
markRun();

const args = [
  EXPORT_SCRIPT,
  "--bl-root", BL_ROOT,
  "--db", TRAINING_DB,
];

// Attach confidence data if any patterns are tracked
if (confKeys.length > 0) {
  args.push("--pattern-confidence", JSON.stringify(patternConfidence));
}

const child = spawn(python, args, {
  cwd: BL_ROOT,
  encoding: "utf8",
  env: { ...process.env },
});

child.stdout.on("data", (data) => process.stderr.write(data));
child.stderr.on("data", (data) => process.stderr.write(data));

child.on("close", (code) => {
  if (code !== 0) {
    process.stderr.write(`[masonry-training-export] export failed: exit code ${code}\n`);
    // Non-fatal — don't block session stop on export failure
  } else {
    process.stderr.write("[masonry-training-export] done\n");
  }
  process.exit(0);
});

child.on("error", (err) => {
  process.stderr.write(`[masonry-training-export] export failed: ${err.message}\n`);
  process.exit(0);
});

#!/usr/bin/env node
/**
 * Stop hook (Masonry): Run EMA collector at session end.
 *
 * Spawns collector.py detached (fire-and-forget) to update ema_history.json
 * from masonry/telemetry.jsonl. Only runs if telemetry.jsonl exists and has
 * at least one entry. Debounced: skips if run in the last 5 minutes.
 *
 * Last-run timestamp is stored in ~/.mas/ema-last-run.json.
 */

'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { readStdin } = require('./session/stop-utils');

const DEBOUNCE_MS = 5 * 60 * 1000; // 5 minutes
const LAST_RUN_FILE = path.join(os.homedir(), '.mas', 'ema-last-run.json');

function normalizeCwd(p) {
  if (process.platform === 'win32' && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ':' + p.slice(2).replace(/\//g, '\\');
  }
  return p;
}

function isResearchProject(dir) {
  return (
    fs.existsSync(path.join(dir, 'program.md')) &&
    fs.existsSync(path.join(dir, 'questions.md'))
  );
}

/**
 * Read last-run timestamp from ~/.mas/ema-last-run.json.
 * Returns 0 if missing or malformed.
 */
function readLastRun() {
  try {
    const raw = fs.readFileSync(LAST_RUN_FILE, 'utf8');
    const parsed = JSON.parse(raw);
    return typeof parsed.ts === 'number' ? parsed.ts : 0;
  } catch {
    return 0;
  }
}

/**
 * Write current timestamp to ~/.mas/ema-last-run.json.
 */
function writeLastRun() {
  try {
    const masDir = path.dirname(LAST_RUN_FILE);
    fs.mkdirSync(masDir, { recursive: true });
    fs.writeFileSync(
      LAST_RUN_FILE,
      JSON.stringify({ ts: Date.now() }, null, 2),
      'utf8'
    );
  } catch (err) {
    process.stderr.write(`[Masonry/EMA] Could not write last-run: ${err.message}\n`);
  }
}

/**
 * Check whether telemetry.jsonl exists and has at least one non-empty line.
 */
function telemetryHasEntries(telemetryPath) {
  try {
    const content = fs.readFileSync(telemetryPath, 'utf8');
    return content.split('\n').some((l) => l.trim().length > 0);
  } catch {
    return false;
  }
}

async function main() {
  // Skip inside BL research subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  // Don't re-trigger on second stop attempt
  if (parsed.stop_hook_active) process.exit(0);

  const cwd = normalizeCwd(parsed.cwd || process.cwd());

  // Only run in the BL repo root (where masonry/ exists)
  const masonryDir = path.join(cwd, 'masonry');
  if (!fs.existsSync(masonryDir)) process.exit(0);

  // Check telemetry.jsonl exists and has entries
  const telemetryPath = path.join(cwd, 'masonry', 'telemetry.jsonl');
  if (!telemetryHasEntries(telemetryPath)) process.exit(0);

  // Debounce: skip if run within the last 5 minutes
  const lastRun = readLastRun();
  if (Date.now() - lastRun < DEBOUNCE_MS) {
    process.stderr.write('[Masonry/EMA] Skipped — ran within last 5 minutes.\n');
    process.exit(0);
  }

  const collectorPath = path.join(
    cwd,
    'masonry',
    'src',
    'training',
    'collector.py'
  );
  if (!fs.existsSync(collectorPath)) {
    process.stderr.write('[Masonry/EMA] collector.py not found — skipping.\n');
    process.exit(0);
  }

  // Record the run before spawning (prevents parallel duplicate runs)
  writeLastRun();

  // Fire-and-forget: spawn detached
  const child = spawn('python', [collectorPath], {
    detached: true, windowsHide: true,
    stdio: 'ignore',
    cwd,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.stderr.write('[Masonry/EMA] EMA collector started in background.\n');
  process.exit(0);
}

main().catch(() => process.exit(0));

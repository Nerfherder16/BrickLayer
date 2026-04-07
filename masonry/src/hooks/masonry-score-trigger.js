#!/usr/bin/env node
/**
 * Stop hook (Masonry): Auto-trigger score_all_agents.py when scores are stale.
 * Also auto-triggers run_optimization.py every 50 new scored examples (fire-and-forget).
 *
 * Runs async (detached) so it never blocks the Stop event.
 * Rate-limited: only re-scores if scored_all.jsonl is older than 24 hours.
 * Skips silently inside BrickLayer research project subprocesses.
 */

'use strict';

const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { readStdin } = require('./session/stop-utils');

// ── DSPy optimization trigger constants ───────────────────────────────────────
const DSPY_THRESHOLD = 50;
const DSPY_TRIGGER_FILE = '.mas/dspy-trigger-count.json';
const DSPY_FLAG_FILE = path.join('.autopilot', 'TRIGGER_DSPY');
const DSPY_DEFAULT_AGENT = 'research-analyst';

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

function normalizeCwd(p) {
  if (process.platform === 'win32' && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ':' + p.slice(2).replace(/\//g, '\\');
  }
  return p;
}

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, 'program.md')) &&
         fs.existsSync(path.join(dir, 'questions.md'));
}

function scoresAreStale(repoRoot) {
  const scoredPath = path.join(repoRoot, 'masonry', 'training_data', 'scored_all.jsonl');
  try {
    const stat = fs.statSync(scoredPath);
    return (Date.now() - stat.mtimeMs) > TWENTY_FOUR_HOURS_MS;
  } catch {
    // File doesn't exist — treat as stale so we try to generate it
    return true;
  }
}

/**
 * Count lines in scored_all.jsonl (each line is one scored example).
 * Returns 0 if the file doesn't exist or can't be read.
 */
function countScoredExamples(repoRoot) {
  try {
    const scoredPath = path.join(repoRoot, 'masonry', 'training_data', 'scored_all.jsonl');
    const content = fs.readFileSync(scoredPath, 'utf8');
    return content.split('\n').filter((l) => l.trim().length > 0).length;
  } catch {
    return 0;
  }
}

/**
 * Read the DSPy trigger state from .mas/dspy-trigger-count.json.
 * Returns { lastCount: number, lastRun: string|null }.
 */
function readDspyTriggerState(repoRoot) {
  try {
    const raw = fs.readFileSync(path.join(repoRoot, DSPY_TRIGGER_FILE), 'utf8');
    const parsed = JSON.parse(raw);
    return {
      lastCount: typeof parsed.lastCount === 'number' ? parsed.lastCount : 0,
      lastRun: parsed.lastRun || null,
    };
  } catch {
    return { lastCount: 0, lastRun: null };
  }
}

/**
 * Persist the DSPy trigger state, creating .mas/ if needed.
 */
function writeDspyTriggerState(repoRoot, state) {
  const masDir = path.join(repoRoot, '.mas');
  fs.mkdirSync(masDir, { recursive: true });
  fs.writeFileSync(
    path.join(repoRoot, DSPY_TRIGGER_FILE),
    JSON.stringify({ ...state, updatedAt: new Date().toISOString() }, null, 2),
    'utf8'
  );
}

/**
 * Fire-and-forget: spawn run_optimization.py detached.
 * Never throws — all errors are caught and written to stderr.
 */
function spawnDspyOptimization(repoRoot) {
  try {
    const scriptPath = path.join(repoRoot, 'masonry', 'scripts', 'run_optimization.py');
    if (!fs.existsSync(scriptPath)) {
      process.stderr.write('[Masonry] run_optimization.py not found — skipping DSPy trigger.\n');
      return;
    }
    const child = spawn(
      'python',
      [scriptPath, DSPY_DEFAULT_AGENT, '--base-dir', repoRoot],
      {
        detached: true, windowsHide: true,
        stdio: 'ignore',
        cwd: repoRoot,
        windowsHide: true,
        env: { ...process.env, PYTHONPATH: repoRoot },
      }
    );
    child.unref();
    process.stderr.write(
      `[Masonry] DSPy optimization triggered for agent "${DSPY_DEFAULT_AGENT}" (fire-and-forget).\n`
    );
  } catch (err) {
    process.stderr.write(`[Masonry] DSPy trigger spawn error: ${err.message}\n`);
  }
}

/**
 * Check whether DSPy optimization should run based on scored-example count
 * or the presence of a TRIGGER_DSPY flag file. If triggered, resets the
 * counter and deletes the flag file.
 */
function maybeTriggerDspy(repoRoot) {
  try {
    const currentCount = countScoredExamples(repoRoot);
    if (currentCount === 0) return;

    const flagPath = path.join(repoRoot, DSPY_FLAG_FILE);
    const flagExists = fs.existsSync(flagPath);

    const state = readDspyTriggerState(repoRoot);
    const delta = currentCount - state.lastCount;
    const shouldTrigger = flagExists || delta >= DSPY_THRESHOLD;

    if (!shouldTrigger) return;

    // Trigger optimization
    spawnDspyOptimization(repoRoot);

    // Reset counter and delete flag
    writeDspyTriggerState(repoRoot, { lastCount: currentCount, lastRun: new Date().toISOString() });
    if (flagExists) {
      try { fs.unlinkSync(flagPath); } catch { /* best-effort */ }
    }
  } catch (err) {
    // Never throw — hook must not block Stop
    process.stderr.write(`[Masonry] DSPy trigger check error: ${err.message}\n`);
  }
}

async function main() {
  // Skip inside BL research subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  // Don't re-trigger on the second stop attempt
  if (parsed.stop_hook_active) process.exit(0);

  const cwd = normalizeCwd(parsed.cwd || process.cwd());

  // Only run checks if masonry/ exists here (this is the BL repo root, not a project subdir)
  const masonryDir = path.join(cwd, 'masonry');
  if (!fs.existsSync(masonryDir)) process.exit(0);

  // ── DSPy optimization trigger (always runs when masonry/ is present) ───────
  maybeTriggerDspy(cwd);

  // ── Score pipeline: rate-limited to once per 24h ──────────────────────────
  if (!scoresAreStale(cwd)) {
    process.exit(0);
  }

  const scriptPath = path.join(cwd, 'masonry', 'scripts', 'score_all_agents.py');
  if (!fs.existsSync(scriptPath)) process.exit(0);

  // Spawn detached — does not block Stop
  const child = spawn('python', [scriptPath, '--base-dir', cwd], {
    detached: true, windowsHide: true,
    stdio: 'ignore',
    cwd,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.stderr.write('[Masonry] Scoring pipeline started in background (scores >24h old).\n');

  // ── Training readiness check ──────────────────────────────────────────────
  const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB;
  const TRAINING_THRESHOLD = parseInt(process.env.TRAINING_THRESHOLD || '500', 10);
  const TRAINING_FLAG = path.join(cwd, '.mas', 'training_ready.flag');

  if (TRAINING_DB) {
    const check = spawnSync('python3', [
      '-c',
      [
        'import sqlite3',
        `db = sqlite3.connect('${TRAINING_DB.replace(/\\/g, '/')}')`,
        "n = db.execute('SELECT COUNT(*) FROM traces WHERE sft_eligible=1').fetchone()[0]",
        'print(n)',
      ].join(';'),
    ], { encoding: 'utf8', timeout: 1000 });

    if (check.status === 0) {
      const eligible = parseInt(check.stdout.trim(), 10);
      const masDir = path.join(cwd, '.mas');
      if (!fs.existsSync(masDir)) fs.mkdirSync(masDir, { recursive: true });
      if (eligible >= TRAINING_THRESHOLD) {
        fs.writeFileSync(TRAINING_FLAG, String(eligible), 'utf8');
        process.stderr.write(
          `[Masonry] Training ready: ${eligible} eligible traces (threshold: ${TRAINING_THRESHOLD})\n`
        );
      } else {
        if (fs.existsSync(TRAINING_FLAG)) fs.unlinkSync(TRAINING_FLAG);
        process.stderr.write(
          `[Masonry] Training progress: ${eligible}/${TRAINING_THRESHOLD} eligible traces\n`
        );
      }
    }
  }

  process.exit(0);
}

main().then(() => process.exit(0)).catch(() => process.exit(0));

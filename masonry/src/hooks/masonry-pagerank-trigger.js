#!/usr/bin/env node
/**
 * Stop hook (Masonry): trigger pagerank.py if >60 min since last run.
 *
 * Runs fire-and-forget (detached) so it never blocks the Stop event.
 * Rate-limited: only re-runs if ~/.mas/pagerank-last-run.json is older than 60 min.
 * Skips silently inside BrickLayer research project subprocesses.
 */

'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const SIXTY_MINUTES_MS = 60 * 60 * 1000;
const LAST_RUN_FILE = path.join(os.homedir(), '.mas', 'pagerank-last-run.json');

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

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

function isWithinCooldown() {
  try {
    const raw = fs.readFileSync(LAST_RUN_FILE, 'utf8');
    const data = JSON.parse(raw);
    if (!data.last_run) return false;
    const elapsed = Date.now() - new Date(data.last_run).getTime();
    return elapsed < SIXTY_MINUTES_MS;
  } catch {
    return false;
  }
}

function writeLastRun() {
  try {
    const masDir = path.join(os.homedir(), '.mas');
    fs.mkdirSync(masDir, { recursive: true });
    fs.writeFileSync(LAST_RUN_FILE, JSON.stringify({ last_run: new Date().toISOString() }, null, 2), 'utf8');
  } catch {
    // Non-fatal — skip silently
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

  // Only run if masonry/ exists here (this is the BL repo root, not a project subdir)
  const masonryDir = path.join(cwd, 'masonry');
  if (!fs.existsSync(masonryDir)) process.exit(0);

  const scriptPath = path.join(cwd, 'masonry', 'src', 'reasoning', 'pagerank.py');
  if (!fs.existsSync(scriptPath)) process.exit(0);

  // Rate limit: skip if run within last 60 minutes
  if (isWithinCooldown()) {
    process.exit(0);
  }

  // Update timestamp before spawning so concurrent stops don't double-fire
  writeLastRun();

  // Spawn detached — does not block Stop
  const project = path.basename(cwd);
  const confidenceJsonPath = path.join(cwd, '.autopilot', 'pattern-confidence.json');
  const child = spawn('python', [scriptPath, project, confidenceJsonPath], {
    detached: true,
    stdio: 'ignore',
    cwd,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.stderr.write('[Masonry] PageRank trigger started in background (last run >60 min ago).\n');

  process.exit(0);
}

main().catch(() => process.exit(0));

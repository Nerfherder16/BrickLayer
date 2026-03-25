#!/usr/bin/env node
/**
 * Stop hook (Masonry): Auto-trigger score_all_agents.py when scores are stale.
 *
 * Runs async (detached) so it never blocks the Stop event.
 * Rate-limited: only re-scores if scored_all.jsonl is older than 24 hours.
 * Skips silently inside BrickLayer research project subprocesses.
 */

'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

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

  // Only score if masonry/ exists here (this is the BL repo root, not a project subdir)
  const masonryDir = path.join(cwd, 'masonry');
  if (!fs.existsSync(masonryDir)) process.exit(0);

  // Rate limit: skip if scored within last 24h
  if (!scoresAreStale(cwd)) {
    process.exit(0);
  }

  const scriptPath = path.join(cwd, 'masonry', 'scripts', 'score_all_agents.py');
  if (!fs.existsSync(scriptPath)) process.exit(0);

  // Spawn detached — does not block Stop
  const child = spawn('python', [scriptPath, '--base-dir', cwd], {
    detached: true,
    stdio: 'ignore',
    cwd,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: cwd },
  });
  child.unref();

  process.stderr.write('[Masonry] Scoring pipeline started in background (scores >24h old).\n');
  process.exit(0);
}

main().catch(() => process.exit(0));

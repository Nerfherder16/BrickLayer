#!/usr/bin/env node
/**
 * masonry-pre-protect.js
 * PreToolUse hook — combined Write/Edit protection (replaces masonry-session-lock.js
 * and masonry-pre-edit.js, archived 2026-03-28).
 *
 * Phase 1 — Session lock check: blocks writes to protected campaign files if a
 *   different session holds a fresh lock. May output { decision: "block", reason }.
 * Phase 2 — File backup: copies the target file to .autopilot/backups/ during
 *   build/fix mode. Never blocks — always exits 0 after backup attempt.
 *
 * Protected files (session lock):
 *   masonry-state.json, .autopilot/progress.json, .autopilot/mode,
 *   .autopilot/compact-state.json, questions.md, findings/*.md
 *
 * Backup path: .autopilot/backups/{relative_dir}/{filename}/{filename}.{ISO-timestamp}
 * Stale lock threshold: 4 hours.
 */

'use strict';
const fs = require('fs');
const { existsSync, readFileSync } = fs;
const path = require('path');
const { readStdin } = require('./session/stop-utils');

const LOCK_STALE_MS = 4 * 60 * 60 * 1000;

const SESSION_LOCK_PROTECTED = [
  /^masonry-state\.json$/,
  /^\.autopilot[\\/](progress\.json|mode|compact-state\.json)$/,
  /^questions\.md$/,
  /^findings[\\/].+\.md$/,
];


function isResearchProject(dir) {
  return existsSync(path.join(dir, 'program.md')) && existsSync(path.join(dir, 'questions.md'));
}

function isProtectedPath(cwd, filePath) {
  if (!filePath) return false;
  let rel;
  try { rel = path.relative(cwd, path.resolve(cwd, filePath)); } catch { return false; }
  if (rel.startsWith('..')) return false;
  const normalized = rel.replace(/\\/g, '/');
  return SESSION_LOCK_PROTECTED.some(re => re.test(normalized));
}

function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const ap = path.join(dir, '.autopilot');
    if (existsSync(ap)) return { autopilotDir: ap, projectRoot: dir };
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function safeTimestamp() {
  return new Date().toISOString().replace(/:/g, '-').replace(/\.\d{3}Z$/, '');
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();

  // Silent inside BL research subprocesses
  if (isResearchProject(cwd)) process.exit(0);

  const toolName = input.tool_name || '';
  if (!['Write', 'Edit'].includes(toolName)) process.exit(0);

  const toolInput = input.tool_input || {};
  const targetFile = toolInput.file_path || null;

  // ── Phase 1: Session lock check ──────────────────────────────────────────
  if (targetFile && isProtectedPath(cwd, targetFile)) {
    const currentSessionId = require('./session/stop-utils').getSessionId(input);
    if (currentSessionId) {
      const lockPath = path.join(cwd, '.mas', 'session.lock');
      let lock = null;
      try {
        if (existsSync(lockPath)) lock = JSON.parse(readFileSync(lockPath, 'utf8'));
      } catch {}

      if (lock) {
        const lockAge = Date.now() - new Date(lock.started_at || 0).getTime();
        if (lockAge >= LOCK_STALE_MS) {
          try { fs.unlinkSync(lockPath); } catch {}
        } else if (lock.session_id !== currentSessionId) {
          const relFile = path.relative(cwd, path.resolve(cwd, targetFile)).replace(/\\/g, '/');
          process.stdout.write(JSON.stringify({
            decision: 'block',
            reason: `[Masonry Session Lock] "${relFile}" is owned by session ${lock.session_id} ` +
              `(started ${lock.started_at}, branch: ${lock.branch || 'unknown'}). ` +
              `Parallel session conflict detected. ` +
              `Delete .mas/session.lock if that session has ended, then retry.`,
          }));
          process.exit(0);
        }
      }
    }
  }

  // ── Phase 1.5: Mortar routing soft gate ─────────────────────────────────
  // Warn (not block) when Write/Edit fires without Mortar being consulted.
  // The prompt-router writes mortar_consulted=false at turn start;
  // subagent-tracker sets it to true when Mortar is spawned.
  // Skip: state files, config files, build/fix mode (already orchestrated).
  try {
    const os = require('os');
    const gateFile = path.join(os.tmpdir(), 'masonry-mortar-gate.json');
    if (existsSync(gateFile)) {
      const gate = JSON.parse(readFileSync(gateFile, 'utf8'));
      const gateAge = Date.now() - new Date(gate.timestamp || 0).getTime();
      if (!gate.mortar_consulted && gateAge < 300_000) { // 5 min freshness
        // Don't warn for state/config files or build-mode work
        const skipPatterns = [
          /\.(autopilot|mas|ui)[/\\]/,
          /masonry-state\.json$/,
          /\.claude[/\\]/,
          /node_modules[/\\]/,
          /package-lock\.json$/,
        ];
        const filePath = targetFile || '';
        const isStateFile = skipPatterns.some(p => p.test(filePath));

        // Don't warn during active build/fix mode
        const buildMode = (() => {
          try {
            const ap = findAutopilotDir(cwd);
            if (!ap) return false;
            const m = readFileSync(path.join(ap.autopilotDir, 'mode'), 'utf8').trim();
            return m === 'build' || m === 'fix';
          } catch { return false; }
        })();

        if (!isStateFile && !buildMode) {
          process.stderr.write(
            `[Masonry] ⚠ Write/Edit without Mortar routing. ` +
            `Route through Mortar first for code review and TDD.\n`
          );
        }
      }
    }
  } catch {}

  // ── Phase 2: File backup (build/fix mode only) ────────────────────────────
  try {
    if (!targetFile) process.exit(0);

    const absPath = path.isAbsolute(targetFile) ? targetFile : path.resolve(cwd, targetFile);
    if (!existsSync(absPath)) process.exit(0);

    const fileDir = path.dirname(absPath);
    const found = findAutopilotDir(fileDir) || findAutopilotDir(cwd);
    if (!found) process.exit(0);

    const { autopilotDir, projectRoot } = found;
    const modeFile = path.join(autopilotDir, 'mode');
    if (!existsSync(modeFile)) process.exit(0);

    const mode = readFileSync(modeFile, 'utf8').trim();
    if (mode !== 'build' && mode !== 'fix') process.exit(0);

    const relPath = path.relative(projectRoot, absPath);
    const relDir = path.dirname(relPath);
    const filename = path.basename(absPath);
    const backupDir = path.join(autopilotDir, 'backups', relDir, filename);
    const backupFile = path.join(backupDir, `${filename}.${safeTimestamp()}`);

    fs.mkdirSync(backupDir, { recursive: true });
    fs.copyFileSync(absPath, backupFile);
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));

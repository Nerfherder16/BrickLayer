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

const LOCK_STALE_MS = 4 * 60 * 60 * 1000;

const SESSION_LOCK_PROTECTED = [
  /^masonry-state\.json$/,
  /^\.autopilot[\\/](progress\.json|mode|compact-state\.json)$/,
  /^questions\.md$/,
  /^findings[\\/].+\.md$/,
];

function readStdin() {
  return new Promise(resolve => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => (data += c));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

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
    const currentSessionId = input.session_id || input.sessionId || null;
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

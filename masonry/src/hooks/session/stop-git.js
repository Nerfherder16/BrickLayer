'use strict';
/**
 * stop-git.js — git helpers for masonry-stop-guard.js
 * generateAutoCommitMessage, loadSessionWrites
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const { normalizeCwd } = require('./stop-utils');

function generateAutoCommitMessage(files, cwd) {
  try {
    const lastCommitFiles = new Set(
      execSync('git show --name-only --pretty=format: HEAD', {
        encoding: 'utf8', timeout: 5000, cwd,
      }).trim().split('\n').filter(Boolean)
    );
    if (files.length > 0 && files.every(f => lastCommitFiles.has(f))) {
      const hash = execSync('git rev-parse --short HEAD', {
        encoding: 'utf8', timeout: 3000, cwd,
      }).trim();
      return `style: lint cleanup after ${hash} (${files.length} file${files.length !== 1 ? 's' : ''})`;
    }
  } catch { /* fall through */ }

  const dirs = new Set(files.map(f => f.split('/')[0]).filter(Boolean));
  const dirList = [...dirs].slice(0, 3).join(', ');
  if (dirs.size <= 3 && dirList) {
    return `chore: update ${dirList} (${files.length} file${files.length !== 1 ? 's' : ''})`;
  }
  return `chore: auto-commit ${files.length} session file${files.length !== 1 ? 's' : ''} on stop`;
}

function loadSessionWrites(sessionId, cwd) {
  if (!sessionId) return null;
  try {
    const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
    if (!fs.existsSync(activityFile)) return null;
    const lines = fs.readFileSync(activityFile, 'utf8').trim().split('\n').filter(Boolean);
    const writes = new Set();
    const normalCwd = normalizeCwd(cwd).replace(/\\/g, '/');
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (!entry.file) continue;
        let f = entry.file.replace(/\\/g, '/');
        if (f.startsWith(normalCwd + '/')) f = f.slice(normalCwd.length + 1);
        writes.add(f);
      } catch { /* skip malformed */ }
    }
    return writes;
  } catch {
    return null;
  }
}

module.exports = { generateAutoCommitMessage, loadSessionWrites };

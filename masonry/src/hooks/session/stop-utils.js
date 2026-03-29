'use strict';
/**
 * stop-utils.js — shared utilities for masonry-stop-guard.js
 */

const fs = require('fs');
const path = require('path');
const { readJson, writeJson, appendJsonl } = require('../../core/mas');

function readStdin(timeoutMs = 2000) {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), timeoutMs);
  });
}

function normalizeCwd(p) {
  if (process.platform === 'win32' && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ':' + p.slice(2).replace(/\//g, '\\');
  }
  return p;
}

function fileAgeDays(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return Math.floor((Date.now() - stat.mtimeMs) / (1000 * 60 * 60 * 24));
  } catch {
    return null;
  }
}

function ageLabel(days) {
  if (days === null || days === 0) return '';
  if (days === 1) return ' (yesterday)';
  return ` (${days}d old)`;
}

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, 'program.md')) &&
         fs.existsSync(path.join(dir, 'questions.md'));
}

function closeSession(projectDir) {
  try {
    const session = readJson(projectDir, 'session.json');
    if (!session || !session.started_at) return;
    const now = new Date();
    session.ended_at = now.toISOString();
    session.duration_ms = now.getTime() - new Date(session.started_at).getTime();
    writeJson(projectDir, 'session.json', session);
    appendJsonl(projectDir, 'history.jsonl', session);
  } catch (_) {}
}

function tryRead(p) {
  try { return fs.readFileSync(p, 'utf8').trim(); } catch { return null; }
}

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; }
}

module.exports = { readStdin, normalizeCwd, fileAgeDays, ageLabel, isResearchProject, closeSession, tryRead, tryJSON };

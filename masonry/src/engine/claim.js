'use strict';
// engine/claim.js — Atomic question claim manager for parallel campaigns.
//
// Port of bl/claim.py to Node.js.

const fs = require('fs');
const path = require('path');

function _claimsPath(projectPath) {
  return path.join(String(projectPath), 'claims.json');
}

function _lockPath(projectPath) {
  return path.join(String(projectPath), 'claims.lock');
}

function _acquireLock(projectPath, retries = 30) {
  const lock = _lockPath(projectPath);
  for (let i = 0; i < retries; i++) {
    try {
      const fd = fs.openSync(lock, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY);
      fs.closeSync(fd);
      return true;
    } catch (err) {
      if (err.code === 'EEXIST') {
        // Busy wait — 100ms
        const end = Date.now() + 100;
        while (Date.now() < end) { /* spin */ }
        continue;
      }
      throw err;
    }
  }
  return false;
}

function _releaseLock(projectPath) {
  try {
    fs.unlinkSync(_lockPath(projectPath));
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
}

function _load(projectPath) {
  const p = _claimsPath(projectPath);
  if (!fs.existsSync(p)) return {};
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return {};
  }
}

function _save(projectPath, claims) {
  const p = _claimsPath(projectPath);
  const tmp = p + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(claims, null, 2), 'utf8');
  fs.renameSync(tmp, p);
}

function cmdClaim(projectPath, questionId, workerId) {
  if (!_acquireLock(projectPath)) return 'LOCK_FAILED';
  try {
    const claims = _load(projectPath);
    if (questionId in claims && (claims[questionId].status === 'IN_PROGRESS' || claims[questionId].status === 'DONE')) {
      return 'TAKEN';
    }
    claims[questionId] = {
      worker: workerId,
      claimed_at: new Date().toISOString(),
      status: 'IN_PROGRESS',
    };
    _save(projectPath, claims);
    return 'CLAIMED';
  } finally {
    _releaseLock(projectPath);
  }
}

function cmdRelease(projectPath, questionId) {
  if (!_acquireLock(projectPath)) return 'LOCK_FAILED';
  try {
    const claims = _load(projectPath);
    if (questionId in claims) {
      delete claims[questionId];
      _save(projectPath, claims);
    }
    return 'OK';
  } finally {
    _releaseLock(projectPath);
  }
}

function cmdComplete(projectPath, questionId, verdict) {
  if (!_acquireLock(projectPath)) return 'LOCK_FAILED';
  try {
    const claims = _load(projectPath);
    if (!(questionId in claims)) {
      claims[questionId] = { worker: 'unknown' };
    }
    claims[questionId].status = 'DONE';
    claims[questionId].verdict = verdict;
    claims[questionId].completed_at = new Date().toISOString();
    _save(projectPath, claims);
    return 'OK';
  } finally {
    _releaseLock(projectPath);
  }
}

module.exports = { cmdClaim, cmdRelease, cmdComplete };

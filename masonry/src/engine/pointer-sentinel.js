'use strict';
// engine/pointer-sentinel.js — Sentinel helpers for pointer agent firing intervals.
//
// Port of bl/pointer_sentinel.py to Node.js.

const fs = require('fs');
const path = require('path');

function shouldFirePointer(globalCount, interval = 8) {
  if (globalCount === 0) return false;
  return globalCount % interval === 0;
}

function _checkpointSortKey(filename) {
  const match = filename.match(/wave(\d+)-q(\d+)/);
  if (match) return [parseInt(match[1], 10), parseInt(match[2], 10)];
  return [0, 0];
}

function getLatestCheckpoint(checkpointDir) {
  if (!fs.existsSync(checkpointDir)) return null;

  let files;
  try {
    files = fs.readdirSync(checkpointDir);
  } catch {
    return null;
  }

  if (files.length === 0) return null;

  files.sort((a, b) => {
    const [aw, aq] = _checkpointSortKey(a);
    const [bw, bq] = _checkpointSortKey(b);
    if (aw !== bw) return aw - bw;
    return aq - bq;
  });

  return path.join(checkpointDir, files[files.length - 1]);
}

module.exports = { shouldFirePointer, getLatestCheckpoint };

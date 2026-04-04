'use strict';
// engine/scratch.js — Typed signal board management for BL 2.0 campaigns.
//
// Port of bl/scratch.py to Node.js.

const fs = require('fs');

const _VALID_TYPES = new Set(['WATCH', 'BLOCK', 'DATA', 'RESOLVED']);
const _SIGNAL_RE = /\[SIGNAL:\s*([A-Z]+)\s*--\s*(.*?)\]/gs;

const _TABLE_HEADER = '| # | Signal | Type | Source | Date |';
const _TABLE_SEP = '|---|--------|------|--------|------|';

function parseSignals(findingText) {
  const results = [];
  let match;
  // Reset regex state
  _SIGNAL_RE.lastIndex = 0;
  while ((match = _SIGNAL_RE.exec(findingText)) !== null) {
    const sigType = match[1];
    const message = match[2].trim();
    if (!_VALID_TYPES.has(sigType)) continue;
    results.push({ signal: message, type: sigType, source: '', date: '' });
  }
  return results;
}

function renderScratch(rows) {
  const lines = [_TABLE_HEADER, _TABLE_SEP];
  rows.forEach((row, i) => {
    lines.push(`| ${i + 1} | ${row.signal} | ${row.type} | ${row.source} | ${row.date} |`);
  });
  return lines.join('\n');
}

function saveScratch(filePath, rows) {
  const table = renderScratch(rows);
  const content = `# Campaign Scratch Pad\n\n${table}\n`;
  fs.writeFileSync(filePath, content, 'utf8');
}

function loadScratch(filePath) {
  if (!fs.existsSync(filePath)) return [];

  const content = fs.readFileSync(filePath, 'utf8');
  const rows = [];
  let inTable = false;
  let pastSeparator = false;

  for (const line of content.split('\n')) {
    const stripped = line.trim();
    if (stripped.startsWith('| # |')) {
      inTable = true;
      pastSeparator = false;
      continue;
    }
    if (inTable && !pastSeparator && stripped.startsWith('|---')) {
      pastSeparator = true;
      continue;
    }
    if (inTable && pastSeparator && stripped.startsWith('|')) {
      // rsplit equivalent: split from right with max 4 splits
      const rightParts = _rsplit(stripped, '|', 4).map(p => p.trim());
      if (rightParts.length >= 4) {
        const leftParts = rightParts[0].split('|', 3).map(p => p.trim());
        if (leftParts.length >= 3) {
          rows.push({
            signal: leftParts[2],
            type: rightParts[1],
            source: rightParts[2],
            date: rightParts[3],
          });
        }
      }
    }
  }

  return rows;
}

function _rsplit(str, sep, maxSplits) {
  const parts = [];
  let remaining = str;
  for (let i = 0; i < maxSplits; i++) {
    const idx = remaining.lastIndexOf(sep);
    if (idx === -1) break;
    parts.unshift(remaining.slice(idx + 1));
    remaining = remaining.slice(0, idx);
  }
  parts.unshift(remaining);
  return parts;
}

function trimScratch(rows, maxEntries = 15) {
  const result = [...rows];
  while (result.length > maxEntries) {
    // Remove first RESOLVED
    let removed = false;
    for (let i = 0; i < result.length; i++) {
      if (result[i].type === 'RESOLVED') {
        result.splice(i, 1);
        removed = true;
        break;
      }
    }
    if (removed) continue;

    // Remove first DATA
    for (let i = 0; i < result.length; i++) {
      if (result[i].type === 'DATA') {
        result.splice(i, 1);
        removed = true;
        break;
      }
    }
    if (removed) continue;

    // Nothing removable
    break;
  }
  return result;
}

module.exports = { parseSignals, renderScratch, saveScratch, loadScratch, trimScratch };

'use strict';
// engine/followup.js — Adaptive follow-up question generator.
//
// Port of bl/followup.py to Node.js.
// Pure parsing functions are exported; Ollama-dependent functions are runtime only.

const fs = require('fs');
const path = require('path');

function _isLeafId(qid) {
  let stripped = qid;
  if (stripped.startsWith('QG')) {
    stripped = stripped.slice(2);
  } else if (stripped.startsWith('Q')) {
    stripped = stripped.slice(1);
  } else {
    // BL 2.0 IDs (D1, D5.1, F4.3) — use dot count
    return qid.split('.').length >= 3;
  }
  return stripped.split('.').length >= 3;
}

function _getExistingSubIds(questionsMdPath, parentId) {
  if (!fs.existsSync(questionsMdPath)) return [];

  const text = fs.readFileSync(questionsMdPath, 'utf8');
  const escaped = parentId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`^##\\s+${escaped}\\.\\d+`, 'gm');
  const matches = text.match(pattern) || [];

  const ids = [];
  for (const m of matches) {
    const parts = m.split(/\s+/);
    if (parts.length >= 2) ids.push(parts[1]);
  }
  return ids;
}

function _nextSubIndex(questionsMdPath, parentId) {
  const existing = _getExistingSubIds(questionsMdPath, parentId);
  if (existing.length === 0) return 1;

  const indices = [];
  for (const sid of existing) {
    const lastPart = sid.split('.').pop();
    const idx = parseInt(lastPart, 10);
    if (!isNaN(idx)) indices.push(idx);
  }
  return indices.length > 0 ? Math.max(...indices) + 1 : 1;
}

function _parseFollowupBlocks(raw, parentId, startIndex) {
  const segments = raw.split(/\n---\n|^---\n|\n---$|^---$/m);
  const valid = [];
  let currentIndex = startIndex;

  for (let seg of segments) {
    seg = seg.trim();
    if (!seg) continue;
    if (!seg.includes('**Status**: PENDING')) continue;
    if (!seg.includes('**Derived from**:')) continue;
    if (!seg.startsWith('##')) continue;

    // Renumber the header ID
    const correctId = `${parentId}.${currentIndex}`;
    seg = seg.replace(/^##\s+\S+/, `## ${correctId}`);

    // Ensure mode tag in header if missing
    const headerMatch = seg.match(/^## \S+(.*)$/m);
    if (headerMatch && !headerMatch[1].includes('[')) {
      const _OP_MODE_TO_TAG = {
        diagnose: 'DIAGNOSE', fix: 'FIX', audit: 'AUDIT',
        validate: 'VALIDATE', monitor: 'MONITOR', frontier: 'FRONTIER',
        predict: 'PREDICT', research: 'RESEARCH', evolve: 'EVOLVE',
        code_audit: 'AUDIT', agent: 'DIAGNOSE',
      };

      let modeTag = null;
      const opModeMatch = seg.match(/\*\*Operational Mode\*\*:\s*(\w+)/i);
      if (opModeMatch) {
        const rawOp = opModeMatch[1].toLowerCase();
        modeTag = `[${_OP_MODE_TO_TAG[rawOp] || 'DIAGNOSE'}]`;
      } else {
        const modeMatch = seg.match(/\*\*Mode\*\*:\s*(\w+)/);
        if (modeMatch) {
          const rawMode = modeMatch[1].toLowerCase();
          modeTag = `[${_OP_MODE_TO_TAG[rawMode] || 'DIAGNOSE'}]`;
        }
      }
      if (modeTag) {
        seg = seg.replace(/^(## \S+) /, `$1 ${modeTag} `);
      }
    }

    valid.push(seg);
    currentIndex++;
  }

  return valid;
}

module.exports = {
  _isLeafId,
  _getExistingSubIds,
  _nextSubIndex,
  _parseFollowupBlocks,
};

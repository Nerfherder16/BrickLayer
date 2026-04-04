'use strict';
// engine/hypothesis.js — Hypothesis generator: reads campaign findings
// and generates the next wave of PENDING questions.
//
// Port of bl/hypothesis.py to Node.js.
// Pure parsing functions are exported; Ollama-dependent functions are runtime only.

const fs = require('fs');
const path = require('path');

const _QUESTION_BLOCK_HEADER = /^## ([\w][\w.-]*)\s+\[(\w+)\]\s+(.+)$/gm;

function _getWaveNumber(questionsText) {
  const re = new RegExp(_QUESTION_BLOCK_HEADER.source, _QUESTION_BLOCK_HEADER.flags);
  const matches = [];
  let m;
  while ((m = re.exec(questionsText)) !== null) {
    matches.push(m[1]);
  }
  if (matches.length === 0) return 1;

  const waves = [];
  for (const qid of matches) {
    try {
      const firstPart = qid.split('.')[0];
      const num = parseInt(firstPart.slice(1), 10);
      if (!isNaN(num)) waves.push(num);
    } catch (_) { /* skip */ }
  }
  return waves.length > 0 ? Math.max(...waves) : 1;
}

function _getExistingIds(questionsText) {
  const re = new RegExp(_QUESTION_BLOCK_HEADER.source, _QUESTION_BLOCK_HEADER.flags);
  const ids = new Set();
  let m;
  while ((m = re.exec(questionsText)) !== null) {
    ids.add(m[1]);
  }
  return ids;
}

function _buildFindingsSummary(resultsTsvPath) {
  if (!fs.existsSync(resultsTsvPath)) return 'No results available.';

  const text = fs.readFileSync(resultsTsvPath, 'utf8');
  const lines = text.split('\n').filter(Boolean);
  if (lines.length <= 1) return 'No results yet.';

  const summaryLines = [];
  const warnings = [];
  const failures = [];
  const inconclusives = [];

  for (const line of lines.slice(1)) {
    const parts = line.split('\t');
    if (parts.length < 3) continue;
    const qid = parts[0].trim();
    const verdict = parts[1].trim();
    const summary = parts.length >= 4
      ? parts[parts.length - 2].trim()
      : parts[2].trim();

    const entry = `  ${qid}: ${verdict} — ${summary.slice(0, 120)}`;
    summaryLines.push(entry);
    if (verdict === 'WARNING') warnings.push(entry);
    else if (verdict === 'FAILURE') failures.push(entry);
    else if (verdict === 'INCONCLUSIVE') inconclusives.push(entry);
  }

  const out = ['=== All findings ===', ...summaryLines];

  if (failures.length) {
    out.push('\n=== FAILURES (highest priority) ===', ...failures);
  }
  if (warnings.length) {
    out.push('\n=== WARNINGS (investigate further) ===', ...warnings);
  }
  if (inconclusives.length) {
    out.push('\n=== INCONCLUSIVE (may need re-run or agent analysis) ===', ...inconclusives);
  }

  return out.join('\n');
}

function _parseQuestionBlocks(raw, nextWave) {
  const blocks = raw.split(/\n---\n|\n---$|^---\n/m);
  const valid = [];

  for (let block of blocks) {
    block = block.trim();
    if (!block) continue;

    // Must contain a question header for our wave
    const waveRe = new RegExp(`## \\w+${nextWave}\\.\\d+`);
    if (!waveRe.test(block)) continue;

    // Must have Status: PENDING
    if (!block.includes('**Status**: PENDING')) {
      block = block.replace('**Mode**:', '**Status**: PENDING\n**Mode**:', 1);
      if (!block.includes('**Status**: PENDING')) continue;
    }
    valid.push(block);
  }

  return valid;
}

module.exports = {
  _getWaveNumber,
  _getExistingIds,
  _buildFindingsSummary,
  _parseQuestionBlocks,
};

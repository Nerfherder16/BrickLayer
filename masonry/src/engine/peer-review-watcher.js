'use strict';
// engine/peer-review-watcher.js — Process peer-reviewer results and requeue
// low-quality INCONCLUSIVEs.
//
// Port of bl/peer_review_watcher.py to Node.js.

const fs = require('fs');
const path = require('path');
const { recordResult } = require('./question-weights');

const REQUEUE_THRESHOLD = 0.4;

const _PRIMARY_VERDICT_RE = /^\*\*Verdict\*\*:\s*(\w+)/m;
const _PEER_SECTION_RE = /## Peer Review/m;
const _PEER_VERDICT_RE = /## Peer Review[\s\S]*?\*\*Verdict\*\*:\s*(\w+)/;
const _PEER_QUALITY_RE = /## Peer Review[\s\S]*?\*\*Quality Score\*\*:\s*([0-9.]+)/;

function parseFinding(filePath) {
  if (!fs.existsSync(filePath)) return null;

  let text;
  try {
    text = fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }

  if (!_PEER_SECTION_RE.test(text)) return null;

  const primaryM = text.match(_PRIMARY_VERDICT_RE);
  const peerVerdictM = text.match(_PEER_VERDICT_RE);
  const qualityM = text.match(_PEER_QUALITY_RE);

  return {
    qid: path.basename(filePath, '.md'),
    primary_verdict: primaryM ? primaryM[1].toUpperCase() : 'UNKNOWN',
    peer_verdict: peerVerdictM ? peerVerdictM[1].toUpperCase() : null,
    quality_score: qualityM ? parseFloat(qualityM[1]) : null,
  };
}

function _alreadyRequeued(questionsText, rqId) {
  return questionsText.includes(`## ${rqId}`) || questionsText.includes(`## ${rqId} [`);
}

function _originalQuestionText(questionsText, qid) {
  let blockStart = questionsText.indexOf(`## ${qid} [`);
  if (blockStart === -1) blockStart = questionsText.indexOf(`## ${qid}\n`);
  if (blockStart === -1) return `Original question ${qid} (text not found)`;

  const nextBlock = questionsText.indexOf('\n## ', blockStart + 1);
  const block = questionsText.slice(blockStart, nextBlock !== -1 ? nextBlock : undefined);

  const hypM = block.match(/\*\*Hypothesis\*\*:\s*(.+)/);
  const qM = block.match(/\*\*Question\*\*:\s*(.+)/);
  if (hypM) return hypM[1].trim();
  if (qM) return qM[1].trim();
  return `Original question ${qid}`;
}

function _appendRequeue(questionsPath, qid, rqId, qualityScore) {
  let text = fs.readFileSync(questionsPath, 'utf8');
  const origHypothesis = _originalQuestionText(text, qid).slice(0, 200);
  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  // Infer mode from original block
  let mode = 'research';
  const blockStart = text.indexOf(`## ${qid}`);
  if (blockStart !== -1) {
    const nextBlock = text.indexOf('\n## ', blockStart + 1);
    const block = text.slice(blockStart, nextBlock !== -1 ? nextBlock : undefined);
    const modeM = block.match(/\*\*Mode\*\*:\s*(\w+)/);
    if (modeM) mode = modeM[1];
  }

  const requeueBlock = `\n## ${rqId} [PENDING]\n\n**Question**: ${origHypothesis} — REQUEUE: prior finding INCONCLUSIVE with low quality score (${qualityScore.toFixed(2)} < ${REQUEUE_THRESHOLD}). Narrow scope and focus on the most specific claim.\n**Hypothesis**: ${origHypothesis}\n**Mode**: ${mode}\n**Status**: PENDING\n**Priority**: high\n**Added**: ${timestamp}\n**Source**: peer_review_watcher (requeue of ${qid})\n\n`;

  const newText = text.trimEnd() + '\n' + requeueBlock;

  const tmpPath = questionsPath + `.${process.pid}.tmp`;
  try {
    fs.writeFileSync(tmpPath, newText, 'utf8');
    fs.renameSync(tmpPath, questionsPath);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* ignore */ }
    throw err;
  }
}

function process(projectRoot) {
  const findingsDir = path.join(projectRoot, 'findings');
  const questionsPath = path.join(projectRoot, 'questions.md');

  if (!fs.existsSync(findingsDir)) return [];

  const requeued = [];

  const files = fs.readdirSync(findingsDir)
    .filter(f => f.endsWith('.md') && f !== 'synthesis.md')
    .sort();

  for (const fname of files) {
    const info = parseFinding(path.join(findingsDir, fname));
    if (!info) continue;

    if (info.primary_verdict !== 'INCONCLUSIVE') continue;
    if (info.quality_score === null || info.quality_score >= REQUEUE_THRESHOLD) continue;

    const qid = info.qid;
    const qualityScore = info.quality_score;

    // Update weights
    recordResult(projectRoot, qid, 'INCONCLUSIVE', qualityScore);

    // Requeue in questions.md if it exists
    if (fs.existsSync(questionsPath)) {
      const questionsText = fs.readFileSync(questionsPath, 'utf8');
      const rqId = `${qid}-RQ1`;
      if (!_alreadyRequeued(questionsText, rqId)) {
        _appendRequeue(questionsPath, qid, rqId, qualityScore);
        requeued.push(qid);
      }
    } else {
      requeued.push(qid);
    }
  }

  return requeued;
}

module.exports = {
  REQUEUE_THRESHOLD,
  parseFinding,
  process,
};

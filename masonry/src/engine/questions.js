'use strict';
// engine/questions.js — Question bank I/O.
//
// Port of bl/questions.py to Node.js. Parses questions.md and
// reads/writes question status via results.tsv.

const fs = require('fs');
const path = require('path');
const { cfg } = require('./config');

// C-30: tags that require live evidence vs. static analysis only
const BEHAVIORAL_TAGS = new Set([
  'performance', 'correctness', 'agent', 'http', 'benchmark',
]);
const CODE_AUDIT_TAGS = new Set([
  'quality', 'static', 'code-audit',
]);

const BLOCK_PATTERN = /^## ([\w][\w.-]*) \[(\w+)\] (.+?)$/gm;
const FIELD_PATTERN = /^\*\*(Mode|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source|Operational Mode|Resume After)\*\*:\s*(.+?)(?=\n\*\*|$)/gms;

// Statuses that are parked / terminal — getNextPending skips these
const PARKED_STATUSES = new Set([
  'DIAGNOSIS_COMPLETE', 'PENDING_EXTERNAL', 'DEPLOYMENT_BLOCKED',
  'DONE', 'INCONCLUSIVE', 'FIXED', 'FIX_FAILED',
  'COMPLIANT', 'NON_COMPLIANT', 'CALIBRATED', 'BLOCKED', 'HEAL_EXHAUSTED',
]);

// Statuses that count as "resolved" for resume_after question-ID references
const RESOLVED_STATUSES = new Set([
  'DONE', 'HEALTHY', 'WARNING', 'FAILURE', 'INCONCLUSIVE',
  'FIXED', 'FIX_FAILED', 'COMPLIANT', 'NON_COMPLIANT',
  'CALIBRATED', 'HEAL_EXHAUSTED',
]);

// Terminal verdicts from results.tsv that trigger status sync
const TERMINAL_VERDICTS = new Set([
  'HEALTHY', 'WARNING', 'FAILURE', 'INCONCLUSIVE',
  'DIAGNOSIS_COMPLETE', 'PENDING_EXTERNAL', 'FIXED', 'FIX_FAILED',
  'PROMISING', 'WEAK', 'BLOCKED', 'CALIBRATED', 'UNCALIBRATED',
  'NOT_MEASURABLE', 'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL',
  'NOT_APPLICABLE', 'IMPROVEMENT', 'REGRESSION', 'IMMINENT',
  'PROBABLE', 'POSSIBLE', 'UNLIKELY', 'OK', 'DEGRADED', 'ALERT',
  'UNKNOWN', 'SUBJECTIVE', 'DEGRADED_TRENDING',
  'DEPLOYMENT_BLOCKED', 'HEAL_EXHAUSTED',
]);

// Verdicts preserved as-is in questions.md (not collapsed to DONE)
const PRESERVE_VERDICTS = new Set([
  'INCONCLUSIVE', 'DIAGNOSIS_COMPLETE', 'PENDING_EXTERNAL',
  'DEPLOYMENT_BLOCKED', 'FIXED', 'FIX_FAILED', 'BLOCKED',
  'FAILURE', 'NON_COMPLIANT', 'WARNING', 'REGRESSION',
  'ALERT', 'HEAL_EXHAUSTED',
]);

const QREF_PATTERN = /\b([A-Za-z]\d+(?:\.\d+)?)\b/;

// ---------------------------------------------------------------------------
// Status lookup
// ---------------------------------------------------------------------------

/**
 * Read current verdict from results.tsv. Returns 'PENDING' if not found.
 */
function getQuestionStatus(qid) {
  if (!fs.existsSync(cfg.resultsTsv)) return 'PENDING';
  const lines = fs.readFileSync(cfg.resultsTsv, 'utf8').split('\n');
  for (const line of lines) {
    const parts = line.split('\t');
    if (parts[0] === qid) {
      return (parts[1] || '').trim() || 'PENDING';
    }
  }
  return 'PENDING';
}

// ---------------------------------------------------------------------------
// Question type classification
// ---------------------------------------------------------------------------

function _classifyType(tagRaw, fields) {
  const explicitType = (fields.type || '').toLowerCase();
  if (explicitType === 'behavioral' || explicitType === 'code_audit') return explicitType;
  const tagLower = tagRaw.toLowerCase();
  if (CODE_AUDIT_TAGS.has(tagLower)) return 'code_audit';
  if (BEHAVIORAL_TAGS.has(tagLower)) return 'behavioral';
  return 'behavioral';
}

// ---------------------------------------------------------------------------
// Parsing
// ---------------------------------------------------------------------------

function _parseBody(body) {
  const fields = {};
  let fm;
  const re = new RegExp(FIELD_PATTERN.source, FIELD_PATTERN.flags);
  while ((fm = re.exec(body)) !== null) {
    const key = fm[1].toLowerCase().replace(/ /g, '_');
    fields[key] = fm[2].trim();
  }
  return fields;
}

/**
 * Parse questions.md from cfg.questionsMd and return list of question dicts.
 */
function parseQuestions() {
  const text = fs.readFileSync(cfg.questionsMd, 'utf8');
  const re = new RegExp(BLOCK_PATTERN.source, BLOCK_PATTERN.flags);
  const matches = [];
  let bm;
  while ((bm = re.exec(text)) !== null) {
    matches.push({ index: bm.index, end: bm.index + bm[0].length, groups: [bm[1], bm[2], bm[3]] });
  }

  const questions = [];
  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    const [qid, tagRaw, titleRaw] = m.groups;
    const title = titleRaw.trim();
    const start = m.end;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const body = text.slice(start, end);
    const fields = _parseBody(body);

    questions.push({
      id: qid,
      mode: fields.mode || tagRaw.toLowerCase(),
      title,
      status: getQuestionStatus(qid),
      question_type: _classifyType(tagRaw, fields),
      target: fields.target || '',
      hypothesis: fields.hypothesis || '',
      test: fields.test || '',
      verdict_threshold: fields.verdict_threshold || '',
      agent_name: (fields.agent || '').trim(),
      finding: (fields.finding || '').trim(),
      source: (fields.source || '').trim(),
      operational_mode: fields.operational_mode || 'diagnose',
      resume_after: (fields.resume_after || '').trim(),
    });
  }

  return questions;
}

/**
 * Parse questions.md from an arbitrary path, using results.tsv in the same dir.
 */
function loadQuestions(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const resultsPath = path.join(path.dirname(filePath), 'results.tsv');

  function localStatus(qid) {
    if (!fs.existsSync(resultsPath)) return 'PENDING';
    const lines = fs.readFileSync(resultsPath, 'utf8').split('\n');
    for (const line of lines) {
      const parts = line.split('\t');
      if (parts[0] === qid) return (parts[1] || '').trim() || 'PENDING';
    }
    return 'PENDING';
  }

  const re = new RegExp(BLOCK_PATTERN.source, BLOCK_PATTERN.flags);
  const matches = [];
  let bm;
  while ((bm = re.exec(text)) !== null) {
    matches.push({ index: bm.index, end: bm.index + bm[0].length, groups: [bm[1], bm[2], bm[3]] });
  }

  const questions = [];
  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    const [qid, tagRaw, titleRaw] = m.groups;
    const title = titleRaw.trim();
    const start = m.end;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const body = text.slice(start, end);
    const fields = _parseBody(body);

    questions.push({
      id: qid,
      mode: fields.mode || tagRaw.toLowerCase(),
      title,
      status: localStatus(qid),
      question_type: _classifyType(tagRaw, fields),
      target: fields.target || '',
      hypothesis: fields.hypothesis || '',
      test: fields.test || '',
      verdict_threshold: fields.verdict_threshold || '',
      agent_name: (fields.agent || '').trim(),
      finding: (fields.finding || '').trim(),
      source: (fields.source || '').trim(),
      operational_mode: fields.operational_mode || 'diagnose',
      resume_after: (fields.resume_after || '').trim(),
    });
  }

  return questions;
}

// ---------------------------------------------------------------------------
// Next-question logic
// ---------------------------------------------------------------------------

/**
 * Return the first PENDING question, skipping parked/terminal statuses.
 * resume_after supports ISO-8601 datetime or question-ID references.
 */
function getNextPending(questions) {
  const now = new Date();

  for (const q of questions) {
    if (PARKED_STATUSES.has(q.status)) continue;
    if (q.status !== 'PENDING') continue;

    const resumeAfter = q.resume_after || '';
    if (resumeAfter) {
      // Try ISO-8601 datetime first
      const gate = new Date(resumeAfter);
      if (!isNaN(gate.getTime()) && _looksLikeDatetime(resumeAfter)) {
        if (now < gate) continue;
      } else {
        // Try question-ID reference
        const refMatch = resumeAfter.match(QREF_PATTERN);
        if (refMatch) {
          const refQid = refMatch[1].toUpperCase();
          const refQ = getQuestionById(questions, refQid);
          if (refQ && !RESOLVED_STATUSES.has(refQ.status)) continue;
        }
      }
    }

    return q;
  }
  return null;
}

/**
 * Heuristic to distinguish ISO datetime strings from question-ID references.
 */
function _looksLikeDatetime(s) {
  return /^\d{4}-\d{2}/.test(s);
}

/**
 * Return the question with the given ID, or null.
 */
function getQuestionById(questions, qid) {
  for (const q of questions) {
    if (q.id === qid) return q;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Status sync
// ---------------------------------------------------------------------------

/**
 * Reconcile questions.md Status fields against results.tsv.
 * Returns count of questions updated.
 */
function syncStatusFromResults() {
  if (!fs.existsSync(cfg.resultsTsv) || !fs.existsSync(cfg.questionsMd)) return 0;

  // Build map of qid → new status from results.tsv
  const doneIds = {};
  const lines = fs.readFileSync(cfg.resultsTsv, 'utf8').split('\n');
  for (const line of lines) {
    const parts = line.split('\t');
    if (parts.length < 2 || parts[0] === 'question_id' || parts[0] === '') continue;
    const verdict = parts[1].trim();
    if (TERMINAL_VERDICTS.has(verdict)) {
      doneIds[parts[0]] = PRESERVE_VERDICTS.has(verdict) ? verdict : 'DONE';
    }
  }

  // Update questions.md
  let text = fs.readFileSync(cfg.questionsMd, 'utf8');
  let updated = 0;

  for (const [qid, newStatus] of Object.entries(doneIds)) {
    let blockStart = text.indexOf(`## ${qid} [`);
    if (blockStart === -1) blockStart = text.indexOf(`## ${qid}\n`);
    if (blockStart === -1) continue;

    const nextBlock = text.indexOf('\n## ', blockStart + 1);
    const blockEnd = nextBlock !== -1 ? nextBlock : text.length;
    const block = text.slice(blockStart, blockEnd);

    if (!block.includes('**Status**: PENDING')) continue;

    const newBlock = block.replace('**Status**: PENDING', `**Status**: ${newStatus}`);
    text = text.slice(0, blockStart) + newBlock + text.slice(blockEnd);
    updated++;
  }

  if (updated) {
    const tmpPath = path.join(path.dirname(cfg.questionsMd), `.questions-${process.pid}.tmp`);
    try {
      fs.writeFileSync(tmpPath, text, 'utf8');
      fs.renameSync(tmpPath, cfg.questionsMd);
    } catch (err) {
      try { fs.unlinkSync(tmpPath); } catch (_) { /* ignore */ }
      throw err;
    }
  }

  return updated;
}

module.exports = {
  parseQuestions,
  loadQuestions,
  getQuestionStatus,
  getNextPending,
  getQuestionById,
  syncStatusFromResults,
  PARKED_STATUSES,
  RESOLVED_STATUSES,
};

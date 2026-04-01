'use strict';
// engine/findings.js — Finding writer, failure classifier, results.tsv updater.
//
// Port of bl/findings.py to Node.js. No local_inference dependency —
// uses heuristic classification only (local model calls to be added later).

const fs = require('fs');
const path = require('path');
const os = require('os');
const { cfg } = require('./config');

// ---------------------------------------------------------------------------
// Failure taxonomy
// ---------------------------------------------------------------------------

const NON_FAILURE_VERDICTS = new Set([
  'HEALTHY', 'WARNING', 'DIAGNOSIS_COMPLETE', 'PENDING_EXTERNAL',
  'PROMISING', 'WEAK', 'CALIBRATED', 'FIXED', 'COMPLIANT', 'PARTIAL',
  'NOT_APPLICABLE', 'IMPROVEMENT', 'OK', 'POSSIBLE', 'UNLIKELY',
  'DEGRADED_TRENDING', 'SUBJECTIVE', 'NOT_MEASURABLE', 'UNCALIBRATED',
  'DEGRADED', 'ALERT', 'UNKNOWN', 'BLOCKED',
]);

const CONFIDENCE_FLOAT = { high: 0.9, medium: 0.6, low: 0.3, uncertain: 0.1 };

/**
 * Classify why a question failed. Returns null for non-failure verdicts.
 * @param {{ verdict: string, details?: string, summary?: string }} result
 * @param {string} mode
 * @returns {string|null} timeout|tool_failure|syntax|logic|hallucination|unknown
 */
function classifyFailureType(result, mode) {
  const verdict = result.verdict || '';
  if (NON_FAILURE_VERDICTS.has(verdict)) return null;

  const details = (result.details || '').toLowerCase();
  const summary = (result.summary || '').toLowerCase();
  const combined = details + ' ' + summary;

  const timeoutKeywords = ['timeout', 'timed out', 'readtimeout', 'connecttimeout', 'time limit exceeded'];
  if (timeoutKeywords.some(k => combined.includes(k))) return 'timeout';

  const toolKeywords = [
    'connection refused', 'connection error', 'importerror', 'modulenotfounderror',
    'no module named', 'oserror', 'permissionerror', 'filenotfounderror',
    'subprocess failed', 'process exited', 'returncode', 'could not connect',
    'httpstatuserror', 'network error',
  ];
  if (toolKeywords.some(k => combined.includes(k))) return 'tool_failure';

  const syntaxKeywords = ['syntaxerror', 'indentationerror', 'parse error', 'syntax error', 'invalid syntax'];
  if (syntaxKeywords.some(k => combined.includes(k))) return 'syntax';

  if (mode === 'correctness' || mode === 'performance') return 'logic';

  if (mode === 'agent' || mode === 'quality' || mode === 'static') {
    const hallucinationKeywords = [
      'no evidence', 'cannot verify', 'no concrete', 'assumed', 'unclear',
      'speculative', 'no data', 'not found in', 'could not find evidence',
    ];
    if (hallucinationKeywords.some(k => combined.includes(k))) return 'hallucination';
  }

  return 'unknown';
}

// ---------------------------------------------------------------------------
// Confidence classification
// ---------------------------------------------------------------------------

const CONFIDENCE_ROUTING = { high: 'accept', medium: 'validate', low: 'escalate', uncertain: 're-run' };

/**
 * Estimate how much trust to place in this verdict.
 * @param {{ verdict: string, data?: object, details?: string }} result
 * @param {string} mode
 * @returns {'high'|'medium'|'low'|'uncertain'}
 */
function classifyConfidence(result, mode) {
  const verdict = result.verdict || '';
  if (verdict === 'INCONCLUSIVE') return 'uncertain';

  const data = result.data || {};
  const details = (result.details || '').toLowerCase();

  if (mode === 'performance') {
    const stages = data.stages || [];
    if (!stages.length) return 'uncertain';
    if (data.early_stop_at) return 'low';
    return stages.length >= 3 ? 'high' : 'medium';
  }

  if (mode === 'correctness') {
    const passed = data.passed || 0;
    const failed = data.failed || 0;
    const total = passed + failed;
    if (total === 0) return 'uncertain';
    if (total >= 10) return 'high';
    if (total >= 3) return 'medium';
    return 'low';
  }

  if (mode === 'agent' || mode === 'quality' || mode === 'static') {
    const concreteSignals = [
      'line ', 'line:', '.py:', '.rs:', '.ts:', '.kt:',
      'function ', 'def ', 'file:', '/src/', 'test_',
      'error:', 'warning:', 'assert', 'found ',
    ];
    const evidenceCount = concreteSignals.filter(s => details.includes(s)).length;
    if (evidenceCount >= 4) return 'high';
    if (evidenceCount >= 2) return 'medium';
    if (evidenceCount >= 1) return 'low';
    if (data && Object.keys(data).length > 0) return 'medium';
    return 'uncertain';
  }

  // Generic fallback by verdict
  if (verdict === 'FAILURE') return details.trim() ? 'high' : 'low';
  if (verdict === 'WARNING') return 'medium';
  if (verdict === 'HEALTHY') return details.trim() ? 'high' : 'medium';

  return 'uncertain';
}

// ---------------------------------------------------------------------------
// Scoring
// ---------------------------------------------------------------------------

const VERDICT_CLARITY = {
  HEALTHY: 1.0, FAILURE: 1.0, WARNING: 0.7, INCONCLUSIVE: 0.0,
  PROMISING: 0.8, WEAK: 0.6, BLOCKED: 0.5,
  CALIBRATED: 1.0, UNCALIBRATED: 0.7, NOT_MEASURABLE: 0.3,
  FIXED: 1.0, FIX_FAILED: 1.0, DIAGNOSIS_COMPLETE: 1.0,
  COMPLIANT: 1.0, NON_COMPLIANT: 1.0, PARTIAL: 0.7, NOT_APPLICABLE: 0.5,
  IMPROVEMENT: 1.0, REGRESSION: 1.0,
  IMMINENT: 1.0, PROBABLE: 0.8, POSSIBLE: 0.6, UNLIKELY: 0.4,
  OK: 1.0, DEGRADED: 0.8, DEGRADED_TRENDING: 0.7, ALERT: 1.0, UNKNOWN: 0.1,
  PENDING_EXTERNAL: 0.5, SUBJECTIVE: 0.2,
};

const CONFIDENCE_EVIDENCE = { high: 1.0, medium: 0.7, low: 0.3, uncertain: 0.0 };

const FAILURE_EXECUTION = {
  null: 1.0, logic: 0.9, syntax: 0.8, hallucination: 0.4,
  unknown: 0.5, timeout: 0.3, tool_failure: 0.0,
};

/**
 * Score a verdict envelope on a 0.0–1.0 scale.
 * @param {{ verdict: string, confidence?: string, failure_type?: string }} result
 * @returns {number}
 */
function scoreResult(result) {
  const verdict = result.verdict || 'INCONCLUSIVE';
  const confidence = result.confidence || 'uncertain';
  const failureType = result.failure_type || null;

  const evidenceQuality = CONFIDENCE_EVIDENCE[confidence] ?? 0.0;
  const verdictClarity = VERDICT_CLARITY[verdict] ?? 0.0;
  const executionSuccess = FAILURE_EXECUTION[failureType] ?? 0.5;

  const score = (evidenceQuality * 0.4) + (verdictClarity * 0.4) + (executionSuccess * 0.2);
  return Math.round(score * 1000) / 1000;
}

// ---------------------------------------------------------------------------
// Finding writer
// ---------------------------------------------------------------------------

const SEVERITY_MAP = {
  FAILURE: 'High', WARNING: 'Medium', HEALTHY: 'Info', INCONCLUSIVE: 'Low',
  PROMISING: 'Info', WEAK: 'Low', BLOCKED: 'Medium',
  CALIBRATED: 'Info', UNCALIBRATED: 'Medium', NOT_MEASURABLE: 'Low',
  FIXED: 'Info', FIX_FAILED: 'High',
  COMPLIANT: 'Info', NON_COMPLIANT: 'High', PARTIAL: 'Medium', NOT_APPLICABLE: 'Low',
  IMPROVEMENT: 'Info', REGRESSION: 'High',
  IMMINENT: 'Critical', PROBABLE: 'High', POSSIBLE: 'Medium', UNLIKELY: 'Low',
  OK: 'Info', DEGRADED: 'Medium', DEGRADED_TRENDING: 'Medium', ALERT: 'High', UNKNOWN: 'Low',
  DIAGNOSIS_COMPLETE: 'Info', PENDING_EXTERNAL: 'Low', SUBJECTIVE: 'Low',
};

/**
 * Write findings/{qid}.md in BrickLayer finding format. Returns the path.
 * @param {{ id: string, title: string, hypothesis: string, mode: string, target: string, verdict_threshold: string, question_type?: string, operational_mode?: string }} question
 * @param {{ verdict: string, summary: string, details: string, data: object, confidence?: string }} result
 * @returns {string} path to the written finding file
 */
function writeFinding(question, result) {
  const qid = question.id;
  const findingPath = path.join(cfg.findingsDir, `${qid}.md`);

  // Clone result for potential mutation
  let r = { ...result };
  const questionType = question.question_type || 'behavioral';

  // C-30: enforce code_audit constraints
  if (questionType === 'code_audit') {
    if (r.confidence === 'high') r.confidence = 'medium';
    if (r.verdict === 'HEALTHY') {
      r.verdict = 'WARNING';
      r.summary = (r.summary || '') +
        ' (C-30: CODE-AUDIT questions cannot produce HEALTHY verdicts — requires live HTTP/test evidence)';
    }
  }

  const severity = SEVERITY_MAP[r.verdict] || 'Low';
  const failureType = r.failure_type;
  const failureTypeLine = failureType ? `\n**Failure Type**: ${failureType}` : '';
  const typeLabel = questionType === 'code_audit' ? 'CODE-AUDIT' : 'BEHAVIORAL';
  const confStr = r.confidence || 'uncertain';
  const confidenceFloat = CONFIDENCE_FLOAT[confStr] ?? 0.1;
  const needsHuman = confidenceFloat < 0.35;
  const modeStr = question.operational_mode || question.mode;

  const content = `# Finding: ${qid} — ${question.title}

**Question**: ${question.hypothesis}
**Verdict**: ${r.verdict}
**Severity**: ${severity}${failureTypeLine}
**Mode**: ${modeStr}
**Type**: ${typeLabel}
**Target**: ${question.target}
**Confidence**: ${confidenceFloat}
**Needs Human**: ${needsHuman}

## Summary

${r.summary}

## Evidence

${(r.details || '').slice(0, 3000)}

## Raw Data

\`\`\`json
${JSON.stringify(r.data, null, 2).slice(0, 2000)}
\`\`\`

## Verdict Threshold

${question.verdict_threshold}

## Mitigation Recommendation

[To be filled by agent analysis]

## Open Follow-up Questions

[Add follow-up questions here if verdict is FAILURE or WARNING]
`;

  fs.writeFileSync(findingPath, content, 'utf8');
  return findingPath;
}

// ---------------------------------------------------------------------------
// Results TSV
// ---------------------------------------------------------------------------

/**
 * Upsert a result row in results.tsv.
 * @param {string} qid
 * @param {string} verdict
 * @param {string} summary
 * @param {string|null} failureType
 * @param {number|null} evalScore
 */
function updateResultsTsv(qid, verdict, summary, failureType, evalScore) {
  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  if (!fs.existsSync(cfg.resultsTsv)) {
    fs.writeFileSync(cfg.resultsTsv, 'question_id\tverdict\tfailure_type\teval_score\tsummary\ttimestamp\n', 'utf8');
  }

  const lines = fs.readFileSync(cfg.resultsTsv, 'utf8').split('\n').filter(Boolean);
  const ft = failureType || '';
  const scoreStr = evalScore != null ? evalScore.toFixed(3) : '';
  const safeSummary = (summary || '').replace(/\t/g, ' ').slice(0, 120);
  const newRow = `${qid}\t${verdict}\t${ft}\t${scoreStr}\t${safeSummary}\t${timestamp}`;

  let updated = false;
  const newLines = lines.map(line => {
    const parts = line.split('\t');
    if (parts[0] === qid) {
      updated = true;
      return newRow;
    }
    return line;
  });

  if (!updated) newLines.push(newRow);

  const content = newLines.join('\n') + '\n';

  // Atomic write via temp file
  const tmpPath = path.join(path.dirname(cfg.resultsTsv), `.results-${process.pid}.tmp`);
  try {
    fs.writeFileSync(tmpPath, content, 'utf8');
    fs.renameSync(tmpPath, cfg.resultsTsv);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* ignore */ }
    throw err;
  }

  _markQuestionDone(qid, verdict);
}

// ---------------------------------------------------------------------------
// Question status update
// ---------------------------------------------------------------------------

const PRESERVE_AS_IS = new Set([
  'INCONCLUSIVE', 'DIAGNOSIS_COMPLETE', 'PENDING_EXTERNAL', 'FIXED', 'FIX_FAILED',
  'BLOCKED', 'FAILURE', 'NON_COMPLIANT', 'WARNING', 'REGRESSION', 'ALERT', 'HEAL_EXHAUSTED',
]);

function _markQuestionDone(qid, verdict) {
  if (!fs.existsSync(cfg.questionsMd)) return;

  const newStatus = PRESERVE_AS_IS.has(verdict) ? verdict : 'DONE';
  const text = fs.readFileSync(cfg.questionsMd, 'utf8');

  let blockStart = text.indexOf(`## ${qid} [`);
  if (blockStart === -1) blockStart = text.indexOf(`## ${qid}\n`);
  if (blockStart === -1) return;

  const nextBlock = text.indexOf('\n## ', blockStart + 1);
  const blockEnd = nextBlock !== -1 ? nextBlock : text.length;
  const block = text.slice(blockStart, blockEnd);

  if (!block.includes('**Status**: PENDING')) return;

  const newBlock = block.replace('**Status**: PENDING', `**Status**: ${newStatus}`);
  const newText = text.slice(0, blockStart) + newBlock + text.slice(blockEnd);

  const tmpPath = path.join(path.dirname(cfg.questionsMd), `.questions-${process.pid}.tmp`);
  try {
    fs.writeFileSync(tmpPath, newText, 'utf8');
    fs.renameSync(tmpPath, cfg.questionsMd);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* ignore */ }
    throw err;
  }
}

module.exports = {
  classifyFailureType,
  classifyConfidence,
  scoreResult,
  writeFinding,
  updateResultsTsv,
  CONFIDENCE_ROUTING,
  NON_FAILURE_VERDICTS,
  CONFIDENCE_FLOAT,
};

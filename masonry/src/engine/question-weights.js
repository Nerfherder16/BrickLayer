'use strict';
// engine/question-weights.js — Self-improving question bank weights.
//
// Port of bl/question_weights.py to Node.js.

const fs = require('fs');
const path = require('path');

const _WEIGHTS_FILE = '.bl-weights.json';
const NEEDS_HUMAN_THRESHOLD = 0.35;

function shouldFlagHuman(confidence) {
  return confidence < NEEDS_HUMAN_THRESHOLD;
}

// --- Persistence ---

function _weightsPath(projectDir) {
  return path.join(String(projectDir), _WEIGHTS_FILE);
}

function loadWeights(projectDir) {
  const wpath = _weightsPath(projectDir);
  if (!fs.existsSync(wpath)) return {};
  try {
    const raw = JSON.parse(fs.readFileSync(wpath, 'utf8'));
    const weights = {};
    for (const [qid, entry] of Object.entries(raw)) {
      if (typeof entry !== 'object' || entry === null) continue;
      weights[qid] = {
        questionId: entry.question_id || entry.questionId || qid,
        runs: parseInt(entry.runs || 0, 10),
        failures: parseInt(entry.failures || 0, 10),
        warnings: parseInt(entry.warnings || 0, 10),
        healthys: parseInt(entry.healthys || 0, 10),
        inconclusives: parseInt(entry.inconclusives || 0, 10),
        lastVerdict: entry.last_verdict || entry.lastVerdict || '',
        weight: parseFloat(entry.weight || 1.0),
        lastUpdated: entry.last_updated || entry.lastUpdated || '',
        lastQualityScore: entry.last_quality_score != null ? parseFloat(entry.last_quality_score) : null,
      };
    }
    return weights;
  } catch {
    return {};
  }
}

function saveWeights(projectDir, weights) {
  const serialized = {};
  for (const [qid, qw] of Object.entries(weights)) {
    serialized[qid] = {
      question_id: qw.questionId,
      runs: qw.runs,
      failures: qw.failures,
      warnings: qw.warnings,
      healthys: qw.healthys,
      inconclusives: qw.inconclusives,
      last_verdict: qw.lastVerdict,
      weight: qw.weight,
      last_updated: qw.lastUpdated,
      last_quality_score: qw.lastQualityScore,
    };
  }
  fs.writeFileSync(_weightsPath(projectDir), JSON.stringify(serialized, null, 2), 'utf8');
}

// --- Weight computation ---

function computeWeight(qw) {
  if (qw.runs === 0) return 1.0;

  const signalRuns = qw.failures + qw.warnings + qw.inconclusives;
  if (signalRuns === 0) {
    if (qw.runs >= 5) return 0.1;
    if (qw.runs >= 3) return 0.3;
  }

  if (qw.healthys === 0 && qw.failures === 0 && qw.warnings === 0 && qw.runs >= 3) {
    return 0.2;
  }

  const failureBonus = Math.min(qw.failures * 0.5, 2.0);
  const warningBonus = Math.min(qw.warnings * 0.2, 0.6);
  return Math.min(1.0 + failureBonus + warningBonus, 3.0);
}

// --- Record a result ---

function recordResult(projectDir, questionId, verdict, qualityScore = null) {
  const weights = loadWeights(projectDir);
  const qw = weights[questionId] || {
    questionId, runs: 0, failures: 0, warnings: 0, healthys: 0,
    inconclusives: 0, lastVerdict: '', weight: 1.0, lastUpdated: '',
    lastQualityScore: null,
  };

  qw.runs += 1;
  qw.lastVerdict = verdict;
  const v = verdict.toUpperCase();
  if (v === 'FAILURE') qw.failures += 1;
  else if (v === 'WARNING') qw.warnings += 1;
  else if (v === 'HEALTHY') qw.healthys += 1;
  else qw.inconclusives += 1;

  if (qualityScore !== null) qw.lastQualityScore = qualityScore;

  qw.weight = computeWeight(qw);

  if (v === 'INCONCLUSIVE' && qualityScore !== null && qualityScore < 0.4) {
    qw.weight = Math.min(qw.weight + 0.3, 3.0);
  }

  qw.lastUpdated = new Date().toISOString();
  weights[questionId] = qw;
  saveWeights(projectDir, weights);
  return qw;
}

// --- Selection helpers ---

function getSortedQuestions(projectDir, questionIds) {
  const weights = loadWeights(projectDir);
  return [...questionIds].sort((a, b) => {
    const wa = weights[a] ? weights[a].weight : 1.0;
    const wb = weights[b] ? weights[b].weight : 1.0;
    return wb - wa;
  });
}

function pruneCandidates(projectDir, threshold = 0.15) {
  const weights = loadWeights(projectDir);
  return Object.entries(weights)
    .filter(([, qw]) => qw.weight <= threshold)
    .map(([qid]) => qid);
}

// --- Report ---

function weightReport(projectDir) {
  const weights = loadWeights(projectDir);
  const entries = Object.values(weights);
  if (entries.length === 0) return 'Question Weights (0 tracked): no data.';

  const prunable = pruneCandidates(projectDir);
  const sorted = [...entries].sort((a, b) => b.weight - a.weight);

  const lines = [`Question Weights (${entries.length} tracked):`];
  for (const qw of sorted) {
    let label;
    if (qw.weight >= 1.5) label = 'HIGH';
    else if (qw.weight >= 0.5) label = 'NORM';
    else label = 'LOW ';

    const parts = [];
    if (qw.failures) parts.push(`${qw.failures}F`);
    if (qw.warnings) parts.push(`${qw.warnings}W`);
    if (qw.healthys) parts.push(`${qw.healthys}H`);
    if (qw.inconclusives) parts.push(`${qw.inconclusives}I`);
    const runSummary = parts.length ? parts.join(' ') : 'no signal';

    lines.push(
      `  ${label}  ${qw.questionId.padEnd(10)}  weight=${String(qw.weight.toFixed(2)).padEnd(5)}  ` +
      `(${qw.runs} run${qw.runs !== 1 ? 's' : ''}: ${runSummary})`
    );
  }

  if (prunable.length) {
    lines.push(`PRUNE candidates: ${prunable.sort().join(', ')}`);
  } else {
    lines.push('PRUNE candidates: none');
  }

  return lines.join('\n');
}

module.exports = {
  NEEDS_HUMAN_THRESHOLD, shouldFlagHuman,
  loadWeights, saveWeights, computeWeight,
  recordResult, getSortedQuestions, pruneCandidates, weightReport,
};

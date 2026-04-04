'use strict';
// engine/baseline.js — Baseline snapshot manager for BL 2.0.
//
// Port of bl/baseline.py to Node.js.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function _baselineDir(projectDir) {
  const d = path.join(String(projectDir), '.bl-baseline');
  fs.mkdirSync(d, { recursive: true });
  return d;
}

function _gitSha(projectDir) {
  try {
    const result = execSync('git rev-parse --short HEAD', {
      cwd: String(projectDir),
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return result.trim() || null;
  } catch {
    return null;
  }
}

function _numericFields(d) {
  const out = {};
  if (!d || typeof d !== 'object') return out;
  for (const [k, v] of Object.entries(d)) {
    if (typeof v === 'number') out[k] = v;
  }
  return out;
}

function _issueList(result) {
  const data = result.data || {};
  const candidates = [
    ...(data.issues || []),
    ...(data.errors || []),
    ...(data.checks_failed || []),
    ...(data.failure_reasons || []),
  ];
  return candidates.filter(c => c).map(String);
}

function saveBaseline(projectDir, questionId, result) {
  const baselineFile = path.join(_baselineDir(projectDir), `${questionId}.json`);
  const snapshot = {
    question_id: questionId,
    timestamp: new Date().toISOString(),
    git_sha: _gitSha(projectDir),
    result,
  };
  fs.writeFileSync(baselineFile, JSON.stringify(snapshot, null, 2), 'utf8');
}

function loadBaseline(projectDir, questionId) {
  const baselineFile = path.join(_baselineDir(projectDir), `${questionId}.json`);
  if (!fs.existsSync(baselineFile)) return null;
  try {
    return JSON.parse(fs.readFileSync(baselineFile, 'utf8'));
  } catch {
    return null;
  }
}

function diffAgainstBaseline(result, baseline) {
  const baselineResult = baseline.result || baseline;

  const currentVerdict = result.verdict || 'INCONCLUSIVE';
  const baselineVerdict = baselineResult.verdict || 'INCONCLUSIVE';

  const _SEVERITY = { HEALTHY: 0, INCONCLUSIVE: 1, WARNING: 2, FAILURE: 3 };
  const currentSev = _SEVERITY[currentVerdict] ?? 1;
  const baselineSev = _SEVERITY[baselineVerdict] ?? 1;

  const verdictChanged = currentSev > baselineSev;
  const verdictDelta = verdictChanged ? `${baselineVerdict}→${currentVerdict}` : null;

  const currentNums = _numericFields(result.data);
  const baselineNums = _numericFields(baselineResult.data);

  const metricDeltas = {};
  for (const [field, curVal] of Object.entries(currentNums)) {
    if (!(field in baselineNums)) continue;
    const baseVal = baselineNums[field];
    if (baseVal === curVal) continue;
    const deltaPct = baseVal !== 0
      ? Math.round(((curVal - baseVal) / Math.abs(baseVal)) * 1000) / 10
      : (curVal !== 0 ? Infinity : 0.0);
    metricDeltas[field] = { baseline: baseVal, current: curVal, delta_pct: deltaPct };
  }

  const currentIssues = new Set(_issueList(result));
  const baselineIssues = new Set(_issueList(baselineResult));
  const newIssues = [...currentIssues].filter(i => !baselineIssues.has(i)).sort();
  const resolvedIssues = [...baselineIssues].filter(i => !currentIssues.has(i)).sort();

  const hasRegression = verdictChanged || newIssues.length > 0;

  return {
    hasRegression,
    verdictChanged,
    verdictDelta,
    metricDeltas,
    newIssues,
    resolvedIssues,
  };
}

function listBaselines(projectDir) {
  const blDir = _baselineDir(projectDir);
  const summaries = [];
  let files;
  try {
    files = fs.readdirSync(blDir).sort();
  } catch {
    return summaries;
  }

  for (const f of files) {
    if (!f.endsWith('.json') || f.includes('_latest')) continue;
    try {
      const snap = JSON.parse(fs.readFileSync(path.join(blDir, f), 'utf8'));
      summaries.push({
        questionId: snap.question_id || path.basename(f, '.json'),
        timestamp: snap.timestamp || '',
        verdict: (snap.result || {}).verdict || 'UNKNOWN',
        gitSha: snap.git_sha || null,
      });
    } catch {
      continue;
    }
  }
  return summaries;
}

function clearBaseline(projectDir, questionId) {
  const baselineFile = path.join(_baselineDir(projectDir), `${questionId}.json`);
  if (fs.existsSync(baselineFile)) {
    fs.unlinkSync(baselineFile);
    return true;
  }
  return false;
}

module.exports = {
  saveBaseline, loadBaseline, diffAgainstBaseline, listBaselines, clearBaseline,
};

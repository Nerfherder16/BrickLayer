'use strict';
// engine/agent-db.js — Agent performance database.
//
// Port of bl/agent_db.py to Node.js.

const fs = require('fs');
const path = require('path');

const _SUCCESS_VERDICTS = new Set([
  'HEALTHY', 'FIXED', 'COMPLIANT', 'CALIBRATED', 'IMPROVEMENT',
  'OK', 'PROMISING', 'DIAGNOSIS_COMPLETE', 'NOT_APPLICABLE', 'DONE',
]);

const _PARTIAL_VERDICTS = new Set([
  'WARNING', 'PARTIAL', 'WEAK', 'DEGRADED', 'DEGRADED_TRENDING',
  'FIX_FAILED', 'PENDING_EXTERNAL', 'BLOCKED', 'SUBJECTIVE',
  'IMMINENT', 'PROBABLE', 'POSSIBLE', 'UNLIKELY', 'HEAL_EXHAUSTED',
]);

const MIN_RUNS_FOR_REVIEW = 3;
const UNDERPERFORMER_THRESHOLD = 0.40;

function _dbPath(projectRoot) {
  return path.join(String(projectRoot), 'agent_db.json');
}

function _load(projectRoot) {
  const dbp = _dbPath(projectRoot);
  if (!fs.existsSync(dbp)) return {};
  try {
    return JSON.parse(fs.readFileSync(dbp, 'utf8'));
  } catch {
    return {};
  }
}

function _save(projectRoot, db) {
  fs.writeFileSync(_dbPath(projectRoot), JSON.stringify(db, null, 2), 'utf8');
}

function _computeScore(record) {
  const total = record.runs || 0;
  if (total === 0) return 1.0;
  const verdicts = record.verdicts || {};
  let success = 0;
  let partial = 0;
  for (const [v, count] of Object.entries(verdicts)) {
    if (_SUCCESS_VERDICTS.has(v)) success += count;
    else if (_PARTIAL_VERDICTS.has(v)) partial += count;
  }
  return (success + partial * 0.5) / total;
}

function recordRun(projectRoot, agentName, verdict, durationMs = 0, qualityScore = null) {
  const db = _load(projectRoot);
  const now = new Date().toISOString();

  if (!(agentName in db)) {
    db[agentName] = {
      runs: 0, verdicts: {}, score: 1.0, last_run: now,
      created: now, repair_count: 0, last_repair: null, run_history: [],
    };
  }

  const rec = db[agentName];
  rec.runs += 1;
  rec.verdicts[verdict] = (rec.verdicts[verdict] || 0) + 1;
  rec.last_run = now;
  rec.score = Math.round(_computeScore(rec) * 10000) / 10000;

  const runEntry = { timestamp: now, verdict, duration_ms: durationMs, quality_score: qualityScore };
  if (!rec.run_history) rec.run_history = [];
  rec.run_history.push(runEntry);
  if (rec.run_history.length > 100) {
    rec.run_history = rec.run_history.slice(-100);
  }

  _save(projectRoot, db);
  return rec.score;
}

function getScore(projectRoot, agentName) {
  const db = _load(projectRoot);
  if (!(agentName in db)) return 1.0;
  return Math.round(_computeScore(db[agentName]) * 10000) / 10000;
}

function getTrend(projectRoot, agentName, window = 5) {
  const db = _load(projectRoot);
  if (!(agentName in db)) {
    return { scoreRecent: 0.0, scorePrior: null, trending: 'insufficient_data', recentRuns: 0 };
  }

  const history = db[agentName].run_history || [];
  const total = history.length;

  if (total < window) {
    const recentCount = total;
    let scoreRecent = 0.0;
    if (recentCount > 0) {
      const success = history.filter(r => _SUCCESS_VERDICTS.has(r.verdict)).length;
      scoreRecent = success / recentCount;
    }
    return {
      scoreRecent: Math.round(scoreRecent * 10000) / 10000,
      scorePrior: null,
      trending: 'insufficient_data',
      recentRuns: recentCount,
    };
  }

  const recent = history.slice(-window);
  const prior = total >= window * 2 ? history.slice(-(window * 2), -window) : null;

  const successRecent = recent.filter(r => _SUCCESS_VERDICTS.has(r.verdict)).length;
  const scoreRecent = successRecent / window;

  if (prior === null) {
    return {
      scoreRecent: Math.round(scoreRecent * 10000) / 10000,
      scorePrior: null,
      trending: 'insufficient_data',
      recentRuns: window,
    };
  }

  const successPrior = prior.filter(r => _SUCCESS_VERDICTS.has(r.verdict)).length;
  const scorePrior = successPrior / prior.length;

  let trending;
  if (scoreRecent > scorePrior + 0.1) trending = 'up';
  else if (scoreRecent < scorePrior - 0.1) trending = 'down';
  else trending = 'stable';

  return {
    scoreRecent: Math.round(scoreRecent * 10000) / 10000,
    scorePrior: Math.round(scorePrior * 10000) / 10000,
    trending,
    recentRuns: window,
  };
}

function recordRepair(projectRoot, agentName) {
  const db = _load(projectRoot);
  if (!(agentName in db)) return;
  db[agentName].repair_count = (db[agentName].repair_count || 0) + 1;
  db[agentName].last_repair = new Date().toISOString();
  _save(projectRoot, db);
}

function getUnderperformers(projectRoot, threshold = UNDERPERFORMER_THRESHOLD, minRuns = MIN_RUNS_FOR_REVIEW) {
  const db = _load(projectRoot);
  const result = [];
  for (const [name, rec] of Object.entries(db)) {
    if ((rec.runs || 0) >= minRuns) {
      const score = _computeScore(rec);
      if (score < threshold) {
        result.push({
          name,
          score: Math.round(score * 10000) / 10000,
          runs: rec.runs,
          verdicts: rec.verdicts,
          repairCount: rec.repair_count || 0,
          lastRun: rec.last_run || '',
        });
      }
    }
  }
  return result.sort((a, b) => a.score - b.score);
}

function getSummary(projectRoot) {
  const db = _load(projectRoot);
  const rows = [];
  for (const [name, rec] of Object.entries(db)) {
    rows.push({
      name,
      runs: rec.runs || 0,
      score: Math.round(_computeScore(rec) * 10000) / 10000,
      verdicts: rec.verdicts || {},
      lastRun: rec.last_run || '',
      repairCount: rec.repair_count || 0,
      lastRepair: rec.last_repair || null,
    });
  }
  return rows.sort((a, b) => a.score - b.score);
}

module.exports = {
  recordRun, getScore, getTrend, recordRepair,
  getUnderperformers, getSummary,
  MIN_RUNS_FOR_REVIEW, UNDERPERFORMER_THRESHOLD,
};

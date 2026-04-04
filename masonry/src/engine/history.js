'use strict';
// engine/history.js — SQLite verdict history ledger and regression detector.
//
// Port of bl/history.py to Node.js. Stores every verdict produced by a
// campaign run. Detects regressions (HEALTHY → FAILURE/WARNING) across runs.

const Database = require('better-sqlite3');
const { cfg } = require('./config');

const SCHEMA = `
CREATE TABLE IF NOT EXISTS verdict_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id  TEXT NOT NULL,
    verdict      TEXT NOT NULL,
    failure_type TEXT,
    confidence   TEXT,
    summary      TEXT,
    run_id       TEXT,
    timestamp    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_qid_time
    ON verdict_history(question_id, timestamp);
`;

function _connect() {
  const db = new Database(cfg.historyDb);
  db.exec(SCHEMA);
  return db;
}

// ---------------------------------------------------------------------------
// Write
// ---------------------------------------------------------------------------

function recordVerdict(questionId, verdict, summary = '', failureType = null, confidence = null, runId = null) {
  const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const rid = runId || ts;
  const db = _connect();
  try {
    db.prepare(`
      INSERT INTO verdict_history
        (question_id, verdict, failure_type, confidence, summary, run_id, timestamp)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(questionId, verdict, failureType, confidence, (summary || '').slice(0, 500), rid, ts);
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// Read
// ---------------------------------------------------------------------------

function getHistory(questionId, limit = 20) {
  const db = _connect();
  try {
    return db.prepare(`
      SELECT question_id, verdict, failure_type, confidence, summary, run_id, timestamp
      FROM verdict_history
      WHERE question_id = ?
      ORDER BY id DESC
      LIMIT ?
    `).all(questionId, limit);
  } finally {
    db.close();
  }
}

function getAllLatest() {
  const db = _connect();
  try {
    return db.prepare(`
      SELECT question_id, verdict, failure_type, confidence, summary, run_id, timestamp
      FROM verdict_history
      WHERE id IN (
        SELECT MAX(id) FROM verdict_history GROUP BY question_id
      )
      ORDER BY question_id
    `).all();
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// Regression detection
// ---------------------------------------------------------------------------

const REGRESSIONS = new Set([
  'HEALTHY->FAILURE', 'HEALTHY->WARNING', 'WARNING->FAILURE',
  'COMPLIANT->NON_COMPLIANT', 'COMPLIANT->FAILURE',
  'FIXED->FAILURE', 'FIXED->NON_COMPLIANT', 'FIXED->WARNING',
  'HEALTHY->NON_COMPLIANT', 'HEALTHY->ALERT',
  'DIAGNOSIS_COMPLETE->FAILURE',
]);

function detectRegression(questionId, newVerdict) {
  const history = getHistory(questionId, 2);
  if (history.length < 2) return null;

  // history[0] is the row we just wrote; history[1] is the prior run
  const prevVerdict = history[1].verdict;
  const key = `${prevVerdict}->${newVerdict}`;

  if (REGRESSIONS.has(key)) {
    return {
      question_id: questionId,
      previous_verdict: prevVerdict,
      new_verdict: newVerdict,
      previous_timestamp: history[1].timestamp,
    };
  }
  return null;
}

function getRegressions() {
  const db = _connect();
  try {
    const rows = db.prepare(`
      SELECT question_id, verdict, timestamp
      FROM verdict_history
      ORDER BY question_id, id DESC
    `).all();

    // Group into per-qid lists (already sorted newest-first within each group)
    const byQid = {};
    for (const row of rows) {
      if (!byQid[row.question_id]) byQid[row.question_id] = [];
      byQid[row.question_id].push(row);
    }

    const regressions = [];
    for (const [qid, records] of Object.entries(byQid)) {
      if (records.length < 2) continue;
      const [current, previous] = records;
      const key = `${previous.verdict}->${current.verdict}`;
      if (REGRESSIONS.has(key)) {
        regressions.push({
          question_id: qid,
          previous_verdict: previous.verdict,
          new_verdict: current.verdict,
          previous_timestamp: previous.timestamp,
          current_timestamp: current.timestamp,
        });
      }
    }
    return regressions;
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function regressionReport() {
  const regressions = getRegressions();
  if (!regressions.length) return '';

  const lines = [`REGRESSIONS DETECTED (${regressions.length}):`];
  for (const r of regressions) {
    lines.push(
      `  ${r.question_id}: ${r.previous_verdict} -> ${r.new_verdict}` +
      `  (was: ${r.previous_timestamp})`,
    );
  }
  return lines.join('\n');
}

module.exports = {
  recordVerdict,
  getHistory,
  getAllLatest,
  detectRegression,
  getRegressions,
  regressionReport,
};

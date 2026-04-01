'use strict';
// engine/training-schema.js — Training System schema mappings.
//
// Port of bl/training_schema.py to Node.js.

const PASS_VERDICTS = new Set([
  'HEALTHY', 'FIXED', 'COMPLIANT', 'CALIBRATED', 'IMPROVEMENT',
  'FRONTIER_VIABLE', 'DIAGNOSIS_COMPLETE', 'VALIDATED', 'OPTIMIZED',
  'PREDICTED', 'ALERT_RESOLVED',
]);

const PARTIAL_VERDICTS = {
  WARNING: 0.70,
  FRONTIER_PARTIAL: 0.60,
  IMMINENT: 0.50,
  PROBABLE: 0.50,
  DEGRADED: 0.40,
  INCONCLUSIVE: 0.30,
  ALERT: 0.25,
};

const FAIL_VERDICTS = new Set([
  'FAILURE', 'FIX_FAILED', 'NON_COMPLIANT', 'REGRESSION', 'FRONTIER_BLOCKED',
]);

const SFT_BLOCKED_VERDICTS = new Set([
  'INCONCLUSIVE', 'FIX_FAILED', 'FRONTIER_BLOCKED',
]);

const CONFIDENCE_MAP = {
  high: 1.0,
  medium: 0.7,
  low: 0.3,
  uncertain: 0.0,
};

const NEEDS_HUMAN_THRESHOLD = 0.35;
const SFT_MIN_SCORE = 0.82;

function verdictToBinaryPass(verdict) {
  return PASS_VERDICTS.has(verdict.toUpperCase());
}

function verdictToPartialCredit(verdict) {
  const v = verdict.toUpperCase();
  if (PASS_VERDICTS.has(v)) return 1.0;
  if (FAIL_VERDICTS.has(v)) return 0.0;
  return PARTIAL_VERDICTS[v] ?? 0.2;
}

function confidenceStrToFloat(confidence) {
  if (confidence === null || confidence === undefined) return 0.5;
  if (typeof confidence === 'number') return confidence;
  const s = String(confidence).trim().toLowerCase();
  const num = parseFloat(s);
  if (!isNaN(num)) return Math.max(0.0, Math.min(1.0, num));
  return CONFIDENCE_MAP[s] ?? 0.5;
}

function computeTrajectoryScore(evalScore, verdict, confidence = null) {
  const partial = verdictToPartialCredit(verdict);
  let base;
  if (evalScore !== null && evalScore !== undefined) {
    base = Math.max(0.0, Math.min(1.0, Number(evalScore) / 100.0));
  } else {
    base = partial;
  }
  const conf = confidenceStrToFloat(confidence);
  return Math.round((base * 0.8 + conf * 0.2) * 10000) / 10000;
}

function isSftEligible(verdict, trajectoryScore, needsHuman = false) {
  if (trajectoryScore < SFT_MIN_SCORE) return false;
  if (SFT_BLOCKED_VERDICTS.has(verdict.toUpperCase())) return false;
  if (needsHuman) return false;
  return true;
}

function verdictToCriticFlag(verdict) {
  const v = verdict.toUpperCase();
  if (PASS_VERDICTS.has(v)) return 'good';
  if (FAIL_VERDICTS.has(v)) return 'mistake';
  if (v === 'INCONCLUSIVE') return 'waste';
  return 'good';
}

module.exports = {
  PASS_VERDICTS, PARTIAL_VERDICTS, FAIL_VERDICTS, SFT_BLOCKED_VERDICTS,
  CONFIDENCE_MAP, NEEDS_HUMAN_THRESHOLD, SFT_MIN_SCORE,
  verdictToBinaryPass, verdictToPartialCredit, confidenceStrToFloat,
  computeTrajectoryScore, isSftEligible, verdictToCriticFlag,
};

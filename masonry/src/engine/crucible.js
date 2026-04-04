'use strict';
// engine/crucible.js — Agent benchmarking and promotion/retirement (C-15).
//
// Port of bl/crucible.py to Node.js. Scores agent output quality against
// rubrics, tracks scores in SQLite, promotes/flags/retires agents.

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const PROMOTE_THRESHOLD = 0.80;
const FLAG_THRESHOLD = 0.50;
const RETIRE_THRESHOLD = 0.40;
const MIN_RUNS_FOR_STATUS = 3;

const KNOWN_AGENTS = [
  'hypothesis-generator', 'question-designer', 'synthesizer', 'quantitative-analyst',
  'diagnose-analyst', 'fix-implementer', 'compliance-auditor', 'design-reviewer',
];

const SCHEMA = `
CREATE TABLE IF NOT EXISTS crucible_scores (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    agent   TEXT NOT NULL,
    score   REAL NOT NULL,
    checks  TEXT NOT NULL,
    details TEXT,
    ts      TEXT NOT NULL
);
`;

// ---------------------------------------------------------------------------
// SQLite
// ---------------------------------------------------------------------------

function _getDb(projectDir) {
  const dbPath = path.join(projectDir, 'history.db');
  const db = new Database(dbPath);
  db.exec(SCHEMA);
  return db;
}

function recordScore(projectDir, score) {
  const ts = score.timestamp || new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const db = _getDb(projectDir);
  try {
    db.prepare('INSERT INTO crucible_scores (agent, score, checks, details, ts) VALUES (?, ?, ?, ?, ?)')
      .run(score.agent, score.score, JSON.stringify(score.checks || {}), (score.details || '').slice(0, 1000), ts);
  } finally {
    db.close();
  }
}

function getAgentStatus(projectDir, agent) {
  const db = _getDb(projectDir);
  try {
    const rows = db.prepare('SELECT score FROM crucible_scores WHERE agent = ? ORDER BY id DESC LIMIT 10')
      .all(agent);

    const runCount = rows.length;
    if (runCount === 0) {
      return { agent, status: 'active', avg_score: 0.0, run_count: 0, last_score: 0.0 };
    }

    const scores = rows.map(r => r.score);
    const avg = scores.reduce((s, v) => s + v, 0) / scores.length;
    const last = scores[0];

    let status = 'active';
    if (runCount >= MIN_RUNS_FOR_STATUS) {
      if (avg >= PROMOTE_THRESHOLD) status = 'promoted';
      else if (avg < RETIRE_THRESHOLD) status = 'retired';
      else if (avg < FLAG_THRESHOLD) status = 'flagged';
    }

    return { agent, status, avg_score: avg, run_count: runCount, last_score: last };
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// Weighted scoring
// ---------------------------------------------------------------------------

function _weighted(checks) {
  let totalWeight = 0;
  let score = 0;
  const passRates = {};

  for (const [name, [value, weight]] of Object.entries(checks)) {
    totalWeight += weight;
    score += value * weight;
    passRates[name] = value;
  }

  return [score / Math.max(totalWeight, 1.0), passRates];
}

// ---------------------------------------------------------------------------
// Rubrics
// ---------------------------------------------------------------------------

function scoreHypothesisGenerator(projectDir) {
  const qpath = path.join(projectDir, 'questions.md');
  if (!fs.existsSync(qpath)) {
    return { agent: 'hypothesis-generator', score: 0.0, checks: {}, details: 'questions.md not found' };
  }

  const text = fs.readFileSync(qpath, 'utf8');
  const waveNums = [...text.matchAll(/^## \w+(\d+)\.\d+/gm)].map(m => parseInt(m[1]));
  const maxWave = waveNums.length ? Math.max(...waveNums) : 0;

  if (maxWave < 2) {
    return { agent: 'hypothesis-generator', score: 0.0, checks: {}, details: 'No Wave 2+ questions found' };
  }

  const blocks = text.split(/(?=^## \w+[2-9]\d*\.\d+)/m)
    .filter(b => /^## \w+[2-9]\d*\.\d+/.test(b.trim()));

  if (!blocks.length) {
    return { agent: 'hypothesis-generator', score: 0.0, checks: {}, details: 'No Wave 2+ question blocks found' };
  }

  const weights = { has_status: 0.10, has_derived_from: 0.35, has_test: 0.20, has_verdict_threshold: 0.25, has_hypothesis: 0.10 };
  const allResults = {};
  for (const k of Object.keys(weights)) allResults[k] = [];

  for (const block of blocks) {
    allResults.has_status.push(/PENDING|DONE|Status/.test(block) ? 1.0 : 0.0);
    allResults.has_derived_from.push(/Derived from|Motivated by/.test(block) ? 1.0 : 0.0);
    allResults.has_test.push(/\*\*Method\*\*:|\*\*Test\*\*:|\*\*Simulation path\*\*:|Test:|pytest|Simulation path/.test(block) ? 1.0 : 0.0);
    allResults.has_verdict_threshold.push(
      (/FAILURE:/.test(block) && /HEALTHY:/.test(block)) || /\*\*Verdict threshold\*\*:|\*\*Success criterion\*\*:/.test(block) ? 1.0 : 0.0,
    );
    allResults.has_hypothesis.push(/\*\*Hypothesis\*\*:|Hypothesis:/.test(block) ? 1.0 : 0.0);
  }

  const passRates = {};
  for (const [k, vs] of Object.entries(allResults)) {
    passRates[k] = vs.reduce((s, v) => s + v, 0) / vs.length;
  }

  const score = Object.keys(weights).reduce((s, k) => s + passRates[k] * weights[k], 0);
  return { agent: 'hypothesis-generator', score: Math.round(score * 10000) / 10000, checks: passRates, details: `Scored ${blocks.length} Wave 2+ questions` };
}

function scoreSynthesizer(projectDir) {
  const spath = path.join(projectDir, 'findings', 'synthesis.md');
  if (!fs.existsSync(spath)) {
    return { agent: 'synthesizer', score: 0.0, checks: {}, details: 'findings/synthesis.md not found' };
  }

  const text = fs.readFileSync(spath, 'utf8');
  const checksRaw = {
    has_critical_path: [text.includes('Critical Path') ? 1.0 : 0.0, 0.25],
    has_finding_refs: [/\b[A-Z]\d+\.\d+/.test(text) ? 1.0 : 0.0, 0.30],
    has_residual_risk: [/[Rr]esidual [Rr]isk|residual/.test(text) ? 1.0 : 0.0, 0.20],
    has_tiered_roadmap: [/Phase [23]|Before/.test(text) ? 1.0 : 0.0, 0.15],
    has_mitigation: [text.toLowerCase().includes('mitigat') ? 1.0 : 0.0, 0.10],
  };

  const [score, passRates] = _weighted(checksRaw);
  return { agent: 'synthesizer', score: Math.round(score * 10000) / 10000, checks: passRates, details: 'synthesis.md checks' };
}

function scoreQuantitativeAnalyst(projectDir) {
  const findingsDir = path.join(projectDir, 'findings');
  if (!fs.existsSync(findingsDir)) {
    return { agent: 'quantitative-analyst', score: 0.0, checks: {}, details: 'findings/ not found' };
  }

  const perfFiles = [];
  for (const file of fs.readdirSync(findingsDir).filter(f => f.endsWith('.md') && f !== 'synthesis.md').sort()) {
    const content = fs.readFileSync(path.join(findingsDir, file), 'utf8');
    if (/\b(performance|D1|D5|PERFORMANCE)\b/.test(content)) perfFiles.push(content);
  }

  if (!perfFiles.length) {
    return { agent: 'quantitative-analyst', score: 0.0, checks: {}, details: 'No performance findings found' };
  }

  const weights = { has_metric: 0.30, has_verdict_justification: 0.30, has_boundary_value: 0.25, has_recommendation: 0.15 };
  const perCheck = {};
  for (const k of Object.keys(weights)) perCheck[k] = [];

  for (const content of perfFiles) {
    perCheck.has_metric.push(/\d+\s*(ms|%|req\/s|rps|s\b|MB|KB|GB)/.test(content) ? 1.0 : 0.0);
    perCheck.has_verdict_justification.push(/[Vv]erdict\s*:/.test(content) ? 1.0 : 0.0);
    perCheck.has_boundary_value.push(/threshold|boundary|>\s*\d|<\s*\d/.test(content) ? 1.0 : 0.0);
    perCheck.has_recommendation.push(/recommend|mitigat|action/i.test(content) ? 1.0 : 0.0);
  }

  const passRates = {};
  for (const [k, vs] of Object.entries(perCheck)) passRates[k] = vs.reduce((s, v) => s + v, 0) / vs.length;

  const score = Object.keys(weights).reduce((s, k) => s + passRates[k] * weights[k], 0);
  return { agent: 'quantitative-analyst', score: Math.round(score * 10000) / 10000, checks: passRates, details: `Scored ${perfFiles.length} performance findings` };
}

function scoreQuestionDesigner(projectDir) {
  const qpath = path.join(projectDir, 'questions.md');
  if (!fs.existsSync(qpath)) {
    return { agent: 'question-designer', score: 0.0, checks: {}, details: 'questions.md not found' };
  }

  const text = fs.readFileSync(qpath, 'utf8');
  const wave2Match = text.match(/^## \w+[2-9]\d*\.\d+/m);
  const wave1Text = wave2Match ? text.slice(0, wave2Match.index) : text;

  const blocks = wave1Text.split(/(?=^## [A-Z]+\d+(?:\.\d+)?(?:\s|$))/m)
    .filter(b => /^## [A-Z]+\d+(?:\.\d+)?(?:\s|$)/.test(b.trim()));

  if (blocks.length < 5) {
    return { agent: 'question-designer', score: 0.0, checks: {}, details: `Only ${blocks.length} Wave 1 questions found` };
  }

  const uniquePrefixes = new Set([...wave1Text.matchAll(/^## ([A-Z]+)\d+(?:\.\d+)?(?:\s|$)/gm)].map(m => m[1]));
  const domainsScore = Math.min(1.0, uniquePrefixes.size / 5.0);

  const hasThresholds = blocks.filter(b =>
    (/FAILURE:/.test(b) && /HEALTHY:/.test(b)) || /\*\*Verdict threshold\*\*:|\*\*Success criterion\*\*:/.test(b),
  ).length / blocks.length;
  const hasStatus = blocks.filter(b => /PENDING|DONE/.test(b)).length / blocks.length;
  const hasHypothesis = blocks.filter(b => /\*\*Hypothesis\*\*:|Hypothesis:/.test(b)).length / blocks.length;

  const weights = { domains_covered: 0.35, has_thresholds: 0.30, has_status: 0.15, has_hypothesis: 0.20 };
  const passRates = { domains_covered: domainsScore, has_thresholds: hasThresholds, has_status: hasStatus, has_hypothesis: hasHypothesis };
  const score = Object.keys(weights).reduce((s, k) => s + passRates[k] * weights[k], 0);

  return { agent: 'question-designer', score: Math.round(score * 10000) / 10000, checks: passRates, details: `Scored ${blocks.length} Wave 1 questions` };
}

// BL 2.0 operational agent scorers

function scoreDiagnoseAnalyst(projectDir) {
  const findingsDir = path.join(projectDir, 'findings');
  const resultsTsv = path.join(projectDir, 'results.tsv');
  if (!fs.existsSync(findingsDir)) {
    return { agent: 'diagnose-analyst', score: 0.0, checks: {}, details: 'findings/ not found' };
  }

  let dcRate = 0.0;
  if (fs.existsSync(resultsTsv)) {
    const lines = fs.readFileSync(resultsTsv, 'utf8').split('\n');
    const diagRows = lines.filter(ln => {
      const parts = ln.split('\t');
      return parts.length >= 3 && parts[0] === 'N/A' && parts[1].startsWith('D') &&
        /^(DIAGNOSIS_COMPLETE|HEALTHY|FAILURE|INCONCLUSIVE)$/.test(parts[2]);
    });
    const dcRows = diagRows.filter(ln => /\tDIAGNOSIS_COMPLETE\t|\tHEALTHY\t/.test(ln));
    dcRate = diagRows.length ? dcRows.length / diagRows.length : 0.0;
  }

  const specFields = ['Target file', 'Target location', 'Concrete edit', 'Verification command'];
  const specScores = [];
  for (const file of fs.readdirSync(findingsDir).filter(f => f.endsWith('.md') && f !== 'synthesis.md').sort()) {
    const content = fs.readFileSync(path.join(findingsDir, file), 'utf8');
    const firstLines = content.split('\n').slice(0, 6);
    if (!firstLines.some(l => l.trim() === '**Verdict**: DIAGNOSIS_COMPLETE')) continue;
    specScores.push(specFields.filter(f => content.includes(f)).length / specFields.length);
  }
  const specCompleteness = specScores.length ? specScores.reduce((s, v) => s + v, 0) / specScores.length : 0.0;

  const [score, passRates] = _weighted({ dc_rate: [dcRate, 0.60], fix_spec_completeness: [specCompleteness, 0.40] });
  return { agent: 'diagnose-analyst', score: Math.round(score * 10000) / 10000, checks: passRates, details: `dc_rate=${dcRate.toFixed(2)}, spec=${specCompleteness.toFixed(2)}` };
}

function scoreFixImplementer(projectDir) {
  const findingsDir = path.join(projectDir, 'findings');
  const resultsTsv = path.join(projectDir, 'results.tsv');
  if (!fs.existsSync(findingsDir)) {
    return { agent: 'fix-implementer', score: 0.0, checks: {}, details: 'findings/ not found' };
  }

  let fixedRate = 0.0;
  let fixFailedRate = 0.0;
  if (fs.existsSync(resultsTsv)) {
    const lines = fs.readFileSync(resultsTsv, 'utf8').split('\n');
    const fixRows = lines.filter(ln => {
      const parts = ln.split('\t');
      if (parts.length >= 3 && parts[0] === 'N/A') {
        return parts[1].startsWith('F') && /^(FIXED|FIX_FAILED)$/.test(parts[2]);
      }
      return /\t(FIXED|FIX_FAILED)\t/.test(ln);
    });
    if (fixRows.length) {
      fixedRate = fixRows.filter(ln => ln.includes('\tFIXED\t')).length / fixRows.length;
      fixFailedRate = 1.0 - fixedRate;
    }
  }

  const verifyScores = [];
  for (const file of fs.readdirSync(findingsDir).filter(f => f.endsWith('.md') && f !== 'synthesis.md').sort()) {
    const content = fs.readFileSync(path.join(findingsDir, file), 'utf8');
    const firstLines = content.split('\n').slice(0, 6);
    if (!firstLines.some(l => l.trim() === '**Verdict**: FIXED')) continue;
    verifyScores.push(/## (Verification|Fix Applied|Evidence)/.test(content) ? 1.0 : 0.0);
  }
  const verifyRate = verifyScores.length ? verifyScores.reduce((s, v) => s + v, 0) / verifyScores.length : 0.0;
  const reliability = Math.max(0.0, 1.0 - fixFailedRate * 2);

  const [score, passRates] = _weighted({
    fixed_rate: [fixedRate, 0.45], verify_section_rate: [verifyRate, 0.35], reliability: [reliability, 0.20],
  });
  return { agent: 'fix-implementer', score: Math.round(score * 10000) / 10000, checks: passRates, details: `fixed=${fixedRate.toFixed(2)}` };
}

function scoreComplianceAuditor(projectDir) {
  const findingsDir = path.join(projectDir, 'findings');
  const resultsTsv = path.join(projectDir, 'results.tsv');
  if (!fs.existsSync(findingsDir)) {
    return { agent: 'compliance-auditor', score: 0.0, checks: {}, details: 'findings/ not found' };
  }

  let definitiveRate = 0.0;
  if (fs.existsSync(resultsTsv)) {
    const lines = fs.readFileSync(resultsTsv, 'utf8').split('\n');
    const auditRows = lines.filter(ln => /\t(COMPLIANT|NON_COMPLIANT|PARTIAL|INCONCLUSIVE)\t/.test(ln));
    if (auditRows.length) {
      definitiveRate = auditRows.filter(ln => /\t(COMPLIANT|NON_COMPLIANT|PARTIAL)\t/.test(ln)).length / auditRows.length;
    }
  }

  const fixSpecScores = [];
  for (const file of fs.readdirSync(findingsDir).filter(f => f.endsWith('.md') && f !== 'synthesis.md').sort()) {
    const content = fs.readFileSync(path.join(findingsDir, file), 'utf8');
    const firstLines = content.split('\n').slice(0, 6);
    if (!firstLines.some(l => l.trim() === '**Verdict**: NON_COMPLIANT')) continue;
    fixSpecScores.push(content.includes('Fix Specification') || content.includes('Concrete edit') ? 1.0 : 0.0);
  }
  const fixSpecRate = fixSpecScores.length ? fixSpecScores.reduce((s, v) => s + v, 0) / fixSpecScores.length : 0.0;

  const [score, passRates] = _weighted({ definitive_verdict_rate: [definitiveRate, 0.60], non_compliant_has_fix_spec: [fixSpecRate, 0.40] });
  return { agent: 'compliance-auditor', score: Math.round(score * 10000) / 10000, checks: passRates, details: `definitive=${definitiveRate.toFixed(2)}` };
}

function scoreDesignReviewer(projectDir) {
  const findingsDir = path.join(projectDir, 'findings');
  const resultsTsv = path.join(projectDir, 'results.tsv');
  if (!fs.existsSync(findingsDir)) {
    return { agent: 'design-reviewer', score: 0.0, checks: {}, details: 'findings/ not found' };
  }

  let compliantRate = 0.0;
  if (fs.existsSync(resultsTsv)) {
    const lines = fs.readFileSync(resultsTsv, 'utf8').split('\n');
    const reviewRows = lines.filter(ln => /\t(COMPLIANT|NON_COMPLIANT|PARTIAL)\t/.test(ln));
    if (reviewRows.length) {
      compliantRate = reviewRows.filter(ln => ln.includes('\tCOMPLIANT\t')).length / reviewRows.length;
    }
  }

  const linenoScores = [];
  for (const file of fs.readdirSync(findingsDir).filter(f => f.endsWith('.md') && f !== 'synthesis.md').sort()) {
    const content = fs.readFileSync(path.join(findingsDir, file), 'utf8');
    const firstLines = content.split('\n').slice(0, 6);
    const validVerdicts = ['**Verdict**: COMPLIANT', '**Verdict**: NON_COMPLIANT', '**Verdict**: PARTIAL'];
    if (!firstLines.some(l => validVerdicts.includes(l.trim()))) continue;
    linenoScores.push(/line[s]?\s+\d+|:\d+[-–]\d+|lines?\s+\d+[-–]\d+/.test(content) ? 1.0 : 0.0);
  }
  const linenoRate = linenoScores.length ? linenoScores.reduce((s, v) => s + v, 0) / linenoScores.length : 0.0;

  const [score, passRates] = _weighted({ compliant_rate: [compliantRate, 0.55], lineno_reference_rate: [linenoRate, 0.45] });
  return { agent: 'design-reviewer', score: Math.round(score * 10000) / 10000, checks: passRates, details: `compliant=${compliantRate.toFixed(2)}` };
}

// ---------------------------------------------------------------------------
// Main API
// ---------------------------------------------------------------------------

const SCORERS = {
  'hypothesis-generator': scoreHypothesisGenerator,
  'question-designer': scoreQuestionDesigner,
  'synthesizer': scoreSynthesizer,
  'quantitative-analyst': scoreQuantitativeAnalyst,
  'diagnose-analyst': scoreDiagnoseAnalyst,
  'fix-implementer': scoreFixImplementer,
  'compliance-auditor': scoreComplianceAuditor,
  'design-reviewer': scoreDesignReviewer,
};

function runAllBenchmarks(projectDir) {
  const scores = [];
  for (const [agent, scorer] of Object.entries(SCORERS)) {
    let score;
    try {
      score = scorer(projectDir);
    } catch (err) {
      score = { agent, score: 0.0, checks: {}, details: `Scorer raised: ${err.message}` };
    }
    recordScore(projectDir, score);
    scores.push(score);
  }
  return scores;
}

function getAllStatuses(projectDir) {
  return KNOWN_AGENTS.map(agent => getAgentStatus(projectDir, agent));
}

module.exports = {
  recordScore,
  getAgentStatus,
  runAllBenchmarks,
  getAllStatuses,
  _weighted,
  scoreHypothesisGenerator,
  scoreQuestionDesigner,
  scoreSynthesizer,
  scoreQuantitativeAnalyst,
  scoreDiagnoseAnalyst,
  scoreFixImplementer,
  scoreComplianceAuditor,
  scoreDesignReviewer,
  PROMOTE_THRESHOLD,
  FLAG_THRESHOLD,
  RETIRE_THRESHOLD,
  KNOWN_AGENTS,
};

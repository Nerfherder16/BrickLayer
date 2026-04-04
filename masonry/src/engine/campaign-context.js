'use strict';
// engine/campaign-context.js — Generate campaign-context.md for agent warm-start.
//
// Port of bl/campaign_context.py to Node.js. Writes a compact context file
// that specialist agents read before processing questions.

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Severity ordering (highest first)
// ---------------------------------------------------------------------------

const SEVERITY_RANK = {
  critical: 0, high: 1, medium: 2, info: 3, low: 4,
};

const VERDICT_SEVERITY = {
  FAILURE: 'high', NON_COMPLIANT: 'high', REGRESSION: 'high',
  ALERT: 'high', FIX_FAILED: 'high', IMMINENT: 'critical',
  PROBABLE: 'high', WARNING: 'medium', DEGRADED: 'medium',
  DEGRADED_TRENDING: 'medium', PARTIAL: 'medium', POSSIBLE: 'medium',
  UNCALIBRATED: 'medium', BLOCKED: 'medium',
};

function _severityRank(verdict, severityStr) {
  if (severityStr) {
    const key = severityStr.toLowerCase();
    if (key in SEVERITY_RANK) return SEVERITY_RANK[key];
  }
  const mapped = VERDICT_SEVERITY[verdict] || 'low';
  return SEVERITY_RANK[mapped] ?? 4;
}

// ---------------------------------------------------------------------------
// Finding parser
// ---------------------------------------------------------------------------

function _parseFinding(qid, text) {
  const verdictM = text.match(/\*\*Verdict\*\*:\s*(\w+)/);
  const severityM = text.match(/\*\*Severity\*\*:\s*(\w+)/);
  const summaryM = text.match(/## Summary\s*\n(.*)/);

  const verdict = verdictM ? verdictM[1] : 'UNKNOWN';
  const severity = severityM ? severityM[1] : '';
  const summary = summaryM
    ? summaryM[1].trim().slice(0, 120)
    : text.slice(0, 80).replace(/\n/g, ' ').trim();

  return {
    id: qid,
    verdict,
    severity,
    summary,
    rank: _severityRank(verdict, severity),
  };
}

function _parseFindingFile(filePath) {
  try {
    const text = fs.readFileSync(filePath, 'utf8');
    const qid = path.basename(filePath, '.md');
    return _parseFinding(qid, text);
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Top findings
// ---------------------------------------------------------------------------

function _topFindings(findingsDir, n = 5) {
  if (!fs.existsSync(findingsDir)) return [];

  const files = fs.readdirSync(findingsDir)
    .filter(f => f.endsWith('.md') && f !== 'synthesis.md');

  const parsed = [];
  for (const file of files) {
    const f = _parseFindingFile(path.join(findingsDir, file));
    if (f) parsed.push(f);
  }

  parsed.sort((a, b) => a.rank - b.rank);
  return parsed.slice(0, n);
}

// ---------------------------------------------------------------------------
// Project summary
// ---------------------------------------------------------------------------

function _projectSummary(projectRoot) {
  const briefPath = path.join(projectRoot, 'project-brief.md');
  if (!fs.existsSync(briefPath)) return 'No project brief found.';

  const text = fs.readFileSync(briefPath, 'utf8');
  const lines = text.split('\n');
  const paraLines = [];
  let inPara = false;

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith('#')) {
      if (inPara) break;
      continue;
    }
    if (stripped) {
      inPara = true;
      paraLines.push(stripped);
    } else if (inPara) {
      break;
    }
  }

  return paraLines.length ? paraLines.join(' ').slice(0, 400) : 'No project brief found.';
}

// ---------------------------------------------------------------------------
// Open hypotheses
// ---------------------------------------------------------------------------

function _openHypotheses(projectRoot, minWeight = 1.5) {
  const weightsPath = path.join(projectRoot, '.bl-weights.json');
  if (!fs.existsSync(weightsPath)) return [];

  let data;
  try {
    data = JSON.parse(fs.readFileSync(weightsPath, 'utf8'));
  } catch (_) {
    return [];
  }

  const high = [];
  for (const [qid, info] of Object.entries(data)) {
    let w, status;
    if (typeof info === 'object' && info !== null) {
      w = parseFloat(info.weight || 1.0);
      status = info.status || 'PENDING';
    } else {
      w = parseFloat(info);
      status = 'PENDING';
    }
    if (status === 'PENDING' && w >= minWeight) {
      high.push({ weight: w, qid });
    }
  }

  high.sort((a, b) => b.weight - a.weight);
  return high.slice(0, 10).map(h => h.qid);
}

// ---------------------------------------------------------------------------
// Wave detection
// ---------------------------------------------------------------------------

function _detectWave(projectRoot) {
  const tsvPath = path.join(projectRoot, 'results.tsv');
  if (!fs.existsSync(tsvPath)) return 1;
  try {
    const lines = fs.readFileSync(tsvPath, 'utf8').split('\n').filter(Boolean);
    const count = Math.max(0, lines.length - 1); // subtract header
    return Math.max(1, Math.floor(count / 10) + 1);
  } catch (_) {
    return 1;
  }
}

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------

/**
 * Build campaign-context.md and write it to projectRoot.
 * Returns the path written.
 */
function generate(projectRoot, wave) {
  projectRoot = path.resolve(projectRoot);
  wave = wave || _detectWave(projectRoot);
  const projectName = path.basename(projectRoot);

  const summary = _projectSummary(projectRoot);
  const findings = _topFindings(path.join(projectRoot, 'findings'));
  const hypotheses = _openHypotheses(projectRoot);

  let findingsSection;
  if (findings.length) {
    findingsSection = findings
      .map(f => `- **${f.id}** [${f.verdict}]: ${f.summary}`)
      .join('\n');
  } else {
    findingsSection = '_No findings yet._';
  }

  let hypSection;
  if (hypotheses.length) {
    hypSection = hypotheses.join(', ');
  } else {
    hypSection = '_None above weight threshold (run more questions to generate weights)._';
  }

  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  const content = `# Campaign Context — ${projectName} (Wave ${wave})

_Generated: ${timestamp} — Read this before processing any question._

## Project

${summary}

## Top Findings

${findingsSection}

## Open Hypotheses

High-weight PENDING questions (priority targets):
${hypSection}
`;

  const outPath = path.join(projectRoot, 'campaign-context.md');
  fs.writeFileSync(outPath, content, 'utf8');
  return outPath;
}

module.exports = {
  generate,
  _parseFinding,
  _severityRank,
  _topFindings,
  _projectSummary,
  _openHypotheses,
  _detectWave,
};

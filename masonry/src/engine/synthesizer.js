'use strict';
// engine/synthesizer.js — Campaign synthesizer.
//
// Port of bl/synthesizer.py to Node.js. Reads findings + results.tsv after
// each wave and calls Claude CLI to produce synthesis.md.

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const MAX_CORPUS_CHARS = 12000;

const HIGH_SEVERITY = new Set([
  'FAILURE', 'NON_COMPLIANT', 'WARNING', 'REGRESSION',
  'ALERT', 'DIAGNOSIS_COMPLETE', 'FIX_FAILED',
]);

// ---------------------------------------------------------------------------
// Corpus builder
// ---------------------------------------------------------------------------

function _buildFindingsCorpus(findingsDir, resultsTsv) {
  let tsvSection = '';
  if (fs.existsSync(resultsTsv)) {
    const tsvContent = fs.readFileSync(resultsTsv, 'utf8').trim();
    if (tsvContent) tsvSection = `## Results Summary\n\n${tsvContent}\n`;
  }

  let findingSections = [];
  if (fs.existsSync(findingsDir)) {
    const files = fs.readdirSync(findingsDir).filter(f => f.endsWith('.md')).sort();
    for (const file of files) {
      const content = fs.readFileSync(path.join(findingsDir, file), 'utf8').trim();
      if (content) {
        findingSections.push(`### ${path.basename(file, '.md')}\n\n${content}\n`);
      }
    }
  }

  const tsvChars = tsvSection.length;
  const budget = MAX_CORPUS_CHARS - tsvChars;

  // Severity-aware truncation: high-severity first, drop low-severity tail
  findingSections.sort((a, b) => _findingPriority(a) - _findingPriority(b));
  while (findingSections.length && budget < findingSections.reduce((s, f) => s + f.length, 0)) {
    findingSections.pop();
  }

  const parts = [];
  if (tsvSection) parts.push(tsvSection);
  if (findingSections.length) parts.push('## Findings\n\n' + findingSections.join('\n'));

  return parts.length ? parts.join('\n') : 'No findings or results available yet.';
}

function _findingPriority(section) {
  for (const verdict of HIGH_SEVERITY) {
    if (section.includes(`**Verdict**: ${verdict}`) || section.includes(`: ${verdict}`)) {
      return 0;
    }
  }
  return 1;
}

// ---------------------------------------------------------------------------
// Doctrine
// ---------------------------------------------------------------------------

function _readDoctrine(projectDir) {
  const doctrinePath = path.join(projectDir, 'doctrine.md');
  if (!fs.existsSync(doctrinePath)) return '';
  return fs.readFileSync(doctrinePath, 'utf8').trim();
}

// ---------------------------------------------------------------------------
// Claude CLI
// ---------------------------------------------------------------------------

function _callClaude(prompt) {
  const claudeBin = _findClaude();
  try {
    const result = execFileSync(claudeBin, ['-p', prompt, '--output-format', 'text'], {
      encoding: 'utf8',
      timeout: 120000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return result.trim() || null;
  } catch (err) {
    if (err.code === 'ENOENT') {
      process.stderr.write('[synthesizer] claude CLI not found\n');
    } else if (err.killed) {
      process.stderr.write('[synthesizer] Claude timed out after 120s\n');
    } else {
      process.stderr.write(`[synthesizer] Claude error: ${err.message}\n`);
    }
    return null;
  }
}

function _findClaude() {
  // Check common locations
  const { execSync } = require('child_process');
  try {
    return execSync('which claude', { encoding: 'utf8' }).trim();
  } catch (_) {
    return 'claude';
  }
}

// ---------------------------------------------------------------------------
// Recommendation parser
// ---------------------------------------------------------------------------

function parseRecommendation(synthesisText) {
  const lines = synthesisText.split('\n');

  let sectionStart = null;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].toLowerCase().includes('recommended next action')) {
      sectionStart = i + 1;
      break;
    }
  }

  const scanLines = sectionStart !== null ? lines.slice(sectionStart) : lines;

  for (const line of scanLines) {
    const upper = line.toUpperCase();
    if (upper.includes('STOP')) return 'STOP';
    if (upper.includes('PIVOT')) return 'PIVOT';
    if (upper.includes('CONTINUE')) return 'CONTINUE';
  }
  return 'CONTINUE';
}

// ---------------------------------------------------------------------------
// Retrospective
// ---------------------------------------------------------------------------

function _runRetrospective(projectDir) {
  const agentFile = path.join(projectDir, '.claude', 'agents', 'retrospective.md');
  if (!fs.existsSync(agentFile)) return;

  const questionsMd = path.join(projectDir, 'questions.md');
  let doneCount = 0;
  let totalCount = 0;
  if (fs.existsSync(questionsMd)) {
    const text = fs.readFileSync(questionsMd, 'utf8');
    totalCount = (text.match(/\*\*Status\*\*:/g) || []).length;
    doneCount = (text.match(/\*\*Status\*\*: DONE/g) || []).length;
  }

  let projectName = path.basename(projectDir);
  const briefPath = path.join(projectDir, 'project-brief.md');
  if (fs.existsSync(briefPath)) {
    const firstLine = fs.readFileSync(briefPath, 'utf8').split('\n')[0].replace(/^#\s*/, '').trim();
    if (firstLine) projectName = firstLine;
  }

  const prompt = `Act as the retrospective agent defined in ${agentFile}. ` +
    `Project: ${projectName}. Project directory: ${projectDir}. ` +
    `Campaign stats: ${totalCount} questions total, ${doneCount} DONE. ` +
    'Complete all three parts: (1) process scoring, (2) content integrity analysis, (3) LLM self-report. ' +
    'Write retrospective.md to the project root.';

  const claudeBin = _findClaude();
  try {
    execFileSync(claudeBin, ['-p', prompt, '--output-format', 'text'], {
      encoding: 'utf8',
      timeout: 300000,
      cwd: projectDir,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    process.stderr.write('[synthesizer] Retrospective complete.\n');
  } catch (err) {
    process.stderr.write(`[synthesizer] Retrospective skipped: ${err.message}\n`);
  }
}

// ---------------------------------------------------------------------------
// Main API
// ---------------------------------------------------------------------------

function synthesize(projectDir, wave, dryRun = false) {
  projectDir = path.resolve(projectDir);
  const findingsDir = path.join(projectDir, 'findings');
  const resultsTsv = path.join(projectDir, 'results.tsv');

  const corpus = _buildFindingsCorpus(findingsDir, resultsTsv);
  const doctrine = _readDoctrine(projectDir);

  const waveLabel = wave != null ? wave : '?';

  const doctrineSection = doctrine ? `## Project Doctrine\n\n${doctrine}\n\n` : '';

  const prompt = `You are a research campaign director reviewing findings from a BrickLayer autonomous research campaign.

Your job: synthesize the accumulated evidence and produce a structured campaign status report.

${doctrineSection}CAMPAIGN FINDINGS:
${corpus}

Produce a synthesis report in this EXACT format:

# Campaign Synthesis — Wave ${waveLabel}

## Core Hypothesis Verdict
[CONFIRMED | UNCONFIRMED | PARTIALLY CONFIRMED | REFUTED] — one paragraph explaining why.

## Validated Bets
List each thing the campaign has confirmed with evidence.

## Dead Ends
List paths that have been exhausted.

## Unvalidated Bets
List key questions or assumptions not yet tested.

## Recommended Next Action
State exactly one of: CONTINUE, STOP, or PIVOT
Then one paragraph of specific reasoning.`;

  const output = _callClaude(prompt);
  if (!output) {
    process.stderr.write('[synthesizer] Claude call failed — no synthesis written\n');
    return null;
  }

  const recommendation = parseRecommendation(output);
  process.stderr.write(`[synthesizer] Recommendation: ${recommendation}\n`);

  if (dryRun) {
    process.stdout.write(output + '\n');
    return null;
  }

  const synthesisPath = path.join(projectDir, 'synthesis.md');
  fs.writeFileSync(synthesisPath, output, 'utf8');

  _runRetrospective(projectDir);

  return synthesisPath;
}

module.exports = {
  synthesize,
  parseRecommendation,
  _buildFindingsCorpus,
  _readDoctrine,
};

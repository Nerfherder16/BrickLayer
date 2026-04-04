'use strict';
// engine/git-hypothesis.js — Automatic hypothesis generation from git diffs.
//
// Port of bl/git_hypothesis.py to Node.js. Analyzes recent commits and
// produces research questions targeting changed code paths.

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Pattern registry
// ---------------------------------------------------------------------------

const DIFF_PATTERNS = [
  { name: 'concurrency', pattern: /concurrent|asyncio|threading|lock|mutex|race/i, domain: 'D4', mode: 'diagnose',
    template: 'Does {file} handle concurrent access safely? What happens under {pattern} conditions at high load?', priority: 'high' },
  { name: 'fee_calculation', pattern: /def.*fee|fee.*calc|rate.*calc|calc.*rate|commission|royalt/i, domain: 'D1', mode: 'quantitative',
    template: 'What are the boundary conditions for the fee calculation in {file}? Sweep parameters to find where the formula produces unexpected results.', priority: 'high' },
  { name: 'schema_migration', pattern: /migration|ALTER TABLE|schema.*change|add.*column|drop.*column/i, domain: 'D2', mode: 'validate',
    template: 'Does the schema change in {file} maintain backward compatibility? What happens to existing data during migration?', priority: 'high' },
  { name: 'auth_access_control', pattern: /auth|permission|role|access.*control|require.*login|jwt|token/i, domain: 'D3', mode: 'audit',
    template: 'Does the auth change in {file} maintain proper access control? What happens if {pattern} is bypassed or malformed?', priority: 'high' },
  { name: 'cache', pattern: /cache|redis|memcache|ttl|expire|invalidat/i, domain: 'D4', mode: 'diagnose',
    template: 'What happens when the cache in {file} is cold, stale, or evicted under load? Does the system degrade gracefully?', priority: 'medium' },
  { name: 'resilience', pattern: /retry|backoff|timeout|circuit.*break|fallback/i, domain: 'D4', mode: 'diagnose',
    template: 'Does the retry/resilience logic in {file} work correctly under sustained failure? What is the failure cascade if {pattern} fails permanently?', priority: 'medium' },
  { name: 'dependency', pattern: /import|require|dependency|package|version/i, domain: 'D5', mode: 'research',
    template: 'Does the new dependency in {file} introduce any known vulnerabilities or breaking changes in recent versions?', priority: 'low' },
];

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };

// ---------------------------------------------------------------------------
// Git diff retrieval
// ---------------------------------------------------------------------------

function getRecentDiff(repoPath, commits = 3) {
  try {
    return execFileSync('git', ['diff', `HEAD~${commits}..HEAD`], {
      cwd: repoPath, encoding: 'utf8', timeout: 10000, stdio: ['pipe', 'pipe', 'pipe'],
    });
  } catch (_) {
    if (commits > 1) return getRecentDiff(repoPath, 1);
    return '';
  }
}

function _getHeadSha(repoPath) {
  try {
    return execFileSync('git', ['rev-parse', '--short', 'HEAD'], {
      cwd: repoPath, encoding: 'utf8', timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch (_) {
    return 'unknown';
  }
}

// ---------------------------------------------------------------------------
// Diff parser
// ---------------------------------------------------------------------------

function parseDiffFiles(diffText) {
  if (!diffText) return [];

  const files = [];
  let current = null;

  for (const line of diffText.split('\n')) {
    if (line.startsWith('diff --git ')) {
      const m = line.match(/ b\/(.+)$/);
      current = { file: m ? m[1] : line, added_lines: [], removed_lines: [], is_new_file: false };
      files.push(current);
    } else if (line.startsWith('new file mode') && current) {
      current.is_new_file = true;
    } else if (line.startsWith('+') && !line.startsWith('+++') && current) {
      current.added_lines.push(line.slice(1));
    } else if (line.startsWith('-') && !line.startsWith('---') && current) {
      current.removed_lines.push(line.slice(1));
    }
  }

  return files;
}

// ---------------------------------------------------------------------------
// Pattern matching
// ---------------------------------------------------------------------------

function matchPatterns(diffFiles) {
  const seen = new Set();
  const matches = [];

  for (const fileInfo of diffFiles) {
    const addedText = fileInfo.added_lines.join('\n');

    for (const pat of DIFF_PATTERNS) {
      const key = `${fileInfo.file}::${pat.name}`;
      if (seen.has(key)) continue;

      const m = pat.pattern.exec(addedText);
      if (m) {
        seen.add(key);
        matches.push({
          file: fileInfo.file,
          pattern_name: pat.name,
          template: pat.template,
          domain: pat.domain,
          mode: pat.mode,
          priority: pat.priority,
          matched_text: m[0],
        });
      }
    }
  }

  return matches;
}

// ---------------------------------------------------------------------------
// Question generation
// ---------------------------------------------------------------------------

function generateQuestions(repoPath, commits = 3, maxQuestions = 5) {
  const diffText = getRecentDiff(repoPath, commits);
  if (!diffText) return [];

  const diffFiles = parseDiffFiles(diffText);
  if (!diffFiles.length) return [];

  const patternMatches = matchPatterns(diffFiles);
  if (!patternMatches.length) return [];

  patternMatches.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99));

  const sha = _getHeadSha(repoPath);
  const questions = [];

  for (let n = 0; n < Math.min(patternMatches.length, maxQuestions); n++) {
    const match = patternMatches[n];
    const questionText = match.template
      .replace('{file}', match.file)
      .replace('{pattern}', match.matched_text);

    const basename = path.basename(match.file);
    const title = `${match.pattern_name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} risk in ${basename}`;

    questions.push({
      id: `GH-${sha}-${n + 1}`,
      title,
      mode: match.mode,
      domain: match.domain,
      status: 'PENDING',
      priority: match.priority,
      source: 'git_hypothesis',
      commit_sha: sha,
      question: questionText,
    });
  }

  return questions;
}

// ---------------------------------------------------------------------------
// Append to questions.md
// ---------------------------------------------------------------------------

function _getNextQNumber(questionsMdText) {
  const sectionNums = [...questionsMdText.matchAll(/^###\s+Q(\d+)\s+/gm)].map(m => parseInt(m[1]));
  const ghNums = [...questionsMdText.matchAll(/^##\s+GH-\S+-(\d+)\s/gm)].map(m => parseInt(m[1]));
  const all = [...sectionNums, ...ghNums];
  return all.length ? Math.max(...all) + 1 : 1;
}

function appendToQuestionsMd(projectDir, questions, waveLabel = 'Auto (git)') {
  if (!questions.length) return 0;

  const questionsPath = path.join(projectDir, 'questions.md');
  if (!fs.existsSync(questionsPath)) {
    process.stderr.write(`[git_hypothesis] questions.md not found at ${questionsPath}\n`);
    return 0;
  }

  const existingText = fs.readFileSync(questionsPath, 'utf8');
  const nextQ = _getNextQNumber(existingText);

  const lines = [
    '', '---', '',
    `## ${waveLabel}`, '',
    `**Source**: git diff — ${questions[0].commit_sha}`,
    `**Generated**: ${questions.length} question(s) from changed code patterns`,
    '',
  ];

  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    const qNum = nextQ + i;
    lines.push(`### Q${qNum} — ${q.title}`, '',
      `**Status**: ${q.status}`,
      `**Operational Mode**: ${q.mode}`,
      `**Priority**: ${q.priority.toUpperCase()}`,
      `**Domain**: ${q.domain}`,
      `**Source**: ${q.source} (${q.commit_sha})`,
      `**Question**: ${q.question}`,
      '', '---', '',
    );
  }

  fs.appendFileSync(questionsPath, lines.join('\n'), 'utf8');
  return questions.length;
}

// ---------------------------------------------------------------------------
// Convenience entry point
// ---------------------------------------------------------------------------

function run(projectDir = '.', commits = 3, maxQuestions = 5, dryRun = false, waveLabel = 'Auto (git)') {
  const questions = generateQuestions(projectDir, commits, maxQuestions);

  if (!questions.length) {
    process.stderr.write('[git_hypothesis] No matching patterns found in recent diff.\n');
    return [];
  }

  if (dryRun) return questions;

  const appended = appendToQuestionsMd(projectDir, questions, waveLabel);
  process.stderr.write(`[git_hypothesis] Appended ${appended} question(s) to questions.md\n`);
  return questions;
}

module.exports = {
  getRecentDiff,
  parseDiffFiles,
  matchPatterns,
  generateQuestions,
  appendToQuestionsMd,
  run,
  DIFF_PATTERNS,
};

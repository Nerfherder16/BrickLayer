#!/usr/bin/env node
/**
 * status.js
 * Read campaign state from disk and output a JSON status object.
 *
 * Usage:
 *   node masonry/src/engine/cli/status.js --project-dir <path>
 *
 * stdout: {"state":"<mode>","questions":{"total":N,"answered":N,"pending":N},"wave":N,"findings":N}
 * exit 0: always (missing project is NOT an error)
 * exit 1: only on unexpected crash or missing --project-dir
 */

import fs from 'node:fs';
import path from 'node:path';

const NO_PROJECT = {
  state: 'no_project',
  questions: { total: 0, answered: 0, pending: 0 },
  wave: 0,
  findings: 0,
};

function parseArgs(argv) {
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--project-dir' && argv[i + 1]) {
      return argv[i + 1];
    }
  }
  return null;
}

/**
 * Parse questions.md content and return { total, answered, wave }.
 *
 * Supports two formats:
 *   1. Table rows:  | Q1.1 | ... | DONE | ...  or  | E3.2 | ... | DONE | ...
 *   2. Checkbox:    - [x] answered   - [ ] pending
 *
 * Wave detection (highest wins):
 *   - "Wave N" section headers
 *   - Question IDs like E3.2 → wave 3, Q2.1 → wave 2
 *   - Domain IDs like Q1.1 → wave 1 (domain 1, treated as wave 1 baseline)
 */
function parseQuestions(content) {
  let total = 0;
  let answered = 0;
  let maxWave = 0;

  const lines = content.split('\n');

  for (const line of lines) {
    // Wave N header (e.g. "## Wave 3 — Evolve" or "Wave 2")
    const waveHeaderMatch = line.match(/\bwave\s+(\d+)\b/i);
    if (waveHeaderMatch) {
      const w = parseInt(waveHeaderMatch[1], 10);
      if (w > maxWave) maxWave = w;
    }

    // Table row with Status column: | ID | ... | STATUS | ... |
    // Match lines that have at least 3 pipe-separated cells
    const tableMatch = line.match(/^\s*\|\s*(\S+)\s*\|.*\|\s*(DONE|PENDING|IN_PROGRESS|INCONCLUSIVE)\s*\|/i);
    if (tableMatch) {
      total++;
      const status = tableMatch[2].toUpperCase();
      if (status === 'DONE') answered++;

      // Extract wave from question ID
      const id = tableMatch[1];
      // E3.2 → wave 3, Q2.1 → wave 2
      const waveFromId = id.match(/^[A-Za-z]+(\d+)\.\d+$/);
      if (waveFromId) {
        const w = parseInt(waveFromId[1], 10);
        if (w > maxWave) maxWave = w;
      }
      continue;
    }

    // Also handle table rows where Status is in a different column position
    // Some tables: | ID | Mode | Status | Question | — status in col 3
    const tableMatch2 = line.match(/^\s*\|\s*(\S+)\s*\|[^|]*\|\s*(DONE|PENDING|IN_PROGRESS|INCONCLUSIVE)\s*\|/i);
    if (tableMatch2 && !tableMatch) {
      total++;
      const status = tableMatch2[2].toUpperCase();
      if (status === 'DONE') answered++;

      const id = tableMatch2[1];
      const waveFromId = id.match(/^[A-Za-z]+(\d+)\.\d+$/);
      if (waveFromId) {
        const w = parseInt(waveFromId[1], 10);
        if (w > maxWave) maxWave = w;
      }
      continue;
    }

    // Checkbox format: - [x] or - [ ]
    if (/^\s*-\s*\[x\]/i.test(line)) {
      total++;
      answered++;
    } else if (/^\s*-\s*\[ \]/.test(line)) {
      total++;
    }
  }

  return { total, answered, wave: maxWave };
}

/**
 * Count *.md files in a findings directory.
 * Returns 0 if directory doesn't exist.
 */
function countFindings(findingsDir) {
  if (!fs.existsSync(findingsDir)) return 0;
  try {
    const entries = fs.readdirSync(findingsDir, { withFileTypes: true });
    return entries.filter((e) => e.isFile() && e.name.endsWith('.md')).length;
  } catch {
    return 0;
  }
}

/**
 * Read the campaign state from .autopilot/mode.
 * Returns 'no_mode' if file missing or empty.
 */
function readState(projectDir) {
  const modePath = path.join(projectDir, '.autopilot', 'mode');
  try {
    const content = fs.readFileSync(modePath, 'utf8').trim();
    return content || 'no_mode';
  } catch {
    return 'no_mode';
  }
}

function main() {
  const projectDirRaw = parseArgs(process.argv.slice(2));

  if (!projectDirRaw) {
    process.stdout.write(JSON.stringify({ error: '--project-dir is required' }) + '\n');
    process.exit(1);
  }

  const projectDir = path.resolve(projectDirRaw);

  if (!fs.existsSync(projectDir)) {
    process.stdout.write(JSON.stringify(NO_PROJECT) + '\n');
    process.exit(0);
  }

  const questionsPath = path.join(projectDir, 'questions.md');
  if (!fs.existsSync(questionsPath)) {
    process.stdout.write(JSON.stringify(NO_PROJECT) + '\n');
    process.exit(0);
  }

  let questionsContent;
  try {
    questionsContent = fs.readFileSync(questionsPath, 'utf8');
  } catch (err) {
    process.stdout.write(JSON.stringify({ error: `failed to read questions.md: ${err.message}` }) + '\n');
    process.exit(1);
  }

  const { total, answered, wave } = parseQuestions(questionsContent);
  const findingsCount = countFindings(path.join(projectDir, 'findings'));
  const state = readState(projectDir);

  const output = {
    state,
    questions: {
      total,
      answered,
      pending: total - answered,
    },
    wave,
    findings: findingsCount,
  };

  process.stdout.write(JSON.stringify(output) + '\n');
  process.exit(0);
}

main();

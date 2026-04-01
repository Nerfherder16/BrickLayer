'use strict';
// engine/goal.js — Goal-directed campaign question generator (C-03).
//
// Port of bl/goal.py to Node.js. Reads goal.md, calls local Ollama or
// Claude CLI fallback to generate focused research questions, and
// appends them to questions.md.

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { cfg } = require('./config');

const DEFAULT_MAX_QUESTIONS = 6;
const MAX_CONTEXT_CHARS = 3000;

// ---------------------------------------------------------------------------
// goal.md parser
// ---------------------------------------------------------------------------

function _parseGoal(goalText) {
  const result = { goal: '', target: '', focus: [], max_questions: DEFAULT_MAX_QUESTIONS, context: '' };

  for (const line of goalText.split('\n')) {
    const clean = line.trim().replace(/\*\*/g, '');
    if (clean.startsWith('Goal:')) result.goal = clean.slice(5).trim();
    else if (clean.startsWith('Target:')) result.target = clean.slice(7).trim();
    else if (clean.startsWith('Focus:')) {
      result.focus = clean.slice(6).split(',').map(s => s.trim()).filter(Boolean);
    } else if (clean.startsWith('Max questions:')) {
      const n = parseInt(clean.slice(14).trim(), 10);
      if (!isNaN(n)) result.max_questions = n;
    } else if (clean.startsWith('Context:')) result.context = clean.slice(8).trim();
  }

  if (!result.goal) {
    throw new Error('goal.md is missing required **Goal**: field.');
  }

  return result;
}

// ---------------------------------------------------------------------------
// Simulation context
// ---------------------------------------------------------------------------

function _readSimParams(projectDir) {
  const parts = [];

  const constantsPath = path.join(projectDir, 'constants.py');
  if (fs.existsSync(constantsPath)) {
    parts.push('=== constants.py ===');
    parts.push(fs.readFileSync(constantsPath, 'utf8'));
  }

  const simulatePath = path.join(projectDir, 'simulate.py');
  if (fs.existsSync(simulatePath)) {
    const simText = fs.readFileSync(simulatePath, 'utf8');
    const scenarioIdx = simText.indexOf('# SCENARIO PARAMETERS');
    if (scenarioIdx !== -1) {
      parts.push('=== simulate.py SCENARIO PARAMETERS ===');
      parts.push(simText.slice(scenarioIdx, scenarioIdx + 80 * 60));
    } else {
      parts.push('=== simulate.py (first 60 lines) ===');
      parts.push(simText.split('\n').slice(0, 60).join('\n'));
    }
  }

  return parts.join('\n\n').slice(0, MAX_CONTEXT_CHARS);
}

// ---------------------------------------------------------------------------
// Output parser
// ---------------------------------------------------------------------------

function _getNextWaveIndex(questionsText) {
  const qgMatches = [...questionsText.matchAll(/## QG(\d+)\.\d+/g)].map(m => parseInt(m[1]));
  const bl2Matches = [...questionsText.matchAll(/## [DFAV](\d+)\.\d+/g)].map(m => parseInt(m[1]));
  const allWaves = [...qgMatches, ...bl2Matches];
  return allWaves.length ? Math.max(...allWaves) + 1 : 1;
}

function _parseGoalQuestions(raw) {
  const blocks = raw.split(/\n---\n|^---\n|\n---$/m);
  const valid = [];

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;
    if (!trimmed.includes('**Status**: PENDING')) continue;
    if (!trimmed.includes('## QG')) continue;
    valid.push(trimmed);
  }

  return valid;
}

// ---------------------------------------------------------------------------
// LLM calls
// ---------------------------------------------------------------------------

function _callOllama(prompt) {
  try {
    const resp = execFileSync('curl', [
      '-s', '-X', 'POST',
      `${cfg.localOllamaUrl}/api/generate`,
      '-H', 'Content-Type: application/json',
      '-d', JSON.stringify({
        model: cfg.localModel,
        prompt,
        stream: false,
        options: { temperature: 0.2, num_predict: 2048 },
      }),
    ], { encoding: 'utf8', timeout: 120000 });

    const data = JSON.parse(resp);
    return (data.response || '').trim() || null;
  } catch (_) {
    return null;
  }
}

function _callClaudeFallback(prompt) {
  try {
    const result = execFileSync('claude', [
      '-p', prompt, '--output-format', 'text',
      '--model', 'claude-haiku-4-5-20251001', '--no-mcp',
    ], { encoding: 'utf8', timeout: 120000, stdio: ['pipe', 'pipe', 'pipe'] });
    return result.trim() || null;
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

function generateGoalQuestions(goalMdPath, questionsMdPath, dryRun = false) {
  if (!fs.existsSync(goalMdPath)) {
    process.stderr.write(`[goal] goal.md not found at ${goalMdPath}\n`);
    return [];
  }

  const goalText = fs.readFileSync(goalMdPath, 'utf8');
  let goal;
  try {
    goal = _parseGoal(goalText);
  } catch (err) {
    process.stderr.write(`[goal] Parse error: ${err.message}\n`);
    return [];
  }

  process.stderr.write(`[goal] Goal: ${goal.goal.slice(0, 80)}\n`);
  const projectDir = path.dirname(goalMdPath);
  const simContext = _readSimParams(projectDir);

  // Read campaign plan if available
  let campaignPlan = '';
  const planPath = path.join(projectDir, 'CAMPAIGN_PLAN.md');
  if (fs.existsSync(planPath)) {
    const planText = fs.readFileSync(planPath, 'utf8');
    const briefMatch = planText.match(/## Targeting Brief.*?(?=\n## |\Z)/s);
    campaignPlan = briefMatch ? briefMatch[0].slice(0, 1500) : planText.slice(0, 1500);
  }

  const focusStr = goal.focus.length
    ? goal.focus.join(', ')
    : 'all operational modes (DIAGNOSE, FIX, AUDIT, VALIDATE)';
  const n = goal.max_questions;

  const prompt = `You are a research campaign director. Generate ${n} focused, falsifiable research questions targeting this goal:

RESEARCH GOAL: ${goal.goal}
TARGET SYSTEM: ${goal.target || 'See simulate.py'}
DOMAIN FOCUS: ${focusStr}
CONTEXT: ${goal.context || 'None'}

${campaignPlan ? `CAMPAIGN PLAN:\n${campaignPlan}\n` : ''}
SIMULATION CONTEXT:\n${simContext}

Output exactly ${n} question blocks in this format, separated by ---:

---
## QG1.1 [DIAGNOSE] Short title
**Operational Mode**: diagnose
**Mode**: agent
**Status**: PENDING
**Hypothesis**: One sentence.
**Test**: Exact test instruction.
**Verdict threshold**:
- FAILURE: condition
- WARNING: condition
- HEALTHY: condition
**Goal**: Which aspect this addresses.
---`;

  let raw = _callOllama(prompt);
  if (!raw) {
    process.stderr.write('[goal] Ollama unavailable, trying Claude fallback...\n');
    raw = _callClaudeFallback(prompt);
  }
  if (!raw) {
    process.stderr.write('[goal] No LLM output — aborting.\n');
    return [];
  }

  const blocks = _parseGoalQuestions(raw);
  if (!blocks.length) {
    process.stderr.write('[goal] Could not parse any valid question blocks.\n');
    return [];
  }

  const existingText = fs.existsSync(questionsMdPath) ? fs.readFileSync(questionsMdPath, 'utf8') : '';
  const waveIdx = _getNextWaveIndex(existingText);

  const renumbered = blocks.map((block, i) =>
    block.replace(/## QG\d+\.(\d+)/, `## QG${waveIdx}.${i + 1}`),
  );

  if (dryRun) {
    return renumbered.map((_, i) => `QG${waveIdx}.${i + 1}`);
  }

  const goalSummary = goal.goal.slice(0, 60);
  const header = `\n\n---\n\n## Goal Campaign — ${goalSummary}\n\n*Generated by BrickLayer goal-directed mode from goal.md.*\n\n---\n`;
  const content = header + renumbered.map(b => `\n${b}\n\n---\n`).join('');
  fs.appendFileSync(questionsMdPath, content, 'utf8');

  const generatedIds = renumbered.map((_, i) => `QG${waveIdx}.${i + 1}`);
  process.stderr.write(`[goal] Generated ${generatedIds.length} question(s): ${generatedIds.join(', ')}\n`);
  return generatedIds;
}

module.exports = {
  generateGoalQuestions,
  _parseGoal,
  _parseGoalQuestions,
  _getNextWaveIndex,
};

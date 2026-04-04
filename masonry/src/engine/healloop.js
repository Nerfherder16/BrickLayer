'use strict';
// engine/healloop.js — BrickLayer 2.0 self-healing loop.
//
// Port of bl/healloop.py to Node.js. Chains diagnose-analyst → fix-implementer
// automatically without human intervention. The runner function is injected
// so this module doesn't depend directly on the runner implementation.

const fs = require('fs');
const path = require('path');
const { cfg } = require('./config');
const { writeFinding, updateResultsTsv } = require('./findings');

// ---------------------------------------------------------------------------
// Config helpers
// ---------------------------------------------------------------------------

function isEnabled() {
  return process.env.BRICKLAYER_HEAL_LOOP === '1';
}

function maxCycles() {
  const val = parseInt(process.env.BRICKLAYER_HEAL_MAX_CYCLES, 10);
  return isNaN(val) ? 3 : val;
}

function _agentExists(agentName) {
  return fs.existsSync(path.join(cfg.agentsDir, `${agentName}.md`));
}

function _appendHealNote(findingPath, cycle, status, note) {
  const section = `\n## Heal Cycle ${cycle} — ${status}\n\n${note}\n`;
  try {
    fs.appendFileSync(findingPath, section, 'utf8');
  } catch (err) {
    process.stderr.write(`[heal-loop] Warning: could not append to ${findingPath}: ${err.message}\n`);
  }
}

// ---------------------------------------------------------------------------
// Synthetic question builder
// ---------------------------------------------------------------------------

function _syntheticQuestion(originalQuestion, agentName, findingId, cycle, operationalMode, extraContext = '') {
  const q = { ...originalQuestion };
  q.question_type = 'behavioral';
  const shortType = agentName.includes('diagnose') ? 'diag' : 'fix';
  q.id = `${originalQuestion.id}_heal${cycle}_${shortType}`;
  q.mode = 'agent';
  q.agent_name = agentName;
  q.finding = findingId;
  q.operational_mode = operationalMode;
  q.title = `[Heal ${cycle}] ${agentName} for ${originalQuestion.id}`;
  if (extraContext) {
    q.session_context = ((extraContext + '\n\n' + (q.session_context || '')).trim());
  }
  return q;
}

// ---------------------------------------------------------------------------
// Main heal loop
// ---------------------------------------------------------------------------

/**
 * Run the self-healing loop for a failed question.
 * @param {object} originalQuestion - The original question dict
 * @param {object} initialResult - The initial result (FAILURE or DIAGNOSIS_COMPLETE)
 * @param {string} findingPath - Path to the finding file
 * @param {function} runAgent - Function that runs an agent: (question) => result
 * @returns {object} The final result dict
 */
function runHealLoop(originalQuestion, initialResult, findingPath, runAgent) {
  if (!isEnabled()) return initialResult;

  const max = maxCycles();
  const originalQid = originalQuestion.id;
  let currentVerdict = initialResult.verdict;

  if (currentVerdict !== 'FAILURE' && currentVerdict !== 'DIAGNOSIS_COMPLETE') {
    return initialResult;
  }

  process.stderr.write(
    `\n[heal-loop] Starting heal loop for ${originalQid} (verdict=${currentVerdict}, max_cycles=${max})\n`,
  );

  let currentResult = initialResult;
  let currentFindingId = originalQid;
  let lastCycle = 0;

  for (let cycle = 1; cycle <= max; cycle++) {
    lastCycle = cycle;
    let verdict = currentResult.verdict;
    process.stderr.write(`\n[heal-loop] Cycle ${cycle}/${max} — current verdict: ${verdict}\n`);

    // Phase 1: FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE
    if (verdict === 'FAILURE') {
      if (!_agentExists('diagnose-analyst')) {
        process.stderr.write('[heal-loop] diagnose-analyst.md not found — cannot auto-diagnose\n');
        _appendHealNote(findingPath, cycle, 'SKIPPED', 'diagnose-analyst.md missing');
        break;
      }

      const diagQ = _syntheticQuestion(
        originalQuestion, 'diagnose-analyst', currentFindingId, cycle, 'diagnose',
        `HEAL LOOP CONTEXT: Cycle ${cycle}/${max} for ${originalQid}. Previous verdict: FAILURE. Produce DIAGNOSIS_COMPLETE with Fix Specification.`,
      );

      process.stderr.write(`[heal-loop] Running diagnose-analyst for ${currentFindingId}...\n`);
      const diagResult = runAgent(diagQ);
      const diagVerdict = diagResult.verdict;
      process.stderr.write(`[heal-loop] diagnose-analyst → ${diagVerdict}\n`);

      if (diagVerdict !== 'DIAGNOSIS_COMPLETE') {
        _appendHealNote(findingPath, cycle, `DIAGNOSE_${diagVerdict}`,
          `diagnose-analyst returned ${diagVerdict}: ${diagResult.summary || ''}`);
        break;
      }

      writeFinding(diagQ, diagResult);
      updateResultsTsv(diagQ.id, diagResult.verdict, diagResult.summary || '');
      _appendHealNote(findingPath, cycle, 'DIAGNOSIS_COMPLETE',
        `diagnose-analyst identified root cause: ${diagResult.summary || ''}`);

      currentResult = diagResult;
      currentFindingId = diagQ.id;
      verdict = 'DIAGNOSIS_COMPLETE';
    }

    // Phase 2: DIAGNOSIS_COMPLETE → fix-implementer → FIXED / FIX_FAILED
    if (verdict === 'DIAGNOSIS_COMPLETE') {
      if (!_agentExists('fix-implementer')) {
        process.stderr.write('[heal-loop] fix-implementer.md not found — cannot auto-fix\n');
        _appendHealNote(findingPath, cycle, 'SKIPPED', 'fix-implementer.md missing');
        break;
      }

      const fixQ = _syntheticQuestion(
        originalQuestion, 'fix-implementer', currentFindingId, cycle, 'fix',
        `HEAL LOOP CONTEXT: Cycle ${cycle}/${max} for ${originalQid}. Apply the fix, run verification. Output FIXED or FIX_FAILED.`,
      );

      process.stderr.write(`[heal-loop] Running fix-implementer for ${currentFindingId}...\n`);
      const fixResult = runAgent(fixQ);
      const fixVerdict = fixResult.verdict;
      process.stderr.write(`[heal-loop] fix-implementer → ${fixVerdict}\n`);

      writeFinding(fixQ, fixResult);
      updateResultsTsv(fixQ.id, fixResult.verdict, fixResult.summary || '');

      if (fixVerdict === 'FIXED') {
        _appendHealNote(findingPath, cycle, 'FIXED',
          `fix-implementer resolved the issue: ${fixResult.summary || ''}`);
        updateResultsTsv(originalQid, 'FIXED',
          `Auto-healed in cycle ${cycle}: ${fixResult.summary || ''}`);
        process.stderr.write(`\n[heal-loop] ${originalQid} FIXED on cycle ${cycle}\n`);
        return fixResult;
      }

      // FIX_FAILED — loop back
      _appendHealNote(findingPath, cycle, 'FIX_FAILED',
        `fix-implementer failed: ${fixResult.summary || ''}. Looping back.`);
      currentResult = { ...fixResult, verdict: 'FAILURE' };
      currentFindingId = fixQ.id;
    } else {
      process.stderr.write(`[heal-loop] Unexpected verdict ${verdict} — exiting heal loop\n`);
      break;
    }
  }

  _appendHealNote(findingPath, lastCycle, 'EXHAUSTED',
    `Self-healing exhausted ${lastCycle} cycle(s) — human intervention required.`);
  updateResultsTsv(originalQid, 'HEAL_EXHAUSTED',
    `Self-healing exhausted ${lastCycle} cycle(s) — human intervention required.`);
  process.stderr.write(`[heal-loop] ${originalQid} exhausted ${lastCycle} cycle(s) — still unresolved\n`);
  return currentResult;
}

module.exports = {
  isEnabled,
  maxCycles,
  runHealLoop,
  _syntheticQuestion,
};

'use strict';
// engine/fixloop.js — Fix loop integration.
//
// Port of bl/fixloop.py to Node.js.
// After a FAILURE verdict, attempts fix + re-run cycle.
// Uses injectable fixAgent/reRunner functions for testability.

const fs = require('fs');

function _appendFixNote(findingPath, attempt, status, note) {
  const section = `\n## Fix Attempt ${attempt} — ${status}\n\n${note}\n`;
  try {
    fs.appendFileSync(findingPath, section, 'utf8');
  } catch (err) {
    process.stderr.write(`[fix-loop] Warning: could not append to ${findingPath}: ${err.message}\n`);
  }
}

function runFixLoop(question, result, findingPath, options = {}) {
  if (result.verdict !== 'FAILURE') return result;

  const fixAgent = options.fixAgent;
  const reRunner = options.reRunner;
  const maxAttempts = options.maxAttempts || 2;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    _appendFixNote(findingPath, attempt, 'RUNNING', 'Fix agent spawned');

    const success = fixAgent(question, result, findingPath);
    if (!success) {
      _appendFixNote(findingPath, attempt, 'FAILED', 'Agent exited non-zero');
      continue;
    }

    const newResult = reRunner(question);
    if (newResult.verdict === 'HEALTHY') {
      _appendFixNote(findingPath, attempt, 'RESOLVED', newResult.summary || '');
      return newResult;
    }

    _appendFixNote(findingPath, attempt, 'FAILED', newResult.summary || '');
  }

  _appendFixNote(findingPath, maxAttempts, 'EXHAUSTED',
    'Max attempts reached — human intervention required');
  return result;
}

module.exports = { runFixLoop };

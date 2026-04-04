'use strict';
// engine/runners/correctness.js — Pytest subprocess runner.
//
// Port of bl/runners/correctness.py to Node.js.

const { execSync } = require('child_process');
const { cfg } = require('../config');

function _extractTestPaths(testField) {
  const pytestMatches = testField.match(/pytest\s+([\w/.]+(?:\s+[\w/.]+)*)/);
  if (pytestMatches) return pytestMatches[1];

  const pathMatches = testField.match(/(?:tests?|src)\/[\w/.-]+\.py/g);
  if (pathMatches) return pathMatches.join(' ');

  return null;
}

function _parsePytestOutput(combined) {
  const passedMatch = combined.match(/(\d+) passed/);
  const failedMatch = combined.match(/(\d+) failed/);
  const errorsMatch = combined.match(/(\d+) error/);

  const passed = passedMatch ? parseInt(passedMatch[1], 10) : 0;
  const failed = failedMatch ? parseInt(failedMatch[1], 10) : 0;
  const errors = errorsMatch ? parseInt(errorsMatch[1], 10) : 0;

  const noTests =
    combined.toLowerCase().includes('no tests ran') ||
    combined.includes('collected 0 items') ||
    (combined.includes('ERROR') && combined.toLowerCase().includes('not found'));

  if (noTests && passed === 0 && failed === 0) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'No tests found for paths in question.',
      data: { passed, failed, errors },
      details: combined.slice(0, 4000),
    };
  }

  if (failed > 0 || errors > 0) {
    return {
      verdict: 'FAILURE',
      summary: `${passed} passed, ${failed} failed, ${errors} errors`,
      data: { passed, failed, errors },
      details: combined.slice(0, 4000),
    };
  }

  return {
    verdict: 'HEALTHY',
    summary: `${passed} passed, ${failed} failed`,
    data: { passed, failed, errors },
    details: combined.slice(0, 4000),
  };
}

function runCorrectness(question) {
  const testField = question.test || question.Test || '';
  const paths = _extractTestPaths(testField);

  if (!paths) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'Could not extract pytest path from question Test field',
      data: {},
      details: `Test field: ${testField}`,
    };
  }

  const cmd = `python -m pytest ${paths} -v --tb=short -q`;

  try {
    const stdout = execSync(cmd, {
      encoding: 'utf8',
      timeout: 300000,
      cwd: cfg.recallSrc,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return _parsePytestOutput(stdout);
  } catch (err) {
    if (err.killed) {
      return {
        verdict: 'INCONCLUSIVE',
        summary: 'pytest timed out after 300s',
        data: {},
        details: 'Subprocess timeout',
      };
    }
    if (err.stdout || err.stderr) {
      const combined = (err.stdout || '').toString() + '\n' + (err.stderr || '').toString();
      return _parsePytestOutput(combined);
    }
    return {
      verdict: 'INCONCLUSIVE',
      summary: `pytest subprocess error: ${err.message}`,
      data: {},
      details: err.message,
    };
  }
}

module.exports = {
  runCorrectness,
  _extractTestPaths,
  _parsePytestOutput,
};

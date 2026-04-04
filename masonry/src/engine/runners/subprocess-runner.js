'use strict';
// engine/runners/subprocess-runner.js — General subprocess command runner.
//
// Port of bl/runners/subprocess_runner.py to Node.js.

const { execSync } = require('child_process');
const { cfg } = require('../config');

const _DIRECTIVES = ['expect_exit:', 'expect_stdout:', 'expect_not_stdout:', 'timeout:'];
const _CODE_FENCE = '```';

function _parseSubprocessSpec(testField) {
  const spec = {
    command: null,
    expectExit: 0,
    expectStdout: null,
    expectNotStdout: null,
    timeout: 30,
  };

  const commandLines = [];

  for (const line of testField.split('\n')) {
    const stripped = line.trim();
    if (stripped.startsWith(_CODE_FENCE)) continue;
    if (!stripped) continue;

    const low = stripped.toLowerCase();

    if (low.startsWith('expect_exit:')) {
      const val = parseInt(stripped.slice(stripped.indexOf(':') + 1).trim(), 10);
      if (!isNaN(val)) spec.expectExit = val;
      continue;
    }
    if (low.startsWith('expect_stdout:')) {
      spec.expectStdout = stripped.slice(stripped.indexOf(':') + 1).trim();
      continue;
    }
    if (low.startsWith('expect_not_stdout:')) {
      spec.expectNotStdout = stripped.slice(stripped.indexOf(':') + 1).trim();
      continue;
    }
    if (low.startsWith('timeout:')) {
      const val = parseInt(stripped.slice(stripped.indexOf(':') + 1).trim(), 10);
      if (!isNaN(val)) spec.timeout = val;
      continue;
    }

    commandLines.push(stripped);
  }

  if (commandLines.length) {
    spec.command = commandLines.join(' && ');
  }

  return spec;
}

function _buildVerdict({ command, returncode, stdout, stderr, expectExit, expectStdout, expectNotStdout }) {
  // Check if stdout is a JSON verdict envelope
  const stdoutTrimmed = stdout.trim();
  if (stdoutTrimmed.startsWith('{')) {
    try {
      const parsed = JSON.parse(stdoutTrimmed);
      if (parsed.verdict) {
        if (!parsed.summary) parsed.summary = `exit=${returncode}: ${stdoutTrimmed.slice(0, 100)}`;
        if (!parsed.data) parsed.data = { command, returncode, exit_expected: expectExit, stdout_preview: stdout.slice(0, 500), stderr_preview: stderr.slice(0, 200) };
        if (!parsed.details) parsed.details = `Command: ${command}\nExit: ${returncode} (expected ${expectExit})\nStdout:\n${stdout.slice(0, 800)}\nStderr:\n${stderr.slice(0, 400)}`;
        return parsed;
      }
    } catch {
      // not valid JSON
    }
  }

  let verdict = 'HEALTHY';
  const failureReasons = [];

  if (returncode !== expectExit) {
    verdict = 'FAILURE';
    failureReasons.push(`exit code ${returncode} != expected ${expectExit}`);
  }

  if (expectStdout !== null && !stdout.includes(expectStdout)) {
    verdict = 'FAILURE';
    failureReasons.push(`expected stdout substring '${expectStdout}' not found`);
  }

  if (expectNotStdout !== null && stdout.includes(expectNotStdout)) {
    verdict = 'FAILURE';
    failureReasons.push(`forbidden stdout substring '${expectNotStdout}' was found`);
  }

  const oneLine = (stdout.slice(0, 100) || stderr.slice(0, 100)).trim().replace(/\n/g, ' ');
  let summary = `exit=${returncode}: ${oneLine}`;
  if (failureReasons.length) {
    summary += ' | ' + failureReasons.join('; ');
  }

  return {
    verdict,
    summary,
    data: {
      command,
      returncode,
      exit_expected: expectExit,
      stdout_preview: stdout.slice(0, 500),
      stderr_preview: stderr.slice(0, 200),
    },
    details: `Command: ${command}\nExit: ${returncode} (expected ${expectExit})\nStdout:\n${stdout.slice(0, 800)}\nStderr:\n${stderr.slice(0, 400)}`,
  };
}

function runSubprocess(question) {
  const testField = question.test || question.Test || '';
  const spec = _parseSubprocessSpec(testField);

  if (!spec.command) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'No command found in Test field',
      data: { test_field: testField.slice(0, 200) },
      details: 'The Test field contained no executable command lines.',
    };
  }

  try {
    const stdout = execSync(spec.command, {
      encoding: 'utf8',
      timeout: spec.timeout * 1000,
      cwd: cfg.autosearchRoot,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return _buildVerdict({
      command: spec.command,
      returncode: 0,
      stdout: stdout || '',
      stderr: '',
      expectExit: spec.expectExit,
      expectStdout: spec.expectStdout,
      expectNotStdout: spec.expectNotStdout,
    });
  } catch (err) {
    if (err.killed) {
      return {
        verdict: 'FAILURE',
        summary: `Command timed out after ${spec.timeout}s: ${spec.command.slice(0, 80)}`,
        data: { command: spec.command, returncode: null, failure_type: 'timeout' },
        details: `Command: ${spec.command}\nTimeout: ${spec.timeout}s exceeded`,
        failure_type: 'timeout',
      };
    }
    if (err.status !== undefined) {
      return _buildVerdict({
        command: spec.command,
        returncode: err.status,
        stdout: (err.stdout || '').toString(),
        stderr: (err.stderr || '').toString(),
        expectExit: spec.expectExit,
        expectStdout: spec.expectStdout,
        expectNotStdout: spec.expectNotStdout,
      });
    }
    return {
      verdict: 'INCONCLUSIVE',
      summary: `Failed to run command: ${err.message}`,
      data: { command: spec.command, error: err.message },
      details: `Command: ${spec.command}\nError: ${err.message}`,
    };
  }
}

module.exports = {
  runSubprocess,
  _parseSubprocessSpec,
  _buildVerdict,
};

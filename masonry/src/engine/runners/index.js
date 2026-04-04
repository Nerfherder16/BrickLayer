'use strict';
// engine/runners/index.js — Runner dispatch and built-in registration.
//
// Port of bl/runners/__init__.py to Node.js.

const base = require('./base');
const { runAgent } = require('./agent');
const { runHttp, _parseHttpSpec, _buildHttpVerdict } = require('./http');
const { runSubprocess } = require('./subprocess-runner');
const { runCorrectness } = require('./correctness');
const { runQuality } = require('./quality');
const { runSwarm } = require('./swarm');

// Register built-in runners
function _registerBuiltins() {
  base.register('agent', runAgent, {
    mode: 'agent',
    description: 'LLM agent runner — spawns a specialist Claude agent to investigate a question',
    targetTypes: ['codebase', 'api', 'document', 'any'],
    syntaxSummary: 'Agent:, Target:, Test: (optional)',
  });

  base.register('code_audit', runAgent, {
    mode: 'code_audit',
    description: 'Semantic alias for agent mode — code audit questions routed to agent',
    targetTypes: ['codebase'],
    syntaxSummary: 'Target: (source files or dirs)',
  });

  base.register('http', runHttp, {
    mode: 'http',
    description: 'HTTP runner — fires real HTTP requests, checks status, body, and latency',
    targetTypes: ['api', 'service', 'url'],
    syntaxSummary: 'GET/POST {url}, expect_status:, expect_body:, latency_threshold_ms:',
  });

  base.register('subprocess', runSubprocess, {
    mode: 'subprocess',
    description: 'Subprocess runner — executes shell commands, checks exit codes and stdout patterns',
    targetTypes: ['codebase', 'test_suite', 'cli'],
    syntaxSummary: '{command}, expect_exit:, expect_stdout:, expect_not_stdout:, timeout:',
  });

  base.register('quality', runQuality, {
    mode: 'quality',
    description: 'Quality/static analysis runner — reads source files and pattern-matches against quality criteria',
    targetTypes: ['codebase'],
    syntaxSummary: 'Target: (source files or dirs)',
  });

  base.register('static', runQuality, {
    mode: 'static',
    description: 'Static analysis runner (alias for quality)',
    targetTypes: ['codebase'],
  });

  base.register('correctness', runCorrectness, {
    mode: 'correctness',
    description: 'Correctness runner — verifies functional correctness by running test suites',
    targetTypes: ['codebase', 'test_suite'],
    syntaxSummary: 'Target: (test file), Test: (assertion to verify)',
  });

  base.register('swarm', runSwarm, {
    mode: 'swarm',
    description: 'Swarm meta-runner — runs multiple sub-runners in parallel and aggregates verdicts',
    targetTypes: ['any'],
    syntaxSummary: 'workers: [{id, mode, spec}], aggregation: worst|majority|any_failure',
  });
}

_registerBuiltins();

function runQuestion(question) {
  const mode = question.mode;
  const qid = question.id;

  const runner = base.get(mode);
  let result;
  if (runner) {
    result = runner(question);
  } else {
    result = {
      verdict: 'INCONCLUSIVE',
      summary: `Unknown mode '${mode}' — no runner registered`,
      data: { registered_modes: base.registeredModes() },
      details: `Mode '${mode}' has no registered runner. Available: ${base.registeredModes().join(', ')}.`,
    };
  }

  result.question_id = qid;
  result.mode = mode;
  return result;
}

module.exports = {
  runQuestion,
  // Re-export base
  register: base.register,
  get: base.get,
  registeredModes: base.registeredModes,
  describe: base.describe,
  listRunners: base.listRunners,
  runnerMenu: base.runnerMenu,
};

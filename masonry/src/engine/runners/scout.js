'use strict';
// engine/runners/scout.js — Scout agent runner for question generation.
//
// Port of bl/runners/scout.py to Node.js.
// The full runner requires tmux agent spawning at runtime.
// This module provides a placeholder that returns INCONCLUSIVE
// when called outside of a tmux environment.

const RUNNER_NAME = 'scout';

function runScout(_question) {
  return {
    verdict: 'INCONCLUSIVE',
    summary: 'Scout runner requires runtime tmux agent spawning',
    data: { error: 'runtime_only' },
    details: 'The scout runner spawns a tmux agent to scan the codebase and generate questions. ' +
      'It requires the full BrickLayer runtime environment (tmux, claude CLI, project config).',
  };
}

module.exports = {
  RUNNER_NAME,
  runScout,
};

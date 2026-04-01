'use strict';
// engine/tmux/index.js — Public API for tmux orchestration layer.

const { SpawnResult, AgentResult, spawnAgent, waitForAgent } = require('./core');
const { spawnWave, collectWave } = require('./wave');
const { cleanupPanes } = require('./pane');
const { MODEL_MAP, inTmux, resolveModel, buildEnv, buildClaudeArgs, extractSessionId } = require('./helpers');
const { writeStartSignal, writeStopSignal } = require('./signals');

module.exports = {
  // Core
  SpawnResult,
  AgentResult,
  spawnAgent,
  waitForAgent,

  // Wave
  spawnWave,
  collectWave,

  // Pane
  cleanupPanes,

  // Helpers
  MODEL_MAP,
  inTmux,
  resolveModel,
  buildEnv,
  buildClaudeArgs,
  extractSessionId,

  // Signals
  writeStartSignal,
  writeStopSignal,
};

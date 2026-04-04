'use strict';
// engine/tmux/signals.js — Hook lifecycle signal files for masonry integration.
//
// Port of bl/tmux/signals.py to Node.js.

const fs = require('fs');
const path = require('path');
const { resolveModel } = require('./helpers');

let SIGNAL_DIR = '/tmp';

function _writeSignal(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data), 'utf8');
  } catch {
    // silently ignore write errors
  }
}

function writeStartSignal(agentId, agentName, cwd, model, paneId) {
  _writeSignal(
    path.join(SIGNAL_DIR, `bl-agent-start-${agentId}.json`),
    {
      agent_id: agentId,
      agent_name: agentName,
      model: resolveModel(model) || '',
      cwd,
      timestamp: new Date().toISOString(),
      pane_id: paneId,
      tmux: paneId !== null && paneId !== undefined,
    },
  );
}

function writeStopSignal(agentId, agentName, result) {
  _writeSignal(
    path.join(SIGNAL_DIR, `bl-agent-stop-${agentId}.json`),
    {
      agent_id: agentId,
      agent_name: agentName,
      exit_code: result.exit_code,
      duration_ms: result.duration_ms,
      session_id: result.session_id,
      timestamp: new Date().toISOString(),
    },
  );
}

module.exports = {
  get SIGNAL_DIR() { return SIGNAL_DIR; },
  set SIGNAL_DIR(v) { SIGNAL_DIR = v; },
  writeStartSignal,
  writeStopSignal,
};

'use strict';
// engine/tmux/wave.js — Batch spawn and collect for agent waves.
//
// Port of bl/tmux/wave.py to Node.js.

const { execFileSync } = require('child_process');
const { spawnAgent } = require('./core');
const { waitForAgent } = require('./core');
const { inTmux } = require('./helpers');

function spawnWave(agents, { maxConcurrency = null, spawner = null } = {}) {
  const batch = maxConcurrency ? agents.slice(0, maxConcurrency) : agents;
  const _spawn = spawner || ((name, prompt, opts) => spawnAgent(name, prompt, opts));

  const spawns = [];
  for (const spec of batch) {
    const { agentName, prompt, ...rest } = spec;
    spawns.push(_spawn(agentName, prompt, rest));
  }

  if (inTmux() && spawns.length) {
    try {
      execFileSync('tmux', ['select-layout', 'tiled'], {
        timeout: 5000,
        stdio: ['pipe', 'pipe', 'pipe'],
      });
    } catch {
      // ignore layout failures
    }
  }

  return spawns;
}

function collectWave(spawns, { timeout = 600, waiter = null } = {}) {
  const _wait = waiter || ((spawn, opts) => waitForAgent(spawn, opts));
  return spawns.map(s => _wait(s, { timeout }));
}

module.exports = {
  spawnWave,
  collectWave,
};

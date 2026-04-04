'use strict';
// engine/runners/base.js — Runner registry and protocol.
//
// Port of bl/runners/base.py to Node.js.
// Any function (question) => verdictEnvelope qualifies as a Runner.

let _registry = {};
let _info = {};

function register(mode, runner, info) {
  if (typeof runner !== 'function') {
    throw new TypeError(
      `Runner for mode '${mode}' must be a function with signature (question) => envelope.`,
    );
  }
  _registry[mode] = runner;
  if (info) {
    _info[mode] = info;
  }
}

function get(mode) {
  return _registry[mode] || null;
}

function registeredModes() {
  return Object.keys(_registry).sort();
}

function describe(mode) {
  return _info[mode] || null;
}

function listRunners() {
  return Object.values(_info).sort((a, b) => (a.mode < b.mode ? -1 : a.mode > b.mode ? 1 : 0));
}

function runnerMenu() {
  const runners = listRunners();
  if (!runners.length) return 'No runner metadata available.';

  const lines = [];
  for (const info of runners) {
    lines.push(`- \`${info.mode}\`: ${info.description}`);
    if (info.syntaxSummary) {
      lines.push(`  Syntax: ${info.syntaxSummary}`);
    }
  }
  return lines.join('\n');
}

function _reset() {
  _registry = {};
  _info = {};
}

module.exports = {
  register,
  get,
  registeredModes,
  describe,
  listRunners,
  runnerMenu,
  _reset,
};

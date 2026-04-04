'use strict';
// engine/tmux/helpers.js — Detection, model resolution, env building, CLI args.
//
// Port of bl/tmux/helpers.py to Node.js.

const { execFileSync } = require('child_process');

const MODEL_MAP = {
  opus: 'claude-opus-4-6',
  sonnet: 'claude-sonnet-4-6',
  haiku: 'claude-haiku-4-5-20251001',
};

function _tmuxSocketActive() {
  try {
    execFileSync('tmux', ['display-message', '-p', ''], {
      timeout: 3000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return true;
  } catch {
    return false;
  }
}

function inTmux() {
  return Boolean(process.env.TMUX) || _tmuxSocketActive();
}

function resolveModel(model) {
  if (!model) return null;
  return MODEL_MAP[model] || model || null;
}

function buildEnv(envOverrides) {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (k !== 'CLAUDECODE') env[k] = v;
  }
  if (envOverrides) {
    for (const [k, v] of Object.entries(envOverrides)) {
      if (v === '') {
        delete env[k];
      } else {
        env[k] = v;
      }
    }
  }
  return env;
}

function buildClaudeArgs({
  model = null,
  allowedTools = null,
  disallowedTools = null,
  dangerouslySkipPermissions = false,
  outputFormat = 'json',
  sessionId = null,
} = {}) {
  const args = ['-p', '-'];
  if (outputFormat) {
    args.push('--output-format', outputFormat);
  }
  const resolved = resolveModel(model);
  if (resolved) {
    args.push('--model', resolved);
  }
  if (allowedTools) {
    args.push('--allowedTools', allowedTools.join(','));
  }
  if (disallowedTools) {
    args.push('--disallowedTools', disallowedTools.join(','));
  }
  if (dangerouslySkipPermissions) {
    args.push('--dangerously-skip-permissions');
  }
  if (sessionId) {
    args.push('--resume', sessionId);
  }
  return args;
}

function extractSessionId(raw) {
  try {
    const data = JSON.parse(raw);
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return data.session_id || null;
    }
  } catch {
    // invalid JSON
  }
  return null;
}

module.exports = {
  MODEL_MAP,
  inTmux,
  resolveModel,
  buildEnv,
  buildClaudeArgs,
  extractSessionId,
};

'use strict';
// engine/tmux/pane.js — Tmux pane spawning, waiting, and cleanup.
//
// Port of bl/tmux/pane.py to Node.js.

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function _quote(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

function buildPaneCommand({
  agentId,
  agentName,
  claudeBin,
  claudeArgs,
  promptFile,
  resultFile,
  exitFile,
  cwd,
  envOverrides,
}) {
  const cmdStr = [claudeBin, ...claudeArgs].map(_quote).join(' ');

  const parts = ['unset CLAUDECODE'];

  if (envOverrides) {
    for (const [k, v] of Object.entries(envOverrides)) {
      if (v) {
        parts.push(`export ${k}=${_quote(v)}`);
      } else {
        parts.push(`unset ${k}`);
      }
    }
  }

  parts.push(`cd ${_quote(cwd)}`);
  parts.push(`printf '\\n── Agent: %s ──\\n\\n' ${_quote(agentName)}`);

  const usesStream = claudeArgs.includes('stream-json');
  if (usesStream) {
    parts.push(`${cmdStr} < ${_quote(promptFile)} | python3 -u stream_format.py`);
  } else {
    parts.push(`${cmdStr} < ${_quote(promptFile)}`);
  }

  const exitCodeVar = usesStream ? '${PIPESTATUS[0]}' : '$?';
  parts.push(`echo ${exitCodeVar} > ${_quote(exitFile)}`);

  if (resultFile) {
    parts.push(`tmux capture-pane -p -S - -J > ${_quote(resultFile)}`);
  }

  parts.push(`tmux wait-for -S bl-done-${agentId}`);

  return parts.join('; ');
}

function spawnTmuxPane({
  agentId,
  agentName,
  claudeBin,
  claudeArgs,
  promptFile,
  resultFile,
  exitFile,
  cwd,
  envOverrides,
}) {
  const paneCmd = buildPaneCommand({
    agentId, agentName, claudeBin, claudeArgs,
    promptFile, resultFile, exitFile, cwd, envOverrides,
  });

  try {
    const proc = execFileSync('tmux', [
      'split-window', '-h', '-d', '-P', '-F', '#{pane_id}', paneCmd,
    ], { encoding: 'utf8', timeout: 10000, stdio: ['pipe', 'pipe', 'pipe'] });
    const paneId = proc.trim() || null;

    if (paneId) {
      try {
        execFileSync('tmux', [
          'select-pane', '-t', paneId, '-T', `agent:${agentName}`,
        ], { timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'] });
      } catch {
        // ignore title-set failures
      }
    }
    return paneId;
  } catch {
    return null;
  }
}

function tmuxWaitWithTimeout(channel, timeout) {
  try {
    execFileSync('timeout', [String(timeout), 'tmux', 'wait-for', channel], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return true;
  } catch {
    return false;
  }
}

function cleanupPanes(spawns, signalDir = '/tmp') {
  for (const spawn of spawns) {
    for (const f of [spawn.prompt_file, spawn.result_file, spawn.exit_file]) {
      try {
        if (f) fs.unlinkSync(f);
      } catch {
        // ignore missing files
      }
    }

    for (const prefix of ['bl-agent-start-', 'bl-agent-stop-']) {
      try {
        fs.unlinkSync(path.join(signalDir, `${prefix}${spawn.agent_id}.json`));
      } catch {
        // ignore missing signal files
      }
    }

    if (spawn.pane_id && process.env.BL_KEEP_PANES !== '1') {
      try {
        execFileSync('tmux', ['kill-pane', '-t', spawn.pane_id], {
          timeout: 5000,
          stdio: ['pipe', 'pipe', 'pipe'],
        });
      } catch {
        // ignore kill failures
      }
    }
  }
}

module.exports = {
  buildPaneCommand,
  spawnTmuxPane,
  tmuxWaitWithTimeout,
  cleanupPanes,
};

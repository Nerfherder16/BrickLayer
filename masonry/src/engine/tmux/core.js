'use strict';
// engine/tmux/core.js — Dataclasses, spawn_agent, wait_for_agent.
//
// Port of bl/tmux/core.py to Node.js.

const { spawn: cpSpawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { randomUUID } = require('crypto');
const { buildClaudeArgs, buildEnv, extractSessionId, inTmux } = require('./helpers');
const { spawnTmuxPane, tmuxWaitWithTimeout } = require('./pane');
const { writeStartSignal, writeStopSignal } = require('./signals');

const TEMP_DIR = '/tmp';

class SpawnResult {
  constructor({ agentId, agentName, paneId, resultFile, exitFile, promptFile, process = null }) {
    this.agentId = agentId;
    this.agentName = agentName;
    this.paneId = paneId;
    this.resultFile = resultFile;
    this.exitFile = exitFile;
    this.promptFile = promptFile;
    this.process = process;
    this.startTime = Date.now();
  }
}

class AgentResult {
  constructor({ agentId, agentName, exitCode, stdout, sessionId, durationMs }) {
    this.agentId = agentId;
    this.agentName = agentName;
    this.exitCode = exitCode;
    this.stdout = stdout;
    this.sessionId = sessionId;
    this.durationMs = durationMs;
  }
}

function spawnAgent(agentName, prompt, {
  model = null,
  allowedTools = null,
  disallowedTools = null,
  cwd = null,
  timeout = 600,
  captureOutput = true,
  outputFormat = 'json',
  dangerouslySkipPermissions = false,
  sessionId = null,
  envOverrides = null,
} = {}) {
  const agentId = randomUUID().replace(/-/g, '').slice(0, 8);
  const resultFile = path.join(TEMP_DIR, `bl-result-${agentId}.json`);
  const exitFile = path.join(TEMP_DIR, `bl-exit-${agentId}.txt`);
  const promptFile = path.join(TEMP_DIR, `bl-prompt-${agentId}.txt`);
  fs.writeFileSync(promptFile, prompt, 'utf8');

  const claudeBin = 'claude';
  const claudeArgs = buildClaudeArgs({
    model,
    allowedTools,
    disallowedTools,
    dangerouslySkipPermissions,
    outputFormat: captureOutput ? outputFormat : null,
    sessionId,
  });
  const effectiveCwd = cwd || process.cwd();
  writeStartSignal(agentId, agentName, effectiveCwd, model, null);

  if (inTmux()) {
    const paneClaudeArgs = buildClaudeArgs({
      model,
      allowedTools,
      disallowedTools,
      dangerouslySkipPermissions,
      outputFormat: 'stream-json',
      sessionId,
    });
    const paneId = spawnTmuxPane({
      agentId,
      agentName,
      claudeBin,
      claudeArgs: paneClaudeArgs,
      promptFile,
      resultFile: captureOutput ? resultFile : null,
      exitFile,
      cwd: effectiveCwd,
      envOverrides,
    });
    writeStartSignal(agentId, agentName, effectiveCwd, model, paneId);
    return new SpawnResult({
      agentId, agentName, paneId, resultFile, exitFile, promptFile,
    });
  }

  // Non-tmux: subprocess
  const childEnv = buildEnv(envOverrides);
  const stdinFh = fs.openSync(promptFile, 'r');
  const proc = cpSpawn(claudeBin, claudeArgs, {
    stdio: [stdinFh, captureOutput ? 'pipe' : 'ignore', captureOutput ? 'pipe' : 'ignore'],
    cwd: effectiveCwd,
    env: childEnv,
  });
  fs.closeSync(stdinFh);

  return new SpawnResult({
    agentId, agentName, paneId: null, resultFile, exitFile, promptFile, process: proc,
  });
}

function waitForSubprocess(spawn, timeout) {
  const proc = spawn.process;
  const raw = proc.communicate ? proc.communicate(timeout) : { stdout: '', returncode: 0 };
  const stdout = raw.stdout || '';
  const exitCode = raw.returncode || 0;

  const result = new AgentResult({
    agentId: spawn.agentId,
    agentName: spawn.agentName,
    exitCode,
    stdout,
    sessionId: extractSessionId(stdout),
    durationMs: Date.now() - spawn.startTime,
  });
  writeStopSignal(spawn.agentId, spawn.agentName, {
    exit_code: result.exitCode,
    duration_ms: result.durationMs,
    session_id: result.sessionId,
  });
  return result;
}

function collectTmuxResult(spawn, completed) {
  const durationMs = Date.now() - spawn.startTime;

  let stdout = '';
  let exitCode = -1;

  if (completed) {
    try {
      stdout = fs.readFileSync(spawn.resultFile, 'utf8');
    } catch {
      // file may not exist
    }
    try {
      exitCode = parseInt(fs.readFileSync(spawn.exitFile, 'utf8').trim(), 10);
      if (isNaN(exitCode)) exitCode = -1;
    } catch {
      // file may not exist
    }
  }

  const result = new AgentResult({
    agentId: spawn.agentId,
    agentName: spawn.agentName,
    exitCode,
    stdout,
    sessionId: extractSessionId(stdout),
    durationMs,
  });
  writeStopSignal(spawn.agentId, spawn.agentName, {
    exit_code: result.exitCode,
    duration_ms: result.durationMs,
    session_id: result.sessionId,
  });
  return result;
}

function waitForAgent(spawn, { timeout = 600 } = {}) {
  if (spawn.process !== null) {
    return waitForSubprocess(spawn, timeout);
  }
  const channel = `bl-done-${spawn.agentId}`;
  const completed = tmuxWaitWithTimeout(channel, timeout);
  return collectTmuxResult(spawn, completed);
}

module.exports = {
  SpawnResult,
  AgentResult,
  spawnAgent,
  waitForAgent,
  waitForSubprocess,
  collectTmuxResult,
};

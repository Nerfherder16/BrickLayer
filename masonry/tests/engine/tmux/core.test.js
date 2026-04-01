import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/tmux/core — SpawnResult', () => {
  let core;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'core.js');
    delete require.cache[modPath];
    core = require(modPath);
  });

  it('should create SpawnResult with all fields', () => {
    const sr = new core.SpawnResult({
      agentId: 'abc',
      agentName: 'test',
      paneId: '%5',
      resultFile: '/tmp/result.json',
      exitFile: '/tmp/exit.txt',
      promptFile: '/tmp/prompt.txt',
    });
    expect(sr.agentId).toBe('abc');
    expect(sr.agentName).toBe('test');
    expect(sr.paneId).toBe('%5');
    expect(sr.resultFile).toBe('/tmp/result.json');
    expect(sr.exitFile).toBe('/tmp/exit.txt');
    expect(sr.promptFile).toBe('/tmp/prompt.txt');
    expect(sr.process).toBeNull();
    expect(typeof sr.startTime).toBe('number');
  });

  it('should accept optional process field', () => {
    const fakeProc = { pid: 123 };
    const sr = new core.SpawnResult({
      agentId: 'x',
      agentName: 'y',
      paneId: null,
      resultFile: '/tmp/r.json',
      exitFile: '/tmp/e.txt',
      promptFile: '/tmp/p.txt',
      process: fakeProc,
    });
    expect(sr.process).toBe(fakeProc);
  });
});

describe('engine/tmux/core — AgentResult', () => {
  let core;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'core.js');
    delete require.cache[modPath];
    core = require(modPath);
  });

  it('should create AgentResult with all fields', () => {
    const ar = new core.AgentResult({
      agentId: 'abc',
      agentName: 'test',
      exitCode: 0,
      stdout: 'output',
      sessionId: 'sess-1',
      durationMs: 5000,
    });
    expect(ar.agentId).toBe('abc');
    expect(ar.agentName).toBe('test');
    expect(ar.exitCode).toBe(0);
    expect(ar.stdout).toBe('output');
    expect(ar.sessionId).toBe('sess-1');
    expect(ar.durationMs).toBe(5000);
  });

  it('should handle null session_id', () => {
    const ar = new core.AgentResult({
      agentId: 'x',
      agentName: 'y',
      exitCode: 1,
      stdout: '',
      sessionId: null,
      durationMs: 100,
    });
    expect(ar.sessionId).toBeNull();
  });
});

describe('engine/tmux/core — waitForAgent (subprocess path)', () => {
  let core, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-core-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'core.js');
    delete require.cache[modPath];
    core = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should collect result from completed subprocess', async () => {
    // Simulate a child process that has already finished
    const resultFile = path.join(tmpDir, 'result.json');
    const exitFile = path.join(tmpDir, 'exit.txt');
    const promptFile = path.join(tmpDir, 'prompt.txt');
    fs.writeFileSync(promptFile, 'test prompt');

    // Create a mock process that immediately resolves
    const mockProcess = {
      _stdout: JSON.stringify({ session_id: 'sess-test', result: 'ok' }),
      _exitCode: 0,
      communicate(timeout) {
        return { stdout: this._stdout, returncode: this._exitCode };
      },
    };

    const spawn = new core.SpawnResult({
      agentId: 'subproc1',
      agentName: 'test-agent',
      paneId: null,
      resultFile,
      exitFile,
      promptFile,
      process: mockProcess,
    });

    const result = core.waitForSubprocess(spawn, 600);
    expect(result).toBeInstanceOf(core.AgentResult);
    expect(result.agentId).toBe('subproc1');
    expect(result.agentName).toBe('test-agent');
    expect(result.exitCode).toBe(0);
    expect(result.sessionId).toBe('sess-test');
    expect(result.durationMs).toBeGreaterThanOrEqual(0);
  });

  it('should handle subprocess with no JSON output', () => {
    const spawn = new core.SpawnResult({
      agentId: 'nojs1',
      agentName: 'agent',
      paneId: null,
      resultFile: path.join(tmpDir, 'r.json'),
      exitFile: path.join(tmpDir, 'e.txt'),
      promptFile: path.join(tmpDir, 'p.txt'),
      process: {
        _stdout: 'plain text output',
        _exitCode: 0,
        communicate() { return { stdout: this._stdout, returncode: this._exitCode }; },
      },
    });

    const result = core.waitForSubprocess(spawn, 600);
    expect(result.stdout).toBe('plain text output');
    expect(result.sessionId).toBeNull();
  });
});

describe('engine/tmux/core — waitForTmux', () => {
  let core, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-core-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'core.js');
    delete require.cache[modPath];
    core = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should read result and exit files when completed', () => {
    const resultFile = path.join(tmpDir, 'result.json');
    const exitFile = path.join(tmpDir, 'exit.txt');
    fs.writeFileSync(resultFile, JSON.stringify({ session_id: 'tmux-sess' }));
    fs.writeFileSync(exitFile, '0\n');

    const spawn = new core.SpawnResult({
      agentId: 'tmux1',
      agentName: 'agent',
      paneId: '%3',
      resultFile,
      exitFile,
      promptFile: path.join(tmpDir, 'p.txt'),
    });

    const result = core.collectTmuxResult(spawn, true);
    expect(result.exitCode).toBe(0);
    expect(result.sessionId).toBe('tmux-sess');
  });

  it('should return exit_code -1 when not completed', () => {
    const spawn = new core.SpawnResult({
      agentId: 'tmux2',
      agentName: 'agent',
      paneId: '%3',
      resultFile: path.join(tmpDir, 'noexist.json'),
      exitFile: path.join(tmpDir, 'noexist.txt'),
      promptFile: path.join(tmpDir, 'p.txt'),
    });

    const result = core.collectTmuxResult(spawn, false);
    expect(result.exitCode).toBe(-1);
    expect(result.stdout).toBe('');
    expect(result.sessionId).toBeNull();
  });
});

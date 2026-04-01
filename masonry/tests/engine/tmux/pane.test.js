import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/tmux/pane — buildPaneCommand', () => {
  let pane;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'pane.js');
    delete require.cache[modPath];
    pane = require(modPath);
  });

  it('should build a pane command string with all parts', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'abc123',
      agentName: 'test-agent',
      claudeBin: '/usr/bin/claude',
      claudeArgs: ['-p', '-', '--output-format', 'stream-json'],
      promptFile: '/tmp/bl-prompt-abc123.txt',
      resultFile: '/tmp/bl-result-abc123.json',
      exitFile: '/tmp/bl-exit-abc123.txt',
      cwd: '/home/user/project',
      envOverrides: null,
    });
    expect(cmd).toContain('unset CLAUDECODE');
    expect(cmd).toContain("cd '/home/user/project'");
    expect(cmd).toContain("'test-agent'");
    expect(cmd).toContain('bl-done-abc123');
    expect(cmd).toContain('/tmp/bl-exit-abc123.txt');
  });

  it('should include env overrides in command', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'x1',
      agentName: 'agent',
      claudeBin: 'claude',
      claudeArgs: ['-p', '-'],
      promptFile: '/tmp/prompt.txt',
      resultFile: null,
      exitFile: '/tmp/exit.txt',
      cwd: '/tmp',
      envOverrides: { MY_VAR: 'hello', REMOVE: '' },
    });
    expect(cmd).toContain("export MY_VAR='hello'");
    expect(cmd).toContain('unset REMOVE');
  });

  it('should include tmux capture-pane when resultFile is provided', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'x2',
      agentName: 'agent',
      claudeBin: 'claude',
      claudeArgs: ['-p', '-'],
      promptFile: '/tmp/prompt.txt',
      resultFile: '/tmp/result.json',
      exitFile: '/tmp/exit.txt',
      cwd: '/tmp',
      envOverrides: null,
    });
    expect(cmd).toContain('tmux capture-pane');
    expect(cmd).toContain('/tmp/result.json');
  });

  it('should omit tmux capture-pane when resultFile is null', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'x3',
      agentName: 'agent',
      claudeBin: 'claude',
      claudeArgs: ['-p', '-'],
      promptFile: '/tmp/prompt.txt',
      resultFile: null,
      exitFile: '/tmp/exit.txt',
      cwd: '/tmp',
      envOverrides: null,
    });
    expect(cmd).not.toContain('tmux capture-pane');
  });

  it('should use PIPESTATUS for stream-json mode', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'x4',
      agentName: 'agent',
      claudeBin: 'claude',
      claudeArgs: ['-p', '-', '--output-format', 'stream-json'],
      promptFile: '/tmp/prompt.txt',
      resultFile: null,
      exitFile: '/tmp/exit.txt',
      cwd: '/tmp',
      envOverrides: null,
    });
    expect(cmd).toContain('PIPESTATUS[0]');
  });

  it('should use $? for non-stream mode', () => {
    const cmd = pane.buildPaneCommand({
      agentId: 'x5',
      agentName: 'agent',
      claudeBin: 'claude',
      claudeArgs: ['-p', '-', '--output-format', 'json'],
      promptFile: '/tmp/prompt.txt',
      resultFile: null,
      exitFile: '/tmp/exit.txt',
      cwd: '/tmp',
      envOverrides: null,
    });
    expect(cmd).not.toContain('PIPESTATUS');
    expect(cmd).toContain('$?');
  });
});

describe('engine/tmux/pane — cleanupPanes', () => {
  let pane, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-pane-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'pane.js');
    delete require.cache[modPath];
    pane = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should remove temp files for spawns', () => {
    const promptFile = path.join(tmpDir, 'prompt.txt');
    const resultFile = path.join(tmpDir, 'result.json');
    const exitFile = path.join(tmpDir, 'exit.txt');
    fs.writeFileSync(promptFile, 'test');
    fs.writeFileSync(resultFile, 'test');
    fs.writeFileSync(exitFile, 'test');

    const spawn = {
      agent_id: 'cleanup1',
      pane_id: null,
      prompt_file: promptFile,
      result_file: resultFile,
      exit_file: exitFile,
    };

    pane.cleanupPanes([spawn], tmpDir);

    expect(fs.existsSync(promptFile)).toBe(false);
    expect(fs.existsSync(resultFile)).toBe(false);
    expect(fs.existsSync(exitFile)).toBe(false);
  });

  it('should remove signal files', () => {
    const startSig = path.join(tmpDir, 'bl-agent-start-sig1.json');
    const stopSig = path.join(tmpDir, 'bl-agent-stop-sig1.json');
    fs.writeFileSync(startSig, '{}');
    fs.writeFileSync(stopSig, '{}');

    const spawn = {
      agent_id: 'sig1',
      pane_id: null,
      prompt_file: path.join(tmpDir, 'nonexist.txt'),
      result_file: path.join(tmpDir, 'nonexist.json'),
      exit_file: path.join(tmpDir, 'nonexist2.txt'),
    };

    pane.cleanupPanes([spawn], tmpDir);

    expect(fs.existsSync(startSig)).toBe(false);
    expect(fs.existsSync(stopSig)).toBe(false);
  });

  it('should not throw when files do not exist', () => {
    const spawn = {
      agent_id: 'miss1',
      pane_id: null,
      prompt_file: path.join(tmpDir, 'nope.txt'),
      result_file: path.join(tmpDir, 'nope.json'),
      exit_file: path.join(tmpDir, 'nope2.txt'),
    };
    expect(() => pane.cleanupPanes([spawn], tmpDir)).not.toThrow();
  });
});

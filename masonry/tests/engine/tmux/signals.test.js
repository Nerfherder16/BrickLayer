import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/tmux/signals — writeStartSignal', () => {
  let signals, tmpDir, origSignalDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-sig-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'signals.js');
    delete require.cache[modPath];
    signals = require(modPath);
    origSignalDir = signals.SIGNAL_DIR;
    signals.SIGNAL_DIR = tmpDir;
  });

  afterEach(() => {
    signals.SIGNAL_DIR = origSignalDir;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should write start signal JSON file', () => {
    signals.writeStartSignal('abc123', 'research-analyst', '/tmp/proj', 'opus', '%5');
    const filePath = path.join(tmpDir, 'bl-agent-start-abc123.json');
    expect(fs.existsSync(filePath)).toBe(true);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    expect(data.agent_id).toBe('abc123');
    expect(data.agent_name).toBe('research-analyst');
    expect(data.model).toBe('claude-opus-4-6');
    expect(data.cwd).toBe('/tmp/proj');
    expect(data.pane_id).toBe('%5');
    expect(data.tmux).toBe(true);
    expect(data.timestamp).toBeTruthy();
  });

  it('should set tmux=false when pane_id is null', () => {
    signals.writeStartSignal('def456', 'agent', '/tmp', null, null);
    const data = JSON.parse(
      fs.readFileSync(path.join(tmpDir, 'bl-agent-start-def456.json'), 'utf8'),
    );
    expect(data.tmux).toBe(false);
    expect(data.pane_id).toBeNull();
  });

  it('should set model to empty string when model is null', () => {
    signals.writeStartSignal('ghi789', 'agent', '/tmp', null, null);
    const data = JSON.parse(
      fs.readFileSync(path.join(tmpDir, 'bl-agent-start-ghi789.json'), 'utf8'),
    );
    expect(data.model).toBe('');
  });
});

describe('engine/tmux/signals — writeStopSignal', () => {
  let signals, tmpDir, origSignalDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-sig-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'signals.js');
    delete require.cache[modPath];
    signals = require(modPath);
    origSignalDir = signals.SIGNAL_DIR;
    signals.SIGNAL_DIR = tmpDir;
  });

  afterEach(() => {
    signals.SIGNAL_DIR = origSignalDir;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should write stop signal JSON file', () => {
    const result = {
      exit_code: 0,
      duration_ms: 5000,
      session_id: 'sess-xyz',
    };
    signals.writeStopSignal('abc123', 'research-analyst', result);
    const filePath = path.join(tmpDir, 'bl-agent-stop-abc123.json');
    expect(fs.existsSync(filePath)).toBe(true);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    expect(data.agent_id).toBe('abc123');
    expect(data.agent_name).toBe('research-analyst');
    expect(data.exit_code).toBe(0);
    expect(data.duration_ms).toBe(5000);
    expect(data.session_id).toBe('sess-xyz');
    expect(data.timestamp).toBeTruthy();
  });

  it('should handle null session_id', () => {
    const result = { exit_code: 1, duration_ms: 100, session_id: null };
    signals.writeStopSignal('fail1', 'agent', result);
    const data = JSON.parse(
      fs.readFileSync(path.join(tmpDir, 'bl-agent-stop-fail1.json'), 'utf8'),
    );
    expect(data.session_id).toBeNull();
    expect(data.exit_code).toBe(1);
  });
});

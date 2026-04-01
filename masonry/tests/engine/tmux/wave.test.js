import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/tmux/wave — spawnWave', () => {
  let wave;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'wave.js');
    delete require.cache[modPath];
    wave = require(modPath);
  });

  it('should export spawnWave and collectWave', () => {
    expect(typeof wave.spawnWave).toBe('function');
    expect(typeof wave.collectWave).toBe('function');
  });

  it('should respect maxConcurrency by slicing agents', () => {
    const agents = [
      { agentName: 'a1', prompt: 'p1' },
      { agentName: 'a2', prompt: 'p2' },
      { agentName: 'a3', prompt: 'p3' },
    ];
    // spawnWave with injectable spawner to avoid real tmux/claude
    const spawned = [];
    const mockSpawner = (name, prompt, opts) => {
      spawned.push(name);
      return { agentId: name, agentName: name, paneId: null };
    };
    wave.spawnWave(agents, { maxConcurrency: 2, spawner: mockSpawner });
    expect(spawned).toEqual(['a1', 'a2']);
  });

  it('should spawn all agents when maxConcurrency is null', () => {
    const agents = [
      { agentName: 'a1', prompt: 'p1' },
      { agentName: 'a2', prompt: 'p2' },
      { agentName: 'a3', prompt: 'p3' },
    ];
    const spawned = [];
    const mockSpawner = (name, prompt, opts) => {
      spawned.push(name);
      return { agentId: name, agentName: name, paneId: null };
    };
    wave.spawnWave(agents, { spawner: mockSpawner });
    expect(spawned).toEqual(['a1', 'a2', 'a3']);
  });
});

describe('engine/tmux/wave — collectWave', () => {
  let wave;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tmux', 'wave.js');
    delete require.cache[modPath];
    wave = require(modPath);
  });

  it('should collect results using injectable waiter', () => {
    const spawns = [
      { agentId: 'a1', agentName: 'agent1', paneId: null },
      { agentId: 'a2', agentName: 'agent2', paneId: null },
    ];
    const mockWaiter = (spawn, opts) => ({
      agentId: spawn.agentId,
      agentName: spawn.agentName,
      exitCode: 0,
      stdout: 'done',
      sessionId: null,
      durationMs: 100,
    });
    const results = wave.collectWave(spawns, { waiter: mockWaiter });
    expect(results).toHaveLength(2);
    expect(results[0].agentId).toBe('a1');
    expect(results[1].agentId).toBe('a2');
    expect(results[0].exitCode).toBe(0);
  });
});

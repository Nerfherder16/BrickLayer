import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/index — runQuestion', () => {
  let runners;

  beforeEach(() => {
    // Clear all runner module caches
    const baseModPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'base.js');
    const idxModPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'index.js');
    delete require.cache[baseModPath];
    delete require.cache[idxModPath];
    runners = require(idxModPath);
  });

  it('should dispatch to registered runner', () => {
    const base = require(path.resolve(process.cwd(), 'src', 'engine', 'runners', 'base.js'));
    base.register('test-custom', (q) => ({
      verdict: 'HEALTHY',
      summary: `Custom: ${q.id}`,
      data: {},
      details: '',
    }));

    const result = runners.runQuestion({ id: 'Q1', mode: 'test-custom' });
    expect(result.verdict).toBe('HEALTHY');
    expect(result.summary).toContain('Q1');
    expect(result.question_id).toBe('Q1');
    expect(result.mode).toBe('test-custom');
  });

  it('should return INCONCLUSIVE for unknown mode', () => {
    const result = runners.runQuestion({ id: 'Q2', mode: 'nonexistent' });
    expect(result.verdict).toBe('INCONCLUSIVE');
    expect(result.summary).toContain('nonexistent');
    expect(result.question_id).toBe('Q2');
  });

  it('should export re-exported base functions', () => {
    expect(typeof runners.register).toBe('function');
    expect(typeof runners.get).toBe('function');
    expect(typeof runners.registeredModes).toBe('function');
    expect(typeof runners.runnerMenu).toBe('function');
  });

  it('should have built-in runners registered', () => {
    const modes = runners.registeredModes();
    expect(modes).toContain('http');
    expect(modes).toContain('subprocess');
    expect(modes).toContain('agent');
    expect(modes).toContain('swarm');
  });
});

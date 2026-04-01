import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/swarm — verdict aggregation', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'swarm.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should aggregate worst — returns FAILURE when any worker fails', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'FAILURE' },
      { id: 'c', verdict: 'WARNING' },
    ];
    expect(mod._aggregateWorst(results)).toBe('FAILURE');
  });

  it('should aggregate worst — returns HEALTHY when all healthy', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'HEALTHY' },
    ];
    expect(mod._aggregateWorst(results)).toBe('HEALTHY');
  });

  it('should aggregate worst — returns INCONCLUSIVE for empty', () => {
    expect(mod._aggregateWorst([])).toBe('INCONCLUSIVE');
  });

  it('should aggregate majority — returns most weighted verdict', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'FAILURE' },
      { id: 'c', verdict: 'HEALTHY' },
    ];
    expect(mod._aggregateMajority(results, {})).toBe('HEALTHY');
  });

  it('should aggregate majority — respects weights', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'FAILURE' },
    ];
    expect(mod._aggregateMajority(results, { b: 3 })).toBe('FAILURE');
  });

  it('should aggregate any_failure — returns FAILURE if any worker failed', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'FAILURE' },
    ];
    expect(mod._aggregateAnyFailure(results)).toBe('FAILURE');
  });

  it('should aggregate any_failure — returns worst of rest when no failure', () => {
    const results = [
      { id: 'a', verdict: 'HEALTHY' },
      { id: 'b', verdict: 'WARNING' },
    ];
    expect(mod._aggregateAnyFailure(results)).toBe('WARNING');
  });
});

describe('engine/runners/swarm — verdictRank', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'swarm.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should rank FAILURE as worst (0)', () => {
    expect(mod._verdictRank('FAILURE')).toBe(0);
  });

  it('should rank HEALTHY as best (3)', () => {
    expect(mod._verdictRank('HEALTHY')).toBe(3);
  });

  it('should treat unknown as INCONCLUSIVE (2)', () => {
    expect(mod._verdictRank('SOMETHING_WEIRD')).toBe(2);
  });
});

describe('engine/runners/swarm — runSwarm', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'swarm.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return INCONCLUSIVE when no workers defined', () => {
    const result = mod.runSwarm({ spec: { workers: [] } });
    expect(result.verdict).toBe('INCONCLUSIVE');
    expect(result.summary).toContain('no workers');
  });

  it('should run workers via injectable workerRunner', () => {
    const mockWorkerRunner = (workerDef) => ({
      id: workerDef.id,
      mode: workerDef.mode,
      verdict: workerDef.id === 'good' ? 'HEALTHY' : 'WARNING',
      summary: `Worker ${workerDef.id}`,
      data: {},
      details: '',
      duration_ms: 50,
    });

    const result = mod.runSwarm(
      {
        spec: {
          workers: [
            { id: 'good', mode: 'http', spec: {} },
            { id: 'meh', mode: 'subprocess', spec: {} },
          ],
          aggregation: 'worst',
        },
      },
      { workerRunner: mockWorkerRunner },
    );

    expect(result.verdict).toBe('WARNING');
    expect(result.data.workers_total).toBe(2);
    expect(result.data.workers_complete).toBe(2);
    expect(result.data.by_worker.good.verdict).toBe('HEALTHY');
    expect(result.data.by_worker.meh.verdict).toBe('WARNING');
  });
});

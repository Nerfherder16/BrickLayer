import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/agent-db', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-agentdb-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'agent-db.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('recordRun', () => {
    it('should create agent record on first run', () => {
      const score = mod.recordRun(tmpDir, 'agent-1', 'HEALTHY');
      expect(score).toBe(1.0);
    });

    it('should track multiple verdicts and compute score', () => {
      mod.recordRun(tmpDir, 'agent-1', 'HEALTHY');
      mod.recordRun(tmpDir, 'agent-1', 'FAILURE');
      const score = mod.recordRun(tmpDir, 'agent-1', 'WARNING');
      // 1 success + 0.5 partial + 0 fail = 1.5 / 3 = 0.5
      expect(score).toBeCloseTo(0.5, 2);
    });
  });

  describe('getScore', () => {
    it('should return 1.0 for unknown agent', () => {
      expect(mod.getScore(tmpDir, 'unknown')).toBe(1.0);
    });

    it('should return computed score', () => {
      mod.recordRun(tmpDir, 'agent-1', 'FAILURE');
      expect(mod.getScore(tmpDir, 'agent-1')).toBe(0.0);
    });
  });

  describe('getTrend', () => {
    it('should return insufficient_data for unknown agent', () => {
      const trend = mod.getTrend(tmpDir, 'unknown');
      expect(trend.trending).toBe('insufficient_data');
    });

    it('should return trend when enough data', () => {
      // 10 runs: first 5 FAILURE, last 5 HEALTHY
      for (let i = 0; i < 5; i++) mod.recordRun(tmpDir, 'a', 'FAILURE');
      for (let i = 0; i < 5; i++) mod.recordRun(tmpDir, 'a', 'HEALTHY');
      const trend = mod.getTrend(tmpDir, 'a', 5);
      expect(trend.trending).toBe('up');
      expect(trend.scoreRecent).toBe(1.0);
      expect(trend.scorePrior).toBe(0.0);
    });
  });

  describe('getUnderperformers', () => {
    it('should return agents below threshold with enough runs', () => {
      for (let i = 0; i < 3; i++) mod.recordRun(tmpDir, 'bad-agent', 'FAILURE');
      for (let i = 0; i < 3; i++) mod.recordRun(tmpDir, 'good-agent', 'HEALTHY');

      const under = mod.getUnderperformers(tmpDir);
      expect(under).toHaveLength(1);
      expect(under[0].name).toBe('bad-agent');
    });
  });

  describe('getSummary', () => {
    it('should return all agents sorted by score', () => {
      mod.recordRun(tmpDir, 'agent-a', 'HEALTHY');
      mod.recordRun(tmpDir, 'agent-b', 'FAILURE');
      const summary = mod.getSummary(tmpDir);
      expect(summary).toHaveLength(2);
      expect(summary[0].name).toBe('agent-b'); // lower score first
    });
  });

  describe('recordRepair', () => {
    it('should increment repair count', () => {
      mod.recordRun(tmpDir, 'agent-1', 'FAILURE');
      mod.recordRepair(tmpDir, 'agent-1');
      const summary = mod.getSummary(tmpDir);
      const agent = summary.find(a => a.name === 'agent-1');
      expect(agent.repairCount).toBe(1);
    });
  });
});

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/baseline', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-baseline-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'baseline.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('saveBaseline and loadBaseline', () => {
    it('should round-trip save and load', () => {
      const result = { verdict: 'HEALTHY', summary: 'ok', data: { passed: 10 }, details: '' };
      mod.saveBaseline(tmpDir, 'Q1', result);

      const loaded = mod.loadBaseline(tmpDir, 'Q1');
      expect(loaded).not.toBeNull();
      expect(loaded.question_id).toBe('Q1');
      expect(loaded.result.verdict).toBe('HEALTHY');
      expect(loaded.timestamp).toBeTruthy();
    });

    it('should return null for non-existent baseline', () => {
      expect(mod.loadBaseline(tmpDir, 'Q99')).toBeNull();
    });
  });

  describe('diffAgainstBaseline', () => {
    it('should detect verdict regression', () => {
      const baseline = { result: { verdict: 'HEALTHY', data: {} } };
      const current = { verdict: 'FAILURE', data: {} };
      const diff = mod.diffAgainstBaseline(current, baseline);
      expect(diff.hasRegression).toBe(true);
      expect(diff.verdictChanged).toBe(true);
      expect(diff.verdictDelta).toBe('HEALTHY→FAILURE');
    });

    it('should detect no regression for same verdict', () => {
      const baseline = { result: { verdict: 'HEALTHY', data: {} } };
      const current = { verdict: 'HEALTHY', data: {} };
      const diff = mod.diffAgainstBaseline(current, baseline);
      expect(diff.hasRegression).toBe(false);
      expect(diff.verdictChanged).toBe(false);
    });

    it('should detect metric deltas', () => {
      const baseline = { result: { verdict: 'HEALTHY', data: { passed: 10 } } };
      const current = { verdict: 'HEALTHY', data: { passed: 8 } };
      const diff = mod.diffAgainstBaseline(current, baseline);
      expect(diff.metricDeltas.passed).toBeDefined();
      expect(diff.metricDeltas.passed.baseline).toBe(10);
      expect(diff.metricDeltas.passed.current).toBe(8);
    });

    it('should detect new issues', () => {
      const baseline = { result: { verdict: 'HEALTHY', data: { issues: ['old'] } } };
      const current = { verdict: 'HEALTHY', data: { issues: ['old', 'new'] } };
      const diff = mod.diffAgainstBaseline(current, baseline);
      expect(diff.newIssues).toContain('new');
      expect(diff.hasRegression).toBe(true);
    });
  });

  describe('listBaselines', () => {
    it('should list saved baselines', () => {
      mod.saveBaseline(tmpDir, 'Q1', { verdict: 'HEALTHY', data: {} });
      mod.saveBaseline(tmpDir, 'Q2', { verdict: 'WARNING', data: {} });
      const list = mod.listBaselines(tmpDir);
      expect(list).toHaveLength(2);
    });
  });

  describe('clearBaseline', () => {
    it('should remove a saved baseline', () => {
      mod.saveBaseline(tmpDir, 'Q1', { verdict: 'HEALTHY', data: {} });
      expect(mod.clearBaseline(tmpDir, 'Q1')).toBe(true);
      expect(mod.loadBaseline(tmpDir, 'Q1')).toBeNull();
    });

    it('should return false for non-existent baseline', () => {
      expect(mod.clearBaseline(tmpDir, 'Q99')).toBe(false);
    });
  });
});

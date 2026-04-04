import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/training-schema', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'training-schema.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('verdictToBinaryPass', () => {
    it('should return true for HEALTHY', () => {
      expect(mod.verdictToBinaryPass('HEALTHY')).toBe(true);
    });

    it('should return true for FIXED', () => {
      expect(mod.verdictToBinaryPass('FIXED')).toBe(true);
    });

    it('should return false for FAILURE', () => {
      expect(mod.verdictToBinaryPass('FAILURE')).toBe(false);
    });

    it('should return false for WARNING', () => {
      expect(mod.verdictToBinaryPass('WARNING')).toBe(false);
    });
  });

  describe('verdictToPartialCredit', () => {
    it('should return 1.0 for pass verdicts', () => {
      expect(mod.verdictToPartialCredit('HEALTHY')).toBe(1.0);
    });

    it('should return 0.0 for fail verdicts', () => {
      expect(mod.verdictToPartialCredit('FAILURE')).toBe(0.0);
    });

    it('should return partial value for WARNING', () => {
      expect(mod.verdictToPartialCredit('WARNING')).toBe(0.7);
    });

    it('should return 0.2 for unknown verdicts', () => {
      expect(mod.verdictToPartialCredit('MYSTERY')).toBe(0.2);
    });
  });

  describe('confidenceStrToFloat', () => {
    it('should return 0.5 for null', () => {
      expect(mod.confidenceStrToFloat(null)).toBe(0.5);
    });

    it('should return numeric value for number', () => {
      expect(mod.confidenceStrToFloat(0.8)).toBe(0.8);
    });

    it('should map string labels', () => {
      expect(mod.confidenceStrToFloat('high')).toBe(1.0);
      expect(mod.confidenceStrToFloat('medium')).toBe(0.7);
      expect(mod.confidenceStrToFloat('low')).toBe(0.3);
      expect(mod.confidenceStrToFloat('uncertain')).toBe(0.0);
    });

    it('should parse numeric strings', () => {
      expect(mod.confidenceStrToFloat('0.82')).toBe(0.82);
    });

    it('should clamp to [0, 1]', () => {
      expect(mod.confidenceStrToFloat('1.5')).toBe(1.0);
      expect(mod.confidenceStrToFloat('-0.5')).toBe(0.0);
    });
  });

  describe('computeTrajectoryScore', () => {
    it('should compute from eval_score when provided', () => {
      const score = mod.computeTrajectoryScore(90, 'HEALTHY', 'high');
      // base = 0.9, conf = 1.0 → 0.9 * 0.8 + 1.0 * 0.2 = 0.92
      expect(score).toBeCloseTo(0.92, 2);
    });

    it('should use partial credit as base when no eval_score', () => {
      const score = mod.computeTrajectoryScore(null, 'WARNING', 'medium');
      // partial(WARNING) = 0.7, conf(medium) = 0.7 → 0.7*0.8 + 0.7*0.2 = 0.7
      expect(score).toBeCloseTo(0.7, 2);
    });
  });

  describe('isSftEligible', () => {
    it('should return true for high-scoring non-blocked verdicts', () => {
      expect(mod.isSftEligible('HEALTHY', 0.9, false)).toBe(true);
    });

    it('should return false for low trajectory score', () => {
      expect(mod.isSftEligible('HEALTHY', 0.5, false)).toBe(false);
    });

    it('should return false for blocked verdicts', () => {
      expect(mod.isSftEligible('INCONCLUSIVE', 0.95, false)).toBe(false);
    });

    it('should return false when needs_human', () => {
      expect(mod.isSftEligible('HEALTHY', 0.95, true)).toBe(false);
    });
  });

  describe('verdictToCriticFlag', () => {
    it('should return good for pass verdicts', () => {
      expect(mod.verdictToCriticFlag('HEALTHY')).toBe('good');
    });

    it('should return mistake for fail verdicts', () => {
      expect(mod.verdictToCriticFlag('FAILURE')).toBe('mistake');
    });

    it('should return waste for INCONCLUSIVE', () => {
      expect(mod.verdictToCriticFlag('INCONCLUSIVE')).toBe('waste');
    });
  });
});

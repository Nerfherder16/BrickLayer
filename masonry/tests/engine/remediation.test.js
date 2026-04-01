import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/remediation', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'remediation.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('estimateRemediationFeasibility', () => {
    it('should return feasible for amnesty when projected passes threshold', () => {
      const result = mod.estimateRemediationFeasibility({
        actionType: 'amnesty',
        currentMean: 0.5,
        healthyThreshold: 0.6,
        floor: 0.7,
        nAffected: 10,
        corpusSize: 10,
      });
      expect(result.feasible).toBe(true);
      expect(result.projectedMean).toBeGreaterThanOrEqual(0.6);
      expect(result.delta).toBeGreaterThan(0);
    });

    it('should return not feasible when amnesty cannot reach threshold', () => {
      const result = mod.estimateRemediationFeasibility({
        actionType: 'amnesty',
        currentMean: 0.3,
        healthyThreshold: 0.9,
        floor: 0.4,
        nAffected: 2,
        corpusSize: 10,
      });
      expect(result.feasible).toBe(false);
    });

    it('should return zero delta when floor <= currentMean', () => {
      const result = mod.estimateRemediationFeasibility({
        actionType: 'amnesty',
        currentMean: 0.7,
        healthyThreshold: 0.6,
        floor: 0.5,
        nAffected: 5,
        corpusSize: 10,
      });
      expect(result.delta).toBe(0);
      expect(result.projectedMean).toBe(0.7);
    });

    it('should return null fields for unknown action type', () => {
      const result = mod.estimateRemediationFeasibility({
        actionType: 'unknown_action',
        currentMean: 0.5,
        healthyThreshold: 0.6,
      });
      expect(result.feasible).toBeNull();
      expect(result.projectedMean).toBeNull();
      expect(result.reason).toContain('unknown_action');
    });
  });
});

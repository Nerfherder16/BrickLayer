import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/local-inference', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'local-inference.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('classifyFailureType (heuristic fallback)', () => {
    it('should return null for HEALTHY verdict', () => {
      expect(mod.classifyFailureTypeHeuristic({ verdict: 'HEALTHY', summary: '', details: '' })).toBeNull();
    });

    it('should detect timeout', () => {
      expect(mod.classifyFailureTypeHeuristic({
        verdict: 'FAILURE', summary: 'ReadTimeoutError after 30s', details: '',
      })).toBe('timeout');
    });

    it('should detect tool_failure', () => {
      expect(mod.classifyFailureTypeHeuristic({
        verdict: 'FAILURE', summary: '', details: 'ModuleNotFoundError: No module named httpx',
      })).toBe('tool_failure');
    });

    it('should detect logic', () => {
      expect(mod.classifyFailureTypeHeuristic({
        verdict: 'FAILURE', summary: 'AssertionError: expected 200 got 404', details: '',
      })).toBe('logic');
    });

    it('should detect hallucination', () => {
      expect(mod.classifyFailureTypeHeuristic({
        verdict: 'INCONCLUSIVE', summary: 'agent assumed the cache was populated', details: '',
      })).toBe('hallucination');
    });

    it('should return unknown for unrecognized pattern', () => {
      expect(mod.classifyFailureTypeHeuristic({
        verdict: 'FAILURE', summary: 'something happened', details: 'no clear cause',
      })).toBe('unknown');
    });
  });

  describe('classifyConfidenceHeuristic', () => {
    it('should return high for concrete evidence', () => {
      expect(mod.classifyConfidenceHeuristic({
        verdict: 'HEALTHY', summary: '23 passed 0 failed', details: 'line 42',
      })).toBe('high');
    });

    it('should return uncertain for INCONCLUSIVE', () => {
      expect(mod.classifyConfidenceHeuristic({
        verdict: 'INCONCLUSIVE', summary: 'requires agent analysis', details: '',
      })).toBe('uncertain');
    });
  });
});

import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/performance', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'performance.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('_percentile', () => {
    it('should return 0 for empty array', () => {
      expect(mod._percentile([], 50)).toBe(0);
    });

    it('should return element for single-element array', () => {
      expect(mod._percentile([42], 50)).toBe(42);
      expect(mod._percentile([42], 95)).toBe(42);
    });

    it('should compute p50 correctly', () => {
      const values = [100, 200, 300, 400, 500];
      const p50 = mod._percentile(values, 50);
      expect(p50).toBe(300);
    });

    it('should compute p95 correctly for 20 elements', () => {
      const values = Array.from({ length: 20 }, (_, i) => (i + 1) * 10);
      const p95 = mod._percentile(values, 95);
      // p95 index: min(int(20 * 0.95), 19) = min(19, 19) = 19 → values[19] = 200
      expect(p95).toBe(200);
    });

    it('should handle unsorted input', () => {
      const values = [500, 100, 300, 200, 400];
      const p50 = mod._percentile(values, 50);
      expect(p50).toBe(300);
    });
  });
});

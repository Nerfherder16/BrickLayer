import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/benchmark', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'benchmark.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('_coerce', () => {
    it('should coerce null/none', () => {
      expect(mod._coerce('null')).toBeNull();
      expect(mod._coerce('none')).toBeNull();
      expect(mod._coerce('~')).toBeNull();
    });

    it('should coerce booleans', () => {
      expect(mod._coerce('true')).toBe(true);
      expect(mod._coerce('yes')).toBe(true);
      expect(mod._coerce('false')).toBe(false);
      expect(mod._coerce('no')).toBe(false);
    });

    it('should strip surrounding quotes', () => {
      expect(mod._coerce('"hello"')).toBe('hello');
      expect(mod._coerce("'world'")).toBe('world');
    });

    it('should coerce integers', () => {
      expect(mod._coerce('42')).toBe(42);
      expect(mod._coerce('0')).toBe(0);
    });

    it('should coerce floats', () => {
      expect(mod._coerce('3.14')).toBe(3.14);
      expect(mod._coerce('0.5')).toBe(0.5);
    });

    it('should return raw string for non-coercible', () => {
      expect(mod._coerce('hello')).toBe('hello');
    });
  });

  describe('_percentile', () => {
    it('should return single value for single-element array', () => {
      expect(mod._percentile([100], 95)).toBe(100);
    });

    it('should compute p50 correctly', () => {
      const values = [10, 20, 30, 40, 50];
      expect(mod._percentile(values, 50)).toBe(30);
    });

    it('should compute p95 correctly', () => {
      const values = [10, 20, 30, 40, 50];
      const p95 = mod._percentile(values, 95);
      expect(p95).toBeGreaterThanOrEqual(46);
      expect(p95).toBeLessThanOrEqual(50);
    });
  });

  describe('_parseSpecText', () => {
    it('should parse top-level key-value pairs', () => {
      const text = [
        'endpoint: "http://localhost:11434/api/generate"',
        'provider: "ollama"',
        'model: "qwen3:14b"',
        'timeout: 30',
      ].join('\n');
      const spec = mod._parseSpecText(text);
      expect(spec.endpoint).toBe('http://localhost:11434/api/generate');
      expect(spec.provider).toBe('ollama');
      expect(spec.timeout).toBe(30);
    });

    it('should parse nested sections', () => {
      const text = [
        'endpoint: "http://localhost:11434/api/generate"',
        'latency_test:',
        '  prompt: "Say hello."',
        '  runs: 5',
        '  threshold_ms: 10000',
      ].join('\n');
      const spec = mod._parseSpecText(text);
      expect(spec.latency_test).toBeDefined();
      expect(spec.latency_test.prompt).toBe('Say hello.');
      expect(spec.latency_test.runs).toBe(5);
      expect(spec.latency_test.threshold_ms).toBe(10000);
    });

    it('should parse list items in nested sections', () => {
      const text = [
        'accuracy_test:',
        '  prompts:',
        '    - input: "What is 2+2?"',
        '      expected_contains: "4"',
        '    - input: "Capital of France?"',
        '      expected_contains: "Paris"',
        '  pass_threshold: 0.8',
      ].join('\n');
      const spec = mod._parseSpecText(text);
      expect(spec.accuracy_test).toBeDefined();
      expect(spec.accuracy_test.prompts).toHaveLength(2);
      expect(spec.accuracy_test.prompts[0].input).toBe('What is 2+2?');
      expect(spec.accuracy_test.prompts[1].expected_contains).toBe('Paris');
      expect(spec.accuracy_test.pass_threshold).toBe(0.8);
    });

    it('should skip comments and empty lines', () => {
      const text = [
        '# This is a comment',
        '',
        'endpoint: "http://localhost"',
      ].join('\n');
      const spec = mod._parseSpecText(text);
      expect(spec.endpoint).toBe('http://localhost');
    });
  });

  describe('_extractSpec', () => {
    it('should return spec dict directly if present', () => {
      const question = { spec: { endpoint: 'http://test', provider: 'ollama' } };
      const spec = mod._extractSpec(question);
      expect(spec.endpoint).toBe('http://test');
    });

    it('should parse from test field', () => {
      const question = {
        test: 'endpoint: "http://test"\nprovider: "ollama"',
      };
      const spec = mod._extractSpec(question);
      expect(spec.endpoint).toBe('http://test');
    });

    it('should return null for empty question', () => {
      expect(mod._extractSpec({})).toBeNull();
    });
  });
});

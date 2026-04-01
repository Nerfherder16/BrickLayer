import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/simulate', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'simulate.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('_coerceValue', () => {
    it('should coerce booleans', () => {
      expect(mod._coerceValue('true')).toBe(true);
      expect(mod._coerceValue('yes')).toBe(true);
      expect(mod._coerceValue('false')).toBe(false);
      expect(mod._coerceValue('no')).toBe(false);
    });

    it('should coerce integers', () => {
      expect(mod._coerceValue('42')).toBe(42);
      expect(mod._coerceValue('0')).toBe(0);
    });

    it('should coerce floats', () => {
      expect(mod._coerceValue('3.14')).toBe(3.14);
    });

    it('should return raw string for non-coercible', () => {
      expect(mod._coerceValue('hello')).toBe('hello');
    });
  });

  describe('_parseSimulateSpec', () => {
    it('should parse basic spec', () => {
      const text = [
        'script: simulate.py',
        'stress_param: churn_rate',
        'stress_range: [0.05, 0.50]',
        'stress_steps: 10',
        'timeout: 60',
      ].join('\n');
      const spec = mod._parseSimulateSpec(text);
      expect(spec.script).toBe('simulate.py');
      expect(spec.stress_param).toBe('churn_rate');
      expect(spec.stress_range).toEqual([0.05, 0.50]);
      expect(spec.stress_steps).toBe(10);
      expect(spec.timeout).toBe(60);
    });

    it('should parse params block', () => {
      const text = [
        'script: simulate.py',
        'params:',
        '  churn_rate: 0.15',
        '  months: 24',
        '  enabled: true',
      ].join('\n');
      const spec = mod._parseSimulateSpec(text);
      expect(spec.params.churn_rate).toBe(0.15);
      expect(spec.params.months).toBe(24);
      expect(spec.params.enabled).toBe(true);
    });

    it('should use defaults for missing fields', () => {
      const spec = mod._parseSimulateSpec('');
      expect(spec.script).toBe('simulate.py');
      expect(spec.stress_param).toBeNull();
      expect(spec.stress_range).toBeNull();
      expect(spec.stress_steps).toBe(8);
      expect(spec.baseline_check).toBe(true);
      expect(spec.timeout).toBe(30);
      expect(spec.params).toEqual({});
    });

    it('should handle baseline_check false', () => {
      const spec = mod._parseSimulateSpec('baseline_check: false');
      expect(spec.baseline_check).toBe(false);
    });

    it('should skip code fences', () => {
      const text = '```yaml\nscript: test.py\n```';
      const spec = mod._parseSimulateSpec(text);
      expect(spec.script).toBe('test.py');
    });

    it('should enforce minimum stress_steps of 2', () => {
      const spec = mod._parseSimulateSpec('stress_steps: 1');
      expect(spec.stress_steps).toBe(2);
    });
  });

  describe('_patchScriptSource', () => {
    it('should replace existing parameter lines', () => {
      const source = 'churn_rate = 0.10\nmonths = 12\n';
      const patched = mod._patchScriptSource(source, { churn_rate: 0.25 });
      expect(patched).toContain('churn_rate = 0.25');
      expect(patched).toContain('months = 12');
    });

    it('should preserve trailing comments', () => {
      const source = 'churn_rate = 0.10  # max 1.0\n';
      const patched = mod._patchScriptSource(source, { churn_rate: 0.50 });
      expect(patched).toContain('churn_rate = 0.5');
      expect(patched).toContain('# max 1.0');
    });

    it('should append missing parameters', () => {
      const source = 'existing = 1\n';
      const patched = mod._patchScriptSource(source, { new_param: 42 });
      expect(patched).toContain('existing = 1');
      expect(patched).toContain('new_param = 42');
      expect(patched).toContain('simulate runner overrides');
    });

    it('should format boolean values as Python True/False', () => {
      const source = 'enabled = False\n';
      const patched = mod._patchScriptSource(source, { enabled: true });
      expect(patched).toContain('enabled = True');
    });

    it('should format string values with quotes', () => {
      const source = 'name = "old"\n';
      const patched = mod._patchScriptSource(source, { name: 'new' });
      expect(patched).toMatch(/name = ['"]new['"]/);
    });
  });

  describe('_formatValue', () => {
    it('should format booleans as Python literals', () => {
      expect(mod._formatValue(true)).toBe('True');
      expect(mod._formatValue(false)).toBe('False');
    });

    it('should format strings with quotes', () => {
      const result = mod._formatValue('hello');
      expect(result).toMatch(/['"]hello['"]/);
    });

    it('should format numbers as strings', () => {
      expect(mod._formatValue(42)).toBe('42');
      expect(mod._formatValue(3.14)).toBe('3.14');
    });
  });
});

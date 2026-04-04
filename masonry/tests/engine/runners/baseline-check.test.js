import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/baseline-check', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'baseline-check.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('_parseBaselineCheckSpec', () => {
    it('should parse spec from dict', () => {
      const question = {
        spec: {
          question_id: 'D1.1',
          current_result_file: '.bl-baseline/D1.1_latest.json',
          project_dir: '/tmp/proj',
          fail_on_verdict_change: true,
          fail_on_metric_regression: { p95_ms: 50 },
        },
      };
      const result = mod._parseBaselineCheckSpec(question);
      expect(result.question_id).toBe('D1.1');
      expect(result.current_result_file).toBe('.bl-baseline/D1.1_latest.json');
      expect(result.project_dir).toBe('/tmp/proj');
      expect(result.fail_on_verdict_change).toBe(true);
      expect(result.fail_on_metric_regression).toEqual({ p95_ms: 50 });
    });

    it('should parse spec from text', () => {
      const question = {
        test: [
          'question_id: D1.1',
          'current_result_file: .bl-baseline/D1.1_latest.json',
          'fail_on_verdict_change: false',
          'fail_on_metric_regression:',
          '  p95_ms: 50',
          '  pass_rate: 10',
        ].join('\n'),
      };
      const result = mod._parseBaselineCheckSpec(question);
      expect(result.question_id).toBe('D1.1');
      expect(result.fail_on_verdict_change).toBe(false);
      expect(result.fail_on_metric_regression.p95_ms).toBe(50);
      expect(result.fail_on_metric_regression.pass_rate).toBe(10);
    });

    it('should default to true for fail_on_verdict_change', () => {
      const question = { spec: { question_id: 'Q1' } };
      const result = mod._parseBaselineCheckSpec(question);
      expect(result.fail_on_verdict_change).toBe(true);
      expect(result.fail_on_metric_regression).toEqual({});
    });

    it('should handle "false" string for fail_on_verdict_change in dict', () => {
      const question = { spec: { question_id: 'Q1', fail_on_verdict_change: 'false' } };
      const result = mod._parseBaselineCheckSpec(question);
      expect(result.fail_on_verdict_change).toBe(false);
    });

    it('should return defaults for empty question', () => {
      const result = mod._parseBaselineCheckSpec({});
      expect(result.question_id).toBeNull();
      expect(result.fail_on_verdict_change).toBe(true);
      expect(result.fail_on_metric_regression).toEqual({});
    });
  });
});

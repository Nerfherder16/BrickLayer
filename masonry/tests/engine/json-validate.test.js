import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/json-validate', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'json-validate.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('validateFindingJson', () => {
    it('should return [null, null] when no JSON block found', () => {
      const [parsed, error] = mod.validateFindingJson('just plain text');
      expect(parsed).toBeNull();
      expect(error).toBeNull();
    });

    it('should parse valid JSON with required fields', () => {
      const text = 'preamble\n```json\n{"verdict":"HEALTHY","question_id":"Q1"}\n```\npost';
      const [parsed, error] = mod.validateFindingJson(text);
      expect(error).toBeNull();
      expect(parsed.verdict).toBe('HEALTHY');
      expect(parsed.question_id).toBe('Q1');
    });

    it('should return error for malformed JSON', () => {
      const text = '```json\n{bad json}\n```';
      const [parsed, error] = mod.validateFindingJson(text);
      expect(parsed).toBeNull();
      expect(error).toContain('JSON parse error');
    });

    it('should return error for missing required fields', () => {
      const text = '```json\n{"verdict":"HEALTHY"}\n```';
      const [parsed, error] = mod.validateFindingJson(text);
      expect(parsed).toBeNull();
      expect(error).toContain('missing required fields');
      expect(error).toContain('question_id');
    });

    it('should use the LAST json block when multiple exist', () => {
      const text = '```json\n{"verdict":"OLD","question_id":"Q0"}\n```\ntext\n```json\n{"verdict":"NEW","question_id":"Q1"}\n```';
      const [parsed, error] = mod.validateFindingJson(text);
      expect(error).toBeNull();
      expect(parsed.verdict).toBe('NEW');
    });
  });

  describe('isRetry', () => {
    it('should return true for PENDING_RETRY', () => {
      expect(mod.isRetry('PENDING_RETRY')).toBe(true);
    });

    it('should return true for FORMAT-RETRY', () => {
      expect(mod.isRetry('FORMAT-RETRY')).toBe(true);
    });

    it('should return false for PENDING', () => {
      expect(mod.isRetry('PENDING')).toBe(false);
    });
  });
});

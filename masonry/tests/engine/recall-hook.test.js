import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/recall-hook', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'recall-hook.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('extractRecallPayload', () => {
    it('should extract from JSON block', () => {
      const text = 'preamble\n```json\n{"verdict":"FAILURE","summary":"test failed"}\n```\npost';
      const payload = mod.extractRecallPayload(text, 'agent-1', 'Q1', 'myproject');
      expect(payload).not.toBeNull();
      expect(payload.content).toContain('agent-1');
      expect(payload.content).toContain('Q1');
      expect(payload.content).toContain('FAILURE');
      expect(payload.domain).toBe('myproject-bricklayer');
      expect(payload.importance).toBe(0.9);
      expect(payload.tags).toContain('verdict:FAILURE');
    });

    it('should use higher importance for FAILURE verdicts', () => {
      const text = '```json\n{"verdict":"FAILURE","summary":"bad"}\n```';
      const payload = mod.extractRecallPayload(text, 'a', 'Q1', 'p');
      expect(payload.importance).toBe(0.9);
    });

    it('should use lower importance for HEALTHY verdicts', () => {
      const text = '```json\n{"verdict":"HEALTHY","summary":"ok"}\n```';
      const payload = mod.extractRecallPayload(text, 'a', 'Q1', 'p');
      expect(payload.importance).toBe(0.7);
    });

    it('should fall back to **Verdict** line when no JSON', () => {
      const text = '**Verdict**: WARNING\n\n## Evidence\nSome evidence text here';
      const payload = mod.extractRecallPayload(text, 'agent-2', 'Q2', 'proj');
      expect(payload).not.toBeNull();
      expect(payload.content).toContain('WARNING');
    });

    it('should return null when no verdict found', () => {
      const text = 'just some random text with no verdict';
      expect(mod.extractRecallPayload(text, 'a', 'Q1', 'p')).toBeNull();
    });

    it('should handle INCONCLUSIVE as high importance', () => {
      const text = '```json\n{"verdict":"INCONCLUSIVE","summary":"dunno"}\n```';
      const payload = mod.extractRecallPayload(text, 'a', 'Q1', 'p');
      expect(payload.importance).toBe(0.9);
    });

    it('should use simulation_result as summary fallback', () => {
      const text = '```json\n{"verdict":"HEALTHY","simulation_result":"sim ok"}\n```';
      const payload = mod.extractRecallPayload(text, 'a', 'Q1', 'p');
      expect(payload.content).toContain('sim ok');
    });
  });
});

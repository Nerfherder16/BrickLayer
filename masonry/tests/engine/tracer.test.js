import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/tracer', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-tracer-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'tracer.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('traced', () => {
    it('should wrap a function and capture trace', () => {
      const tracesFile = path.join(tmpDir, 'traces.jsonl');
      const fn = (q) => ({ verdict: 'HEALTHY', summary: 'ok', data: {}, details: '' });
      const wrapped = mod.traced(fn, tmpDir);

      const result = wrapped({ id: 'Q1', mode: 'agent', title: 'Test question' });
      expect(result.verdict).toBe('HEALTHY');

      const traces = fs.readFileSync(tracesFile, 'utf8').trim().split('\n').map(JSON.parse);
      expect(traces).toHaveLength(1);
      expect(traces[0].verdict).toBe('HEALTHY');
      expect(traces[0].question_id).toBe('Q1');
      expect(traces[0].latency_ms).toBeGreaterThanOrEqual(0);
    });

    it('should capture exception and re-throw', () => {
      const tracesFile = path.join(tmpDir, 'traces.jsonl');
      const fn = () => { throw new Error('boom'); };
      const wrapped = mod.traced(fn, tmpDir);

      expect(() => wrapped({ id: 'Q2', mode: 'test' })).toThrow('boom');

      const traces = fs.readFileSync(tracesFile, 'utf8').trim().split('\n').map(JSON.parse);
      expect(traces).toHaveLength(1);
      expect(traces[0].verdict).toBe('INCONCLUSIVE');
      expect(traces[0].error_type).toBe('tool_failure');
    });
  });

  describe('loadTraces', () => {
    it('should return empty array for non-existent file', () => {
      expect(mod.loadTraces(tmpDir)).toEqual([]);
    });

    it('should load valid JSONL traces', () => {
      const tracesFile = path.join(tmpDir, 'traces.jsonl');
      fs.writeFileSync(tracesFile, '{"verdict":"HEALTHY","question_id":"Q1"}\n{"verdict":"FAILURE","question_id":"Q2"}\n');
      const traces = mod.loadTraces(tmpDir);
      expect(traces).toHaveLength(2);
      expect(traces[0].verdict).toBe('HEALTHY');
      expect(traces[1].verdict).toBe('FAILURE');
    });

    it('should skip malformed JSON lines', () => {
      const tracesFile = path.join(tmpDir, 'traces.jsonl');
      fs.writeFileSync(tracesFile, '{"verdict":"OK"}\nbad json\n{"verdict":"FAIL"}\n');
      const traces = mod.loadTraces(tmpDir);
      expect(traces).toHaveLength(2);
    });
  });
});

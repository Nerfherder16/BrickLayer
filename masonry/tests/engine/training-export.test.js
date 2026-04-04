import { describe, it, expect, beforeEach, afterEach, beforeAll } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/training-export', () => {
  let mod, tmpDir;

  beforeAll(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'training-export.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-export-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('parseFinding', () => {
    it('should extract verdict and confidence from finding text', () => {
      const text = '**Verdict**: FAILURE\n**Confidence**: 0.8\n**Mode**: diagnose\n## Summary\nBroken\n';
      const result = mod.parseFinding(text);
      expect(result.verdict).toBe('FAILURE');
      expect(result.confidence).toBe(0.8);
      expect(result.mode).toBe('diagnose');
    });

    it('should return defaults for empty text', () => {
      const result = mod.parseFinding('');
      expect(result.verdict).toBe('INCONCLUSIVE');
    });
  });

  describe('makeTrace', () => {
    it('should build a trace record', () => {
      const trace = mod.makeTrace({
        questionId: 'Q1',
        taskDomain: 'test',
        taskDescription: 'Test task',
        agentName: 'agent-1',
        tracerRecord: { thought: 'thinking', result_summary: 'done', latency_ms: 100 },
        scoredEntry: { score: 85 },
        verdict: 'HEALTHY',
        confidenceRaw: 'high',
        needsHuman: false,
        wave: 1,
        mode: 'diagnose',
      });

      expect(trace.task_id).toBe('Q1');
      expect(trace.trajectory_score).toBeGreaterThan(0);
      expect(trace.sft_eligible).toBeDefined();
      expect(trace.steps).toHaveLength(1);
    });
  });

  describe('exportProject', () => {
    it('should return empty for missing traces.jsonl', () => {
      expect(mod.exportProject(tmpDir, {})).toEqual([]);
    });

    it('should export traces from a project dir', () => {
      // Create traces.jsonl
      const trace = { question_id: 'Q1', thought: 'test', domain: 'test' };
      fs.writeFileSync(path.join(tmpDir, 'traces.jsonl'), JSON.stringify(trace) + '\n');

      // Create finding
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: HEALTHY\n**Confidence**: 0.9\n**Mode**: diagnose\n## Summary\nOK\n'
      );

      const traces = mod.exportProject(tmpDir, {});
      expect(traces.length).toBeGreaterThan(0);
      expect(traces[0].task_id).toBe('Q1');
    });
  });
});

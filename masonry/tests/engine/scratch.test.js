import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/scratch', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-scratch-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'scratch.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('parseSignals', () => {
    it('should parse WATCH signal', () => {
      const text = 'some text [SIGNAL: WATCH -- check latency] more text';
      const signals = mod.parseSignals(text);
      expect(signals).toHaveLength(1);
      expect(signals[0].type).toBe('WATCH');
      expect(signals[0].signal).toBe('check latency');
    });

    it('should parse multiple signals', () => {
      const text = '[SIGNAL: WATCH -- a] and [SIGNAL: BLOCK -- b] also [SIGNAL: DATA -- c]';
      const signals = mod.parseSignals(text);
      expect(signals).toHaveLength(3);
    });

    it('should ignore unknown signal types', () => {
      const text = '[SIGNAL: INVALID -- nope]';
      expect(mod.parseSignals(text)).toHaveLength(0);
    });
  });

  describe('renderScratch', () => {
    it('should render rows as markdown table', () => {
      const rows = [
        { signal: 'high latency', type: 'WATCH', source: 'Q1', date: '2024-01' },
      ];
      const table = mod.renderScratch(rows);
      expect(table).toContain('| # | Signal | Type | Source | Date |');
      expect(table).toContain('| 1 | high latency | WATCH | Q1 | 2024-01 |');
    });
  });

  describe('save and load scratch', () => {
    it('should round-trip save and load', () => {
      const scratchPath = path.join(tmpDir, 'scratch.md');
      const rows = [
        { signal: 'issue A', type: 'WATCH', source: 'Q1', date: '2024-01' },
        { signal: 'blocked B', type: 'BLOCK', source: 'Q2', date: '2024-02' },
      ];
      mod.saveScratch(scratchPath, rows);
      const loaded = mod.loadScratch(scratchPath);
      expect(loaded).toHaveLength(2);
      expect(loaded[0].signal).toBe('issue A');
      expect(loaded[1].type).toBe('BLOCK');
    });

    it('should return empty array for non-existent file', () => {
      expect(mod.loadScratch(path.join(tmpDir, 'nope.md'))).toEqual([]);
    });
  });

  describe('trimScratch', () => {
    it('should remove RESOLVED first when over cap', () => {
      const rows = [
        { signal: 'a', type: 'RESOLVED', source: '', date: '' },
        { signal: 'b', type: 'WATCH', source: '', date: '' },
        { signal: 'c', type: 'DATA', source: '', date: '' },
      ];
      const trimmed = mod.trimScratch(rows, 2);
      expect(trimmed).toHaveLength(2);
      expect(trimmed.find(r => r.type === 'RESOLVED')).toBeUndefined();
    });

    it('should remove DATA after RESOLVED exhausted', () => {
      const rows = [
        { signal: 'a', type: 'WATCH', source: '', date: '' },
        { signal: 'b', type: 'BLOCK', source: '', date: '' },
        { signal: 'c', type: 'DATA', source: '', date: '' },
      ];
      const trimmed = mod.trimScratch(rows, 2);
      expect(trimmed).toHaveLength(2);
      expect(trimmed.find(r => r.type === 'DATA')).toBeUndefined();
    });

    it('should never remove WATCH or BLOCK', () => {
      const rows = [
        { signal: 'a', type: 'WATCH', source: '', date: '' },
        { signal: 'b', type: 'BLOCK', source: '', date: '' },
        { signal: 'c', type: 'WATCH', source: '', date: '' },
      ];
      const trimmed = mod.trimScratch(rows, 2);
      // Can't trim below — all are WATCH/BLOCK
      expect(trimmed).toHaveLength(3);
    });
  });
});

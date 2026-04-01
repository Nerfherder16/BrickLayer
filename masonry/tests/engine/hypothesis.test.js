import { describe, it, expect, beforeAll, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/hypothesis', () => {
  let mod, tmpDir;

  beforeAll(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'hypothesis.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-hyp-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('_getWaveNumber', () => {
    it('should return 1 for empty text', () => {
      expect(mod._getWaveNumber('')).toBe(1);
    });

    it('should detect highest wave number from question IDs', () => {
      const text = '## Q3.1 [DIAGNOSE] Title\n## Q5.2 [FIX] Title\n## Q2.1 [AUDIT] Title\n';
      expect(mod._getWaveNumber(text)).toBe(5);
    });

    it('should handle BL 2.0 IDs like D8.1', () => {
      const text = '## D8.1 [DIAGNOSE] Title\n## D3.2 [FIX] Title\n';
      expect(mod._getWaveNumber(text)).toBe(8);
    });
  });

  describe('_getExistingIds', () => {
    it('should return empty set for no matches', () => {
      expect(mod._getExistingIds('no questions here').size).toBe(0);
    });

    it('should extract all question IDs', () => {
      const text = '## Q1.1 [DIAGNOSE] Title\n## Q2.3 [FIX] Other\n';
      const ids = mod._getExistingIds(text);
      expect(ids.has('Q1.1')).toBe(true);
      expect(ids.has('Q2.3')).toBe(true);
    });
  });

  describe('_buildFindingsSummary', () => {
    it('should return no results for missing file', () => {
      const result = mod._buildFindingsSummary(path.join(tmpDir, 'missing.tsv'));
      expect(result).toContain('No results');
    });

    it('should return no results for header-only file', () => {
      fs.writeFileSync(path.join(tmpDir, 'results.tsv'), 'QID\tVerdict\tSummary\n');
      const result = mod._buildFindingsSummary(path.join(tmpDir, 'results.tsv'));
      expect(result).toContain('No results');
    });

    it('should categorize findings by verdict', () => {
      const tsv = 'QID\tVerdict\tSummary\tTimestamp\n'
        + 'Q1.1\tFAILURE\tBroken thing\t2024-01-01\n'
        + 'Q1.2\tWARNING\tSlow thing\t2024-01-01\n'
        + 'Q1.3\tHEALTHY\tAll good\t2024-01-01\n';
      fs.writeFileSync(path.join(tmpDir, 'results.tsv'), tsv);
      const result = mod._buildFindingsSummary(path.join(tmpDir, 'results.tsv'));
      expect(result).toContain('FAILURES');
      expect(result).toContain('WARNINGS');
      expect(result).toContain('Q1.1');
    });
  });

  describe('_parseQuestionBlocks', () => {
    it('should extract valid blocks for the given wave', () => {
      const raw = '---\n## Q5.1 [DIAGNOSE] Title\n**Status**: PENDING\n---\n## Q5.2 [FIX] Other\n**Status**: PENDING\n---';
      const blocks = mod._parseQuestionBlocks(raw, 5);
      expect(blocks).toHaveLength(2);
    });

    it('should skip blocks from wrong wave', () => {
      const raw = '---\n## Q3.1 [DIAGNOSE] Title\n**Status**: PENDING\n---';
      const blocks = mod._parseQuestionBlocks(raw, 5);
      expect(blocks).toHaveLength(0);
    });

    it('should add Status: PENDING if missing', () => {
      const raw = '---\n## Q5.1 [DIAGNOSE] Title\n**Mode**: agent\n---';
      const blocks = mod._parseQuestionBlocks(raw, 5);
      expect(blocks).toHaveLength(1);
      expect(blocks[0]).toContain('**Status**: PENDING');
    });
  });
});

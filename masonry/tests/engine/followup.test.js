import { describe, it, expect, beforeAll, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/followup', () => {
  let mod, tmpDir;

  beforeAll(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'followup.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-followup-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('_isLeafId', () => {
    it('should return false for top-level IDs', () => {
      expect(mod._isLeafId('Q2.4')).toBe(false);
      expect(mod._isLeafId('Q8.1')).toBe(false);
      expect(mod._isLeafId('QG1.2')).toBe(false);
    });

    it('should return true for sub-question IDs', () => {
      expect(mod._isLeafId('Q2.4.1')).toBe(true);
      expect(mod._isLeafId('Q2.4.1.2')).toBe(true);
    });

    it('should handle BL 2.0 IDs', () => {
      expect(mod._isLeafId('D5.1')).toBe(false);
      expect(mod._isLeafId('D5.1.1')).toBe(true);
      expect(mod._isLeafId('F4.3')).toBe(false);
    });
  });

  describe('_getExistingSubIds', () => {
    it('should return empty for missing file', () => {
      expect(mod._getExistingSubIds(path.join(tmpDir, 'nope.md'), 'Q2.4')).toEqual([]);
    });

    it('should find existing sub-question IDs', () => {
      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '## Q2.4 [DIAGNOSE] Parent\n## Q2.4.1 [DIAGNOSE] Sub1\n## Q2.4.2 [FIX] Sub2\n',
      );
      const ids = mod._getExistingSubIds(path.join(tmpDir, 'questions.md'), 'Q2.4');
      expect(ids).toHaveLength(2);
      expect(ids).toContain('Q2.4.1');
      expect(ids).toContain('Q2.4.2');
    });
  });

  describe('_nextSubIndex', () => {
    it('should return 1 for no existing subs', () => {
      expect(mod._nextSubIndex(path.join(tmpDir, 'nope.md'), 'Q2.4')).toBe(1);
    });

    it('should return next index after existing subs', () => {
      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '## Q2.4 [DIAGNOSE] Parent\n## Q2.4.1 [DIAGNOSE] Sub1\n## Q2.4.2 [FIX] Sub2\n',
      );
      expect(mod._nextSubIndex(path.join(tmpDir, 'questions.md'), 'Q2.4')).toBe(3);
    });
  });

  describe('_parseFollowupBlocks', () => {
    it('should parse valid blocks and renumber', () => {
      const raw = '---\n## Q2.4.99 [DIAGNOSE] Title\n**Status**: PENDING\n**Derived from**: Q2.4\n---';
      const blocks = mod._parseFollowupBlocks(raw, 'Q2.4', 1);
      expect(blocks).toHaveLength(1);
      expect(blocks[0]).toContain('## Q2.4.1');
    });

    it('should skip blocks missing required fields', () => {
      const raw = '---\n## Q2.4.1 [DIAGNOSE] Title\nNo status or derived\n---';
      const blocks = mod._parseFollowupBlocks(raw, 'Q2.4', 1);
      expect(blocks).toHaveLength(0);
    });

    it('should handle multiple blocks with sequential numbering', () => {
      const raw = [
        '---',
        '## Q2.4.1 [DIAGNOSE] First',
        '**Status**: PENDING',
        '**Derived from**: Q2.4',
        '---',
        '## Q2.4.2 [DIAGNOSE] Second',
        '**Status**: PENDING',
        '**Derived from**: Q2.4',
        '---',
      ].join('\n');
      const blocks = mod._parseFollowupBlocks(raw, 'Q2.4', 3);
      expect(blocks).toHaveLength(2);
      expect(blocks[0]).toContain('## Q2.4.3');
      expect(blocks[1]).toContain('## Q2.4.4');
    });
  });
});

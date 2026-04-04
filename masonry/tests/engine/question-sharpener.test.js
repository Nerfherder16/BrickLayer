import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/question-sharpener', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-sharpener-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'question-sharpener.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('_extractFindingMode', () => {
    it('should extract mode from finding content', () => {
      expect(mod._extractFindingMode('**Mode**: diagnose\n')).toBe('diagnose');
    });

    it('should return null when no mode', () => {
      expect(mod._extractFindingMode('no mode here')).toBeNull();
    });
  });

  describe('_findingKeyword', () => {
    it('should extract slug from ## Summary', () => {
      const text = '## Summary\nHigh latency detected in queue\n## Evidence';
      expect(mod._findingKeyword(text)).toBe('high-latency-detected');
    });

    it('should return inconclusive when no summary', () => {
      expect(mod._findingKeyword('no summary section')).toBe('inconclusive');
    });
  });

  describe('sharpenPendingQuestions', () => {
    it('should return empty when no questions.md', () => {
      expect(mod.sharpenPendingQuestions(tmpDir)).toEqual([]);
    });

    it('should sharpen matching PENDING questions', () => {
      // Create findings dir with an INCONCLUSIVE finding
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n**Mode**: diagnose\n## Summary\nNeed more data\n'
      );

      // Create questions.md with a matching PENDING question
      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '### Q1 — Test Question\n**Status**: PENDING\n**Mode**: diagnose\n'
      );

      const modified = mod.sharpenPendingQuestions(tmpDir);
      expect(modified).toContain('Q1');

      const text = fs.readFileSync(path.join(tmpDir, 'questions.md'), 'utf8');
      expect(text).toContain('[narrowed:');
      expect(text).toContain('**Sharpened**: true');
    });

    it('should not sharpen already-sharpened questions', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n**Mode**: diagnose\n## Summary\nTest\n'
      );

      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '### Q1 — Test\n**Status**: PENDING\n**Sharpened**: true\n**Mode**: diagnose\n'
      );

      expect(mod.sharpenPendingQuestions(tmpDir)).toEqual([]);
    });

    it('should respect dry_run', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n**Mode**: diagnose\n## Summary\nTest\n'
      );

      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '### Q1 — Test\n**Status**: PENDING\n**Mode**: diagnose\n'
      );

      const modified = mod.sharpenPendingQuestions(tmpDir, 5, true);
      expect(modified).toContain('Q1');

      // File should not be modified in dry run
      const text = fs.readFileSync(path.join(tmpDir, 'questions.md'), 'utf8');
      expect(text).not.toContain('[narrowed:');
    });
  });
});

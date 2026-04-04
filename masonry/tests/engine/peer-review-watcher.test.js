import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/peer-review-watcher', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-prw-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'peer-review-watcher.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('parseFinding', () => {
    it('should return null for missing file', () => {
      expect(mod.parseFinding(path.join(tmpDir, 'nope.md'))).toBeNull();
    });

    it('should return null for file without peer review section', () => {
      fs.writeFileSync(path.join(tmpDir, 'Q1.md'), '**Verdict**: HEALTHY\n');
      expect(mod.parseFinding(path.join(tmpDir, 'Q1.md'))).toBeNull();
    });

    it('should extract fields from finding with peer review', () => {
      const content = [
        '**Verdict**: INCONCLUSIVE',
        '',
        '## Peer Review',
        '**Verdict**: INCONCLUSIVE',
        '**Quality Score**: 0.25',
      ].join('\n');
      fs.writeFileSync(path.join(tmpDir, 'Q1.md'), content);
      const info = mod.parseFinding(path.join(tmpDir, 'Q1.md'));
      expect(info.qid).toBe('Q1');
      expect(info.primary_verdict).toBe('INCONCLUSIVE');
      expect(info.quality_score).toBe(0.25);
    });
  });

  describe('process', () => {
    it('should return empty for missing findings dir', () => {
      expect(mod.process(tmpDir)).toEqual([]);
    });

    it('should skip non-INCONCLUSIVE findings', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: HEALTHY\n\n## Peer Review\n**Verdict**: HEALTHY\n**Quality Score**: 0.1\n',
      );
      expect(mod.process(tmpDir)).toEqual([]);
    });

    it('should skip findings with quality >= threshold', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n\n## Peer Review\n**Verdict**: INCONCLUSIVE\n**Quality Score**: 0.8\n',
      );
      expect(mod.process(tmpDir)).toEqual([]);
    });

    it('should requeue low-quality INCONCLUSIVE with questions.md', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n\n## Peer Review\n**Verdict**: INCONCLUSIVE\n**Quality Score**: 0.2\n',
      );
      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '## Q1 [DIAGNOSE] Original question\n**Hypothesis**: Test thing\n**Mode**: diagnose\n**Status**: DONE\n',
      );

      const requeued = mod.process(tmpDir);
      expect(requeued).toContain('Q1');

      const text = fs.readFileSync(path.join(tmpDir, 'questions.md'), 'utf8');
      expect(text).toContain('Q1-RQ1');
      expect(text).toContain('REQUEUE');
    });

    it('should not requeue if already requeued', () => {
      const findingsDir = path.join(tmpDir, 'findings');
      fs.mkdirSync(findingsDir);
      fs.writeFileSync(
        path.join(findingsDir, 'Q1.md'),
        '**Verdict**: INCONCLUSIVE\n\n## Peer Review\n**Verdict**: INCONCLUSIVE\n**Quality Score**: 0.2\n',
      );
      fs.writeFileSync(
        path.join(tmpDir, 'questions.md'),
        '## Q1 [DIAGNOSE] Original\n**Hypothesis**: Test\n**Mode**: diagnose\n## Q1-RQ1 [PENDING]\nAlready here\n',
      );

      const requeued = mod.process(tmpDir);
      expect(requeued).toEqual([]);
    });
  });
});

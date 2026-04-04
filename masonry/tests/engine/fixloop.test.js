import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/fixloop', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-fixloop-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'fixloop.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('runFixLoop', () => {
    it('should return original result if verdict is not FAILURE', () => {
      const result = { verdict: 'HEALTHY', summary: 'ok' };
      const out = mod.runFixLoop(
        { id: 'Q1', title: 'test', mode: 'agent' },
        result,
        path.join(tmpDir, 'Q1.md'),
        { fixAgent: () => false, reRunner: () => result },
      );
      expect(out.verdict).toBe('HEALTHY');
    });

    it('should attempt fix and return HEALTHY on success', () => {
      const findingPath = path.join(tmpDir, 'Q1.md');
      fs.writeFileSync(findingPath, '# Finding');

      const failResult = { verdict: 'FAILURE', summary: 'bad' };
      const fixedResult = { verdict: 'HEALTHY', summary: 'fixed' };

      const out = mod.runFixLoop(
        { id: 'Q1', title: 'test', mode: 'agent' },
        failResult,
        findingPath,
        {
          fixAgent: () => true,
          reRunner: () => fixedResult,
          maxAttempts: 2,
        },
      );
      expect(out.verdict).toBe('HEALTHY');

      const content = fs.readFileSync(findingPath, 'utf8');
      expect(content).toContain('RESOLVED');
    });

    it('should exhaust attempts and return original on all failures', () => {
      const findingPath = path.join(tmpDir, 'Q1.md');
      fs.writeFileSync(findingPath, '# Finding');

      const failResult = { verdict: 'FAILURE', summary: 'bad' };

      const out = mod.runFixLoop(
        { id: 'Q1', title: 'test', mode: 'agent' },
        failResult,
        findingPath,
        {
          fixAgent: () => false,
          reRunner: () => failResult,
          maxAttempts: 2,
        },
      );
      expect(out.verdict).toBe('FAILURE');

      const content = fs.readFileSync(findingPath, 'utf8');
      expect(content).toContain('EXHAUSTED');
    });
  });
});

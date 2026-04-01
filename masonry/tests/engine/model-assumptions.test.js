import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/model-assumptions', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-assumptions-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'model-assumptions.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('ensureExists', () => {
    it('should create model_assumptions.md with template', () => {
      const filePath = mod.ensureExists(tmpDir);
      expect(fs.existsSync(filePath)).toBe(true);
      const content = fs.readFileSync(filePath, 'utf8');
      expect(content).toContain('# Model Assumptions Log');
    });

    it('should not overwrite if already exists', () => {
      const maPath = path.join(tmpDir, 'model_assumptions.md');
      fs.writeFileSync(maPath, 'custom content');
      mod.ensureExists(tmpDir);
      expect(fs.readFileSync(maPath, 'utf8')).toBe('custom content');
    });
  });

  describe('appendEntry', () => {
    it('should append an entry to the file', () => {
      mod.ensureExists(tmpDir);
      mod.appendEntry(tmpDir, 'test-agent', 'Added X', 'file.py', 'reason Y', 'impact Z');
      const content = fs.readFileSync(path.join(tmpDir, 'model_assumptions.md'), 'utf8');
      expect(content).toContain('test-agent');
      expect(content).toContain('Added X');
      expect(content).toContain('**Changed**: file.py');
      expect(content).toContain('**Why**: reason Y');
      expect(content).toContain('**Impact**: impact Z');
    });
  });
});

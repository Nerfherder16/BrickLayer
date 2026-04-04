import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/pointer-sentinel', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-pointer-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'pointer-sentinel.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('shouldFirePointer', () => {
    it('should not fire at count 0', () => {
      expect(mod.shouldFirePointer(0)).toBe(false);
    });

    it('should fire at multiples of 8', () => {
      expect(mod.shouldFirePointer(8)).toBe(true);
      expect(mod.shouldFirePointer(16)).toBe(true);
      expect(mod.shouldFirePointer(24)).toBe(true);
    });

    it('should not fire at non-multiples of 8', () => {
      expect(mod.shouldFirePointer(1)).toBe(false);
      expect(mod.shouldFirePointer(7)).toBe(false);
      expect(mod.shouldFirePointer(9)).toBe(false);
    });

    it('should respect custom interval', () => {
      expect(mod.shouldFirePointer(5, 5)).toBe(true);
      expect(mod.shouldFirePointer(3, 5)).toBe(false);
    });
  });

  describe('getLatestCheckpoint', () => {
    it('should return null for non-existent directory', () => {
      expect(mod.getLatestCheckpoint(path.join(tmpDir, 'nope'))).toBeNull();
    });

    it('should return null for empty directory', () => {
      const cpDir = path.join(tmpDir, 'checkpoints');
      fs.mkdirSync(cpDir);
      expect(mod.getLatestCheckpoint(cpDir)).toBeNull();
    });

    it('should return latest checkpoint by wave then question number', () => {
      const cpDir = path.join(tmpDir, 'checkpoints');
      fs.mkdirSync(cpDir);
      fs.writeFileSync(path.join(cpDir, 'wave1-q3.md'), 'cp1');
      fs.writeFileSync(path.join(cpDir, 'wave2-q1.md'), 'cp2');
      fs.writeFileSync(path.join(cpDir, 'wave1-q5.md'), 'cp3');

      const latest = mod.getLatestCheckpoint(cpDir);
      expect(latest).toContain('wave2-q1.md');
    });
  });
});

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/claim', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-claim-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'claim.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('cmdClaim', () => {
    it('should claim an unclaimed question', () => {
      expect(mod.cmdClaim(tmpDir, 'Q1', 'worker-1')).toBe('CLAIMED');
    });

    it('should return TAKEN for already claimed question', () => {
      mod.cmdClaim(tmpDir, 'Q1', 'worker-1');
      expect(mod.cmdClaim(tmpDir, 'Q1', 'worker-2')).toBe('TAKEN');
    });

    it('should allow claiming after release', () => {
      mod.cmdClaim(tmpDir, 'Q1', 'worker-1');
      mod.cmdRelease(tmpDir, 'Q1');
      expect(mod.cmdClaim(tmpDir, 'Q1', 'worker-2')).toBe('CLAIMED');
    });
  });

  describe('cmdRelease', () => {
    it('should release a claimed question', () => {
      mod.cmdClaim(tmpDir, 'Q1', 'worker-1');
      expect(mod.cmdRelease(tmpDir, 'Q1')).toBe('OK');
    });

    it('should return OK for unclaimed question', () => {
      expect(mod.cmdRelease(tmpDir, 'Q99')).toBe('OK');
    });
  });

  describe('cmdComplete', () => {
    it('should mark question as done', () => {
      mod.cmdClaim(tmpDir, 'Q1', 'worker-1');
      expect(mod.cmdComplete(tmpDir, 'Q1', 'HEALTHY')).toBe('OK');
      // Should now be TAKEN (status DONE)
      expect(mod.cmdClaim(tmpDir, 'Q1', 'worker-2')).toBe('TAKEN');
    });

    it('should work for unclaimed question', () => {
      expect(mod.cmdComplete(tmpDir, 'Q5', 'FAILURE')).toBe('OK');
    });
  });
});

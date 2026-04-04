import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/model-version', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-model-version-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'model-version.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return no-model when neither file exists', () => {
    expect(mod.computeModelHash(tmpDir)).toBe('no-model');
  });

  it('should return a 12-char hex hash when simulate.py exists', () => {
    fs.writeFileSync(path.join(tmpDir, 'simulate.py'), 'print("sim")');
    const hash = mod.computeModelHash(tmpDir);
    expect(hash).toMatch(/^[0-9a-f]{12}$/);
  });

  it('should return a 12-char hex hash when constants.py exists', () => {
    fs.writeFileSync(path.join(tmpDir, 'constants.py'), 'X = 1');
    const hash = mod.computeModelHash(tmpDir);
    expect(hash).toMatch(/^[0-9a-f]{12}$/);
  });

  it('should return different hashes for different content', () => {
    fs.writeFileSync(path.join(tmpDir, 'simulate.py'), 'v1');
    const hash1 = mod.computeModelHash(tmpDir);

    fs.writeFileSync(path.join(tmpDir, 'simulate.py'), 'v2');
    const hash2 = mod.computeModelHash(tmpDir);

    expect(hash1).not.toBe(hash2);
  });

  it('embedInFinding should append model hash if not present', () => {
    const content = '## Finding\nSome text';
    const result = mod.embedInFinding(content, 'abc123def456');
    expect(result).toContain('**Model hash**: abc123def456');
  });

  it('embedInFinding should not duplicate if already present', () => {
    const content = '## Finding\n**Model hash**: existing123';
    const result = mod.embedInFinding(content, 'abc123def456');
    expect(result).toBe(content);
  });
});

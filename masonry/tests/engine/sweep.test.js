import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/sweep — validateSweepParameter', () => {
  let sweep, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-sweep-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'sweep.js');
    delete require.cache[modPath];
    sweep = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should fail when simulate.py does not exist', () => {
    const [ok, err] = sweep.validateSweepParameter(tmpDir, 'param');
    expect(ok).toBe(false);
    expect(err).toContain('SWEEP_BLOCKED');
    expect(err).toContain('not found');
  });

  it('should fail when no SCENARIO PARAMETERS block exists', () => {
    fs.writeFileSync(path.join(tmpDir, 'simulate.py'), 'def run(): pass\n');
    const [ok, err] = sweep.validateSweepParameter(tmpDir, 'param');
    expect(ok).toBe(false);
    expect(err).toContain('SCENARIO PARAMETERS');
  });

  it('should fail when parameter not found in block', () => {
    fs.writeFileSync(path.join(tmpDir, 'simulate.py'),
      '# SCENARIO PARAMETERS\nrate = 0.5\nfee = 100\n');
    const [ok, err] = sweep.validateSweepParameter(tmpDir, 'missing_param');
    expect(ok).toBe(false);
    expect(err).toContain("'missing_param' not found");
  });

  it('should succeed when parameter exists in SCENARIO PARAMETERS', () => {
    fs.writeFileSync(path.join(tmpDir, 'simulate.py'),
      '# SCENARIO PARAMETERS\nrate = 0.5\nfee = 100\n');
    const [ok, err] = sweep.validateSweepParameter(tmpDir, 'rate');
    expect(ok).toBe(true);
    expect(err).toBe('');
  });
});

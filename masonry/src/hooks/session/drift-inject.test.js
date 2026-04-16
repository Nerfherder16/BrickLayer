import { describe, it, expect, afterEach } from 'vitest';
import { getDriftSummary } from './drift-inject.js';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const tempDirs = [];

function makeTempDir() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'drift-inject-test-'));
  tempDirs.push(dir);
  return dir;
}

afterEach(() => {
  for (const dir of tempDirs.splice(0)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe('getDriftSummary', () => {
  it('returns prefixed content when drift-summary.txt has content', () => {
    const dir = makeTempDir();
    fs.mkdirSync(path.join(dir, '.autopilot'));
    fs.writeFileSync(
      path.join(dir, '.autopilot', 'drift-summary.txt'),
      '✓ CLEAN — 7 files matched',
      'utf8'
    );
    expect(getDriftSummary(dir)).toBe('[Last build] ✓ CLEAN — 7 files matched');
  });

  it('returns null when drift-summary.txt does not exist', () => {
    const dir = makeTempDir();
    expect(getDriftSummary(dir)).toBeNull();
  });

  it('returns null when drift-summary.txt is empty', () => {
    const dir = makeTempDir();
    fs.mkdirSync(path.join(dir, '.autopilot'));
    fs.writeFileSync(path.join(dir, '.autopilot', 'drift-summary.txt'), '', 'utf8');
    expect(getDriftSummary(dir)).toBeNull();
  });
});

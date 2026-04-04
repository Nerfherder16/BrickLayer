import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/runners/quality — analyzeQualityPatterns', () => {
  let mod, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-quality-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'quality.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should detect structlog mismatch as FAILURE', () => {
    const filePath = path.join(tmpDir, 'test.py');
    fs.writeFileSync(filePath, [
      'import logging',
      'import structlog',
      'logger = logging.getLogger()',
      'logger.error("fail", extra_kwarg=True)',
    ].join('\n'));

    const [verdict, summary] = mod._analyzeQualityPatterns(
      { hypothesis: 'structlog stdlib mismatch' },
      [filePath],
      fs.readFileSync(filePath, 'utf8'),
      [],
      4,
    );
    expect(verdict).toBe('FAILURE');
    expect(summary).toContain('Logger mismatch');
  });

  it('should detect utcnow as FAILURE', () => {
    const filePath = path.join(tmpDir, 'dates.py');
    fs.writeFileSync(filePath, 'from datetime import datetime\nt = datetime.utcnow()\n');

    const [verdict] = mod._analyzeQualityPatterns(
      { hypothesis: 'utcnow deprecation' },
      [filePath],
      fs.readFileSync(filePath, 'utf8'),
      [],
      2,
    );
    expect(verdict).toBe('FAILURE');
  });

  it('should return HEALTHY when no utcnow found', () => {
    const filePath = path.join(tmpDir, 'clean.py');
    fs.writeFileSync(filePath, 'from datetime import datetime, timezone\nt = datetime.now(timezone.utc)\n');

    const [verdict] = mod._analyzeQualityPatterns(
      { hypothesis: 'utcnow deprecation' },
      [filePath],
      fs.readFileSync(filePath, 'utf8'),
      [],
      2,
    );
    expect(verdict).toBe('HEALTHY');
  });

  it('should return INCONCLUSIVE as fallback', () => {
    const filePath = path.join(tmpDir, 'x.py');
    fs.writeFileSync(filePath, 'print("hello")\n');

    const [verdict] = mod._analyzeQualityPatterns(
      { hypothesis: 'something unrecognized' },
      [filePath],
      fs.readFileSync(filePath, 'utf8'),
      [],
      1,
    );
    expect(verdict).toBe('INCONCLUSIVE');
  });

  it('should note missing files in fallback', () => {
    const [verdict, summary] = mod._analyzeQualityPatterns(
      { hypothesis: 'some check' },
      ['/nonexistent.py'],
      '',
      ['/nonexistent.py'],
      0,
    );
    expect(verdict).toBe('INCONCLUSIVE');
    expect(summary).toContain('Missing');
  });
});

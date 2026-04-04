import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/correctness — parsePytestOutput', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'correctness.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return HEALTHY when all tests pass', () => {
    const result = mod._parsePytestOutput('10 passed in 1.5s');
    expect(result.verdict).toBe('HEALTHY');
    expect(result.data.passed).toBe(10);
    expect(result.data.failed).toBe(0);
  });

  it('should return FAILURE when tests fail', () => {
    const result = mod._parsePytestOutput('8 passed, 2 failed in 3.0s');
    expect(result.verdict).toBe('FAILURE');
    expect(result.data.passed).toBe(8);
    expect(result.data.failed).toBe(2);
  });

  it('should return FAILURE on errors', () => {
    const result = mod._parsePytestOutput('3 passed, 1 error in 1.0s');
    expect(result.verdict).toBe('FAILURE');
    expect(result.data.errors).toBe(1);
  });

  it('should return INCONCLUSIVE when no tests ran', () => {
    const result = mod._parsePytestOutput('no tests ran');
    expect(result.verdict).toBe('INCONCLUSIVE');
  });

  it('should return INCONCLUSIVE for "collected 0 items"', () => {
    const result = mod._parsePytestOutput('collected 0 items');
    expect(result.verdict).toBe('INCONCLUSIVE');
  });
});

describe('engine/runners/correctness — extractTestPaths', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'correctness.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should extract pytest path from test field', () => {
    const paths = mod._extractTestPaths('Run `pytest tests/test_core.py -v`');
    expect(paths).toContain('tests/test_core.py');
  });

  it('should return null for test field with no paths', () => {
    const paths = mod._extractTestPaths('Check that everything works');
    expect(paths).toBeNull();
  });
});

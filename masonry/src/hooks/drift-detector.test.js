import { describe, it, expect } from 'vitest';
import { parseSpecFiles, computeDrift } from './drift-detector.js';

describe('parseSpecFiles', () => {
  it('extracts paths from fenced code block', () => {
    const text = [
      '## Files',
      '```',
      'masonry/src/foo.js',
      'masonry/src/bar.ts',
      '```',
    ].join('\n');
    const result = parseSpecFiles(text);
    expect(result).toContain('masonry/src/foo.js');
    expect(result).toContain('masonry/src/bar.ts');
  });

  it('extracts paths from ## Files section bullet list', () => {
    const text = [
      '## Files to modify',
      '- masonry/src/hooks/drift-detector.js',
      '- masonry/src/brainstorm/server.cjs',
    ].join('\n');
    const result = parseSpecFiles(text);
    expect(result).toContain('masonry/src/hooks/drift-detector.js');
    expect(result).toContain('masonry/src/brainstorm/server.cjs');
  });

  it('deduplicates repeated paths', () => {
    const text = [
      '## Files',
      '- masonry/src/foo.js',
      '- masonry/src/foo.js',
      '```',
      'masonry/src/foo.js',
      '```',
    ].join('\n');
    const result = parseSpecFiles(text);
    const count = result.filter((p) => p === 'masonry/src/foo.js').length;
    expect(count).toBe(1);
  });
});

describe('computeDrift', () => {
  it('detects drift when files differ', () => {
    const result = computeDrift(['a.js', 'b.js'], ['b.js', 'c.js']);
    expect(result.matched).toEqual(['b.js']);
    expect(result.onlyInSpec).toEqual(['a.js']);
    expect(result.onlyInDiff).toEqual(['c.js']);
    expect(result.verdict).toBe('DRIFT_DETECTED');
  });

  it('returns CLEAN when claimed and changed are identical', () => {
    const result = computeDrift(['a.js', 'b.js'], ['a.js', 'b.js']);
    expect(result.verdict).toBe('CLEAN');
    expect(result.onlyInSpec).toHaveLength(0);
    expect(result.onlyInDiff).toHaveLength(0);
  });

  it('returns CLEAN for empty inputs', () => {
    const result = computeDrift([], []);
    expect(result.verdict).toBe('CLEAN');
  });
});

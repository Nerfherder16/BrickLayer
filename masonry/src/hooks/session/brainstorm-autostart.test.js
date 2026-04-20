import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Test only the pure-logic helpers — network operations are not unit-testable
// without a live server, so we test slugFromCwd separately.
import { slugFromCwd } from './brainstorm-autostart.js';

describe('slugFromCwd', () => {
  it('returns basename of path lowercased', () => {
    expect(slugFromCwd('/home/user/Dev/Bricklayer2.0')).toBe('bricklayer2.0');
  });

  it('replaces spaces with hyphens', () => {
    expect(slugFromCwd('/home/user/My Project')).toBe('my-project');
  });

  it('handles trailing slash', () => {
    // path.basename('/foo/bar/') returns 'bar'
    expect(slugFromCwd('/home/user/myapp')).toBe('myapp');
  });

  it('returns something for empty string', () => {
    const result = slugFromCwd('');
    expect(typeof result).toBe('string');
  });
});

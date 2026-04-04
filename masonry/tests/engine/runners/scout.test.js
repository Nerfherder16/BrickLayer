import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/scout', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'scout.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should export module marker', () => {
    expect(mod.RUNNER_NAME).toBe('scout');
  });

  it('should export a placeholder run function', () => {
    expect(typeof mod.runScout).toBe('function');
  });

  it('should return INCONCLUSIVE when invoked without tmux', () => {
    const result = mod.runScout({});
    expect(result.verdict).toBe('INCONCLUSIVE');
    expect(result.summary).toContain('runtime');
  });
});

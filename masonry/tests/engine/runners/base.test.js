import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/base — registry', () => {
  let base;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'base.js');
    delete require.cache[modPath];
    base = require(modPath);
    base._reset();
  });

  it('should register and retrieve a runner', () => {
    const mockRunner = (q) => ({ verdict: 'HEALTHY', summary: '', data: {}, details: '' });
    base.register('test-mode', mockRunner);
    expect(base.get('test-mode')).toBe(mockRunner);
  });

  it('should return null for unregistered mode', () => {
    expect(base.get('nonexistent')).toBeNull();
  });

  it('should throw for non-callable runner', () => {
    expect(() => base.register('bad', 'not a function')).toThrow('must be a function');
  });

  it('should return sorted registered modes', () => {
    base.register('zz', () => ({}));
    base.register('aa', () => ({}));
    base.register('mm', () => ({}));
    expect(base.registeredModes()).toEqual(['aa', 'mm', 'zz']);
  });

  it('should store and retrieve RunnerInfo', () => {
    const info = { mode: 'http', description: 'HTTP runner', targetTypes: ['api'] };
    base.register('http', () => ({}), info);
    expect(base.describe('http')).toEqual(info);
  });

  it('should return null info for runner without metadata', () => {
    base.register('bare', () => ({}));
    expect(base.describe('bare')).toBeNull();
  });

  it('should list all runners with metadata sorted by mode', () => {
    base.register('zz', () => ({}), { mode: 'zz', description: 'Z runner' });
    base.register('aa', () => ({}), { mode: 'aa', description: 'A runner' });
    const list = base.listRunners();
    expect(list).toHaveLength(2);
    expect(list[0].mode).toBe('aa');
    expect(list[1].mode).toBe('zz');
  });

  it('should generate runner menu', () => {
    base.register('http', () => ({}), {
      mode: 'http',
      description: 'HTTP runner',
      syntaxSummary: 'GET {url}',
    });
    const menu = base.runnerMenu();
    expect(menu).toContain('`http`');
    expect(menu).toContain('HTTP runner');
    expect(menu).toContain('Syntax:');
  });

  it('should return fallback message when no runners have metadata', () => {
    expect(base.runnerMenu()).toBe('No runner metadata available.');
  });
});

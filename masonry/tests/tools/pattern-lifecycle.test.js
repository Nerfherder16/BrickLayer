import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

// Redirect cwd so lifecycle.json lands in a temp dir
const origCwd = process.cwd;
let tempDir;
let mod;

function load() {
  // Clear require cache so module picks up new cwd each time
  const modPath = new URL('../../src/tools/pattern-lifecycle.js', import.meta.url).pathname;
  delete require.cache[require.resolve(modPath)];
  return require(modPath);
}

beforeEach(() => {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pl-vitest-'));
  process.cwd = () => tempDir;
  mod = load();
});

afterEach(() => {
  process.cwd = origCwd;
  fs.rmSync(tempDir, { recursive: true, force: true });
});

describe('pattern-lifecycle — schemas', () => {
  it('exports an array of 4 schemas with correct names', () => {
    const { schemas } = mod;
    expect(Array.isArray(schemas)).toBe(true);
    expect(schemas).toHaveLength(4);
    const names = schemas.map(s => s.name);
    expect(names).toContain('masonry_pattern_use');
    expect(names).toContain('masonry_pattern_quality');
    expect(names).toContain('masonry_pattern_promote');
    expect(names).toContain('masonry_pattern_demote');
  });
});

describe('pattern-lifecycle — masonry_pattern_use', () => {
  it('creates entry on first call with usage_count=1', () => {
    const r = mod.handle('masonry_pattern_use', { pattern_id: 'p1' });
    expect(r.success).toBe(true);
    expect(r.pattern_id).toBe('p1');
    expect(r.usage_count).toBe(1);
  });

  it('increments usage_count on second call', () => {
    mod.handle('masonry_pattern_use', { pattern_id: 'p1' });
    const r = mod.handle('masonry_pattern_use', { pattern_id: 'p1' });
    expect(r.usage_count).toBe(2);
  });
});

describe('pattern-lifecycle — masonry_pattern_quality', () => {
  it('promotes when usage_count>=3 and quality>=0.6', () => {
    mod.handle('masonry_pattern_use', { pattern_id: 'p2' });
    mod.handle('masonry_pattern_use', { pattern_id: 'p2' });
    mod.handle('masonry_pattern_use', { pattern_id: 'p2' });
    const r = mod.handle('masonry_pattern_quality', { pattern_id: 'p2', quality: 0.8 });
    expect(r.tier).toBe('promoted');
    expect(r.promoted).toBe(true);
  });

  it('marks stale when usage_count<=1 and quality<0.4', () => {
    mod.handle('masonry_pattern_use', { pattern_id: 'p3' });
    const r = mod.handle('masonry_pattern_quality', { pattern_id: 'p3', quality: 0.2 });
    expect(r.tier).toBe('stale');
  });
});

describe('pattern-lifecycle — promote and demote', () => {
  it('masonry_pattern_promote forces tier to promoted', () => {
    const r = mod.handle('masonry_pattern_promote', { pattern_id: 'p4' });
    expect(r.success).toBe(true);
    expect(r.tier).toBe('promoted');
  });

  it('masonry_pattern_demote forces tier to stale', () => {
    mod.handle('masonry_pattern_promote', { pattern_id: 'p5' });
    const r = mod.handle('masonry_pattern_demote', { pattern_id: 'p5' });
    expect(r.success).toBe(true);
    expect(r.tier).toBe('stale');
  });

  it('unknown tool throws', () => {
    expect(() => mod.handle('masonry_pattern_noop', {}))
      .toThrow(/pattern-lifecycle: unknown tool masonry_pattern_noop/);
  });
});

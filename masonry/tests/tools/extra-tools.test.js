import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { handle, schemas } = require('../../src/tools/extra-tools');

describe('extra-tools — schemas', () => {
  it('exports exactly 2 schemas', () => {
    expect(Array.isArray(schemas)).toBe(true);
    expect(schemas).toHaveLength(2);
  });

  it('includes masonry_daemon and masonry_checkpoint', () => {
    const names = schemas.map(s => s.name);
    expect(names).toContain('masonry_daemon');
    expect(names).toContain('masonry_checkpoint');
  });

  it('each schema has description and inputSchema', () => {
    for (const s of schemas) {
      expect(s.description.length).toBeGreaterThan(10);
      expect(s.inputSchema?.type).toBe('object');
    }
  });
});

describe('extra-tools — masonry_checkpoint', () => {
  let tmpDir;
  let masonryDir;

  beforeAll(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-extra-tools-'));
    masonryDir = path.join(tmpDir, '.masonry');
    fs.mkdirSync(masonryDir);
  });

  afterAll(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('returns empty array when no checkpoints file exists', () => {
    const r = handle('masonry_checkpoint', { project_path: tmpDir });
    expect(r.success).toBe(true);
    expect(r.checkpoints).toEqual([]);
    expect(r.total).toBe(0);
  });

  it('returns all checkpoints from file', () => {
    const cpFile = path.join(masonryDir, 'checkpoints.jsonl');
    const entries = [
      { ts: '2026-01-01T00:00:00Z', file: 'src/a.ts', branch: 'main', diff_summary: 'add fn', tool: 'Write', session_id: 's1' },
      { ts: '2026-01-01T00:01:00Z', file: 'src/b.ts', branch: 'main', diff_summary: 'fix bug', tool: 'Edit', session_id: 's1' },
      { ts: '2026-01-01T00:02:00Z', file: 'src/c.ts', branch: 'main', diff_summary: 'refactor', tool: 'Edit', session_id: 's1' },
    ];
    fs.writeFileSync(cpFile, entries.map(e => JSON.stringify(e)).join('\n') + '\n', 'utf8');

    const r = handle('masonry_checkpoint', { project_path: tmpDir });
    expect(r.success).toBe(true);
    expect(r.total).toBe(3);
    expect(r.checkpoints).toHaveLength(3);
  });

  it('respects limit parameter', () => {
    const r = handle('masonry_checkpoint', { project_path: tmpDir, limit: 2 });
    expect(r.checkpoints).toHaveLength(2);
    expect(r.checkpoints[0].file).toBe('src/b.ts');
  });

  it('throws on unknown tool', () => {
    expect(() => handle('masonry_unknown', {})).toThrow(/unknown tool/);
  });
});

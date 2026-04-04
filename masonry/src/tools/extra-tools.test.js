'use strict';

const assert = require('assert');
const path = require('path');
const fs = require('fs');
const os = require('os');

const { handle, schemas } = require('./extra-tools');

// ── schema tests ─────────────────────────────────────────────────────────────

assert(Array.isArray(schemas), 'schemas must be an array');
assert.strictEqual(schemas.length, 2, 'should export 2 schemas');
const names = schemas.map((s) => s.name);
assert(names.includes('masonry_daemon'), 'masonry_daemon schema missing');
assert(names.includes('masonry_checkpoint'), 'masonry_checkpoint schema missing');
for (const s of schemas) {
  assert(s.description && s.description.length > 10, `${s.name} needs a description`);
  assert(s.inputSchema && s.inputSchema.type === 'object', `${s.name} inputSchema must be object`);
}

// ── masonry_checkpoint tests ──────────────────────────────────────────────────

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-extra-tools-'));
const masonryDir = path.join(tmpDir, '.masonry');
fs.mkdirSync(masonryDir);

// empty checkpoints
let result = handle('masonry_checkpoint', { project_path: tmpDir });
assert.strictEqual(result.success, true, 'empty: should succeed');
assert.deepStrictEqual(result.checkpoints, [], 'empty: should return []');
assert.strictEqual(result.total, 0, 'empty: total should be 0');

// write checkpoint entries
const cpFile = path.join(masonryDir, 'checkpoints.jsonl');
const entries = [
  { ts: '2026-01-01T00:00:00Z', file: 'src/a.ts', branch: 'main', diff_summary: 'add fn', tool: 'Write', session_id: 's1' },
  { ts: '2026-01-01T00:01:00Z', file: 'src/b.ts', branch: 'main', diff_summary: 'fix bug', tool: 'Edit', session_id: 's1' },
  { ts: '2026-01-01T00:02:00Z', file: 'src/c.ts', branch: 'main', diff_summary: 'refactor', tool: 'Edit', session_id: 's1' },
];
fs.writeFileSync(cpFile, entries.map((e) => JSON.stringify(e)).join('\n') + '\n', 'utf8');

result = handle('masonry_checkpoint', { project_path: tmpDir });
assert.strictEqual(result.success, true, '3 entries: should succeed');
assert.strictEqual(result.total, 3, '3 entries: total');
assert.strictEqual(result.checkpoints.length, 3, '3 entries: returned count');

// limit
result = handle('masonry_checkpoint', { project_path: tmpDir, limit: 2 });
assert.strictEqual(result.checkpoints.length, 2, 'limit=2 should return 2');
assert.strictEqual(result.checkpoints[0].file, 'src/b.ts', 'limit=2 should return last 2');

// unknown tool throws
assert.throws(() => handle('masonry_unknown', {}), /unknown tool/, 'unknown tool should throw');

// cleanup
fs.rmSync(tmpDir, { recursive: true, force: true });

console.log('extra-tools tests: ALL PASS');

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ── Test isolation: redirect cwd so lifecycle.json lands in a temp dir ──────
const origCwd = process.cwd;
let tempDir;

function setup() {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pl-test-'));
  process.cwd = () => tempDir;
  // Clear require cache so the module picks up the new cwd on each test
  delete require.cache[require.resolve('./pattern-lifecycle')];
}

function teardown() {
  process.cwd = origCwd;
  try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch (_) {}
}

function load() {
  delete require.cache[require.resolve('./pattern-lifecycle')];
  return require('./pattern-lifecycle');
}

// ── 1. schemas exports array of 4 with correct names ────────────────────────
{
  setup();
  const { schemas } = load();
  assert.ok(Array.isArray(schemas), 'schemas must be an array');
  assert.strictEqual(schemas.length, 4, 'schemas must have 4 entries');
  const names = schemas.map(s => s.name);
  assert.ok(names.includes('masonry_pattern_use'), 'missing masonry_pattern_use');
  assert.ok(names.includes('masonry_pattern_quality'), 'missing masonry_pattern_quality');
  assert.ok(names.includes('masonry_pattern_promote'), 'missing masonry_pattern_promote');
  assert.ok(names.includes('masonry_pattern_demote'), 'missing masonry_pattern_demote');
  teardown();
  console.log('PASS 1: schemas exports array of 4 with correct names');
}

// ── 2. masonry_pattern_use creates entry on first call, increments on second ─
{
  setup();
  const { handle } = load();
  const r1 = handle('masonry_pattern_use', { pattern_id: 'p1' });
  assert.strictEqual(r1.success, true);
  assert.strictEqual(r1.pattern_id, 'p1');
  assert.strictEqual(r1.usage_count, 1);

  const r2 = handle('masonry_pattern_use', { pattern_id: 'p1' });
  assert.strictEqual(r2.usage_count, 2);
  teardown();
  console.log('PASS 2: masonry_pattern_use creates entry on first call, increments on second');
}

// ── 3. masonry_pattern_quality promotes when usage_count>=3 && quality>=0.6 ─
{
  setup();
  const { handle } = load();
  // Reach usage_count=3
  handle('masonry_pattern_use', { pattern_id: 'p2' });
  handle('masonry_pattern_use', { pattern_id: 'p2' });
  handle('masonry_pattern_use', { pattern_id: 'p2' });
  const r = handle('masonry_pattern_quality', { pattern_id: 'p2', quality: 0.8 });
  assert.strictEqual(r.tier, 'promoted', `expected promoted, got ${r.tier}`);
  assert.strictEqual(r.promoted, true);
  teardown();
  console.log('PASS 3: masonry_pattern_quality promotes when usage_count>=3 && quality>=0.6');
}

// ── 4. masonry_pattern_quality marks stale when usage_count<=1 && quality<0.4 ─
{
  setup();
  const { handle } = load();
  handle('masonry_pattern_use', { pattern_id: 'p3' });
  const r = handle('masonry_pattern_quality', { pattern_id: 'p3', quality: 0.2 });
  assert.strictEqual(r.tier, 'stale', `expected stale, got ${r.tier}`);
  teardown();
  console.log('PASS 4: masonry_pattern_quality marks stale when usage_count<=1 && quality<0.4');
}

// ── 5. masonry_pattern_promote forces tier to "promoted" ────────────────────
{
  setup();
  const { handle } = load();
  const r = handle('masonry_pattern_promote', { pattern_id: 'p4' });
  assert.strictEqual(r.success, true);
  assert.strictEqual(r.tier, 'promoted');
  teardown();
  console.log('PASS 5: masonry_pattern_promote forces tier to "promoted"');
}

// ── 6. masonry_pattern_demote forces tier to "stale" ────────────────────────
{
  setup();
  const { handle } = load();
  handle('masonry_pattern_promote', { pattern_id: 'p5' });
  const r = handle('masonry_pattern_demote', { pattern_id: 'p5' });
  assert.strictEqual(r.success, true);
  assert.strictEqual(r.tier, 'stale');
  teardown();
  console.log('PASS 6: masonry_pattern_demote forces tier to "stale"');
}

// ── 7. unknown tool throws ───────────────────────────────────────────────────
{
  setup();
  const { handle } = load();
  assert.throws(
    () => handle('masonry_pattern_noop', {}),
    /pattern-lifecycle: unknown tool masonry_pattern_noop/
  );
  teardown();
  console.log('PASS 7: unknown tool throws');
}

console.log('\nAll 7 tests passed.');

'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Use a temp dir as project root for all tests
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hotpaths-test-'));

// Re-require fresh instance pointing to our temp dir
const { recordEdit, getTopPaths, injectContext, getSlug, getHotpathsFile } = require('./hotpaths');

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  PASS: ${name}`);
    passed++;
  } catch (e) {
    console.log(`  FAIL: ${name} — ${e.message}`);
    failed++;
  }
}

// Test: getSlug has no colons or slashes
test('getSlug has no colons or slashes', () => {
  const slug = getSlug('C:/Users/trg16/Dev/MyProject');
  assert(!slug.includes(':'), 'slug contains colon');
  assert(!slug.includes('/'), 'slug contains forward slash');
  assert(!slug.includes('\\'), 'slug contains backslash');
  assert(slug.length > 0, 'slug is empty');
});

// Test: recordEdit increments counter
test('recordEdit increments counter', () => {
  const projRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hp-rec-'));
  recordEdit(projRoot, 'src/foo.py');
  recordEdit(projRoot, 'src/foo.py');
  recordEdit(projRoot, 'src/bar.py');
  const top = getTopPaths(projRoot, 10);
  const fooEntry = top.find(e => e.file === 'src/foo.py');
  assert(fooEntry, 'foo.py not found in top paths');
  assert.strictEqual(fooEntry.count, 2, `expected count 2, got ${fooEntry.count}`);
});

// Test: getTopPaths returns sorted descending
test('getTopPaths returns results sorted descending by count', () => {
  const projRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hp-sort-'));
  recordEdit(projRoot, 'a.py');
  recordEdit(projRoot, 'b.py');
  recordEdit(projRoot, 'b.py');
  recordEdit(projRoot, 'b.py');
  recordEdit(projRoot, 'c.py');
  recordEdit(projRoot, 'c.py');
  const top = getTopPaths(projRoot, 10);
  assert.strictEqual(top[0].file, 'b.py', `expected b.py first, got ${top[0].file}`);
  assert(top[0].count >= top[1].count, 'not sorted descending');
});

// Test: getTopPaths returns [] if no data
test('getTopPaths returns [] if no data', () => {
  const projRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hp-empty-'));
  const top = getTopPaths(projRoot, 5);
  assert(Array.isArray(top), 'not an array');
  assert.strictEqual(top.length, 0, `expected 0 entries, got ${top.length}`);
});

// Test: injectContext returns '' if no data
test('injectContext returns empty string if no data', () => {
  const projRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hp-noctx-'));
  const result = injectContext(projRoot);
  assert.strictEqual(result, '', `expected empty string, got '${result}'`);
});

// Test: injectContext returns formatted string with data
test('injectContext returns formatted string with data', () => {
  const projRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'hp-ctx-'));
  recordEdit(projRoot, 'bl/sweep.py');
  recordEdit(projRoot, 'bl/sweep.py');
  recordEdit(projRoot, 'bl/findings.py');
  const result = injectContext(projRoot);
  assert(result.includes('[Hot paths]'), 'missing [Hot paths] header');
  assert(result.includes('bl/sweep.py'), 'missing sweep.py entry');
  assert(result.includes('2 edits'), 'missing edit count');
});

// Cleanup
try { fs.rmSync(tmpRoot, { recursive: true, force: true }); } catch {}

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);

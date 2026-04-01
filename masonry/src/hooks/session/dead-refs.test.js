'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');

const { scanFile, scanAll, formatWarnings, DEAD_REFS } = require('./dead-refs');

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

// Test: scanFile detects oh-my-claudecode
test('scanFile detects oh-my-claudecode reference', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'drt-'));
  const f = path.join(tmp, 'agent.md');
  fs.writeFileSync(f, '# Agent\nUse oh-my-claudecode for setup.\n', 'utf8');
  const findings = scanFile(f);
  assert(findings.length > 0, 'expected at least one finding');
  assert(findings.some(r => r.label.includes('oh-my-claudecode')), 'expected oh-my-claudecode label');
  fs.rmSync(tmp, { recursive: true, force: true });
});

// Test: scanFile passes clean file
test('scanFile passes clean file with no dead refs', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'drt-'));
  const f = path.join(tmp, 'clean.md');
  fs.writeFileSync(f, '# Clean Agent\nThis file has no dead references.\n', 'utf8');
  const findings = scanFile(f);
  assert.strictEqual(findings.length, 0, `expected 0 findings, got ${findings.length}`);
  fs.rmSync(tmp, { recursive: true, force: true });
});

// Test: scanFile detects masonry-lint-check.js
test('scanFile detects masonry-lint-check.js reference', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'drt-'));
  const f = path.join(tmp, 'hooks.md');
  fs.writeFileSync(f, 'Hook: masonry-lint-check.js runs on every edit.\n', 'utf8');
  const findings = scanFile(f);
  assert(findings.some(r => r.label.includes('masonry-lint-check.js')), 'expected masonry-lint-check.js label');
  fs.rmSync(tmp, { recursive: true, force: true });
});

// Test: scanFile returns [] for nonexistent file
test('scanFile returns [] for nonexistent file', () => {
  const findings = scanFile('/nonexistent/path/no-such-file.md');
  assert(Array.isArray(findings), 'not an array');
  assert.strictEqual(findings.length, 0, `expected 0, got ${findings.length}`);
});

// Test: formatWarnings returns '' for empty array
test('formatWarnings returns empty string for empty array', () => {
  const result = formatWarnings([]);
  assert.strictEqual(result, '', `expected '', got '${result}'`);
});

// Test: formatWarnings returns STALE_REF lines
test('formatWarnings returns STALE_REF lines for findings', () => {
  const findings = [
    { file: '/path/to/agent.md', label: 'oh-my-claudecode (uninstalled)' },
    { file: '/path/to/CLAUDE.md', label: 'DISABLE_OMC env var (removed)' },
  ];
  const result = formatWarnings(findings);
  assert(result.includes('[Masonry] STALE_REF:'), 'missing STALE_REF prefix');
  assert(result.includes('oh-my-claudecode'), 'missing oh-my-claudecode');
  assert(result.includes('DISABLE_OMC'), 'missing DISABLE_OMC');
  const lines = result.split('\n').filter(Boolean);
  assert.strictEqual(lines.length, 2, `expected 2 lines, got ${lines.length}`);
});

// Test: DEAD_REFS.length >= 9
test('DEAD_REFS contains at least 9 patterns', () => {
  assert(Array.isArray(DEAD_REFS), 'DEAD_REFS is not an array');
  assert(DEAD_REFS.length >= 9, `expected >= 9, got ${DEAD_REFS.length}`);
});

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);

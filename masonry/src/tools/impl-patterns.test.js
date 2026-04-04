'use strict';
const assert = require('assert');
const impl = require('./impl-patterns');

const expected = ['toolPatternStore', 'toolPatternSearch', 'toolPatternDecay'];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-patterns must export ${fn}`);
}

// toolPatternDecay on missing dir returns empty decay result
const result = impl.toolPatternDecay({ project_dir: '/nonexistent/xyz' });
assert.ok(typeof result === 'object');
assert.ok('decayed' in result || 'error' in result);

console.log('PASS impl-patterns.test.js');

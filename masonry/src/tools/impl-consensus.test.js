'use strict';
const assert = require('assert');
const impl = require('./impl-consensus');

const expected = ['toolConsensusCheck', 'toolReviewConsensus'];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-consensus must export ${fn}`);
}

// toolConsensusCheck in check mode with no file returns approved: false
const result = impl.toolConsensusCheck({
  project_path: '/nonexistent/xyz',
  action: 'DROP TABLE test',
  mode: 'check',
});
assert.ok(typeof result === 'object');
assert.strictEqual(result.approved, false);

console.log('PASS impl-consensus.test.js');

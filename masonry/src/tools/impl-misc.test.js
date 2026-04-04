'use strict';
const assert = require('assert');
const impl = require('./impl-misc');

const expected = [
  'toolVerify7point', 'toolTrainingUpdate', 'toolSetStrategy',
  'toolReasoningStore', 'toolReasoningQuery',
  'toolGraphRecord', 'toolPageRankRun',
  'toolClaimsAdd', 'toolClaimsList', 'toolClaimResolve',
];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-misc must export ${fn}`);
}

// toolVerify7point on non-existent dir returns overall: FAIL
const result = impl.toolVerify7point({ project_dir: '/nonexistent/xyz' });
assert.ok(typeof result === 'object');
assert.strictEqual(result.overall, 'FAIL');

console.log('PASS impl-misc.test.js');

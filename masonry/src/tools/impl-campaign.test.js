'use strict';
const assert = require('assert');
const impl = require('./impl-campaign');

// All expected exports must be functions
const expected = ['toolStatus', 'toolFindings', 'toolQuestions', 'toolRun', 'toolWeights', 'toolFleet'];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-campaign must export ${fn}`);
}

// toolStatus with a non-existent path returns status: no_campaign
const result = impl.toolStatus({ project_path: '/nonexistent/path/xyz' });
assert.ok(typeof result === 'object', 'toolStatus must return an object');
assert.strictEqual(result.status, 'no_campaign');

console.log('PASS impl-campaign.test.js');

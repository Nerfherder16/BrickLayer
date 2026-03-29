'use strict';
const assert = require('assert');
const impl = require('./impl-agents');

const expected = ['toolWorkerStatus', 'toolTaskAssign', 'toolAgentHealth', 'toolWaveValidate', 'toolSwarmInit'];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-agents must export ${fn}`);
}

// toolTaskAssign with no progress.json returns task: null
const result = impl.toolTaskAssign({ project_path: '/nonexistent/xyz' });
assert.ok(typeof result === 'object');
assert.strictEqual(result.task, null);

console.log('PASS impl-agents.test.js');

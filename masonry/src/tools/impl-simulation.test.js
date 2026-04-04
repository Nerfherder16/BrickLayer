'use strict';
const assert = require('assert');
const impl = require('./impl-simulation');

const expected = ['toolNlGenerate', 'toolGitHypothesis', 'toolRunSimulation', 'toolSweep', 'toolRunQuestion', 'toolRecall', 'toolRoute'];
for (const fn of expected) {
  assert.strictEqual(typeof impl[fn], 'function', `impl-simulation must export ${fn}`);
}

// toolGitHypothesis returns error on non-git path
const result = impl.toolGitHypothesis({ project_path: '/nonexistent/path/xyz', commits: 1 });
assert.ok(typeof result === 'object');
assert.ok('error' in result || 'questions' in result);

console.log('PASS impl-simulation.test.js');

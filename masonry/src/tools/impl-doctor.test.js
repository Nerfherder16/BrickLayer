'use strict';
const assert = require('assert');
const { toolDoctor } = require('./impl-doctor');

assert.strictEqual(typeof toolDoctor, 'function', 'toolDoctor must be a function');
// toolDoctor is async — just confirm it returns a promise
const result = toolDoctor({ project_path: '/nonexistent/xyz' });
assert.ok(result && typeof result.then === 'function', 'toolDoctor must return a Promise');
result.then(r => {
  assert.ok(typeof r === 'object');
  assert.ok(['PASS', 'WARN', 'FAIL'].includes(r.overall));
  console.log('PASS impl-doctor.test.js');
}).catch(err => {
  console.error('FAIL impl-doctor.test.js:', err.message);
  process.exit(1);
});

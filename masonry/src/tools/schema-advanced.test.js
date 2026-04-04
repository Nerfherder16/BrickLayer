'use strict';
const assert = require('assert');
const { TOOLS_ADVANCED } = require('./schema-advanced');

assert.ok(Array.isArray(TOOLS_ADVANCED), 'TOOLS_ADVANCED must be an array');
assert.ok(TOOLS_ADVANCED.length >= 8, 'TOOLS_ADVANCED must have at least 8 entries');
for (const t of TOOLS_ADVANCED) {
  assert.ok(typeof t.name === 'string', `tool missing name: ${JSON.stringify(t)}`);
  assert.ok(typeof t.description === 'string', `tool missing description: ${t.name}`);
  assert.ok(typeof t.inputSchema === 'object', `tool missing inputSchema: ${t.name}`);
}
console.log('PASS schema-advanced.test.js');

'use strict';
const assert = require('assert');
const { TOOLS_CORE } = require('./schema-core');

assert.ok(Array.isArray(TOOLS_CORE), 'TOOLS_CORE must be an array');
assert.ok(TOOLS_CORE.length >= 8, 'TOOLS_CORE must have at least 8 entries');
for (const t of TOOLS_CORE) {
  assert.ok(typeof t.name === 'string', `tool missing name: ${JSON.stringify(t)}`);
  assert.ok(typeof t.description === 'string', `tool missing description: ${t.name}`);
  assert.ok(typeof t.inputSchema === 'object', `tool missing inputSchema: ${t.name}`);
}
console.log('PASS schema-core.test.js');

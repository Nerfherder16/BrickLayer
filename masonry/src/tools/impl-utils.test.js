'use strict';
const assert = require('assert');
const { httpRequest, callPython } = require('./impl-utils');

// httpRequest and callPython must be functions
assert.strictEqual(typeof httpRequest, 'function', 'httpRequest must be a function');
assert.strictEqual(typeof callPython, 'function', 'callPython must be a function');

// callPython returns error object on bad script (not throw)
const result = callPython('raise ValueError("test")', {});
assert.ok(typeof result === 'object', 'callPython must return an object');
assert.ok('error' in result, 'callPython must return { error } on failure');

console.log('PASS impl-utils.test.js');

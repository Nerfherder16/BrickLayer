'use strict';
const assert = require('assert');
const { loadConfig, CONFIG_PATH, CONFIG_DEFAULTS } = require('./config');

// 1. loadConfig returns an object with recallHost
const cfg = loadConfig();
assert.ok(typeof cfg.recallHost === 'string', 'recallHost must be a string');
assert.ok(cfg.recallHost.startsWith('http'), 'recallHost must be an http URL');

// 2. CONFIG_PATH is a string ending in config.json
assert.ok(typeof CONFIG_PATH === 'string');
assert.ok(CONFIG_PATH.endsWith('config.json'));

// 3. CONFIG_DEFAULTS has recallHost
assert.ok(typeof CONFIG_DEFAULTS.recallHost === 'string');

console.log('PASS config.test.js');

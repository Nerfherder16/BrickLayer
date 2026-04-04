'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_PATH = path.join(os.homedir(), '.masonry', 'config.json');

const CONFIG_DEFAULTS = {
  recallHost: 'http://100.70.195.84:8200',
  recallApiKey: process.env.RECALL_API_KEY || '',
};

function loadConfig() {
  let fileConfig = {};
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      fileConfig = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
    }
  } catch (_err) {
    // optional — fall back to defaults
  }
  return {
    ...CONFIG_DEFAULTS,
    ...fileConfig,
    recallApiKey:
      process.env.RECALL_API_KEY ||
      fileConfig.recallApiKey ||
      CONFIG_DEFAULTS.recallApiKey,
  };
}

module.exports = { loadConfig, CONFIG_PATH, CONFIG_DEFAULTS };

"use strict";
// src/core/config.js — Masonry config loader
// Reads ~/.masonry/config.json with sensible defaults.

const fs = require("fs");
const path = require("path");
const os = require("os");

const CONFIG_PATH = path.join(os.homedir(), ".masonry", "config.json");

const DEFAULTS = {
  recallHost: "http://100.70.195.84:8200",
  recallApiKey: process.env.RECALL_API_KEY || "",
  ollamaHost: "http://192.168.50.62:11434",
  ollamaModel: "qwen3:14b",
  handoffThreshold: 70,
};

/**
 * Load Masonry config from ~/.masonry/config.json merged with defaults.
 * Never throws — always returns a valid config object.
 * @returns {{ recallHost, recallApiKey, ollamaHost, ollamaModel, handoffThreshold }}
 */
function loadConfig() {
  let fileConfig = {};

  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const raw = fs.readFileSync(CONFIG_PATH, "utf8");
      fileConfig = JSON.parse(raw);
    }
  } catch (_err) {
    // Config file is optional — fall back to defaults
  }

  return {
    ...DEFAULTS,
    ...fileConfig,
    // env var always wins for API key
    recallApiKey:
      process.env.RECALL_API_KEY ||
      fileConfig.recallApiKey ||
      DEFAULTS.recallApiKey,
  };
}

module.exports = { loadConfig };

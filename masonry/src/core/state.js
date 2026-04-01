"use strict";
// src/core/state.js — masonry-state.json read/write utilities
// State lives at {projectDir}/masonry-state.json

const fs = require("fs");
const path = require("path");

const STATE_FILE = "masonry-state.json";

/**
 * Read masonry-state.json from projectDir.
 * @param {string} projectDir  absolute path to project directory
 * @returns {object|null}  parsed state or null if not found / parse error
 */
function readState(projectDir) {
  try {
    const stateFile = path.join(projectDir, STATE_FILE);
    if (!fs.existsSync(stateFile)) return null;
    const raw = fs.readFileSync(stateFile, "utf8");
    return JSON.parse(raw);
  } catch (_err) {
    return null;
  }
}

/**
 * Write (merge) state into masonry-state.json.
 * Shallow-merges verdicts object; top-level keys are overwritten.
 * Always sets updated_at to current ISO timestamp.
 * @param {string} projectDir
 * @param {object} updates  partial state to merge
 */
function writeState(projectDir, updates) {
  try {
    const stateFile = path.join(projectDir, STATE_FILE);
    const existing = readState(projectDir) || {};

    // Deep-merge verdicts sub-object so individual counts aren't wiped
    const verdicts = {
      ...(existing.verdicts || {}),
      ...(updates.verdicts || {}),
    };

    const next = {
      ...existing,
      ...updates,
      verdicts,
      updated_at: new Date().toISOString(),
    };

    // Atomic write: write to temp file then rename to prevent lost-update races
    // between concurrent sessions (casaclaude + proxyclaude on same project).
    const tmpFile = stateFile + ".tmp." + process.pid;
    fs.writeFileSync(tmpFile, JSON.stringify(next, null, 2), "utf8");
    fs.renameSync(tmpFile, stateFile);
  } catch (_err) {
    // Non-fatal — never block the loop
  }
}

/**
 * Delete masonry-state.json from projectDir.
 * @param {string} projectDir
 */
function clearState(projectDir) {
  try {
    const stateFile = path.join(projectDir, STATE_FILE);
    if (fs.existsSync(stateFile)) fs.unlinkSync(stateFile);
  } catch (_err) {
    // Non-fatal
  }
}

module.exports = { readState, writeState, clearState };

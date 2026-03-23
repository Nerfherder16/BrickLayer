/**
 * masonry/src/core/mas.js
 *
 * Shared utilities for reading and writing the per-project `.mas/` telemetry
 * directory. Every function is non-fatal: wrapped in try/catch, never throws.
 * All file I/O is synchronous (matching existing hook patterns).
 *
 * Export: { getMasDir, appendJsonl, writeJson, readJson, readJsonl,
 *           prunePulse, isResearchProject, initKilnJson }
 */

"use strict";

const fs = require("fs");
const path = require("path");

const PULSE_FILE = "pulse.jsonl";
const DEFAULT_PULSE_MAX_AGE_MS = 86_400_000; // 24 hours

// ── getMasDir ─────────────────────────────────────────────────────────────────

/**
 * Returns the `.mas/` directory path for `projectDir`, creating it if needed.
 * Non-fatal: returns the path string even on mkdir error.
 *
 * @param {string} projectDir
 * @returns {string}
 */
function getMasDir(projectDir) {
  const dir = path.join(projectDir, ".mas");
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (_) {}
  return dir;
}

// ── appendJsonl ───────────────────────────────────────────────────────────────

/**
 * Appends a JSON record as a single line to `.mas/{filename}`.
 * Creates the file (and the `.mas/` dir) if it does not exist.
 *
 * @param {string} projectDir
 * @param {string} filename
 * @param {object} record
 */
function appendJsonl(projectDir, filename, record) {
  try {
    const masDir = getMasDir(projectDir);
    const line = JSON.stringify(record);
    fs.appendFileSync(path.join(masDir, filename), line + "\n", "utf8");
  } catch (_) {}
}

// ── writeJson ─────────────────────────────────────────────────────────────────

/**
 * Writes (overwrites) a JSON object to `.mas/{filename}`, pretty-printed.
 *
 * @param {string} projectDir
 * @param {string} filename
 * @param {object} data
 */
function writeJson(projectDir, filename, data) {
  try {
    const masDir = getMasDir(projectDir);
    fs.writeFileSync(
      path.join(masDir, filename),
      JSON.stringify(data, null, 2),
      "utf8"
    );
  } catch (_) {}
}

// ── readJson ──────────────────────────────────────────────────────────────────

/**
 * Reads and parses `.mas/{filename}`. Returns parsed object or `null` on any
 * error (missing file, bad JSON, etc.).
 *
 * @param {string} projectDir
 * @param {string} filename
 * @returns {object|null}
 */
function readJson(projectDir, filename) {
  try {
    const filePath = path.join(projectDir, ".mas", filename);
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_) {
    return null;
  }
}

// ── readJsonl ─────────────────────────────────────────────────────────────────

/**
 * Reads `.mas/{filename}`, splits by newline, parses each non-empty line as
 * JSON. Skips malformed lines. Returns `[]` on any error.
 *
 * @param {string} projectDir
 * @param {string} filename
 * @returns {object[]}
 */
function readJsonl(projectDir, filename) {
  try {
    const filePath = path.join(projectDir, ".mas", filename);
    const content = fs.readFileSync(filePath, "utf8");
    const results = [];
    for (const line of content.split("\n")) {
      if (!line.trim()) continue;
      try {
        results.push(JSON.parse(line));
      } catch (_) {
        // skip malformed line
      }
    }
    return results;
  } catch (_) {
    return [];
  }
}

// ── prunePulse ────────────────────────────────────────────────────────────────

/**
 * Removes entries from `pulse.jsonl` older than `maxAgeMs` milliseconds.
 * Rewrites the file with surviving entries only. Non-fatal.
 *
 * @param {string} projectDir
 * @param {number} [maxAgeMs=86400000] defaults to 24 hours
 */
function prunePulse(projectDir, maxAgeMs) {
  try {
    const age = typeof maxAgeMs === "number" ? maxAgeMs : DEFAULT_PULSE_MAX_AGE_MS;
    const entries = readJsonl(projectDir, PULSE_FILE);
    const now = Date.now();
    const surviving = entries.filter((e) => {
      if (!e || !e.timestamp) return false;
      return now - Date.parse(e.timestamp) < age;
    });
    const masDir = getMasDir(projectDir);
    const filePath = path.join(masDir, PULSE_FILE);
    fs.writeFileSync(
      filePath,
      surviving.map((e) => JSON.stringify(e)).join("\n") + (surviving.length ? "\n" : ""),
      "utf8"
    );
  } catch (_) {}
}

// ── isResearchProject ─────────────────────────────────────────────────────────

/**
 * Returns true if both `program.md` and `questions.md` exist in `dir`.
 * Used by hooks to skip silently inside BL research subprocesses.
 *
 * @param {string} dir
 * @returns {boolean}
 */
function isResearchProject(dir) {
  try {
    return (
      fs.existsSync(path.join(dir, "program.md")) &&
      fs.existsSync(path.join(dir, "questions.md"))
    );
  } catch (_) {
    return false;
  }
}

// ── initKilnJson ──────────────────────────────────────────────────────────────

/**
 * Creates `.mas/kiln.json` with identity metadata for this project.
 * If `kiln.json` already exists, returns without writing (idempotent).
 *
 * @param {string} projectDir
 * @param {{ displayName?: string, description?: string, color?: string,
 *           icon?: string, phase?: string, status?: string }} [opts={}]
 */
function initKilnJson(projectDir, opts) {
  try {
    const masDir = getMasDir(projectDir);
    const kilnPath = path.join(masDir, "kiln.json");
    // Don't overwrite if already exists
    if (fs.existsSync(kilnPath)) return;

    const o = opts || {};

    // Auto-derive display_name from directory basename
    let displayName = o.displayName;
    if (!displayName) {
      const base = path.basename(projectDir);
      displayName = base
        .replace(/[-_]/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
    }

    const kiln = {
      display_name: displayName,
      description: o.description || "",
      color: o.color || null,
      icon: o.icon || null,
      pinned: false,
      phase: o.phase || "research",
      status: o.status || "active",
      created_at: new Date().toISOString(),
    };

    fs.writeFileSync(kilnPath, JSON.stringify(kiln, null, 2), "utf8");
  } catch (_) {}
}

// ── exports ───────────────────────────────────────────────────────────────────

module.exports = {
  getMasDir,
  appendJsonl,
  writeJson,
  readJson,
  readJsonl,
  prunePulse,
  isResearchProject,
  initKilnJson,
};

/**
 * Tests for masonry/src/core/mas.js
 *
 * Run with: node --test tests/test_mas_core.js
 */

"use strict";

const { test, describe, before, after, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");

// ── helpers ──────────────────────────────────────────────────────────────────

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "mas-test-"));
}

function rmrf(dir) {
  try {
    fs.rmSync(dir, { recursive: true, force: true });
  } catch (_) {}
}

// ── import the module under test ─────────────────────────────────────────────

const masPath = path.join(__dirname, "..", "masonry", "src", "core", "mas.js");
const mas = require(masPath);

// ── getMasDir ─────────────────────────────────────────────────────────────────

describe("getMasDir", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates .mas/ subdir and returns path", () => {
    tmp = makeTmp();
    const result = mas.getMasDir(tmp);
    assert.equal(result, path.join(tmp, ".mas"));
    assert.ok(fs.existsSync(result), ".mas dir should exist");
    assert.ok(fs.statSync(result).isDirectory(), "should be a directory");
  });

  test("second call is idempotent (no error)", () => {
    tmp = makeTmp();
    const r1 = mas.getMasDir(tmp);
    const r2 = mas.getMasDir(tmp);
    assert.equal(r1, r2);
    assert.ok(fs.existsSync(r1));
  });

  test("non-fatal: invalid path does not throw", () => {
    tmp = makeTmp();
    assert.doesNotThrow(() => {
      mas.getMasDir("/nonexistent/deeply/nested/\x00invalid");
    });
  });
});

// ── appendJsonl ───────────────────────────────────────────────────────────────

describe("appendJsonl", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates file on first call with valid JSON", () => {
    tmp = makeTmp();
    mas.appendJsonl(tmp, "test.jsonl", { a: 1 });
    const filePath = path.join(tmp, ".mas", "test.jsonl");
    assert.ok(fs.existsSync(filePath));
    const line = fs.readFileSync(filePath, "utf8").trim();
    assert.deepEqual(JSON.parse(line), { a: 1 });
  });

  test("appends on second call — two valid JSON lines", () => {
    tmp = makeTmp();
    mas.appendJsonl(tmp, "test.jsonl", { seq: 1 });
    mas.appendJsonl(tmp, "test.jsonl", { seq: 2 });
    const filePath = path.join(tmp, ".mas", "test.jsonl");
    const lines = fs.readFileSync(filePath, "utf8").trim().split("\n");
    assert.equal(lines.length, 2);
    assert.equal(JSON.parse(lines[0]).seq, 1);
    assert.equal(JSON.parse(lines[1]).seq, 2);
  });

  test("non-fatal: invalid path does not throw", () => {
    tmp = makeTmp();
    assert.doesNotThrow(() => {
      mas.appendJsonl("/nonexistent/\x00path", "test.jsonl", { x: 1 });
    });
  });
});

// ── writeJson ─────────────────────────────────────────────────────────────────

describe("writeJson", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates file with pretty-printed JSON", () => {
    tmp = makeTmp();
    mas.writeJson(tmp, "data.json", { key: "val" });
    const filePath = path.join(tmp, ".mas", "data.json");
    assert.ok(fs.existsSync(filePath));
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    assert.deepEqual(parsed, { key: "val" });
  });

  test("overwrites on second call (not appended)", () => {
    tmp = makeTmp();
    mas.writeJson(tmp, "data.json", { v: 1 });
    mas.writeJson(tmp, "data.json", { v: 2 });
    const parsed = JSON.parse(fs.readFileSync(path.join(tmp, ".mas", "data.json"), "utf8"));
    assert.equal(parsed.v, 2);
  });

  test("non-fatal: invalid path does not throw", () => {
    tmp = makeTmp();
    assert.doesNotThrow(() => {
      mas.writeJson("/nonexistent/\x00path", "data.json", { x: 1 });
    });
  });
});

// ── readJson ──────────────────────────────────────────────────────────────────

describe("readJson", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("returns null for missing file", () => {
    tmp = makeTmp();
    const result = mas.readJson(tmp, "nonexistent.json");
    assert.equal(result, null);
  });

  test("returns null for malformed JSON", () => {
    tmp = makeTmp();
    mas.getMasDir(tmp); // ensure dir exists
    fs.writeFileSync(path.join(tmp, ".mas", "bad.json"), "{ not valid json }", "utf8");
    const result = mas.readJson(tmp, "bad.json");
    assert.equal(result, null);
  });

  test("returns parsed object for valid file", () => {
    tmp = makeTmp();
    mas.writeJson(tmp, "good.json", { hello: "world" });
    const result = mas.readJson(tmp, "good.json");
    assert.deepEqual(result, { hello: "world" });
  });
});

// ── readJsonl ─────────────────────────────────────────────────────────────────

describe("readJsonl", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("returns [] for missing file", () => {
    tmp = makeTmp();
    const result = mas.readJsonl(tmp, "missing.jsonl");
    assert.deepEqual(result, []);
  });

  test("skips malformed lines, returns valid entries", () => {
    tmp = makeTmp();
    mas.getMasDir(tmp);
    fs.writeFileSync(
      path.join(tmp, ".mas", "mixed.jsonl"),
      '{"a":1}\nnot valid\n{"b":2}\n',
      "utf8"
    );
    const result = mas.readJsonl(tmp, "mixed.jsonl");
    assert.equal(result.length, 2);
    assert.equal(result[0].a, 1);
    assert.equal(result[1].b, 2);
  });

  test("returns all entries for fully valid file", () => {
    tmp = makeTmp();
    mas.appendJsonl(tmp, "full.jsonl", { n: 1 });
    mas.appendJsonl(tmp, "full.jsonl", { n: 2 });
    mas.appendJsonl(tmp, "full.jsonl", { n: 3 });
    const result = mas.readJsonl(tmp, "full.jsonl");
    assert.equal(result.length, 3);
  });
});

// ── prunePulse ────────────────────────────────────────────────────────────────

describe("prunePulse", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("prunes entries older than maxAgeMs, keeps recent ones", () => {
    tmp = makeTmp();
    const now = Date.now();
    const old = new Date(now - 25 * 3600 * 1000).toISOString();   // 25h ago
    const recent1 = new Date(now - 23 * 3600 * 1000).toISOString(); // 23h ago
    const recent2 = new Date(now - 1000).toISOString();             // 1s ago

    mas.getMasDir(tmp);
    fs.writeFileSync(
      path.join(tmp, ".mas", "pulse.jsonl"),
      JSON.stringify({ timestamp: old, session_id: "s1" }) + "\n" +
      JSON.stringify({ timestamp: recent1, session_id: "s2" }) + "\n" +
      JSON.stringify({ timestamp: recent2, session_id: "s3" }) + "\n",
      "utf8"
    );

    mas.prunePulse(tmp); // default 24h

    const entries = mas.readJsonl(tmp, "pulse.jsonl");
    assert.equal(entries.length, 2, "old entry should be pruned");
    assert.equal(entries[0].session_id, "s2");
    assert.equal(entries[1].session_id, "s3");
  });

  test("non-fatal when pulse.jsonl missing", () => {
    tmp = makeTmp();
    assert.doesNotThrow(() => mas.prunePulse(tmp));
  });
});

// ── isResearchProject ─────────────────────────────────────────────────────────

describe("isResearchProject", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("returns true when both program.md and questions.md exist", () => {
    tmp = makeTmp();
    fs.writeFileSync(path.join(tmp, "program.md"), "# loop", "utf8");
    fs.writeFileSync(path.join(tmp, "questions.md"), "# Q", "utf8");
    assert.equal(mas.isResearchProject(tmp), true);
  });

  test("returns false when only program.md exists", () => {
    tmp = makeTmp();
    fs.writeFileSync(path.join(tmp, "program.md"), "# loop", "utf8");
    assert.equal(mas.isResearchProject(tmp), false);
  });

  test("returns false when only questions.md exists", () => {
    tmp = makeTmp();
    fs.writeFileSync(path.join(tmp, "questions.md"), "# Q", "utf8");
    assert.equal(mas.isResearchProject(tmp), false);
  });

  test("returns false when neither file exists", () => {
    tmp = makeTmp();
    assert.equal(mas.isResearchProject(tmp), false);
  });
});

// ── initKilnJson ──────────────────────────────────────────────────────────────

describe("initKilnJson", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates kiln.json with auto-derived display_name", () => {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mas-test-my-project-"));
    // Use a symlink-safe basename by renaming
    const projectDir = path.join(os.tmpdir(), "mas-test-my-project");
    try { fs.rmSync(projectDir, { recursive: true, force: true }); } catch (_) {}
    fs.mkdirSync(projectDir, { recursive: true });

    mas.initKilnJson(projectDir);

    const kiln = mas.readJson(projectDir, "kiln.json");
    assert.ok(kiln, "kiln.json should exist");
    assert.ok(typeof kiln.display_name === "string", "display_name should be string");
    assert.ok(kiln.display_name.length > 0, "display_name should not be empty");
    assert.equal(kiln.pinned, false);
    assert.equal(kiln.phase, "research");
    assert.equal(kiln.status, "active");
    assert.ok(kiln.created_at, "created_at should be set");

    fs.rmSync(projectDir, { recursive: true, force: true });
  });

  test("does not overwrite existing kiln.json", () => {
    tmp = makeTmp();
    mas.writeJson(tmp, "kiln.json", { display_name: "Existing", pinned: true });
    mas.initKilnJson(tmp);
    const kiln = mas.readJson(tmp, "kiln.json");
    assert.equal(kiln.display_name, "Existing");
    assert.equal(kiln.pinned, true);
  });

  test("respects custom opts", () => {
    tmp = makeTmp();
    mas.initKilnJson(tmp, {
      displayName: "My Campaign",
      description: "Testing discount credit",
      color: "#38bdf8",
      icon: "beaker",
      phase: "validation",
      status: "paused",
    });
    const kiln = mas.readJson(tmp, "kiln.json");
    assert.equal(kiln.display_name, "My Campaign");
    assert.equal(kiln.description, "Testing discount credit");
    assert.equal(kiln.color, "#38bdf8");
    assert.equal(kiln.icon, "beaker");
    assert.equal(kiln.phase, "validation");
    assert.equal(kiln.status, "paused");
  });

  test("non-fatal: invalid path does not throw", () => {
    tmp = makeTmp();
    assert.doesNotThrow(() => {
      mas.initKilnJson("/nonexistent/\x00path");
    });
  });
});

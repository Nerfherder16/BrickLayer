/**
 * tests/test_overseer_trigger.js — Tests for the overseer trigger mechanism.
 *
 * Tests the invocation counter (masonry-observe.js) and trigger flag check
 * (masonry-stop-guard.js) that will be added to those hook files.
 *
 * Written before implementation. All tests must fail until the developer
 * exports `handleObserveWrite` from masonry-observe.js and
 * `checkOverseerTrigger` from masonry-stop-guard.js.
 *
 * Run with: node --test tests/test_overseer_trigger.js
 */

"use strict";

const { test, describe, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");

// --- Imports that WILL fail until the developer adds exports ---
// masonry-observe.js must export handleObserveWrite(filePath, snapshotsDir)
// masonry-stop-guard.js must export checkOverseerTrigger(snapshotsDir, stderrFn)
const OBSERVE_HOOK = path.join(
  __dirname,
  "..",
  "masonry",
  "src",
  "hooks",
  "masonry-observe.js"
);
const STOP_GUARD_HOOK = path.join(
  __dirname,
  "..",
  "masonry",
  "src",
  "hooks",
  "masonry-stop-guard.js"
);

// These destructures will throw if the exports don't exist — that is the
// intended RED state.
const { handleObserveWrite } = require(OBSERVE_HOOK);
const { checkOverseerTrigger } = require(STOP_GUARD_HOOK);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "overseer-trigger-test-"));
}

function rmrf(dir) {
  try {
    fs.rmSync(dir, { recursive: true, force: true });
  } catch (_) {}
}

/** Read JSON file; return null if missing. */
function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe("overseer trigger — invocation counter (masonry-observe.js)", () => {
  let tmp;
  let snapshotsDir;

  beforeEach(() => {
    tmp = makeTmp();
    snapshotsDir = path.join(tmp, "masonry", "agent_snapshots");
    fs.mkdirSync(snapshotsDir, { recursive: true });
  });

  afterEach(() => rmrf(tmp));

  // -------------------------------------------------------------------------
  // Test 1: count increments from 0 to 1 on a single agent .md write
  // -------------------------------------------------------------------------
  test("test_invocation_count_increments — write to agents/karen.md bumps count from 0 to 1", () => {
    // Arrange: no .invocation_count file yet (implicit default 0)
    const agentFilePath = path.join(tmp, ".claude", "agents", "karen.md");
    fs.mkdirSync(path.dirname(agentFilePath), { recursive: true });
    fs.writeFileSync(agentFilePath, "# karen agent", "utf8");

    // Act
    handleObserveWrite(agentFilePath, snapshotsDir);

    // Assert
    const countFile = path.join(snapshotsDir, ".invocation_count");
    assert.ok(fs.existsSync(countFile), ".invocation_count file should exist after first write");

    const data = readJson(countFile);
    assert.ok(data !== null, ".invocation_count should be valid JSON");
    assert.equal(typeof data.count, "number", "count field should be a number");
    assert.equal(data.count, 1, "count should be 1 after first agent .md write");
  });

  // -------------------------------------------------------------------------
  // Test 2: flag written exactly at the 10th write
  // -------------------------------------------------------------------------
  test("test_trigger_flag_written_at_threshold — flag file exists after 10th agent .md write", () => {
    // Arrange
    const agentFilePath = path.join(tmp, ".claude", "agents", "research-analyst.md");
    fs.mkdirSync(path.dirname(agentFilePath), { recursive: true });
    fs.writeFileSync(agentFilePath, "# research-analyst", "utf8");

    const flagFile = path.join(snapshotsDir, "overseer_trigger.flag");

    // Act: 9 writes — flag must NOT exist yet
    for (let i = 0; i < 9; i++) {
      handleObserveWrite(agentFilePath, snapshotsDir);
    }
    assert.ok(
      !fs.existsSync(flagFile),
      "overseer_trigger.flag must not exist before the 10th write"
    );

    // 10th write — flag MUST now exist
    handleObserveWrite(agentFilePath, snapshotsDir);

    assert.ok(
      fs.existsSync(flagFile),
      "overseer_trigger.flag should exist after the 10th agent .md write"
    );

    // Flag content validation
    const flag = readJson(flagFile);
    assert.ok(flag !== null, "flag file should contain valid JSON");
    assert.ok(flag.triggered_at, "flag should have triggered_at ISO-8601 string");
    assert.equal(flag.count, 10, "flag count should equal 10");
    // triggered_at must parse as a valid date
    const parsed = new Date(flag.triggered_at);
    assert.ok(!isNaN(parsed.getTime()), "triggered_at must be a valid ISO-8601 date");
  });
});

describe("overseer trigger — stop-guard check (masonry-stop-guard.js)", () => {
  let tmp;
  let snapshotsDir;

  beforeEach(() => {
    tmp = makeTmp();
    snapshotsDir = path.join(tmp, "masonry", "agent_snapshots");
    fs.mkdirSync(snapshotsDir, { recursive: true });
  });

  afterEach(() => rmrf(tmp));

  // -------------------------------------------------------------------------
  // Test 3: flag exists → printed to stderr AND deleted
  // -------------------------------------------------------------------------
  test("test_stop_guard_clears_flag — flag deleted and [overseer] notice written to stderr", () => {
    // Arrange: pre-create the flag file
    const flagFile = path.join(snapshotsDir, "overseer_trigger.flag");
    fs.writeFileSync(
      flagFile,
      JSON.stringify({ triggered_at: new Date().toISOString(), count: 10 }),
      "utf8"
    );

    const stderrLines = [];
    const captureStderr = (line) => stderrLines.push(line);

    // Act
    checkOverseerTrigger(snapshotsDir, captureStderr);

    // Assert: (a) flag file must be deleted
    assert.ok(
      !fs.existsSync(flagFile),
      "overseer_trigger.flag should be deleted after stop-guard runs"
    );

    // Assert: (b) stderr output must contain '[overseer]'
    const combined = stderrLines.join("\n");
    assert.ok(
      combined.includes("[overseer]"),
      `stderr output should contain '[overseer]'. Got: ${JSON.stringify(combined)}`
    );
  });

  // -------------------------------------------------------------------------
  // Test 4: no flag → no output, no crash
  // -------------------------------------------------------------------------
  test("test_stop_guard_no_flag_no_noise — no flag file means no overseer output in stderr", () => {
    // Arrange: snapshotsDir exists but no flag file
    const stderrLines = [];
    const captureStderr = (line) => stderrLines.push(line);

    // Act
    checkOverseerTrigger(snapshotsDir, captureStderr);

    // Assert: no overseer noise in stderr
    const combined = stderrLines.join("\n");
    assert.ok(
      !combined.includes("[overseer]"),
      `stderr should contain no overseer output when no flag exists. Got: ${JSON.stringify(combined)}`
    );
    assert.equal(stderrLines.length, 0, "no stderr lines should be emitted when flag is absent");
  });
});

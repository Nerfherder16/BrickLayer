/**
 * Tests for masonry/src/hooks/masonry-pulse.js
 *
 * Run with: node --test tests/test_pulse_hook.js
 */

"use strict";

const { test, describe, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

const HOOK = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-pulse.js");

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "pulse-test-"));
}

function rmrf(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

function runHook(payload, opts = {}) {
  return spawnSync("node", [HOOK], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 8000,
    cwd: opts.cwd || process.cwd(),
    env: { ...process.env, RECALL_API_KEY: "", RECALL_HOST: "http://localhost:1" },
  });
}

function throttlePath(sessionId) {
  return path.join(os.tmpdir(), `masonry-pulse-last-${sessionId}`);
}

describe("masonry-pulse.js", () => {
  let tmp;
  afterEach(() => {
    rmrf(tmp);
    // Clean up throttle file
    try { fs.unlinkSync(throttlePath("test-123")); } catch (_) {}
    try { fs.unlinkSync(throttlePath("integ-pulse")); } catch (_) {}
  });

  test("creates pulse.jsonl with one valid JSON entry on first run", () => {
    tmp = makeTmp();
    // Ensure no throttle file from prior run
    try { fs.unlinkSync(throttlePath("test-123")); } catch (_) {}

    runHook({ session_id: "test-123", cwd: tmp, tool_name: "Edit" });

    const pulseFile = path.join(tmp, ".mas", "pulse.jsonl");
    assert.ok(fs.existsSync(pulseFile), "pulse.jsonl should be created");
    const lines = fs.readFileSync(pulseFile, "utf8").trim().split("\n").filter(Boolean);
    assert.equal(lines.length, 1, "should have exactly one entry");
    const entry = JSON.parse(lines[0]);
    assert.ok(entry.timestamp, "entry should have timestamp");
    assert.equal(entry.session_id, "test-123");
    assert.equal(entry.tool, "Edit");
    assert.equal(entry.cwd, tmp);
  });

  test("throttled: second immediate call does not add a second entry", () => {
    tmp = makeTmp();
    try { fs.unlinkSync(throttlePath("test-123")); } catch (_) {}

    runHook({ session_id: "test-123", cwd: tmp, tool_name: "Edit" });
    runHook({ session_id: "test-123", cwd: tmp, tool_name: "Write" });

    const pulseFile = path.join(tmp, ".mas", "pulse.jsonl");
    const lines = fs.readFileSync(pulseFile, "utf8").trim().split("\n").filter(Boolean);
    assert.equal(lines.length, 1, "throttle should prevent second write");
  });

  test("after backdating throttle file by 61s, second run adds entry", () => {
    tmp = makeTmp();
    try { fs.unlinkSync(throttlePath("test-123")); } catch (_) {}

    runHook({ session_id: "test-123", cwd: tmp, tool_name: "Edit" });

    // Backdate the throttle file by 61 seconds
    const tPath = throttlePath("test-123");
    const past = new Date(Date.now() - 61_000);
    fs.utimesSync(tPath, past, past);

    runHook({ session_id: "test-123", cwd: tmp, tool_name: "Read" });

    const pulseFile = path.join(tmp, ".mas", "pulse.jsonl");
    const lines = fs.readFileSync(pulseFile, "utf8").trim().split("\n").filter(Boolean);
    assert.equal(lines.length, 2, "should have two entries after throttle expires");
  });

  test("prune: 25h-old entry is removed, others kept", () => {
    tmp = makeTmp();
    try { fs.unlinkSync(throttlePath("test-123")); } catch (_) {}

    // Pre-populate pulse.jsonl with 3 entries
    const masDir = path.join(tmp, ".mas");
    fs.mkdirSync(masDir, { recursive: true });
    const now = Date.now();
    const old = new Date(now - 25 * 3600 * 1000).toISOString();
    const recent1 = new Date(now - 23 * 3600 * 1000).toISOString();
    const content =
      JSON.stringify({ timestamp: old, session_id: "old", tool: "Edit", cwd: tmp }) + "\n" +
      JSON.stringify({ timestamp: recent1, session_id: "r1", tool: "Write", cwd: tmp }) + "\n";
    fs.writeFileSync(path.join(masDir, "pulse.jsonl"), content, "utf8");

    // Run hook (fresh session, no throttle)
    const sid = "test-prune-" + Date.now();
    try { fs.unlinkSync(throttlePath(sid)); } catch (_) {}
    runHook({ session_id: sid, cwd: tmp, tool_name: "Read" });
    try { fs.unlinkSync(throttlePath(sid)); } catch (_) {}

    const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));
    const entries = mas.readJsonl(tmp, "pulse.jsonl");
    // Should have: recent1 + the new entry from this run = 2
    // (old entry should be pruned)
    assert.ok(entries.length >= 2, "old entry should be pruned, recent ones remain");
    assert.ok(!entries.some(e => e.session_id === "old"), "25h-old entry should be gone");
  });

  test("research project skip: no .mas/ created when program.md+questions.md exist", () => {
    tmp = makeTmp();
    fs.writeFileSync(path.join(tmp, "program.md"), "# loop", "utf8");
    fs.writeFileSync(path.join(tmp, "questions.md"), "# Q", "utf8");

    try { fs.unlinkSync(throttlePath("test-skip")); } catch (_) {}
    runHook({ session_id: "test-skip", cwd: tmp, tool_name: "Edit" });

    assert.ok(
      !fs.existsSync(path.join(tmp, ".mas")),
      ".mas/ should NOT be created for research projects"
    );
  });
});

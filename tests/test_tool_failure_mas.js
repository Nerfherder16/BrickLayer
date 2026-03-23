/**
 * Tests for .mas/errors.jsonl in masonry-tool-failure.js
 *
 * Run with: node --test tests/test_tool_failure_mas.js
 */

"use strict";

const { test, describe, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

const HOOK = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-tool-failure.js");
const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "tfail-mas-test-"));
}

function rmrf(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

function runHook(payload, cwd) {
  return spawnSync("node", [HOOK], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 8000,
    cwd: cwd || process.cwd(),
    env: { ...process.env },
  });
}

describe("masonry-tool-failure.js .mas/errors.jsonl", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates errors.jsonl with one entry on first failure", () => {
    tmp = makeTmp();

    runHook({ tool_name: "Edit", tool_response: "ENOENT: no such file" }, tmp);

    const errors = mas.readJsonl(tmp, "errors.jsonl");
    assert.equal(errors.length, 1, "should have exactly one error entry");
    const e = errors[0];
    assert.equal(e.tool, "Edit");
    assert.ok(e.error && e.error.length > 0, "error field should be non-empty");
    assert.ok(typeof e.retries === "number", "retries should be a number");
    assert.ok(e.timestamp, "timestamp should be set");
    assert.ok(e.fingerprint, "fingerprint should be set");
  });

  test("global ~/.masonry/state/ file is ALSO created (backwards compat)", () => {
    tmp = makeTmp();

    runHook({ tool_name: "Bash", tool_response: "command not found: foo" }, tmp);

    const slug = tmp.replace(/[^a-zA-Z0-9]/g, "-").replace(/-+/g, "-").slice(-40);
    const stateFile = path.join(os.homedir(), ".masonry", "state", `${slug}-Bash.json`);
    assert.ok(fs.existsSync(stateFile), `global state file should exist at ${stateFile}`);
  });

  test("second invocation with same error appends second entry (append-only)", () => {
    tmp = makeTmp();

    runHook({ tool_name: "Write", tool_response: "permission denied" }, tmp);
    runHook({ tool_name: "Write", tool_response: "permission denied" }, tmp);

    const errors = mas.readJsonl(tmp, "errors.jsonl");
    assert.equal(errors.length, 2, "errors.jsonl should have two entries");
    // Both should parse as valid JSON
    for (const e of errors) {
      assert.ok(e.tool, "each entry should have tool field");
    }
  });
});

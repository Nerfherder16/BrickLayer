/**
 * Tests for .mas/ integration in masonry-session-start.js
 *
 * Run with: node --test tests/test_session_start_mas.js
 */

"use strict";

const { test, describe, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync, spawnSync } = require("child_process");

const HOOK = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-session-start.js");
const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "session-mas-test-"));
}

function rmrf(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

function initGitRepo(dir, branch = "test-branch") {
  try {
    execSync("git init", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync(`git checkout -b ${branch}`, { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.email test@test.com", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.name Test", { cwd: dir, encoding: "utf8", stdio: "pipe" });
  } catch (_) {}
}

function runHook(payload, cwd) {
  return spawnSync("node", [HOOK], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 10000,
    cwd: cwd || process.cwd(),
    env: { ...process.env, RECALL_API_KEY: "", RECALL_HOST: "http://localhost:1" },
  });
}

describe("masonry-session-start.js .mas/ integration", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("creates .mas/session.json with correct fields", () => {
    tmp = makeTmp();
    initGitRepo(tmp, "test-branch");

    runHook({ cwd: tmp, session_id: "sess-1" });

    const session = mas.readJson(tmp, "session.json");
    assert.ok(session, "session.json should exist");
    assert.equal(session.session_id, "sess-1");
    assert.ok(session.started_at, "started_at should be set");
    assert.equal(session.cwd, tmp);
    assert.equal(session.branch, "test-branch");
  });

  test("creates .mas/kiln.json with auto-derived display_name", () => {
    tmp = makeTmp();
    initGitRepo(tmp);

    runHook({ cwd: tmp, session_id: "sess-2" });

    const kiln = mas.readJson(tmp, "kiln.json");
    assert.ok(kiln, "kiln.json should exist");
    assert.ok(typeof kiln.display_name === "string" && kiln.display_name.length > 0);
    assert.equal(kiln.phase, "research");
    assert.equal(kiln.status, "active");
  });

  test("session.json is overwritten on second run (not appended)", () => {
    tmp = makeTmp();
    initGitRepo(tmp);

    runHook({ cwd: tmp, session_id: "sess-a" });
    const first = mas.readJson(tmp, "session.json");

    // Small delay to ensure different timestamp
    const waitUntil = Date.now() + 50;
    while (Date.now() < waitUntil) {}

    runHook({ cwd: tmp, session_id: "sess-b" });
    const second = mas.readJson(tmp, "session.json");

    assert.equal(second.session_id, "sess-b");
    assert.notEqual(second.started_at, first.started_at);
    // File should be JSON, not JSONL
    const raw = fs.readFileSync(path.join(tmp, ".mas", "session.json"), "utf8");
    assert.ok(!raw.includes("\n}\n{"), "session.json should be overwritten, not appended");
  });

  test("kiln.json is NOT overwritten on second run (initKilnJson is idempotent)", () => {
    tmp = makeTmp();
    initGitRepo(tmp);

    runHook({ cwd: tmp, session_id: "sess-x" });
    const first = mas.readJson(tmp, "kiln.json");

    runHook({ cwd: tmp, session_id: "sess-y" });
    const second = mas.readJson(tmp, "kiln.json");

    assert.equal(first.created_at, second.created_at, "kiln.json created_at should not change");
  });

  test("injects context.md message when file exists", () => {
    tmp = makeTmp();
    initGitRepo(tmp);

    // First run to create .mas/
    runHook({ cwd: tmp, session_id: "sess-ctx-1" });

    // Write context.md
    fs.writeFileSync(
      path.join(tmp, ".mas", "context.md"),
      "This campaign tests discount credit economics.",
      "utf8"
    );

    // Second run — should inject context
    const result = runHook({ cwd: tmp, session_id: "sess-ctx-2" });
    const allOutput = (result.stdout || "") + (result.stderr || "");
    assert.ok(
      allOutput.includes("context.md"),
      `Output should mention context.md. Got: ${allOutput.slice(0, 500)}`
    );
  });
});

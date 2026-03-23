/**
 * Tests for .mas/ session close in masonry-stop-guard.js
 *
 * Run with: node --test tests/test_stop_guard_mas.js
 */

"use strict";

const { test, describe, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync, spawnSync } = require("child_process");

const HOOK = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-stop-guard.js");
const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "stop-mas-test-"));
}

function rmrf(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

function initCleanGitRepo(dir) {
  try {
    execSync("git init", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.email test@test.com", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.name Test", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    // Gitignore .mas/ so the stop-guard doesn't flag it as untracked
    fs.writeFileSync(path.join(dir, ".gitignore"), "**/.mas/\n", "utf8");
    // Need at least one commit so git status works
    fs.writeFileSync(path.join(dir, ".gitkeep"), "", "utf8");
    execSync("git add .gitkeep .gitignore", { cwd: dir, encoding: "utf8", stdio: "pipe" });
    execSync('git commit -m "init"', { cwd: dir, encoding: "utf8", stdio: "pipe" });
  } catch (_) {}
}

function writeSession(dir, data) {
  mas.writeJson(dir, "session.json", data);
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

describe("masonry-stop-guard.js .mas/ session close", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("adds ended_at and duration_ms to session.json on clean exit", () => {
    tmp = makeTmp();
    initCleanGitRepo(tmp);

    writeSession(tmp, {
      session_id: "s1",
      started_at: "2026-03-23T00:00:00.000Z",
      cwd: tmp,
      branch: "main",
    });

    const result = runHook({ cwd: tmp, session_id: "s1" }, tmp);
    assert.ok(result.status !== 2, `Hook should not block. stderr: ${result.stderr}`);

    const session = mas.readJson(tmp, "session.json");
    assert.ok(session, "session.json should still exist");
    assert.ok(session.ended_at, "ended_at should be set");
    assert.ok(typeof session.duration_ms === "number", "duration_ms should be a number");
    assert.ok(session.duration_ms >= 0, "duration_ms should be non-negative");
  });

  test("appends closed session to history.jsonl", () => {
    tmp = makeTmp();
    initCleanGitRepo(tmp);

    writeSession(tmp, {
      session_id: "s2",
      started_at: new Date(Date.now() - 5000).toISOString(),
      cwd: tmp,
      branch: "main",
    });

    runHook({ cwd: tmp, session_id: "s2" }, tmp);

    const history = mas.readJsonl(tmp, "history.jsonl");
    assert.equal(history.length, 1, "history.jsonl should have one entry");
    assert.ok(history[0].ended_at, "history entry should have ended_at");
    assert.equal(history[0].session_id, "s2");
  });

  test("history.jsonl is append-only: second run adds second entry", () => {
    tmp = makeTmp();
    initCleanGitRepo(tmp);

    writeSession(tmp, {
      session_id: "s3a",
      started_at: new Date(Date.now() - 3000).toISOString(),
      cwd: tmp,
    });
    runHook({ cwd: tmp, session_id: "s3a" }, tmp);

    writeSession(tmp, {
      session_id: "s3b",
      started_at: new Date(Date.now() - 1000).toISOString(),
      cwd: tmp,
    });
    runHook({ cwd: tmp, session_id: "s3b" }, tmp);

    const history = mas.readJsonl(tmp, "history.jsonl");
    assert.equal(history.length, 2, "history.jsonl should have two entries after two runs");
  });

  test("blocked path: uncommitted file means exit 2, session.json has no ended_at", () => {
    tmp = makeTmp();
    initCleanGitRepo(tmp);

    writeSession(tmp, {
      session_id: "s4",
      started_at: new Date().toISOString(),
      cwd: tmp,
    });

    // Create an untracked file to trigger the block
    fs.writeFileSync(path.join(tmp, "uncommitted.js"), "// dirty", "utf8");

    const result = runHook({ cwd: tmp, session_id: "s4" }, tmp);
    assert.equal(result.status, 2, "should exit 2 when uncommitted files exist");

    const session = mas.readJson(tmp, "session.json");
    assert.ok(!session.ended_at, "session.json should NOT have ended_at on blocked path");
  });
});

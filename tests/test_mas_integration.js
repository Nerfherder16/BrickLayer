/**
 * Integration test: full .mas/ lifecycle
 *
 * Exercises session-start → pulse → observe → tool-failure → stop-guard
 * in sequence using actual hook scripts on real temp directories.
 *
 * Run with: node --test tests/test_mas_integration.js
 */

"use strict";

const { test, describe, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync, spawnSync } = require("child_process");

const HOOKS = path.join(__dirname, "..", "masonry", "src", "hooks");
const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));

let TMP;

function spawnHook(hookName, payload, opts = {}) {
  return spawnSync("node", [path.join(HOOKS, hookName)], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 12000,
    cwd: opts.cwd || TMP,
    env: {
      ...process.env,
      RECALL_API_KEY: "",
      RECALL_HOST: "http://localhost:1",
    },
  });
}

describe("Full .mas/ lifecycle integration", () => {
  // Setup: create temp dir with git repo + findings
  TMP = fs.mkdtempSync(path.join(os.tmpdir(), "mas-integ-"));

  // Init git repo with .gitignore for .mas/
  try {
    execSync("git init", { cwd: TMP, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.email integ@test.com", { cwd: TMP, encoding: "utf8", stdio: "pipe" });
    execSync("git config user.name Integ", { cwd: TMP, encoding: "utf8", stdio: "pipe" });
    fs.writeFileSync(path.join(TMP, ".gitignore"), "**/.mas/\n", "utf8");
    execSync("git add .gitignore", { cwd: TMP, encoding: "utf8", stdio: "pipe" });
    execSync('git commit -m "init"', { cwd: TMP, encoding: "utf8", stdio: "pipe" });
  } catch (_) {}

  // Create findings dir with D1.md
  const findingsDir = path.join(TMP, "findings");
  fs.mkdirSync(findingsDir, { recursive: true });
  const d1Path = path.join(findingsDir, "D1.md");
  fs.writeFileSync(d1Path, [
    "# Finding D1",
    "**Verdict**: WARNING",
    "**Agent**: quantitative-analyst",
    "**Confidence**: 0.85",
    "**Wave**: 1",
    "Integration test evidence.",
  ].join("\n"), "utf8");

  after(() => {
    try { fs.rmSync(TMP, { recursive: true, force: true }); } catch (_) {}
  });

  test("step 1: session-start creates session.json and kiln.json", () => {
    const result = spawnHook("masonry-session-start.js", {
      cwd: TMP,
      session_id: "integ-1",
    });

    const session = mas.readJson(TMP, "session.json");
    assert.ok(session, "session.json should be created");
    assert.equal(session.session_id, "integ-1");
    assert.ok(session.started_at, "started_at should be set");

    const kiln = mas.readJson(TMP, "kiln.json");
    assert.ok(kiln, "kiln.json should be created");
    assert.ok(kiln.display_name, "display_name should be set");
  });

  test("step 2: pulse creates pulse.jsonl with 1 entry", () => {
    // Remove any lingering throttle file
    try { fs.unlinkSync(path.join(os.tmpdir(), "masonry-pulse-last-integ-1")); } catch (_) {}

    spawnHook("masonry-pulse.js", {
      session_id: "integ-1",
      cwd: TMP,
      tool_name: "Read",
    });

    const pulseEntries = mas.readJsonl(TMP, "pulse.jsonl");
    assert.ok(pulseEntries.length >= 1, "pulse.jsonl should have at least 1 entry");
    assert.equal(pulseEntries[0].session_id, "integ-1");
    assert.equal(pulseEntries[0].tool, "Read");

    try { fs.unlinkSync(path.join(os.tmpdir(), "masonry-pulse-last-integ-1")); } catch (_) {}
  });

  test("step 3: observe writes timing.jsonl and agent_scores.json", () => {
    spawnHook("masonry-observe.js", {
      tool_name: "Write",
      tool_input: { file_path: d1Path },
      session_id: "integ-1",
      cwd: TMP,
    });

    const timing = mas.readJsonl(TMP, "timing.jsonl");
    assert.ok(timing.length >= 1, "timing.jsonl should have at least 1 entry");
    assert.equal(timing[timing.length - 1].qid, "D1");
    assert.equal(timing[timing.length - 1].verdict, "WARNING");

    const scores = mas.readJson(TMP, "agent_scores.json");
    assert.ok(scores, "agent_scores.json should exist");
    assert.ok(scores["quantitative-analyst"], "quantitative-analyst should be scored");
  });

  test("step 4: tool-failure writes errors.jsonl", () => {
    spawnHook("masonry-tool-failure.js", {
      tool_name: "Bash",
      tool_response: "command not found: integ-test-cmd",
    });

    const errors = mas.readJsonl(TMP, "errors.jsonl");
    assert.ok(errors.length >= 1, "errors.jsonl should have at least 1 entry");
    assert.equal(errors[0].tool, "Bash");
    assert.ok(errors[0].error, "error field should be non-empty");
  });

  test("step 5: commit finding so stop-guard is clean", () => {
    try {
      execSync("git add -A", { cwd: TMP, encoding: "utf8", stdio: "pipe" });
      execSync('git commit -m "add finding"', { cwd: TMP, encoding: "utf8", stdio: "pipe" });
    } catch (_) {}
    // Verify working tree is now clean
    const status = execSync("git status --porcelain", {
      cwd: TMP, encoding: "utf8", stdio: "pipe",
    }).trim();
    assert.equal(status, "", "working tree should be clean before stop-guard");
  });

  test("step 6: stop-guard closes session — session.json has ended_at, history.jsonl has 1 entry", () => {
    const result = spawnHook("masonry-stop-guard.js", {
      cwd: TMP,
      session_id: "integ-1",
    });

    assert.notEqual(result.status, 2, `stop-guard should not block. stderr: ${result.stderr}`);

    const session = mas.readJson(TMP, "session.json");
    assert.ok(session.ended_at, "session.json should have ended_at");
    assert.ok(typeof session.duration_ms === "number", "duration_ms should be a number");

    const history = mas.readJsonl(TMP, "history.jsonl");
    assert.ok(history.length >= 1, "history.jsonl should have at least 1 entry");
    assert.equal(history[0].session_id, "integ-1");
    assert.ok(history[0].ended_at, "history entry should have ended_at");
  });

  test("step 7: all .mas/ files parse as valid JSON or JSONL", () => {
    const masDir = path.join(TMP, ".mas");
    const files = fs.readdirSync(masDir);
    assert.ok(files.length > 0, ".mas/ should have at least one file");

    for (const file of files) {
      const filePath = path.join(masDir, file);
      const content = fs.readFileSync(filePath, "utf8").trim();
      if (!content) continue;

      if (file.endsWith(".jsonl")) {
        const lines = content.split("\n").filter(Boolean);
        for (const line of lines) {
          assert.doesNotThrow(
            () => JSON.parse(line),
            `${file}: line should be valid JSON: ${line.slice(0, 80)}`
          );
        }
      } else if (file.endsWith(".json")) {
        assert.doesNotThrow(
          () => JSON.parse(content),
          `${file} should be valid JSON`
        );
      }
    }
  });
});

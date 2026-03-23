/**
 * Tests for .mas/ telemetry in masonry-observe.js
 *
 * Run with: node --test tests/test_observe_mas.js
 */

"use strict";

const { test, describe, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

const HOOK = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-observe.js");
const mas = require(path.join(__dirname, "..", "masonry", "src", "core", "mas.js"));

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "observe-mas-test-"));
}

function rmrf(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

function writeFinding(dir, filename, content) {
  const findingsDir = path.join(dir, "findings");
  fs.mkdirSync(findingsDir, { recursive: true });
  fs.writeFileSync(path.join(findingsDir, filename), content, "utf8");
  return path.join(findingsDir, filename);
}

const FINDING_D1 = `# Finding D1
**Verdict**: WARNING
**Agent**: quantitative-analyst
**Confidence**: 0.85
**Wave**: 3
Some evidence text here.
`;

const FINDING_D2 = `# Finding D2
**Verdict**: HEALTHY
**Agent**: quantitative-analyst
**Confidence**: 0.92
**Wave**: 3
Different evidence.
`;

function runHook(payload, cwd) {
  return spawnSync("node", [HOOK], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 10000,
    cwd: cwd || process.cwd(),
    env: {
      ...process.env,
      RECALL_API_KEY: "",
      RECALL_HOST: "http://localhost:1",
    },
  });
}

describe("masonry-observe.js .mas/ telemetry", () => {
  let tmp;
  afterEach(() => rmrf(tmp));

  test("writes timing.jsonl with correct fields on finding write", () => {
    tmp = makeTmp();
    const findingPath = writeFinding(tmp, "D1.md", FINDING_D1);

    runHook({
      tool_name: "Write",
      tool_input: { file_path: findingPath },
      session_id: "obs-1",
      cwd: tmp,
    }, tmp);

    const timing = mas.readJsonl(tmp, "timing.jsonl");
    assert.ok(timing.length >= 1, "timing.jsonl should have at least one entry");
    const entry = timing[timing.length - 1];
    assert.equal(entry.qid, "D1");
    assert.equal(entry.verdict, "WARNING");
    assert.equal(entry.wave, 3);
    assert.equal(entry.agent, "quantitative-analyst");
    assert.ok(entry.timestamp, "timestamp should be set");
  });

  test("writes agent_scores.json with count and verdicts", () => {
    tmp = makeTmp();
    const findingPath = writeFinding(tmp, "D1.md", FINDING_D1);

    runHook({
      tool_name: "Write",
      tool_input: { file_path: findingPath },
      session_id: "obs-2",
      cwd: tmp,
    }, tmp);

    const scores = mas.readJson(tmp, "agent_scores.json");
    assert.ok(scores, "agent_scores.json should exist");
    assert.ok(scores["quantitative-analyst"], "should have quantitative-analyst entry");
    assert.equal(scores["quantitative-analyst"].count, 1);
    assert.deepEqual(scores["quantitative-analyst"].verdicts, { WARNING: 1 });
    assert.ok(scores["quantitative-analyst"].last_seen, "last_seen should be set");
  });

  test("writes recall_log.jsonl with correct fields", () => {
    tmp = makeTmp();
    const findingPath = writeFinding(tmp, "D1.md", FINDING_D1);

    runHook({
      tool_name: "Write",
      tool_input: { file_path: findingPath },
      session_id: "obs-3",
      cwd: tmp,
    }, tmp);

    const recallLog = mas.readJsonl(tmp, "recall_log.jsonl");
    assert.ok(recallLog.length >= 1, "recall_log.jsonl should have at least one entry");
    const entry = recallLog[recallLog.length - 1];
    assert.equal(entry.qid, "D1");
    // memory_id may be null (Recall network call fails in test)
    assert.ok("memory_id" in entry, "memory_id field should exist");
    assert.ok(entry.domain, "domain should be set");
    assert.ok(entry.timestamp, "timestamp should be set");
  });

  test("second finding updates agent_scores count and verdict map", () => {
    tmp = makeTmp();
    const d1Path = writeFinding(tmp, "D1.md", FINDING_D1);
    const d2Path = writeFinding(tmp, "D2.md", FINDING_D2);

    runHook({
      tool_name: "Write",
      tool_input: { file_path: d1Path },
      session_id: "obs-4",
      cwd: tmp,
    }, tmp);

    runHook({
      tool_name: "Write",
      tool_input: { file_path: d2Path },
      session_id: "obs-4",
      cwd: tmp,
    }, tmp);

    const scores = mas.readJson(tmp, "agent_scores.json");
    const qa = scores["quantitative-analyst"];
    assert.ok(qa, "quantitative-analyst should exist");
    assert.equal(qa.count, 2, "count should be 2 after two findings");
    assert.equal(qa.verdicts["WARNING"], 1);
    assert.equal(qa.verdicts["HEALTHY"], 1);
  });
});

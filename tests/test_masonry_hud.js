#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

const MASONRY_ROOT = path.join(__dirname, "..");
const STATUSLINE = path.join(
  MASONRY_ROOT,
  "masonry",
  "src",
  "hooks",
  "masonry-statusline.js",
);

function runStatusline(inputObj) {
  const input = JSON.stringify(inputObj);
  const result = execSync(`node "${STATUSLINE}"`, {
    input,
    encoding: "utf8",
    timeout: 5000,
  });
  return result;
}

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

console.log("\ntest_masonry_hud.js\n");

// T1: outputs a single line
test("outputs a single line ending in newline", () => {
  const out = runStatusline({
    context_window: { used_percentage: 30 },
    cwd: MASONRY_ROOT,
  });
  const lines = out.split("\n").filter(Boolean);
  assert.strictEqual(lines.length, 1, `Expected 1 line, got ${lines.length}`);
});

// T2: contains 'masonry' brand
test("output contains masonry brand", () => {
  const out = runStatusline({
    context_window: { used_percentage: 30 },
    cwd: MASONRY_ROOT,
  });
  assert.ok(out.includes("masonry"), "Output should contain 'masonry'");
});

// T3: does not crash with empty input
test("does not crash with minimal input", () => {
  const out = runStatusline({});
  assert.ok(
    typeof out === "string" && out.length > 0,
    "Should produce non-empty output",
  );
});

// T4: shows progress percentage
test("shows context percentage", () => {
  const out = runStatusline({
    context_window: { used_percentage: 55 },
    cwd: MASONRY_ROOT,
  });
  assert.ok(out.includes("55%"), "Should show 55%");
});

// T5: with masonry-state.json present, shows wave info
test("shows wave and mode when masonry-state.json present", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "masonry-hud-test-"));
  try {
    const state = {
      mode: "research",
      last_qid: "Q12",
      active_agent: "mortar",
      verdicts: { HEALTHY: 5, WARNING: 1, FAILURE: 0 },
    };
    fs.writeFileSync(
      path.join(tmpDir, "masonry-state.json"),
      JSON.stringify(state),
    );
    // Write questions.md with 7 Wave headers and 49 questions so statusline can derive counts
    const wavesAndQs = Array.from(
      { length: 7 },
      (_, w) =>
        `## Wave ${w + 1}\n` +
        Array.from(
          { length: 7 },
          (_, q) => `### Q${w * 7 + q + 1} — test question`,
        ).join("\n"),
    ).join("\n");
    fs.writeFileSync(path.join(tmpDir, "questions.md"), wavesAndQs);
    const out = runStatusline({
      context_window: { used_percentage: 20 },
      cwd: tmpDir,
    });
    assert.ok(
      out.includes("wave"),
      `Should contain 'wave', got: ${out.trim()}`,
    );
    assert.ok(out.includes("7"), `Should contain wave number 7`);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T6: git segment appears (we're in a git repo)
test("shows git branch segment", () => {
  const out = runStatusline({
    context_window: { used_percentage: 10 },
    cwd: MASONRY_ROOT,
  });
  // Should contain some branch-like string (letters/numbers/slashes/hyphens)
  // Strip ANSI codes first
  const clean = out.replace(/\x1b\[[0-9;]*m/g, "");
  assert.ok(
    /[a-z0-9][a-z0-9/\-_]+/.test(clean),
    `Should contain branch name in: ${clean.trim()}`,
  );
});

// T7: build segment appears when progress.json has IN_PROGRESS task
test("shows build segment when IN_PROGRESS task exists", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "masonry-hud-test-"));
  try {
    const autopilotDir = path.join(tmpDir, ".autopilot");
    fs.mkdirSync(autopilotDir);
    const progress = {
      project: "test",
      status: "BUILDING",
      tasks: [{ id: 3, description: "Do thing", status: "IN_PROGRESS" }],
    };
    fs.writeFileSync(
      path.join(autopilotDir, "progress.json"),
      JSON.stringify(progress),
    );
    const out = runStatusline({
      context_window: { used_percentage: 10 },
      cwd: tmpDir,
    });
    const clean = out.replace(/\x1b\[[0-9;]*m/g, "");
    assert.ok(
      clean.includes("bld:#3"),
      `Should contain 'bld:#3', got: ${clean.trim()}`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T8: ui segment appears when .ui/mode is set
test("shows ui mode segment when .ui/mode exists", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "masonry-hud-test-"));
  try {
    const uiDir = path.join(tmpDir, ".ui");
    fs.mkdirSync(uiDir);
    fs.writeFileSync(path.join(uiDir, "mode"), "compose");
    const out = runStatusline({
      context_window: { used_percentage: 10 },
      cwd: tmpDir,
    });
    const clean = out.replace(/\x1b\[[0-9;]*m/g, "");
    assert.ok(
      clean.includes("ui:compose"),
      `Should contain 'ui:compose', got: ${clean.trim()}`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

console.log(`\n${passed} passed, ${failed} failed\n`);
if (failed > 0) process.exit(1);

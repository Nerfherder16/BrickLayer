/**
 * Tests for masonry-tool-failure.js
 *
 * Verifies that state file path is scoped to project slug + tool name,
 * so concurrent sessions in different projects don't cross-contaminate.
 *
 * Run with: node --test tests/test_tool_failure_hook.js
 */

"use strict";

const { test, describe, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync, spawnSync } = require("child_process");

// ──────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────

function slugify(cwd) {
  // Must match the logic in masonry-tool-failure.js
  return cwd.replace(/[^a-zA-Z0-9]/g, "-").replace(/-+/g, "-").slice(-40);
}

function stateFilePath(projectCwd, toolName) {
  const slug = slugify(projectCwd);
  return path.join(os.homedir(), ".masonry", "state", `${slug}-${toolName}.json`);
}

function runHook(input, cwd) {
  const hookPath = path.join(__dirname, "..", "masonry", "src", "hooks", "masonry-tool-failure.js");
  const result = spawnSync("node", [hookPath], {
    input: JSON.stringify(input),
    encoding: "utf8",
    cwd: cwd || process.cwd(),
    timeout: 5000,
  });
  return result;
}

function cleanup(stateFile) {
  try { fs.unlinkSync(stateFile); } catch (_) {}
  // Also attempt to clean parent dir if empty
  try {
    const dir = path.dirname(stateFile);
    if (fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
  } catch (_) {}
}

// ──────────────────────────────────────────────────────────────────────────
// Test: state file path includes project slug
// ──────────────────────────────────────────────────────────────────────────

test("state file path includes project slug derived from CWD", () => {
  const cwd = "C:\\Users\\trg16\\Dev\\Bricklayer2.0";
  const slug = slugify(cwd);
  const statePath = stateFilePath(cwd, "Write");

  // The path should contain the slug
  assert.ok(statePath.includes(slug), `Expected path to contain slug '${slug}', got: ${statePath}`);
});

// ──────────────────────────────────────────────────────────────────────────
// Test: different project dirs produce different state file paths
// ──────────────────────────────────────────────────────────────────────────

test("two different project dirs produce different state file paths for same tool", () => {
  const cwd1 = "C:\\Users\\trg16\\Dev\\Bricklayer2.0";
  const cwd2 = "C:\\Users\\trg16\\Dev\\OtherProject";

  const path1 = stateFilePath(cwd1, "Write");
  const path2 = stateFilePath(cwd2, "Write");

  assert.notEqual(path1, path2,
    `Expected different paths for different projects, but both were: ${path1}`);
});

// ──────────────────────────────────────────────────────────────────────────
// Test: different tools produce different state file paths in same project
// ──────────────────────────────────────────────────────────────────────────

test("two different tools produce different state file paths in same project", () => {
  const cwd = "C:\\Users\\trg16\\Dev\\Bricklayer2.0";

  const pathWrite = stateFilePath(cwd, "Write");
  const pathBash = stateFilePath(cwd, "Bash");
  const pathEdit = stateFilePath(cwd, "Edit");

  assert.notEqual(pathWrite, pathBash,
    "Write and Bash should have different state file paths");
  assert.notEqual(pathWrite, pathEdit,
    "Write and Edit should have different state file paths");
  assert.notEqual(pathBash, pathEdit,
    "Bash and Edit should have different state file paths");
});

// ──────────────────────────────────────────────────────────────────────────
// Test: strike count increments correctly within a project
// ──────────────────────────────────────────────────────────────────────────

test("strike count increments for same tool + error in same project", () => {
  const cwd = process.cwd();
  const toolName = "TestTool";
  const stateFile = stateFilePath(cwd, toolName);

  // Clean up before test
  cleanup(stateFile);

  const input = { tool_name: toolName, tool_response: "Error: connection refused" };

  try {
    // First failure
    runHook(input, cwd);

    // Read state after first failure
    let state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    assert.equal(state.retries, 1, `Expected retries=1 after first failure, got ${state.retries}`);

    // Second failure (same error)
    runHook(input, cwd);
    state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    assert.equal(state.retries, 2, `Expected retries=2 after second failure, got ${state.retries}`);

    // Third failure
    runHook(input, cwd);
    state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    assert.equal(state.retries, 3, `Expected retries=3 after third failure, got ${state.retries}`);
  } finally {
    cleanup(stateFile);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// Test: strike counts for different tools are independent
// ──────────────────────────────────────────────────────────────────────────

test("strike counts for different tools are independent", () => {
  const cwd = process.cwd();
  const tool1 = "WriteTool";
  const tool2 = "BashTool";
  const stateFile1 = stateFilePath(cwd, tool1);
  const stateFile2 = stateFilePath(cwd, tool2);

  cleanup(stateFile1);
  cleanup(stateFile2);

  try {
    const input1 = { tool_name: tool1, tool_response: "Error: write failed" };
    const input2 = { tool_name: tool2, tool_response: "Error: bash failed" };

    // Fail tool1 twice
    runHook(input1, cwd);
    runHook(input1, cwd);

    // Fail tool2 once
    runHook(input2, cwd);

    const state1 = JSON.parse(fs.readFileSync(stateFile1, "utf8"));
    const state2 = JSON.parse(fs.readFileSync(stateFile2, "utf8"));

    assert.equal(state1.retries, 2, `tool1 should have 2 retries, got ${state1.retries}`);
    assert.equal(state2.retries, 1, `tool2 should have 1 retry, got ${state2.retries}`);
  } finally {
    cleanup(stateFile1);
    cleanup(stateFile2);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// Test: reaching 3 strikes triggers escalation output
// ──────────────────────────────────────────────────────────────────────────

test("reaching 3 strikes writes escalation message to stderr", () => {
  const cwd = process.cwd();
  const toolName = "EscalateTestTool";
  const stateFile = stateFilePath(cwd, toolName);

  cleanup(stateFile);

  const input = { tool_name: toolName, tool_response: "Error: persistent failure" };

  try {
    // Run 3 times to trigger escalation
    runHook(input, cwd);
    runHook(input, cwd);
    const result3 = runHook(input, cwd);

    // Third run should produce escalation message
    assert.ok(
      result3.stderr.includes("3-strike") || result3.stderr.includes("diagnose"),
      `Expected escalation message in stderr, got: ${result3.stderr}`
    );
  } finally {
    cleanup(stateFile);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// Test: first two strikes produce standard guidance (not escalation)
// ──────────────────────────────────────────────────────────────────────────

test("first two strikes produce standard guidance, not escalation", () => {
  const cwd = process.cwd();
  const toolName = "StandardGuidanceTool";
  const stateFile = stateFilePath(cwd, toolName);

  cleanup(stateFile);

  const input = { tool_name: toolName, tool_response: "Error: temporary failure" };

  try {
    const result1 = runHook(input, cwd);
    const result2 = runHook(input, cwd);

    // Should NOT have escalation message
    assert.ok(
      !result1.stderr.includes("3-strike"),
      `First strike should not trigger escalation: ${result1.stderr}`
    );
    assert.ok(
      !result2.stderr.includes("3-strike"),
      `Second strike should not trigger escalation: ${result2.stderr}`
    );
    // Should have standard guidance
    assert.ok(
      result1.stderr.includes("attempt") || result1.stderr.includes("failed"),
      `First strike should have standard guidance: ${result1.stderr}`
    );
  } finally {
    cleanup(stateFile);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// Test: state file name format is {slug}-{toolName}.json (flat, no subdirectory)
// ──────────────────────────────────────────────────────────────────────────

test("state file is flat in .masonry/state/ with slug-toolname format", () => {
  const cwd = process.cwd();
  const toolName = "TestTool";
  const stateFile = stateFilePath(cwd, toolName);

  // Should be directly in .masonry/state/, not in a subdirectory
  const stateDir = path.join(os.homedir(), ".masonry", "state");
  const relativePath = path.relative(stateDir, stateFile);

  // relativePath should be just a filename (no directory separators)
  assert.ok(
    !relativePath.includes(path.sep),
    `Expected flat file in .masonry/state/, but got subdirectory: ${relativePath}`
  );

  // Filename should end with -{toolName}.json
  assert.ok(
    path.basename(stateFile).endsWith(`-${toolName}.json`),
    `Expected filename to end with -${toolName}.json, got: ${path.basename(stateFile)}`
  );
});

#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

const MASONRY_ROOT = path.join(__dirname, "..");
const FLEET_CLI = path.join(
  MASONRY_ROOT,
  "masonry",
  "bin",
  "masonry-fleet-cli.js",
);

function run(args, cwd) {
  return execSync(`node "${FLEET_CLI}" ${args}`, {
    encoding: "utf8",
    timeout: 10000,
    cwd: cwd || MASONRY_ROOT,
  });
}

function makeTestProject() {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "masonry-fleet-test-"));
  const agentsDir = path.join(tmpDir, ".claude", "agents");
  fs.mkdirSync(agentsDir, { recursive: true });

  // Write two agent files with valid frontmatter
  const agent1 = `---\nname: test-alpha\ndescription: Alpha test agent\nmodel: sonnet\n---\n\nAlpha agent body.\n`;
  const agent2 = `---\nname: test-beta\ndescription: Beta test agent\nmodel: haiku\n---\n\nBeta agent body.\n`;
  fs.writeFileSync(path.join(agentsDir, "test-alpha.md"), agent1);
  fs.writeFileSync(path.join(agentsDir, "test-beta.md"), agent2);

  // Run regen so registry.json exists and status can read agent names
  run(`regen "${tmpDir}"`, MASONRY_ROOT);

  return tmpDir;
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

console.log("\ntest_masonry_fleet_cli.js\n");

// T1: status shows both agents
test("status: shows table with both agents", () => {
  const tmpDir = makeTestProject();
  try {
    const out = run(`status "${tmpDir}"`, MASONRY_ROOT);
    assert.ok(
      out.includes("test-alpha"),
      `Should contain test-alpha, got:\n${out}`,
    );
    assert.ok(
      out.includes("test-beta"),
      `Should contain test-beta, got:\n${out}`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T2: add creates agent file and updates registry
test("add: creates agent file and updates registry", () => {
  const tmpDir = makeTestProject();
  try {
    run(`add test-gamma "${tmpDir}"`, MASONRY_ROOT);
    const agentFile = path.join(tmpDir, ".claude", "agents", "test-gamma.md");
    assert.ok(
      fs.existsSync(agentFile),
      `Agent file should exist at ${agentFile}`,
    );
    const registry = path.join(tmpDir, "registry.json");
    assert.ok(fs.existsSync(registry), "registry.json should exist after add");
    const reg = JSON.parse(fs.readFileSync(registry, "utf8"));
    const names = (reg.agents || []).map((a) => a.name);
    assert.ok(
      names.includes("test-gamma"),
      `registry.json should contain test-gamma, got: ${names}`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T3: retire moves file and updates registry
test("retire: moves file to .retired/ and removes from registry", () => {
  const tmpDir = makeTestProject();
  try {
    run(`retire test-alpha "${tmpDir}"`, MASONRY_ROOT);
    const original = path.join(tmpDir, ".claude", "agents", "test-alpha.md");
    const retired = path.join(
      tmpDir,
      ".claude",
      "agents",
      ".retired",
      "test-alpha.md",
    );
    assert.ok(!fs.existsSync(original), "Original file should be gone");
    assert.ok(
      fs.existsSync(retired),
      `Retired file should exist at ${retired}`,
    );
    const registry = path.join(tmpDir, "registry.json");
    if (fs.existsSync(registry)) {
      const reg = JSON.parse(fs.readFileSync(registry, "utf8"));
      const names = (reg.agents || []).map((a) => a.name);
      assert.ok(
        !names.includes("test-alpha"),
        "test-alpha should not be in registry after retire",
      );
    }
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T4: regen updates registry to match actual agent count
test("regen: registry count matches actual agent files", () => {
  const tmpDir = makeTestProject();
  try {
    run(`regen "${tmpDir}"`, MASONRY_ROOT);
    const registry = path.join(tmpDir, "registry.json");
    assert.ok(
      fs.existsSync(registry),
      "registry.json should exist after regen",
    );
    const reg = JSON.parse(fs.readFileSync(registry, "utf8"));
    const agentsDir = path.join(tmpDir, ".claude", "agents");
    const actualFiles = fs
      .readdirSync(agentsDir)
      .filter((f) => f.endsWith(".md"));
    assert.strictEqual(
      (reg.agents || []).length,
      actualFiles.length,
      `Registry count (${(reg.agents || []).length}) should match file count (${actualFiles.length})`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// T5: status shows summary line
test("status: shows summary line", () => {
  const tmpDir = makeTestProject();
  try {
    const out = run(`status "${tmpDir}"`, MASONRY_ROOT);
    assert.ok(
      out.toLowerCase().includes("summary") || out.includes("agent"),
      `Should show summary, got:\n${out}`,
    );
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

console.log(`\n${passed} passed, ${failed} failed\n`);
if (failed > 0) process.exit(1);

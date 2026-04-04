/**
 * masonry/tests/test_impl_patterns_confidence.test.js
 *
 * Tests for toolPatternPromote and toolPatternDemote in impl-patterns.js.
 * Written BEFORE implementation. All tests must FAIL until the developer
 * implements toolPatternPromote and toolPatternDemote.
 *
 * Behavior under test:
 *   toolPatternPromote({ agent_type, project_dir })
 *     - Reads {project_dir}/.autopilot/pattern-confidence.json
 *     - If agent_type absent, initializes with confidence 0.76
 *     - Applies ceiling formula: confidence = conf + 0.2 * (1.0 - conf)
 *     - Increments uses, updates last_used, writes back
 *     - Returns { agent_type, old_confidence, new_confidence, uses }
 *
 *   toolPatternDemote({ agent_type, project_dir })
 *     - Reads same file
 *     - Applies proportional reduction: confidence = conf - 0.15 * conf
 *     - Floor: never below 0.1
 *     - Increments uses, updates last_used, writes back
 *     - Returns { agent_type, old_confidence, new_confidence, uses }
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import os from "os";

const require = createRequire(import.meta.url);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let tempDir;

function setup() {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "impl-patterns-conf-"));
  // Create .autopilot/ subdirectory — the functions should also handle its absence,
  // but we scaffold the directory for the basic cases.
  fs.mkdirSync(path.join(tempDir, ".autopilot"), { recursive: true });
}

function teardown() {
  try {
    fs.rmSync(tempDir, { recursive: true, force: true });
  } catch (_) {}
}

function loadImpl() {
  // Force fresh load each time so state does not bleed between tests.
  delete require.cache[require.resolve("../src/tools/impl-patterns.js")];
  return require("../src/tools/impl-patterns.js");
}

function confidencePath() {
  return path.join(tempDir, ".autopilot", "pattern-confidence.json");
}

function writeConfidence(data) {
  fs.writeFileSync(confidencePath(), JSON.stringify(data, null, 2));
}

function readConfidence() {
  return JSON.parse(fs.readFileSync(confidencePath(), "utf8"));
}

// Tolerance for floating-point comparisons
const EPSILON = 0.0001;

// ---------------------------------------------------------------------------
// Export contract
// ---------------------------------------------------------------------------

describe("impl-patterns export contract", () => {
  it("exports toolPatternPromote as a function", () => {
    const impl = loadImpl();
    expect(typeof impl.toolPatternPromote).toBe("function");
  });

  it("exports toolPatternDemote as a function", () => {
    const impl = loadImpl();
    expect(typeof impl.toolPatternDemote).toBe("function");
  });
});

// ---------------------------------------------------------------------------
// toolPatternPromote — new agent (initialization path)
// ---------------------------------------------------------------------------

describe("toolPatternPromote — new agent initialization", () => {
  beforeEach(setup);
  afterEach(teardown);

  it("initializes missing agent at 0.76 then promotes to ~0.808", () => {
    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "developer",
      project_dir: tempDir,
    });

    // old_confidence must be the initialization value 0.76
    expect(result.old_confidence).toBeCloseTo(0.76, 4);

    // Ceiling formula: 0.76 + 0.2 * (1 - 0.76) = 0.76 + 0.2 * 0.24 = 0.76 + 0.048 = 0.808
    expect(result.new_confidence).toBeCloseTo(0.808, 4);

    expect(result.agent_type).toBe("developer");
    expect(typeof result.uses).toBe("number");
    expect(result.uses).toBeGreaterThanOrEqual(1);
  });

  it("creates pattern-confidence.json when the file does not exist", () => {
    const impl = loadImpl();
    // File must not exist before the call
    expect(fs.existsSync(confidencePath())).toBe(false);

    impl.toolPatternPromote({
      agent_type: "test-writer",
      project_dir: tempDir,
    });

    expect(fs.existsSync(confidencePath())).toBe(true);
  });

  it("persists the promoted confidence to disk", () => {
    const impl = loadImpl();
    impl.toolPatternPromote({
      agent_type: "developer",
      project_dir: tempDir,
    });

    const stored = readConfidence();
    expect(stored["developer"]).toBeDefined();
    expect(stored["developer"].confidence).toBeCloseTo(0.808, 4);
  });

  it("sets last_used on the newly created entry", () => {
    const impl = loadImpl();
    const before = Date.now();

    impl.toolPatternPromote({
      agent_type: "developer",
      project_dir: tempDir,
    });

    const stored = readConfidence();
    const lastUsed = new Date(stored["developer"].last_used).getTime();
    expect(lastUsed).toBeGreaterThanOrEqual(before);
  });
});

// ---------------------------------------------------------------------------
// toolPatternPromote — existing agent at 0.9
// ---------------------------------------------------------------------------

describe("toolPatternPromote — existing agent ceiling math", () => {
  beforeEach(setup);
  afterEach(teardown);

  it("promotes 0.9 to ~0.92 using ceiling formula", () => {
    // Pre-seed the file with an agent already at 0.9
    writeConfidence({
      "code-reviewer": { confidence: 0.9, uses: 5, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "code-reviewer",
      project_dir: tempDir,
    });

    // old confidence must be read back correctly
    expect(result.old_confidence).toBeCloseTo(0.9, 4);

    // Ceiling formula: 0.9 + 0.2 * (1 - 0.9) = 0.9 + 0.2 * 0.1 = 0.9 + 0.02 = 0.92
    expect(result.new_confidence).toBeCloseTo(0.92, 4);
  });

  it("increments uses on an existing entry", () => {
    writeConfidence({
      "code-reviewer": { confidence: 0.9, uses: 5, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "code-reviewer",
      project_dir: tempDir,
    });

    expect(result.uses).toBe(6);
  });

  it("written confidence approaches but never exceeds 1.0", () => {
    // Start very close to ceiling
    writeConfidence({
      "agent-x": { confidence: 0.999, uses: 100, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "agent-x",
      project_dir: tempDir,
    });

    expect(result.new_confidence).toBeLessThanOrEqual(1.0);
    // And it moved upward from 0.999
    expect(result.new_confidence).toBeGreaterThanOrEqual(result.old_confidence);
  });
});

// ---------------------------------------------------------------------------
// toolPatternDemote — existing agent at 0.9
// ---------------------------------------------------------------------------

describe("toolPatternDemote — proportional reduction", () => {
  beforeEach(setup);
  afterEach(teardown);

  it("demotes 0.9 to ~0.765", () => {
    writeConfidence({
      "research-analyst": { confidence: 0.9, uses: 3, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "research-analyst",
      project_dir: tempDir,
    });

    expect(result.old_confidence).toBeCloseTo(0.9, 4);

    // Proportional reduction: 0.9 - 0.15 * 0.9 = 0.9 - 0.135 = 0.765
    expect(result.new_confidence).toBeCloseTo(0.765, 4);
  });

  it("increments uses on demote", () => {
    writeConfidence({
      "research-analyst": { confidence: 0.9, uses: 3, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "research-analyst",
      project_dir: tempDir,
    });

    expect(result.uses).toBe(4);
  });

  it("persists the demoted confidence to disk", () => {
    writeConfidence({
      "research-analyst": { confidence: 0.9, uses: 3, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    impl.toolPatternDemote({
      agent_type: "research-analyst",
      project_dir: tempDir,
    });

    const stored = readConfidence();
    expect(stored["research-analyst"].confidence).toBeCloseTo(0.765, 4);
  });
});

// ---------------------------------------------------------------------------
// toolPatternDemote — floor enforcement at 0.1
// ---------------------------------------------------------------------------

describe("toolPatternDemote — floor at 0.1", () => {
  beforeEach(setup);
  afterEach(teardown);

  it("does not reduce confidence below 0.1 when already at 0.1", () => {
    writeConfidence({
      "low-agent": { confidence: 0.1, uses: 10, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "low-agent",
      project_dir: tempDir,
    });

    expect(result.new_confidence).toBeCloseTo(0.1, 4);
    expect(result.new_confidence).toBeGreaterThanOrEqual(0.1 - EPSILON);
  });

  it("clamps to 0.1 when the formula would go below the floor", () => {
    // A value just above the floor — after 15% reduction it would drop below 0.1
    writeConfidence({
      "weak-agent": { confidence: 0.11, uses: 2, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "weak-agent",
      project_dir: tempDir,
    });

    // 0.11 - 0.15 * 0.11 = 0.11 - 0.0165 = 0.0935 → clamped to 0.1
    expect(result.new_confidence).toBeCloseTo(0.1, 4);
    expect(result.new_confidence).toBeGreaterThanOrEqual(0.1 - EPSILON);
  });

  it("writes the floored value (0.1) to disk, not the raw formula result", () => {
    writeConfidence({
      "weak-agent": { confidence: 0.11, uses: 2, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    impl.toolPatternDemote({
      agent_type: "weak-agent",
      project_dir: tempDir,
    });

    const stored = readConfidence();
    expect(stored["weak-agent"].confidence).toBeGreaterThanOrEqual(0.1 - EPSILON);
    expect(stored["weak-agent"].confidence).toBeCloseTo(0.1, 4);
  });
});

// ---------------------------------------------------------------------------
// Missing file handling — both functions must create the file if absent
// ---------------------------------------------------------------------------

describe("missing pattern-confidence.json — graceful creation", () => {
  beforeEach(() => {
    // Create tempDir but do NOT create .autopilot or pattern-confidence.json
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "impl-patterns-missing-"));
  });
  afterEach(teardown);

  it("toolPatternPromote creates the file when .autopilot dir is absent", () => {
    expect(fs.existsSync(path.join(tempDir, ".autopilot"))).toBe(false);

    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "new-agent",
      project_dir: tempDir,
    });

    expect(fs.existsSync(confidencePath())).toBe(true);
    expect(result.agent_type).toBe("new-agent");
    expect(typeof result.new_confidence).toBe("number");
  });

  it("toolPatternDemote creates the file when .autopilot dir is absent", () => {
    expect(fs.existsSync(path.join(tempDir, ".autopilot"))).toBe(false);

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "new-agent",
      project_dir: tempDir,
    });

    expect(fs.existsSync(confidencePath())).toBe(true);
    expect(result.agent_type).toBe("new-agent");
    expect(typeof result.new_confidence).toBe("number");
  });

  it("toolPatternDemote on a brand-new agent respects the floor", () => {
    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "brand-new",
      project_dir: tempDir,
    });

    // Whatever initialization value is chosen, demote must still respect floor
    expect(result.new_confidence).toBeGreaterThanOrEqual(0.1 - EPSILON);
  });
});

// ---------------------------------------------------------------------------
// Return shape contract
// ---------------------------------------------------------------------------

describe("return shape contract", () => {
  beforeEach(setup);
  afterEach(teardown);

  it("toolPatternPromote returns all four required keys", () => {
    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "shape-test",
      project_dir: tempDir,
    });

    expect(result).toHaveProperty("agent_type");
    expect(result).toHaveProperty("old_confidence");
    expect(result).toHaveProperty("new_confidence");
    expect(result).toHaveProperty("uses");
  });

  it("toolPatternDemote returns all four required keys", () => {
    writeConfidence({
      "shape-test": { confidence: 0.7, uses: 1, last_used: new Date().toISOString() },
    });

    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "shape-test",
      project_dir: tempDir,
    });

    expect(result).toHaveProperty("agent_type");
    expect(result).toHaveProperty("old_confidence");
    expect(result).toHaveProperty("new_confidence");
    expect(result).toHaveProperty("uses");
  });

  it("toolPatternPromote agent_type in return matches input", () => {
    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "my-specialist",
      project_dir: tempDir,
    });
    expect(result.agent_type).toBe("my-specialist");
  });

  it("toolPatternDemote agent_type in return matches input", () => {
    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "my-specialist",
      project_dir: tempDir,
    });
    expect(result.agent_type).toBe("my-specialist");
  });

  it("new_confidence is a number between 0 and 1 after promote", () => {
    const impl = loadImpl();
    const result = impl.toolPatternPromote({
      agent_type: "bounds-check",
      project_dir: tempDir,
    });
    expect(result.new_confidence).toBeGreaterThan(0);
    expect(result.new_confidence).toBeLessThanOrEqual(1.0);
  });

  it("new_confidence is a number >= 0.1 after demote", () => {
    const impl = loadImpl();
    const result = impl.toolPatternDemote({
      agent_type: "bounds-check-demote",
      project_dir: tempDir,
    });
    expect(result.new_confidence).toBeGreaterThanOrEqual(0.1 - EPSILON);
    expect(result.new_confidence).toBeLessThanOrEqual(1.0);
  });
});

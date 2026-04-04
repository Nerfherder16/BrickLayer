/**
 * masonry/tests/hooks/test_build_outcome.test.js
 *
 * Tests for masonry-build-outcome.js — PostToolUse:Write hook that watches
 * .autopilot/progress.json for task state transitions and calls
 * toolPatternPromote / toolPatternDemote.
 *
 * Written BEFORE implementation. All tests must fail until the developer
 * completes masonry/src/hooks/masonry-build-outcome.js.
 *
 * Convention matches existing hook tests in this directory:
 *   - Run the hook as a subprocess via spawnSync
 *   - Assert side effects on the filesystem (pattern-confidence.json, cache file)
 *   - Never mock the core logic under test; only isolate via filesystem fixtures
 */

import { spawnSync } from "child_process";
import {
  mkdtempSync,
  writeFileSync,
  mkdirSync,
  readFileSync,
  existsSync,
  unlinkSync,
  rmSync,
} from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

// ---------------------------------------------------------------------------
// Path to the hook under test (does not exist yet — that is intentional)
// ---------------------------------------------------------------------------
const HOOK = join(process.cwd(), "src", "hooks", "masonry-build-outcome.js");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Run the hook with a given cwd and stdin payload. Returns { exitCode, stdout, stderr }. */
function runHook(cwd, stdinPayload) {
  const env = { ...process.env };
  delete env.PWD; // force hook to use process.cwd(), not inherited shell PWD
  const result = spawnSync("node", [HOOK], {
    input: JSON.stringify(stdinPayload),
    cwd,
    env,
    stdio: ["pipe", "pipe", "pipe"],
    encoding: "utf8",
    timeout: 10000,
  });
  return {
    exitCode: result.status ?? 1,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
  };
}

/** Create a fresh temp directory for each test. */
function makeDir() {
  return mkdtempSync(join(tmpdir(), "build-outcome-test-"));
}

/**
 * Write .autopilot/mode and .autopilot/progress.json into dir.
 * Returns the path to progress.json.
 */
function writeAutopilot(dir, { mode = "build", tasks = [] } = {}) {
  const autopilotDir = join(dir, ".autopilot");
  mkdirSync(autopilotDir, { recursive: true });
  writeFileSync(join(autopilotDir, "mode"), mode, "utf8");
  const progressPath = join(autopilotDir, "progress.json");
  writeFileSync(
    progressPath,
    JSON.stringify({ status: "BUILDING", tasks }),
    "utf8"
  );
  return progressPath;
}

/**
 * Write the prev-state cache file that the hook reads to detect transitions.
 * session_id → used to form the cache file name in os.tmpdir().
 */
function writePrevCache(sessionId, taskStates) {
  // Hook is specified to use: {os.tmpdir()}/masonry-outcome-prev-{sessionId}.json
  const cachePath = join(tmpdir(), `masonry-outcome-prev-${sessionId}.json`);
  writeFileSync(cachePath, JSON.stringify(taskStates), "utf8");
  return cachePath;
}

/** Read .autopilot/pattern-confidence.json from dir. Returns parsed object or null. */
function readConfidence(dir) {
  const confPath = join(dir, ".autopilot", "pattern-confidence.json");
  if (!existsSync(confPath)) return null;
  return JSON.parse(readFileSync(confPath, "utf8"));
}

/** Build a minimal hook stdin payload for a Write to progress.json. */
function progressWritePayload(progressPath, sessionId) {
  return {
    tool_name: "Write",
    tool_input: { file_path: progressPath },
    session_id: sessionId,
  };
}

// ---------------------------------------------------------------------------
// 1. DONE transition → toolPatternPromote called with correct agent_type
// ---------------------------------------------------------------------------

describe("DONE transition fires toolPatternPromote", () => {
  it("increases confidence for 'developer' when a plain task transitions to DONE", () => {
    const dir = makeDir();
    const sessionId = "sess-done-plain";

    // Previous state: task 1 was PENDING
    writePrevCache(sessionId, { "1": "PENDING" });

    // Current state: task 1 is now DONE (no mode annotation → developer)
    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "DONE", description: "Implement auth endpoint" }],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["developer"]).toBeDefined();
    // Promote increases confidence above the 0.76 initial value
    expect(conf["developer"].confidence).toBeGreaterThan(0.76);
  });

  it("increases confidence for 'python-specialist' when [mode:python] task transitions to DONE", () => {
    const dir = makeDir();
    const sessionId = "sess-done-python";

    writePrevCache(sessionId, { "2": "IN_PROGRESS" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        {
          id: 2,
          status: "DONE",
          description: "Write FastAPI route [mode:python]",
        },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["python-specialist"]).toBeDefined();
    expect(conf["python-specialist"].confidence).toBeGreaterThan(0.76);
    // developer should NOT have been touched
    expect(conf["developer"]).toBeUndefined();
  });

  it("increases confidence for 'typescript-specialist' when [mode:typescript] task transitions to DONE", () => {
    const dir = makeDir();
    const sessionId = "sess-done-ts";

    writePrevCache(sessionId, { "3": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        {
          id: 3,
          status: "DONE",
          description: "Add React component [mode:typescript]",
        },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["typescript-specialist"]).toBeDefined();
    expect(conf["typescript-specialist"].confidence).toBeGreaterThan(0.76);
  });

  it("records `uses` counter for the agent on promotion", () => {
    const dir = makeDir();
    const sessionId = "sess-done-uses";

    writePrevCache(sessionId, { "1": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "DONE", description: "Task without annotation" }],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf["developer"].uses).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// 2. FAILED transition → toolPatternDemote called with correct agent_type
// ---------------------------------------------------------------------------

describe("FAILED transition fires toolPatternDemote", () => {
  it("decreases confidence for 'developer' when a plain task transitions to FAILED", () => {
    const dir = makeDir();
    const sessionId = "sess-fail-plain";

    writePrevCache(sessionId, { "10": "IN_PROGRESS" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        { id: 10, status: "FAILED", description: "Build thing without annotation" },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["developer"]).toBeDefined();
    // Demote decreases confidence below the 0.76 initial value
    expect(conf["developer"].confidence).toBeLessThan(0.76);
  });

  it("decreases confidence for 'tdd-london-swarm' when [mode:tdd] task transitions to FAILED", () => {
    const dir = makeDir();
    const sessionId = "sess-fail-tdd";

    writePrevCache(sessionId, { "5": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "fix",
      tasks: [
        {
          id: 5,
          status: "FAILED",
          description: "Add test coverage [mode:tdd]",
        },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["tdd-london-swarm"]).toBeDefined();
    expect(conf["tdd-london-swarm"].confidence).toBeLessThan(0.76);
    expect(conf["developer"]).toBeUndefined();
  });

  it("decreases confidence for 'security' when [mode:security] task transitions to FAILED", () => {
    const dir = makeDir();
    const sessionId = "sess-fail-security";

    writePrevCache(sessionId, { "7": "IN_PROGRESS" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        {
          id: 7,
          status: "FAILED",
          description: "Audit input validation [mode:security]",
        },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf["security"]).toBeDefined();
    expect(conf["security"].confidence).toBeLessThan(0.76);
  });

  it("confidence never drops below 0.1 after repeated demotions", () => {
    const dir = makeDir();
    const sessionId = "sess-floor";

    // Seed pattern-confidence.json with very low existing confidence
    const autopilotDir = join(dir, ".autopilot");
    mkdirSync(autopilotDir, { recursive: true });
    writeFileSync(
      join(autopilotDir, "pattern-confidence.json"),
      JSON.stringify({ developer: { confidence: 0.11, uses: 20, last_used: new Date().toISOString() } }),
      "utf8"
    );

    writePrevCache(sessionId, { "1": "IN_PROGRESS" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "FAILED", description: "Task" }],
    });

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    // Hook must have run and exited cleanly
    expect(result.exitCode).toBe(0);
    const conf = readConfidence(dir);
    // After demote, confidence is updated (not the original seeded 0.11)
    // toolPatternDemote computes: max(0.1, 0.11 - 0.15*0.11) = max(0.1, 0.0935) = 0.1
    expect(conf["developer"].confidence).toBeGreaterThanOrEqual(0.1);
    // Specifically, it should have been modified from the seeded value of 0.11
    expect(conf["developer"].confidence).not.toBe(0.11);
  });
});

// ---------------------------------------------------------------------------
// 3. No transition (already DONE in prev) → neither promote nor demote
// ---------------------------------------------------------------------------

describe("no transition when task already had terminal state in prev cache", () => {
  it("does NOT write pattern-confidence.json when task was already DONE", () => {
    const dir = makeDir();
    const sessionId = "sess-no-transition";

    // Previous state already DONE
    writePrevCache(sessionId, { "1": "DONE" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "DONE", description: "Already complete task" }],
    });

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    // Hook must have run and exited cleanly
    expect(result.exitCode).toBe(0);
    // No confidence file should have been created (no new transition)
    const conf = readConfidence(dir);
    expect(conf).toBeNull();
  });

  it("does NOT write pattern-confidence.json when task was already FAILED", () => {
    const dir = makeDir();
    const sessionId = "sess-no-transition-fail";

    writePrevCache(sessionId, { "2": "FAILED" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 2, status: "FAILED", description: "Already failed task" }],
    });

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    // Hook must have run cleanly
    expect(result.exitCode).toBe(0);
    const conf = readConfidence(dir);
    expect(conf).toBeNull();
  });

  it("only promotes the task that newly reached DONE, not existing DONE tasks", () => {
    const dir = makeDir();
    const sessionId = "sess-partial-transition";

    // Task 1 was DONE, task 2 was PENDING
    writePrevCache(sessionId, { "1": "DONE", "2": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        { id: 1, status: "DONE", description: "Old task [mode:python]" },
        { id: 2, status: "DONE", description: "New task [mode:typescript]" },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    // Only typescript-specialist should have been promoted (task 2 transitioned)
    expect(conf["typescript-specialist"]).toBeDefined();
    // python-specialist was already DONE — should not have been touched
    expect(conf["python-specialist"]).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// 4. Mode annotation parsing
// ---------------------------------------------------------------------------

describe("mode annotation inference maps [mode:X] to correct agent_type", () => {
  const ANNOTATION_MAP = [
    { annotation: "[mode:python]", expected: "python-specialist" },
    { annotation: "[mode:typescript]", expected: "typescript-specialist" },
    { annotation: "[mode:database]", expected: "database-specialist" },
    { annotation: "[mode:tdd]", expected: "tdd-london-swarm" },
    { annotation: "[mode:devops]", expected: "devops" },
    { annotation: "[mode:security]", expected: "security" },
    { annotation: "[mode:architect]", expected: "architect" },
  ];

  for (const { annotation, expected } of ANNOTATION_MAP) {
    it(`maps ${annotation} → ${expected}`, () => {
      const dir = makeDir();
      const sessionId = `sess-annot-${expected}`;

      writePrevCache(sessionId, { "1": "PENDING" });

      const progressPath = writeAutopilot(dir, {
        mode: "build",
        tasks: [
          { id: 1, status: "DONE", description: `Do the thing ${annotation}` },
        ],
      });

      runHook(dir, progressWritePayload(progressPath, sessionId));

      const conf = readConfidence(dir);
      expect(conf).not.toBeNull();
      expect(conf[expected]).toBeDefined();
      // Ensure only the expected agent type was written
      expect(Object.keys(conf)).toEqual([expected]);
    });
  }

  it("uses 'developer' as agent_type when description has no [mode:X] annotation", () => {
    const dir = makeDir();
    const sessionId = "sess-no-annotation";

    writePrevCache(sessionId, { "1": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "DONE", description: "Build the widget" }],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["developer"]).toBeDefined();
    expect(Object.keys(conf)).toEqual(["developer"]);
  });

  it("annotation is case-insensitive — [mode:Python] resolves to python-specialist", () => {
    const dir = makeDir();
    const sessionId = "sess-case-insensitive";

    writePrevCache(sessionId, { "1": "PENDING" });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        {
          id: 1,
          status: "DONE",
          description: "Do work [mode:Python]",
        },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    // Should still resolve to python-specialist
    expect(conf["python-specialist"]).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// 5. Non-progress.json write → exits immediately without any side effects
// ---------------------------------------------------------------------------

describe("non-progress.json write exits immediately with no side effects", () => {
  it("exits 0 and writes nothing when file_path is a .js source file", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build", "utf8");

    const result = runHook(dir, {
      tool_name: "Write",
      tool_input: { file_path: join(dir, "src", "app.js") },
      session_id: "sess-irrelevant",
    });

    expect(result.exitCode).toBe(0);
    expect(existsSync(join(dir, ".autopilot", "pattern-confidence.json"))).toBe(false);
  });

  it("exits 0 and writes nothing when file_path ends in unrelated .json", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build", "utf8");

    const result = runHook(dir, {
      tool_name: "Write",
      tool_input: { file_path: join(dir, ".autopilot", "spec.json") },
      session_id: "sess-irrelevant2",
    });

    expect(result.exitCode).toBe(0);
    expect(existsSync(join(dir, ".autopilot", "pattern-confidence.json"))).toBe(false);
  });

  it("exits 0 and writes nothing when file_path ends in pattern-confidence.json (avoid recursion)", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build", "utf8");

    const result = runHook(dir, {
      tool_name: "Write",
      tool_input: {
        file_path: join(dir, ".autopilot", "pattern-confidence.json"),
      },
      session_id: "sess-no-recursion",
    });

    expect(result.exitCode).toBe(0);
  });

  it("does not attempt to read progress.json at all when file path is irrelevant", () => {
    // If the hook tried to read progress.json when it should early-exit,
    // writing a malformed progress.json would cause an error/non-zero exit.
    const dir = makeDir();
    const autopilotDir = join(dir, ".autopilot");
    mkdirSync(autopilotDir, { recursive: true });
    writeFileSync(join(autopilotDir, "mode"), "build", "utf8");
    // Deliberately malformed — reading it would throw
    writeFileSync(join(autopilotDir, "progress.json"), "NOT VALID JSON", "utf8");

    const result = runHook(dir, {
      tool_name: "Write",
      tool_input: { file_path: join(dir, "src", "index.ts") },
      session_id: "sess-no-read",
    });

    // Hook must exit 0 cleanly — it should never have read progress.json
    expect(result.exitCode).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// 6. Mode guard — hook only fires when .autopilot/mode is "build" or "fix"
// ---------------------------------------------------------------------------

describe("mode guard — hook is a no-op outside build/fix modes", () => {
  it("writes nothing when .autopilot/mode is 'research'", () => {
    const dir = makeDir();
    const sessionId = "sess-research-mode";

    writePrevCache(sessionId, { "1": "PENDING" });

    // Mode = research, not build or fix
    const progressPath = writeAutopilot(dir, {
      mode: "research",
      tasks: [{ id: 1, status: "DONE", description: "Question sweep" }],
    });

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    // Hook must have run and exited cleanly (mode guard causes silent no-op, not crash)
    expect(result.exitCode).toBe(0);
    const conf = readConfidence(dir);
    expect(conf).toBeNull();
  });

  it("writes nothing when .autopilot/mode file is absent", () => {
    const dir = makeDir();
    const sessionId = "sess-no-mode";

    writePrevCache(sessionId, { "1": "PENDING" });

    // Create progress.json but NO mode file
    const autopilotDir = join(dir, ".autopilot");
    mkdirSync(autopilotDir, { recursive: true });
    const progressPath = join(autopilotDir, "progress.json");
    writeFileSync(
      progressPath,
      JSON.stringify({
        status: "BUILDING",
        tasks: [{ id: 1, status: "DONE", description: "Task" }],
      }),
      "utf8"
    );

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    // Hook must have run and exited cleanly
    expect(result.exitCode).toBe(0);
    const conf = readConfidence(dir);
    expect(conf).toBeNull();
  });

  it("promotes when .autopilot/mode is 'fix'", () => {
    const dir = makeDir();
    const sessionId = "sess-fix-mode";

    writePrevCache(sessionId, { "1": "IN_PROGRESS" });

    const progressPath = writeAutopilot(dir, {
      mode: "fix",
      tasks: [{ id: 1, status: "DONE", description: "Fix the broken thing" }],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();
    expect(conf["developer"]).toBeDefined();
    expect(conf["developer"].confidence).toBeGreaterThan(0.76);
  });
});

// ---------------------------------------------------------------------------
// 7. Cache update — hook writes current states to cache for next comparison
// ---------------------------------------------------------------------------

describe("cache file is updated after each run", () => {
  it("writes a cache file after processing progress.json", () => {
    const dir = makeDir();
    const sessionId = "sess-cache-write";

    // No prior cache
    const cachePath = join(tmpdir(), `masonry-outcome-prev-${sessionId}.json`);
    // Ensure it doesn't exist
    try { unlinkSync(cachePath); } catch { /* ok */ }

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "PENDING", description: "Pending task" }],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    // Cache file should now exist
    expect(existsSync(cachePath)).toBe(true);

    const cached = JSON.parse(readFileSync(cachePath, "utf8"));
    // Cache should contain the current state of task 1
    expect(cached["1"]).toBe("PENDING");
  });

  it("cache is keyed by task id and contains current status after run", () => {
    const dir = makeDir();
    const sessionId = "sess-cache-content";

    writePrevCache(sessionId, {});

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        { id: 10, status: "DONE", description: "Task A" },
        { id: 11, status: "FAILED", description: "Task B" },
        { id: 12, status: "PENDING", description: "Task C" },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const cachePath = join(tmpdir(), `masonry-outcome-prev-${sessionId}.json`);
    const cached = JSON.parse(readFileSync(cachePath, "utf8"));

    expect(cached["10"]).toBe("DONE");
    expect(cached["11"]).toBe("FAILED");
    expect(cached["12"]).toBe("PENDING");
  });
});

// ---------------------------------------------------------------------------
// 8. Silent failure — hook must exit 0 on any error (never block Claude)
// ---------------------------------------------------------------------------

describe("silent failure — hook exits 0 on errors", () => {
  it("exits 0 when progress.json is malformed JSON", () => {
    const dir = makeDir();
    const sessionId = "sess-bad-json";

    writePrevCache(sessionId, {});

    const autopilotDir = join(dir, ".autopilot");
    mkdirSync(autopilotDir, { recursive: true });
    writeFileSync(join(autopilotDir, "mode"), "build", "utf8");
    const progressPath = join(autopilotDir, "progress.json");
    writeFileSync(progressPath, "{ INVALID JSON", "utf8");

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    expect(result.exitCode).toBe(0);
  });

  it("exits 0 when progress.json does not exist", () => {
    const dir = makeDir();
    const sessionId = "sess-no-progress";

    writePrevCache(sessionId, {});

    const autopilotDir = join(dir, ".autopilot");
    mkdirSync(autopilotDir, { recursive: true });
    writeFileSync(join(autopilotDir, "mode"), "build", "utf8");
    // progress.json intentionally not written
    const progressPath = join(autopilotDir, "progress.json");

    const result = runHook(dir, progressWritePayload(progressPath, sessionId));

    expect(result.exitCode).toBe(0);
  });

  it("exits 0 when stdin is missing session_id", () => {
    const dir = makeDir();

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [{ id: 1, status: "DONE", description: "Task" }],
    });

    // No session_id in payload
    const result = runHook(dir, {
      tool_name: "Write",
      tool_input: { file_path: progressPath },
    });

    expect(result.exitCode).toBe(0);
  });

  it("exits 0 and does not crash when stdin is empty", () => {
    const dir = makeDir();
    const env = { ...process.env };
    delete env.PWD;
    const result = spawnSync("node", [HOOK], {
      input: "",
      cwd: dir,
      env,
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 10000,
    });
    expect(result.status ?? 1).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// 9. Multiple transitions in a single run
// ---------------------------------------------------------------------------

describe("multiple tasks can transition in a single progress.json write", () => {
  it("promotes developer for one DONE task and demotes python-specialist for one FAILED task", () => {
    const dir = makeDir();
    const sessionId = "sess-multi";

    writePrevCache(sessionId, {
      "1": "IN_PROGRESS",
      "2": "IN_PROGRESS",
    });

    const progressPath = writeAutopilot(dir, {
      mode: "build",
      tasks: [
        { id: 1, status: "DONE", description: "Complete plain task" },
        { id: 2, status: "FAILED", description: "Failed python task [mode:python]" },
      ],
    });

    runHook(dir, progressWritePayload(progressPath, sessionId));

    const conf = readConfidence(dir);
    expect(conf).not.toBeNull();

    // Task 1 → DONE, no annotation → developer promoted
    expect(conf["developer"]).toBeDefined();
    expect(conf["developer"].confidence).toBeGreaterThan(0.76);

    // Task 2 → FAILED, [mode:python] → python-specialist demoted
    expect(conf["python-specialist"]).toBeDefined();
    expect(conf["python-specialist"].confidence).toBeLessThan(0.76);
  });
});

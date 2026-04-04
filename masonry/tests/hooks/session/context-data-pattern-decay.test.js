/**
 * masonry/tests/hooks/session/context-data-pattern-decay.test.js
 *
 * Tests for the pattern-decay integration in addContextData().
 *
 * The spec requires that at the START of addContextData(), before any Recall
 * query block, the function calls toolPatternDecay({ project_dir: cwd }) and:
 *   - If result.pruned > 0: pushes a line to the `lines` array:
 *       "[Masonry] Pattern decay: ${result.decayed} scores updated, ${result.pruned} stale patterns pruned"
 *   - If result.pruned === 0: stays silent (no line added)
 *   - If toolPatternDecay throws: the exception is swallowed (never propagates)
 *
 * Import path inside context-data.js:
 *   const { toolPatternDecay } = require('../../tools/impl-patterns')
 *
 * Actual signature: addContextData(lines, cwd, state)
 *   - lines: string[] — mutated in place
 *   - cwd: string    — project root, passed to toolPatternDecay
 *   - state: object  — must include { autopilotMode, uiMode }
 *
 * Written BEFORE implementation. All tests must FAIL until the developer
 * integrates toolPatternDecay into addContextData() in context-data.js.
 *
 * Test strategy:
 *   - Inject a mock toolPatternDecay via the require cache
 *   - Call addContextData with valid args (lines array + minimal state)
 *   - Assert on mock call count/args AND on decay-specific lines output
 *   - All "exception swallowed" tests also verify the mock WAS called, so
 *     they cannot pass by "decay was never called in the first place"
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import os from "os";

const require = createRequire(import.meta.url);

// ---------------------------------------------------------------------------
// Absolute paths for the modules under test
// ---------------------------------------------------------------------------

const CONTEXT_DATA_PATH = path.resolve(
  new URL(".", import.meta.url).pathname,
  "../../../src/hooks/session/context-data.js"
);

const IMPL_PATTERNS_PATH = path.resolve(
  new URL(".", import.meta.url).pathname,
  "../../../src/tools/impl-patterns.js"
);

// ---------------------------------------------------------------------------
// Inject a mock toolPatternDecay into the require cache, load context-data.js.
// Returns { addContextData, mockDecay }.
// ---------------------------------------------------------------------------

function loadWithMock(mockDecayImpl) {
  delete require.cache[CONTEXT_DATA_PATH];
  delete require.cache[IMPL_PATTERNS_PATH];

  let realExports = {};
  try {
    realExports = require(IMPL_PATTERNS_PATH);
  } catch (_) {}

  const mockDecay = vi.fn(mockDecayImpl);

  require.cache[IMPL_PATTERNS_PATH] = {
    id: IMPL_PATTERNS_PATH,
    filename: IMPL_PATTERNS_PATH,
    loaded: true,
    exports: { ...realExports, toolPatternDecay: mockDecay },
    children: [],
    paths: [],
    parent: null,
  };

  const contextData = require(CONTEXT_DATA_PATH);
  return { addContextData: contextData.addContextData, mockDecay };
}

// ---------------------------------------------------------------------------
// Minimal state object satisfying addContextData(lines, cwd, state).
// ---------------------------------------------------------------------------

function makeState(overrides = {}) {
  return {
    autopilotMode: null,
    uiMode: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Invoke addContextData and return the lines array after the call.
// Swallows errors from operations UNRELATED to decay (Recall, etc.).
// ---------------------------------------------------------------------------

async function runAndGetLines(addContextData, cwd, stateOverrides = {}) {
  const lines = [];
  const state = makeState(stateOverrides);
  try {
    await addContextData(lines, cwd, state);
  } catch (_) {
    // Other context-data.js operations (Recall queries, etc.) may fail in tests.
    // We only assert on decay-specific entries in lines[].
  }
  return lines;
}

// ---------------------------------------------------------------------------
// Temp directory helpers
// ---------------------------------------------------------------------------

let tempDir = null;

function makeProjectDir() {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "ctx-decay-test-"));
  fs.mkdirSync(path.join(tempDir, ".autopilot"), { recursive: true });
  return tempDir;
}

function cleanProjectDir() {
  if (tempDir) {
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (_) {}
    tempDir = null;
  }
}

beforeEach(() => {
  delete require.cache[CONTEXT_DATA_PATH];
  delete require.cache[IMPL_PATTERNS_PATH];
});

afterEach(() => {
  cleanProjectDir();
  delete require.cache[CONTEXT_DATA_PATH];
  delete require.cache[IMPL_PATTERNS_PATH];
});

// ---------------------------------------------------------------------------
// 1. toolPatternDecay called with correct project_dir
// ---------------------------------------------------------------------------

describe("toolPatternDecay is called with the cwd project_dir at session start", () => {
  it("calls toolPatternDecay exactly once when addContextData runs", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    await runAndGetLines(addContextData, cwd);

    expect(mockDecay).toHaveBeenCalledTimes(1);
  });

  it("calls toolPatternDecay with { project_dir: cwd }", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    await runAndGetLines(addContextData, cwd);

    expect(mockDecay).toHaveBeenCalledWith({ project_dir: cwd });
  });

  it("passes the exact cwd string — not process.cwd() or a fallback", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    await runAndGetLines(addContextData, cwd);

    const callArg = mockDecay.mock.calls[0]?.[0];
    expect(callArg).toBeDefined();
    expect(callArg.project_dir).toBe(cwd);
  });

  it("passes a different project_dir when a different cwd is supplied", async () => {
    const cwd1 = makeProjectDir();
    const cwd2 = fs.mkdtempSync(path.join(os.tmpdir(), "ctx-decay-cwd2-"));

    try {
      const first = loadWithMock(() => ({ decayed: 0, pruned: 0 }));
      await runAndGetLines(first.addContextData, cwd1);
      expect(first.mockDecay.mock.calls[0][0].project_dir).toBe(cwd1);

      const second = loadWithMock(() => ({ decayed: 0, pruned: 0 }));
      await runAndGetLines(second.addContextData, cwd2);
      expect(second.mockDecay.mock.calls[0][0].project_dir).toBe(cwd2);
    } finally {
      fs.rmSync(cwd2, { recursive: true, force: true });
    }
  });
});

// ---------------------------------------------------------------------------
// 2. pruned > 0 → decay summary line emitted in lines[]
// ---------------------------------------------------------------------------

describe("decay line is emitted when pruned > 0", () => {
  it("emits the decay line when pruned is 1 and decayed is 3", async () => {
    const cwd = makeProjectDir();
    const { addContextData } = loadWithMock(() => ({
      decayed: 3,
      pruned: 1,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeDefined();
    expect(decayLine).toContain("[Masonry] Pattern decay:");
    expect(decayLine).toContain("3 scores updated");
    expect(decayLine).toContain("1 stale patterns pruned");
  });

  it("emits the decay line when pruned is 12 and decayed is 5", async () => {
    const cwd = makeProjectDir();
    const { addContextData } = loadWithMock(() => ({
      decayed: 5,
      pruned: 12,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeDefined();
    expect(decayLine).toContain("5 scores updated");
    expect(decayLine).toContain("12 stale patterns pruned");
  });

  it("decay line format is exactly: [Masonry] Pattern decay: N scores updated, M stale patterns pruned", async () => {
    const cwd = makeProjectDir();
    const { addContextData } = loadWithMock(() => ({
      decayed: 7,
      pruned: 2,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBe(
      "[Masonry] Pattern decay: 7 scores updated, 2 stale patterns pruned"
    );
  });

  it("decay line uses the actual result values — verified with two distinct return sets", async () => {
    const cwd = makeProjectDir();

    const { addContextData: ad1 } = loadWithMock(() => ({
      decayed: 99,
      pruned: 42,
    }));
    const lines1 = await runAndGetLines(ad1, cwd);
    const line1 = lines1.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(line1).toBeDefined();
    expect(line1).toContain("99 scores updated");
    expect(line1).toContain("42 stale patterns pruned");

    const { addContextData: ad2 } = loadWithMock(() => ({
      decayed: 1,
      pruned: 1,
    }));
    const lines2 = await runAndGetLines(ad2, cwd);
    const line2 = lines2.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(line2).toBeDefined();
    expect(line2).toContain("1 scores updated");
    expect(line2).toContain("1 stale patterns pruned");
  });
});

// ---------------------------------------------------------------------------
// 3. pruned === 0 → no decay line in output (stay silent)
//
// Each test also asserts mockDecay WAS called to rule out "passed because
// decay was never wired in at all" (which would make the absence of a line
// a false positive).
// ---------------------------------------------------------------------------

describe("no decay line when pruned === 0", () => {
  it("mockDecay is called once AND no decay line appears when pruned is 0", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    // Decay must have been called (proves implementation reached this code path)
    expect(mockDecay).toHaveBeenCalledTimes(1);

    // No decay line in output
    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeUndefined();
  });

  it("mockDecay is called once AND no decay line when pruned is 0 even if decayed is non-zero", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 5,
      pruned: 0,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    expect(mockDecay).toHaveBeenCalledTimes(1);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeUndefined();
  });

  it("zero [Masonry] Pattern decay lines in output when pruned is 0, confirmed by call count = 1", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    // Must have been called (not zero)
    expect(mockDecay.mock.calls.length).toBe(1);

    // Zero lines matching the decay prefix
    const masonryDecayLines = lines.filter(
      (l) => typeof l === "string" && l.startsWith("[Masonry] Pattern decay")
    );
    expect(masonryDecayLines).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// 4. Exception in toolPatternDecay does not propagate
//
// Each test asserts that mockDecay WAS called (so we know the try/catch
// was actually executed and the error was actively swallowed, not that
// decay was never invoked).
// ---------------------------------------------------------------------------

describe("exception in toolPatternDecay is swallowed (session start must never fail due to decay)", () => {
  it("mockDecay is called and the error it throws does NOT propagate out of addContextData", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => {
      throw new Error("decay exploded");
    });

    const lines = [];
    const state = makeState();
    let decayErrorPropagated = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      if (e.message === "decay exploded") {
        decayErrorPropagated = true;
      }
    }

    // Decay must have been called (the try/catch was entered)
    expect(mockDecay).toHaveBeenCalledTimes(1);
    // The decay error must not have propagated
    expect(decayErrorPropagated).toBe(false);
  });

  it("addContextData does not reject due to decay when toolPatternDecay throws — verified by call count", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => {
      throw new Error("disk read failure in decay");
    });

    const lines = [];
    const state = makeState();
    let decayErrorLeaked = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      if (e.message === "disk read failure in decay") {
        decayErrorLeaked = true;
      }
    }

    expect(mockDecay).toHaveBeenCalledTimes(1);
    expect(decayErrorLeaked).toBe(false);
  });

  it("no decay line emitted when toolPatternDecay throws, but mock WAS called", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => {
      throw new Error("unexpected decay failure");
    });

    const lines = await runAndGetLines(addContextData, cwd);

    expect(mockDecay).toHaveBeenCalledTimes(1);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeUndefined();
  });

  it("async decay rejection does not propagate — verified by call count", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(async () => {
      throw new Error("async decay failure");
    });

    const lines = [];
    const state = makeState();
    let asyncDecayErrorLeaked = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      if (e.message === "async decay failure") {
        asyncDecayErrorLeaked = true;
      }
    }

    expect(mockDecay).toHaveBeenCalledTimes(1);
    expect(asyncDecayErrorLeaked).toBe(false);
  });

  it("null return from toolPatternDecay does not propagate a TypeError — verified by call count", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => null);

    const lines = [];
    const state = makeState();
    let typeErrorFromNull = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      // A TypeError thrown because we tried to access null.pruned would mean
      // the try/catch wrapper is missing or incomplete
      if (e instanceof TypeError && String(e.message).includes("null")) {
        typeErrorFromNull = true;
      }
    }

    expect(mockDecay).toHaveBeenCalledTimes(1);
    expect(typeErrorFromNull).toBe(false);
  });

  it("missing pruned key does not propagate — verified by call count", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({ decayed: 3 }));

    const lines = [];
    const state = makeState();
    let typeError = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      if (e instanceof TypeError) {
        typeError = true;
      }
    }

    expect(mockDecay).toHaveBeenCalledTimes(1);
    expect(typeError).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 5. Decay is called at the START — before any other context-data operations
// ---------------------------------------------------------------------------

describe("toolPatternDecay is invoked at the start of addContextData", () => {
  it("mockDecay.mock.calls.length >= 1 after addContextData runs", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    await runAndGetLines(addContextData, cwd);

    // If decay were deferred and something threw first, count would be 0
    expect(mockDecay.mock.calls.length).toBeGreaterThanOrEqual(1);
  });

  it("mockDecay is called exactly once per addContextData invocation", async () => {
    const cwd = makeProjectDir();
    const { addContextData, mockDecay } = loadWithMock(() => ({
      decayed: 0,
      pruned: 0,
    }));

    await runAndGetLines(addContextData, cwd);

    expect(mockDecay).toHaveBeenCalledTimes(1);
  });

  it("decay line from pruned > 0 is present in lines[], confirming call occurred before function returned", async () => {
    const cwd = makeProjectDir();
    const { addContextData } = loadWithMock(() => ({
      decayed: 2,
      pruned: 4,
    }));

    const lines = await runAndGetLines(addContextData, cwd);

    const decayLine = lines.find(
      (l) => typeof l === "string" && l.includes("Pattern decay")
    );
    expect(decayLine).toBeDefined();
    expect(decayLine).toContain("2 scores updated");
    expect(decayLine).toContain("4 stale patterns pruned");
  });
});

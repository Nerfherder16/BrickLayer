/**
 * masonry/tests/hooks/session/context-data-top-agents.test.js
 *
 * Tests for the top-confidence-agent injection in addContextData().
 *
 * The spec requires that AFTER the pattern-decay block and BEFORE the Recall
 * query block, addContextData() reads {cwd}/.autopilot/pattern-confidence.json
 * and, when at least 2 qualifying agents exist, pushes one line to `lines`:
 *
 *   "[Masonry] Top agents by confidence: developer (99.9%, 94 uses), ..."
 *
 * Qualification rules:
 *   1. Entry value must be an object with { confidence, uses } — bare numbers
 *      like `"pattern-a": 0.999` are excluded.
 *   2. uses >= 2 (cold-start agents are excluded).
 *   3. Sorted by confidence descending.
 *   4. Top 5 taken.
 *   5. If fewer than 2 qualifying agents → no line emitted.
 *   6. Missing pattern-confidence.json → no line emitted, no throw.
 *
 * Format per agent: `name (X.X%, N uses)` — confidence rounded to 1 decimal
 * place as a percentage, agents joined with ", ".
 *
 * Written BEFORE implementation. All tests must FAIL until the developer
 * integrates the top-agent injection into context-data.js.
 *
 * Test strategy:
 *   - Write fixture pattern-confidence.json files into a real temp dir
 *   - Load context-data.js fresh per test via require cache invalidation
 *   - Also inject a no-op mock for impl-patterns (toolPatternDecay) so the
 *     decay block does not throw and contaminate the lines array
 *   - Assert on the presence and exact format of the top-agents line in lines[]
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import os from "os";

const require = createRequire(import.meta.url);

// ---------------------------------------------------------------------------
// Absolute paths
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
// Load context-data.js with a silent no-op decay mock so the decay block
// never throws and never adds decay lines that could confuse assertions.
// ---------------------------------------------------------------------------

function loadWithSilentDecay() {
  delete require.cache[CONTEXT_DATA_PATH];
  delete require.cache[IMPL_PATTERNS_PATH];

  let realExports = {};
  try {
    realExports = require(IMPL_PATTERNS_PATH);
  } catch (_) {}

  require.cache[IMPL_PATTERNS_PATH] = {
    id: IMPL_PATTERNS_PATH,
    filename: IMPL_PATTERNS_PATH,
    loaded: true,
    exports: {
      ...realExports,
      toolPatternDecay: vi.fn(() => ({ decayed: 0, pruned: 0 })),
    },
    children: [],
    paths: [],
    parent: null,
  };

  const contextData = require(CONTEXT_DATA_PATH);
  return contextData.addContextData;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeState(overrides = {}) {
  return {
    autopilotMode: null,
    uiMode: null,
    ...overrides,
  };
}

async function runAndGetLines(addContextData, cwd, stateOverrides = {}) {
  const lines = [];
  const state = makeState(stateOverrides);
  try {
    await addContextData(lines, cwd, state);
  } catch (_) {
    // Other context-data.js operations (Recall queries, etc.) may fail in
    // test environments. We only assert on the top-agents line.
  }
  return lines;
}

/** Return the top-agents line from lines[], or undefined. */
function findTopAgentsLine(lines) {
  return lines.find(
    (l) => typeof l === "string" && l.includes("Top agents by confidence")
  );
}

// ---------------------------------------------------------------------------
// Temp directory lifecycle
// ---------------------------------------------------------------------------

let tempDir = null;

function makeProjectDir(confidenceData) {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "ctx-top-agents-test-"));
  const autopilotDir = path.join(tempDir, ".autopilot");
  fs.mkdirSync(autopilotDir, { recursive: true });

  if (confidenceData !== undefined) {
    fs.writeFileSync(
      path.join(autopilotDir, "pattern-confidence.json"),
      JSON.stringify(confidenceData),
      "utf8"
    );
  }
  // If confidenceData is undefined, no file is written (simulates missing file).

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
// 1. Correct top-5 sort and format
// ---------------------------------------------------------------------------

describe("top-agents line: correct sort, top-5 truncation, and exact format", () => {
  it("emits a top-agents line when 5+ qualifying agents exist", async () => {
    const cwd = makeProjectDir({
      developer: { confidence: 0.999, uses: 94 },
      Explore: { confidence: 0.999, uses: 25 },
      "code-reviewer": { confidence: 0.987, uses: 40 },
      "test-writer": { confidence: 0.975, uses: 18 },
      "rough-in": { confidence: 0.961, uses: 12 },
      "git-nerd": { confidence: 0.950, uses: 30 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
  });

  it("line starts with the exact prefix [Masonry] Top agents by confidence:", async () => {
    const cwd = makeProjectDir({
      developer: { confidence: 0.999, uses: 94 },
      Explore: { confidence: 0.999, uses: 25 },
      "code-reviewer": { confidence: 0.987, uses: 40 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line.startsWith("[Masonry] Top agents by confidence: ")).toBe(true);
  });

  it("formats each agent as name (X.X%, N uses)", async () => {
    const cwd = makeProjectDir({
      developer: { confidence: 0.999, uses: 94 },
      Explore: { confidence: 0.999, uses: 25 },
      "code-reviewer": { confidence: 0.987, uses: 40 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    // Each agent segment must match the pattern "name (X.X%, N uses)"
    expect(line).toMatch(/developer \([\d.]+%, \d+ uses\)/);
    expect(line).toMatch(/Explore \([\d.]+%, \d+ uses\)/);
  });

  it("formats confidence as percentage rounded to 1 decimal: 0.999 → 99.9%", async () => {
    const cwd = makeProjectDir({
      developer: { confidence: 0.999, uses: 94 },
      Explore: { confidence: 0.876, uses: 25 },
      "code-reviewer": { confidence: 0.987, uses: 40 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).toContain("developer (99.9%, 94 uses)");
    expect(line).toContain("Explore (87.6%, 25 uses)");
    expect(line).toContain("code-reviewer (98.7%, 40 uses)");
  });

  it("sorts agents by confidence descending — highest confidence appears first", async () => {
    const cwd = makeProjectDir({
      "low-agent": { confidence: 0.800, uses: 10 },
      "high-agent": { confidence: 0.990, uses: 10 },
      "mid-agent": { confidence: 0.900, uses: 10 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();

    const highPos = line.indexOf("high-agent");
    const midPos = line.indexOf("mid-agent");
    const lowPos = line.indexOf("low-agent");

    expect(highPos).toBeGreaterThanOrEqual(0);
    expect(midPos).toBeGreaterThanOrEqual(0);
    expect(lowPos).toBeGreaterThanOrEqual(0);
    expect(highPos).toBeLessThan(midPos);
    expect(midPos).toBeLessThan(lowPos);
  });

  it("caps output at top 5 — a 6th agent is excluded even if qualifying", async () => {
    const cwd = makeProjectDir({
      agent1: { confidence: 0.999, uses: 50 },
      agent2: { confidence: 0.995, uses: 50 },
      agent3: { confidence: 0.990, uses: 50 },
      agent4: { confidence: 0.985, uses: 50 },
      agent5: { confidence: 0.980, uses: 50 },
      agent6: { confidence: 0.900, uses: 50 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).toContain("agent1");
    expect(line).toContain("agent5");
    expect(line).not.toContain("agent6");
  });

  it("exactly 5 agents are listed when 5 qualify and exist", async () => {
    const cwd = makeProjectDir({
      agent1: { confidence: 0.999, uses: 50 },
      agent2: { confidence: 0.995, uses: 50 },
      agent3: { confidence: 0.990, uses: 50 },
      agent4: { confidence: 0.985, uses: 50 },
      agent5: { confidence: 0.980, uses: 50 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    // Count agent segments by counting "% uses)" occurrences
    const segmentMatches = line.match(/\d+\.\d+%, \d+ uses\)/g) || [];
    expect(segmentMatches).toHaveLength(5);
  });

  it("agents within the line are joined with ', '", async () => {
    const cwd = makeProjectDir({
      alpha: { confidence: 0.999, uses: 20 },
      beta: { confidence: 0.990, uses: 20 },
      gamma: { confidence: 0.980, uses: 20 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    // After the prefix, check the suffix uses ", " as the separator
    const suffix = line.replace("[Masonry] Top agents by confidence: ", "");
    // Each agent ends with ")" and is followed by ", " (except the last)
    expect(suffix).toMatch(/\).*, /);
    // Last segment ends with ")" and NOT with ", "
    expect(suffix.trimEnd().endsWith(")")).toBe(true);
  });

  it("exact full line format with known values", async () => {
    const cwd = makeProjectDir({
      developer: { confidence: 0.999, uses: 94 },
      Explore: { confidence: 0.999, uses: 25 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    // Both agents qualify; the exact text depends on sort stability for equal
    // confidence, but either order must match the full format spec.
    const validFormats = [
      "[Masonry] Top agents by confidence: developer (99.9%, 94 uses), Explore (99.9%, 25 uses)",
      "[Masonry] Top agents by confidence: Explore (99.9%, 25 uses), developer (99.9%, 94 uses)",
    ];
    expect(validFormats).toContain(line);
  });
});

// ---------------------------------------------------------------------------
// 2. Bare-number entries are excluded
// ---------------------------------------------------------------------------

describe("bare-number entries are excluded from the top-agents ranking", () => {
  it("does not rank an entry whose value is a plain number", async () => {
    const cwd = makeProjectDir({
      "pattern-a": 0.999,
      "pattern-b": 0.998,
      "pattern-c": 0.997,
      realAgent: { confidence: 0.800, uses: 10 },
      realAgent2: { confidence: 0.750, uses: 5 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    // Only 2 qualifying agents exist (realAgent, realAgent2), so a line IS
    // emitted — but the bare-number entries must not appear in it.
    expect(line).toBeDefined();
    expect(line).not.toContain("pattern-a");
    expect(line).not.toContain("pattern-b");
    expect(line).not.toContain("pattern-c");
  });

  it("bare-number entries do not count toward the qualifying total", async () => {
    // Only 1 real object entry + 3 bare numbers → fewer than 2 qualifying → no line
    const cwd = makeProjectDir({
      "pattern-a": 0.999,
      "pattern-b": 0.998,
      "pattern-c": 0.997,
      realAgent: { confidence: 0.900, uses: 10 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("a mix of bare numbers and valid objects — only valid objects appear in output", async () => {
    const cwd = makeProjectDir({
      "bare-1": 0.999,
      "bare-2": 1.0,
      agentA: { confidence: 0.960, uses: 15 },
      agentB: { confidence: 0.940, uses: 8 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).toContain("agentA");
    expect(line).toContain("agentB");
    expect(line).not.toContain("bare-1");
    expect(line).not.toContain("bare-2");
  });

  it("null values are treated the same as bare numbers — excluded", async () => {
    const cwd = makeProjectDir({
      "null-entry": null,
      agentA: { confidence: 0.960, uses: 15 },
      agentB: { confidence: 0.940, uses: 8 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).not.toContain("null-entry");
  });
});

// ---------------------------------------------------------------------------
// 3. Agents with uses < 2 are excluded (cold-start filter)
// ---------------------------------------------------------------------------

describe("agents with uses < 2 are excluded (cold-start filter)", () => {
  it("agent with uses === 0 is excluded", async () => {
    const cwd = makeProjectDir({
      coldAgent: { confidence: 0.999, uses: 0 },
      warmAgent: { confidence: 0.800, uses: 5 },
      warmAgent2: { confidence: 0.750, uses: 3 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    // 2 warm agents qualify (warmAgent, warmAgent2), so a line IS emitted
    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).not.toContain("coldAgent");
  });

  it("agent with uses === 1 is excluded", async () => {
    const cwd = makeProjectDir({
      singleUseAgent: { confidence: 0.999, uses: 1 },
      warmAgent: { confidence: 0.800, uses: 5 },
      warmAgent2: { confidence: 0.750, uses: 3 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    // 2 warm agents qualify (warmAgent, warmAgent2), so a line IS emitted
    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).not.toContain("singleUseAgent");
  });

  it("agent with uses === 2 is included (boundary: exactly at threshold)", async () => {
    const cwd = makeProjectDir({
      thresholdAgent: { confidence: 0.999, uses: 2 },
      warmAgent: { confidence: 0.800, uses: 5 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
    expect(line).toContain("thresholdAgent");
  });

  it("all agents with uses < 2 excluded — count falls below 2 → no line emitted", async () => {
    const cwd = makeProjectDir({
      cold1: { confidence: 0.999, uses: 0 },
      cold2: { confidence: 0.995, uses: 1 },
      cold3: { confidence: 0.990, uses: 0 },
      warm: { confidence: 0.800, uses: 5 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    // Only 1 warm agent → fewer than 2 qualifying → no line
    expect(line).toBeUndefined();
  });

  it("cold-start agents with uses < 2 do not count toward minimum-2 threshold", async () => {
    const cwd = makeProjectDir({
      cold1: { confidence: 0.999, uses: 0 },
      cold2: { confidence: 0.998, uses: 1 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    // 2 entries exist but both have uses < 2 → 0 qualifying → no line
    expect(line).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// 4. Fewer than 2 qualifying agents → no line emitted
// ---------------------------------------------------------------------------

describe("fewer than 2 qualifying agents → no top-agents line emitted", () => {
  it("empty pattern-confidence.json → no line", async () => {
    const cwd = makeProjectDir({});

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("exactly 1 qualifying agent → no line", async () => {
    const cwd = makeProjectDir({
      soloAgent: { confidence: 0.990, uses: 10 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("exactly 2 qualifying agents → line IS emitted", async () => {
    const cwd = makeProjectDir({
      agentA: { confidence: 0.990, uses: 10 },
      agentB: { confidence: 0.980, uses: 5 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeDefined();
  });

  it("1 qualifying + 1 bare number → total qualifying is 1 → no line", async () => {
    const cwd = makeProjectDir({
      "bare-pattern": 0.999,
      realAgent: { confidence: 0.900, uses: 7 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("1 qualifying + 1 cold-start → total qualifying is 1 → no line", async () => {
    const cwd = makeProjectDir({
      coldAgent: { confidence: 0.999, uses: 1 },
      warmAgent: { confidence: 0.900, uses: 3 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// 5. Missing pattern-confidence.json → no line, no throw
// ---------------------------------------------------------------------------

describe("missing pattern-confidence.json → no line emitted and no exception thrown", () => {
  it("no top-agents line is emitted when the file does not exist", async () => {
    // makeProjectDir with undefined writes no pattern-confidence.json
    const cwd = makeProjectDir(undefined);

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("addContextData does not throw when pattern-confidence.json is missing", async () => {
    const cwd = makeProjectDir(undefined);

    const addContextData = loadWithSilentDecay();
    const lines = [];
    const state = makeState();

    let threw = false;
    let isEnoent = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      threw = true;
      if (e.code === "ENOENT" || (e.message && e.message.includes("ENOENT"))) {
        isEnoent = true;
      }
    }

    // If the function threw for an unrelated reason (Recall unavailable, etc.)
    // that's OK — but it must NOT be because of the missing json file.
    expect(isEnoent).toBe(false);
  });

  it("no top-agents line when .autopilot directory itself is missing", async () => {
    // Create a project dir with no .autopilot subdirectory at all
    const cwd = fs.mkdtempSync(
      path.join(os.tmpdir(), "ctx-top-agents-no-autopilot-")
    );
    // Replace tempDir so afterEach cleanup works
    cleanProjectDir();
    tempDir = cwd;

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("no top-agents line when pattern-confidence.json contains invalid JSON", async () => {
    const cwd = makeProjectDir(undefined);
    // Write deliberately malformed JSON
    fs.writeFileSync(
      path.join(cwd, ".autopilot", "pattern-confidence.json"),
      "{ this is: not valid JSON !!!",
      "utf8"
    );

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });

  it("invalid JSON does not propagate a SyntaxError out of addContextData", async () => {
    const cwd = makeProjectDir(undefined);
    fs.writeFileSync(
      path.join(cwd, ".autopilot", "pattern-confidence.json"),
      "TOTALLY BROKEN",
      "utf8"
    );

    const addContextData = loadWithSilentDecay();
    const lines = [];
    const state = makeState();

    let syntaxErrorLeaked = false;

    try {
      await addContextData(lines, cwd, state);
    } catch (e) {
      if (e instanceof SyntaxError) {
        syntaxErrorLeaked = true;
      }
    }

    expect(syntaxErrorLeaked).toBe(false);
  });

  it("empty string content does not throw — treated as unreadable", async () => {
    const cwd = makeProjectDir(undefined);
    fs.writeFileSync(
      path.join(cwd, ".autopilot", "pattern-confidence.json"),
      "",
      "utf8"
    );

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const line = findTopAgentsLine(lines);
    expect(line).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// 6. Only one top-agents line is emitted (not duplicated)
// ---------------------------------------------------------------------------

describe("only one top-agents line is emitted per addContextData call", () => {
  it("exactly one [Masonry] Top agents line in output when qualifying agents exist", async () => {
    const cwd = makeProjectDir({
      agentA: { confidence: 0.999, uses: 50 },
      agentB: { confidence: 0.990, uses: 30 },
      agentC: { confidence: 0.980, uses: 20 },
    });

    const addContextData = loadWithSilentDecay();
    const lines = await runAndGetLines(addContextData, cwd);

    const topAgentLines = lines.filter(
      (l) =>
        typeof l === "string" && l.includes("Top agents by confidence")
    );
    expect(topAgentLines).toHaveLength(1);
  });
});

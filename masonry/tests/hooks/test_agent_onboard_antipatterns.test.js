/**
 * Tests for anti-pattern detection in masonry-agent-onboard.js
 * Imports detectAntiPatterns directly via require (CommonJS).
 */
import { describe, it, expect } from "vitest";
import { createRequire } from "module";

// Load the hook module — we export detectAntiPatterns at the bottom of the hook.
const require = createRequire(import.meta.url);
const { detectAntiPatterns } = require("../../src/hooks/masonry-agent-onboard.js");

// ─── Helpers ────────────────────────────────────────────────────────────────

function makeMeta(overrides = {}) {
  return {
    name: "test-agent",
    description: "A well-written agent that helps with tasks.",
    triggers: ["when the user asks about X"],
    tools: [],
    ...overrides,
  };
}

/** Build a string of ~N KB */
function makeContent(sizeKB) {
  return "x".repeat(Math.ceil(sizeKB * 1024));
}

// ─── 1. OVER_CONSTRAINED ────────────────────────────────────────────────────

describe("OVER_CONSTRAINED", () => {
  it("warns when description has more than 5 constraint words", () => {
    const meta = makeMeta({
      description:
        "You must always never skip this step. Required mandatory output always.",
      // words: must, always, never, Required, mandatory, always  → 6
    });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    const match = warnings.find((w) => w.includes("ANTI_PATTERN:OVER_CONSTRAINED"));
    expect(match).toBeDefined();
    expect(match).toContain("[WARN]");
  });

  it("does not warn when description has exactly 5 constraint words", () => {
    const meta = makeMeta({
      description: "You must always never skip. Required output here.",
      // words: must, always, never, Required  → 4 (≤5 → no warn)
    });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    const match = warnings.find((w) => w.includes("ANTI_PATTERN:OVER_CONSTRAINED"));
    expect(match).toBeUndefined();
  });

  it("does not warn for a clean description with no constraint words", () => {
    const meta = makeMeta({ description: "Helps users research topics." });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("OVER_CONSTRAINED"))).toBeUndefined();
  });
});

// ─── 2. EMPTY_DESCRIPTION ───────────────────────────────────────────────────

describe("EMPTY_DESCRIPTION", () => {
  it("warns when description is completely missing", () => {
    const meta = makeMeta({ description: undefined });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ANTI_PATTERN:EMPTY_DESCRIPTION"))).toBeDefined();
  });

  it("warns when description is an empty string", () => {
    const meta = makeMeta({ description: "" });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ANTI_PATTERN:EMPTY_DESCRIPTION"))).toBeDefined();
  });

  it("warns when description is fewer than 10 characters", () => {
    const meta = makeMeta({ description: "Too short" }); // 9 chars
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ANTI_PATTERN:EMPTY_DESCRIPTION"))).toBeDefined();
  });

  it("does not warn when description is 10+ characters", () => {
    const meta = makeMeta({ description: "Exactly ten" }); // 11 chars
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("EMPTY_DESCRIPTION"))).toBeUndefined();
  });
});

// ─── 3. MISSING_TRIGGER ─────────────────────────────────────────────────────

describe("MISSING_TRIGGER", () => {
  it("emits INFO when triggers array is empty", () => {
    const meta = makeMeta({ triggers: [] });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    const match = warnings.find((w) => w.includes("ANTI_PATTERN:MISSING_TRIGGER"));
    expect(match).toBeDefined();
    expect(match).toContain("[INFO]");
  });

  it("emits INFO when triggers is missing entirely", () => {
    const meta = makeMeta({ triggers: undefined });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ANTI_PATTERN:MISSING_TRIGGER"))).toBeDefined();
  });

  it("does not warn when triggers has at least one entry", () => {
    const meta = makeMeta({ triggers: ["when user asks about X"] });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("MISSING_TRIGGER"))).toBeUndefined();
  });
});

// ─── 4. BLOATED_SKILL ───────────────────────────────────────────────────────

describe("BLOATED_SKILL", () => {
  it("warns when file content exceeds 50 KB", () => {
    const warnings = detectAntiPatterns(makeMeta(), "/agents/big.md", makeContent(51));
    const match = warnings.find((w) => w.includes("ANTI_PATTERN:BLOATED_SKILL"));
    expect(match).toBeDefined();
    expect(match).toContain("[WARN]");
    expect(match).toContain("KB");
  });

  it("does not warn when file is exactly 50 KB", () => {
    const warnings = detectAntiPatterns(makeMeta(), "/agents/ok.md", makeContent(50));
    expect(warnings.find((w) => w.includes("BLOATED_SKILL"))).toBeUndefined();
  });

  it("does not warn for a small file", () => {
    const warnings = detectAntiPatterns(makeMeta(), "/agents/small.md", makeContent(2));
    expect(warnings.find((w) => w.includes("BLOATED_SKILL"))).toBeUndefined();
  });
});

// ─── 5. ORPHAN_REFERENCE ────────────────────────────────────────────────────

describe("ORPHAN_REFERENCE", () => {
  it("warns when a tool has fewer than 3 __ segments", () => {
    const meta = makeMeta({ tools: ["mcp__recall"] }); // only 2 parts after split
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ANTI_PATTERN:ORPHAN_REFERENCE"))).toBeDefined();
  });

  it("does not warn for a well-formed mcp__ tool name", () => {
    const meta = makeMeta({ tools: ["mcp__recall__recall_search"] });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ORPHAN_REFERENCE"))).toBeUndefined();
  });

  it("does not warn for non-mcp__ tools", () => {
    const meta = makeMeta({ tools: ["bash", "Read", "Write"] });
    const warnings = detectAntiPatterns(meta, "/agents/test.md", makeContent(1));
    expect(warnings.find((w) => w.includes("ORPHAN_REFERENCE"))).toBeUndefined();
  });
});

// ─── 6. Clean agent — no warnings at all ─────────────────────────────────────

describe("clean agent", () => {
  it("produces zero warnings for a well-formed agent metadata object", () => {
    const meta = {
      name: "research-analyst",
      description: "Researches topics thoroughly and returns structured findings.",
      triggers: ["when a research question is assigned"],
      tools: ["mcp__recall__recall_search", "mcp__masonry__masonry_run_question"],
    };
    const smallContent = makeContent(5);
    const warnings = detectAntiPatterns(meta, "/agents/research-analyst.md", smallContent);
    expect(warnings).toHaveLength(0);
  });
});

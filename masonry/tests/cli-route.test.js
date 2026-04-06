/**
 * masonry/tests/cli-route.test.js
 *
 * Tests for masonry/src/engine/cli/route.js
 *
 * Strategy: spawn the CLI as a child process and assert on stdout JSON.
 * This validates the full arg-parsing → routing → output pipeline.
 *
 * All Ollama/network calls are neutralised by pointing OLLAMA_HOST at an
 * unreachable address so Layer 2 always falls back gracefully. Layer 1
 * (keyword + intent rules) is purely synchronous and needs no mocking.
 */

import { describe, it, expect } from "vitest";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.resolve(__dirname, "../src/engine/cli/route.js");

/** Run the CLI and return parsed stdout JSON. Throws on non-zero exit. */
function run(args, env = {}) {
  const stdout = execFileSync(process.execPath, [CLI, ...args], {
    encoding: "utf8",
    timeout: 10_000,
    env: {
      ...process.env,
      // Point Ollama at an unreachable host so L2 always fails fast
      OLLAMA_HOST: "127.0.0.1:19999",
      ...env,
    },
  });
  return JSON.parse(stdout.trim());
}

/** Run the CLI and capture stdout even on non-zero exit. */
function runRaw(args, env = {}) {
  try {
    const stdout = execFileSync(process.execPath, [CLI, ...args], {
      encoding: "utf8",
      timeout: 10_000,
      env: {
        ...process.env,
        OLLAMA_HOST: "127.0.0.1:19999",
        ...env,
      },
    });
    return { stdout: stdout.trim(), code: 0 };
  } catch (err) {
    return { stdout: (err.stdout || "").trim(), code: err.status ?? 1 };
  }
}

// ---------------------------------------------------------------------------
// --prompt missing
// ---------------------------------------------------------------------------

describe("route.js — missing --prompt", () => {
  it("should output error JSON and exit 1 when --prompt is omitted", () => {
    const { stdout, code } = runRaw([]);
    expect(code).toBe(1);
    const out = JSON.parse(stdout);
    expect(out).toHaveProperty("error");
    expect(out.error).toMatch(/--prompt/i);
  });
});

// ---------------------------------------------------------------------------
// Layer 1a — registry keyword match
// ---------------------------------------------------------------------------

describe("route.js — Layer 1a registry keyword match", () => {
  it("should route a /build prompt to a build agent at L1a or L1b", () => {
    const out = run(["--prompt", "/build implement the auth service"]);
    // /build is matched by either the registry keyword or the hardcoded L1b rule
    expect(out.agent).not.toBeNull();
    expect(["L1a", "L1b"]).toContain(out.layer);
    expect(out.confidence).toBe(1.0);
  });
});

// ---------------------------------------------------------------------------
// Layer 1b — hardcoded intent rules
// ---------------------------------------------------------------------------

describe("route.js — Layer 1b hardcoded intent rules", () => {
  it("should route /build slash command to rough-in pipeline at L1b", () => {
    // /build by itself triggers the INTENT_RULES dev-task rule (L1b), not a registry keyword.
    const out = run(["--prompt", "/build"]);
    expect(out.agent).not.toBeNull();
    expect(out.agent).toMatch(/rough-in/i);
    expect(out.layer).toBe("L1b");
    expect(out.confidence).toBe(1.0);
  });

  it("should route a git commit prompt to git-nerd", () => {
    const out = run(["--prompt", "commit my changes and push to the branch"]);
    expect(out.agent).toMatch(/git-nerd/i);
    expect(out.layer).toMatch(/^L1/);
    expect(out.confidence).toBe(1.0);
  });

  it("should route a security audit prompt to the security agent", () => {
    const out = run(["--prompt", "run a security audit on the new API routes"]);
    expect(out.agent).toMatch(/security/i);
    expect(out.layer).toMatch(/^L1/);
    expect(out.confidence).toBe(1.0);
  });
});

// ---------------------------------------------------------------------------
// No match — gibberish with Ollama unreachable
// ---------------------------------------------------------------------------

describe("route.js — no match", () => {
  it("should return agent:null for gibberish when Ollama is unreachable", () => {
    const out = run(["--prompt", "xzqjkwvblorf plobnarg zztop42"]);
    expect(out.agent).toBeNull();
    expect(out.confidence).toBe(0);
    expect(out.layer).toBeNull();
    expect(out.note).toBe("no match");
  });

  it("should exit 0 on no-match (not an error)", () => {
    const { code } = runRaw(["--prompt", "xzqjkwvblorf plobnarg zztop42"]);
    expect(code).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Conversational prompts — skip (returns no match)
// ---------------------------------------------------------------------------

describe("route.js — conversational prompts are skipped", () => {
  it("should return no-match for a simple yes confirmation", () => {
    const out = run(["--prompt", "yes"]);
    expect(out.agent).toBeNull();
  });

  it("should return no-match for a how-do-I question", () => {
    const out = run(["--prompt", "how do I configure the proxy?"]);
    expect(out.agent).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Output shape contract
// ---------------------------------------------------------------------------

describe("route.js — output shape", () => {
  it("should always return an object with agent, confidence, layer, note on match", () => {
    const out = run(["--prompt", "implement a new feature for the dashboard component"]);
    expect(out).toHaveProperty("agent");
    expect(out).toHaveProperty("confidence");
    expect(out).toHaveProperty("layer");
    expect(out).toHaveProperty("note");
    expect(typeof out.confidence).toBe("number");
  });

  it("should always return an object with agent, confidence, layer, note on no-match", () => {
    const out = run(["--prompt", "xzqjkwvblorf plobnarg zztop42"]);
    expect(out).toHaveProperty("agent");
    expect(out).toHaveProperty("confidence");
    expect(out).toHaveProperty("layer");
    expect(out).toHaveProperty("note");
  });

  it("stdout should be valid JSON with no extra output", () => {
    const { stdout } = runRaw(["--prompt", "implement a widget"]);
    expect(() => JSON.parse(stdout)).not.toThrow();
    // Should be a single line (no multiline garbage)
    expect(stdout.split("\n").filter(Boolean)).toHaveLength(1);
  });

  it("should accept --project-dir without error", () => {
    const { code } = runRaw([
      "--prompt", "implement a new endpoint",
      "--project-dir", path.resolve(__dirname, "../../"),
    ]);
    expect(code).toBe(0);
  });
});

/**
 * masonry/tests/cli-status.test.js
 *
 * Tests for masonry/src/engine/cli/status.js
 *
 * Strategy: spawn the CLI as a child process against temp directories
 * with fixture questions.md files. All I/O is real (no mocks needed —
 * the CLI only reads local files).
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.resolve(__dirname, "../src/engine/cli/status.js");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Run the CLI and return parsed stdout JSON. Throws on non-zero exit. */
function run(args) {
  const stdout = execFileSync(process.execPath, [CLI, ...args], {
    encoding: "utf8",
    timeout: 10_000,
  });
  return JSON.parse(stdout.trim());
}

/** Run the CLI, capture stdout even on non-zero exit. */
function runRaw(args) {
  try {
    const stdout = execFileSync(process.execPath, [CLI, ...args], {
      encoding: "utf8",
      timeout: 10_000,
    });
    return { stdout: stdout.trim(), code: 0 };
  } catch (err) {
    return { stdout: (err.stdout || "").trim(), code: err.status ?? 1 };
  }
}

/** Create a temp directory and return its path. Caller owns cleanup. */
function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "bl-status-test-"));
}

/** Recursively delete a temp directory. */
function removeTempDir(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

// ---------------------------------------------------------------------------
// Fixture: questions.md in the format used by bricklayer-v2
// ---------------------------------------------------------------------------

const FIXTURE_QUESTIONS_TABLE = `\
# Research Questions — BrickLayer 2.0

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Domain 1 — Architecture

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q1.1 | diagnose | DONE | First question |
| Q1.2 | diagnose | DONE | Second question |
| Q1.3 | diagnose | PENDING | Third question |

---

## Wave 2 — Fix

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E2.1 | evolve | DONE | Wave two question one |
| E2.2 | evolve | INCONCLUSIVE | Wave two question two |
| E2.3 | evolve | PENDING | Wave two question three |

---

## Wave 3 — Evolve

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E3.1 | evolve | DONE | Wave three question one |
| E3.2 | evolve | IN_PROGRESS | Wave three question two |
`;

const FIXTURE_QUESTIONS_CHECKBOX = `\
# Questions

- [x] First done question
- [x] Second done question
- [ ] Pending question one
- [ ] Pending question two
- [ ] Pending question three
`;

// ---------------------------------------------------------------------------
// Shared temp dir management
// ---------------------------------------------------------------------------

let tempRoot;

beforeAll(() => {
  tempRoot = makeTempDir();
});

afterAll(() => {
  removeTempDir(tempRoot);
});

/** Create a sub-directory under tempRoot with optional files. */
function makeProject(name, files = {}) {
  const dir = path.join(tempRoot, name);
  fs.mkdirSync(dir, { recursive: true });
  for (const [relPath, content] of Object.entries(files)) {
    const full = path.join(dir, relPath);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content, "utf8");
  }
  return dir;
}

// ---------------------------------------------------------------------------
// Missing --project-dir
// ---------------------------------------------------------------------------

describe("status.js — missing --project-dir", () => {
  it("should output error JSON and exit 1 when --project-dir is omitted", () => {
    const { stdout, code } = runRaw([]);
    expect(code).toBe(1);
    const out = JSON.parse(stdout);
    expect(out).toHaveProperty("error");
    expect(out.error).toMatch(/--project-dir/i);
  });
});

// ---------------------------------------------------------------------------
// Non-existent directory
// ---------------------------------------------------------------------------

describe("status.js — non-existent project dir", () => {
  it("should return no_project state and exit 0 when dir does not exist", () => {
    const { stdout, code } = runRaw([
      "--project-dir",
      path.join(tempRoot, "does-not-exist-xyzzy"),
    ]);
    expect(code).toBe(0);
    const out = JSON.parse(stdout);
    expect(out.state).toBe("no_project");
    expect(out.questions.total).toBe(0);
    expect(out.questions.answered).toBe(0);
    expect(out.questions.pending).toBe(0);
    expect(out.wave).toBe(0);
    expect(out.findings).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Existing dir but no questions.md
// ---------------------------------------------------------------------------

describe("status.js — missing questions.md", () => {
  it("should return no_project state and exit 0 when questions.md is absent", () => {
    const dir = makeProject("no-questions");
    const { stdout, code } = runRaw(["--project-dir", dir]);
    expect(code).toBe(0);
    const out = JSON.parse(stdout);
    expect(out.state).toBe("no_project");
    expect(out.questions.total).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Table-format questions.md
// ---------------------------------------------------------------------------

describe("status.js — table format questions.md", () => {
  let projectDir;

  beforeAll(() => {
    projectDir = makeProject("table-questions", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
    });
  });

  it("should count total questions correctly", () => {
    const out = run(["--project-dir", projectDir]);
    // 3 in Domain 1 + 3 in Wave 2 + 2 in Wave 3 = 8
    expect(out.questions.total).toBe(8);
  });

  it("should count answered (DONE) questions correctly", () => {
    const out = run(["--project-dir", projectDir]);
    // Q1.1, Q1.2, E2.1, E3.1 = 4 DONE
    expect(out.questions.answered).toBe(4);
  });

  it("should compute pending as total minus answered", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.questions.pending).toBe(out.questions.total - out.questions.answered);
  });

  it("should detect highest wave number from headers", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.wave).toBe(3);
  });

  it("should return no_mode state when .autopilot/mode is absent", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.state).toBe("no_mode");
  });

  it("should return 0 findings when findings dir is absent", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.findings).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Checkbox-format questions.md
// ---------------------------------------------------------------------------

describe("status.js — checkbox format questions.md", () => {
  let projectDir;

  beforeAll(() => {
    projectDir = makeProject("checkbox-questions", {
      "questions.md": FIXTURE_QUESTIONS_CHECKBOX,
    });
  });

  it("should count total questions from checkboxes", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.questions.total).toBe(5);
  });

  it("should count answered from checked boxes", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.questions.answered).toBe(2);
  });

  it("should compute pending correctly", () => {
    const out = run(["--project-dir", projectDir]);
    expect(out.questions.pending).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// .autopilot/mode state file
// ---------------------------------------------------------------------------

describe("status.js — .autopilot/mode state", () => {
  it("should read state from .autopilot/mode when present", () => {
    const dir = makeProject("with-mode", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
      ".autopilot/mode": "evolve",
    });
    const out = run(["--project-dir", dir]);
    expect(out.state).toBe("evolve");
  });

  it("should return no_mode when .autopilot/mode is empty", () => {
    const dir = makeProject("empty-mode", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
      ".autopilot/mode": "   \n",
    });
    const out = run(["--project-dir", dir]);
    expect(out.state).toBe("no_mode");
  });
});

// ---------------------------------------------------------------------------
// Findings count
// ---------------------------------------------------------------------------

describe("status.js — findings count", () => {
  it("should count .md files in findings/ directory", () => {
    const dir = makeProject("with-findings", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
      "findings/Q1.1.md": "# Finding Q1.1\nContent.",
      "findings/Q1.2.md": "# Finding Q1.2\nContent.",
      "findings/synthesis.md": "# Synthesis\nContent.",
    });
    const out = run(["--project-dir", dir]);
    expect(out.findings).toBe(3);
  });

  it("should return 0 when findings dir exists but is empty", () => {
    const dir = makeProject("empty-findings", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
    });
    fs.mkdirSync(path.join(dir, "findings"), { recursive: true });
    const out = run(["--project-dir", dir]);
    expect(out.findings).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Wave detection from question IDs
// ---------------------------------------------------------------------------

describe("status.js — wave detection from question IDs", () => {
  it("should detect wave from E-prefix question IDs when no Wave header exists", () => {
    const dir = makeProject("wave-from-ids", {
      "questions.md": `\
| ID | Mode | Status | Question |
|----|------|--------|---------|
| E5.1 | evolve | DONE | Question in wave 5 |
| E5.2 | evolve | PENDING | Another wave 5 question |
`,
    });
    const out = run(["--project-dir", dir]);
    expect(out.wave).toBe(5);
  });

  it("should prefer Wave header number over question ID wave when header is higher", () => {
    const dir = makeProject("wave-header-wins", {
      "questions.md": `\
## Wave 7 — Big Wave

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E3.1 | evolve | DONE | Old question still in file |
`,
    });
    const out = run(["--project-dir", dir]);
    expect(out.wave).toBe(7);
  });
});

// ---------------------------------------------------------------------------
// Output shape contract
// ---------------------------------------------------------------------------

describe("status.js — output shape", () => {
  it("should always output a single line of valid JSON on success", () => {
    const dir = makeProject("shape-check", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
    });
    const { stdout, code } = runRaw(["--project-dir", dir]);
    expect(code).toBe(0);
    expect(() => JSON.parse(stdout)).not.toThrow();
    expect(stdout.split("\n").filter(Boolean)).toHaveLength(1);
  });

  it("should include all required keys: state, questions, wave, findings", () => {
    const dir = makeProject("keys-check", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
    });
    const out = run(["--project-dir", dir]);
    expect(out).toHaveProperty("state");
    expect(out).toHaveProperty("questions");
    expect(out).toHaveProperty("wave");
    expect(out).toHaveProperty("findings");
    expect(out.questions).toHaveProperty("total");
    expect(out.questions).toHaveProperty("answered");
    expect(out.questions).toHaveProperty("pending");
  });

  it("should exit 0 for valid project", () => {
    const dir = makeProject("exit-code-valid", {
      "questions.md": FIXTURE_QUESTIONS_TABLE,
    });
    const { code } = runRaw(["--project-dir", dir]);
    expect(code).toBe(0);
  });

  it("should exit 0 even for missing project dir (not an error)", () => {
    const { code } = runRaw([
      "--project-dir",
      path.join(tempRoot, "totally-missing-dir"),
    ]);
    expect(code).toBe(0);
  });
});

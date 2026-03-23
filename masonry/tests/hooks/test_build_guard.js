import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect, beforeEach } from "vitest";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-build-guard.js");

function runHook(cwd, stdinPayload) {
  const env = { ...process.env };
  // Unset PWD so the hook uses process.cwd() (set by execFileSync's cwd option)
  // rather than the inherited shell PWD which points to the test runner's directory.
  delete env.PWD;
  try {
    execFileSync("node", [HOOK], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env,
      stdio: ["pipe", "pipe", "pipe"],
    });
    return 0;
  } catch (e) {
    return e.status ?? 1;
  }
}

function makeDir() {
  return mkdtempSync(join(tmpdir(), "build-guard-test-"));
}

function writeProgress(dir, data) {
  mkdirSync(join(dir, ".autopilot"), { recursive: true });
  writeFileSync(join(dir, ".autopilot", "mode"), "build");
  writeFileSync(join(dir, ".autopilot", "progress.json"), JSON.stringify(data));
}

describe("masonry-build-guard session awareness", () => {
  it("blocks when session_id matches and tasks are pending", () => {
    const dir = makeDir();
    writeProgress(dir, {
      status: "BUILDING",
      session_id: "session-abc",
      tasks: [{ id: 1, status: "PENDING", description: "task 1" }],
    });
    const code = runHook(dir, { session_id: "session-abc" });
    expect(code).toBe(2);
  });

  it("allows stop when session_id differs (different session owns the build)", () => {
    const dir = makeDir();
    writeProgress(dir, {
      status: "BUILDING",
      session_id: "session-abc",
      tasks: [{ id: 1, status: "PENDING", description: "task 1" }],
    });
    const code = runHook(dir, { session_id: "session-xyz" });
    expect(code).toBe(0);
  });

  it("allows stop when progress.json has no session_id (legacy build)", () => {
    const dir = makeDir();
    writeProgress(dir, {
      status: "BUILDING",
      tasks: [{ id: 1, status: "PENDING", description: "task 1" }],
    });
    const code = runHook(dir, { session_id: "session-xyz" });
    expect(code).toBe(0);
  });

  it("allows stop when no pending tasks regardless of session", () => {
    const dir = makeDir();
    writeProgress(dir, {
      status: "BUILDING",
      session_id: "session-abc",
      tasks: [{ id: 1, status: "DONE", description: "task 1" }],
    });
    const code = runHook(dir, { session_id: "session-abc" });
    expect(code).toBe(0);
  });

  it("allows stop when no .autopilot directory", () => {
    const dir = makeDir();
    const code = runHook(dir, { session_id: "session-abc" });
    expect(code).toBe(0);
  });

  it("blocks defensively when current session has no session_id (null) and tasks pending", () => {
    const dir = makeDir();
    writeProgress(dir, {
      status: "BUILDING",
      session_id: "session-abc",
      tasks: [{ id: 1, status: "PENDING", description: "task 1" }],
    });
    const code = runHook(dir, {});
    expect(code).toBe(2);
  });
});

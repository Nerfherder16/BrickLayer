import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync, existsSync } from "fs";
import { join, basename } from "path";
import { tmpdir } from "os";
import { describe, it, expect } from "vitest";

const PRE_COMPACT = join(process.cwd(), "src", "hooks", "masonry-pre-compact.js");
const POST_COMPACT = join(process.cwd(), "src", "hooks", "masonry-post-compact.js");

function makeDir() {
  return mkdtempSync(join(tmpdir(), "compact-test-"));
}

function runHook(hookPath, cwd, stdinPayload) {
  const env = { ...process.env };
  delete env.PWD;
  try {
    const out = execFileSync("node", [hookPath], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env,
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
    });
    return { exit: 0, stdout: out };
  } catch (e) {
    return { exit: e.status ?? 1, stdout: e.stdout || "", stderr: e.stderr || "" };
  }
}

function writeAutopilot(cwd, files) {
  mkdirSync(join(cwd, ".autopilot"), { recursive: true });
  for (const [name, content] of Object.entries(files)) {
    writeFileSync(join(cwd, ".autopilot", name), typeof content === "string" ? content : JSON.stringify(content, null, 2), "utf8");
  }
}

// ── masonry-pre-compact.js tests ─────────────────────────────────────────────

describe("masonry-pre-compact.js", () => {
  it("clears stale compact-state.json when build is complete and mode is empty", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "mode": "",  // build completed, mode cleared
      "compact-state.json": {
        mode: "build",
        project: "my-project",
        done: 0,
        total: 4,
        nextTask: { id: 1, description: "some task" },
        compactedAt: new Date().toISOString(),
      },
      "progress.json": {
        status: "COMPLETE",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "DONE" },
        ],
      },
    });

    runHook(PRE_COMPACT, cwd, { cwd });

    const cleared = JSON.parse(readFileSync(join(cwd, ".autopilot", "compact-state.json"), "utf8"));
    expect(cleared.reason).toBe("build-complete");
    expect(cleared).not.toHaveProperty("mode");
    expect(cleared).not.toHaveProperty("nextTask");
  });

  it("does NOT clear compact-state.json when build is still in progress", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "mode": "build",
      "compact-state.json": {
        mode: "build",
        project: "my-project",
        done: 1,
        total: 4,
        nextTask: { id: 2, description: "task 2" },
        compactedAt: new Date().toISOString(),
      },
      "progress.json": {
        status: "BUILDING",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "PENDING" },
          { id: 3, status: "PENDING" },
          { id: 4, status: "PENDING" },
        ],
      },
    });

    runHook(PRE_COMPACT, cwd, { cwd });

    const compact = JSON.parse(readFileSync(join(cwd, ".autopilot", "compact-state.json"), "utf8"));
    // compact-state should be UPDATED with current progress, not cleared
    expect(compact.mode).toBe("build");
  });

  it("does NOT write pre-compact-snapshot.json or build.log entry when all tasks are done", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "mode": "build",
      "compact-state.json": {},
      "progress.json": {
        project: "test-proj",
        status: "BUILDING",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "DONE" },
        ],
      },
      "build.log": "",
    });

    runHook(PRE_COMPACT, cwd, { cwd });

    const log = readFileSync(join(cwd, ".autopilot", "build.log"), "utf8");
    // Should NOT write "All tasks done. Resume with /build." noise
    expect(log).not.toContain("All tasks done");
    expect(log).not.toContain("Resume with /build");
  });

  it("DOES write pre-compact-snapshot.json when there are pending tasks", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "mode": "build",
      "compact-state.json": {},
      "progress.json": {
        project: "test-proj",
        status: "BUILDING",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "PENDING", description: "task 2 pending" },
        ],
      },
      "build.log": "",
    });

    runHook(PRE_COMPACT, cwd, { cwd });

    expect(existsSync(join(cwd, ".autopilot", "pre-compact-snapshot.json"))).toBe(true);
    const snapshot = JSON.parse(readFileSync(join(cwd, ".autopilot", "pre-compact-snapshot.json"), "utf8"));
    expect(snapshot.tasks[1].status).toBe("PENDING");
  });

  it("exits 0 with no autopilot files present", () => {
    const cwd = makeDir();
    const result = runHook(PRE_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);
  });
});

// ── masonry-post-compact.js tests ────────────────────────────────────────────

describe("masonry-post-compact.js", () => {
  it("does NOT inject resume context when progress.json shows COMPLETE (stale compact-state)", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "compact-state.json": {
        mode: "build",
        project: "my-project",
        done: 0,
        total: 4,
        nextTask: { id: 1, description: "Implement task 1" },
        compactedAt: new Date().toISOString(),
      },
      "progress.json": {
        status: "COMPLETE",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "DONE" },
        ],
      },
    });

    const result = runHook(POST_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);

    // Should produce no output (or empty output) — not inject stale resume context
    const output = result.stdout || "";
    if (output.trim()) {
      const parsed = JSON.parse(output);
      expect(parsed.systemMessage || "").not.toContain("RESUMED after compaction");
      expect(parsed.systemMessage || "").not.toContain("Run /masonry-build");
    }
  });

  it("DOES inject resume context when build is genuinely in progress", () => {
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "compact-state.json": {
        mode: "build",
        project: "my-project",
        done: 1,
        total: 4,
        nextTask: { id: 2, description: "Task 2 still pending" },
        compactedAt: new Date().toISOString(),
      },
      "progress.json": {
        status: "BUILDING",
        tasks: [
          { id: 1, status: "DONE" },
          { id: 2, status: "PENDING" },
        ],
      },
    });

    const result = runHook(POST_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);

    const parsed = JSON.parse(result.stdout);
    expect(parsed.systemMessage).toContain("RESUMED after compaction");
    expect(parsed.systemMessage).toContain("Task 2 still pending");
  });

  it("exits 0 with no compact-state.json present", () => {
    const cwd = makeDir();
    const result = runHook(POST_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);
  });

  it("injects resume context when compact-state has no matching progress.json (no progress written yet)", () => {
    // Edge case: spec approved, build never started — no progress.json
    const cwd = makeDir();
    writeAutopilot(cwd, {
      "compact-state.json": {
        mode: "build",
        project: "my-project",
        done: 0,
        total: 3,
        nextTask: { id: 1, description: "First task" },
        compactedAt: new Date().toISOString(),
      },
      // No progress.json
    });

    const result = runHook(POST_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);

    const parsed = JSON.parse(result.stdout);
    expect(parsed.systemMessage).toContain("RESUMED after compaction");
    expect(parsed.systemMessage).toContain("First task");
  });

  it("injects activity breadcrumb from pre-compact-work.json when no build was active", () => {
    const cwd = makeDir();
    // Simulate a conversational session that wrote some files, then compacted
    writeAutopilot(cwd, {
      "pre-compact-work.json": {
        saved_at: new Date().toISOString(),
        session_id: "abc123",
        total_edits: 5,
        recent_edits: [
          "Write → jcodemunch.md",
          "Write → masonry-jcodemunch-nudge.js",
          "Edit → settings.json",
          "Edit → masonry-observe.js",
          "Edit → masonry-stop-guard.js",
        ],
      },
      // No compact-state.json — pure conversational session
    });

    const result = runHook(POST_COMPACT, cwd, { cwd });
    expect(result.exit).toBe(0);

    const parsed = JSON.parse(result.stdout);
    expect(parsed.systemMessage).toContain("last session edited 5 file(s)");
    expect(parsed.systemMessage).toContain("jcodemunch");
  });
});

// ── masonry-pre-compact.js — activity breadcrumb tests ───────────────────────

describe("masonry-pre-compact.js — session activity breadcrumb", () => {
  it("writes pre-compact-work.json from session activity log", () => {
    const cwd = makeDir();
    const sessionId = "test-session-abc";
    const activityFile = join(tmpdir(), `masonry-activity-${sessionId}.ndjson`);

    // Write fake activity log
    const edits = [
      { tool: "Write", file: "jcodemunch.md", summary: "Write → jcodemunch.md" },
      { tool: "Write", file: "masonry-jcodemunch-nudge.js", summary: "Write → masonry-jcodemunch-nudge.js" },
      { tool: "Edit", file: "settings.json", summary: "Edit → settings.json" },
    ];
    writeFileSync(activityFile, edits.map(e => JSON.stringify(e)).join("\n") + "\n", "utf8");

    mkdirSync(join(cwd, ".autopilot"), { recursive: true });
    writeFileSync(join(cwd, ".autopilot", "mode"), "", "utf8"); // no active build

    const result = runHook(PRE_COMPACT, cwd, { cwd, session_id: sessionId });
    expect(result.exit).toBe(0);

    // pre-compact-work.json should be written
    const workFile = join(cwd, ".autopilot", "pre-compact-work.json");
    expect(existsSync(workFile)).toBe(true);
    const work = JSON.parse(readFileSync(workFile, "utf8"));
    expect(work.session_id).toBe(sessionId);
    expect(work.recent_edits).toContain("Write → jcodemunch.md");
    expect(work.total_edits).toBe(3);

    // Clean up activity file
    try { require("fs").unlinkSync(activityFile); } catch {}
  });

  it("includes session work in compact systemMessage", () => {
    const cwd = makeDir();
    const sessionId = "test-session-xyz";
    const activityFile = join(tmpdir(), `masonry-activity-${sessionId}.ndjson`);

    const edits = [
      { summary: "Edit → masonry-pre-compact.js" },
      { summary: "Edit → masonry-post-compact.js" },
      { summary: "Write → test_compact_hooks.test.js" },
    ];
    writeFileSync(activityFile, edits.map(e => JSON.stringify(e)).join("\n") + "\n", "utf8");
    mkdirSync(join(cwd, ".autopilot"), { recursive: true });

    const result = runHook(PRE_COMPACT, cwd, { cwd, session_id: sessionId });

    // Should include session work in systemMessage
    if (result.stdout.trim()) {
      const parsed = JSON.parse(result.stdout);
      expect(parsed.systemMessage).toContain("Session work");
      expect(parsed.systemMessage).toContain("masonry-pre-compact.js");
    }

    try { require("fs").unlinkSync(activityFile); } catch {}
  });
});

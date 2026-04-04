/**
 * Hook output schema validation harness.
 *
 * Pipes known JSON payloads through each hook and verifies:
 *   1. Valid JSON on stdout (or empty for silent hooks)
 *   2. Output matches expected schema for the hook's event type
 *   3. No process crash (exit code 0)
 *
 * Uses execFileSync to mirror how Claude Code's hook-runner invokes hooks.
 */
import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect } from "vitest";

const HOOKS_DIR = join(process.cwd(), "src", "hooks");

function runHook(hookFile, stdinPayload, cwd) {
  const env = { ...process.env };
  delete env.PWD;
  // Prevent hooks from hitting real Recall/Ollama
  env.RECALL_HOST = "http://127.0.0.1:1";
  env.OLLAMA_HOST = "http://127.0.0.1:1";
  const hookPath = join(HOOKS_DIR, hookFile);
  const result = { stdout: "", stderr: "", exitCode: 0 };
  try {
    const out = execFileSync("node", [hookPath], {
      input: JSON.stringify(stdinPayload),
      cwd: cwd || tmpdir(),
      env,
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 10000,
    });
    result.stdout = out.toString("utf8").trim();
  } catch (e) {
    result.exitCode = e.status ?? 1;
    result.stdout = (e.stdout || "").toString("utf8").trim();
    result.stderr = (e.stderr || "").toString("utf8").trim();
  }
  return result;
}

function parseOutput(result) {
  if (!result.stdout) return null;
  return JSON.parse(result.stdout);
}

function makeDir() {
  return mkdtempSync(join(tmpdir(), "hook-schema-test-"));
}

// ─── SessionStart: masonry-session-start.js ──────────────────────────────────

describe("masonry-session-start.js schema", () => {
  it("outputs { systemMessage } or empty on clean dir", () => {
    const dir = makeDir();
    const result = runHook("masonry-session-start.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    if (result.stdout) {
      const parsed = parseOutput(result);
      expect(parsed).toHaveProperty("systemMessage");
      expect(typeof parsed.systemMessage).toBe("string");
      // Must NOT contain hookSpecificOutput
      expect(parsed).not.toHaveProperty("hookSpecificOutput");
    }
  });

  it("outputs { systemMessage } with autopilot state", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build");
    writeFileSync(
      join(dir, ".autopilot", "progress.json"),
      JSON.stringify({
        project: "test",
        tasks: [{ id: 1, description: "task", status: "DONE" }],
      })
    );
    const result = runHook("masonry-session-start.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    const parsed = parseOutput(result);
    expect(parsed).toHaveProperty("systemMessage");
    expect(parsed.systemMessage).toContain("Autopilot");
    expect(parsed).not.toHaveProperty("hookSpecificOutput");
  });

  it("outputs { systemMessage } on interrupted build (earlyExit path)", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build");
    writeFileSync(
      join(dir, ".autopilot", "progress.json"),
      JSON.stringify({
        project: "test",
        tasks: [
          { id: 1, description: "done task", status: "DONE" },
          { id: 2, description: "pending task", status: "PENDING" },
        ],
      })
    );
    const result = runHook("masonry-session-start.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    const parsed = parseOutput(result);
    expect(parsed).toHaveProperty("systemMessage");
    expect(parsed.systemMessage).toContain("Interrupted");
    expect(parsed).not.toHaveProperty("hookSpecificOutput");
  });
});

// ─── UserPromptSubmit: masonry-prompt-router.js ──────────────────────────────

describe("masonry-prompt-router.js schema", () => {
  it("outputs { additionalContext } for routable prompts", () => {
    const result = runHook("masonry-prompt-router.js", {
      prompt: "debug the failing authentication service",
      cwd: "/tmp",
    });
    expect(result.exitCode).toBe(0);
    const parsed = parseOutput(result);
    expect(parsed).toHaveProperty("additionalContext");
    expect(typeof parsed.additionalContext).toBe("string");
    expect(parsed).not.toHaveProperty("hookSpecificOutput");
    expect(parsed).not.toHaveProperty("systemMessage");
  });

  it("outputs soft hint for low-effort queries", () => {
    const result = runHook("masonry-prompt-router.js", {
      prompt: "what port does the redis cache run on?",
      cwd: "/tmp",
    });
    expect(result.exitCode).toBe(0);
    if (result.stdout) {
      const parsed = parseOutput(result);
      expect(parsed).toHaveProperty("additionalContext");
      expect(parsed.additionalContext).toContain("ROUTING HINT");
      expect(parsed.additionalContext).not.toContain("You MUST");
    }
  });

  it("outputs MUST hint for high-effort queries", () => {
    const result = runHook("masonry-prompt-router.js", {
      prompt: "refactor the entire authentication system across all services and update tests",
      cwd: "/tmp",
    });
    expect(result.exitCode).toBe(0);
    const parsed = parseOutput(result);
    expect(parsed).toHaveProperty("additionalContext");
    expect(parsed.additionalContext).toContain("MASONRY ROUTING");
  });

  it("silent for short prompts", () => {
    const result = runHook("masonry-prompt-router.js", {
      prompt: "hi",
      cwd: "/tmp",
    });
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("");
  });

  it("silent for slash commands", () => {
    const result = runHook("masonry-prompt-router.js", {
      prompt: "/build start the project",
      cwd: "/tmp",
    });
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("");
  });
});

// ─── PreCompact: masonry-pre-compact.js ──────────────────────────────────────

describe("masonry-pre-compact.js schema", () => {
  it("outputs { systemMessage } or empty with autopilot state", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build");
    writeFileSync(
      join(dir, ".autopilot", "progress.json"),
      JSON.stringify({
        project: "test",
        status: "BUILDING",
        tasks: [{ id: 1, description: "task", status: "IN_PROGRESS" }],
      })
    );
    const result = runHook("masonry-pre-compact.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    if (result.stdout) {
      const parsed = parseOutput(result);
      expect(parsed).toHaveProperty("systemMessage");
      expect(parsed).not.toHaveProperty("hookSpecificOutput");
    }
  });

  it("silent on clean dir with no state", () => {
    const dir = makeDir();
    const result = runHook("masonry-pre-compact.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    // May or may not have output depending on campaign state
  });
});

// ─── TeammateIdle: masonry-teammate-idle.js ──────────────────────────────────

describe("masonry-teammate-idle.js schema", () => {
  it("outputs { systemMessage } with pending task", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build");
    writeFileSync(
      join(dir, ".autopilot", "progress.json"),
      JSON.stringify({
        project: "test",
        tasks: [
          { id: 1, description: "first task", status: "DONE" },
          { id: 2, description: "second task", status: "PENDING" },
        ],
      })
    );
    const result = runHook("masonry-teammate-idle.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    const parsed = parseOutput(result);
    expect(parsed).toHaveProperty("systemMessage");
    expect(parsed.systemMessage).toContain("Auto-assigning task #2");
    expect(parsed).not.toHaveProperty("hookSpecificOutput");
  });

  it("outputs all-complete message when no pending tasks", () => {
    const dir = makeDir();
    mkdirSync(join(dir, ".autopilot"), { recursive: true });
    writeFileSync(join(dir, ".autopilot", "mode"), "build");
    writeFileSync(
      join(dir, ".autopilot", "progress.json"),
      JSON.stringify({
        project: "test",
        tasks: [{ id: 1, description: "done task", status: "DONE" }],
      })
    );
    const result = runHook("masonry-teammate-idle.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    if (result.stdout) {
      const parsed = parseOutput(result);
      expect(parsed).toHaveProperty("systemMessage");
      expect(parsed.systemMessage).toContain("complete");
    }
  });

  it("silent when no .autopilot directory", () => {
    const dir = makeDir();
    const result = runHook("masonry-teammate-idle.js", { cwd: dir }, dir);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("");
  });
});

// ─── Stop: masonry-context-monitor.js ────────────────────────────────────────

describe("masonry-context-monitor.js schema", () => {
  it("silent for small transcripts (no block, no warning)", () => {
    const dir = makeDir();
    // Create a tiny transcript file
    const transcriptPath = join(dir, "transcript.jsonl");
    writeFileSync(transcriptPath, '{"role":"user"}\n'.repeat(10));
    const result = runHook(
      "masonry-context-monitor.js",
      { transcript_path: transcriptPath, cwd: dir },
      dir
    );
    expect(result.exitCode).toBe(0);
    // Small transcript should produce no stdout (no block decision)
    expect(result.stdout).toBe("");
  });

  it("outputs { decision, reason } for large transcript with dirty repo", () => {
    const dir = makeDir();
    // Create a large transcript file (>750K tokens = >3MB)
    const transcriptPath = join(dir, "transcript.jsonl");
    writeFileSync(transcriptPath, "x".repeat(4_000_000));
    // Init git repo with uncommitted file
    const { execSync } = require("child_process");
    execSync("git init", { cwd: dir, stdio: "pipe" });
    writeFileSync(join(dir, "dirty.txt"), "uncommitted");
    execSync("git add dirty.txt", { cwd: dir, stdio: "pipe" });
    const result = runHook(
      "masonry-context-monitor.js",
      { transcript_path: transcriptPath, cwd: dir },
      dir
    );
    expect(result.exitCode).toBe(0);
    if (result.stdout) {
      const parsed = parseOutput(result);
      expect(parsed).toHaveProperty("decision", "block");
      expect(parsed).toHaveProperty("reason");
      expect(parsed).not.toHaveProperty("hookSpecificOutput");
      expect(parsed).not.toHaveProperty("systemMessage");
    }
  });
});

// ─── Cross-cutting: no hookSpecificOutput in non-PreToolUse hooks ────────────

describe("hookSpecificOutput isolation", () => {
  const NON_PRETOOLUSE_HOOKS = [
    "masonry-session-start.js",
    "masonry-prompt-router.js",
    "masonry-pre-compact.js",
    "masonry-teammate-idle.js",
    "masonry-context-monitor.js",
  ];

  it.each(NON_PRETOOLUSE_HOOKS)(
    "%s never outputs hookSpecificOutput",
    (hookFile) => {
      const dir = makeDir();
      // Give each hook something to work with
      mkdirSync(join(dir, ".autopilot"), { recursive: true });
      writeFileSync(join(dir, ".autopilot", "mode"), "build");
      writeFileSync(
        join(dir, ".autopilot", "progress.json"),
        JSON.stringify({
          project: "test",
          tasks: [{ id: 1, description: "task", status: "PENDING" }],
        })
      );

      const payload =
        hookFile === "masonry-prompt-router.js"
          ? { prompt: "research the authentication patterns", cwd: dir }
          : hookFile === "masonry-context-monitor.js"
            ? (() => {
                const tp = join(dir, "t.jsonl");
                writeFileSync(tp, "x");
                return { transcript_path: tp, cwd: dir };
              })()
            : { cwd: dir };

      const result = runHook(hookFile, payload, dir);
      expect(result.exitCode).toBe(0);
      if (result.stdout) {
        const parsed = JSON.parse(result.stdout);
        expect(parsed).not.toHaveProperty("hookSpecificOutput");
      }
    }
  );
});

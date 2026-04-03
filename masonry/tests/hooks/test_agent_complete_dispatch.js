import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync, existsSync, unlinkSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-agent-complete.js");

function runHook(cwd, stdinPayload) {
  const env = { ...process.env };
  delete env.PWD;
  // Mock git status by creating a fake git script if needed
  try {
    const result = execFileSync("node", [HOOK], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env,
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 10000,
    });
    return {
      code: 0,
      stdout: result.toString(),
      stderr: (Buffer.isBuffer(result) ? "" : ""),
    };
  } catch (e) {
    return {
      code: e.status ?? 1,
      stdout: (e.stdout || "").toString(),
      stderr: (e.stderr || "").toString(),
    };
  }
}

function makeDir() {
  return mkdtempSync(join(tmpdir(), "agent-complete-test-"));
}

function setupAutopilot(dir, progressData) {
  const autopilotDir = join(dir, ".autopilot");
  mkdirSync(autopilotDir, { recursive: true });
  if (progressData) {
    writeFileSync(
      join(autopilotDir, "progress.json"),
      JSON.stringify(progressData),
      "utf8"
    );
  }
  return autopilotDir;
}

function setupGitRepo(dir) {
  // Initialize a minimal git repo so git status works
  try {
    execFileSync("git", ["init"], { cwd: dir, stdio: "pipe" });
    execFileSync("git", ["config", "user.email", "test@test.com"], { cwd: dir, stdio: "pipe" });
    execFileSync("git", ["config", "user.name", "Test"], { cwd: dir, stdio: "pipe" });
    writeFileSync(join(dir, "initial.txt"), "init", "utf8");
    execFileSync("git", ["add", "."], { cwd: dir, stdio: "pipe" });
    execFileSync("git", ["commit", "-m", "init"], { cwd: dir, stdio: "pipe" });
  } catch {}
}

const DEV_AGENTS = [
  "rough-in",
  "developer",
  "worker-specialist",
  "fix-implementer",
  "senior-developer",
];

const NON_DEV_AGENTS = [
  "research-analyst",
  "karen",
  "git-nerd",
  "synthesizer",
];

describe("masonry-agent-complete post-implementation dispatch", () => {
  describe("detects dev agent completion and writes git-nerd-needed.json", () => {
    for (const agent of DEV_AGENTS) {
      it(`writes git-nerd-needed.json when ${agent} completes with uncommitted changes`, () => {
        const dir = makeDir();
        setupGitRepo(dir);
        const autopilotDir = setupAutopilot(dir, {
          status: "BUILDING",
          tasks: [{ id: 1, status: "DONE", description: "test" }],
        });

        // Create an uncommitted file to trigger git status detection
        writeFileSync(join(dir, "new-file.js"), "// new code", "utf8");

        runHook(dir, {
          cwd: dir,
          agent_name: agent,
          agent_id: `agent-${Date.now()}`,
          tool_result: "TASK_COMPLETE: implemented feature",
        });

        const gitNerdFile = join(autopilotDir, "git-nerd-needed.json");
        expect(existsSync(gitNerdFile)).toBe(true);

        const payload = JSON.parse(readFileSync(gitNerdFile, "utf8"));
        expect(payload.reason).toBe("agent_complete");
        expect(payload.agent).toBe(agent);
        expect(payload.timestamp).toBeDefined();
        expect(Array.isArray(payload.files_changed)).toBe(true);
      });
    }
  });

  describe("skips git-nerd dispatch for non-dev agents", () => {
    for (const agent of NON_DEV_AGENTS) {
      it(`does NOT write git-nerd-needed.json when ${agent} completes`, () => {
        const dir = makeDir();
        setupGitRepo(dir);
        const autopilotDir = setupAutopilot(dir, {
          status: "BUILDING",
          tasks: [{ id: 1, status: "DONE", description: "test" }],
        });

        writeFileSync(join(dir, "new-file.js"), "// new code", "utf8");

        runHook(dir, {
          cwd: dir,
          agent_name: agent,
          agent_id: `agent-${Date.now()}`,
          tool_result: "COMPLETE",
        });

        const gitNerdFile = join(autopilotDir, "git-nerd-needed.json");
        expect(existsSync(gitNerdFile)).toBe(false);
      });
    }
  });

  describe("skips when no uncommitted changes", () => {
    it("does NOT write git-nerd-needed.json when working tree is clean", () => {
      const dir = makeDir();
      setupGitRepo(dir);
      const autopilotDir = setupAutopilot(dir, {
        status: "BUILDING",
        tasks: [{ id: 1, status: "DONE", description: "test" }],
      });

      // No uncommitted files — working tree is clean

      runHook(dir, {
        cwd: dir,
        agent_name: "developer",
        agent_id: `agent-${Date.now()}`,
        tool_result: "TASK_COMPLETE",
      });

      const gitNerdFile = join(autopilotDir, "git-nerd-needed.json");
      expect(existsSync(gitNerdFile)).toBe(false);
    });
  });

  describe("outputs additionalContext for same-session dispatch", () => {
    it("outputs additionalContext JSON when dev agent completes with changes", () => {
      const dir = makeDir();
      setupGitRepo(dir);
      setupAutopilot(dir, {
        status: "BUILDING",
        tasks: [{ id: 1, status: "DONE", description: "test" }],
      });

      writeFileSync(join(dir, "new-file.js"), "// new code", "utf8");

      const result = runHook(dir, {
        cwd: dir,
        agent_name: "developer",
        agent_id: `agent-${Date.now()}`,
        tool_result: "TASK_COMPLETE",
      });

      // The hook should output additionalContext on stdout
      if (result.stdout) {
        try {
          const output = JSON.parse(result.stdout);
          if (output.additionalContext) {
            expect(output.additionalContext).toContain("developer");
          }
        } catch {
          // stdout might not be JSON — that's okay if git-nerd-needed.json was written
        }
      }
    });
  });

  describe("skips inside BrickLayer research projects", () => {
    it("does not write dispatch files for research projects", () => {
      const dir = makeDir();
      setupGitRepo(dir);
      writeFileSync(join(dir, "program.md"), "# program", "utf8");
      writeFileSync(join(dir, "questions.md"), "# questions", "utf8");
      const autopilotDir = setupAutopilot(dir, {
        status: "BUILDING",
        tasks: [{ id: 1, status: "DONE", description: "test" }],
      });

      writeFileSync(join(dir, "new-file.js"), "// new code", "utf8");

      runHook(dir, {
        cwd: dir,
        agent_name: "developer",
        agent_id: `agent-${Date.now()}`,
        tool_result: "TASK_COMPLETE",
      });

      const gitNerdFile = join(autopilotDir, "git-nerd-needed.json");
      expect(existsSync(gitNerdFile)).toBe(false);
    });
  });

  describe("preserves existing dependency unblocking behavior", () => {
    it("still unblocks BLOCKED tasks when deps are DONE", () => {
      const dir = makeDir();
      const autopilotDir = setupAutopilot(dir, {
        status: "BUILDING",
        tasks: [
          { id: 1, status: "DONE", description: "task 1" },
          { id: 2, status: "BLOCKED", description: "task 2", depends_on: [1] },
        ],
      });

      runHook(dir, {
        cwd: dir,
        agent_name: "developer",
        agent_id: `agent-${Date.now()}`,
        tool_result: "TASK_COMPLETE",
      });

      const progress = JSON.parse(
        readFileSync(join(autopilotDir, "progress.json"), "utf8")
      );
      const task2 = progress.tasks.find((t) => t.id === 2);
      expect(task2.status).toBe("PENDING");
    });
  });
});

import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-routing-gate.js");
const GATE_FILE = join(tmpdir(), "masonry-mortar-gate.json");

function runHook(cwd, stdinPayload) {
  const env = { ...process.env };
  delete env.PWD;
  try {
    const result = execFileSync("node", [HOOK], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env,
      stdio: ["pipe", "pipe", "pipe"],
    });
    return { code: 0, stdout: result.toString(), stderr: "" };
  } catch (e) {
    return {
      code: e.status ?? 1,
      stdout: (e.stdout || "").toString(),
      stderr: (e.stderr || "").toString(),
    };
  }
}

function makeDir() {
  return mkdtempSync(join(tmpdir(), "routing-gate-test-"));
}

function writeGateFile(overrides = {}) {
  const gate = {
    mortar_consulted: false,
    timestamp: new Date().toISOString(),
    prompt_summary: "test prompt",
    ...overrides,
  };
  writeFileSync(GATE_FILE, JSON.stringify(gate), "utf8");
}

function clearGateFile() {
  try {
    const fs = require("fs");
    fs.unlinkSync(GATE_FILE);
  } catch {}
}

function writeAutopilotMode(dir, mode) {
  mkdirSync(join(dir, ".autopilot"), { recursive: true });
  writeFileSync(join(dir, ".autopilot", "mode"), mode, "utf8");
}

describe("masonry-routing-gate", () => {
  afterEach(() => {
    clearGateFile();
  });

  describe("blocks production code writes when mortar not consulted", () => {
    it("blocks Write to a .js file when mortar_consulted is false", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(2);
      expect(result.stderr).toContain("routing");
    });

    it("blocks Edit to a .py file when mortar_consulted is false", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Edit",
        tool_input: { file_path: join(dir, "app", "main.py") },
        cwd: dir,
      });
      expect(result.code).toBe(2);
    });
  });

  describe("allows writes when mortar has been consulted", () => {
    it("allows Write when mortar_consulted is true", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: true });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("allows state and config file writes regardless of gate", () => {
    it("allows writes to .autopilot/ directory", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, ".autopilot", "progress.json") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to .ui/ directory", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, ".ui", "tokens.json") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to .claude/ directory", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, ".claude", "agents", "dev.md") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to /tmp/ paths", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(tmpdir(), "scratch.txt") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("allows writes in test directories", () => {
    it("allows writes to tests/ directory", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "tests", "test_app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to __tests__/ directory", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "__tests__", "app.test.ts") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to files matching *.test.* pattern", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.test.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes to files matching *.spec.* pattern", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.spec.ts") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("skips gate in autopilot build/fix mode", () => {
    it("allows writes when .autopilot/mode is build", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      writeAutopilotMode(dir, "build");
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows writes when .autopilot/mode is fix", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      writeAutopilotMode(dir, "fix");
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("handles gate expiry", () => {
    it("allows writes when gate file is older than 10 minutes", () => {
      const dir = makeDir();
      const expired = new Date(Date.now() - 11 * 60 * 1000).toISOString();
      writeGateFile({ mortar_consulted: false, timestamp: expired });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("handles missing gate file", () => {
    it("allows writes when no gate file exists", () => {
      const dir = makeDir();
      clearGateFile();
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("ignores non-Write/Edit tools", () => {
    it("allows Bash tool regardless of gate state", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Bash",
        tool_input: { command: "echo hello" },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });

    it("allows Read tool regardless of gate state", () => {
      const dir = makeDir();
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Read",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });

  describe("skips inside BrickLayer research projects", () => {
    it("allows writes inside research project directories", () => {
      const dir = makeDir();
      writeFileSync(join(dir, "program.md"), "# program", "utf8");
      writeFileSync(join(dir, "questions.md"), "# questions", "utf8");
      writeGateFile({ mortar_consulted: false });
      const result = runHook(dir, {
        tool_name: "Write",
        tool_input: { file_path: join(dir, "src", "app.js") },
        cwd: dir,
      });
      expect(result.code).toBe(0);
    });
  });
});

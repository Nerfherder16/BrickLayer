import { execFileSync, spawnSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync, existsSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { tmpdir } from "os";
import { describe, it, expect } from "vitest";

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOOK = join(__dirname, "..", "..", "src", "hooks", "masonry-stop-guard.js");

function makeGitRepo() {
  const dir = mkdtempSync(join(tmpdir(), "stop-guard-karen-test-"));
  spawnSync("git", ["init"], { cwd: dir });
  spawnSync("git", ["config", "user.email", "test@test.com"], { cwd: dir });
  spawnSync("git", ["config", "user.name", "Test"], { cwd: dir });
  return dir;
}

function commit(dir, filename, content = "content") {
  const filePath = join(dir, filename);
  const fileDir = join(dir, filename.includes("/") ? filename.split("/").slice(0, -1).join("/") : "");
  if (filename.includes("/")) mkdirSync(fileDir, { recursive: true });
  writeFileSync(filePath, content);
  spawnSync("git", ["add", filename], { cwd: dir });
  spawnSync("git", ["commit", "-m", `add ${filename}`], { cwd: dir });
}

function runHook(cwd, stdinPayload) {
  try {
    execFileSync("node", [HOOK], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env: { ...process.env },
      stdio: ["pipe", "pipe", "pipe"],
    });
    return 0;
  } catch (e) {
    return e.status ?? 1;
  }
}

describe("stop-guard karen flag file", () => {
  it("writes karen-needed.json when source committed and docs are stale", () => {
    const dir = makeGitRepo();
    mkdirSync(join(dir, ".autopilot"));
    // Use a path matching SOURCE_PATTERNS (masonry/ prefix)
    commit(dir, "masonry/feature.py", "def foo(): pass");
    runHook(dir, { session_id: "s1", tool_name: "Stop" });
    const flagPath = join(dir, ".autopilot", "karen-needed.json");
    expect(existsSync(flagPath)).toBe(true);
    const flag = JSON.parse(readFileSync(flagPath, "utf8"));
    expect(flag.reason).toBe("doc_staleness");
    expect(Array.isArray(flag.stale_files)).toBe(true);
    expect(flag.stale_files.length).toBeGreaterThan(0);
    expect(flag.timestamp).toBeDefined();
  });

  it("does NOT write flag when docs are also committed", () => {
    const dir = makeGitRepo();
    mkdirSync(join(dir, ".autopilot"));
    commit(dir, "masonry/feature.py", "def foo(): pass");
    // Commit all PROJECT_DOCS entries
    commit(dir, "README.md", "# Read me");
    commit(dir, "PROJECT_STATUS.md", "# Status");
    commit(dir, "ROADMAP.md", "# Roadmap");
    mkdirSync(join(dir, "docs/architecture"), { recursive: true });
    commit(dir, "docs/architecture/ARCHITECTURE.md", "# Arch");
    runHook(dir, { session_id: "s1", tool_name: "Stop" });
    const flagPath = join(dir, ".autopilot", "karen-needed.json");
    expect(existsSync(flagPath)).toBe(false);
  });

  it("does NOT write flag when only doc files changed (no source changes)", () => {
    const dir = makeGitRepo();
    mkdirSync(join(dir, ".autopilot"));
    commit(dir, "CHANGELOG.md", "# Changelog");
    runHook(dir, { session_id: "s1", tool_name: "Stop" });
    const flagPath = join(dir, ".autopilot", "karen-needed.json");
    expect(existsSync(flagPath)).toBe(false);
  });

  it("does NOT crash when no .autopilot directory exists", () => {
    const dir = makeGitRepo();
    commit(dir, "masonry/feature.py", "def foo(): pass");
    expect(() => runHook(dir, { session_id: "s1", tool_name: "Stop" })).not.toThrow();
    expect(existsSync(join(dir, ".autopilot", "karen-needed.json"))).toBe(false);
  });

  it("karen-needed.json has correct schema shape", () => {
    const dir = makeGitRepo();
    mkdirSync(join(dir, ".autopilot"));
    commit(dir, "masonry/feature.py", "x=1");
    runHook(dir, { session_id: "s1", tool_name: "Stop" });
    const flagPath = join(dir, ".autopilot", "karen-needed.json");
    if (!existsSync(flagPath)) return;
    const flag = JSON.parse(readFileSync(flagPath, "utf8"));
    expect(flag).toHaveProperty("reason");
    expect(flag).toHaveProperty("stale_files");
    expect(flag).toHaveProperty("timestamp");
  });
});

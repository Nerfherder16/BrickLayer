import { execFileSync } from "child_process";
import { mkdtempSync, writeFileSync, mkdirSync, existsSync, rmSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { tmpdir } from "os";
import { describe, it, expect } from "vitest";

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOOK = join(__dirname, "..", "..", "src", "hooks", "masonry-session-start.js");

function runHook(cwd, stdinPayload) {
  try {
    const result = execFileSync("node", [HOOK], {
      input: JSON.stringify(stdinPayload),
      cwd,
      env: { ...process.env, PWD: cwd },
      stdio: ["pipe", "pipe", "pipe"],
    });
    return { code: 0, stdout: result.toString() };
  } catch (e) {
    return { code: e.status ?? 1, stdout: e.stdout?.toString() ?? "" };
  }
}

function makeDir() {
  const dir = mkdtempSync(join(tmpdir(), "session-start-karen-test-"));
  mkdirSync(join(dir, ".autopilot"), { recursive: true });
  return dir;
}

describe("session-start karen flag pickup", () => {
  it("injects doc maintenance directive when karen-needed.json exists", () => {
    const dir = makeDir();
    writeFileSync(
      join(dir, ".autopilot", "karen-needed.json"),
      JSON.stringify({
        reason: "doc_staleness",
        stale_files: ["CHANGELOG.md", "ROADMAP.md"],
        timestamp: new Date().toISOString(),
      })
    );
    const { stdout } = runHook(dir, { session_id: "s1" });
    expect(stdout).toContain("Doc maintenance needed");
    expect(stdout).toContain("CHANGELOG.md");
  });

  it("deletes the flag file after pickup", () => {
    const dir = makeDir();
    const flagPath = join(dir, ".autopilot", "karen-needed.json");
    writeFileSync(
      flagPath,
      JSON.stringify({ reason: "doc_staleness", stale_files: ["CHANGELOG.md"], timestamp: new Date().toISOString() })
    );
    runHook(dir, { session_id: "s1" });
    expect(existsSync(flagPath)).toBe(false);
  });

  it("produces no karen output when no flag file exists", () => {
    const dir = makeDir();
    const { stdout } = runHook(dir, { session_id: "s1" });
    expect(stdout).not.toContain("Doc maintenance needed");
    expect(stdout).not.toContain("karen");
  });

  it("does not crash when flag file contains malformed JSON", () => {
    const dir = makeDir();
    writeFileSync(join(dir, ".autopilot", "karen-needed.json"), "{ invalid json }");
    expect(() => runHook(dir, { session_id: "s1" })).not.toThrow();
    // Should produce no karen output (graceful skip)
    const { stdout } = runHook(dir, { session_id: "s1" });
    expect(stdout).not.toContain("Doc maintenance needed");
  });
});

import { spawnSync } from "child_process";
import { mkdtempSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { describe, it, expect } from "vitest";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-jcodemunch-nudge.js");

function runHook(toolInput) {
  const env = { ...process.env };
  delete env.PWD;
  const result = spawnSync("node", [HOOK], {
    input: JSON.stringify({ tool_input: toolInput }),
    env,
    encoding: "utf8",
  });
  return {
    exit: result.status ?? 1,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
  };
}

/** Create a temp file of approximately `sizeBytes` bytes. */
function makeTempFile(ext, sizeBytes) {
  const dir = mkdtempSync(join(tmpdir(), "jcode-nudge-"));
  const filePath = join(dir, `large_service${ext}`);
  // Fill with JS-like content so it looks real
  const line = "const x = 1; // placeholder line for testing\n";
  const content = line.repeat(Math.ceil(sizeBytes / line.length)).slice(0, sizeBytes);
  writeFileSync(filePath, content, "utf8");
  return filePath;
}

describe("masonry-jcodemunch-nudge.js", () => {
  // ── Exempt cases — always pass ─────────────────────────────────────────────

  it("passes silently for non-code file extensions", () => {
    const result = runHook({ file_path: "/some/path/config.json" });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("passes silently for test files", () => {
    const result = runHook({ file_path: "/some/path/my.test.js" });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("passes silently when offset is specified (targeted read)", () => {
    const large = makeTempFile(".js", 10000);
    const result = runHook({ file_path: large, offset: 0 });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("passes silently when limit is specified (partial read)", () => {
    const large = makeTempFile(".ts", 10000);
    const result = runHook({ file_path: large, limit: 50 });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("passes silently for small code files (< 3KB)", () => {
    const small = makeTempFile(".js", 2000);
    const result = runHook({ file_path: small });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });

  // ── Nudge zone (3–8KB) ──────────────────────────────────────────────────────

  it("nudges but does NOT block medium-sized code files (3–8KB)", () => {
    const medium = makeTempFile(".py", 5000);
    const result = runHook({ file_path: medium });
    expect(result.exit).toBe(0); // non-blocking
    expect(result.stderr).toContain("consider symbol-level retrieval");
    expect(result.stderr).toContain("get_file_outline");
    expect(result.stderr).not.toContain("BLOCKED");
  });

  // ── Block zone (> 8KB) ──────────────────────────────────────────────────────

  it("BLOCKS large code files (> 8KB) with exit 2", () => {
    const large = makeTempFile(".js", 10000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain("BLOCKED");
    expect(result.stderr).toContain("wastes tokens");
    expect(result.stderr).toContain("get_file_outline");
    expect(result.stderr).toContain("get_symbol_source");
    expect(result.stderr).toContain("search_symbols");
  });

  it("BLOCKS large TypeScript files", () => {
    const large = makeTempFile(".ts", 12000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain("BLOCKED");
  });

  it("BLOCKS large Python files", () => {
    const large = makeTempFile(".py", 9000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain("BLOCKED");
  });

  it("BLOCKS large Rust files", () => {
    const large = makeTempFile(".rs", 15000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain("BLOCKED");
  });

  it("block message includes exact file_path for copy-paste convenience", () => {
    const large = makeTempFile(".js", 10000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain(large);
  });

  it("block message includes bypass instruction (offset=0)", () => {
    const large = makeTempFile(".js", 10000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toContain("offset=0");
  });

  // ── Size display ─────────────────────────────────────────────────────────────

  it("shows KB size in the block message", () => {
    const large = makeTempFile(".go", 10000);
    const result = runHook({ file_path: large });
    expect(result.exit).toBe(2);
    expect(result.stderr).toMatch(/\d+\.\d+KB/);
  });

  // ── Missing file ─────────────────────────────────────────────────────────────

  it("passes silently for a file that does not exist (avoids crashing)", () => {
    const result = runHook({ file_path: "/nonexistent/path/service.ts" });
    expect(result.exit).toBe(0);
    expect(result.stderr).toBe("");
  });
});

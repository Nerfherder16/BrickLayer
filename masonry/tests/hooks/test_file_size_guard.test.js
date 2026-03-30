import { execFileSync, spawnSync } from "child_process";
import { join } from "path";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "fs";
import os from "os";
import path from "path";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-file-size-guard.js");

/**
 * Run the file-size-guard hook with a synthetic tool payload.
 * The hook reads the actual file from disk, so we create a temp file first.
 * Returns { exitCode, stderr }.
 */
function runHook(toolName, toolInput) {
  const result = spawnSync("node", [HOOK], {
    input: JSON.stringify({ tool_name: toolName, tool_input: toolInput }),
    stdio: ["pipe", "pipe", "pipe"],
    encoding: "utf8",
  });
  return {
    exitCode: result.status ?? 1,
    stderr: result.stderr || "",
    stdout: result.stdout || "",
  };
}

/**
 * Create a temp file with N lines of content and return its absolute path.
 */
function makeTempFile(lines, ext = ".js") {
  // Avoid digits-underscore patterns that match the migration file regex /^\d{4}_/
  const rnd = Math.random().toString(36).slice(2, 8);
  const tmpPath = join(os.tmpdir(), `masonry-guard-${rnd}${ext}`);
  const content = Array.from({ length: lines }, (_, i) => `const x${i} = ${i};`).join("\n");
  fs.writeFileSync(tmpPath, content, "utf8");
  return tmpPath;
}

// ---------------------------------------------------------------------------
// Hard block: > 300 lines must exit 2
// ---------------------------------------------------------------------------

describe("file-size-guard — hard block (>300 lines)", () => {
  it("exits 2 and outputs FILE_SIZE_BLOCK for a .js file with 301 lines", () => {
    const tmpFile = makeTempFile(301, ".js");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(2);
      expect(stderr).toContain("FILE_SIZE_BLOCK");
      expect(stderr).toContain("301");
      expect(stderr).toContain("300");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exits 2 for a .ts file with 350 lines", () => {
    const tmpFile = makeTempFile(350, ".ts");
    try {
      const { exitCode, stderr } = runHook("Edit", { file_path: tmpFile });
      expect(exitCode).toBe(2);
      expect(stderr).toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exits 2 for a .py file with 400 lines", () => {
    const tmpFile = makeTempFile(400, ".py");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(2);
      expect(stderr).toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("FILE_SIZE_BLOCK message includes the file path", () => {
    const tmpFile = makeTempFile(310, ".js");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(2);
      expect(stderr).toContain(tmpFile);
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

// ---------------------------------------------------------------------------
// Warning zone: 251–300 lines must exit 0 with FILE_SIZE_WARN
// ---------------------------------------------------------------------------

describe("file-size-guard — warning zone (251–300 lines)", () => {
  it("exits 0 with FILE_SIZE_WARN for a .js file with 260 lines", () => {
    const tmpFile = makeTempFile(260, ".js");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).toContain("FILE_SIZE_WARN");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exits 0 with FILE_SIZE_WARN for exactly 300 lines", () => {
    const tmpFile = makeTempFile(300, ".ts");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).toContain("FILE_SIZE_WARN");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

// ---------------------------------------------------------------------------
// Clean files: ≤ 250 lines must exit 0 silently
// ---------------------------------------------------------------------------

describe("file-size-guard — clean files (≤250 lines)", () => {
  it("exits 0 silently for a .js file with 100 lines", () => {
    const tmpFile = makeTempFile(100, ".js");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).toBe("");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exits 0 silently for a .py file with 250 lines (boundary)", () => {
    const tmpFile = makeTempFile(250, ".py");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).toBe("");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

// ---------------------------------------------------------------------------
// Test file exemptions — must always exit 0 regardless of line count
// ---------------------------------------------------------------------------

describe("file-size-guard — test file exemptions", () => {
  it("exempts test_ prefixed .js files even if >300 lines", () => {
    const tmpDir = os.tmpdir();
    const tmpFile = join(tmpDir, `test_large_module_${Date.now()}.js`);
    const content = Array.from({ length: 350 }, (_, i) => `const x${i} = ${i};`).join("\n");
    fs.writeFileSync(tmpFile, content);
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exempts *.test.js files even if >300 lines", () => {
    const tmpDir = os.tmpdir();
    const tmpFile = join(tmpDir, `my_module_${Date.now()}.test.js`);
    const content = Array.from({ length: 310 }, (_, i) => `const x${i} = ${i};`).join("\n");
    fs.writeFileSync(tmpFile, content);
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("exempts *_test.py files even if >300 lines", () => {
    const tmpDir = os.tmpdir();
    const tmpFile = join(tmpDir, `module_${Date.now()}_test.py`);
    const content = Array.from({ length: 320 }, (_, i) => `x_${i} = ${i}`).join("\n");
    fs.writeFileSync(tmpFile, content);
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

// ---------------------------------------------------------------------------
// Special file exemptions
// ---------------------------------------------------------------------------

describe("file-size-guard — special file exemptions", () => {
  it("exempts __init__.py even if >300 lines", () => {
    const tmpDir = fs.mkdtempSync(join(os.tmpdir(), "masonry_init_test_"));
    const tmpFile = join(tmpDir, "__init__.py");
    const content = Array.from({ length: 310 }, (_, i) => `x_${i} = ${i}`).join("\n");
    fs.writeFileSync(tmpFile, content);
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
      fs.rmdirSync(tmpDir);
    }
  });

  it("exempts *.d.ts declaration files even if >300 lines", () => {
    const tmpDir = os.tmpdir();
    const tmpFile = join(tmpDir, `types_${Date.now()}.d.ts`);
    const content = Array.from({ length: 350 }, (_, i) => `export type T${i} = string;`).join("\n");
    fs.writeFileSync(tmpFile, content);
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

// ---------------------------------------------------------------------------
// Non-target file extensions — should be skipped
// ---------------------------------------------------------------------------

describe("file-size-guard — non-target extensions are skipped", () => {
  it("exits 0 silently for a .json file regardless of size", () => {
    const { exitCode, stderr } = runHook("Write", {
      file_path: "/some/path/config.json",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });

  it("exits 0 silently for a .md file", () => {
    const { exitCode, stderr } = runHook("Write", {
      file_path: "/some/path/README.md",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });

  it("exits 0 for Bash tool operations (non-Write/Edit)", () => {
    const { exitCode, stderr } = runHook("Bash", {
      command: "wc -l large_file.js",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });
});

// ---------------------------------------------------------------------------
// Shrinking edits on oversized files — should be allowed
// ---------------------------------------------------------------------------

describe("file-size-guard — shrinking edits on oversized files", () => {
  it("allows Edit that removes more lines than it adds on a 400-line file", () => {
    const tmpFile = makeTempFile(400, ".js");
    try {
      // old_string has 20 lines, new_string has 5 lines → net -15
      const oldStr = Array.from({ length: 20 }, (_, i) => `const x${i} = ${i};`).join("\n");
      const newStr = Array.from({ length: 5 }, (_, i) => `const y${i} = ${i};`).join("\n");
      const { exitCode, stderr } = runHook("Edit", {
        file_path: tmpFile,
        old_string: oldStr,
        new_string: newStr,
      });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("allows Edit that replaces same number of lines on a 400-line file", () => {
    const tmpFile = makeTempFile(400, ".py");
    try {
      const oldStr = Array.from({ length: 10 }, (_, i) => `x_${i} = ${i}`).join("\n");
      const newStr = Array.from({ length: 10 }, (_, i) => `y_${i} = ${i}`).join("\n");
      const { exitCode, stderr } = runHook("Edit", {
        file_path: tmpFile,
        old_string: oldStr,
        new_string: newStr,
      });
      expect(exitCode).toBe(0);
      expect(stderr).not.toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("still blocks Edit that adds lines to an already oversized file", () => {
    const tmpFile = makeTempFile(310, ".js");
    try {
      const oldStr = "const x0 = 0;";
      const newStr = Array.from({ length: 20 }, (_, i) => `const z${i} = ${i};`).join("\n");
      const { exitCode, stderr } = runHook("Edit", {
        file_path: tmpFile,
        old_string: oldStr,
        new_string: newStr,
      });
      expect(exitCode).toBe(2);
      expect(stderr).toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("still blocks Write (not Edit) on oversized files", () => {
    const tmpFile = makeTempFile(350, ".ts");
    try {
      const { exitCode, stderr } = runHook("Write", { file_path: tmpFile });
      expect(exitCode).toBe(2);
      expect(stderr).toContain("FILE_SIZE_BLOCK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });

  it("emits FILE_SIZE_SHRINK message for allowed shrinking edits", () => {
    const tmpFile = makeTempFile(400, ".js");
    try {
      const oldStr = Array.from({ length: 30 }, (_, i) => `const x${i} = ${i};`).join("\n");
      const newStr = Array.from({ length: 5 }, (_, i) => `const y${i} = ${i};`).join("\n");
      const { exitCode, stderr } = runHook("Edit", {
        file_path: tmpFile,
        old_string: oldStr,
        new_string: newStr,
      });
      expect(exitCode).toBe(0);
      expect(stderr).toContain("FILE_SIZE_SHRINK");
    } finally {
      fs.unlinkSync(tmpFile);
    }
  });
});

import { execFileSync, spawnSync } from "child_process";
import { join } from "path";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";
import os from "os";

const HOOK = join(process.cwd(), "src", "hooks", "masonry-dep-audit.js");

/**
 * Run the dep-audit hook with a synthetic tool payload.
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

// ---------------------------------------------------------------------------
// Non-dependency files — must be skipped silently
// ---------------------------------------------------------------------------

describe("dep-audit — non-dependency files are skipped", () => {
  it("exits 0 silently for a .js file", () => {
    const { exitCode, stderr } = runHook("Write", {
      file_path: "src/utils.js",
      content: "function add(a,b){return a+b;}",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });

  it("exits 0 silently for a Python .py file", () => {
    const { exitCode, stderr } = runHook("Write", {
      file_path: "app/main.py",
      content: "print('hello')",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });

  it("exits 0 silently for Bash tool operations", () => {
    const { exitCode, stderr } = runHook("Bash", {
      command: "cat package.json",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });

  it("exits 0 silently for a README.md file", () => {
    const { exitCode, stderr } = runHook("Edit", {
      file_path: "README.md",
      old_string: "old",
      new_string: "new",
    });
    expect(exitCode).toBe(0);
    expect(stderr).toBe("");
  });
});

// ---------------------------------------------------------------------------
// npm not found — graceful skip message
// ---------------------------------------------------------------------------

describe("dep-audit — npm tool unavailable", () => {
  it("outputs DEP_AUDIT_SKIP when npm is not found on PATH", () => {
    // We simulate npm-not-found by running the hook in an env with empty PATH.
    // Use process.execPath (absolute node binary) so node itself is still found.
    const result = spawnSync(process.execPath, [HOOK], {
      input: JSON.stringify({
        tool_name: "Write",
        tool_input: { file_path: "package.json", content: "{}" },
      }),
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      env: { ...process.env, PATH: "/nonexistent_path_xyz" },
    });
    // Should always exit 0 (never block)
    expect(result.status).toBe(0);
    // Should emit the skip message (or succeed silently if npm is absent and hook exits early)
    // The hook emits DEP_AUDIT_SKIP when commandExists returns false
    expect(result.stderr).toContain("DEP_AUDIT_SKIP");
  });
});

// ---------------------------------------------------------------------------
// pip-audit not found — graceful skip message
// ---------------------------------------------------------------------------

describe("dep-audit — pip-audit tool unavailable", () => {
  it("outputs DEP_AUDIT_SKIP when pip-audit is not found on PATH", () => {
    // Use process.execPath (absolute node binary) so node itself is still found.
    const result = spawnSync(process.execPath, [HOOK], {
      input: JSON.stringify({
        tool_name: "Write",
        tool_input: { file_path: "requirements.txt", content: "flask==2.0.0\n" },
      }),
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      env: { ...process.env, PATH: "/nonexistent_path_xyz" },
    });
    expect(result.status).toBe(0);
    expect(result.stderr).toContain("DEP_AUDIT_SKIP");
  });
});

// ---------------------------------------------------------------------------
// Output format and exit code contract
// ---------------------------------------------------------------------------

describe("dep-audit — always exits 0 (never blocks)", () => {
  it("exits 0 for package.json regardless of audit outcome", () => {
    const { exitCode } = runHook("Write", {
      file_path: "package.json",
      content: "{}",
    });
    // Hook MUST never block — always exit 0
    expect(exitCode).toBe(0);
  });

  it("exits 0 for requirements.txt regardless of audit outcome", () => {
    const { exitCode } = runHook("Write", {
      file_path: "requirements.txt",
      content: "flask==1.0.0\n",
    });
    expect(exitCode).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// DEPENDENCY_WARNING output format validation
// ---------------------------------------------------------------------------

describe("dep-audit — output format when vulnerabilities are mocked", () => {
  it("DEPENDENCY_WARNING message contains severity and file name", () => {
    // Create a tiny helper script that wraps the hook and injects mock audit results
    // We test the warning format by spawning a wrapper that substitutes the audit functions.
    const tmpDir = os.tmpdir();
    const wrapperPath = join(tmpDir, "dep_audit_wrapper_test.js");

    // Write a wrapper that replaces execFileSync to return mock vulnerable audit data
    const wrapperContent = `
const Module = require('module');
const origLoad = Module._load;
Module._load = function(request, ...args) {
  if (request === 'child_process') {
    return {
      execFileSync: (cmd, cmdArgs, opts) => {
        if (cmd === 'npm' && cmdArgs.includes('--version')) return Buffer.from('9.0.0');
        if (cmd === 'npm' && cmdArgs.includes('--json')) {
          // Return audit data with 2 HIGH, 1 CRITICAL
          const mockResult = {
            metadata: { vulnerabilities: { high: 2, critical: 1 } }
          };
          // npm audit exits non-zero when vulns found, so throw
          const err = new Error('audit');
          err.status = 1;
          err.stdout = Buffer.from(JSON.stringify(mockResult));
          throw err;
        }
        return Buffer.from('');
      }
    };
  }
  return origLoad.call(this, request, ...args);
};

// Now load the actual hook but redirect stdin manually
const hookCode = require('fs').readFileSync(${JSON.stringify(HOOK)}, 'utf8');
// Provide mock stdin
process.stdin.destroy();
const { Readable } = require('stream');
const mockStdin = new Readable({ read() {} });
mockStdin.push(JSON.stringify({
  tool_name: 'Write',
  tool_input: { file_path: 'package.json', content: '{}' }
}));
mockStdin.push(null);
Object.defineProperty(process, 'stdin', { value: mockStdin });
eval(hookCode);
`;

    fs.writeFileSync(wrapperPath, wrapperContent);
    const result = spawnSync("node", [wrapperPath], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 5000,
    });
    fs.unlinkSync(wrapperPath);

    expect(result.status).toBe(0);
    expect(result.stderr).toContain("DEPENDENCY_WARNING");
    expect(result.stderr).toContain("package.json");
  });

  it("DEPENDENCY_WARNING for requirements.txt contains file name", () => {
    const tmpDir = os.tmpdir();
    const wrapperPath = join(tmpDir, "pip_audit_wrapper_test.js");

    const wrapperContent = `
const Module = require('module');
const origLoad = Module._load;
Module._load = function(request, ...args) {
  if (request === 'child_process') {
    return {
      execFileSync: (cmd, cmdArgs, opts) => {
        if (cmd === 'pip-audit' && cmdArgs.includes('--version')) return Buffer.from('2.0.0');
        if (cmd === 'pip-audit') {
          // Mock vulnerable pip-audit output
          const mockResult = [
            { name: 'flask', version: '1.0.0', vulns: [{ id: 'PYSEC-1', severity: 'HIGH', fix_versions: ['2.0'] }] },
            { name: 'requests', version: '2.0.0', vulns: [{ id: 'PYSEC-2', severity: 'CRITICAL', fix_versions: ['3.0'] }] }
          ];
          const err = new Error('audit');
          err.status = 1;
          err.stdout = Buffer.from(JSON.stringify(mockResult));
          throw err;
        }
        return Buffer.from('');
      }
    };
  }
  return origLoad.call(this, request, ...args);
};

const hookCode = require('fs').readFileSync(${JSON.stringify(HOOK)}, 'utf8');
process.stdin.destroy();
const { Readable } = require('stream');
const mockStdin = new Readable({ read() {} });
mockStdin.push(JSON.stringify({
  tool_name: 'Write',
  tool_input: { file_path: 'requirements.txt', content: 'flask==1.0.0' }
}));
mockStdin.push(null);
Object.defineProperty(process, 'stdin', { value: mockStdin });
eval(hookCode);
`;

    fs.writeFileSync(wrapperPath, wrapperContent);
    const result = spawnSync("node", [wrapperPath], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 5000,
    });
    fs.unlinkSync(wrapperPath);

    expect(result.status).toBe(0);
    expect(result.stderr).toContain("DEPENDENCY_WARNING");
    expect(result.stderr).toContain("requirements.txt");
  });
});

// ---------------------------------------------------------------------------
// HIGH/CRITICAL counting — parsePipAuditOutput unit test via wrapper
// ---------------------------------------------------------------------------

describe("dep-audit — pip-audit severity counting", () => {
  it("counts HIGH and CRITICAL vulnerabilities separately", () => {
    const tmpDir = os.tmpdir();
    const wrapperPath = join(tmpDir, "pip_count_test.js");

    const wrapperContent = `
const Module = require('module');
const origLoad = Module._load;
Module._load = function(request, ...args) {
  if (request === 'child_process') {
    return {
      execFileSync: (cmd, cmdArgs, opts) => {
        if (cmd === 'pip-audit' && cmdArgs.includes('--version')) return Buffer.from('2.0.0');
        if (cmd === 'pip-audit') {
          const mockResult = [
            { name: 'pkg1', version: '1.0', vulns: [
              { id: 'A', severity: 'HIGH' },
              { id: 'B', severity: 'HIGH' },
              { id: 'C', severity: 'CRITICAL' }
            ]}
          ];
          const err = new Error('vuln');
          err.status = 1;
          err.stdout = Buffer.from(JSON.stringify(mockResult));
          throw err;
        }
        return Buffer.from('');
      }
    };
  }
  return origLoad.call(this, request, ...args);
};

const hookCode = require('fs').readFileSync(${JSON.stringify(HOOK)}, 'utf8');
process.stdin.destroy();
const { Readable } = require('stream');
const mockStdin = new Readable({ read() {} });
mockStdin.push(JSON.stringify({
  tool_name: 'Write',
  tool_input: { file_path: 'requirements.txt', content: 'pkg==1.0' }
}));
mockStdin.push(null);
Object.defineProperty(process, 'stdin', { value: mockStdin });
eval(hookCode);
`;

    fs.writeFileSync(wrapperPath, wrapperContent);
    const result = spawnSync("node", [wrapperPath], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 5000,
    });
    fs.unlinkSync(wrapperPath);

    expect(result.status).toBe(0);
    // Should see both HIGH and CRITICAL warnings
    expect(result.stderr).toContain("HIGH");
    expect(result.stderr).toContain("CRITICAL");
  });

  it("exits 0 silently when pip-audit reports zero vulnerabilities", () => {
    const tmpDir = os.tmpdir();
    const wrapperPath = join(tmpDir, "pip_clean_test.js");

    const wrapperContent = `
const Module = require('module');
const origLoad = Module._load;
Module._load = function(request, ...args) {
  if (request === 'child_process') {
    return {
      execFileSync: (cmd, cmdArgs, opts) => {
        if (cmd === 'pip-audit' && cmdArgs.includes('--version')) return Buffer.from('2.0.0');
        if (cmd === 'pip-audit') {
          // Clean: no vulns
          return Buffer.from(JSON.stringify([]));
        }
        return Buffer.from('');
      }
    };
  }
  return origLoad.call(this, request, ...args);
};

const hookCode = require('fs').readFileSync(${JSON.stringify(HOOK)}, 'utf8');
process.stdin.destroy();
const { Readable } = require('stream');
const mockStdin = new Readable({ read() {} });
mockStdin.push(JSON.stringify({
  tool_name: 'Write',
  tool_input: { file_path: 'requirements.txt', content: 'flask==3.0.0' }
}));
mockStdin.push(null);
Object.defineProperty(process, 'stdin', { value: mockStdin });
eval(hookCode);
`;

    fs.writeFileSync(wrapperPath, wrapperContent);
    const result = spawnSync("node", [wrapperPath], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 5000,
    });
    fs.unlinkSync(wrapperPath);

    expect(result.status).toBe(0);
    expect(result.stderr).not.toContain("DEPENDENCY_WARNING");
  });
});

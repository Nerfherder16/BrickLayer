#!/usr/bin/env node
/**
 * Masonry Daemon Worker: optimize
 *
 * Runs linter + typecheck in the background. Writes findings to .autopilot/quality.md.
 * Never blocks Claude — runs async, results available next time Claude checks.
 *
 * Interval: 30 minutes (managed by daemon-manager.sh)
 */

"use strict";
const fs = require("fs");
const path = require("path");
const { execSync, spawnSync } = require("child_process");

function findProjectRoot() {
  try {
    return execSync("git rev-parse --show-toplevel", { encoding: "utf8", timeout: 3000 }).trim();
  } catch {
    return process.cwd();
  }
}

function runCommand(cmd, cwd, timeout = 30000) {
  try {
    const result = spawnSync("bash", ["-c", cmd], {
      cwd,
      encoding: "utf8",
      timeout,
      env: { ...process.env, FORCE_COLOR: "0" },
    });
    return {
      ok: result.status === 0,
      stdout: (result.stdout || "").trim(),
      stderr: (result.stderr || "").trim(),
      status: result.status,
      timedOut: result.signal === "SIGTERM",
    };
  } catch (err) {
    return { ok: false, stdout: "", stderr: err.message, status: -1, timedOut: false };
  }
}

function detectProject(root) {
  const hasPyproject = fs.existsSync(path.join(root, "pyproject.toml"));
  const hasRequirements = fs.existsSync(path.join(root, "requirements.txt"));
  const hasPackageJson = fs.existsSync(path.join(root, "package.json"));
  const hasTsConfig = fs.existsSync(path.join(root, "tsconfig.json"));

  return {
    python: hasPyproject || hasRequirements,
    typescript: hasPackageJson && hasTsConfig,
    javascript: hasPackageJson && !hasTsConfig,
  };
}

function parseRuffOutput(stdout) {
  if (!stdout) return [];
  return stdout.split("\n")
    .filter(l => l.includes(".py:"))
    .map(l => l.trim())
    .filter(Boolean)
    .slice(0, 50);
}

function parsePyrightOutput(stdout) {
  if (!stdout) return [];
  const errors = stdout.split("\n")
    .filter(l => l.includes("error:") || l.includes("warning:"))
    .map(l => l.trim())
    .filter(Boolean)
    .slice(0, 50);
  const summary = stdout.split("\n").find(l => l.includes("errors,") || l.includes("error reported")) || "";
  return { errors, summary };
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  const project = detectProject(root);

  console.log(`[optimize] Running quality checks in ${root} at ${timestamp}`);

  const results = {
    timestamp,
    python_lint: null,
    python_typecheck: null,
    typescript_lint: null,
    typescript_typecheck: null,
    overall: "UNKNOWN",
  };

  let issues = 0;

  // --- Python checks ---
  if (project.python) {
    // ruff lint
    const ruffResult = runCommand("ruff check . --output-format=concise 2>&1 | head -60", root, 30000);
    results.python_lint = {
      tool: "ruff",
      ok: ruffResult.ok,
      issues: parseRuffOutput(ruffResult.stdout + ruffResult.stderr),
    };
    if (!ruffResult.ok) issues += results.python_lint.issues.length;

    // pyright typecheck
    const pyrightResult = runCommand("pyright --outputjson 2>/dev/null || pyright 2>&1 | tail -20", root, 60000);
    const pyrightParsed = parsePyrightOutput(pyrightResult.stdout + pyrightResult.stderr);
    results.python_typecheck = {
      tool: "pyright",
      ok: pyrightResult.ok,
      errors: pyrightParsed.errors || [],
      summary: pyrightParsed.summary || "",
    };
    if (!pyrightResult.ok) issues += (pyrightParsed.errors || []).length;
  }

  // --- TypeScript/JavaScript checks ---
  if (project.typescript || project.javascript) {
    // eslint
    const eslintResult = runCommand("npx --no-install eslint . --ext .ts,.tsx,.js,.jsx --max-warnings 0 --format compact 2>&1 | head -60", root, 45000);
    results.typescript_lint = {
      tool: "eslint",
      ok: eslintResult.ok,
      issues: eslintResult.stdout.split("\n").filter(l => l.includes(":")).map(l => l.trim()).filter(Boolean).slice(0, 50),
    };
    if (!eslintResult.ok) issues += results.typescript_lint.issues.length;

    // tsc typecheck (only for TypeScript)
    if (project.typescript) {
      const tscResult = runCommand("npx --no-install tsc --noEmit 2>&1 | head -60", root, 60000);
      results.typescript_typecheck = {
        tool: "tsc",
        ok: tscResult.ok,
        errors: tscResult.stdout.split("\n").filter(l => l.includes("error TS")).map(l => l.trim()).filter(Boolean).slice(0, 50),
      };
      if (!tscResult.ok) issues += results.typescript_typecheck.errors.length;
    }
  }

  results.overall = issues === 0 ? "CLEAN" : `${issues} issues`;

  // --- Write output ---
  const lines = [
    `# Quality Report`,
    ``,
    `Generated: ${timestamp}`,
    `Project: ${path.basename(root)}`,
    `Overall: **${results.overall}**`,
    ``,
  ];

  if (project.python) {
    lines.push("## Python");
    lines.push("");

    const lint = results.python_lint;
    lines.push(`### Ruff Lint — ${lint.ok ? "✓ CLEAN" : `✗ ${lint.issues.length} issues`}`);
    if (lint.issues.length > 0) {
      lines.push("```");
      lines.push(...lint.issues.slice(0, 20));
      if (lint.issues.length > 20) lines.push(`... and ${lint.issues.length - 20} more`);
      lines.push("```");
    }
    lines.push("");

    const tc = results.python_typecheck;
    lines.push(`### Pyright Typecheck — ${tc.ok ? "✓ CLEAN" : `✗ ${tc.errors.length} errors`}`);
    if (tc.summary) lines.push(`> ${tc.summary}`);
    if (tc.errors.length > 0) {
      lines.push("```");
      lines.push(...tc.errors.slice(0, 20));
      if (tc.errors.length > 20) lines.push(`... and ${tc.errors.length - 20} more`);
      lines.push("```");
    }
    lines.push("");
  }

  if (project.typescript || project.javascript) {
    lines.push("## TypeScript/JavaScript");
    lines.push("");

    if (results.typescript_lint) {
      const lint = results.typescript_lint;
      lines.push(`### ESLint — ${lint.ok ? "✓ CLEAN" : `✗ ${lint.issues.length} issues`}`);
      if (lint.issues.length > 0) {
        lines.push("```");
        lines.push(...lint.issues.slice(0, 20));
        if (lint.issues.length > 20) lines.push(`... and ${lint.issues.length - 20} more`);
        lines.push("```");
      }
      lines.push("");
    }

    if (results.typescript_typecheck) {
      const tc = results.typescript_typecheck;
      lines.push(`### TypeScript — ${tc.ok ? "✓ CLEAN" : `✗ ${tc.errors.length} errors`}`);
      if (tc.errors.length > 0) {
        lines.push("```");
        lines.push(...tc.errors.slice(0, 20));
        if (tc.errors.length > 20) lines.push(`... and ${tc.errors.length - 20} more`);
        lines.push("```");
      }
      lines.push("");
    }
  }

  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch { /* exists */ }

  fs.writeFileSync(path.join(autopilotDir, "quality.md"), lines.join("\n"), "utf8");
  console.log(`[optimize] Done — ${results.overall}, wrote .autopilot/quality.md`);
}

main().catch(err => {
  console.error("[optimize] Error:", err.message);
  process.exit(0);
});

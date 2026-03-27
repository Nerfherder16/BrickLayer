#!/usr/bin/env node
/**
 * Masonry Daemon Worker: testgaps
 *
 * Scans the project for source files that lack corresponding test files.
 * Writes findings to .autopilot/testgaps.md.
 *
 * Interval: 30 minutes (managed by daemon-manager.sh)
 */

"use strict";
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function findProjectRoot() {
  try {
    return execSync("git rev-parse --show-toplevel", { encoding: "utf8", timeout: 3000 }).trim();
  } catch {
    return process.cwd();
  }
}

function walkDir(dir, extensions, ignorePatterns) {
  const results = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relPath = fullPath.replace(dir + path.sep, "");

      // Skip ignored patterns
      if (ignorePatterns.some(p => fullPath.includes(p))) continue;

      if (entry.isDirectory()) {
        results.push(...walkDir(fullPath, extensions, ignorePatterns));
      } else if (extensions.includes(path.extname(entry.name).toLowerCase())) {
        results.push(fullPath);
      }
    }
  } catch { /* unreadable dir */ }
  return results;
}

function findTestFile(srcFile, allFiles, root) {
  const ext = path.extname(srcFile);
  const baseName = path.basename(srcFile, ext);
  const dir = path.dirname(srcFile);
  const relDir = path.relative(root, dir);

  // Python patterns
  if (ext === ".py") {
    const testPatterns = [
      path.join(root, "tests", relDir, `test_${baseName}.py`),
      path.join(root, "tests", `test_${baseName}.py`),
      path.join(dir, `test_${baseName}.py`),
      path.join(root, "tests", relDir.replace("src/", ""), `test_${baseName}.py`),
    ];
    return testPatterns.some(p => allFiles.includes(p));
  }

  // TypeScript/JavaScript patterns
  if ([".ts", ".tsx", ".js", ".jsx"].includes(ext)) {
    const testPatterns = [
      // Same directory __tests__
      path.join(dir, "__tests__", `${baseName}.test${ext}`),
      path.join(dir, "__tests__", `${baseName}.spec${ext}`),
      // Root __tests__
      path.join(root, "src", "__tests__", `${baseName}.test${ext}`),
      // Separate tests dir
      path.join(root, "tests", `${baseName}.test${ext}`),
      path.join(root, "tests", relDir.replace("src/", ""), `${baseName}.test${ext}`),
    ];
    return testPatterns.some(p => allFiles.includes(p));
  }

  return false;
}

function isTestFile(filePath) {
  const base = path.basename(filePath);
  return base.startsWith("test_") ||
    base.endsWith(".test.ts") ||
    base.endsWith(".test.tsx") ||
    base.endsWith(".test.js") ||
    base.endsWith(".spec.ts") ||
    base.endsWith(".spec.js") ||
    filePath.includes("__tests__") ||
    filePath.includes("/tests/");
}

function isExempt(filePath) {
  const exempt = [
    "__init__.py", "conftest.py", "setup.py", "manage.py",
    "settings.py", "config.py", "constants.py",
    "tailwind.config", "vite.config", "vitest.config",
    "tsconfig", ".d.ts", "index.ts",
  ];
  const base = path.basename(filePath);
  return exempt.some(e => base.startsWith(e) || base.endsWith(e));
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();

  const IGNORE = [
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "coverage", ".autopilot", ".ui", ".mas",
    "masonry/src", "migrations", "alembic",
  ];

  const SOURCE_EXTS = [".py", ".ts", ".tsx", ".js"];

  console.log(`[testgaps] Scanning ${root} at ${timestamp}`);

  const allFiles = walkDir(root, [...SOURCE_EXTS, ".py"], IGNORE);
  const testFiles = new Set(allFiles.filter(isTestFile));
  const sourceFiles = allFiles.filter(f => !isTestFile(f) && !isExempt(f));

  const gaps = [];
  for (const src of sourceFiles) {
    const relSrc = path.relative(root, src);
    if (!findTestFile(src, [...allFiles], root)) {
      gaps.push(relSrc);
    }
  }

  const output = [
    `# Test Gap Report`,
    ``,
    `Generated: ${timestamp}`,
    `Project: ${path.basename(root)}`,
    ``,
    `## Summary`,
    ``,
    `- Source files scanned: ${sourceFiles.length}`,
    `- Test files found: ${testFiles.size}`,
    `- Files missing tests: ${gaps.length}`,
    `- Coverage: ${sourceFiles.length > 0 ? Math.round((1 - gaps.length / sourceFiles.length) * 100) : 0}%`,
    ``,
    `## Files Without Tests`,
    ``,
  ];

  if (gaps.length === 0) {
    output.push("All source files have corresponding test files. ✓");
  } else {
    // Group by directory
    const byDir = {};
    for (const gap of gaps) {
      const dir = path.dirname(gap);
      if (!byDir[dir]) byDir[dir] = [];
      byDir[dir].push(path.basename(gap));
    }

    for (const [dir, files] of Object.entries(byDir).sort()) {
      output.push(`### ${dir}/`);
      for (const f of files.sort()) {
        output.push(`- [ ] \`${f}\``);
      }
      output.push("");
    }
  }

  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch { /* exists */ }

  fs.writeFileSync(path.join(autopilotDir, "testgaps.md"), output.join("\n"), "utf8");
  console.log(`[testgaps] Done — ${gaps.length} gaps found, wrote .autopilot/testgaps.md`);
}

main().catch(err => {
  console.error("[testgaps] Error:", err.message);
  process.exit(0); // Never crash the daemon loop
});

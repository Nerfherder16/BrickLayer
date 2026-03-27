#!/usr/bin/env node
/**
 * Masonry Daemon Worker: map
 *
 * Generates a codebase structure snapshot at .autopilot/map.md.
 * Used by masonry-session-start.js to inject targeted context without
 * requiring Claude to re-discover the project structure each session.
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
      if (ignorePatterns.some(p => fullPath.includes(p))) continue;
      if (entry.isDirectory()) {
        results.push(...walkDir(fullPath, extensions, ignorePatterns));
      } else if (extensions.includes(path.extname(entry.name).toLowerCase())) {
        results.push(fullPath);
      }
    }
  } catch { /* unreadable */ }
  return results;
}

function isTestFile(filePath) {
  return path.basename(filePath).startsWith("test_") ||
    /\.(test|spec)\.(ts|tsx|js|jsx)$/.test(filePath) ||
    filePath.includes("__tests__") ||
    filePath.includes("/tests/");
}

function getCurrentBranch(cwd) {
  try {
    return execSync("git branch --show-current", { encoding: "utf8", timeout: 3000, cwd }).trim() || "unknown";
  } catch { return "unknown"; }
}

function getRecentCommits(cwd, n = 5) {
  try {
    return execSync(`git log --oneline -${n}`, { encoding: "utf8", timeout: 3000, cwd })
      .trim().split("\n").filter(Boolean);
  } catch { return []; }
}

function detectStack(files, root) {
  const counts = {};
  const exts = [".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".cs", ".kt"];
  for (const f of files) {
    const ext = path.extname(f).toLowerCase();
    if (exts.includes(ext)) counts[ext] = (counts[ext] || 0) + 1;
  }

  // Languages with counts
  const langs = [];
  if (counts[".py"]) langs.push(`Python (${counts[".py"]} files)`);
  if (counts[".ts"] || counts[".tsx"]) langs.push(`TypeScript (${(counts[".ts"] || 0) + (counts[".tsx"] || 0)} files)`);
  if (counts[".js"] || counts[".jsx"]) langs.push(`JavaScript (${(counts[".js"] || 0) + (counts[".jsx"] || 0)} files)`);
  if (counts[".rs"]) langs.push(`Rust (${counts[".rs"]} files)`);
  if (counts[".go"]) langs.push(`Go (${counts[".go"]} files)`);
  if (counts[".cs"]) langs.push(`C# (${counts[".cs"]} files)`);
  if (counts[".kt"]) langs.push(`Kotlin (${counts[".kt"]} files)`);

  // Frameworks from path signals
  const filePaths = files.join("/");
  const frameworks = [];
  if (/\/routers?\//.test(filePaths) && counts[".py"]) frameworks.push("FastAPI");
  if (/manage\.py/.test(filePaths)) frameworks.push("Django");
  if (counts[".tsx"] || /\/components?\//i.test(filePaths)) {
    if (fs.existsSync(path.join(root, "next.config.js")) || fs.existsSync(path.join(root, "next.config.ts"))) {
      frameworks.push("Next.js");
    } else {
      frameworks.push("React");
    }
  }
  if (/\/routes?\//i.test(filePaths) && !counts[".py"]) frameworks.push("Express");
  if (frameworks.length === 0 && langs.length > 0) frameworks.push("unknown");

  // Test runner
  let testRunner = "not detected";
  if (fs.existsSync(path.join(root, "vitest.config.ts")) || fs.existsSync(path.join(root, "vitest.config.js"))) {
    testRunner = "vitest";
  } else if (fs.existsSync(path.join(root, "jest.config.js")) || fs.existsSync(path.join(root, "jest.config.ts"))) {
    testRunner = "jest";
  } else if (fs.existsSync(path.join(root, "pytest.ini")) || fs.existsSync(path.join(root, "pyproject.toml"))) {
    testRunner = "pytest";
  } else if (fs.existsSync(path.join(root, "tests", "conftest.py"))) {
    testRunner = "pytest";
  }

  // Build tool
  let buildTool = "not detected";
  if (fs.existsSync(path.join(root, "vite.config.ts")) || fs.existsSync(path.join(root, "vite.config.js"))) {
    buildTool = "Vite";
  } else if (fs.existsSync(path.join(root, "webpack.config.js"))) {
    buildTool = "Webpack";
  } else if (fs.existsSync(path.join(root, "next.config.js")) || fs.existsSync(path.join(root, "next.config.ts"))) {
    buildTool = "Next.js";
  }

  return { langs, frameworks, testRunner, buildTool };
}

function detectEntryPoints(root) {
  const candidates = [
    "app/main.py", "main.py", "app.py", "manage.py",
    "src/main.tsx", "src/App.tsx", "src/index.ts", "src/main.ts",
    "index.ts", "server.ts", "src/server.ts", "index.js", "server.js",
  ];
  return candidates.filter(p => fs.existsSync(path.join(root, p)));
}

function getKeyDirs(files, root) {
  const counts = {};
  for (const f of files) {
    const rel = path.relative(root, f);
    const parts = rel.split(path.sep);
    if (parts.length >= 2) {
      const dir = parts.slice(0, 2).join("/");
      counts[dir] = (counts[dir] || 0) + 1;
    }
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  console.log(`[map] Mapping ${root} at ${timestamp}`);

  const IGNORE = [
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "coverage", ".autopilot", ".ui", ".mas",
    "masonry/src", "migrations", "alembic",
  ];

  const SOURCE_EXTS = [".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".cs", ".kt"];

  const files = walkDir(root, SOURCE_EXTS, IGNORE);
  console.log(`[map] Found ${files.length} source files`);

  const stack = detectStack(files, root);
  const entryPoints = detectEntryPoints(root);
  const keyDirs = getKeyDirs(files, root);
  const branch = getCurrentBranch(root);
  const recentCommits = getRecentCommits(root);

  const sourceFiles = files.filter(f => !isTestFile(f));
  const testFiles = files.filter(f => isTestFile(f));
  const roughPct = sourceFiles.length > 0
    ? Math.round(Math.min(testFiles.length / sourceFiles.length, 1) * 100)
    : 0;

  const output = [
    `# Codebase Map`,
    ``,
    `Generated: ${timestamp}`,
    `Project: ${path.basename(root)}`,
    `Branch: ${branch}`,
    ``,
    `## Stack Detection`,
    ``,
    `- Languages: ${stack.langs.join(", ") || "none detected"}`,
    `- Frameworks: ${stack.frameworks.join(", ")}`,
    `- Test runner: ${stack.testRunner}`,
    `- Build tool: ${stack.buildTool}`,
    ``,
    `## Entry Points`,
    ``,
  ];

  if (entryPoints.length === 0) {
    output.push("None detected");
  } else {
    for (const ep of entryPoints) output.push(`- \`${ep}\``);
  }

  output.push("", "## Key Directories", "");
  output.push("| Directory | File Count |");
  output.push("|-----------|-----------|");
  for (const [dir, count] of keyDirs) {
    output.push(`| \`${dir}/\` | ${count} |`);
  }

  output.push("", "## Test Coverage Snapshot", "");
  output.push(`- Source files: ${sourceFiles.length}`);
  output.push(`- Test files: ${testFiles.length}`);
  output.push(`- Rough coverage: ${roughPct}%`);

  output.push("", "## Recent Activity", "");
  if (recentCommits.length === 0) {
    output.push("No commits found");
  } else {
    for (const commit of recentCommits) output.push(`- ${commit}`);
  }

  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch { /* exists */ }

  fs.writeFileSync(path.join(autopilotDir, "map.md"), output.join("\n"), "utf8");
  console.log(`[map] Done — wrote .autopilot/map.md (${files.length} files, ${stack.langs.length} langs, ${stack.frameworks.join("/")} frameworks)`);
}

main().catch(err => {
  console.error("[map] Error:", err.message);
  process.exit(0);
});

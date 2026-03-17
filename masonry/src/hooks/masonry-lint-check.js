#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Auto-lint after Write/Edit.
 * Skips in build/fix mode (agents handle linting).
 * Exit code 2 blocks on lint errors.
 *
 * NOTE: tsc --noEmit removed — full project typecheck per edit
 * caused VS Code crashes (especially in Tauri/large TS projects).
 * Use /verify or manual tsc for type checking.
 */

const { execSync } = require("child_process");
const { existsSync, readFileSync } = require("fs");
const path = require("path");

// Dirs/patterns to skip entirely
const SKIP_PATTERNS = [
  "/node_modules/",
  "/dist/",
  "/build/",
  "/.next/",
  "/__pycache__/",
  "/static/dashboard/",
  "/.autopilot/",
  "/.ui/",
  "/src-tauri/target/",
  "/masonry/",
];

function findRuff() {
  try {
    execSync("ruff --version", { stdio: "pipe", timeout: 3000 });
    return "ruff";
  } catch {}

  if (process.platform === "win32") {
    const localAppData = process.env.LOCALAPPDATA || "";
    const appData = process.env.APPDATA || "";
    const candidates = [];
    for (const ver of ["Python311", "Python312", "Python313", "Python314"]) {
      candidates.push(path.join(localAppData, "Programs", "Python", ver, "Scripts", "ruff.exe"));
    }
    candidates.push(path.join(appData, "Python", "Scripts", "ruff.exe"));
    // pip install --user location
    candidates.push(path.join(localAppData, "Python", "pythoncore-3.14-64", "Scripts", "ruff.exe"));
    for (const p of candidates) {
      try {
        execSync(`"${p}" --version`, { stdio: "pipe", timeout: 3000 });
        return p;
      } catch {}
    }
  } else {
    const home = process.env.HOME || "";
    for (const p of [
      path.join(home, ".local", "bin", "ruff"),
      path.join(home, ".cargo", "bin", "ruff"),
      "/usr/local/bin/ruff",
    ]) {
      try {
        execSync(`"${p}" --version`, { stdio: "pipe", timeout: 3000 });
        return p;
      } catch {}
    }
  }
  return null;
}

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 3000);
  });
}

function getAutopilotMode(filePath) {
  let dir = path.dirname(filePath);
  for (let i = 0; i < 10; i++) {
    const modeFile = path.join(dir, ".autopilot", "mode");
    if (existsSync(modeFile)) {
      try { return readFileSync(modeFile, "utf8").trim(); } catch { return ""; }
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return "";
}

function normalizeWindowsPath(filePath) {
  // Convert Git Bash /c/Users/... paths to C:\Users\... on Windows
  if (process.platform === "win32" && /^\/[a-zA-Z]\//.test(filePath)) {
    return filePath[1].toUpperCase() + ":" + filePath.slice(2).replace(/\//g, "\\");
  }
  return filePath;
}

function findProjectRoot(filePath) {
  let dir = path.dirname(normalizeWindowsPath(filePath));
  for (let i = 0; i < 10; i++) {
    if (existsSync(path.join(dir, "package.json")) || existsSync(path.join(dir, "pyproject.toml"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return path.dirname(normalizeWindowsPath(filePath));
}

function run(cmd, opts = {}) {
  try {
    execSync(cmd, { stdio: ["pipe", "pipe", "pipe"], timeout: 10000, ...opts });
    return { ok: true, output: "" };
  } catch (e) {
    return { ok: false, output: (e.stderr?.toString() || "") + (e.stdout?.toString() || "") };
  }
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  const filePath = parsed.tool_input?.file_path || parsed.tool_input?.path || "";
  if (!filePath) process.exit(0);

  // On Windows, bash-style /c/Users/... paths must be converted to C:\Users\...
  // before passing to ruff/eslint — the existing normalizeWindowsPath() handles this.
  const winPath = normalizeWindowsPath(filePath);
  const normalized = filePath.replace(/\\/g, "/");

  // In build/fix mode, agents handle linting
  const mode = getAutopilotMode(filePath);
  if (mode === "build" || mode === "fix") process.exit(0);

  // Skip hooks, build output, node_modules, static assets
  if (normalized.includes("/hooks/")) process.exit(0);
  if (SKIP_PATTERNS.some((p) => normalized.includes(p))) process.exit(0);

  const projectRoot = findProjectRoot(filePath);
  const cwdOpts = { cwd: projectRoot };

  if (filePath.endsWith(".py")) {
    const ruff = findRuff();
    if (!ruff) process.exit(0);
    run(`"${ruff}" check --fix "${winPath}"`, cwdOpts);
    run(`"${ruff}" format "${winPath}"`, cwdOpts);
    const check = run(`"${ruff}" check "${winPath}"`, cwdOpts);
    if (!check.ok) {
      process.stderr.write(`Lint errors in ${filePath}:\n${check.output}\n`);
      process.exit(2);
    }
  } else if (/\.(ts|tsx|js|jsx)$/.test(filePath)) {
    // Prettier only
    run(`npx prettier --write "${filePath}"`, cwdOpts);

    // ESLint only if config exists nearby
    let hasEslintConfig = false;
    let dir = path.dirname(filePath);
    for (let i = 0; i < 5; i++) {
      if (
        existsSync(path.join(dir, "eslint.config.js")) ||
        existsSync(path.join(dir, "eslint.config.mjs")) ||
        existsSync(path.join(dir, ".eslintrc.json")) ||
        existsSync(path.join(dir, ".eslintrc.js"))
      ) {
        hasEslintConfig = true;
        break;
      }
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }

    if (hasEslintConfig) {
      const eslint = run(`npx eslint --fix "${winPath}"`, cwdOpts);
      if (!eslint.ok && !eslint.output.includes("eslint.config")) {
        const recheck = run(`npx eslint "${winPath}"`, cwdOpts);
        if (!recheck.ok && !recheck.output.includes("eslint.config")) {
          process.stderr.write(`Lint errors in ${filePath}:\n${recheck.output}\n`);
          process.exit(2);
        }
      }
    }

    // tsc --noEmit intentionally removed.
    // Full project typecheck on every file edit caused VS Code crashes,
    // especially in Tauri + React projects. Use /verify for type checking.
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

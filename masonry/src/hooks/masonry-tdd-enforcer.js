#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Warn when editing implementation files without corresponding tests.
 *
 * Behavior:
 * - In /build mode (`.autopilot/mode` === "build"): exit 2 (blocks) if test file missing
 * - Otherwise: stderr warning only
 *
 * Skips files that are exempt from TDD (configs, types, migrations, etc.)
 */

const { existsSync, readFileSync } = require("fs");
const path = require("path");
const { readStdin } = require('./session/stop-utils');

const EXEMPT_PATTERNS = [
  /\.config\.(ts|js|mjs|cjs)$/,
  /tsconfig.*\.json$/,
  /\.d\.ts$/,
  /__init__\.py$/,
  /migrations?\//,
  /\.env/,
  /\.md$/,
  /\.json$/,
  /\.yaml$/,
  /\.yml$/,
  /\.toml$/,
  /\.css$/,
  /\.svg$/,
  /\.png$/,
  /\.ico$/,
  /conftest\.py$/,
  /setup\.(py|cfg)$/,
  /pyproject\.toml$/,
  /vite\.config/,
  /tailwind\.config/,
  /postcss\.config/,
  // Electron preload scripts — IPC bridge wiring, not independently unit-testable
  /[/\\]preload[/\\]/,
  // Renderer entry points — wiring only
  /[/\\]renderer[/\\]src[/\\]main\.(ts|tsx|js|jsx)$/,
  // App-level entry points (main process bootstrap)
  /[/\\]main[/\\]index\.(ts|js)$/,
];

// Patterns that indicate a file IS a test file (checked against basename only)
const TEST_FILE_PATTERNS = [
  /^test_.*\.py$/,
  /^.*_test\.py$/,
  /^.*\.test\.(ts|tsx|js|jsx)$/,
  /^.*\.spec\.(ts|tsx|js|jsx)$/,
  // Node --test pattern: test_*.js (e.g. test_mas_core.js, test_pulse_hook.js)
  /^test_.*\.js$/,
  // Hyphenated test files: test-*.js (e.g. test-prompt-router-followup.js)
  /^test-.*\.js$/,
];

function getAutopilotMode(filePath) {
  let dir = path.dirname(filePath);
  for (let i = 0; i < 10; i++) {
    const modeFile = path.join(dir, ".autopilot", "mode");
    if (existsSync(modeFile)) {
      try {
        return readFileSync(modeFile, "utf8").trim();
      } catch {
        return "";
      }
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return "";
}

function isExempt(filePath) {
  const normalized = filePath.replace(/\\/g, "/");
  return EXEMPT_PATTERNS.some((p) => p.test(normalized));
}

function isTestFile(filePath) {
  const basename = path.basename(filePath);
  // Check filename patterns
  if (TEST_FILE_PATTERNS.some((p) => p.test(basename))) return true;
  // Check if inside a __tests__ directory
  const normalized = filePath.replace(/\\/g, "/");
  return /__tests__\//.test(normalized);
}

function isImplementationFile(filePath) {
  return /\.(py|ts|tsx|js|jsx)$/.test(filePath);
}

/**
 * Walk up the directory tree to find the project root.
 * Stops at the first directory containing a known root marker.
 */
function findProjectRoot(startDir) {
  const markers = [
    'pyproject.toml', 'setup.py', 'setup.cfg',
    'package.json', 'Cargo.toml', 'go.mod', 'Makefile',
  ];
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    if (markers.some((m) => existsSync(path.join(dir, m)))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return startDir;
}

/**
 * Find the corresponding test file for an implementation file.
 * Checks common test layout conventions for Python and JS/TS projects,
 * including project-root tests/ with subpath mirroring:
 *   src/workers/observer.py → tests/workers/test_observer.py
 */
function findTestFile(filePath) {
  const dir = path.dirname(filePath);
  const ext = path.extname(filePath);
  const base = path.basename(filePath, ext);
  const projectRoot = findProjectRoot(dir);

  // Relative path from project root to file's dir (enables subpath mirroring)
  let relDir = '';
  try { relDir = path.relative(projectRoot, dir); } catch { /* ignore */ }
  const relDirStripped = relDir.replace(/^src[/\\]/, '');

  const candidates = [];

  if (ext === '.py') {
    candidates.push(
      // Adjacent
      path.join(dir, `test_${base}.py`),
      path.join(dir, `${base}_test.py`),
      // Adjacent tests/ subdir
      path.join(dir, 'tests', `test_${base}.py`),
      path.join(dir, 'tests', `${base}_test.py`),
      // One level up
      path.join(dir, '..', 'tests', `test_${base}.py`),
      path.join(dir, '..', 'tests', `${base}_test.py`),
      // Project-root tests/ flat
      path.join(projectRoot, 'tests', `test_${base}.py`),
      path.join(projectRoot, 'tests', `${base}_test.py`),
      // Project-root tests/ with full subpath mirror (src/workers/foo → tests/src/workers/test_foo)
      path.join(projectRoot, 'tests', relDir, `test_${base}.py`),
      path.join(projectRoot, 'tests', relDir, `${base}_test.py`),
      // Strip leading src/ from mirror (src/workers/foo → tests/workers/test_foo)
      path.join(projectRoot, 'tests', relDirStripped, `test_${base}.py`),
      path.join(projectRoot, 'tests', relDirStripped, `${base}_test.py`),
    );
  } else {
    // JS / TS
    candidates.push(
      path.join(dir, '__tests__', `${base}.test${ext}`),
      path.join(dir, '__tests__', `${base}.spec${ext}`),
      path.join(dir, `${base}.test${ext}`),
      path.join(dir, `${base}.spec${ext}`),
      path.join(dir, '..', '__tests__', `${base}.test${ext}`),
      path.join(dir, '..', '__tests__', `${base}.spec${ext}`),
      // Masonry CLI convention: masonry/tests/cli-<base>.test.js
      path.join(dir, '..', 'tests', `cli-${base}.test${ext}`),
      path.join(dir, '..', '..', 'tests', `cli-${base}.test${ext}`),
      path.join(dir, '..', '..', '..', 'tests', `cli-${base}.test${ext}`),
      path.join(dir, '..', '..', '..', '..', 'tests', `cli-${base}.test${ext}`),
      // Plain name at deeper levels
      path.join(dir, '..', '..', 'tests', `${base}.test${ext}`),
      path.join(dir, '..', '..', '..', 'tests', `${base}.test${ext}`),
      // Project-root tests/ with subpath mirror
      path.join(projectRoot, 'tests', relDir, `${base}.test${ext}`),
      path.join(projectRoot, 'tests', relDir, `${base}.spec${ext}`),
      path.join(projectRoot, 'tests', relDirStripped, `${base}.test${ext}`),
      path.join(projectRoot, 'tests', relDirStripped, `${base}.spec${ext}`),
    );
  }

  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return null;
}

/**
 * Check if a test file actually imports the implementation module.
 * Returns { imports: boolean }.
 * Reads first 30 lines — enough to cover import sections.
 */
function checkTestImports(testFile, implFile) {
  try {
    const content = readFileSync(testFile, "utf8");
    const lines = content.split("\n").slice(0, 30).join("\n");
    const implBase = path.basename(implFile, path.extname(implFile));

    // Python: from <module> import ... or import <module>
    if (implFile.endsWith(".py")) {
      const pyPattern = new RegExp(
        `(?:from\\s+\\S*${implBase}\\s+import|import\\s+\\S*${implBase})`,
      );
      return { imports: pyPattern.test(lines) };
    }

    // TS/JS: import ... from '...<basename>' or require('...<basename>')
    const jsPattern = new RegExp(
      `(?:import\\s+.*from\\s+.*${implBase}|require\\s*\\(.*${implBase})`,
    );
    return { imports: jsPattern.test(lines) };
  } catch {
    return { imports: true }; // Can't read — assume OK
  }
}

function isResearchProject(dir) {
  return existsSync(path.join(dir, 'program.md')) &&
         existsSync(path.join(dir, 'questions.md'));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const toolInput = parsed.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || "";

  if (!filePath) process.exit(0);

  // Skip non-implementation files
  if (!isImplementationFile(filePath)) process.exit(0);

  // Skip exempt files (configs, types, migrations, etc.)
  if (isExempt(filePath)) process.exit(0);

  // Skip if the file being edited IS a test file
  if (isTestFile(filePath)) process.exit(0);

  // Skip hook files
  if (filePath.replace(/\\/g, "/").includes("/hooks/")) process.exit(0);

  // Look for a corresponding test file
  const testFile = findTestFile(filePath);

  if (testFile) {
    const { imports } = checkTestImports(testFile, filePath);
    if (!imports) {
      const implBasename = path.basename(filePath);
      const testBasename = path.basename(testFile);
      const mode = getAutopilotMode(filePath);
      const msg = mode === "build"
        ? `TDD enforcer: ${testBasename} exists but doesn't appear to import ${implBasename}.\n`
        : `TDD hint: ${testBasename} may not import ${implBasename}.\n`;
      process.stderr.write(`\n${msg}`);
    }
    process.exit(0); // Always exit 0 — indirect imports are valid
  }

  // No test file found
  const mode = getAutopilotMode(filePath);
  const basename = path.basename(filePath);

  if (mode === "build") {
    process.stderr.write(
      `\nTDD enforcer: No test file found for ${basename}.\n` +
        `In /build mode, every implementation file must have a corresponding test.\n` +
        `Write the test first (RED phase), then implement.\n`,
    );
    process.exit(2);
  } else {
    process.stderr.write(
      `\nTDD hint: No test file found for ${basename}. Consider adding tests.\n`,
    );
    process.exit(0);
  }
}

main().catch((e) => {
  process.stderr.write(`tdd-enforcer error: ${e.message}\n`);
  process.exit(0);
});

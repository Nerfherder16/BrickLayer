#!/usr/bin/env node
/**
 * masonry-style-checker.js
 * PostToolUse hook — combined style gate (replaces masonry-lint-check.js and
 * masonry-design-token-enforcer.js, archived 2026-03-28).
 *
 * Pass 1 — Lint check: ruff (Python) / prettier + eslint (TS/JS) in background.
 *   Skips in build/fix autopilot mode. Never blocks (exit 0 always for lint).
 * Pass 2 — Design token enforcer: warns on hardcoded hex colors, banned fonts,
 *   DaisyUI patterns. Only fires when .ui/ dir exists. Always exit 0.
 *
 * NOTE: tsc --noEmit removed — full project typecheck per edit causes VS Code crashes.
 * Use /verify or manual tsc for type checking.
 */

'use strict';
const { execSync, spawn } = require('child_process');
const { existsSync, readFileSync } = require('fs');
const path = require('path');

// ─── Shared helpers ───────────────────────────────────────────────────────────

function readStdin() {
  return new Promise(resolve => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => (data += c));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 3000);
  });
}

function isResearchProject(dir) {
  return existsSync(path.join(dir, 'program.md')) && existsSync(path.join(dir, 'questions.md'));
}

function normalizeWindowsPath(filePath) {
  if (process.platform === 'win32' && /^\/[a-zA-Z]\//.test(filePath)) {
    return filePath[1].toUpperCase() + ':' + filePath.slice(2).replace(/\//g, '\\');
  }
  return filePath;
}

// ─── Pass 1: Lint check ────────────────────────────────────────────────────────

const SKIP_PATTERNS = [
  '/node_modules/', '/dist/', '/build/', '/.next/', '/__pycache__/',
  '/static/dashboard/', '/.autopilot/', '/.ui/', '/src-tauri/target/', '/masonry/',
];

function runBackground(cmd, args, cwd) {
  try {
    const finalCmd = process.platform === 'win32' ? 'cmd' : cmd;
    const finalArgs = process.platform === 'win32' ? ['/c', cmd, ...args] : args;
    const proc = spawn(finalCmd, finalArgs, {
      detached: true, windowsHide: true, stdio: 'ignore', cwd, shell: false,
    });
    proc.unref();
  } catch {}
}

function findRuff() {
  try { execSync('ruff --version', { stdio: 'pipe', timeout: 3000 }); return 'ruff'; } catch {}
  if (process.platform === 'win32') {
    const localAppData = process.env.LOCALAPPDATA || '';
    const appData = process.env.APPDATA || '';
    const candidates = [];
    for (const ver of ['Python311', 'Python312', 'Python313', 'Python314']) {
      candidates.push(path.join(localAppData, 'Programs', 'Python', ver, 'Scripts', 'ruff.exe'));
    }
    candidates.push(path.join(appData, 'Python', 'Scripts', 'ruff.exe'));
    for (const p of candidates) {
      try { execSync(`"${p}" --version`, { stdio: 'pipe', timeout: 3000 }); return p; } catch {}
    }
  } else {
    const home = process.env.HOME || '';
    for (const p of [path.join(home, '.local', 'bin', 'ruff'), path.join(home, '.cargo', 'bin', 'ruff'), '/usr/local/bin/ruff']) {
      try { execSync(`"${p}" --version`, { stdio: 'pipe', timeout: 3000 }); return p; } catch {}
    }
  }
  return null;
}

function getAutopilotMode(filePath) {
  let dir = path.dirname(filePath);
  for (let i = 0; i < 10; i++) {
    const modeFile = path.join(dir, '.autopilot', 'mode');
    if (existsSync(modeFile)) {
      try { return readFileSync(modeFile, 'utf8').trim(); } catch { return ''; }
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return '';
}

function findProjectRoot(filePath) {
  let dir = path.dirname(normalizeWindowsPath(filePath));
  for (let i = 0; i < 10; i++) {
    if (existsSync(path.join(dir, 'package.json')) || existsSync(path.join(dir, 'pyproject.toml'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return path.dirname(normalizeWindowsPath(filePath));
}

function runSync(cmd, opts = {}) {
  try {
    execSync(cmd, { stdio: ['pipe', 'pipe', 'pipe'], timeout: 10000, ...opts });
    return { ok: true, output: '' };
  } catch (e) {
    return { ok: false, output: (e.stderr?.toString() || '') + (e.stdout?.toString() || '') };
  }
}

function findLocalBin(binName, root) {
  const ext = process.platform === 'win32' ? '.cmd' : '';
  let dir = root;
  for (let i = 0; i < 5; i++) {
    const p = path.join(dir, 'node_modules', '.bin', binName + ext);
    if (existsSync(p)) return p;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function runLintCheck(filePath, winPath, projectRoot) {
  const normalized = filePath.replace(/\\/g, '/');
  const mode = getAutopilotMode(filePath);
  if (mode === 'build' || mode === 'fix') return; // agents handle linting
  if (normalized.includes('/hooks/')) return;
  if (SKIP_PATTERNS.some(p => normalized.includes(p))) return;

  const cwdOpts = { cwd: projectRoot };

  if (filePath.endsWith('.py')) {
    const ruff = findRuff();
    if (!ruff) return;
    runBackground(ruff, ['format', winPath], projectRoot);
    const check = runSync(`"${ruff}" check "${winPath}"`, cwdOpts);
    if (!check.ok) {
      process.stderr.write(`ruff: ${path.basename(filePath)}: ${check.output.split('\n')[0]}\n`);
    }
  } else if (/\.(ts|tsx|js|jsx)$/.test(filePath)) {
    const prettierBin = findLocalBin('prettier', projectRoot);
    if (prettierBin) runBackground(prettierBin, ['--write', filePath], projectRoot);

    let hasEslintConfig = false;
    let dir = path.dirname(filePath);
    for (let i = 0; i < 5; i++) {
      if (existsSync(path.join(dir, 'eslint.config.js')) || existsSync(path.join(dir, 'eslint.config.mjs')) ||
          existsSync(path.join(dir, '.eslintrc.json')) || existsSync(path.join(dir, '.eslintrc.js'))) {
        hasEslintConfig = true; break;
      }
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
    if (hasEslintConfig) {
      const eslintBin = findLocalBin('eslint', projectRoot);
      if (eslintBin) runBackground(eslintBin, ['--fix', winPath], projectRoot);
    }
  }
}

// ─── Pass 2: Design token enforcer ───────────────────────────────────────────

const BANNED_FONTS = ['Inter', 'Roboto', 'Open Sans', 'Lato', 'Arial', 'Helvetica', 'system-ui'];
const BANNED_LIBRARIES = ['btn-', 'daisy', 'shadcn', 'ui-btn', 'chakra-'];

function findUiDir(startDir) {
  if (!startDir) return null;
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const uiDir = path.join(dir, '.ui');
    if (existsSync(uiDir)) return uiDir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function loadTokens(uiDir) {
  const tokensFile = path.join(uiDir, 'tokens.json');
  if (!existsSync(tokensFile)) return null;
  try { return JSON.parse(readFileSync(tokensFile, 'utf8')); } catch { return null; }
}

function getUiMode(uiDir) {
  const modeFile = path.join(uiDir, 'mode');
  if (!existsSync(modeFile)) return '';
  try { return readFileSync(modeFile, 'utf8').trim(); } catch { return ''; }
}

function extractHexColors(tokens) {
  const hexMap = {};
  if (!tokens || !tokens.colors) return hexMap;
  function walk(obj, prefix) {
    for (const [key, val] of Object.entries(obj)) {
      if (typeof val === 'string' && val.startsWith('#')) {
        hexMap[val.toLowerCase()] = `var(--${prefix ? prefix + '-' : ''}${key})`;
      } else if (typeof val === 'object' && val !== null) {
        walk(val, prefix ? `${prefix}-${key}` : key);
      }
    }
  }
  walk(tokens.colors, '');
  return hexMap;
}

function runTokenCheck(filePath, content) {
  const ext = path.extname(filePath).toLowerCase();
  if (!['.tsx', '.ts', '.css'].includes(ext)) return;

  const uiDir = findUiDir(path.dirname(filePath));
  if (!uiDir) return;

  const mode = getUiMode(uiDir);
  if (mode === 'compose' || mode === 'fix') return; // agents handle compliance

  const tokens = loadTokens(uiDir);
  const hexMap = extractHexColors(tokens);
  const warnings = [];

  const hexMatches = content.match(/#[0-9a-fA-F]{6}\b/g);
  if (hexMatches) {
    for (const hex of hexMatches) {
      const lower = hex.toLowerCase();
      if (hexMap[lower]) warnings.push(`Hardcoded color ${hex} -> use ${hexMap[lower]}`);
    }
  }
  for (const font of BANNED_FONTS) {
    const regex = new RegExp(`['"]${font}['"]|font-family:.*${font}`, 'i');
    if (regex.test(content)) warnings.push(`Banned font "${font}" detected. Use var(--font-display) or var(--font-mono).`);
  }
  for (const pattern of BANNED_LIBRARIES) {
    if (content.includes(pattern)) warnings.push(`Component library pattern "${pattern}" detected. Use raw Tailwind + CSS custom properties.`);
  }

  if (warnings.length > 0) {
    process.stderr.write(`\n[masonry-tokens] Design token warnings in ${filePath}:\n${warnings.map(w => `  - ${w}`).join('\n')}\n`);
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  const filePath = parsed.tool_input?.file_path || parsed.tool_input?.path || '';
  if (!filePath) process.exit(0);

  const winPath = normalizeWindowsPath(filePath);
  const projectRoot = findProjectRoot(filePath);

  // Pass 1: lint check
  runLintCheck(filePath, winPath, projectRoot);

  // Pass 2: design token enforcer
  const content = parsed.tool_input?.content || parsed.tool_input?.new_string || '';
  if (content) runTokenCheck(filePath, content);

  process.exit(0);
}

main().catch(() => process.exit(0));

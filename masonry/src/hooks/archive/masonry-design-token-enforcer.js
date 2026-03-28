#!/usr/bin/env node
/**
 * PostToolUse hook (Masonry): Warns when UI files contain hardcoded design values
 * that should use CSS custom properties from tokens.json.
 *
 * Triggers on .tsx, .css, .ts files in projects with .ui/
 * Silent during compose/fix mode (agents handle compliance).
 * Exit 0 always (warning only, never blocks).
 */

const { existsSync, readFileSync } = require("fs");
const { join, dirname, extname } = require("path");

const BANNED_FONTS = [
  "Inter",
  "Roboto",
  "Open Sans",
  "Lato",
  "Arial",
  "Helvetica",
  "system-ui",
];

const BANNED_LIBRARIES = [
  "btn-", // DaisyUI
  "daisy",
  "shadcn",
  "ui-btn",
  "chakra-",
];

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function findUiDir(startDir) {
  if (!startDir) return null;
  let dir = startDir;
  for (let i = 0; i < 15; i++) {
    const uiDir = join(dir, ".ui");
    if (existsSync(uiDir)) return uiDir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function loadTokens(uiDir) {
  const tokensFile = join(uiDir, "tokens.json");
  if (!existsSync(tokensFile)) return null;
  try {
    return JSON.parse(readFileSync(tokensFile, "utf8"));
  } catch {
    return null;
  }
}

function getMode(uiDir) {
  const modeFile = join(uiDir, "mode");
  if (!existsSync(modeFile)) return "";
  try {
    return readFileSync(modeFile, "utf8").trim();
  } catch {
    return "";
  }
}

function extractHexColors(tokens) {
  const hexMap = {};
  if (!tokens || !tokens.colors) return hexMap;

  function walk(obj, path) {
    for (const [key, val] of Object.entries(obj)) {
      if (typeof val === "string" && val.startsWith("#")) {
        hexMap[val.toLowerCase()] = `var(--${path ? path + "-" : ""}${key})`;
      } else if (typeof val === "object" && val !== null) {
        walk(val, path ? `${path}-${key}` : key);
      }
    }
  }

  walk(tokens.colors, "");
  return hexMap;
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const toolInput = parsed.tool_input || {};
  const filePath = toolInput.file_path;
  if (!filePath) process.exit(0);

  // Only check .tsx, .ts, .css files
  const ext = extname(filePath).toLowerCase();
  if (![".tsx", ".ts", ".css"].includes(ext)) process.exit(0);

  // Find .ui/ directory
  const uiDir = findUiDir(dirname(filePath));
  if (!uiDir) process.exit(0);

  // Silent during compose/fix mode — agents handle compliance
  const mode = getMode(uiDir);
  if (mode === "compose" || mode === "fix") process.exit(0);

  const tokens = loadTokens(uiDir);
  const hexMap = extractHexColors(tokens);
  const warnings = [];

  // Read the file content that was just written/edited
  let content = "";
  if (toolInput.content) {
    content = toolInput.content;
  } else if (toolInput.new_string) {
    content = toolInput.new_string;
  } else {
    process.exit(0);
  }

  // Check for hardcoded hex colors that match token values
  const hexMatches = content.match(/#[0-9a-fA-F]{6}\b/g);
  if (hexMatches) {
    for (const hex of hexMatches) {
      const lower = hex.toLowerCase();
      if (hexMap[lower]) {
        warnings.push(`Hardcoded color ${hex} -> use ${hexMap[lower]}`);
      }
    }
  }

  // Check for banned fonts
  for (const font of BANNED_FONTS) {
    const regex = new RegExp(`['"]${font}['"]|font-family:.*${font}`, "i");
    if (regex.test(content)) {
      warnings.push(
        `Banned font "${font}" detected. Use var(--font-display) or var(--font-mono).`
      );
    }
  }

  // Check for banned library patterns
  for (const pattern of BANNED_LIBRARIES) {
    if (content.includes(pattern)) {
      warnings.push(
        `Component library pattern "${pattern}" detected. Use raw Tailwind + CSS custom properties.`
      );
    }
  }

  if (warnings.length > 0) {
    process.stderr.write(
      `\n[masonry-tokens] Design token warnings in ${filePath}:\n${warnings.map((w) => `  - ${w}`).join("\n")}\n`
    );
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

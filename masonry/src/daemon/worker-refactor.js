#!/usr/bin/env node
/**
 * Masonry Daemon Worker: refactor
 *
 * Beyond deepdive — detects structural refactoring opportunities:
 *   - God files: > 500 lines (more aggressive than deepdive's 300)
 *   - Duplicate code blocks: near-identical 8+ line blocks across files
 *   - Deeply nested callbacks / promise chains (> 4 levels of nesting)
 *   - Large exported objects that should be split into modules
 *
 * Writes findings to .autopilot/refactor-candidates.md.
 *
 * Interval: 2 hours (managed by daemon-manager.sh)
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
  } catch {}
  return results;
}

// Compute a normalized "block fingerprint" for deduplication
function blockFingerprint(lines) {
  return lines
    .map(l => l.trim().replace(/["'`]/g, '"').replace(/\w+Id\b/g, "ID").replace(/\d+/g, "N"))
    .join("|");
}

function findDuplicateBlocks(files, root, blockSize = 8) {
  const fingerprints = {}; // fingerprint → [{file, startLine}]

  for (const file of files) {
    try {
      const content = fs.readFileSync(file, "utf8");
      const lines = content.split("\n");
      const relPath = path.relative(root, file);

      for (let i = 0; i <= lines.length - blockSize; i++) {
        const block = lines.slice(i, i + blockSize);
        // Skip blocks that are mostly blank or comment lines
        const meaningful = block.filter(l => l.trim() && !l.trim().startsWith("//") && !l.trim().startsWith("#")).length;
        if (meaningful < blockSize * 0.6) continue;

        const fp = blockFingerprint(block);
        if (!fingerprints[fp]) fingerprints[fp] = [];
        fingerprints[fp].push({ file: relPath, startLine: i + 1 });
      }
    } catch {}
  }

  // Return only fingerprints that appear in 2+ different files
  return Object.entries(fingerprints)
    .filter(([, locs]) => {
      const files = new Set(locs.map(l => l.file));
      return files.size >= 2;
    })
    .map(([fp, locs]) => ({
      fingerprint: fp.slice(0, 60),
      locations: locs.slice(0, 4),
      fileCount: new Set(locs.map(l => l.file)).size,
    }))
    .slice(0, 20);
}

function findGodFiles(files, root, threshold = 500) {
  return files
    .map(file => {
      try {
        const content = fs.readFileSync(file, "utf8");
        const lineCount = content.split("\n").length;
        if (lineCount >= threshold) {
          return { file: path.relative(root, file), lines: lineCount };
        }
      } catch {}
      return null;
    })
    .filter(Boolean)
    .sort((a, b) => b.lines - a.lines);
}

function findDeepNesting(files, root, maxDepth = 5) {
  const issues = [];
  for (const file of files.filter(f => /\.(ts|tsx|js|jsx)$/.test(f))) {
    try {
      const content = fs.readFileSync(file, "utf8");
      const lines = content.split("\n");
      let depth = 0;
      for (let i = 0; i < lines.length; i++) {
        depth += (lines[i].match(/\{/g) || []).length;
        depth -= (lines[i].match(/\}/g) || []).length;
        if (depth < 0) depth = 0;
        if (depth > maxDepth) {
          issues.push({ file: path.relative(root, file), line: i + 1, depth });
          // Skip ahead to avoid repeated flags for same nesting
          i += 10;
          depth = Math.max(0, depth - 2);
        }
      }
    } catch {}
  }
  return issues.slice(0, 15);
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  console.log(`[refactor] Running at ${timestamp}`);

  const IGNORE = [
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "coverage", ".autopilot", ".ui", ".mas",
    "masonry/src", "migrations", "alembic",
  ];
  const SOURCE_EXTS = [".py", ".ts", ".tsx", ".js"];

  const files = walkDir(root, SOURCE_EXTS, IGNORE);
  console.log(`[refactor] Scanning ${files.length} files`);

  const godFiles = findGodFiles(files, root);
  const deepNesting = findDeepNesting(files, root);
  const duplicates = findDuplicateBlocks(files.slice(0, 80), root); // cap for perf

  const output = [
    `# Refactor Candidates`,
    ``,
    `Generated: ${timestamp}`,
    `Project: ${path.basename(root)}`,
    `Files scanned: ${files.length}`,
    ``,
    `## Summary`,
    ``,
    `| Check | Count |`,
    `|-------|-------|`,
    `| God files (>500 lines) | ${godFiles.length} |`,
    `| Deep nesting (>${5} levels) | ${deepNesting.length} |`,
    `| Duplicate code blocks | ${duplicates.length} |`,
    ``,
  ];

  if (godFiles.length > 0) {
    output.push(`## God Files (${godFiles.length})`);
    output.push("");
    output.push("These files exceed 500 lines and should be split into focused modules.");
    output.push("");
    for (const f of godFiles) {
      output.push(`- \`${f.file}\` — **${f.lines} lines**`);
    }
    output.push("");
  }

  if (duplicates.length > 0) {
    output.push(`## Duplicate Code Blocks (${duplicates.length})`);
    output.push("");
    output.push("8+ line blocks with identical structure found across multiple files.");
    output.push("");
    for (const dup of duplicates) {
      const locs = dup.locations.map(l => `\`${l.file}:${l.startLine}\``).join(", ");
      output.push(`- **${dup.fileCount} files**: ${locs}`);
      output.push(`  Pattern: \`${dup.fingerprint}...\``);
    }
    output.push("");
  }

  if (deepNesting.length > 0) {
    output.push(`## Deep Nesting (${deepNesting.length})`);
    output.push("");
    output.push("Nesting depth > 5 levels — consider extracting inner logic.");
    output.push("");
    for (const n of deepNesting) {
      output.push(`- \`${n.file}:${n.line}\` — depth ${n.depth}`);
    }
    output.push("");
  }

  output.push("## Actions");
  output.push("");
  output.push("Spawn the `refactorer` agent: `Act as the refactorer agent in ~/.claude/agents/refactorer.md.`");
  output.push("Or use `/fix` targeting specific files listed above.");

  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch {}

  fs.writeFileSync(path.join(autopilotDir, "refactor-candidates.md"), output.join("\n"), "utf8");
  console.log(`[refactor] Done — ${godFiles.length} god files, ${duplicates.length} duplicates, ${deepNesting.length} deep nesting → .autopilot/refactor-candidates.md`);
}

main().catch(err => {
  console.error("[refactor] Error:", err.message);
  process.exit(0);
});

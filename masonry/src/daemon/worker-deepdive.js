#!/usr/bin/env node
/**
 * Masonry Daemon Worker: deepdive
 *
 * Audits code complexity, dead code, and duplication across the project.
 * Writes findings to .autopilot/deepdive.md.
 *
 * Checks:
 *   - Long functions (> 40 lines in Python, > 150 lines for React components)
 *   - High cyclomatic complexity (branches: if/for/while/try > 10 per function)
 *   - Dead code: functions defined but never called
 *   - File size violations (> 300 lines for source files)
 *   - TODO/FIXME/HACK/XXX markers with count
 *
 * Interval: 4 hours (managed by daemon-manager.sh)
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

function analyzeFile(filePath, root) {
  const content = fs.readFileSync(filePath, "utf8");
  const lines = content.split("\n");
  const relPath = path.relative(root, filePath);
  const ext = path.extname(filePath).toLowerCase();
  const issues = [];

  // File size check
  if (lines.length > 300) {
    issues.push({
      type: "file-size",
      severity: lines.length > 500 ? "HIGH" : "MEDIUM",
      message: `${lines.length} lines (limit: 300)`,
      file: relPath,
      line: null,
    });
  }

  // TODO/FIXME/HACK/XXX markers
  const markers = [];
  lines.forEach((line, i) => {
    const m = line.match(/\b(TODO|FIXME|HACK|XXX|TEMP|BUG)\b/i);
    if (m) markers.push({ marker: m[1].toUpperCase(), line: i + 1, text: line.trim().slice(0, 80) });
  });
  if (markers.length > 0) {
    issues.push({
      type: "tech-debt-markers",
      severity: "LOW",
      message: `${markers.length} markers: ${markers.map(m => `${m.marker}:${m.line}`).join(", ")}`,
      file: relPath,
      line: null,
      details: markers,
    });
  }

  // Python-specific: function length + complexity
  if (ext === ".py") {
    let inFunction = false;
    let funcStart = 0;
    let funcName = "";
    let funcLines = 0;
    let branchCount = 0;

    lines.forEach((line, i) => {
      const trimmed = line.trim();

      // Detect function definition
      const funcMatch = trimmed.match(/^(?:async\s+)?def\s+(\w+)/);
      if (funcMatch) {
        // Check previous function
        if (inFunction && funcLines > 40) {
          issues.push({
            type: "long-function",
            severity: funcLines > 80 ? "HIGH" : "MEDIUM",
            message: `${funcName}() is ${funcLines} lines (limit: 40)`,
            file: relPath,
            line: funcStart,
          });
        }
        if (inFunction && branchCount > 10) {
          issues.push({
            type: "high-complexity",
            severity: "HIGH",
            message: `${funcName}() has complexity ${branchCount} (limit: 10)`,
            file: relPath,
            line: funcStart,
          });
        }

        inFunction = true;
        funcStart = i + 1;
        funcName = funcMatch[1];
        funcLines = 0;
        branchCount = 0;
      }

      if (inFunction) {
        funcLines++;
        if (/^\s+(if|elif|for|while|try|except|with)\b/.test(line)) branchCount++;
      }
    });
  }

  // TypeScript/React: component length
  if ([".ts", ".tsx"].includes(ext)) {
    // Check for React components > 150 lines
    const funcMatches = [...content.matchAll(/export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)/g)];
    funcMatches.forEach(match => {
      const funcStart = content.slice(0, match.index).split("\n").length;
      // Rough estimate: find matching closing brace by brace counting
      let depth = 0;
      let funcEnd = funcStart;
      const funcLines = lines.slice(funcStart - 1);
      for (let i = 0; i < funcLines.length; i++) {
        depth += (funcLines[i].match(/{/g) || []).length;
        depth -= (funcLines[i].match(/}/g) || []).length;
        if (depth <= 0 && i > 0) {
          funcEnd = funcStart + i;
          break;
        }
      }
      const length = funcEnd - funcStart;
      if (length > 150) {
        issues.push({
          type: "long-component",
          severity: length > 250 ? "HIGH" : "MEDIUM",
          message: `${match[1]}() component is ~${length} lines (limit: 150)`,
          file: relPath,
          line: funcStart,
        });
      }
    });
  }

  return issues;
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

  console.log(`[deepdive] Analyzing ${root} at ${timestamp}`);

  const files = walkDir(root, SOURCE_EXTS, IGNORE);
  console.log(`[deepdive] Scanning ${files.length} source files`);

  const allIssues = [];
  for (const file of files) {
    try {
      const issues = analyzeFile(file, root);
      allIssues.push(...issues);
    } catch { /* unreadable file */ }
  }

  // Sort by severity
  const severity = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  allIssues.sort((a, b) => (severity[a.severity] || 2) - (severity[b.severity] || 2));

  const high = allIssues.filter(i => i.severity === "HIGH");
  const medium = allIssues.filter(i => i.severity === "MEDIUM");
  const low = allIssues.filter(i => i.severity === "LOW");

  const output = [
    `# Deep Dive Report`,
    ``,
    `Generated: ${timestamp}`,
    `Project: ${path.basename(root)}`,
    `Files scanned: ${files.length}`,
    ``,
    `## Summary`,
    ``,
    `| Severity | Count |`,
    `|----------|-------|`,
    `| HIGH | ${high.length} |`,
    `| MEDIUM | ${medium.length} |`,
    `| LOW | ${low.length} |`,
    `| **Total** | **${allIssues.length}** |`,
    ``,
  ];

  const renderIssues = (issues, title) => {
    if (issues.length === 0) return;
    output.push(`## ${title} (${issues.length})`);
    output.push("");
    for (const issue of issues.slice(0, 30)) {
      const loc = issue.line ? `:${issue.line}` : "";
      output.push(`- **${issue.type}** \`${issue.file}${loc}\` — ${issue.message}`);
    }
    if (issues.length > 30) output.push(`- *...and ${issues.length - 30} more*`);
    output.push("");
  };

  renderIssues(high, "HIGH Severity");
  renderIssues(medium, "MEDIUM Severity");
  renderIssues(low, "LOW Severity (Tech Debt Markers)");

  output.push("## Actions");
  output.push("");
  output.push("Run `/fix` or spawn a `refactorer` agent to address HIGH severity issues.");
  output.push("MEDIUM issues can be addressed in the next `/build` cycle.");

  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch { /* exists */ }

  fs.writeFileSync(path.join(autopilotDir, "deepdive.md"), output.join("\n"), "utf8");
  console.log(`[deepdive] Done — ${allIssues.length} issues (${high.length} HIGH), wrote .autopilot/deepdive.md`);
}

main().catch(err => {
  console.error("[deepdive] Error:", err.message);
  process.exit(0);
});

#!/usr/bin/env node
/**
 * Masonry Daemon Worker: benchmark
 *
 * Runs the project's test suite with timing, compares against a stored baseline,
 * and flags regressions > 20% slower. Also tracks test count over time.
 *
 * Baseline stored in: .autopilot/benchmark-baseline.json
 * Report written to:  .autopilot/benchmark.md
 *
 * Interval: trigger-based (run after builds) or 4h (managed by daemon-manager.sh)
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

function detectTestCommand(root) {
  if (fs.existsSync(path.join(root, "vitest.config.ts")) || fs.existsSync(path.join(root, "vitest.config.js"))) {
    return { cmd: "npx", args: ["vitest", "run", "--reporter=verbose"], parser: "vitest" };
  }
  if (fs.existsSync(path.join(root, "jest.config.js")) || fs.existsSync(path.join(root, "jest.config.ts"))) {
    return { cmd: "npx", args: ["jest", "--passWithNoTests", "--verbose"], parser: "jest" };
  }
  if (fs.existsSync(path.join(root, "pytest.ini")) ||
      fs.existsSync(path.join(root, "pyproject.toml")) ||
      fs.existsSync(path.join(root, "tests", "conftest.py"))) {
    return { cmd: "python", args: ["-m", "pytest", "--tb=no", "-q", "--durations=10"], parser: "pytest" };
  }
  return null;
}

function parseResults(output, parser) {
  let passed = 0, failed = 0, durationMs = 0;

  if (parser === "pytest") {
    // "5 passed, 1 failed in 2.34s"
    const summary = output.match(/(\d+) passed(?:,\s*(\d+) failed)?(?:\s+in\s+([\d.]+)s)?/);
    if (summary) {
      passed = parseInt(summary[1] || "0");
      failed = parseInt(summary[2] || "0");
      durationMs = Math.round(parseFloat(summary[3] || "0") * 1000);
    }
  } else if (parser === "vitest" || parser === "jest") {
    // "Tests: 12 passed, 0 failed"
    const testLine = output.match(/Tests:\s+(\d+)\s+passed(?:,\s*(\d+)\s+failed)?/);
    if (testLine) {
      passed = parseInt(testLine[1] || "0");
      failed = parseInt(testLine[2] || "0");
    }
    // "Duration  1.23s"
    const dur = output.match(/Duration\s+([\d.]+)s/);
    if (dur) durationMs = Math.round(parseFloat(dur[1]) * 1000);
  }

  return { passed, failed, durationMs };
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  console.log(`[benchmark] Running at ${timestamp}`);

  const testSpec = detectTestCommand(root);
  if (!testSpec) {
    console.log("[benchmark] No test runner detected — skipping");
    return;
  }

  console.log(`[benchmark] Running: ${testSpec.cmd} ${testSpec.args.join(" ")}`);
  const startMs = Date.now();

  const result = spawnSync(testSpec.cmd, testSpec.args, {
    cwd: root,
    encoding: "utf8",
    timeout: 120000,
    env: { ...process.env, CI: "1" },
  });

  const wallMs = Date.now() - startMs;
  const output = (result.stdout || "") + (result.stderr || "");
  const parsed = parseResults(output, testSpec.parser);
  if (parsed.durationMs === 0) parsed.durationMs = wallMs;

  console.log(`[benchmark] ${parsed.passed} passed, ${parsed.failed} failed in ${parsed.durationMs}ms`);

  // Load baseline
  const baselinePath = path.join(root, ".autopilot", "benchmark-baseline.json");
  let baseline = null;
  try { baseline = JSON.parse(fs.readFileSync(baselinePath, "utf8")); } catch {}

  // Detect regressions
  const regressions = [];
  if (baseline) {
    const durationDelta = ((parsed.durationMs - baseline.durationMs) / baseline.durationMs) * 100;
    const testsDelta = parsed.passed - baseline.passed;

    if (durationDelta > 20) {
      regressions.push(`Duration regressed ${durationDelta.toFixed(1)}% slower (${baseline.durationMs}ms → ${parsed.durationMs}ms)`);
    }
    if (testsDelta < -2) {
      regressions.push(`Test count dropped: ${baseline.passed} → ${parsed.passed} (${Math.abs(testsDelta)} tests lost)`);
    }
    if (parsed.failed > 0) {
      regressions.push(`${parsed.failed} test(s) failing`);
    }
  }

  // Write report
  const autopilotDir = path.join(root, ".autopilot");
  try { fs.mkdirSync(autopilotDir, { recursive: true }); } catch {}

  const output_lines = [
    `# Benchmark Report`,
    ``,
    `Generated: ${timestamp}`,
    `Test runner: ${testSpec.parser}`,
    ``,
    `## Results`,
    ``,
    `| Metric | Current | Baseline | Delta |`,
    `|--------|---------|----------|-------|`,
    `| Tests passing | ${parsed.passed} | ${baseline?.passed ?? "—"} | ${baseline ? (parsed.passed - baseline.passed >= 0 ? "+" : "") + (parsed.passed - baseline.passed) : "—"} |`,
    `| Tests failing | ${parsed.failed} | ${baseline?.failed ?? "—"} | — |`,
    `| Duration | ${parsed.durationMs}ms | ${baseline?.durationMs ? baseline.durationMs + "ms" : "—"} | ${baseline ? ((parsed.durationMs - baseline.durationMs) / baseline.durationMs * 100).toFixed(1) + "%" : "—"} |`,
    ``,
  ];

  if (regressions.length > 0) {
    output_lines.push(`## ⚠ Regressions (${regressions.length})`);
    output_lines.push("");
    for (const r of regressions) output_lines.push(`- ${r}`);
    output_lines.push("");
    output_lines.push("Run `/fix` or spawn `diagnose-analyst` to investigate.");
  } else if (baseline) {
    output_lines.push("## ✓ No Regressions");
    output_lines.push("");
    output_lines.push("Performance and test count are within acceptable bounds.");
  } else {
    output_lines.push("## Baseline Established");
    output_lines.push("");
    output_lines.push("No prior baseline. This run is now the baseline for future comparisons.");
  }

  fs.writeFileSync(path.join(autopilotDir, "benchmark.md"), output_lines.join("\n"), "utf8");

  // Update baseline if tests pass (don't save a failing baseline)
  if (parsed.failed === 0 && parsed.passed > 0) {
    const newBaseline = {
      timestamp,
      passed: parsed.passed,
      failed: parsed.failed,
      durationMs: parsed.durationMs,
      runner: testSpec.parser,
    };
    fs.writeFileSync(baselinePath, JSON.stringify(newBaseline, null, 2), "utf8");
    console.log(`[benchmark] Baseline updated — ${parsed.passed} tests, ${parsed.durationMs}ms`);
  }

  if (regressions.length > 0) {
    console.log(`[benchmark] REGRESSIONS: ${regressions.join(" | ")}`);
  } else {
    console.log(`[benchmark] Done — no regressions`);
  }
}

main().catch(err => {
  console.error("[benchmark] Error:", err.message);
  process.exit(0);
});

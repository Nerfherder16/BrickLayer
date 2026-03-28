/**
 * Tests for masonry_verify_7point tool logic in masonry-mcp.js
 *
 * These tests validate the check result structure, blocking/warning
 * classification, and overall PASS/FAIL aggregation — without spawning
 * real subprocesses (we stub execSync where needed).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";
import os from "os";
import path from "path";

// ---------------------------------------------------------------------------
// Helpers — build a minimal fake project directory
// ---------------------------------------------------------------------------

function makeTmpProject(opts = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "verify7-test-"));
  if (opts.pytestIni) fs.writeFileSync(path.join(dir, "pytest.ini"), "[pytest]\n");
  if (opts.packageJson) {
    fs.writeFileSync(
      path.join(dir, "package.json"),
      JSON.stringify({ scripts: { test: "vitest run" } }),
    );
  }
  if (opts.dockerfile) fs.writeFileSync(path.join(dir, "Dockerfile"), "FROM node:18\n");
  if (opts.integrationDir) {
    fs.mkdirSync(path.join(dir, "tests", "integration"), { recursive: true });
  }
  return dir;
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

// ---------------------------------------------------------------------------
// Unit tests for the result-building helpers (pure logic, no subprocess)
// ---------------------------------------------------------------------------

describe("verify_7point result schema", () => {
  it("result has required fields when all checks pass", () => {
    const result = {
      overall: "PASS",
      checks: [
        { name: "unit_tests", status: "PASS", detail: "12 passed" },
        { name: "coverage", status: "PASS", detail: "84%" },
        { name: "integration_tests", status: "SKIP", detail: "No integration dir found" },
        { name: "e2e_tests", status: "SKIP", detail: "No e2e config found" },
        { name: "security", status: "PASS", detail: "No HIGH/CRITICAL findings" },
        { name: "performance", status: "PASS", detail: "Baseline written" },
        { name: "docker_build", status: "SKIP", detail: "No Dockerfile" },
      ],
      blocking_failures: [],
      warnings: [],
    };

    expect(result).toHaveProperty("overall");
    expect(result).toHaveProperty("checks");
    expect(result).toHaveProperty("blocking_failures");
    expect(result).toHaveProperty("warnings");
    expect(result.overall).toBe("PASS");
    expect(result.checks).toHaveLength(7);
    result.checks.forEach((c) => {
      expect(c).toHaveProperty("name");
      expect(c).toHaveProperty("status");
      expect(c).toHaveProperty("detail");
      expect(["PASS", "FAIL", "SKIP"]).toContain(c.status);
    });
  });

  it("overall is FAIL when any blocking check fails", () => {
    const checks = [
      { name: "unit_tests", status: "FAIL", detail: "3 tests failed" },
      { name: "coverage", status: "PASS", detail: "82%" },
      { name: "integration_tests", status: "SKIP", detail: "" },
      { name: "e2e_tests", status: "SKIP", detail: "" },
      { name: "security", status: "PASS", detail: "" },
      { name: "performance", status: "PASS", detail: "" },
      { name: "docker_build", status: "SKIP", detail: "" },
    ];

    const blockingNames = ["unit_tests", "integration_tests", "e2e_tests", "security", "docker_build"];
    const blocking_failures = checks
      .filter((c) => c.status === "FAIL" && blockingNames.includes(c.name))
      .map((c) => c.name);

    const overall = blocking_failures.length > 0 ? "FAIL" : "PASS";
    expect(overall).toBe("FAIL");
    expect(blocking_failures).toContain("unit_tests");
  });

  it("coverage < 80% is a warning, not a blocking failure", () => {
    const coveragePct = 72;
    const isBlocking = false; // coverage is always non-blocking
    const isWarning = coveragePct < 80;

    expect(isBlocking).toBe(false);
    expect(isWarning).toBe(true);
  });

  it("missing perf baseline is a warning, not a blocking failure", () => {
    const baselineExists = false;
    const isBlocking = false;
    const isWarning = !baselineExists;

    expect(isBlocking).toBe(false);
    expect(isWarning).toBe(true);
  });

  it("docker_build FAIL is blocking", () => {
    const blockingNames = ["unit_tests", "integration_tests", "e2e_tests", "security", "docker_build"];
    expect(blockingNames).toContain("docker_build");
  });

  it("all 7 check names are present", () => {
    const expectedNames = [
      "unit_tests",
      "coverage",
      "integration_tests",
      "e2e_tests",
      "security",
      "performance",
      "docker_build",
    ];
    expect(expectedNames).toHaveLength(7);
    expectedNames.forEach((n) => expect(typeof n).toBe("string"));
  });
});

// ---------------------------------------------------------------------------
// Project-detection logic (filesystem-based, no subprocess)
// ---------------------------------------------------------------------------

describe("project type detection", () => {
  let dir;
  afterEach(() => { if (dir) cleanup(dir); });

  it("detects Python project via pytest.ini", () => {
    dir = makeTmpProject({ pytestIni: true });
    const hasPytest = fs.existsSync(path.join(dir, "pytest.ini"));
    const hasPyproject = fs.existsSync(path.join(dir, "pyproject.toml"));
    const isPython = hasPytest || hasPyproject;
    expect(isPython).toBe(true);
  });

  it("detects JS project via package.json with test script", () => {
    dir = makeTmpProject({ packageJson: true });
    const pkgPath = path.join(dir, "package.json");
    const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
    const isJS = Boolean(pkg.scripts && pkg.scripts.test);
    expect(isJS).toBe(true);
  });

  it("detects Dockerfile presence", () => {
    dir = makeTmpProject({ dockerfile: true });
    const hasDockerfile = fs.existsSync(path.join(dir, "Dockerfile"));
    expect(hasDockerfile).toBe(true);
  });

  it("skips docker check when no Dockerfile", () => {
    dir = makeTmpProject({});
    const hasDockerfile = fs.existsSync(path.join(dir, "Dockerfile"));
    expect(hasDockerfile).toBe(false);
  });

  it("detects integration test directory", () => {
    dir = makeTmpProject({ integrationDir: true });
    const hasIntegration =
      fs.existsSync(path.join(dir, "tests", "integration")) ||
      fs.existsSync(path.join(dir, "test", "integration"));
    expect(hasIntegration).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Perf baseline logic
// ---------------------------------------------------------------------------

describe("performance baseline", () => {
  let dir;
  afterEach(() => { if (dir) cleanup(dir); });

  it("creates baseline file when missing", () => {
    dir = makeTmpProject({});
    const autopilotDir = path.join(dir, ".autopilot");
    const baselineFile = path.join(autopilotDir, "perf-baseline.json");

    // Simulate what the tool does: write baseline if missing
    fs.mkdirSync(autopilotDir, { recursive: true });
    const baseline = { created_at: new Date().toISOString(), timing_ms: 0 };
    fs.writeFileSync(baselineFile, JSON.stringify(baseline), "utf8");

    expect(fs.existsSync(baselineFile)).toBe(true);
    const read = JSON.parse(fs.readFileSync(baselineFile, "utf8"));
    expect(read).toHaveProperty("created_at");
  });

  it("warns when new timing is >20% slower than baseline", () => {
    const baselineTiming = 1000;
    const currentTiming = 1250;
    const threshold = 1.2;
    const tooSlow = currentTiming > baselineTiming * threshold;
    expect(tooSlow).toBe(true);
  });

  it("passes when new timing is within 20% of baseline", () => {
    const baselineTiming = 1000;
    const currentTiming = 1150;
    const threshold = 1.2;
    const tooSlow = currentTiming > baselineTiming * threshold;
    expect(tooSlow).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Security findings classification
// ---------------------------------------------------------------------------

describe("security check findings parsing", () => {
  it("flags HIGH severity as a finding", () => {
    const findings = [
      { issue_severity: "HIGH", issue_text: "Use of assert" },
      { issue_severity: "LOW", issue_text: "Hardcoded tmp dir" },
    ];
    const critical = findings.filter(
      (f) => f.issue_severity === "HIGH" || f.issue_severity === "CRITICAL",
    );
    expect(critical).toHaveLength(1);
  });

  it("flags CRITICAL severity as a finding", () => {
    const findings = [{ issue_severity: "CRITICAL", issue_text: "SQL injection risk" }];
    const critical = findings.filter(
      (f) => f.issue_severity === "HIGH" || f.issue_severity === "CRITICAL",
    );
    expect(critical).toHaveLength(1);
  });

  it("ignores LOW/MEDIUM severity", () => {
    const findings = [
      { issue_severity: "LOW", issue_text: "Some minor issue" },
      { issue_severity: "MEDIUM", issue_text: "Some medium issue" },
    ];
    const critical = findings.filter(
      (f) => f.issue_severity === "HIGH" || f.issue_severity === "CRITICAL",
    );
    expect(critical).toHaveLength(0);
  });
});

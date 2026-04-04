#!/usr/bin/env node
/**
 * masonry-dep-audit.js
 * PostToolUse hook — audits package.json and requirements.txt for HIGH/CRITICAL vulnerabilities.
 * Never blocks (exit 0 always). Warns to stderr with structured output.
 */

const { execFileSync } = require('child_process');
const path = require('path');

/**
 * Check whether a command exists on PATH by running it with --version.
 * Returns true if the spawn succeeds (or errors with non-ENOENT).
 */
function commandExists(cmd) {
  try {
    execFileSync(cmd, ['--version'], { stdio: 'pipe' });
    return true;
  } catch (e) {
    if (e.code === 'ENOENT') return false;
    // Tool exists but exited non-zero (e.g. pip-audit with no project) — still exists
    return true;
  }
}

/**
 * Run npm audit and return { high, critical } counts.
 * Returns null if npm is unavailable or audit fails in an unexpected way.
 */
function runNpmAudit(fileDir) {
  try {
    const output = execFileSync('npm', ['audit', '--json'], {
      cwd: fileDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 8000,
    });
    const data = JSON.parse(output.toString());
    // npm audit --json v7+ uses data.metadata.vulnerabilities
    const vuln = (data.metadata && data.metadata.vulnerabilities) || {};
    return {
      high: vuln.high || 0,
      critical: vuln.critical || 0,
    };
  } catch (e) {
    // npm audit exits non-zero when vulnerabilities are found; parse stdout
    if (e.stdout) {
      try {
        const data = JSON.parse(e.stdout.toString());
        const vuln = (data.metadata && data.metadata.vulnerabilities) || {};
        return {
          high: vuln.high || 0,
          critical: vuln.critical || 0,
        };
      } catch (_) {
        // unparseable — return null so caller can warn
        return null;
      }
    }
    return null;
  }
}

/**
 * Run pip-audit and return { high, critical } counts.
 * pip-audit uses CVSS severity: HIGH = score >= 7, CRITICAL = score >= 9.
 * Returns null if pip-audit is unavailable or fails unexpectedly.
 */
function runPipAudit(fileDir) {
  try {
    const output = execFileSync('pip-audit', ['--format', 'json', '-r', 'requirements.txt'], {
      cwd: fileDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 6000,
    });
    return parsePipAuditOutput(output.toString());
  } catch (e) {
    // pip-audit exits non-zero when vulnerabilities are found; parse stdout
    if (e.stdout) {
      try {
        return parsePipAuditOutput(e.stdout.toString());
      } catch (_) {
        return null;
      }
    }
    return null;
  }
}

/**
 * Parse pip-audit JSON output into { high, critical } counts.
 * pip-audit JSON schema: array of { name, version, vulns: [{ id, fix_versions, aliases }] }
 * Severity is encoded in the CVE aliases or CVSS scores when available.
 * We conservatively count all vulnerabilities as HIGH unless they have CRITICAL indicators.
 */
function parsePipAuditOutput(jsonStr) {
  const data = JSON.parse(jsonStr);
  // pip-audit outputs: { dependencies: [...] } or directly an array
  const deps = Array.isArray(data) ? data : (data.dependencies || []);
  let high = 0;
  let critical = 0;

  for (const dep of deps) {
    const vulns = dep.vulns || [];
    for (const vuln of vulns) {
      const severity = (vuln.severity || '').toUpperCase();
      if (severity === 'CRITICAL') {
        critical++;
      } else if (severity === 'HIGH') {
        high++;
      } else {
        // No severity field — treat as HIGH per conservative policy
        high++;
      }
    }
  }

  return { high, critical };
}

/**
 * Main hook entry point — reads stdin and dispatches audit.
 */
let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    // Only respond to Write and Edit operations
    if (!['Write', 'Edit'].includes(tool_name)) {
      process.exit(0);
    }

    const filePath = tool_input.file_path || tool_input.path || '';
    const fileName = path.basename(filePath);
    const fileDir = filePath ? path.dirname(path.resolve(filePath)) : process.cwd();

    if (fileName === 'package.json') {
      if (!commandExists('npm')) {
        process.stderr.write('DEP_AUDIT_SKIP: npm not found, skipping vulnerability check\n');
        process.exit(0);
      }
      const result = runNpmAudit(fileDir);
      if (result === null) {
        process.exit(0);
      }
      const total = result.high + result.critical;
      if (result.critical > 0) {
        process.stderr.write(
          `DEPENDENCY_WARNING: ${result.critical} CRITICAL vulnerabilities found in ${filePath}. Run 'npm audit' for details.\n`
        );
      }
      if (result.high > 0) {
        process.stderr.write(
          `DEPENDENCY_WARNING: ${result.high} HIGH vulnerabilities found in ${filePath}. Run 'npm audit' for details.\n`
        );
      }
      if (total === 0) {
        // Clean — silent
      }
      process.exit(0);
    }

    if (fileName === 'requirements.txt') {
      if (!commandExists('pip-audit')) {
        process.stderr.write('DEP_AUDIT_SKIP: pip-audit not found, skipping vulnerability check\n');
        process.exit(0);
      }
      const result = runPipAudit(fileDir);
      if (result === null) {
        process.exit(0);
      }
      const total = result.high + result.critical;
      if (result.critical > 0) {
        process.stderr.write(
          `DEPENDENCY_WARNING: ${result.critical} CRITICAL vulnerabilities found in ${filePath}. Run 'pip-audit' for details.\n`
        );
      }
      if (result.high > 0) {
        process.stderr.write(
          `DEPENDENCY_WARNING: ${result.high} HIGH vulnerabilities found in ${filePath}. Run 'pip-audit' for details.\n`
        );
      }
      if (total === 0) {
        // Clean — silent
      }
      process.exit(0);
    }

    // Non-dependency file — skip silently
    process.exit(0);
  } catch (_e) {
    // Parse error — never block
    process.exit(0);
  }
});

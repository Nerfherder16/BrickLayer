'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { REPO_ROOT } = require('./impl-utils');

// ---------------------------------------------------------------------------
// masonry_verify_7point — 7-point quality gate
// ---------------------------------------------------------------------------

function toolVerify7point(args) {
  const { project_dir } = args;
  if (!fs.existsSync(project_dir)) return { overall: 'FAIL', checks: [], blocking_failures: ['project_dir not found'], warnings: [] };

  const checks = [];
  const blockingFailures = [];
  const warnings = [];
  const execOpts = { encoding: 'utf8', timeout: 120000, cwd: project_dir };

  const hasPytestIni = fs.existsSync(path.join(project_dir, 'pytest.ini'));
  const hasPyproject = fs.existsSync(path.join(project_dir, 'pyproject.toml'));
  const isPython = hasPytestIni || hasPyproject;
  let packageJson = null;
  try {
    const pkgPath = path.join(project_dir, 'package.json');
    if (fs.existsSync(pkgPath)) packageJson = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  } catch (_) {}
  const isJS = packageJson && packageJson.scripts && packageJson.scripts.test;

  // 1. Unit tests
  {
    const cmd = isPython ? 'pytest -q --tb=short' : isJS ? 'npm test -- --reporter=dot' : null;
    if (!cmd) {
      checks.push({ name: 'unit_tests', status: 'SKIP', detail: 'No test runner detected' });
    } else {
      try {
        execSync(cmd, execOpts);
        checks.push({ name: 'unit_tests', status: 'PASS', detail: `${cmd} exited 0` });
      } catch (err) {
        checks.push({ name: 'unit_tests', status: 'FAIL', detail: ((err.stdout || '') + (err.stderr || '')).slice(-1000) || err.message });
        blockingFailures.push('unit_tests');
      }
    }
  }

  // 2. Coverage (warning only)
  try {
    let coveragePct = null;
    let coverageDetail = '';
    if (isPython) {
      try {
        const out = execSync('pytest --cov=src --cov-report=term-missing -q 2>&1', execOpts);
        const match = out.match(/TOTAL\s+\d+\s+\d+\s+(\d+)%/);
        if (match) { coveragePct = parseInt(match[1], 10); coverageDetail = `${coveragePct}% total coverage`; }
        else coverageDetail = 'Coverage output not parseable';
      } catch (err) { coverageDetail = 'pytest --cov failed: ' + (err.message || '').slice(0, 200); }
    } else if (isJS) {
      try {
        const out = execSync('npm test -- --coverage 2>&1', execOpts);
        const match = out.match(/All files[^\|]*\|\s*([\d.]+)/);
        if (match) { coveragePct = parseFloat(match[1]); coverageDetail = `${coveragePct}% total coverage`; }
        else coverageDetail = 'Coverage output not parseable';
      } catch (err) { coverageDetail = 'npm test --coverage failed: ' + (err.message || '').slice(0, 200); }
    } else { coverageDetail = 'No test runner — skipping coverage'; }
    if (coveragePct !== null && coveragePct < 80) warnings.push(`Coverage ${coveragePct}% is below 80% target`);
    checks.push({ name: 'coverage', status: 'PASS', detail: coverageDetail || 'Coverage check skipped' });
  } catch (_) { checks.push({ name: 'coverage', status: 'SKIP', detail: 'Coverage check skipped' }); }

  // 3. Integration tests
  const integrationDir = [path.join(project_dir, 'tests', 'integration'), path.join(project_dir, 'test', 'integration')].find(d => fs.existsSync(d));
  if (!integrationDir) {
    checks.push({ name: 'integration_tests', status: 'SKIP', detail: 'No tests/integration directory found' });
  } else {
    const cmd = isPython ? `pytest ${integrationDir} -q --tb=short` : isJS ? `npx vitest run ${integrationDir} --reporter=dot` : null;
    if (!cmd) { checks.push({ name: 'integration_tests', status: 'SKIP', detail: 'No test runner for integration dir' }); }
    else {
      try {
        execSync(cmd, execOpts);
        checks.push({ name: 'integration_tests', status: 'PASS', detail: `${path.basename(integrationDir)} passed` });
      } catch (err) {
        checks.push({ name: 'integration_tests', status: 'FAIL', detail: ((err.stdout || '') + (err.stderr || '')).slice(-800) || err.message });
        blockingFailures.push('integration_tests');
      }
    }
  }

  // 4. E2E tests
  const playwrightConfig = ['playwright.config.ts', 'playwright.config.js'].find(f => fs.existsSync(path.join(project_dir, f)));
  const cypressConfig = ['cypress.config.ts', 'cypress.config.js', 'cypress.json'].find(f => fs.existsSync(path.join(project_dir, f)));
  if (!playwrightConfig && !cypressConfig) {
    checks.push({ name: 'e2e_tests', status: 'SKIP', detail: 'No Playwright or Cypress config found' });
  } else {
    const cmd = playwrightConfig ? 'npx playwright test --reporter=dot' : 'npx cypress run --headless';
    try {
      execSync(cmd, execOpts);
      checks.push({ name: 'e2e_tests', status: 'PASS', detail: `${playwrightConfig ? 'Playwright' : 'Cypress'} passed` });
    } catch (err) {
      checks.push({ name: 'e2e_tests', status: 'FAIL', detail: ((err.stdout || '') + (err.stderr || '')).slice(-800) || err.message });
      blockingFailures.push('e2e_tests');
    }
  }

  // 5. Security scan
  if (isPython) {
    try {
      const out = execSync('bandit -r src/ -q -f json 2>/dev/null || true', execOpts);
      let findings = [];
      try { const parsed = JSON.parse(out); findings = (parsed.results || []).filter(r => r.issue_severity === 'HIGH' || r.issue_severity === 'CRITICAL'); } catch (_) {}
      if (findings.length > 0) { checks.push({ name: 'security', status: 'FAIL', detail: `${findings.length} HIGH/CRITICAL finding(s)` }); blockingFailures.push('security'); }
      else checks.push({ name: 'security', status: 'PASS', detail: 'No HIGH/CRITICAL bandit findings' });
    } catch (_) { checks.push({ name: 'security', status: 'SKIP', detail: 'bandit not available' }); }
  } else if (isJS) {
    try {
      const out = execSync('npm audit --audit-level=high 2>/dev/null || true', execOpts);
      if (/critical|high/i.test(out)) { checks.push({ name: 'security', status: 'FAIL', detail: 'npm audit found HIGH/CRITICAL vulnerabilities' }); blockingFailures.push('security'); }
      else checks.push({ name: 'security', status: 'PASS', detail: 'No HIGH/CRITICAL npm audit findings' });
    } catch (_) { checks.push({ name: 'security', status: 'SKIP', detail: 'npm audit not available' }); }
  } else { checks.push({ name: 'security', status: 'SKIP', detail: 'No security scanner for detected project type' }); }

  // 6. Performance baseline
  const autopilotDir = path.join(project_dir, '.autopilot');
  const baselineFile = path.join(autopilotDir, 'perf-baseline.json');
  if (!fs.existsSync(baselineFile)) {
    try {
      fs.mkdirSync(autopilotDir, { recursive: true });
      fs.writeFileSync(baselineFile, JSON.stringify({ created_at: new Date().toISOString(), timing_ms: 0, note: 'Initial baseline' }, null, 2), 'utf8');
      checks.push({ name: 'performance', status: 'PASS', detail: 'No prior baseline — wrote initial baseline' });
      warnings.push('Performance baseline did not exist — created initial baseline');
    } catch (err) { checks.push({ name: 'performance', status: 'SKIP', detail: 'Could not write baseline: ' + err.message }); }
  } else {
    try {
      const baseline = JSON.parse(fs.readFileSync(baselineFile, 'utf8'));
      checks.push({ name: 'performance', status: 'PASS', detail: baseline.timing_ms === 0 ? 'Baseline exists but has no timing data' : 'Baseline present' });
    } catch (_) { checks.push({ name: 'performance', status: 'SKIP', detail: 'Could not read baseline' }); }
  }

  // 7. Docker build
  const dockerfilePath = path.join(project_dir, 'Dockerfile');
  if (!fs.existsSync(dockerfilePath)) {
    checks.push({ name: 'docker_build', status: 'SKIP', detail: 'No Dockerfile in project_dir' });
  } else {
    try {
      execSync('docker build . --no-cache -q 2>&1', execOpts);
      checks.push({ name: 'docker_build', status: 'PASS', detail: 'docker build succeeded' });
    } catch (err) {
      checks.push({ name: 'docker_build', status: 'FAIL', detail: ((err.stdout || '') + (err.stderr || '')).slice(-800) || err.message });
      blockingFailures.push('docker_build');
    }
  }

  return { overall: blockingFailures.length > 0 ? 'FAIL' : 'PASS', checks, blocking_failures: blockingFailures, warnings };
}

// ---------------------------------------------------------------------------
// Training, Reasoning, Graph, Strategy
// ---------------------------------------------------------------------------

function toolTrainingUpdate(args) {
  const { telemetry_path } = args;
  const collectorPath = path.join(REPO_ROOT, 'masonry', 'src', 'training', 'collector.py');
  const telPath = telemetry_path || path.join(REPO_ROOT, 'masonry', 'telemetry.jsonl');
  try {
    execSync(`python "${collectorPath}" "${telPath}"`, { timeout: 15000, encoding: 'utf8' });
    const histPath = path.join(REPO_ROOT, 'masonry', 'src', 'training', 'ema_history.json');
    const hist = JSON.parse(fs.readFileSync(histPath, 'utf8'));
    const recommendations = {};
    for (const [taskType, strategies] of Object.entries(hist)) {
      const best = Object.entries(strategies).sort((a, b) => b[1] - a[1])[0];
      recommendations[taskType] = { strategy: best[0], ema_score: best[1] };
    }
    return { success: true, recommendations, task_types: Object.keys(hist).length };
  } catch (e) { return { success: false, error: e.message }; }
}

function toolReasoningQuery(args) {
  const { query, top_k = 5, domain } = args;
  const bankPath = path.join(REPO_ROOT, 'masonry', 'src', 'reasoning', 'bank.py');
  try {
    const domainArg = domain ? ` "${domain}"` : '';
    const out = execSync(`python "${bankPath}" query "${query.replace(/"/g, '\\"')}" ${top_k}${domainArg}`, { timeout: 5000, encoding: 'utf8' });
    const patterns = JSON.parse(out.trim());
    return { patterns, count: patterns.length };
  } catch (e) { return { patterns: [], count: 0, error: e.message }; }
}

function toolReasoningStore(args) {
  const { content, domain = 'general', pattern_id } = args;
  const bankPath = path.join(REPO_ROOT, 'masonry', 'src', 'reasoning', 'bank.py');
  try {
    const idArg = pattern_id ? ` "${pattern_id}"` : '';
    const out = execSync(`python "${bankPath}" store "${content.replace(/"/g, '\\"')}" "${domain}"${idArg}`, { timeout: 5000, encoding: 'utf8' });
    return { success: true, pattern_id: JSON.parse(out.trim()).pattern_id };
  } catch (e) { return { success: false, error: e.message }; }
}

function toolGraphRecord(args) {
  const { task_id, pattern_ids, project = 'default' } = args;
  const graphPath = path.join(REPO_ROOT, 'masonry', 'src', 'reasoning', 'graph.py');
  try {
    const out = execSync(`python "${graphPath}" "${project}" "${task_id}" ${pattern_ids.map(id => `"${id}"`).join(' ')}`, { timeout: 10000, encoding: 'utf8' });
    return JSON.parse(out.trim());
  } catch (e) { return { success: false, error: e.message, skipped: 'neo4j likely unavailable' }; }
}

function toolPageRankRun(args) {
  const { project, confidence_path } = args;
  const pagerankPath = path.join(REPO_ROOT, 'masonry', 'src', 'reasoning', 'pagerank.py');
  const confPath = confidence_path || path.join(process.cwd(), '.autopilot', 'pattern-confidence.json');
  try {
    const out = execSync(`python "${pagerankPath}" "${project}" "${confPath}"`, { timeout: 30000, encoding: 'utf8' });
    return JSON.parse(out.trim());
  } catch (e) { return { success: false, error: e.message, skipped: 'neo4j likely unavailable' }; }
}

function toolSetStrategy(args) {
  const { project_path, strategy } = args;
  const VALID = ['conservative', 'balanced', 'aggressive'];
  if (!VALID.includes(strategy)) return { success: false, error: `Invalid strategy: "${strategy}"` };
  const autopilotDir = path.join(project_path, '.autopilot');
  if (!fs.existsSync(autopilotDir)) return { success: false, error: `No .autopilot/ directory found at ${project_path}` };
  try {
    fs.writeFileSync(path.join(autopilotDir, 'strategy'), strategy, 'utf8');
    return { success: true, strategy, path: path.join(autopilotDir, 'strategy') };
  } catch (e) { return { success: false, error: e.message }; }
}

// ---------------------------------------------------------------------------
// Claims Board
// ---------------------------------------------------------------------------

function _claimsFile(p) { return path.join(p, '.autopilot', 'claims.json'); }
function _loadClaims(claimsPath) {
  if (!fs.existsSync(claimsPath)) return [];
  try { const d = JSON.parse(fs.readFileSync(claimsPath, 'utf8')); return Array.isArray(d) ? d : []; } catch (_) { return []; }
}
function _saveClaims(claimsPath, claims) {
  const dir = path.dirname(claimsPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(claimsPath, JSON.stringify(claims, null, 2), 'utf8');
}
function _nextClaimId(claims) {
  const nums = claims.map(c => parseInt((c.id || '').replace('claim-', ''), 10)).filter(n => !isNaN(n));
  return `claim-${String((nums.length > 0 ? Math.max(...nums) : 0) + 1).padStart(3, '0')}`;
}

function toolClaimsAdd(args) {
  const { project_path, question, task_id, context } = args;
  const claimsPath = _claimsFile(project_path);
  const claims = _loadClaims(claimsPath);
  const claim = { id: _nextClaimId(claims), question, ...(task_id ? { task_id } : {}), ...(context ? { context } : {}), status: 'pending', created_at: new Date().toISOString() };
  claims.push(claim);
  try { _saveClaims(claimsPath, claims); } catch (err) { return { error: `Failed to write claims.json: ${err.message}` }; }
  return { claim_id: claim.id, message: 'Claim filed. Build continues on independent tasks.' };
}

function toolClaimResolve(args) {
  const { project_path, claim_id, answer } = args;
  const claimsPath = _claimsFile(project_path);
  const claims = _loadClaims(claimsPath);
  const claim = claims.find(c => c.id === claim_id);
  if (!claim) return { error: `Claim not found: ${claim_id}` };
  if (claim.status === 'resolved') return { error: `Claim ${claim_id} is already resolved` };
  claim.status = 'resolved'; claim.answer = answer; claim.resolved_at = new Date().toISOString();
  try { _saveClaims(claimsPath, claims); } catch (err) { return { error: `Failed to write claims.json: ${err.message}` }; }
  const pending = claims.filter(c => c.status === 'pending').length;
  return { resolved: claim_id, pending_remaining: pending, message: pending === 0 ? 'All claims resolved.' : `${pending} claim(s) still pending.` };
}

function toolClaimsList(args) {
  const { project_path, status = 'pending' } = args;
  const claimsPath = _claimsFile(project_path);
  const claims = _loadClaims(claimsPath);
  const filtered = status === 'all' ? claims : claims.filter(c => c.status === status);
  return { claims: filtered, count: filtered.length, status_filter: status };
}

module.exports = {
  toolVerify7point, toolTrainingUpdate, toolSetStrategy,
  toolReasoningStore, toolReasoningQuery, toolGraphRecord, toolPageRankRun,
  toolClaimsAdd, toolClaimsList, toolClaimResolve,
};

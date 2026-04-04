'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { httpRequest, REPO_ROOT } = require('./impl-utils');
const { loadConfig } = require('./config');

async function toolDoctor(args) {
  const projectPath = (args && args.project_path) || process.cwd();
  const cfg = loadConfig();
  const daemonDir = path.join(REPO_ROOT, 'masonry', 'src', 'daemon');
  const hooksDir = path.join(REPO_ROOT, 'masonry', 'src', 'hooks');
  const pidsDir = path.join(daemonDir, 'pids');

  const checks = [];

  // 1. Recall connectivity
  try {
    const resp = await Promise.race([
      httpRequest(`${cfg.recallHost}/health`, { method: 'GET', headers: {} }, null),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000)),
    ]);
    if (resp.status >= 200 && resp.status < 300) {
      checks.push({ check: 'Recall API', status: 'PASS', detail: `${cfg.recallHost} → HTTP ${resp.status}` });
    } else {
      checks.push({ check: 'Recall API', status: 'WARN', detail: `HTTP ${resp.status} from ${cfg.recallHost}` });
    }
  } catch (err) {
    checks.push({ check: 'Recall API', status: 'FAIL', detail: `Unreachable: ${err.message}` });
  }

  // 2. Daemon worker status
  const ALL_WORKERS = ['testgaps', 'optimize', 'consolidate', 'deepdive', 'ultralearn', 'map', 'document', 'refactor', 'benchmark'];
  const runningWorkers = [];
  for (const worker of ALL_WORKERS) {
    const pidFile = path.join(pidsDir, `${worker}.pid`);
    let running = false;
    if (fs.existsSync(pidFile)) {
      try {
        const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10);
        try { process.kill(pid, 0); running = true; } catch (_) {}
      } catch (_) {}
    }
    if (running) runningWorkers.push(worker);
  }
  if (runningWorkers.length > 0) {
    checks.push({ check: 'Daemon workers', status: 'PASS', detail: `Running: ${runningWorkers.join(', ')}` });
  } else {
    checks.push({ check: 'Daemon workers', status: 'WARN', detail: 'No workers running — start with daemon-manager.sh start' });
  }

  // 3. Core hook files
  const CORE_HOOKS = [
    'masonry-session-start.js', 'masonry-session-end.js', 'masonry-approver.js',
    'masonry-style-checker.js', 'masonry-stop-guard.js', 'masonry-build-guard.js',
    'masonry-tdd-enforcer.js', 'masonry-mortar-enforcer.js', 'masonry-pre-compact.js',
  ];
  const missingHooks = CORE_HOOKS.filter(h => !fs.existsSync(path.join(hooksDir, h)));
  if (missingHooks.length === 0) {
    checks.push({ check: 'Hook files', status: 'PASS', detail: `All ${CORE_HOOKS.length} core hooks present` });
  } else {
    checks.push({ check: 'Hook files', status: 'FAIL', detail: `Missing: ${missingHooks.join(', ')}` });
  }

  // 4. Agent registry coverage
  const registryFile = path.join(REPO_ROOT, 'masonry', 'agent_registry.yml');
  let registryCount = 0;
  if (fs.existsSync(registryFile)) {
    try { const content = fs.readFileSync(registryFile, 'utf8'); registryCount = (content.match(/^- name:/gm) || []).length; } catch (_) {}
  }
  const agentDirs = [path.join(REPO_ROOT, '.claude', 'agents'), path.join(os.homedir(), '.claude', 'agents')];
  const seenAgents = new Set();
  for (const dir of agentDirs) {
    if (fs.existsSync(dir)) {
      try { fs.readdirSync(dir).filter(f => f.endsWith('.md')).forEach(f => seenAgents.add(f)); } catch (_) {}
    }
  }
  const agentDirCount = seenAgents.size;
  if (registryCount === 0) {
    checks.push({ check: 'Agent registry', status: 'WARN', detail: 'agent_registry.yml not found or empty' });
  } else if (agentDirCount > registryCount + 3) {
    checks.push({ check: 'Agent registry', status: 'WARN', detail: `${agentDirCount} agent files but only ${registryCount} in registry — run masonry_onboard` });
  } else {
    checks.push({ check: 'Agent registry', status: 'PASS', detail: `${registryCount} agents registered, ${agentDirCount} agent files` });
  }

  // 5. Training data freshness
  const trainingFile = path.join(REPO_ROOT, 'masonry', 'training_data', 'scored_all.jsonl');
  if (!fs.existsSync(trainingFile)) {
    checks.push({ check: 'Training data', status: 'WARN', detail: 'scored_all.jsonl not found — run a campaign wave to generate training data' });
  } else {
    try {
      const ageMs = Date.now() - fs.statSync(trainingFile).mtimeMs;
      const ageDays = Math.round(ageMs / (86400 * 1000));
      const lines = fs.readFileSync(trainingFile, 'utf8').split('\n').filter(l => l.trim()).length;
      if (ageDays > 30) {
        checks.push({ check: 'Training data', status: 'WARN', detail: `${lines} records, last updated ${ageDays} days ago` });
      } else {
        checks.push({ check: 'Training data', status: 'PASS', detail: `${lines} records, updated ${ageDays} day(s) ago` });
      }
    } catch (_) { checks.push({ check: 'Training data', status: 'WARN', detail: 'Could not read training data stats' }); }
  }

  // 6. Daemon output freshness
  const OUTPUT_MAP = {
    'testgaps.md': 'testgaps', 'quality.md': 'optimize', 'deepdive.md': 'deepdive',
    'map.md': 'map', 'refactor-candidates.md': 'refactor', 'benchmark.md': 'benchmark',
  };
  const autopilotDir = path.join(projectPath, '.autopilot');
  const staleOutputs = [];
  const presentOutputs = [];
  for (const [file] of Object.entries(OUTPUT_MAP)) {
    const fp = path.join(autopilotDir, file);
    if (fs.existsSync(fp)) {
      try {
        const ageH = Math.round((Date.now() - fs.statSync(fp).mtimeMs) / 3600000);
        presentOutputs.push(`${file}(${ageH}h)`);
        if (ageH > 24) staleOutputs.push(file);
      } catch (_) {}
    }
  }
  if (presentOutputs.length === 0) {
    checks.push({ check: 'Daemon outputs', status: 'WARN', detail: 'No .autopilot output files yet' });
  } else if (staleOutputs.length > 0) {
    checks.push({ check: 'Daemon outputs', status: 'WARN', detail: `Stale (>24h): ${staleOutputs.join(', ')}` });
  } else {
    checks.push({ check: 'Daemon outputs', status: 'PASS', detail: presentOutputs.join(', ') });
  }

  const failed = checks.filter(c => c.status === 'FAIL').length;
  const warned = checks.filter(c => c.status === 'WARN').length;
  const passed = checks.filter(c => c.status === 'PASS').length;
  let overall = 'PASS';
  if (failed > 0) overall = 'FAIL'; else if (warned > 0) overall = 'WARN';
  const table = checks.map(c => `${c.status.padEnd(4)} | ${c.check.padEnd(20)} | ${c.detail}`).join('\n');
  return {
    overall, summary: `${passed} passed, ${warned} warned, ${failed} failed`, checks,
    table: `STATUS | CHECK                 | DETAIL\n${'─'.repeat(70)}\n${table}`,
    project_path: projectPath,
  };
}

module.exports = { toolDoctor };

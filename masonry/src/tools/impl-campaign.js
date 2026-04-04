'use strict';

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const { loadConfig } = require('./config');
const { httpRequest } = require('./impl-utils');

const GIT_DIFF_PATTERNS = [
  { name: 'concurrency', pattern: /concurrent|asyncio|threading|lock|mutex|race/i, domain: 'D4', mode: 'diagnose', template: 'Does {file} handle concurrent access safely under {pattern} conditions?' },
  { name: 'fee_calculation', pattern: /fee|price|cost|rate|amount|decimal|round/i, domain: 'D1', mode: 'validate', template: 'Are fee/price calculations in {file} numerically accurate? Check for floating-point or rounding errors.' },
  { name: 'migration', pattern: /migration|alembic|schema|alter table|add column/i, domain: 'D2', mode: 'diagnose', template: 'Does the migration in {file} handle rollback correctly? What happens if it fails mid-run?' },
  { name: 'auth', pattern: /auth|jwt|token|session|permission|role|acl/i, domain: 'D6', mode: 'audit', template: 'Does {file} enforce authorization checks correctly? Are there privilege escalation risks?' },
  { name: 'cache', pattern: /cache|redis|memcache|ttl|invalidat/i, domain: 'D4', mode: 'diagnose', template: 'What happens in {file} when the cache is cold, stale, or unavailable?' },
  { name: 'retry', pattern: /retry|backoff|circuit.?breaker|timeout|deadline/i, domain: 'D5', mode: 'benchmark', template: 'Does the retry/timeout logic in {file} prevent cascading failures under load?' },
  { name: 'deps', pattern: /requirements|package\.json|pyproject|go\.mod|Cargo\.toml/i, domain: 'D3', mode: 'research', template: 'Do the dependency changes in {file} introduce breaking changes or security vulnerabilities?' },
];

function toolStatus(args) {
  const { project_path } = args;
  const projectName = path.basename(project_path);
  const stateFile = path.join(project_path, 'masonry-state.json');
  const configFile = path.join(project_path, 'masonry.json');

  let state = null;
  let masonryConfig = null;
  try {
    if (fs.existsSync(stateFile)) state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  } catch (_err) {}
  try {
    if (fs.existsSync(configFile)) masonryConfig = JSON.parse(fs.readFileSync(configFile, 'utf8'));
  } catch (_err) {}

  if (!state) {
    return {
      status: 'no_campaign',
      project: (masonryConfig && masonryConfig.name) || projectName,
      ...(masonryConfig ? { mode: masonryConfig.mode } : {}),
    };
  }

  const result = {
    project: (masonryConfig && masonryConfig.name) || projectName,
    ...(masonryConfig ? { mode: masonryConfig.mode } : {}),
    ...state,
  };

  const recallInjectionPath = path.join(project_path, '.autopilot', 'recall-injection.json');
  try {
    if (fs.existsSync(recallInjectionPath)) {
      const injection = JSON.parse(fs.readFileSync(recallInjectionPath, 'utf8'));
      const ageMs = Date.now() - new Date(injection.timestamp || 0).getTime();
      if (ageMs < 30 * 60 * 1000 && Array.isArray(injection.patterns) && injection.patterns.length > 0) {
        result.recall_patterns = injection.patterns;
        result.recall_query = injection.query;
        result.recall_synced_at = injection.timestamp;
      }
    }
  } catch (_) {}

  const topoFile = path.join(project_path, '.autopilot', 'topology');
  if (fs.existsSync(topoFile)) result.topology = fs.readFileSync(topoFile, 'utf8').trim();

  return result;
}

function toolFindings(args) {
  const { project_path, limit = 10, verdict_filter } = args;
  const findingsDir = path.join(project_path, 'findings');
  if (!fs.existsSync(findingsDir)) return [];

  let files;
  try {
    files = fs.readdirSync(findingsDir)
      .filter(f => f.endsWith('.md') && f !== 'synthesis.md' && !f.startsWith('synthesis'))
      .map(f => {
        const fullPath = path.join(findingsDir, f);
        let mtime = 0;
        try { mtime = fs.statSync(fullPath).mtimeMs; } catch (_) {}
        return { file: f, fullPath, mtime };
      })
      .sort((a, b) => b.mtime - a.mtime);
  } catch (_) { return []; }

  const results = [];
  for (const { file, fullPath } of files) {
    if (results.length >= limit) break;
    let content = '';
    try { content = fs.readFileSync(fullPath, 'utf8'); } catch (_) { continue; }

    const verdictMatch = content.match(/\*\*Verdict\*\*:\s*([^\n]+)/i);
    const agentMatch = content.match(/\*\*Agent\*\*:\s*([^\n]+)/i);
    const rawVerdict = verdictMatch ? verdictMatch[1].trim() : 'UNKNOWN';
    const verdictClean = rawVerdict.match(/^[A-Z_]+/);
    const verdict = verdictClean ? verdictClean[0] : 'UNKNOWN';
    const agent = agentMatch ? agentMatch[1].trim() : '';

    if (verdict_filter && verdict.toUpperCase() !== verdict_filter.toUpperCase()) continue;

    const id = file.replace(/\.md$/, '');
    const lines = content.split('\n');
    let summary = '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('**') && !trimmed.startsWith('```')) {
        summary = trimmed.slice(0, 120);
        break;
      }
    }
    results.push({ id, verdict, agent, summary, path: fullPath });
  }
  return results;
}

function toolQuestions(args) {
  const { project_path, status_filter, limit = 20 } = args;
  const questionsFile = path.join(project_path, 'questions.md');
  if (!fs.existsSync(questionsFile)) return [];

  let content = '';
  try { content = fs.readFileSync(questionsFile, 'utf8'); } catch (_) { return []; }

  const QUESTION_ID = /^[A-Z]{1,3}\d[\d.]*[\s:\[]/;
  const blocks = content.split(/^#{2,3} /m).filter(Boolean);
  const results = [];

  for (const block of blocks) {
    if (results.length >= limit) break;
    const lines = block.split('\n');
    const firstLine = lines[0].trim();
    if (!QUESTION_ID.test(firstLine)) continue;

    const statusMatch = block.match(/\*\*Status\*\*:\s*([^\n]+)/i);
    const modeMatch = block.match(/\*\*(?:Operational )?Mode\*\*:\s*([^\n]+)/i);
    const agentMatch = block.match(/\*\*Agent\*\*:\s*([^\n]+)/i);
    if (!statusMatch) continue;

    const status = statusMatch[1].trim();
    const mode = modeMatch ? modeMatch[1].trim() : '';
    const agent = agentMatch ? agentMatch[1].trim() : '';
    if (status_filter && status.toUpperCase() !== status_filter.toUpperCase()) continue;

    const textLines = lines.slice(1).filter(l => {
      const t = l.trim();
      return t && !t.startsWith('**Status**') && !t.startsWith('**Mode**') && !t.startsWith('**Agent**');
    }).slice(0, 3);

    const text = textLines.join(' ').trim().slice(0, 200);
    results.push({ id: firstLine, status, mode, agent, text });
  }
  return results;
}

function toolRun(args) {
  const { project_path, mode = 'resume' } = args;
  const cfg = loadConfig();

  const prompt = mode === 'new'
    ? 'Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md and project-brief.md. Begin the campaign from the first PENDING question. NEVER STOP.'
    : 'Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md, project-brief.md, and findings/synthesis.md. Resume the campaign from the first PENDING question. NEVER STOP.';

  const env = { ...process.env };
  if (cfg.recallApiKey) env.RECALL_API_KEY = cfg.recallApiKey;

  const child = spawn('claude', ['--dangerously-skip-permissions', prompt], {
    cwd: project_path,
    env,
    detached: true,
    stdio: 'ignore',
  });
  child.unref();
  return { launched: true, pid: child.pid, mode, project_path };
}

function toolWeights(args) {
  const { project_path } = args;
  const weightsFile = path.join(project_path, '.bl-weights.json');
  if (!fs.existsSync(weightsFile)) {
    return { report: 'No weights file found — run a campaign first to build verdict history.', weights: [] };
  }
  let weights = {};
  try { weights = JSON.parse(fs.readFileSync(weightsFile, 'utf8')); } catch (_) {
    return { error: 'Failed to parse .bl-weights.json' };
  }

  const entries = Object.entries(weights).map(([id, w]) => ({
    id, weight: w.weight || 1.0, runs: w.runs || 0, failures: w.failures || 0,
    warnings: w.warnings || 0, last_verdict: w.last_verdict || null,
  }));
  entries.sort((a, b) => b.weight - a.weight);
  const high = entries.filter(e => e.weight >= 1.5);
  const normal = entries.filter(e => e.weight >= 0.3 && e.weight < 1.5);
  const prune = entries.filter(e => e.weight < 0.3);
  return {
    total: entries.length, high_signal: high.length, normal: normal.length, prunable: prune.length,
    top_priority: high.slice(0, 10), prunable_ids: prune.map(e => e.id), weights: entries,
  };
}

function toolFleet(args) {
  const { project_path, limit = 30 } = args;
  const registryFile = path.join(project_path, 'registry.json');
  const agentDbFile = path.join(project_path, 'agent_db.json');

  let agents = [];
  let scores = {};
  try {
    if (fs.existsSync(registryFile)) {
      const raw = JSON.parse(fs.readFileSync(registryFile, 'utf8'));
      agents = Array.isArray(raw) ? raw : (raw.agents || []);
    }
  } catch (_) {}
  try {
    if (fs.existsSync(agentDbFile)) {
      const db = JSON.parse(fs.readFileSync(agentDbFile, 'utf8'));
      for (const [name, data] of Object.entries(db)) scores[name] = data.score || data.avg_score || 0;
    }
  } catch (_) {}

  for (const agent of agents) {
    if (scores[agent.name || ''] !== undefined) agent.score = scores[agent.name];
  }
  agents.sort((a, b) => (b.score || 0) - (a.score || 0));
  return { agents: agents.slice(0, limit), count: Math.min(agents.length, limit), total: agents.length, has_scores: Object.keys(scores).length > 0 };
}

module.exports = { toolStatus, toolFindings, toolQuestions, toolRun, toolWeights, toolFleet, GIT_DIFF_PATTERNS };

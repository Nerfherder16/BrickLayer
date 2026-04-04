'use strict';

const fs = require('fs');
const path = require('path');
const { REPO_ROOT } = require('./impl-utils');

function toolWorkerStatus(args) {
  const { project_path } = args;
  const daemonDir = path.join(REPO_ROOT, 'masonry', 'src', 'daemon');
  const pidsDir = path.join(daemonDir, 'pids');
  const logsDir = path.join(daemonDir, 'logs');
  const autopilotDir = path.join(project_path, '.autopilot');

  const WORKERS = ['testgaps', 'optimize', 'consolidate', 'deepdive'];
  const OUTPUT_FILES = { testgaps: 'testgaps.md', optimize: 'quality.md', consolidate: null, deepdive: 'deepdive.md' };

  const status = {};
  for (const worker of WORKERS) {
    const pidFile = path.join(pidsDir, `${worker}.pid`);
    let running = false;
    let pid = null;
    if (fs.existsSync(pidFile)) {
      try {
        pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10);
        try { process.kill(pid, 0); running = true; } catch (_) { running = false; }
      } catch (_) {}
    }
    let lastRunAt = null;
    const logFile = path.join(logsDir, `${worker}.log`);
    if (fs.existsSync(logFile)) {
      try { lastRunAt = new Date(fs.statSync(logFile).mtime).toISOString(); } catch (_) {}
    }
    let outputFile = null;
    let outputAge = null;
    if (OUTPUT_FILES[worker]) {
      const outPath = path.join(autopilotDir, OUTPUT_FILES[worker]);
      if (fs.existsSync(outPath)) {
        outputFile = outPath;
        try {
          const ageMs = Date.now() - fs.statSync(outPath).mtimeMs;
          outputAge = Math.round(ageMs / 60000) + 'min ago';
        } catch (_) {}
      }
    }
    status[worker] = { running, pid, last_run_at: lastRunAt, output_file: outputFile, output_age: outputAge };
  }
  return { workers: status, daemon_dir: daemonDir, project_path };
}

function toolTaskAssign(args) {
  const { project_path, worker_id } = args;
  const progressFile = path.join(project_path, '.autopilot', 'progress.json');
  if (!fs.existsSync(progressFile)) return { task: null, reason: 'No .autopilot/progress.json found' };

  let progress;
  try { progress = JSON.parse(fs.readFileSync(progressFile, 'utf8')); } catch (err) {
    return { task: null, error: `Failed to parse progress.json: ${err.message}` };
  }

  const pending = (progress.tasks || []).find(t => t.status === 'PENDING');
  if (!pending) {
    const inProgress = (progress.tasks || []).filter(t => t.status === 'IN_PROGRESS');
    const done = (progress.tasks || []).filter(t => t.status === 'DONE');
    const blocked = (progress.tasks || []).filter(t => t.status === 'BLOCKED');
    const reason = inProgress.length > 0 ? 'all_in_progress' : blocked.length > 0 ? 'waiting_on_dependencies' : 'all_done';
    return {
      task: null, reason,
      in_progress_count: inProgress.length, done_count: done.length, blocked_count: blocked.length,
      blocked_tasks: blocked.map(t => ({ id: t.id, description: t.description, depends_on: t.depends_on })),
      total: (progress.tasks || []).length,
    };
  }

  pending.status = 'IN_PROGRESS';
  if (worker_id) pending.claimed_by = worker_id;
  pending.claimed_at = new Date().toISOString();
  progress.updated_at = new Date().toISOString();

  try { fs.writeFileSync(progressFile, JSON.stringify(progress, null, 2), 'utf8'); } catch (err) {
    return { task: null, error: `Failed to write progress.json: ${err.message}` };
  }

  const blocked = (progress.tasks || []).filter(t => t.status === 'BLOCKED');
  return {
    task: pending,
    total_tasks: (progress.tasks || []).length,
    pending_remaining: (progress.tasks || []).filter(t => t.status === 'PENDING').length,
    blocked_count: blocked.length,
    note: blocked.length > 0 ? `${blocked.length} task(s) are BLOCKED waiting on depends_on` : undefined,
  };
}

function toolAgentHealth(args) {
  const { project_path, agent_name, sort_by = 'score' } = args;
  const agentDbFile = path.join(project_path, 'agent_db.json');
  const registryFile = path.join(REPO_ROOT, 'masonry', 'agent_registry.yml');

  let db = {};
  let registry = [];
  try { if (fs.existsSync(agentDbFile)) db = JSON.parse(fs.readFileSync(agentDbFile, 'utf8')); } catch (_) {}

  try {
    if (fs.existsSync(registryFile)) {
      const lines = fs.readFileSync(registryFile, 'utf8').split('\n');
      let current = null;
      for (const line of lines) {
        const nameMatch = line.match(/^  - name:\s+(.+)/);
        if (nameMatch) { if (current) registry.push(current); current = { name: nameMatch[1].trim() }; }
        else if (current) {
          const tierMatch = line.match(/^\s+tier:\s+(.+)/);
          const dspyMatch = line.match(/^\s+dspy_optimized:\s+(.+)/);
          if (tierMatch) current.tier = tierMatch[1].trim();
          if (dspyMatch) current.dspy_optimized = dspyMatch[1].trim() === 'true';
        }
      }
      if (current) registry.push(current);
    }
  } catch (_) {}

  const merged = registry.map(r => {
    const dbEntry = db[r.name] || {};
    return {
      name: r.name, tier: r.tier || 'unknown', dspy_optimized: r.dspy_optimized || false,
      score: dbEntry.score ?? dbEntry.avg_score ?? null,
      runs: dbEntry.runs ?? dbEntry.total_runs ?? 0,
      pass_rate: dbEntry.pass_rate ?? null,
      last_run: dbEntry.last_run ?? dbEntry.updated_at ?? null,
    };
  });

  for (const [name, dbEntry] of Object.entries(db)) {
    if (!merged.find(m => m.name === name)) {
      merged.push({
        name, tier: 'unknown', dspy_optimized: false,
        score: dbEntry.score ?? dbEntry.avg_score ?? null,
        runs: dbEntry.runs ?? dbEntry.total_runs ?? 0,
        pass_rate: dbEntry.pass_rate ?? null,
        last_run: dbEntry.last_run ?? dbEntry.updated_at ?? null,
      });
    }
  }

  if (agent_name) {
    const found = merged.find(m => m.name === agent_name);
    return found ? { agent: found } : { error: `Agent '${agent_name}' not found` };
  }

  const sortFn = {
    score: (a, b) => (b.score ?? -1) - (a.score ?? -1),
    runs: (a, b) => (b.runs ?? 0) - (a.runs ?? 0),
    pass_rate: (a, b) => (b.pass_rate ?? -1) - (a.pass_rate ?? -1),
    last_run: (a, b) => (b.last_run || '').localeCompare(a.last_run || ''),
  }[sort_by] || ((a, b) => (b.score ?? -1) - (a.score ?? -1));

  merged.sort(sortFn);
  return { agents: merged, total: merged.length, optimized: merged.filter(m => m.dspy_optimized).length, sort_by };
}

function toolWaveValidate(args) {
  const { project_path, wave_task_ids } = args;
  const progressFile = path.join(project_path, '.autopilot', 'progress.json');
  if (!fs.existsSync(progressFile)) return { valid: false, error: 'No .autopilot/progress.json found' };

  let progress;
  try { progress = JSON.parse(fs.readFileSync(progressFile, 'utf8')); } catch (err) {
    return { valid: false, error: `Failed to parse progress.json: ${err.message}` };
  }

  const taskMap = {};
  for (const t of (progress.tasks || [])) taskMap[t.id] = t;

  const waveTasks = wave_task_ids.map(id => taskMap[id] || { id, status: 'NOT_FOUND' });
  const blocking = waveTasks.filter(t => t.status !== 'DONE');
  const allDone = blocking.length === 0;

  return {
    valid: allDone, safe_to_advance: allDone, wave_task_ids,
    blocking_tasks: blocking.map(t => ({ id: t.id, status: t.status, description: t.description || null })),
    done_count: waveTasks.length - blocking.length, total_wave_tasks: waveTasks.length,
    overall_progress: {
      total: (progress.tasks || []).length,
      done: (progress.tasks || []).filter(t => t.status === 'DONE').length,
      in_progress: (progress.tasks || []).filter(t => t.status === 'IN_PROGRESS').length,
      pending: (progress.tasks || []).filter(t => t.status === 'PENDING').length,
    },
    tests: progress.tests || null,
  };
}

function toolSwarmInit(args) {
  const { project_path, spec_path, project_name } = args;
  const autopilotDir = path.join(project_path, '.autopilot');
  const specFile = spec_path || path.join(autopilotDir, 'spec.md');

  if (!fs.existsSync(specFile)) return { initialized: false, error: `Spec file not found: ${specFile}` };

  let specContent;
  try { specContent = fs.readFileSync(specFile, 'utf8'); } catch (err) {
    return { initialized: false, error: `Failed to read spec: ${err.message}` };
  }

  const tasks = [];
  const lines = specContent.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(/^[-*]\s+\[[ x]\]\s+(?:\*\*)?(?:Task\s+)?(\d+)(?:\.\*\*)?\s*[:\-—]\s*(.+?)(?:\s+\[mode:(\w+)\])?$/i);
    if (m) {
      const task = { id: parseInt(m[1], 10), description: m[2].replace(/\*\*/g, '').trim(), status: 'PENDING', mode: m[3] || 'default' };
      for (let j = i + 1; j <= i + 3 && j < lines.length; j++) {
        const nextLine = lines[j].trim();
        if (!nextLine) break;
        const depsMatch = nextLine.match(/^depends_on:\s*(\[.*?\])/);
        if (depsMatch) { try { task.depends_on = JSON.parse(depsMatch[1]); } catch (_) {} break; }
        if (/^[-*]\s+\[[ x]\]/.test(nextLine)) break;
      }
      tasks.push(task);
    }
  }

  if (tasks.length === 0) {
    let taskNum = 1;
    for (const line of lines) {
      const fm = line.match(/^[-*]\s+\[[ x]\]\s+(.+)/);
      if (fm && !fm[1].startsWith('#')) {
        tasks.push({ id: taskNum++, description: fm[1].replace(/\*\*/g, '').trim(), status: 'PENDING', mode: 'default' });
      }
    }
  }

  if (tasks.length === 0) return { initialized: false, error: "No tasks found in spec. Expected '- [ ] **Task N** — description' format." };

  const taskIds = new Set(tasks.map(t => t.id));
  for (const task of tasks) {
    if (Array.isArray(task.depends_on) && task.depends_on.length > 0 && task.depends_on.some(depId => taskIds.has(depId))) {
      task.status = 'BLOCKED';
    }
  }

  const name = project_name || path.basename(project_path);
  const dateSuffix = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const progress = {
    project: name, status: 'BUILDING', branch: `autopilot/${name}-${dateSuffix}`,
    tasks, tests: { total: 0, passing: 0, failing: 0 }, updated_at: new Date().toISOString(),
  };

  try {
    fs.mkdirSync(autopilotDir, { recursive: true });
    fs.writeFileSync(path.join(autopilotDir, 'progress.json'), JSON.stringify(progress, null, 2), 'utf8');
    fs.writeFileSync(path.join(autopilotDir, 'mode'), 'build', 'utf8');
  } catch (err) {
    return { initialized: false, error: `Failed to write progress.json: ${err.message}` };
  }

  let topology = 'hierarchical';
  const tasksWithDeps = tasks.filter(t => t.depends_on && t.depends_on.length > 0);
  if (tasksWithDeps.length > 0) {
    const isLinear = tasks.every((t, i) => {
      if (i === 0) return !t.depends_on || t.depends_on.length === 0;
      return t.depends_on && t.depends_on.length === 1 && t.depends_on[0] === tasks[i - 1].id;
    });
    if (isLinear) {
      topology = 'ring';
    } else {
      const depRefCount = {};
      for (const t of tasksWithDeps) for (const dep of t.depends_on) depRefCount[dep] = (depRefCount[dep] || 0) + 1;
      topology = Object.values(depRefCount).some(c => c > 1) ? 'mesh' : 'hybrid';
    }
  }

  return { initialized: true, tasks, task_count: tasks.length, project: name, branch: progress.branch, topology };
}

module.exports = { toolWorkerStatus, toolTaskAssign, toolAgentHealth, toolWaveValidate, toolSwarmInit };

#!/usr/bin/env node
/**
 * PostToolUse:Agent hook (Masonry): Telemetry — fires when a Claude agent sub-task completes.
 *
 * Reads the task_id written by masonry-pre-task.js, computes duration from the
 * pre-phase record in telemetry.jsonl, and appends a post-phase record.
 *
 * Skips silently for BrickLayer research projects (program.md + questions.md).
 * Skips silently if no .autopilot/ directory or current-task-id file is found.
 */

"use strict";
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function isResearchProject(dir) {
  return (
    fs.existsSync(path.join(dir, "program.md")) &&
    fs.existsSync(path.join(dir, "questions.md"))
  );
}

function findAutopilotDir(startDir) {
  let dir = startDir;
  for (let i = 0; i < 10; i++) {
    const candidate = path.join(dir, ".autopilot");
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

// Bayesian confidence update
function updatePatternConfidence(autopilotDir, taskType, success) {
  const confPath = path.join(autopilotDir, 'pattern-confidence.json');
  let store = {};
  try { store = JSON.parse(fs.readFileSync(confPath, 'utf8')); } catch {}

  const key = taskType || 'general';
  const now = new Date().toISOString();

  if (!store[key]) {
    store[key] = { confidence: 0.7, last_used: now, uses: 0 };
  }

  const entry = store[key];
  const c = entry.confidence;

  if (success) {
    entry.confidence = Math.min(1.0, c + 0.20 * (1 - c));
  } else {
    entry.confidence = Math.max(0.0, c - 0.15 * c);
  }
  entry.last_used = now;
  entry.uses = (entry.uses || 0) + 1;

  try {
    fs.writeFileSync(confPath, JSON.stringify(store, null, 2), 'utf8');
  } catch {}
}

// Mid-build recall sync — every N=5 completed tasks
// Queries ReasoningBank for patterns relevant to the next pending task and writes
// .autopilot/recall-injection.json for the orchestrator to pick up.
function maybeSyncRecall(autopilotDir, projectDir) {
  const SYNC_INTERVAL = 5;
  try {
    const progressPath = path.join(autopilotDir, 'progress.json');
    if (!fs.existsSync(progressPath)) return;
    const progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
    const doneTasks = (progress.tasks || []).filter(t => t.status === 'DONE').length;

    // Only fire at exact multiples of SYNC_INTERVAL (5, 10, 15, …)
    if (doneTasks <= 0 || doneTasks % SYNC_INTERVAL !== 0) return;

    // Use next pending task description as the query, fall back to generic
    const pendingTask = (progress.tasks || []).find(t => t.status === 'PENDING');
    const query = pendingTask
      ? pendingTask.description.slice(0, 100)
      : 'build task';

    const bankPath = path.join(__dirname, '../../src/reasoning/bank.py');
    if (!fs.existsSync(bankPath)) return;

    const proc = spawn('python', [bankPath, 'query', query, '3'], {
      detached: true,
      stdio: ['ignore', 'pipe', 'ignore'],
      cwd: projectDir,
    });

    let output = '';
    proc.stdout.on('data', d => { output += d; });
    proc.on('close', () => {
      try {
        const patterns = JSON.parse(output.trim());
        if (!Array.isArray(patterns)) return;
        fs.writeFileSync(
          path.join(autopilotDir, 'recall-injection.json'),
          JSON.stringify({
            timestamp: new Date().toISOString(),
            patterns,
            query,
            done_count: doneTasks,
          }),
          'utf8'
        );
      } catch (_) { /* non-fatal — output may be empty or malformed */ }
    });
    proc.unref();
  } catch (_) { /* non-fatal — never blocks the hook */ }
}

async function main() {
  const raw = await readStdin();
  let parsed = {};
  try { parsed = JSON.parse(raw); } catch { process.exit(0); }

  const cwd = parsed.cwd || process.env.PWD || process.cwd();

  // Silent in BrickLayer research projects
  if (isResearchProject(cwd)) process.exit(0);

  const autopilotDir = findAutopilotDir(cwd);
  if (!autopilotDir) process.exit(0);

  // Read the task_id written by the pre hook
  const taskIdFile = path.join(autopilotDir, "current-task-id");
  if (!fs.existsSync(taskIdFile)) process.exit(0);
  let task_id;
  try {
    task_id = fs.readFileSync(taskIdFile, "utf8").trim();
  } catch { process.exit(0); }
  if (!task_id) process.exit(0);

  // Read telemetry.jsonl to find the pre-phase record and compute duration
  let duration_ms = null;
  const telemetryFile = path.join(autopilotDir, "telemetry.jsonl");
  try {
    if (fs.existsSync(telemetryFile)) {
      const lines = fs.readFileSync(telemetryFile, "utf8").split("\n");
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const entry = JSON.parse(line);
          if (entry.task_id === task_id && entry.phase === "pre") {
            duration_ms = Date.now() - Date.parse(entry.timestamp);
            break;
          }
        } catch { /* skip malformed lines */ }
      }
    }
  } catch { /* non-fatal */ }

  // Determine success from tool_result
  const resultStr = JSON.stringify(parsed.tool_result || "");
  const success = !/ERROR|FAILED|DEV_ESCALATE/.test(resultStr);

  const agent = (parsed.tool_input && parsed.tool_input.subagent_type) || "unknown";

  // Bayesian confidence update
  updatePatternConfidence(autopilotDir, agent, success);

  // Fire-and-forget: record pattern co-citations in ReasoningBank graph
  try {
    if (success && task_id) {
      // Derive project name from the directory containing .autopilot/
      const projectDir = path.dirname(autopilotDir);
      const project = path.basename(projectDir) || "unknown";

      // Extract pattern IDs from tool_result if present; fall back to empty
      let patternIds = [];
      try {
        const toolResult = parsed.tool_result;
        if (toolResult && typeof toolResult === "object" && Array.isArray(toolResult.pattern_ids)) {
          patternIds = toolResult.pattern_ids.map(String).filter(Boolean);
        }
      } catch (_) { /* no patterns available — skip silently */ }

      // graph.py requires at least 2 patterns to create edges; pass what we have
      // (the Python side no-ops if < 2 are provided)
      const graphPath = path.join(__dirname, "../../src/reasoning/graph.py");
      const args = ["python", [graphPath, project, task_id, ...patternIds]];
      const proc = spawn(args[0], args[1], {
        detached: true,
        stdio: "ignore",
        cwd: projectDir,
      });
      proc.unref();
    } else {
      // Debug note: skip graph recording — task not successful or task_id missing
    }
  } catch (_) { /* non-fatal — graph recording never blocks the hook */ }

  // Mid-build recall sync — every N=5 completed tasks
  if (success) {
    maybeSyncRecall(autopilotDir, path.dirname(autopilotDir));
  }

  // On first task completion, run topology selector if not already set
  const topoFile = path.join(autopilotDir, 'topology');
  if (!fs.existsSync(topoFile)) {
    try {
      const progressPath = path.join(autopilotDir, 'progress.json');
      if (fs.existsSync(progressPath)) {
        const progress = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
        if (progress.tasks) {
          // Walk up to find the masonry/ project root for the selector script
          let searchDir = path.dirname(autopilotDir);
          let projectRoot = searchDir;
          for (let i = 0; i < 10; i++) {
            if (fs.existsSync(path.join(searchDir, 'masonry'))) {
              projectRoot = searchDir;
              break;
            }
            const parent = path.dirname(searchDir);
            if (parent === searchDir) break;
            searchDir = parent;
          }
          const selectorPath = path.join(projectRoot, 'masonry/src/topology/selector.py');
          if (fs.existsSync(selectorPath)) {
            const { execSync } = require('child_process');
            const result = execSync(
              `python "${selectorPath}" '${JSON.stringify({ tasks: progress.tasks })}'`,
              { cwd: projectRoot, timeout: 5000, stdio: 'pipe' }
            ).toString().trim();
            const topo = JSON.parse(result);
            fs.writeFileSync(topoFile, topo.topology, 'utf8');
          }
        }
      }
    } catch (_) { /* non-fatal — topology is advisory */ }
  }

  // Auto-trigger training collector if telemetry was updated in the last 60 seconds
  try {
    const telemetryStat = fs.existsSync(telemetryFile) ? fs.statSync(telemetryFile) : null;
    if (telemetryStat && (Date.now() - telemetryStat.mtimeMs) < 60000) {
      // Walk up from autopilotDir to find the masonry/ directory (project root)
      let searchDir = path.dirname(autopilotDir);
      let projectRoot = searchDir;
      for (let i = 0; i < 10; i++) {
        if (fs.existsSync(path.join(searchDir, "masonry"))) {
          projectRoot = searchDir;
          break;
        }
        const parent = path.dirname(searchDir);
        if (parent === searchDir) break;
        searchDir = parent;
      }
      const collectorPath = path.join(__dirname, "../../src/training/collector.py");
      spawn("python", [collectorPath], { cwd: projectRoot, detached: true, stdio: "ignore" }).unref();
    }
  } catch (_) { /* non-fatal — silently skip */ }

  const record = JSON.stringify({
    task_id,
    phase: "post",
    timestamp: new Date().toISOString(),
    duration_ms,
    success,
    agent,
  });

  try {
    fs.appendFileSync(telemetryFile, record + "\n", "utf8");
  } catch (_) { /* non-fatal */ }

  process.exit(0);
}

main().catch(() => process.exit(0));

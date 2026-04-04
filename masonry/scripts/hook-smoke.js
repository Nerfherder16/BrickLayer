#!/usr/bin/env node
/**
 * hook-smoke.js — Fast smoke test for all registered Claude Code hooks.
 *
 * Reads ~/.claude/settings.json, validates every registered hook for:
 *   1. File existence
 *   2. Node.js syntax (node --check)
 *   3. Load crash (pipe sample input, check exit code != 1)
 *   4. Async/block consistency (exit(2) in async hooks is silently swallowed)
 *   5. Stdout pollution (must be empty or valid JSON)
 *
 * Also reads runner scripts (masonry-stop-runner, masonry-post-write-runner)
 * and tests the hooks embedded in their BACKGROUND_HOOKS arrays.
 *
 * Usage: node masonry/scripts/hook-smoke.js
 * Exit:  0 = all PASS/WARN  |  1 = any FAIL
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');
const { spawnSync, spawn } = require('child_process');

const HOME         = os.homedir();
const SETTINGS     = path.join(HOME, '.claude', 'settings.json');
const HOOK_TIMEOUT = 15000; // ms per hook

// ─── ANSI colours ────────────────────────────────────────────────────────────
const USE_COLOR = process.stdout.isTTY;
const C = {
  reset:  USE_COLOR ? '\x1b[0m'  : '',
  green:  USE_COLOR ? '\x1b[32m' : '',
  yellow: USE_COLOR ? '\x1b[33m' : '',
  red:    USE_COLOR ? '\x1b[31m' : '',
  bold:   USE_COLOR ? '\x1b[1m'  : '',
  dim:    USE_COLOR ? '\x1b[2m'  : '',
};

// ─── Sample inputs per event type ────────────────────────────────────────────
const SAMPLES = {
  PreToolUse:
    '{"tool_name":"Write","tool_input":{"file_path":"/tmp/smoke-test.txt","content":"hello"},"session_id":"smoke"}',
  PostToolUse:
    '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/smoke-test.txt","old_string":"x","new_string":"y"},"tool_response":"ok","session_id":"smoke"}',
  Stop:
    '{"session_id":"smoke","cwd":"/tmp","transcript_path":"/tmp/smoke.jsonl"}',
  SessionStart:
    '{"session_id":"smoke","cwd":"/tmp"}',
  SessionEnd:
    '{"session_id":"smoke","cwd":"/tmp"}',
  PreCompact:
    '{"session_id":"smoke","cwd":"/tmp"}',
  PostCompact:
    '{"session_id":"smoke","cwd":"/tmp","summary":"test summary"}',
  UserPromptSubmit:
    '{"session_id":"smoke","prompt":"hello world","cwd":"/tmp"}',
  SubagentStart:
    '{"session_id":"smoke","cwd":"/tmp"}',
  SubagentStop:
    '{"session_id":"smoke","cwd":"/tmp"}',
  TeammateIdle:
    '{"session_id":"smoke","cwd":"/tmp"}',
  TaskCompleted:
    '{"session_id":"smoke","cwd":"/tmp"}',
  PostToolUseFailure:
    '{"tool_name":"Bash","tool_input":{"command":"ls"},"error":"failed","session_id":"smoke"}',
  Notification:
    '{"session_id":"smoke","message":"test"}',
};

// ─── Path helpers ─────────────────────────────────────────────────────────────
function expandPath(p) {
  if (!p) return p;
  if (p.startsWith('~/')) return path.join(HOME, p.slice(2));
  return p;
}

// Known Claude Code event names — if an extracted "path" matches one of these,
// it's an argument to the previous script, not a path itself.
const EVENT_NAMES = new Set([
  'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'Stop', 'SessionStart',
  'SessionEnd', 'UserPromptSubmit', 'SubagentStart', 'SubagentStop',
  'TeammateIdle', 'TaskCompleted', 'PreCompact', 'PostCompact',
  'Notification', 'ExitPlanMode', 'Agent',
]);

/**
 * Extract the script path from a hook command string.
 * Handles:
 *   ~/.claude/monitors/hook-timer.sh <label> node <path>
 *   ~/.claude/monitors/hook-timer.sh <label> bash <path.sh> <args...>
 *   node <path>
 *   bash <path.sh> <args...>
 * Returns { scriptPath, isBash }
 */
function parseHookCommand(cmd) {
  if (!cmd) return { scriptPath: null, isBash: false };

  const parts = cmd.trim().split(/\s+/);

  // hook-timer.sh wrapper: hook-timer.sh <label> <cmd> <path> [args...]
  const timerIdx = parts.findIndex(p => p.includes('hook-timer.sh'));
  if (timerIdx !== -1) {
    // inner[0] = label, inner[1] = cmd ('node'|'bash'|...), inner[2] = path
    const inner = parts.slice(timerIdx + 1);
    if (inner.length >= 3) {
      const innerCmd = inner[1];
      const rawPath  = inner[2];

      // If the "path" is actually an event name, the script IS inner[1] (e.g. a .sh)
      // e.g. hook-timer.sh better-hook ~/.tmux/.../better-hook.sh UserPromptSubmit
      if (EVENT_NAMES.has(rawPath)) {
        // inner[1] is actually the script path
        const scriptPath = expandPath(inner[1]);
        return { scriptPath, isBash: true };
      }

      const scriptPath = expandPath(rawPath);
      const isBash = innerCmd === 'bash' || scriptPath.endsWith('.sh');
      return { scriptPath, isBash };
    }
    return { scriptPath: null, isBash: false };
  }

  // Direct: node <path>
  if (parts[0] === 'node' && parts.length >= 2) {
    return { scriptPath: expandPath(parts[1]), isBash: false };
  }

  // Direct bash or .sh
  if (parts[0] === 'bash' || (parts[0] && parts[0].endsWith('.sh'))) {
    const scriptPath = expandPath(parts[0] === 'bash' ? parts[1] : parts[0]);
    return { scriptPath, isBash: true };
  }

  return { scriptPath: null, isBash: false };
}

// ─── Runner extraction ────────────────────────────────────────────────────────
/**
 * Parse BACKGROUND_HOOKS from a runner script source.
 * Returns array of { name, scriptPath, isBash }
 *
 * Handles both:
 *   [`${HOME}/path/to/script.js`]
 *   [path.join(HOOKS_DIR, 'script.js')]
 */
function extractRunnerHooks(runnerPath) {
  let src;
  try { src = fs.readFileSync(runnerPath, 'utf8'); } catch { return []; }

  const hooksDir = path.dirname(runnerPath);
  const hooks    = [];

  // Match lines like: ['label', 'node', [`${HOME}/...`], timeout]
  // or: ['label', 'bash', [path.join(HOOKS_DIR, '...')], timeout]
  const lineRe = /\[\s*'([^']+)'\s*,\s*'(node|bash)'\s*,\s*\[([^\]]+)\]/g;
  let m;
  while ((m = lineRe.exec(src)) !== null) {
    const label   = m[1];
    const cmd     = m[2];
    const argsStr = m[3].trim();

    let scriptPath = null;

    // Form 1: template literal `${HOME}/...` or `${HOOKS_DIR}/...`
    const backtickMatch = argsStr.match(/`([^`]+)`/);
    if (backtickMatch) {
      const raw = backtickMatch[1]
        .replace(/\$\{HOME\}/g,     HOME)
        .replace(/\$\{HOOKS_DIR\}/g, hooksDir);
      scriptPath = expandPath(raw);
    }

    // Form 2: path.join(HOOKS_DIR, 'filename.js') or path.join(__dirname, 'filename.js')
    if (!scriptPath) {
      const joinMatch = argsStr.match(/path\.join\(\s*(?:HOOKS_DIR|__dirname)\s*,\s*['"]([^'"]+)['"]\s*\)/);
      if (joinMatch) {
        scriptPath = path.join(hooksDir, joinMatch[1]);
      }
    }

    // Form 3: bare string literal
    if (!scriptPath) {
      const strMatch = argsStr.match(/^['"]([^'"]+)['"]/);
      if (strMatch) {
        scriptPath = expandPath(strMatch[1]);
      }
    }

    if (!scriptPath) continue;

    hooks.push({
      name:      label,
      scriptPath,
      isBash:    cmd === 'bash' || scriptPath.endsWith('.sh'),
    });
  }
  return hooks;
}

// ─── Individual checks ────────────────────────────────────────────────────────
function checkExists(scriptPath) {
  return fs.existsSync(scriptPath);
}

function checkSyntax(scriptPath) {
  const r = spawnSync('node', ['--check', scriptPath], { timeout: 5000, encoding: 'utf8' });
  return { ok: r.status === 0, detail: (r.stderr || '').trim().split('\n')[0] };
}

function runWithSample(scriptPath, eventType) {
  const sample = SAMPLES[eventType] || SAMPLES['Stop'];
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    let child;
    try {
      child = spawn('node', [scriptPath], { stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (err) {
      return resolve({ exitCode: 1, stdout: '', stderr: err.message });
    }

    child.stdout.on('data', d => (stdout += d));
    child.stderr.on('data', d => (stderr += d));

    child.stdin.write(sample);
    child.stdin.end();

    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch {}
      resolve({ exitCode: -1, stdout, stderr, timedOut: true });
    }, HOOK_TIMEOUT);

    child.on('close', code => {
      clearTimeout(timer);
      resolve({ exitCode: code, stdout, stderr, timedOut: false });
    });
    child.on('error', err => {
      clearTimeout(timer);
      resolve({ exitCode: 1, stdout, stderr: err.message, timedOut: false });
    });
  });
}

function checkStdoutPollution(stdout) {
  if (!stdout || stdout.trim() === '') return { ok: true };
  try {
    JSON.parse(stdout.trim());
    return { ok: true };
  } catch {
    const preview = stdout.trim().slice(0, 80).replace(/\n/g, '\\n');
    return { ok: false, detail: `plain text stdout: "${preview}"` };
  }
}

function checkAsyncExitConflict(scriptPath, isAsync) {
  if (!isAsync) return null; // not async — exit(2) is fine
  try {
    const src = fs.readFileSync(scriptPath, 'utf8');
    if (src.includes('process.exit(2)')) {
      return 'registered async: true but contains process.exit(2) — block silently swallowed';
    }
  } catch {}
  return null;
}

// ─── Build the full hook list ─────────────────────────────────────────────────
function buildHookList(settings) {
  const hooks   = settings.hooks || {};
  const entries = [];

  // Runner scripts whose embedded hooks we also test
  const RUNNER_SCRIPTS = {
    'masonry-stop-runner':
      '/home/nerfherder/Dev/Bricklayer2.0/masonry/src/hooks/masonry-stop-runner.js',
    'masonry-post-write-runner':
      '/home/nerfherder/Dev/Bricklayer2.0/masonry/src/hooks/masonry-post-write-runner.js',
  };

  // Collect names of runner scripts so we can mark them
  const runnerPaths = new Set(Object.values(RUNNER_SCRIPTS));

  for (const [eventType, eventEntries] of Object.entries(hooks)) {
    for (const entry of eventEntries) {
      const matcher = entry.matcher || '';
      for (const hook of (entry.hooks || [])) {
        const cmd      = hook.command || '';
        const isAsync  = !!(hook.async);
        const timeout  = hook.timeout;
        const { scriptPath, isBash } = parseHookCommand(cmd);

        // Derive a display name from the command
        let name = scriptPath ? path.basename(scriptPath, '.js').replace('.sh', '') : cmd.slice(0, 40);

        entries.push({
          event:      eventType,
          matcher,
          name,
          scriptPath,
          isBash,
          isAsync,
          timeout,
          inRunner:   null,
        });

        // If this is a runner, also expand its embedded hooks
        if (scriptPath && runnerPaths.has(scriptPath)) {
          const runnerName = Object.entries(RUNNER_SCRIPTS).find(([, p]) => p === scriptPath)?.[0];
          const embedded   = extractRunnerHooks(scriptPath);
          for (const emb of embedded) {
            entries.push({
              event:     eventType,
              matcher,
              name:      emb.name,
              scriptPath: emb.scriptPath,
              isBash:    emb.isBash,
              isAsync:   true, // runners are async
              timeout:   null,
              inRunner:  runnerName,
            });
          }
        }
      }
    }
  }

  return entries;
}

// Runner scripts that dispatch to child hooks — tested indirectly via embedded hooks.
// Skip the load-crash test for these since they're long-running launchers.
const RUNNER_SCRIPT_NAMES = new Set([
  'masonry-stop-runner',
  'masonry-post-write-runner',
]);

// ─── Run all checks for one entry ─────────────────────────────────────────────
async function smokeOne(entry) {
  const { event, matcher, name, scriptPath, isBash, isAsync, inRunner } = entry;
  const issues  = [];
  const warns   = [];
  const timings = [];

  if (!scriptPath) {
    issues.push('could not parse script path from command');
    return { ...entry, status: 'FAIL', issues, warns, ms: 0 };
  }

  // Check 1: Exists
  if (!checkExists(scriptPath)) {
    issues.push(`file not found: ${scriptPath}`);
    return { ...entry, status: 'FAIL', issues, warns, ms: 0 };
  }

  // Bash scripts: existence only
  if (isBash) {
    return { ...entry, status: 'PASS', issues, warns, ms: 0 };
  }

  // Check 2: Syntax
  const syntaxResult = checkSyntax(scriptPath);
  if (!syntaxResult.ok) {
    issues.push(`syntax error: ${syntaxResult.detail}`);
    return { ...entry, status: 'FAIL', issues, warns, ms: 0 };
  }

  // Runner dispatcher scripts: skip load-crash test (tested via embedded hooks)
  const isRunner = RUNNER_SCRIPT_NAMES.has(path.basename(scriptPath, '.js'));
  if (isRunner) {
    const asyncWarn = checkAsyncExitConflict(scriptPath, isAsync);
    if (asyncWarn) warns.push(asyncWarn);
    const note = 'runner — embedded hooks tested separately';
    warns.push(note);
    return { ...entry, status: 'WARN', issues, warns, timings, ms: 0 };
  }

  // Check 3: Load crash + stdout pollution
  const t0  = Date.now();
  const run = await runWithSample(scriptPath, event);
  const ms  = Date.now() - t0;

  if (run.timedOut) {
    warns.push(`timed out after ${HOOK_TIMEOUT}ms`);
  } else if (run.exitCode === 1) {
    // Distinguish crashes from network errors
    const errLower = (run.stderr || '').toLowerCase();
    const isNetwork = errLower.includes('econnrefused') ||
                      errLower.includes('enotfound') ||
                      errLower.includes('etimedout') ||
                      errLower.includes('network') ||
                      errLower.includes('fetch failed') ||
                      errLower.includes('connect');
    if (isNetwork) {
      warns.push('exit 1 — network error (external service unreachable)');
    } else {
      const detail = (run.stderr || '').trim().split('\n')[0].slice(0, 120);
      issues.push(`exit 1 — crash: ${detail}`);
    }
  }

  // Check 4: Async/exit(2) conflict
  const asyncWarn = checkAsyncExitConflict(scriptPath, isAsync);
  if (asyncWarn) warns.push(asyncWarn);

  // Check 5: Stdout pollution
  if (!run.timedOut && run.exitCode !== 1) {
    const pollutionResult = checkStdoutPollution(run.stdout);
    if (!pollutionResult.ok) warns.push(pollutionResult.detail);
  }

  // Slow hook warning
  if (ms > 1000 && !run.timedOut) {
    timings.push(`${ms}ms (slow)`);
  }

  const status = issues.length > 0 ? 'FAIL' : (warns.length > 0 ? 'WARN' : 'PASS');
  return { ...entry, status, issues, warns, timings, ms };
}

// ─── Formatting ───────────────────────────────────────────────────────────────
function colorStatus(status) {
  if (status === 'PASS') return `${C.green}PASS${C.reset}`;
  if (status === 'WARN') return `${C.yellow}WARN${C.reset}`;
  return `${C.red}FAIL${C.reset}`;
}

function formatEventMatcher(event, matcher) {
  if (matcher) return `${event}:${matcher}`.slice(0, 28);
  return event.slice(0, 28);
}

function printReport(results) {
  const LINE = '─'.repeat(72);
  const HEADER = `${ C.bold }Hook Smoke Test${C.reset} — ${SETTINGS}`;
  console.log('\n' + HEADER);
  console.log(LINE);
  console.log(
    `${ C.bold }${'Event/Matcher'.padEnd(28)}  ${'Hook Name'.padEnd(30)}  ${'Result'.padEnd(6)}  Notes${C.reset}`
  );
  console.log(LINE);

  for (const r of results) {
    const evStr   = formatEventMatcher(r.event, r.matcher).padEnd(28);
    const nameStr = (r.inRunner ? `${r.name} [in runner]` : r.name).slice(0, 30).padEnd(30);
    const status  = colorStatus(r.status);
    const notes   = [
      ...r.issues,
      ...r.warns,
      ...(r.timings || []),
    ].join(' | ');
    console.log(`${evStr}  ${nameStr}  ${status}  ${notes ? C.dim + notes + C.reset : ''}`);
  }

  console.log(LINE);

  const failCount = results.filter(r => r.status === 'FAIL').length;
  const warnCount = results.filter(r => r.status === 'WARN').length;
  const passCount = results.filter(r => r.status === 'PASS').length;

  const summary = [
    failCount > 0 ? `${C.red}${failCount} FAIL${C.reset}` : null,
    warnCount > 0 ? `${C.yellow}${warnCount} WARN${C.reset}` : null,
    `${C.green}${passCount} PASS${C.reset}`,
  ].filter(Boolean).join(', ');

  console.log(`Result: ${summary}`);
  const exitCode = failCount > 0 ? 1 : 0;
  console.log(`Exit: ${exitCode}${exitCode ? ' (failures present)' : ' (clean)'}\n`);

  return exitCode;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  let settings;
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS, 'utf8'));
  } catch (err) {
    console.error(`Failed to read settings.json: ${err.message}`);
    process.exit(1);
  }

  const hookList = buildHookList(settings);

  if (hookList.length === 0) {
    console.log('No hooks found in settings.json');
    process.exit(0);
  }

  // Run all checks in parallel
  const results = await Promise.all(hookList.map(entry => smokeOne(entry)));

  const exitCode = printReport(results);
  process.exit(exitCode);
}

main().catch(err => {
  console.error('hook-smoke.js fatal error:', err.message);
  process.exit(1);
});

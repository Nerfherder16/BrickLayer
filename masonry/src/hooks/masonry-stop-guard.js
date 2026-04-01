#!/usr/bin/env node
/**
 * Stop hook (Masonry): Block if there are uncommitted git changes from THIS session.
 *
 * Primary boundary: session snapshot written by masonry-session-start.js.
 * At SessionStart, all pre-existing dirty files are recorded. On Stop, only
 * files NOT in that snapshot are flagged — i.e. files modified THIS session.
 *
 * Fallback: if no snapshot exists (session-start didn't run or no session ID),
 * falls back to mtime-based detection (today's files only).
 *
 * Exits silently (0) if nothing new was modified this session.
 * Exit code 2 blocks the stop when session files are uncommitted.
 */

const { execSync, execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { readJson, writeJson, appendJsonl } = require("../core/mas");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000);
  });
}

function normalizeCwd(p) {
  // Convert POSIX /c/Users/... paths to Windows C:\Users\... so fs.statSync works
  if (process.platform === "win32" && /^\/[a-zA-Z]\//.test(p)) {
    return p[1].toUpperCase() + ":" + p.slice(2).replace(/\//g, "\\");
  }
  return p;
}

function fileAgeDays(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return Math.floor((Date.now() - stat.mtimeMs) / (1000 * 60 * 60 * 24));
  } catch {
    return null; // treat as today below
  }
}

function ageLabel(days) {
  if (days === null || days === 0) return "";
  if (days === 1) return " (yesterday)";
  return ` (${days}d old)`;
}

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, 'program.md')) &&
         fs.existsSync(path.join(dir, 'questions.md'));
}

function closeSession(projectDir) {
  try {
    const session = readJson(projectDir, 'session.json');
    if (!session || !session.started_at) return;
    const now = new Date();
    session.ended_at = now.toISOString();
    session.duration_ms = now.getTime() - new Date(session.started_at).getTime();
    writeJson(projectDir, 'session.json', session);
    appendJsonl(projectDir, 'history.jsonl', session);
  } catch (_) {}
}

// Key project docs that must stay current with code changes.
const PROJECT_DOCS = [
  "CHANGELOG.md",
  "ROADMAP.md",
  "ARCHITECTURE.md",
  "README.md",
  "PROJECT_STATUS.md",
];

// Source patterns that count as "real code changes" (not just doc/changelog commits).
const SOURCE_PATTERNS = [
  /^masonry\//,
  /^\.claude\//,
  /^template\//,
  /^adbp\//,
  /^kiln\//,
  /^bl\//,
  /^projects\//,
];

/**
 * Warn (non-blocking) if code was committed this session but no project docs were touched.
 * Uses git log since the session snapshot mtime as a proxy for session start.
 */
function checkDocStaleness(cwd, snapPath) {
  try {
    // Use snapshot mtime as session-start anchor; fall back to midnight today.
    let since = "";
    try {
      const snapStat = fs.statSync(snapPath);
      const iso = new Date(snapStat.mtimeMs).toISOString();
      since = `--after="${iso}"`;
    } catch {
      since = '--after="midnight"';
    }

    const log = execSync(`git log --name-only --pretty=format:"" ${since}`, {
      encoding: "utf8",
      timeout: 8000,
      cwd,
    }).trim();

    if (!log) return; // no commits this session

    const changedFiles = log.split("\n").map(l => l.trim()).filter(Boolean);
    const hasSourceChange = changedFiles.some(f => SOURCE_PATTERNS.some(p => p.test(f)));
    if (!hasSourceChange) return; // only doc/misc commits — no warning needed

    const touchedDocs = changedFiles.filter(f => PROJECT_DOCS.includes(f));
    if (touchedDocs.length > 0) return; // docs were updated — all good

    // Docs are stale relative to code commits this session.
    const missing = PROJECT_DOCS.filter(d => !touchedDocs.includes(d));
    process.stderr.write(
      `\n[Masonry] Doc staleness warning: code was committed this session but project docs were not updated.\n` +
      `  Stale: ${missing.join(", ")}\n` +
      `  Run karen or update docs before your next session.\n`
    );

    // Write flag file to .autopilot/ (preferred) for next session's karen pickup.
    // Falls back to .mas/ if .autopilot/ does not exist.
    try {
      const autopilotDir = path.join(cwd, ".autopilot");
      const masDir = path.join(cwd, ".mas");
      const targetDir = fs.existsSync(autopilotDir) ? autopilotDir : masDir;
      fs.mkdirSync(targetDir, { recursive: true });
      const flag = {
        reason: "doc_staleness",
        stale_files: missing,
        source_files_changed: changedFiles.filter(
          (f) =>
            /\.(py|js|ts|tsx|rs|go|md)$/.test(f) &&
            !/(CHANGELOG|ARCHITECTURE|ROADMAP|synthesis|findings)/.test(f)
        ),
        timestamp: new Date().toISOString(),
      };
      fs.writeFileSync(
        path.join(targetDir, "karen-needed.json"),
        JSON.stringify(flag, null, 2),
        "utf8"
      );
    } catch {
      // Non-fatal — skip silently
    }
  } catch {
    // git unavailable or other error — skip silently
  }
}

/**
 * Generate a descriptive auto-commit message based on the files being committed.
 *
 * Heuristics (in priority order):
 * 1. If ALL files appear in the most recent commit's changeset → lint cleanup after that commit.
 * 2. If files span ≤3 top-level directories → name them.
 * 3. Fallback: count + generic label.
 */
function generateAutoCommitMessage(files, cwd) {
  // --- Heuristic 1: lint cleanup detection ---
  try {
    const lastCommitFiles = new Set(
      execSync('git show --name-only --pretty=format: HEAD', {
        encoding: 'utf8', timeout: 5000, cwd,
      }).trim().split('\n').filter(Boolean)
    );
    if (files.length > 0 && files.every(f => lastCommitFiles.has(f))) {
      const hash = execSync('git rev-parse --short HEAD', {
        encoding: 'utf8', timeout: 3000, cwd,
      }).trim();
      return `style: lint cleanup after ${hash} (${files.length} file${files.length !== 1 ? 's' : ''})`;
    }
  } catch { /* git unavailable — fall through */ }

  // --- Heuristic 2: descriptive directory summary ---
  const dirs = new Set(files.map(f => f.split('/')[0]).filter(Boolean));
  const dirList = [...dirs].slice(0, 3).join(', ');
  if (dirs.size <= 3 && dirList) {
    return `chore: update ${dirList} (${files.length} file${files.length !== 1 ? 's' : ''})`;
  }

  // --- Fallback ---
  return `chore: auto-commit ${files.length} session file${files.length !== 1 ? 's' : ''} on stop`;
}

/**
 * Load the set of files this session actually wrote to, from the activity log
 * written by masonry-observe.js (PostToolUse Write/Edit hook).
 * Returns a Set of normalized relative paths, or null if log unavailable.
 */
function loadSessionWrites(sessionId, cwd) {
  if (!sessionId) return null;
  try {
    const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
    if (!fs.existsSync(activityFile)) return null;
    const lines = fs.readFileSync(activityFile, "utf8").trim().split("\n").filter(Boolean);
    const writes = new Set();
    const normalCwd = normalizeCwd(cwd).replace(/\\/g, "/");
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (!entry.file) continue;
        // Normalize to a repo-relative path matching git status output
        let f = entry.file.replace(/\\/g, "/");
        if (f.startsWith(normalCwd + "/")) f = f.slice(normalCwd.length + 1);
        writes.add(f);
      } catch { /* skip malformed lines */ }
    }
    return writes;
  } catch {
    return null;
  }
}

/**
 * Check for overseer trigger flag at Stop. If found, print notice and delete flag.
 * stderrFn defaults to process.stderr.write — injectable for testing.
 */
function checkOverseerTrigger(snapshotsDir, stderrFn) {
  stderrFn = stderrFn || ((s) => process.stderr.write(s));

  const flagPath = path.join(snapshotsDir, 'overseer_trigger.flag');
  if (!fs.existsSync(flagPath)) return;

  const agentsDir = path.join(os.homedir(), '.claude', 'agents');
  const overseerPath = path.join(agentsDir, 'overseer.md');
  stderrFn(
    '\n[overseer] 10 agent invocations since last health check.\n' +
    `Run: claude -p "Act as overseer agent in ${overseerPath}. agents_dir=${agentsDir}. Check all agents."\n`
  );
  fs.unlinkSync(flagPath);
}

module.exports.checkOverseerTrigger = checkOverseerTrigger;

/**
 * Prune backup files older than 7 days from .autopilot/backups/.
 * Walks the directory tree recursively, unlinks stale files, and removes
 * empty directories left behind. Silent on any error — never blocks Stop.
 */
function pruneOldBackups(autopilotDir) {
  const backupsRoot = path.join(autopilotDir, "backups");
  if (!fs.existsSync(backupsRoot)) return;

  const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
  const cutoff = Date.now() - SEVEN_DAYS_MS;

  function pruneDir(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir);
    } catch {
      return;
    }

    for (const entry of entries) {
      const fullPath = path.join(dir, entry);
      let stat;
      try {
        stat = fs.statSync(fullPath);
      } catch {
        continue;
      }

      if (stat.isDirectory()) {
        pruneDir(fullPath);
        // Remove directory if now empty
        try {
          const remaining = fs.readdirSync(fullPath);
          if (remaining.length === 0) fs.rmdirSync(fullPath);
        } catch { /* ignore */ }
      } else if (stat.mtimeMs < cutoff) {
        try {
          fs.unlinkSync(fullPath);
        } catch { /* ignore */ }
      }
    }
  }

  try {
    pruneDir(backupsRoot);
  } catch { /* ignore */ }
}

function tryRead(p) {
  try { return fs.readFileSync(p, "utf8").trim(); } catch { return null; }
}

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  if (parsed.stop_hook_active) process.exit(0);

  const cwd = normalizeCwd(parsed.cwd || process.cwd());
  const sessionId = parsed.session_id || parsed.sessionId || null;
  const snapPath = sessionId ? path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`) : null;

  // Primary: files this session's Write/Edit tools actually touched.
  // This is the authoritative source — prevents false positives from sibling sessions
  // modifying shared files (e.g. questions.md in a concurrent campaign session).
  const sessionWrites = loadSessionWrites(sessionId, cwd);

  // Fallback snapshot: files dirty at session start (pre-existing, not ours).
  let preExistingSet = null;
  if (snapPath) {
    try {
      const snap = JSON.parse(fs.readFileSync(snapPath, "utf8"));
      preExistingSet = new Set(snap.preExisting || []);
    } catch { /* fall through to mtime fallback */ }
  }

  try {
    const status = execSync("git status --porcelain", {
      encoding: "utf8",
      timeout: 6000,
      cwd,
    }).trim();

    if (!status) {
      closeSession(cwd);
      checkDocStaleness(cwd, snapPath);
      checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'));
      process.exit(0);
    }

    const allLines = status.split("\n").filter(Boolean);
    const allFiles = allLines.map((l) => l.slice(3).trim());

    // Filter out gitignored paths
    let ignoredSet = new Set();
    try {
      const ignored = execSync("git check-ignore --stdin", {
        input: allFiles.join("\n"),
        encoding: "utf8",
        timeout: 5000,
        cwd,
      }).trim();
      if (ignored) ignored.split("\n").filter(Boolean).forEach(p => ignoredSet.add(p.trim()));
    } catch { /* no ignored files */ }

    const sessionModified = [];
    const sessionUntracked = [];

    for (const line of allLines) {
      const xy = line.slice(0, 2).trim();
      const file = line.slice(3).trim();

      if (ignoredSet.has(file)) continue;

      if (sessionWrites !== null) {
        // Activity-log mode: only flag files THIS session's tools wrote to.
        if (!sessionWrites.has(file)) continue;
      } else if (preExistingSet !== null) {
        // Snapshot fallback: skip files dirty at session start.
        if (preExistingSet.has(file)) continue;
      } else {
        // Last resort: mtime-based (today's files only).
        const days = fileAgeDays(path.join(cwd, file.replace(/\/$/, "")));
        if (days !== 0 && days !== null) continue;
      }

      (xy === "??" ? sessionUntracked : sessionModified).push(file);
    }

    if (sessionModified.length === 0 && sessionUntracked.length === 0) {
      closeSession(cwd);
      checkDocStaleness(cwd, snapPath);
      checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'));
      process.exit(0);
    }

    // Guard: do not auto-commit if an autopilot build/fix task is IN_PROGRESS.
    // Partial implementations should not be committed without verification.
    const autopilotMode = tryRead(path.join(cwd, '.autopilot', 'mode'));
    if (autopilotMode === 'build' || autopilotMode === 'fix') {
      const progress = tryJSON(path.join(cwd, '.autopilot', 'progress.json'));
      const inProgressTask = progress?.tasks?.find(t => t.status === 'IN_PROGRESS');
      if (inProgressTask) {
        process.stderr.write(`\n[Masonry] Auto-commit skipped: task #${inProgressTask.id} is IN_PROGRESS ("${inProgressTask.description}"). Commit after task completes.\n`);
        checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'));
        process.exit(1);
      }
    }

    // Auto-commit session files rather than blocking — avoids token-expensive Claude intervention.
    try {
      const allSessionFiles = [...sessionModified, ...sessionUntracked];
      // Add files individually — one bad path won't abort the whole batch
      let staged = 0;
      for (const f of allSessionFiles) {
        try {
          execFileSync('git', ['add', '--', f], { encoding: 'utf8', timeout: 5000, cwd });
          staged++;
        } catch (_) { /* skip files with corrupt/missing paths */ }
      }
      if (staged === 0) throw new Error('nothing staged');
      const msg = generateAutoCommitMessage(allSessionFiles, cwd);
      execFileSync('git', ['commit', '-m', msg], { encoding: 'utf8', timeout: 10000, cwd });
      process.stderr.write(`[Masonry] Auto-committed ${staged} session file${staged !== 1 ? 's' : ''}: "${msg}"\n`);
    } catch (commitErr) {
      // Auto-commit failed — fall back to blocking so user knows
      const sessionCount = sessionModified.length + sessionUntracked.length;
      process.stderr.write(`\nStop blocked — ${sessionCount} uncommitted session file${sessionCount !== 1 ? 's' : ''} (git status). Commit before stopping.\n`);
      checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'));
      process.exit(2);
    }

    checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'));
  } catch {
    // Not a git repo or git unavailable — allow stop
  }

  closeSession(cwd);
  checkDocStaleness(cwd, snapPath);

  // Prune stale backups (older than 7 days) from .autopilot/backups/
  const autopilotDirForPrune = path.join(cwd, ".autopilot");
  if (fs.existsSync(autopilotDirForPrune)) {
    pruneOldBackups(autopilotDirForPrune);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

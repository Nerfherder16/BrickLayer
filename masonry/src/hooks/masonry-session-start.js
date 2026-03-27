#!/usr/bin/env node
/**
 * SessionStart hook (Masonry): Restore workflow context at session start.
 *
 * Reads active mode state files and injects context so Claude knows
 * what was in progress when the session opens.
 *
 * Also snapshots the current dirty file list so the stop-guard can
 * distinguish files modified THIS session from pre-existing dirty files.
 *
 * Replaces OMC's session-start.mjs + project-memory-session
 */

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync } = require("child_process");
const { writeJson, initKilnJson } = require("../core/mas");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 3000);
  });
}

function tryRead(p) {
  try { return fs.readFileSync(p, "utf8").trim(); } catch { return null; }
}

function tryJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

function isResearchProject(dir) {
  return fs.existsSync(path.join(dir, 'program.md')) &&
         fs.existsSync(path.join(dir, 'questions.md'));
}

async function main() {
  // Auto-detect BrickLayer research project — hooks are silent inside BL subprocesses
  if (isResearchProject(process.cwd())) process.exit(0);

  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();
  const lines = [];

  // --- Autopilot build state ---
  const autopilotMode = tryRead(path.join(cwd, ".autopilot", "mode"));
  if (autopilotMode && ["build", "fix", "verify"].includes(autopilotMode)) {
    const progress = tryJSON(path.join(cwd, ".autopilot", "progress.json"));
    if (progress) {
      const pending = (progress.tasks || []).filter(t => t.status !== "DONE" && t.status !== "BLOCKED");
      const done = (progress.tasks || []).filter(t => t.status === "DONE").length;
      const total = (progress.tasks || []).length;

      if (pending.length > 0 && (autopilotMode === "build" || autopilotMode === "fix")) {
        // Interrupted build detected — auto-resume by injecting /build into the conversation.
        // Write hookSpecificOutput to stdout so Claude receives it as a prompt directive.
        const resumeMsg = [
          `[Masonry] Interrupted ${autopilotMode} detected: project "${progress.project || "?"}", ${done}/${total} tasks done.`,
          `  Next: #${pending[0].id} — ${pending[0].description}`,
          `  Auto-resuming — run /build to continue.`,
        ].join("\n");
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: "SessionStart",
            content: resumeMsg + "\n\nResume the interrupted build now. Invoke the /build skill to continue from where it left off.",
          },
        }));
        process.exit(0);
      }

      lines.push(`[Masonry] Autopilot ${autopilotMode.toUpperCase()} mode active — project: ${progress.project || "?"}, ${done}/${total} tasks done, ${pending.length} remaining.`);
      if (pending.length > 0) {
        lines.push(`  Next task: #${pending[0].id} — ${pending[0].description}`);
        lines.push(`  Run /build to resume.`);
      }
    } else {
      lines.push(`[Masonry] Autopilot ${autopilotMode.toUpperCase()} mode active. Check .autopilot/ for state.`);
    }
  }

  // --- UI compose state ---
  const uiMode = tryRead(path.join(cwd, ".ui", "mode"));
  if (uiMode && ["compose", "fix", "review"].includes(uiMode)) {
    const uiProgress = tryJSON(path.join(cwd, ".ui", "progress.json"));
    if (uiProgress) {
      const pending = (uiProgress.tasks || []).filter(t => t.status !== "DONE").length;
      lines.push(`[Masonry] UI ${uiMode.toUpperCase()} mode active — ${pending} components pending. Run /ui-compose to resume.`);
    } else {
      lines.push(`[Masonry] UI ${uiMode.toUpperCase()} mode active. Check .ui/ for state.`);
    }
  }

  // --- Campaign state (masonry-state.json) ---
  const campaign = tryJSON(path.join(cwd, "masonry-state.json"));
  if (campaign && campaign.mode) {
    lines.push(`[Masonry] Campaign active — ${campaign.project || path.basename(cwd)}: wave ${campaign.wave || 0}, Q${campaign.q_current || 0}/${campaign.q_total || 0}, mode: ${campaign.mode}.`);
  }

  // --- Karen doc maintenance flag ---
  try {
    const karenFlagPath = path.join(cwd, ".mas", "karen-needed.json");
    if (fs.existsSync(karenFlagPath)) {
      const flag = JSON.parse(fs.readFileSync(karenFlagPath, "utf8"));
      const staleList = (flag.stale_files || []).join(", ");
      lines.push(
        `[ACTION REQUIRED] Spawn karen now: Act as the karen agent in ~/.claude/agents/karen.md. ` +
        `Update and commit these stale project docs: ${staleList}. Do this before any other work.`
      );
      // Clean up flag after pickup so it doesn't fire every session
      try { fs.unlinkSync(karenFlagPath); } catch (_) {}
    }
  } catch (_) {
    // Malformed flag file or read error — skip silently
  }

  // --- BL project detection (auto bl-run) ---
  // If cwd looks like a BL project with pending questions and no active campaign,
  // inject the run commands so the user doesn't have to invoke /bl-run manually.
  const hasProgramMd = fs.existsSync(path.join(cwd, "program.md"));
  const hasQuestionsMd = fs.existsSync(path.join(cwd, "questions.md"));
  const hasActiveCampaign = !!(campaign && campaign.mode);
  const hasActiveAutopilot = !!(autopilotMode && ["build", "fix", "verify"].includes(autopilotMode));

  if (hasProgramMd && hasQuestionsMd && !hasActiveCampaign && !hasActiveAutopilot) {
    try {
      const qText = fs.readFileSync(path.join(cwd, "questions.md"), "utf8");
      const pendingMatches = (qText.match(/\|\s*PENDING\s*\|/gi) || []).length;

      if (pendingMatches > 0) {
        const projectName = path.basename(cwd);
        // Detect BL root by walking up from cwd — look for a directory that has
        // both bl/ and masonry/ subdirectories. Falls back to null (omits path-dependent hints).
        let blRoot = null;
        {
          let dir = cwd;
          for (let i = 0; i < 10; i++) {
            if (fs.existsSync(path.join(dir, "bl")) && fs.existsSync(path.join(dir, "masonry"))) {
              blRoot = dir;
              break;
            }
            const parent = path.dirname(dir);
            if (parent === dir) break;
            dir = parent;
          }
        }
        const tip = pendingMatches > 10 ? `\n  Tip: ${pendingMatches} questions — parallel workers will finish ~3x faster.` : "";

        // Check if claims.json has active workers (parallel session already running)
        const claimsPath = path.join(cwd, "claims.json");
        let activeWorkers = 0;
        if (fs.existsSync(claimsPath)) {
          try {
            const claims = JSON.parse(fs.readFileSync(claimsPath, "utf8"));
            activeWorkers = Object.values(claims).filter(c => c.status === "IN_PROGRESS").length;
          } catch {}
        }

        if (activeWorkers > 0) {
          lines.push(`[BL] ${projectName}: ${pendingMatches} pending, ${activeWorkers} active worker(s) — parallel session may still be running.`);
          if (blRoot) lines.push(`  Check: python ${blRoot}/bl/claim.py status ${cwd}`);
        } else {
          lines.push(`[BL] ${projectName}: ${pendingMatches} questions PENDING — ready to run.${tip}`);
          lines.push(`  Single worker:`);
          lines.push(`    claude --dangerously-skip-permissions "Read program.md and questions.md. Resume the research loop from the first PENDING question. NEVER STOP."`);
          if (blRoot) {
            lines.push(`  Parallel (3x faster):`);
            lines.push(`    cd ${blRoot} && ./bl-parallel.ps1 -Project ${projectName} -Workers 3`);
          }
        }
      }
    } catch {
      // questions.md unreadable — skip silently
    }
  }

  // --- Subagent tracking state (global ~/.masonry/state/) ---
  const agentState = tryJSON(path.join(os.homedir(), ".masonry", "state", "agents.json"));
  if (agentState && agentState.active && agentState.active.length > 0) {
    lines.push(`[Masonry] ${agentState.active.length} agent(s) were active at last session: ${agentState.active.map(a => a.name || a.type).join(", ")}.`);
  }

  // --- .mas/ session + context injection ---
  try {
    const sessionId0 = input.session_id || input.sessionId || null;
    const sessionObj = {
      session_id: sessionId0 || 'unknown',
      started_at: new Date().toISOString(),
      cwd,
      branch: null,
    };
    try {
      sessionObj.branch = execSync('git branch --show-current', {
        encoding: 'utf8', timeout: 3000, cwd,
      }).trim() || null;
    } catch (_) {}
    writeJson(cwd, 'session.json', sessionObj);
    initKilnJson(cwd);

    // --- Session lock (parallel session conflict prevention) ---
    // Write .mas/session.lock so PreToolUse can detect cross-session writes to
    // protected files. Only write if no non-stale lock exists from a different session.
    if (sessionId0) {
      const LOCK_STALE_MS = 4 * 60 * 60 * 1000; // 4 hours
      const lockPath = path.join(cwd, '.mas', 'session.lock');
      let shouldWriteLock = true;
      try {
        if (fs.existsSync(lockPath)) {
          const existingLock = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
          const lockAge = Date.now() - new Date(existingLock.started_at || 0).getTime();
          if (lockAge < LOCK_STALE_MS && existingLock.session_id !== sessionId0) {
            shouldWriteLock = false;
            lines.push(
              `[Masonry] \u26a0\ufe0f  Session lock held by session ${existingLock.session_id} ` +
              `(started ${existingLock.started_at}).` +
              ` Protected files (masonry-state.json, questions.md, findings/, .autopilot/) ` +
              `are READ-ONLY for this session. Delete .mas/session.lock to override.`
            );
          }
        }
      } catch (_) {}
      if (shouldWriteLock) {
        try {
          const lockData = {
            session_id: sessionId0,
            started_at: sessionObj.started_at,
            cwd,
            branch: sessionObj.branch,
          };
          fs.mkdirSync(path.join(cwd, '.mas'), { recursive: true });
          fs.writeFileSync(lockPath, JSON.stringify(lockData, null, 2), 'utf8');
        } catch (_) {}
      }
    }
  } catch (_) {}

  // Inject context.md if present
  try {
    const ctxPath = path.join(cwd, '.mas', 'context.md');
    if (fs.existsSync(ctxPath)) {
      const ctx = fs.readFileSync(ctxPath, 'utf8').trim();
      if (ctx) {
        lines.push('[Masonry] Campaign context loaded from .mas/context.md');
      }
    }
  } catch (_) {}

  // --- Build Pattern Import (Phase 2.2) ---
  // Query Recall for build patterns matching the current project type.
  // Injects relevant patterns as context to avoid regenerating known solutions.
  try {
    const projectFiles = fs.readdirSync(cwd).slice(0, 30);
    const hasPyproject = projectFiles.some(f => f === 'pyproject.toml' || f === 'setup.py' || f === 'requirements.txt');
    const hasPackageJson = projectFiles.some(f => f === 'package.json');

    if (hasPyproject || hasPackageJson) {
      const lang = hasPyproject ? 'python' : 'typescript';
      const RECALL_HOST_URL = process.env.RECALL_HOST || 'http://100.70.195.84:8200';
      const RECALL_API_KEY_VAL = process.env.RECALL_API_KEY || '';

      // Fire-and-forget Recall query — don't block session start
      const http = require('http');
      const https = require('https');
      const queryBody = JSON.stringify({
        query: `build patterns ${lang}`,
        domain: 'build-patterns',
        limit: 5,
      });
      const url = new URL(`${RECALL_HOST_URL}/api/memory/search`);
      const lib = url.protocol === 'https:' ? https : http;
      const req = lib.request({
        hostname: url.hostname,
        port: url.port || (url.protocol === 'https:' ? 443 : 80),
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(queryBody),
          ...(RECALL_API_KEY_VAL ? { 'Authorization': `Bearer ${RECALL_API_KEY_VAL}` } : {}),
        },
        timeout: 3000,
      }, (res) => {
        let data = '';
        res.on('data', c => (data += c));
        res.on('end', () => {
          try {
            const results = JSON.parse(data);
            const memories = Array.isArray(results) ? results : (results.results || results.memories || []);
            if (memories.length > 0) {
              lines.push(`[Masonry] ${memories.length} build pattern(s) from Recall (${lang}): ${memories.map(m => m.tags?.find(t => t.startsWith('framework:'))?.replace('framework:', '') || 'unknown').filter(Boolean).join(', ')}`);
              lines.push('  Relevant patterns available — use masonry_recall tool to retrieve details.');
            }
          } catch (_) {}
        });
      });
      req.on('error', () => {});
      req.on('timeout', () => { req.destroy(); });
      req.write(queryBody);
      req.end();
    }
  } catch (_) {}

  if (lines.length > 0) {
    process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", content: lines.join("\n") } }));
  }

  // --- Session snapshot for stop-guard dirty-file diffing ---
  // Capture which files are already dirty at session open so the stop-guard
  // can ignore them and only flag files modified THIS session.
  const sessionId = input.session_id || input.sessionId || null;
  if (sessionId) {
    try {
      const status = execSync("git status --porcelain", {
        encoding: "utf8",
        timeout: 5000,
        cwd,
      }).trim();
      const preExisting = status
        ? status.split("\n").filter(Boolean).map((l) => l.slice(3).trim())
        : [];
      const snapPath = path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`);
      fs.writeFileSync(snapPath, JSON.stringify({ sessionId, cwd, preExisting }), "utf8");
    } catch {
      // Non-git dir or git unavailable — skip snapshot silently
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

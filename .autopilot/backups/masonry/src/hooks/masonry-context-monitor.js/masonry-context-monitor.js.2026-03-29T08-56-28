#!/usr/bin/env node
/**
 * Stop hook (Masonry): Estimate context window usage + semantic degradation.
 * Blocks stop ONLY when context > 750K AND there are uncommitted changes.
 * If the repo is clean, emits a stderr warning but allows the stop.
 * stop_hook_active prevents infinite loops — fires once, then allows stop.
 *
 * Semantic degradation checks (advisory, never block):
 *   Lost-in-middle — recent vs first assistant message similarity < 0.3
 *   Poisoning      — sudden consecutive similarity drop > 0.5 from baseline
 *   Distraction    — recent messages vs IN_PROGRESS task text similarity < 0.25
 *   Clash          — two very recent messages similarity < 0.1
 */

const { statSync, existsSync, readFileSync } = require("fs");
const { execSync } = require("child_process");
const { readStdin } = require("./session/stop-utils");

function hasUncommittedChanges(cwd, sessionId) {
  try {
    const status = execSync("git status --porcelain", {
      encoding: "utf8", timeout: 5000, cwd,
    }).trim();
    if (!status) return false;

    // If we have a session ID, check the activity log to narrow to THIS session's
    // files only — prevents sibling-session files (campaign, Playwright) from
    // triggering a false block.
    if (sessionId) {
      const os = require("os");
      const path = require("path");
      const fs = require("fs");
      const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
      if (fs.existsSync(activityFile)) {
        const lines = fs.readFileSync(activityFile, "utf8").trim().split("\n").filter(Boolean);
        const normalCwd = cwd.replace(/\\/g, "/");
        const sessionFiles = new Set();
        for (const line of lines) {
          try {
            const entry = JSON.parse(line);
            if (!entry.file) continue;
            let f = entry.file.replace(/\\/g, "/");
            if (f.startsWith(normalCwd + "/")) f = f.slice(normalCwd.length + 1);
            sessionFiles.add(f);
          } catch { /* skip */ }
        }
        if (sessionFiles.size > 0) {
          // Only block if one of THIS session's files appears in git status
          const dirtyFiles = status.split("\n").map(l => l.slice(3).trim());
          return dirtyFiles.some(f => sessionFiles.has(f));
        }
      }

      // Activity log missing — check snapshot for pre-existing files and exclude them
      const snapPath = path.join(os.tmpdir(), `masonry-snap-${sessionId}.json`);
      if (fs.existsSync(snapPath)) {
        try {
          const snap = JSON.parse(fs.readFileSync(snapPath, "utf8"));
          const preExisting = new Set(snap.preExisting || []);
          const dirtyFiles = status.split("\n").map(l => l.slice(3).trim());
          return dirtyFiles.some(f => !preExisting.has(f));
        } catch { /* fall through */ }
      }
    }

    // No session context — fall back to any dirty files
    return true;
  } catch {
    return false;
  }
}

/**
 * Compute cosine similarity between two equal-length numeric vectors.
 * Returns a value in [-1, 1]. Returns 0 if either magnitude is zero.
 */
function cosineSim(a, b) {
  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  const denom = Math.sqrt(magA) * Math.sqrt(magB);
  return denom === 0 ? 0 : dot / denom;
}

/**
 * Fetch an embedding from Ollama for the given text snippet.
 * Returns the embedding array or null on failure.
 */
async function fetchEmbedding(ollamaHost, text, signal) {
  const res = await fetch(`${ollamaHost}/api/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "nomic-embed-text",
      prompt: text.slice(0, 1000),
    }),
    signal,
  });
  if (!res.ok) return null;
  const data = await res.json();
  return Array.isArray(data.embedding) ? data.embedding : null;
}

/**
 * Read the current IN_PROGRESS task description from .autopilot/progress.json.
 * Returns null if the file is missing or no IN_PROGRESS task exists.
 */
function getInProgressTask(cwd) {
  try {
    const progressPath = `${cwd}/.autopilot/progress.json`;
    if (!existsSync(progressPath)) return null;
    const raw = readFileSync(progressPath, "utf8");
    const parsed = JSON.parse(raw);
    const tasks = parsed.tasks || [];
    const task = tasks.find((t) => t.status === "IN_PROGRESS");
    return task ? task.description || null : null;
  } catch {
    return null;
  }
}

/**
 * Run semantic degradation checks against the last N assistant messages.
 * Emits stderr warnings for each detected pattern. Never throws or blocks.
 */
async function checkSemanticDegradation(messages, cwd) {
  const ollamaHost = process.env.OLLAMA_HOST || "http://100.70.195.84:11434";

  if (!messages || messages.length < 3) return;

  const assistantMessages = messages
    .filter((m) => m.role === "assistant")
    .map((m) =>
      typeof m.content === "string" ? m.content : JSON.stringify(m.content)
    );

  // Need at least 2 assistant messages to run any check
  if (assistantMessages.length < 2) return;

  // Samples: first (anchor), last 3 recent
  const first = assistantMessages[0];
  const recent = assistantMessages.slice(-3);

  // IN_PROGRESS task text for Distraction check (may be null)
  const inProgressTask = getInProgressTask(cwd);

  // Build list of texts to embed
  const textsToEmbed = [first, ...recent];
  if (inProgressTask) textsToEmbed.push(inProgressTask);

  // AbortSignal with 5-second timeout
  let signal;
  try {
    signal = AbortSignal.timeout(5000);
  } catch {
    // AbortSignal.timeout may not exist in older Node; fall back to manual abort
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 5000);
    signal = controller.signal;
  }

  let embeddings;
  try {
    const results = await Promise.all(
      textsToEmbed.map((text) => fetchEmbedding(ollamaHost, text, signal))
    );
    // If any embedding failed (null), abort all checks
    if (results.some((e) => e === null)) return;
    embeddings = results;
  } catch {
    // Network error, timeout, model not loaded — skip silently
    return;
  }

  // Unpack embeddings in the same order as textsToEmbed
  const embFirst = embeddings[0];
  const embRecent = embeddings.slice(1, 1 + recent.length);
  const embTask = inProgressTask ? embeddings[embeddings.length - 1] : null;

  const embLast = embRecent[embRecent.length - 1];

  const warnings = [];

  // Check 1: Lost-in-middle — first vs last assistant message
  {
    const sim = cosineSim(embFirst, embLast);
    if (sim < 0.3) {
      warnings.push(
        `lost-in-middle (first↔last similarity: ${sim.toFixed(2)}) — Consider /compact.`
      );
    }
  }

  // Check 2: Poisoning — sudden topic shift between consecutive recent messages
  {
    for (let i = 1; i < embRecent.length; i++) {
      const sim = cosineSim(embRecent[i - 1], embRecent[i]);
      if (sim < 0.2) {
        warnings.push(
          `poisoning (sudden shift at message ${i}, similarity: ${sim.toFixed(2)}) — Consider /compact.`
        );
        break;
      }
    }
  }

  // Check 3: Distraction — recent messages vs IN_PROGRESS task text
  if (embTask) {
    // Average similarity of recent messages to the task description
    const sims = embRecent.map((e) => cosineSim(e, embTask));
    const avgSim = sims.reduce((a, b) => a + b, 0) / sims.length;
    if (avgSim < 0.25) {
      warnings.push(
        `distraction (recent messages vs IN_PROGRESS task similarity: ${avgSim.toFixed(2)}) — Consider /compact.`
      );
    }
  }

  // Check 4: Clash — two very recent messages with near-zero similarity
  if (embRecent.length >= 2) {
    for (let i = 0; i < embRecent.length; i++) {
      for (let j = i + 1; j < embRecent.length; j++) {
        const sim = cosineSim(embRecent[i], embRecent[j]);
        if (sim < 0.1) {
          warnings.push(
            `clash (near-zero similarity between recent messages: ${sim.toFixed(2)}) — Consider /compact.`
          );
          // Report only first clash pair to avoid noise
          break;
        }
      }
    }
  }

  if (warnings.length > 0) {
    process.stderr.write("\n");
    warnings.forEach((w) => {
      process.stderr.write(
        `[masonry-context-monitor] WARNING: Semantic degradation detected — ${w}\n`
      );
    });
  }
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  // Don't block a second time — stop_hook_active is set after first block
  if (parsed.stop_hook_active) process.exit(0);

  const transcriptPath = parsed.transcript_path;
  if (!transcriptPath) process.exit(0);

  const cwd = parsed.cwd || process.cwd();
  const sessionId = parsed.session_id || parsed.sessionId || null;

  // --- Context size check (existing behaviour) ---
  try {
    const stats = statSync(transcriptPath);
    const estimatedTokens = Math.round(stats.size / 4);

    if (estimatedTokens > 750000) {
      const dirty = hasUncommittedChanges(cwd, sessionId);
      const label = `~${Math.round(estimatedTokens / 1000)}K tokens (>750K) — commit + new session.`;

      if (dirty) {
        // Block: uncommitted changes + large context = risk of lost work
        process.stdout.write(JSON.stringify({
          decision: "block",
          reason: label,
        }));
      } else {
        // Warn only: repo is clean, safe to stop
        process.stderr.write(`\n[Masonry] ${label}\n`);
      }
    }
  } catch {}

  // --- Semantic degradation check (advisory, never blocks) ---
  await checkSemanticDegradation(parsed.messages || [], cwd);

  process.exit(0);
}

main().catch(() => process.exit(0));

#!/usr/bin/env node
/**
 * masonry-system-status.js
 * Stop hook — writes unified system status to .mas/system-status.json.
 * Mortar reads this at session start to orient itself.
 * Never blocks session end — all failures are silent.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { readStdin } = require('./session/stop-utils');

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const BL_ROOT = input.cwd || process.cwd();
  const STATUS_FILE = path.join(BL_ROOT, ".mas", "system-status.json");
  const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB;
  const MAS_DIR = path.join(BL_ROOT, ".mas");

  function safeRead(filepath) {
    try { return JSON.parse(fs.readFileSync(filepath, "utf8")); }
    catch { return {}; }
  }

  function getCampaignStatus() {
    try {
      const state = safeRead(path.join(MAS_DIR, "session.json"));
      const masonryState = safeRead(path.join(BL_ROOT, "masonry-state.json"));
      return {
        active: masonryState.campaign_active || false,
        project: masonryState.current_project || null,
        wave: masonryState.current_wave || null,
        pending: masonryState.questions_pending || null,
        complete: masonryState.questions_complete || null,
      };
    } catch { return {}; }
  }

  function getRecallStatus() {
    try {
      const degradedFlag = path.join(MAS_DIR, "recall_degraded");
      return {
        degraded: fs.existsSync(degradedFlag),
        host: process.env.RECALL_HOST || "http://localhost:8200",
      };
    } catch { return { degraded: false }; }
  }

  function getTrainingStatus() {
    if (!TRAINING_DB) {
      // Fallback: check for .mas/training_ready.flag written by the training pipeline
      const flagFile = path.join(MAS_DIR, "training_ready.flag");
      if (fs.existsSync(flagFile)) {
        try {
          const eligible_traces = parseInt(fs.readFileSync(flagFile, "utf8").trim(), 10) || 0;
          return { configured: true, ready: true, eligible_traces, source: "flag" };
        } catch {
          return { configured: true, ready: true, eligible_traces: 0, source: "flag" };
        }
      }
      return { configured: false };
    }
    try {
      const result = spawnSync("python3", [
        "-c",
        [
          "import sqlite3, json",
          `db = sqlite3.connect('${TRAINING_DB.replace(/\\/g, "/")}')`,
          "total = db.execute('SELECT COUNT(*) FROM traces').fetchone()[0]",
          "eligible = db.execute('SELECT COUNT(*) FROM traces WHERE sft_eligible=1').fetchone()[0]",
          "print(json.dumps({'total': total, 'eligible': eligible}))",
        ].join(";"),
      ], { encoding: "utf8", timeout: 1000 });
      if (result.status === 0) {
        const data = JSON.parse(result.stdout.trim());
        return {
          configured: true,
          total_traces: data.total,
          eligible_traces: data.eligible,
          threshold: 500,
          ready: data.eligible >= 500,
        };
      }
    } catch {}
    return { configured: true, error: "could not query db" };
  }

  function getAgentStatus() {
    try {
      const registryPath = path.join(BL_ROOT, "masonry", "agent_registry.yml");
      if (!fs.existsSync(registryPath)) return {};
      const content = fs.readFileSync(registryPath, "utf8");
      const lowScoreMatches = [...content.matchAll(/name:\s*(\S+)[\s\S]*?last_score:\s*([\d.]+)/g)];
      const belowThreshold = lowScoreMatches
        .filter(m => parseFloat(m[2]) < 0.6)
        .map(m => ({ agent: m[1], score: parseFloat(m[2]) }));
      const snapshotDir = path.join(BL_ROOT, "masonry", "agent_snapshots");
      let lastOptimized = null;
      if (fs.existsSync(snapshotDir)) {
        const timestamps = fs.readdirSync(snapshotDir)
          .map(agent => {
            const evalFile = path.join(snapshotDir, agent, "eval_latest.json");
            try {
              const data = JSON.parse(fs.readFileSync(evalFile, "utf8"));
              return data.timestamp || null;
            } catch { return null; }
          })
          .filter(Boolean)
          .sort()
          .reverse();
        lastOptimized = timestamps[0] || null;
      }
      return { below_threshold: belowThreshold, last_optimized: lastOptimized };
    } catch { return {}; }
  }

  function getRoughInStatus() {
    try {
      const stateFile = path.join(BL_ROOT, ".autopilot", "rough-in-state.json");
      if (!fs.existsSync(stateFile)) return { active_task: null };
      const state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
      const pending = (state.tasks || []).filter(t => t.status !== "complete");
      return {
        active_task: state.task_id || null,
        description: state.description || null,
        pending_steps: pending.length,
        last_updated: state.last_updated || null,
      };
    } catch { return { active_task: null }; }
  }

  function getSkillCandidates() {
    try {
      const candidateFile = path.join(MAS_DIR, "skill_candidates.json");
      if (!fs.existsSync(candidateFile)) return { count: 0 };
      const candidates = JSON.parse(fs.readFileSync(candidateFile, "utf8"));
      return { count: Array.isArray(candidates) ? candidates.length : 0 };
    } catch { return { count: 0 }; }
  }

  const status = {
    generated_at: new Date().toISOString(),
    campaign: getCampaignStatus(),
    recall: getRecallStatus(),
    training: getTrainingStatus(),
    agents: getAgentStatus(),
    rough_in: getRoughInStatus(),
    skills: getSkillCandidates(),
  };

  try {
    if (!fs.existsSync(MAS_DIR)) fs.mkdirSync(MAS_DIR, { recursive: true });
    fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2), "utf8");
    process.stderr.write("[masonry-system-status] status written\n");
  } catch (e) {
    process.stderr.write(`[masonry-system-status] write failed: ${e.message}\n`);
  }

  process.exit(0);
}

main().then(() => process.exit(0)).catch(() => process.exit(0));

"use strict";
// session/context-data.js — Recall patterns, codebase map, swarm resume, ReasoningBank, skills

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

/**
 * Adds Recall build patterns, codebase map, swarm compaction resume warning,
 * ReasoningBank patterns, and relevant skills to lines.
 */
async function addContextData(lines, cwd, state) {
  const { autopilotMode, uiMode } = state;

  // --- Build Pattern Import: Recall ---
  try {
    const projectFiles = fs.readdirSync(cwd).slice(0, 30);
    const hasPyproject = projectFiles.some(f => ["pyproject.toml", "setup.py", "requirements.txt"].includes(f));
    const hasPackageJson = projectFiles.some(f => f === "package.json");

    if (hasPyproject || hasPackageJson) {
      const lang = hasPyproject ? "python" : "typescript";
      const RECALL_HOST_URL = process.env.RECALL_HOST || "http://100.70.195.84:8200";
      const RECALL_API_KEY_VAL = process.env.RECALL_API_KEY || "";
      const http = require("http");
      const https = require("https");
      const queryBody = JSON.stringify({ query: `build patterns ${lang}`, domain: "build-patterns", limit: 5 });
      const url = new URL(`${RECALL_HOST_URL}/api/memory/search`);
      const lib = url.protocol === "https:" ? https : http;
      const req = lib.request({
        hostname: url.hostname,
        port: url.port || (url.protocol === "https:" ? 443 : 80),
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(queryBody),
          ...(RECALL_API_KEY_VAL ? { Authorization: `Bearer ${RECALL_API_KEY_VAL}` } : {}),
        },
        timeout: 3000,
      }, (res) => {
        let data = "";
        res.on("data", c => (data += c));
        res.on("end", () => {
          try {
            const results = JSON.parse(data);
            const memories = Array.isArray(results) ? results : (results.results || results.memories || []);
            if (memories.length > 0) {
              lines.push(`[Masonry] ${memories.length} build pattern(s) from Recall (${lang}): ${memories.map(m => m.tags?.find(t => t.startsWith("framework:"))?.replace("framework:", "") || "unknown").filter(Boolean).join(", ")}`);
              lines.push("  Relevant patterns available — use masonry_recall tool to retrieve details.");
            }
          } catch (_) {}
        });
      });
      req.on("error", () => {});
      req.on("timeout", () => { req.destroy(); });
      req.write(queryBody);
      req.end();
    }
  } catch (_) {}

  // --- Codebase Map Injection ---
  try {
    const mapPath = path.join(cwd, ".autopilot", "map.md");
    if (fs.existsSync(mapPath)) {
      const mapStat = fs.statSync(mapPath);
      const mapAgeHours = Math.round((Date.now() - mapStat.mtimeMs) / 3600000);
      const mapLines = fs.readFileSync(mapPath, "utf8").split("\n");

      const stackLine = (mapLines.find(l => l.startsWith("- Languages:")) || "").replace(/^-\s*Languages:\s*/, "").trim();
      const frameworkLine = (mapLines.find(l => l.startsWith("- Frameworks:")) || "").replace(/^-\s*Frameworks:\s*/, "").trim();
      const testLine = (mapLines.find(l => l.startsWith("- Test runner:")) || "").replace(/^-\s*Test runner:\s*/, "").trim();

      const epIdx = mapLines.findIndex(l => l === "## Entry Points");
      const entryPoints = [];
      if (epIdx >= 0) {
        for (let i = epIdx + 1; i < Math.min(epIdx + 8, mapLines.length); i++) {
          const l = mapLines[i].trim();
          if (l.startsWith("##")) break;
          if (l.startsWith("-")) entryPoints.push(l.replace(/^-\s*`?/, "").replace(/`$/, "").trim());
        }
      }

      const kdIdx = mapLines.findIndex(l => l === "## Key Directories");
      const keyDirs = [];
      if (kdIdx >= 0) {
        for (let i = kdIdx + 1; i < Math.min(kdIdx + 18, mapLines.length); i++) {
          const l = mapLines[i].trim();
          if (l.startsWith("##")) break;
          if (l.startsWith("|") && !l.startsWith("|---") && !l.includes("Directory")) {
            const parts = l.split("|").map(s => s.trim()).filter(Boolean);
            if (parts.length >= 2) keyDirs.push(`${parts[0].replace(/`/g, "")}(${parts[1]})`);
          }
        }
      }

      const ageSuffix = mapAgeHours > 24 ? " — stale" : "";
      const stackParts = [stackLine, frameworkLine, testLine !== "not detected" ? testLine : ""].filter(Boolean);
      const stackSummary = stackParts.join(" · ");
      if (stackSummary) {
        lines.push(`[Masonry] Codebase map (${mapAgeHours}h old${ageSuffix}): ${stackSummary}`);
        if (entryPoints.length > 0) lines.push(`  Entry: ${entryPoints.slice(0, 3).join(", ")}`);
        if (keyDirs.length > 0) lines.push(`  Dirs: ${keyDirs.slice(0, 5).join(" ")}`);
      }
    }
  } catch (_) {}

  // --- Swarm compaction resume warning ---
  {
    const inflightPath = path.join(cwd, ".autopilot", "inflight-agents.json");
    if (fs.existsSync(inflightPath)) {
      const inflight = (() => { try { return JSON.parse(fs.readFileSync(inflightPath, "utf8")); } catch { return null; } })();
      if (inflight && Array.isArray(inflight.tasks)) {
        const inProgressTasks = inflight.tasks.filter(t => t.status === "IN_PROGRESS");
        if (inProgressTasks.length > 0) {
          lines.unshift(
            `[Masonry] SWARM RESUME: compaction interrupted ${inProgressTasks.length} in-flight task(s).`,
            `These tasks were IN_PROGRESS before compaction. Check .autopilot/progress.json — tasks still showing IN_PROGRESS are orphaned and need re-dispatch.`,
            `Tasks: ${inProgressTasks.map(t => `#${t.id} (${t.claimed_by || "unknown-worker"}): ${t.description || ""}`).join(", ")}`,
            `Re-dispatch them by reading progress.json and spawning new workers for each IN_PROGRESS task.`
          );
        }
      }
      try { fs.unlinkSync(inflightPath); } catch (_) {}
    }
  }

  // --- ReasoningBank pattern injection ---
  try {
    const bankPath = path.join(__dirname, "../../../src/reasoning/bank.py");
    if (fs.existsSync(bankPath)) {
      const projectBasename = path.basename(cwd);
      const modeStr = autopilotMode || uiMode || "general";
      const rbOut = execSync(
        `python "${bankPath}" query "${(modeStr + " " + projectBasename).replace(/"/g, '\\"')}" 5`,
        { timeout: 3000, encoding: "utf8" }
      );
      const rbPatterns = JSON.parse(rbOut.trim());
      if (Array.isArray(rbPatterns) && rbPatterns.length > 0) {
        lines.push("## Relevant ReasoningBank Patterns");
        for (const p of rbPatterns) {
          const conf = typeof p.confidence === "number" ? p.confidence.toFixed(2) : "?";
          lines.push(`${p.content} (confidence: ${conf})`);
        }
      }
    }
  } catch (_) {}

  // --- Relevant skills from Recall ---
  try {
    const { surfaceSkills } = require("../../core/skill-surface");
    const projectName = path.basename(cwd);
    const modeHint = autopilotMode || uiMode || "general";
    const { markdown } = await surfaceSkills({ query: `${modeHint} ${projectName}`, projectName, limit: 3 });
    if (markdown) {
      lines.push("## Relevant Skills");
      lines.push(markdown);
    }
  } catch (_) {}
}

module.exports = { addContextData };

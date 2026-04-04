"use strict";
/**
 * Pre-compact Recall checkpoint.
 * Reads the session activity log and POSTs a summary to Recall so long-running
 * sessions that never close still get their context preserved across compactions.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");
const https = require("https");
const http = require("http");

const RECALL_URL = process.env.RECALL_API_URL || "http://localhost:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "recall-admin-key-change-me";

/**
 * Store a checkpoint to Recall before context compaction.
 * @param {string} cwd - Working directory (project root)
 * @param {string|undefined} sessionId - Claude session ID
 */
async function storeRecallCheckpoint(cwd, sessionId) {
  if (!sessionId) return;

  try {
    const activityFile = path.join(os.tmpdir(), `masonry-activity-${sessionId}.ndjson`);
    if (!fs.existsSync(activityFile)) return;

    const rawLines = fs.readFileSync(activityFile, "utf8").trim().split("\n").filter(Boolean);
    const entries = rawLines
      .map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);

    if (entries.length === 0) return;

    const summaries = entries.map(e => e.summary).filter(Boolean);
    const project = path.basename(cwd);
    const content = [
      `Session checkpoint for project: ${project}`,
      `Session ID: ${sessionId}`,
      `Total edits: ${entries.length}`,
      `Recent work: ${summaries.slice(-10).join(" → ")}`,
    ].join("\n");

    const body = JSON.stringify({
      content,
      domain: `${project}-session-checkpoints`,
      tags: ["session-checkpoint", "pre-compact", project],
      importance: 0.75,
    });

    await postToRecall(`${RECALL_URL}/memory/store`, body);
  } catch {
    // Non-blocking — silently skip if Recall is unavailable
  }
}

function postToRecall(url, body) {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const lib = parsed.protocol === "https:" ? https : http;
    const req = lib.request(
      {
        hostname: parsed.hostname,
        port: parsed.port || (parsed.protocol === "https:" ? 443 : 80),
        path: parsed.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
          "Authorization": `Bearer ${RECALL_API_KEY}`,
        },
      },
      (res) => {
        res.resume(); // drain response
        resolve(res.statusCode);
      }
    );
    req.on("error", () => resolve(null));
    req.setTimeout(3000, () => { req.destroy(); resolve(null); });
    req.write(body);
    req.end();
  });
}

module.exports = { storeRecallCheckpoint };

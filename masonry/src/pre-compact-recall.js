#!/usr/bin/env node
/**
 * Recall checkpoint helper for masonry-pre-compact.js.
 *
 * Extracted to keep the main hook under the 300-line file-size limit.
 * Stores a mid-session conversation checkpoint to Recall, including both
 * user prompts and assistant responses, before context compaction occurs.
 */

"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");

const RECALL_HOST = process.env.RECALL_HOST || "http://100.70.195.84:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "recall-admin-key-change-me";
const MAX_TRANSCRIPT_LINES = 100;

// Project → canonical domain (matches recall-retrieve.js)
const PROJECT_DOMAINS = {
  "recall": "recall", "system-recall": "recall",
  "familyhub": "family-hub", "family-hub": "family-hub", "sadie": "family-hub",
  "relay": "relay", "codevv": "codevv", "foundry": "foundry",
  "media-server": "media-server", "jellyfin": "media-server", "homelab": "homelab",
};

/**
 * Derive the JSONL transcript path from cwd + session_id.
 * Claude Code stores transcripts at:
 *   ~/.claude/projects/{cwd-slug}/{session_id}.jsonl
 * where cwd-slug = path separators replaced with "--", drive colon removed.
 */
function deriveTranscriptPath(cwd, sessionId) {
  if (!sessionId) return null;
  const slug = cwd
    .replace(/\\/g, "/")
    .replace(/:/g, "-")
    .replace(/\//g, "-")
    .replace(/\./g, "-");
  const transcriptDir = path.join(os.homedir(), ".claude", "projects", slug);
  const transcriptFile = path.join(transcriptDir, `${sessionId}.jsonl`);
  return fs.existsSync(transcriptFile) ? transcriptFile : null;
}

/**
 * Extract recent conversation turns (user + assistant) from the JSONL transcript.
 */
function extractRecentTurns(transcriptPath, maxMessages) {
  try {
    const content = fs.readFileSync(transcriptPath, "utf8");
    const lines = content.trim().split("\n").slice(-MAX_TRANSCRIPT_LINES);
    const turns = [];
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        const isUser = entry.type === "human" || entry.type === "user";
        const isAssistant = entry.type === "assistant";
        if (!isUser && !isAssistant) continue;
        const raw = entry.message?.content ?? entry.content;
        const text = typeof raw === "string" ? raw
          : Array.isArray(raw)
            ? raw.filter((c) => c.type === "text").map((c) => c.text).join(" ")
            : "";
        if (!text || text.length < 5) continue;
        turns.push({ role: isUser ? "User" : "Assistant", text: text.slice(0, 400) });
      } catch {}
    }
    return turns.slice(-maxMessages);
  } catch {
    return [];
  }
}

/**
 * Store a mid-session checkpoint to Recall.
 * Never throws — Recall being down must never block compaction.
 */
async function storeRecallCheckpoint(cwd, sessionId) {
  const transcriptPath = deriveTranscriptPath(cwd, sessionId);
  if (!transcriptPath) return;

  const turns = extractRecentTurns(transcriptPath, 20);
  const hasAssistant = turns.some((t) => t.role === "Assistant");
  if (turns.length < 3 || !hasAssistant) return;

  const projectName = path.basename(cwd);
  const domain = PROJECT_DOMAINS[projectName.toLowerCase()] || projectName.toLowerCase() || "general";
  const turnText = turns.map((t) => `[${t.role}] ${t.text}`).join("\n");
  const content = [
    `[PreCompact Checkpoint] ${projectName} — ${turns.length} turns captured at context compaction (${new Date().toISOString().slice(0, 16)})`,
    turnText,
  ].join("\n\n");

  const headers = {
    "Content-Type": "application/json",
    ...(RECALL_API_KEY ? { Authorization: `Bearer ${RECALL_API_KEY}` } : {}),
  };

  try {
    await fetch(`${RECALL_HOST}/memory/store`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        content: content.slice(0, 4000),
        domain,
        source: "system",
        memory_type: "episodic",
        tags: ["precompact-checkpoint", projectName, "has-assistant-responses"],
        importance: 0.65,
      }),
      signal: AbortSignal.timeout(4000),
    });
  } catch { /* Recall down — never block compaction */ }
}

module.exports = { storeRecallCheckpoint };

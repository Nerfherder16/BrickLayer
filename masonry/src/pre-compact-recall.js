"use strict";
/**
 * Pre-compact Recall checkpoint.
 * Stores a mid-session summary to Recall so long-running sessions
 * that never close still get their context preserved.
 *
 * TODO: Implement full conversation capture + Recall API push.
 *       For now this is a no-op stub so the pre-compact hook doesn't crash.
 */

const RECALL_URL = process.env.RECALL_API_URL || "http://100.70.195.84:8200";

/**
 * Store a checkpoint to Recall before context compaction.
 * @param {string} cwd - Working directory (project root)
 * @param {string|undefined} sessionId - Claude session ID
 */
async function storeRecallCheckpoint(cwd, sessionId) {
  // Stub — no-op until full implementation.
  // When implemented: POST to ${RECALL_URL}/memory with a session summary
  // including user prompts + assistant responses from the current context window.
  void cwd;
  void sessionId;
}

module.exports = { storeRecallCheckpoint };

#!/usr/bin/env node
/**
 * Masonry Daemon Worker: consolidate
 *
 * Queries Recall for build-patterns, deduplicates similar ones by computing
 * text similarity, and removes near-duplicates to keep the pattern library clean.
 *
 * Interval: 2 hours (managed by daemon-manager.sh)
 */

"use strict";
const http = require("http");
const https = require("https");

const RECALL_HOST = process.env.RECALL_HOST || "http://100.70.195.84:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "";
const SIMILARITY_THRESHOLD = 0.85; // patterns this similar are considered duplicates

function httpRequest(method, urlStr, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const lib = url.protocol === "https:" ? https : http;
    const bodyStr = body ? JSON.stringify(body) : null;

    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === "https:" ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers: {
        "Content-Type": "application/json",
        ...(bodyStr ? { "Content-Length": Buffer.byteLength(bodyStr) } : {}),
        ...(RECALL_API_KEY ? { "Authorization": `Bearer ${RECALL_API_KEY}` } : {}),
      },
      timeout: 10000,
    };

    const req = lib.request(options, (res) => {
      let data = "";
      res.on("data", c => (data += c));
      res.on("end", () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data: data }); }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

// Compute Jaccard similarity between two strings (token-level)
function jaccardSimilarity(a, b) {
  const tokenize = s => new Set(s.toLowerCase().split(/\W+/).filter(t => t.length > 2));
  const setA = tokenize(a);
  const setB = tokenize(b);
  const intersection = new Set([...setA].filter(t => setB.has(t)));
  const union = new Set([...setA, ...setB]);
  return union.size === 0 ? 0 : intersection.size / union.size;
}

async function main() {
  const timestamp = new Date().toISOString();
  console.log(`[consolidate] Running at ${timestamp}`);

  // Query Recall for all build-patterns
  let memories = [];
  try {
    const result = await httpRequest("POST", `${RECALL_HOST}/search/query`, {
      query: "build pattern",
      domains: ["build-patterns"],
      limit: 100,
    });

    if (result.status >= 200 && result.status < 300) {
      const data = result.data;
      memories = Array.isArray(data) ? data : (data.results || data.memories || []);
    } else {
      console.log(`[consolidate] Recall returned ${result.status}, skipping`);
      return;
    }
  } catch (err) {
    console.log(`[consolidate] Recall unavailable: ${err.message}, skipping`);
    return;
  }

  console.log(`[consolidate] Found ${memories.length} build patterns`);

  if (memories.length < 2) {
    console.log("[consolidate] Not enough patterns to deduplicate");
    return;
  }

  // Find near-duplicate pairs
  const toDelete = new Set();
  let duplicateCount = 0;

  for (let i = 0; i < memories.length; i++) {
    if (toDelete.has(memories[i].id)) continue;

    for (let j = i + 1; j < memories.length; j++) {
      if (toDelete.has(memories[j].id)) continue;

      const contentA = memories[i].content || memories[i].text || "";
      const contentB = memories[j].content || memories[j].text || "";

      const sim = jaccardSimilarity(contentA, contentB);
      if (sim >= SIMILARITY_THRESHOLD) {
        // Keep the newer one (higher ID or more recent timestamp), delete the older
        const tsA = new Date(memories[i].created_at || memories[i].timestamp || 0).getTime();
        const tsB = new Date(memories[j].created_at || memories[j].timestamp || 0).getTime();

        const keepIdx = tsA >= tsB ? i : j;
        const deleteIdx = keepIdx === i ? j : i;

        toDelete.add(memories[deleteIdx].id);
        duplicateCount++;

        console.log(`[consolidate] Duplicate found (sim=${sim.toFixed(2)}): ${memories[deleteIdx].id} → keep ${memories[keepIdx].id}`);
      }
    }
  }

  // Delete duplicates from Recall
  let deleted = 0;
  for (const id of toDelete) {
    try {
      const result = await httpRequest("DELETE", `${RECALL_HOST}/memory/${id}`);
      if (result.status >= 200 && result.status < 300) {
        deleted++;
      } else {
        console.log(`[consolidate] Failed to delete ${id}: status ${result.status}`);
      }
    } catch (err) {
      console.log(`[consolidate] Error deleting ${id}: ${err.message}`);
    }
  }

  console.log(`[consolidate] Done — ${deleted}/${duplicateCount} duplicates removed, ${memories.length - deleted} patterns remain`);
}

main().catch(err => {
  console.error("[consolidate] Error:", err.message);
  process.exit(0);
});

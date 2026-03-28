#!/usr/bin/env node
/**
 * Masonry Daemon Worker: ultralearn
 *
 * Analyzes the last 20 git commits to extract build patterns and stores them
 * to Recall. Deeper than masonry-build-patterns.js (which fires per-write) —
 * ultralearn does retrospective analysis on completed work.
 *
 * Patterns extracted: language, framework, layer (router/service/model/component/test)
 * Stored to Recall: domain "build-patterns", tags: ["lang:X", "framework:X", "layer:X", "source:ultralearn"]
 *
 * Interval: 60 minutes (managed by daemon-manager.sh)
 */

"use strict";
const http = require("http");
const https = require("https");
const { execSync } = require("child_process");

const RECALL_HOST = process.env.RECALL_HOST || "http://100.70.195.84:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "";

function findProjectRoot() {
  try {
    return execSync("git rev-parse --show-toplevel", { encoding: "utf8", timeout: 3000 }).trim();
  } catch {
    return process.cwd();
  }
}

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

function extractPattern(files) {
  // Detect language from file extensions
  let lang = "unknown";
  if (files.some(f => f.endsWith(".py"))) lang = "python";
  else if (files.some(f => f.endsWith(".ts") || f.endsWith(".tsx"))) lang = "typescript";
  else if (files.some(f => f.endsWith(".rs"))) lang = "rust";
  else if (files.some(f => f.endsWith(".go"))) lang = "go";
  else if (files.some(f => f.endsWith(".js"))) lang = "javascript";

  // Detect framework from path signals
  let framework = "unknown";
  if (files.some(f => /routers?\/|router\.py/.test(f))) framework = "fastapi";
  else if (files.some(f => /components?\/|\.tsx$/.test(f))) framework = "react";
  else if (files.some(f => /routes?\//i.test(f) && /\.js$/.test(f))) framework = "express";
  else if (files.some(f => /schemas?\//.test(f) && /\.py$/.test(f))) framework = "pydantic";
  else if (files.some(f => /models?\//.test(f) && /\.py$/.test(f))) framework = "sqlalchemy";
  else if (files.some(f => /pages?\//.test(f) && /\.tsx?$/.test(f))) framework = "react";

  // Detect layer from path signals
  let layer = "implementation";
  const paths = files.join("/");
  if (/routers?\//.test(paths)) layer = "router";
  else if (/services?\//.test(paths)) layer = "service";
  else if (/models?\//.test(paths)) layer = "model";
  else if (/components?\//.test(paths)) layer = "component";
  else if (/hooks?\//.test(paths)) layer = "hook";
  else if (/test_|__tests__\/|\.test\.|\.spec\./.test(paths)) layer = "test";
  else if (/migrations?\//.test(paths)) layer = "migration";
  else if (/schemas?\//.test(paths)) layer = "schema";

  return { lang, framework, layer, files: files.slice(0, 5) };
}

async function patternExists(lang, framework, layer) {
  try {
    const result = await httpRequest("POST", `${RECALL_HOST}/search/query`, {
      query: `${framework} ${layer} ${lang}`,
      domains: ["build-patterns"],
      limit: 1,
      tags: [`lang:${lang}`, `framework:${framework}`, `layer:${layer}`, "source:ultralearn"],
    });
    if (result.status >= 200 && result.status < 300) {
      const data = result.data;
      const memories = Array.isArray(data) ? data : (data.results || data.memories || []);
      return memories.length > 0;
    }
  } catch { /* unavailable */ }
  return false;
}

async function storePattern(pattern, hash) {
  const content = `Pattern: ${pattern.framework} ${pattern.layer} (${pattern.lang}). Representative files: ${pattern.files.join(", ")}. Source: ultralearn commit ${hash}.`;
  try {
    const result = await httpRequest("POST", `${RECALL_HOST}/memory/store`, {
      domains: ["build-patterns"],
      content,
      tags: [`lang:${pattern.lang}`, `framework:${pattern.framework}`, `layer:${pattern.layer}`, "source:ultralearn"],
    });
    return result.status >= 200 && result.status < 300;
  } catch { return false; }
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  console.log(`[ultralearn] Running at ${timestamp} in ${root}`);

  // Get last 20 commits with file lists
  let logOutput;
  try {
    logOutput = execSync("git log --name-only -n 20 --format=COMMIT:%H:%s", {
      encoding: "utf8",
      timeout: 10000,
      cwd: root,
    });
  } catch (err) {
    console.log(`[ultralearn] git log failed: ${err.message}`);
    return;
  }

  // Parse commits: blocks separated by "COMMIT:hash:subject"
  const commits = [];
  let current = null;
  for (const line of logOutput.split("\n")) {
    if (line.startsWith("COMMIT:")) {
      if (current) commits.push(current);
      const [, hash, ...subjectParts] = line.split(":");
      current = { hash, subject: subjectParts.join(":"), files: [] };
    } else if (current && line.trim()) {
      current.files.push(line.trim());
    }
  }
  if (current && current.files.length > 0) commits.push(current);

  console.log(`[ultralearn] Parsed ${commits.length} commits`);

  // Extract and deduplicate patterns
  const seen = new Set();
  const patterns = [];
  for (const commit of commits) {
    if (commit.files.length === 0) continue;
    const p = extractPattern(commit.files);
    const key = `${p.lang}:${p.framework}:${p.layer}`;
    if (!seen.has(key) && p.lang !== "unknown") {
      seen.add(key);
      patterns.push({ ...p, hash: commit.hash });
    }
  }

  console.log(`[ultralearn] Found ${patterns.length} unique patterns`);

  // Store new patterns to Recall
  let stored = 0;
  let skipped = 0;
  for (const p of patterns) {
    const exists = await patternExists(p.lang, p.framework, p.layer);
    if (exists) {
      skipped++;
      continue;
    }
    const ok = await storePattern(p, p.hash);
    if (ok) {
      stored++;
      console.log(`[ultralearn] Stored: ${p.framework} ${p.layer} (${p.lang})`);
    }
  }

  console.log(`[ultralearn] Done — ${stored} new patterns stored, ${skipped} already in Recall`);
}

main().catch(err => {
  console.error("[ultralearn] Error:", err.message);
  process.exit(0);
});

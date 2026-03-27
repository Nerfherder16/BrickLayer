#!/usr/bin/env node
/**
 * Masonry Daemon Worker: document
 *
 * Scans source files modified in recent commits, finds undocumented functions
 * and classes, and stores documentation gaps + existing docstrings to Recall.
 * Helps Claude inject relevant docs context during code sessions.
 *
 * Stores to Recall: domain "documentation", tags: ["lang:X", "file:X", "source:document"]
 *
 * Interval: 60 minutes (managed by daemon-manager.sh)
 */

"use strict";
const fs = require("fs");
const path = require("path");
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
        catch { resolve({ status: res.statusCode, data }); }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

function extractPythonDocs(content, relPath) {
  const lines = content.split("\n");
  const entries = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const fnMatch = line.match(/^(?:async\s+)?def\s+(\w+)\s*\(/);
    const classMatch = line.match(/^class\s+(\w+)/);
    const match = fnMatch || classMatch;

    if (match) {
      const name = match[1];
      const kind = fnMatch ? "function" : "class";
      // Check next non-empty line for docstring
      let hasDoc = false;
      let docText = "";
      for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
        const trimmed = lines[j].trim();
        if (trimmed.startsWith('"""') || trimmed.startsWith("'''")) {
          hasDoc = true;
          docText = trimmed.replace(/^['"]{3}/, "").replace(/['"]{3}$/, "").trim().slice(0, 120);
          break;
        }
        if (trimmed && !trimmed.startsWith("#")) break;
      }
      entries.push({ name, kind, hasDoc, docText, line: i + 1, file: relPath, lang: "python" });
    }
    i++;
  }
  return entries;
}

function extractTypeScriptDocs(content, relPath) {
  const lines = content.split("\n");
  const entries = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Export functions and React components
    const fnMatch = line.match(/^export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)/);
    const arrowMatch = line.match(/^export\s+(?:const|let)\s+(\w+)\s*[:=]/);
    const classMatch = line.match(/^export\s+(?:default\s+)?class\s+(\w+)/);
    const interfaceMatch = line.match(/^export\s+(?:interface|type)\s+(\w+)/);

    const match = fnMatch || arrowMatch || classMatch || interfaceMatch;
    if (!match) continue;

    const name = match[1];
    const kind = classMatch ? "class" : interfaceMatch ? "type" : "function";
    // Check for JSDoc comment above
    let hasDoc = false;
    let docText = "";
    if (i > 0) {
      const prevLine = lines[i - 1].trim();
      if (prevLine === "*/") {
        // Find the start of the JSDoc block
        for (let j = i - 2; j >= Math.max(0, i - 10); j--) {
          const jl = lines[j].trim();
          if (jl.startsWith("/**") || jl.startsWith("/*")) {
            hasDoc = true;
            // Extract first meaningful line of the doc
            for (let k = j + 1; k < i - 1; k++) {
              const dl = lines[k].trim().replace(/^\*\s*/, "");
              if (dl && !dl.startsWith("@")) { docText = dl.slice(0, 120); break; }
            }
            break;
          }
        }
      }
    }
    entries.push({ name, kind, hasDoc, docText, line: i + 1, file: relPath, lang: "typescript" });
  }
  return entries;
}

async function main() {
  const root = findProjectRoot();
  const timestamp = new Date().toISOString();
  console.log(`[document] Running at ${timestamp}`);

  // Get recently modified source files (last 10 commits)
  let changedFiles = [];
  try {
    const out = execSync("git diff --name-only HEAD~10 HEAD 2>/dev/null || git diff --name-only HEAD", {
      encoding: "utf8", timeout: 8000, cwd: root,
    });
    changedFiles = out.trim().split("\n").filter(f =>
      f.endsWith(".py") || f.endsWith(".ts") || f.endsWith(".tsx")
    ).slice(0, 20);
  } catch {
    console.log("[document] git diff failed, scanning top-level source files");
  }

  if (changedFiles.length === 0) {
    console.log("[document] No changed source files found");
    return;
  }

  const allEntries = [];
  for (const rel of changedFiles) {
    const full = path.join(root, rel);
    try {
      const content = fs.readFileSync(full, "utf8");
      const entries = rel.endsWith(".py")
        ? extractPythonDocs(content, rel)
        : extractTypeScriptDocs(content, rel);
      allEntries.push(...entries);
    } catch { /* unreadable */ }
  }

  console.log(`[document] Extracted ${allEntries.length} symbols from ${changedFiles.length} files`);

  const undocumented = allEntries.filter(e => !e.hasDoc);
  const documented = allEntries.filter(e => e.hasDoc);

  // Build summary content for Recall
  const undocList = undocumented.slice(0, 20).map(e => `  ${e.kind} ${e.name}() at ${e.file}:${e.line}`).join("\n");
  const docList = documented.slice(0, 10).map(e => `  ${e.kind} ${e.name}: "${e.docText}"`).join("\n");

  if (allEntries.length === 0) {
    console.log("[document] No symbols to record");
    return;
  }

  const content = [
    `Documentation scan — ${timestamp.slice(0, 10)}`,
    `Files: ${changedFiles.join(", ")}`,
    ``,
    `Undocumented (${undocumented.length}):`,
    undocList || "  (none)",
    ``,
    `Documented (${documented.length}):`,
    docList || "  (none)",
  ].join("\n");

  const langs = [...new Set(allEntries.map(e => e.lang))];

  try {
    const result = await httpRequest("POST", `${RECALL_HOST}/api/memory`, {
      domain: "documentation",
      content: content.slice(0, 3000),
      tags: [
        ...langs.map(l => `lang:${l}`),
        "source:document",
        `files:${changedFiles.length}`,
        `undocumented:${undocumented.length}`,
      ],
    });
    if (result.status >= 200 && result.status < 300) {
      console.log(`[document] Stored to Recall — ${undocumented.length} undocumented, ${documented.length} documented symbols`);
    } else {
      console.log(`[document] Recall returned ${result.status}`);
    }
  } catch (err) {
    console.log(`[document] Recall unavailable: ${err.message}`);
  }
}

main().catch(err => {
  console.error("[document] Error:", err.message);
  process.exit(0);
});

#!/usr/bin/env node
/**
 * PostToolUse:Write|Edit hook (Masonry): Build Pattern Extraction
 *
 * When an autopilot build is active, extracts the build pattern from each
 * written file and stores it to Recall under domain "build-patterns".
 *
 * Extracted dimensions:
 *   - file_type: "python" | "typescript" | "javascript" | "rust" | "go" | etc.
 *   - framework: "fastapi" | "react" | "sqlalchemy" | "qdrant" | etc.
 *   - layer: "router" | "model" | "service" | "test" | "config" | etc.
 *   - pattern_name: inferred from filename + content structure
 *
 * Stored to Recall:
 *   domain: "build-patterns"
 *   tags: ["lang:python", "framework:fastapi", "layer:router"]
 *   content: summary of the pattern (filename + key constructs found)
 *
 * ASYNC: This hook runs async (does not block Claude).
 */

"use strict";
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");
const { readStdin } = require('./session/stop-utils');

const RECALL_HOST = process.env.RECALL_HOST || "http://100.70.195.84:8200";
const RECALL_API_KEY = process.env.RECALL_API_KEY || "";

function isAutopilotActive(cwd) {
  try {
    const mode = fs.readFileSync(path.join(cwd, ".autopilot", "mode"), "utf8").trim();
    return mode === "build" || mode === "fix";
  } catch { return false; }
}

function detectFileType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const map = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".kt": "kotlin",
    ".java": "java",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
  };
  return map[ext] || "unknown";
}

function detectFramework(content, filePath, fileType) {
  const text = content.toLowerCase();
  const fname = filePath.toLowerCase();

  // Python frameworks
  if (fileType === "python") {
    if (text.includes("from fastapi") || text.includes("import fastapi")) return "fastapi";
    if (text.includes("from sqlalchemy") || text.includes("import sqlalchemy")) return "sqlalchemy";
    if (text.includes("from qdrant_client")) return "qdrant";
    if (text.includes("from neo4j")) return "neo4j";
    if (text.includes("import redis")) return "redis";
    if (text.includes("import asyncio") && text.includes("async def")) return "asyncio";
    if (text.includes("import pytest") || fname.includes("test_")) return "pytest";
    if (text.includes("import pydantic") || text.includes("from pydantic")) return "pydantic";
    return "python";
  }

  // TypeScript/React frameworks
  if (fileType === "typescript") {
    if (text.includes("from 'react'") || text.includes("from \"react\"")) {
      if (text.includes("tailwind") || text.includes("classname")) return "react-tailwind";
      return "react";
    }
    if (text.includes("vitest") || text.includes("@testing-library")) return "vitest";
    if (text.includes("from 'express'") || text.includes("from \"express\"")) return "express";
    return "typescript";
  }

  // JavaScript
  if (fileType === "javascript") {
    if (fname.includes("hook") && (fname.includes("masonry") || fname.includes(".js"))) return "claude-hook";
    if (text.includes("require(") && text.includes("process.stdin")) return "claude-hook";
    return "javascript";
  }

  return fileType;
}

function detectLayer(filePath, content) {
  const fname = path.basename(filePath).toLowerCase();
  const dir = filePath.toLowerCase();

  if (fname.startsWith("test_") || fname.endsWith(".test.ts") || fname.endsWith(".test.tsx") || dir.includes("__tests__") || dir.includes("/tests/")) return "test";
  if (fname.includes("router") || dir.includes("/router") || dir.includes("/routers")) return "router";
  if (fname.includes("model") || dir.includes("/model") || dir.includes("/models")) return "model";
  if (fname.includes("service") || dir.includes("/service") || dir.includes("/services")) return "service";
  if (fname.includes("schema") || fname.includes("pydantic")) return "schema";
  if (fname.includes("migration") || dir.includes("/migrations") || dir.includes("/alembic")) return "migration";
  if (fname.includes("config") || fname.includes("settings") || fname.includes(".env")) return "config";
  if (fname.includes("hook") || dir.includes("/hooks")) return "hook";
  if (fname.includes("component") || fname.endsWith(".tsx") || fname.endsWith(".jsx")) return "component";
  if (fname.includes("util") || fname.includes("helper") || dir.includes("/utils")) return "util";
  if (fname.includes("middleware") || dir.includes("/middleware")) return "middleware";
  return "module";
}

function extractPatternName(filePath, content, framework, layer) {
  const fname = path.basename(filePath, path.extname(filePath));

  // Turn snake_case/kebab-case into a readable pattern name
  const cleanName = fname.replace(/[_-]/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  // Infer pattern from content constructs
  const constructs = [];
  if (content.includes("async def") || content.includes("async function")) constructs.push("async");
  if (content.includes("@router") || content.includes("app.get(") || content.includes("app.post(")) constructs.push("route-handler");
  if (content.includes("BaseModel") || content.includes("interface ")) constructs.push("typed-model");
  if (content.includes("await client") || content.includes("await session")) constructs.push("db-client");
  if (content.includes("cva(") || content.includes("VariantProps")) constructs.push("cva-variants");

  const constructStr = constructs.length ? ` (${constructs.slice(0, 2).join(", ")})` : "";
  return `${cleanName}${constructStr} [${framework}/${layer}]`;
}

function recallStore(domain, tags, content, metadata) {
  return new Promise((resolve) => {
    try {
      const body = JSON.stringify({
        domain,
        content,
        tags,
        metadata: metadata || {},
      });

      const url = new URL(`${RECALL_HOST}/memory/store`);
      const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === "https:" ? 443 : 80),
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
          ...(RECALL_API_KEY ? { "Authorization": `Bearer ${RECALL_API_KEY}` } : {}),
        },
        timeout: 5000,
      };

      const lib = url.protocol === "https:" ? https : http;
      const req = lib.request(options, (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => resolve({ ok: res.statusCode < 300, status: res.statusCode }));
      });
      req.on("error", () => resolve({ ok: false, error: "network" }));
      req.on("timeout", () => { req.destroy(); resolve({ ok: false, error: "timeout" }); });
      req.write(body);
      req.end();
    } catch { resolve({ ok: false, error: "exception" }); }
  });
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try { input = JSON.parse(raw); } catch {}

  const cwd = input.cwd || process.cwd();

  // Only active during autopilot builds
  if (!isAutopilotActive(cwd)) {
    process.exit(0);
  }

  // Get the file that was just written
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || "";
  const content = toolInput.content || toolInput.new_string || "";

  if (!filePath || !content) process.exit(0);

  // Skip non-source files
  const ext = path.extname(filePath).toLowerCase();
  const skippedExts = [".json", ".md", ".lock", ".gitignore", ".env", ".toml", ".ini", ".cfg"];
  if (skippedExts.includes(ext)) process.exit(0);

  // Extract pattern dimensions
  const fileType = detectFileType(filePath);
  if (fileType === "unknown") process.exit(0);

  const framework = detectFramework(content, filePath, fileType);
  const layer = detectLayer(filePath, content);
  const patternName = extractPatternName(filePath, content, framework, layer);

  // Build tags
  const tags = [
    `lang:${fileType}`,
    `framework:${framework}`,
    `layer:${layer}`,
    "source:autopilot-build",
  ];

  // Build summary content
  const lineCount = content.split("\n").length;
  const relPath = path.relative(cwd, filePath);
  const summary = [
    `Pattern: ${patternName}`,
    `File: ${relPath} (${lineCount} lines)`,
    `Stack: ${fileType} / ${framework} / ${layer}`,
    `Key constructs: ${extractKeyConstructs(content, fileType).join(", ") || "none detected"}`,
  ].join("\n");

  // Store to Recall
  await recallStore("build-patterns", tags, summary, {
    file_path: relPath,
    file_type: fileType,
    framework,
    layer,
    line_count: lineCount,
    cwd,
  });

  process.exit(0);
}

function extractKeyConstructs(content, fileType) {
  const constructs = [];

  if (fileType === "python") {
    if (content.includes("@router.get") || content.includes("@router.post")) constructs.push("FastAPI route");
    if (content.includes("class.*BaseModel")) constructs.push("Pydantic model");
    if (content.includes("async_session") || content.includes("AsyncSession")) constructs.push("async SQLAlchemy");
    if (content.includes("await client.search")) constructs.push("Qdrant search");
    if (content.includes("async def test_")) constructs.push("async pytest");
    if (content.includes("mocker.Mock")) constructs.push("pytest-mock");
  }

  if (fileType === "typescript") {
    if (content.includes("export function") && content.includes("JSX")) constructs.push("React component");
    if (content.includes("cva(")) constructs.push("cva variants");
    if (content.includes("useCallback") || content.includes("useMemo")) constructs.push("memoized hooks");
    if (content.includes("vi.fn()")) constructs.push("vitest mock");
    if (content.includes("ResponsiveLine") || content.includes("@nivo")) constructs.push("Nivo chart");
  }

  return constructs.slice(0, 3);
}

main().catch(() => process.exit(0));

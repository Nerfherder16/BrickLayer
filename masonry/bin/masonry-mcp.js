#!/usr/bin/env node
"use strict";
/**
 * bin/masonry-mcp.js — Masonry MCP server
 *
 * Exposes 5 tools over MCP stdio transport (JSON-RPC 2.0):
 *   - masonry_status      — current campaign state
 *   - masonry_findings    — recent findings with verdicts
 *   - masonry_questions   — question bank query
 *   - masonry_run         — launch a campaign subprocess
 *   - masonry_recall      — proxy to Recall memory API
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const http = require("http");
const https = require("https");
const { spawn } = require("child_process");
const readline = require("readline");

const pkg = require("../package.json");

// ---------------------------------------------------------------------------
// Config loader (mirrors src/core/config.js but inline — no external deps)
// ---------------------------------------------------------------------------

const CONFIG_PATH = path.join(os.homedir(), ".masonry", "config.json");

const CONFIG_DEFAULTS = {
  recallHost: "http://100.70.195.84:8200",
  recallApiKey: process.env.RECALL_API_KEY || "",
};

function loadConfig() {
  let fileConfig = {};
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      fileConfig = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
    }
  } catch (_err) {
    // optional — fall back to defaults
  }
  return {
    ...CONFIG_DEFAULTS,
    ...fileConfig,
    recallApiKey:
      process.env.RECALL_API_KEY ||
      fileConfig.recallApiKey ||
      CONFIG_DEFAULTS.recallApiKey,
  };
}

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: "masonry_status",
    description: "Get current campaign state for a Masonry project",
    inputSchema: {
      type: "object",
      properties: {
        project_path: {
          type: "string",
          description: "Absolute path to project directory",
        },
      },
      required: ["project_path"],
    },
  },
  {
    name: "masonry_findings",
    description: "List recent findings from a Masonry campaign",
    inputSchema: {
      type: "object",
      properties: {
        project_path: { type: "string" },
        limit: { type: "number", default: 10 },
        verdict_filter: {
          type: "string",
          description: "Filter by verdict (HEALTHY, FAILURE, etc). Optional.",
        },
      },
      required: ["project_path"],
    },
  },
  {
    name: "masonry_questions",
    description: "Query the question bank for a Masonry project",
    inputSchema: {
      type: "object",
      properties: {
        project_path: { type: "string" },
        status_filter: {
          type: "string",
          description:
            "PENDING, DONE, BLOCKED. Optional, returns all if omitted.",
        },
        limit: { type: "number", default: 20 },
      },
      required: ["project_path"],
    },
  },
  {
    name: "masonry_run",
    description: "Launch or resume a Masonry campaign in a detached subprocess",
    inputSchema: {
      type: "object",
      properties: {
        project_path: { type: "string" },
        mode: {
          type: "string",
          enum: ["new", "resume"],
          default: "resume",
        },
      },
      required: ["project_path"],
    },
  },
  {
    name: "masonry_recall",
    description: "Search Recall memory for a Masonry project domain",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        project: {
          type: "string",
          description: "Project name (used as domain: {project}-bricklayer)",
        },
        limit: { type: "number", default: 10 },
      },
      required: ["query", "project"],
    },
  },
];

// ---------------------------------------------------------------------------
// Tool implementations
// ---------------------------------------------------------------------------

function toolStatus(args) {
  const { project_path } = args;
  const projectName = path.basename(project_path);

  const stateFile = path.join(project_path, "masonry-state.json");
  const configFile = path.join(project_path, "masonry.json");

  let state = null;
  let masonryConfig = null;

  try {
    if (fs.existsSync(stateFile)) {
      state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    }
  } catch (_err) {
    // ignore parse errors
  }

  try {
    if (fs.existsSync(configFile)) {
      masonryConfig = JSON.parse(fs.readFileSync(configFile, "utf8"));
    }
  } catch (_err) {
    // ignore
  }

  if (!state) {
    return {
      status: "no_campaign",
      project: (masonryConfig && masonryConfig.name) || projectName,
      ...(masonryConfig ? { mode: masonryConfig.mode } : {}),
    };
  }

  return {
    project: (masonryConfig && masonryConfig.name) || projectName,
    ...(masonryConfig ? { mode: masonryConfig.mode } : {}),
    ...state,
  };
}

function toolFindings(args) {
  const { project_path, limit = 10, verdict_filter } = args;
  const findingsDir = path.join(project_path, "findings");

  if (!fs.existsSync(findingsDir)) {
    return [];
  }

  let files;
  try {
    files = fs
      .readdirSync(findingsDir)
      .filter(
        (f) =>
          f.endsWith(".md") &&
          f !== "synthesis.md" &&
          !f.startsWith("synthesis"),
      )
      .map((f) => {
        const fullPath = path.join(findingsDir, f);
        let mtime = 0;
        try {
          mtime = fs.statSync(fullPath).mtimeMs;
        } catch (_err) {
          // ignore
        }
        return { file: f, fullPath, mtime };
      })
      .sort((a, b) => b.mtime - a.mtime);
  } catch (_err) {
    return [];
  }

  const results = [];

  for (const { file, fullPath } of files) {
    if (results.length >= limit) break;

    let content = "";
    try {
      content = fs.readFileSync(fullPath, "utf8");
    } catch (_err) {
      continue;
    }

    // Parse fields from markdown
    const verdictMatch = content.match(/\*\*Verdict\*\*:\s*([^\n]+)/i);
    const agentMatch = content.match(/\*\*Agent\*\*:\s*([^\n]+)/i);

    // Extract only uppercase letters/underscores — handles "FIXED — desc", "FIXED`", etc.
    const rawVerdict = verdictMatch ? verdictMatch[1].trim() : "UNKNOWN";
    const verdictClean = rawVerdict.match(/^[A-Z_]+/);
    const verdict = verdictClean ? verdictClean[0] : "UNKNOWN";
    const agent = agentMatch ? agentMatch[1].trim() : "";

    if (
      verdict_filter &&
      verdict.toUpperCase() !== verdict_filter.toUpperCase()
    ) {
      continue;
    }

    // Use filename without extension as id
    const id = file.replace(/\.md$/, "");

    // Extract first non-empty, non-heading line as summary
    const lines = content.split("\n");
    let summary = "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (
        trimmed &&
        !trimmed.startsWith("#") &&
        !trimmed.startsWith("**") &&
        !trimmed.startsWith("```")
      ) {
        summary = trimmed.slice(0, 120);
        break;
      }
    }

    results.push({ id, verdict, agent, summary, path: fullPath });
  }

  return results;
}

function toolQuestions(args) {
  const { project_path, status_filter, limit = 20 } = args;
  const questionsFile = path.join(project_path, "questions.md");

  if (!fs.existsSync(questionsFile)) {
    return [];
  }

  let content = "";
  try {
    content = fs.readFileSync(questionsFile, "utf8");
  } catch (_err) {
    return [];
  }

  // Split on ## or ### headings; question IDs start with 1-3 uppercase letters + digits
  // e.g. D1, D15.1, F26.1, A24.1, V25.1, Q001 — wave/section headers don't match this
  const QUESTION_ID = /^[A-Z]{1,3}\d[\d.]*[\s:\[]/;
  const blocks = content.split(/^#{2,3} /m).filter(Boolean);
  const results = [];

  for (const block of blocks) {
    if (results.length >= limit) break;

    const lines = block.split("\n");
    const firstLine = lines[0].trim();

    // Skip wave headers and section preambles — only process real question blocks
    if (!QUESTION_ID.test(firstLine)) continue;

    // Extract fields
    const statusMatch = block.match(/\*\*Status\*\*:\s*([^\n]+)/i);
    // Accept both **Mode**: and **Operational Mode**: field names
    const modeMatch = block.match(/\*\*(?:Operational )?Mode\*\*:\s*([^\n]+)/i);
    const agentMatch = block.match(/\*\*Agent\*\*:\s*([^\n]+)/i);

    if (!statusMatch) continue;

    const status = statusMatch[1].trim();
    const mode = modeMatch ? modeMatch[1].trim() : "";
    const agent = agentMatch ? agentMatch[1].trim() : "";

    if (status_filter && status.toUpperCase() !== status_filter.toUpperCase()) {
      continue;
    }

    // The first line is the id/title; question text follows after the metadata
    // Collect non-metadata, non-empty lines as the question text
    const textLines = lines
      .slice(1)
      .filter((l) => {
        const t = l.trim();
        return (
          t &&
          !t.startsWith("**Status**") &&
          !t.startsWith("**Mode**") &&
          !t.startsWith("**Agent**")
        );
      })
      .slice(0, 3);

    const text = textLines.join(" ").trim().slice(0, 200);

    results.push({ id: firstLine, status, mode, agent, text });
  }

  return results;
}

function toolRun(args) {
  const { project_path, mode = "resume" } = args;
  const cfg = loadConfig();

  const prompt =
    mode === "new"
      ? "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md and project-brief.md. Begin the campaign from the first PENDING question. NEVER STOP."
      : "Act as the Mortar agent defined in .claude/agents/mortar.md. Read questions.md, project-brief.md, and findings/synthesis.md. Resume the campaign from the first PENDING question. NEVER STOP.";

  const env = { ...process.env };
  if (cfg.recallApiKey) {
    env.RECALL_API_KEY = cfg.recallApiKey;
  }

  const child = spawn("claude", ["--dangerously-skip-permissions", prompt], {
    cwd: project_path,
    env,
    detached: true,
    stdio: "ignore",
  });

  child.unref();

  return { launched: true, pid: child.pid, mode, project_path };
}

function httpRequest(urlStr, options, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const lib = url.protocol === "https:" ? https : http;

    const reqOptions = {
      hostname: url.hostname,
      port: url.port || (url.protocol === "https:" ? 443 : 80),
      path: url.pathname + url.search,
      method: options.method || "GET",
      headers: options.headers || {},
    };

    const req = lib.request(reqOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (_err) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on("error", reject);

    if (body) {
      req.write(body);
    }
    req.end();
  });
}

async function toolRecall(args) {
  const { query, project, limit = 10 } = args;
  const cfg = loadConfig();

  const domain = `${project}-bricklayer`;
  const payload = JSON.stringify({ query, domain, limit });

  try {
    const resp = await Promise.race([
      httpRequest(
        `${cfg.recallHost}/search`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(payload),
            ...(cfg.recallApiKey
              ? { Authorization: `Bearer ${cfg.recallApiKey}` }
              : {}),
          },
        },
        payload,
      ),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("timeout")), 5000),
      ),
    ]);

    if (resp.status >= 400) {
      return {
        error: "recall_error",
        message: `Recall returned HTTP ${resp.status}`,
      };
    }

    const data = resp.body;
    return Array.isArray(data) ? data : data.results || data;
  } catch (err) {
    return {
      error: "recall_unavailable",
      message: err.message || "Could not reach Recall",
    };
  }
}

// ---------------------------------------------------------------------------
// MCP protocol dispatch
// ---------------------------------------------------------------------------

async function dispatchTool(name, args) {
  switch (name) {
    case "masonry_status":
      return toolStatus(args);
    case "masonry_findings":
      return toolFindings(args);
    case "masonry_questions":
      return toolQuestions(args);
    case "masonry_run":
      return toolRun(args);
    case "masonry_recall":
      return await toolRecall(args);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function sendResponse(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function makeError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

async function handleRequest(raw) {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch (_err) {
    sendResponse(makeError(null, -32700, "Parse error"));
    return;
  }

  const { jsonrpc, id, method, params } = msg;

  if (jsonrpc !== "2.0") {
    sendResponse(makeError(id ?? null, -32600, "Invalid Request"));
    return;
  }

  // Notifications (no id) — ignore silently
  if (id === undefined || id === null) return;

  switch (method) {
    case "initialize": {
      sendResponse({
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "masonry-mcp", version: pkg.version },
        },
      });
      break;
    }

    case "tools/list": {
      sendResponse({
        jsonrpc: "2.0",
        id,
        result: { tools: TOOLS },
      });
      break;
    }

    case "tools/call": {
      const toolName = params && params.name;
      const toolArgs = (params && params.arguments) || {};

      if (!toolName) {
        sendResponse(makeError(id, -32602, "Missing tool name"));
        return;
      }

      try {
        const result = await dispatchTool(toolName, toolArgs);
        sendResponse({
          jsonrpc: "2.0",
          id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify(result, null, 2),
              },
            ],
          },
        });
      } catch (err) {
        sendResponse(
          makeError(id, -32603, err.message || "Tool execution error"),
        );
      }
      break;
    }

    // notifications/initialized — server-side notification, no response needed
    case "notifications/initialized":
      break;

    default: {
      sendResponse(makeError(id, -32601, `Method not found: ${method}`));
    }
  }
}

// ---------------------------------------------------------------------------
// Main — read stdin line by line
// ---------------------------------------------------------------------------

process.stderr.write(`masonry-mcp v${pkg.version} started\n`);

const rl = readline.createInterface({
  input: process.stdin,
  output: null,
  terminal: false,
  crlfDelay: Infinity,
});

rl.on("line", (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  handleRequest(trimmed).catch((err) => {
    process.stderr.write(`Unhandled error: ${err.message}\n`);
  });
});

rl.on("close", () => {
  process.exit(0);
});

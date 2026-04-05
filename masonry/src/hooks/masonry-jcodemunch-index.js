#!/usr/bin/env node
/**
 * PostToolUse:Write|Edit async child hook (Masonry): jcodemunch auto-index.
 *
 * Fires inside masonry-post-write-runner after every Write/Edit. Spawns the
 * jcodemunch-mcp server as a subprocess, does the MCP init handshake, then
 * calls index_file on the written path so the index is always current.
 *
 * Skips silently if:
 *   - File is not a source file (.js .ts .py .rs .go .java etc.)
 *   - File is inside node_modules / .git / dist / build
 *   - uvx is not available
 *   - MCP handshake or index call fails (non-blocking — never crashes the runner)
 */

'use strict';

const { spawn } = require('child_process');
const path = require('path');

const INDEXABLE_EXTS = new Set([
  '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx',
  '.py', '.rs', '.go', '.java', '.kt', '.cs',
  '.rb', '.php', '.swift', '.c', '.cpp', '.h',
]);

const SKIP_DIRS = ['node_modules', '.git', 'dist', 'build', '__pycache__', '.venv', 'target'];

function shouldIndex(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (!INDEXABLE_EXTS.has(ext)) return false;
  const parts = filePath.split(path.sep);
  return !parts.some(p => SKIP_DIRS.includes(p));
}

async function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => (data += c));
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 1000);
  });
}

/**
 * Minimal MCP stdio client. Spawns the server, does init handshake,
 * calls one tool, returns the result. Resolves (never rejects).
 */
function callMcpTool(toolName, toolArgs, timeoutMs = 12000) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (result) => {
      if (settled) return;
      settled = true;
      try { server.kill(); } catch {}
      resolve(result);
    };

    const timer = setTimeout(() => done({ error: 'timeout' }), timeoutMs);

    let server;
    try {
      server = spawn('uvx', ['jcodemunch-mcp'], {
        stdio: ['pipe', 'pipe', 'ignore'],
      });
    } catch {
      clearTimeout(timer);
      return resolve({ error: 'spawn failed' });
    }

    server.on('error', () => { clearTimeout(timer); done({ error: 'server error' }); });
    server.on('close', () => { clearTimeout(timer); done({ error: 'server closed' }); });

    let buf = '';
    let msgId = 0;
    let initialized = false;

    const send = (obj) => {
      try {
        server.stdin.write(JSON.stringify(obj) + '\n');
      } catch {}
    };

    server.stdout.on('data', (chunk) => {
      buf += chunk.toString();
      const lines = buf.split('\n');
      buf = lines.pop(); // keep incomplete line

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        let msg;
        try { msg = JSON.parse(trimmed); } catch { continue; }

        if (!initialized && (msg.result?.capabilities !== undefined || msg.id === 1)) {
          initialized = true;
          // Send initialized notification
          send({ jsonrpc: '2.0', method: 'notifications/initialized' });
          // Now call the tool
          msgId++;
          send({
            jsonrpc: '2.0',
            id: msgId,
            method: 'tools/call',
            params: { name: toolName, arguments: toolArgs },
          });
        } else if (msg.id === msgId) {
          clearTimeout(timer);
          done(msg.result || msg.error || {});
        }
      }
    });

    // Send initialize request
    msgId++;
    send({
      jsonrpc: '2.0',
      id: msgId,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'masonry-jcodemunch-index', version: '1.0' },
      },
    });
  });
}

async function main() {
  const raw = await readStdin();
  let parsed = {};
  try { parsed = JSON.parse(raw); } catch { process.exit(0); }

  // Works for both Write (file_path) and Edit (file_path)
  const filePath = parsed.tool_input?.file_path || parsed.tool_input?.path || '';
  if (!filePath) process.exit(0);
  if (!shouldIndex(filePath)) process.exit(0);

  // Resolve to absolute path
  const cwd = parsed.cwd || process.cwd();
  const absPath = path.isAbsolute(filePath) ? filePath : path.resolve(cwd, filePath);

  const result = await callMcpTool('index_file', {
    file_path: absPath,
    repo: cwd,
  });

  if (result?.error) {
    process.stderr.write(`[jcodemunch-index] ${result.error} — ${path.basename(filePath)}\n`);
  } else {
    process.stderr.write(`[jcodemunch-index] indexed ${path.basename(filePath)}\n`);
  }

  process.exit(0);
}

main().catch(() => process.exit(0));

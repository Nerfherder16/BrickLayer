'use strict';
/**
 * UserPromptSubmit hook — Recall context injection.
 * Queries Recall at the prompt text, prepends relevant memories as [RECALL] block.
 * Graceful-fail: exits 0 on any error so it never blocks prompt submission.
 */

const https = require('https');
const http = require('http');

const RECALL_HOST = process.env.RECALL_HOST || 'http://100.70.195.84:8200';
const THRESHOLD = 0.6;
const MAX_RESULTS = 3;
const TIMEOUT_MS = 4000;

function httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const mod = parsed.protocol === 'https:' ? https : http;
    const data = JSON.stringify(body);
    const req = mod.request(
      {
        hostname: parsed.hostname,
        port: parsed.port,
        path: parsed.pathname + parsed.search,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
        timeout: TIMEOUT_MS,
      },
      (res) => {
        let raw = '';
        res.on('data', (c) => (raw += c));
        res.on('end', () => {
          try { resolve(JSON.parse(raw)); } catch { resolve(null); }
        });
      }
    );
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

async function main() {
  let hookData = '';
  try {
    for await (const chunk of process.stdin) hookData += chunk;
  } catch { process.exit(0); }

  let prompt = '';
  try {
    const parsed = JSON.parse(hookData);
    prompt = parsed.prompt || '';
  } catch { process.exit(0); }

  if (!prompt.trim()) process.exit(0);

  try {
    const result = await httpPost(`${RECALL_HOST}/search`, {
      query: prompt.slice(0, 500),
      limit: MAX_RESULTS,
      min_score: THRESHOLD,
    });

    const memories = Array.isArray(result?.results) ? result.results : [];
    if (!memories.length) process.exit(0);

    const lines = memories
      .map((m) => `- ${(m.content || m.text || '').slice(0, 200).replace(/\n/g, ' ')}`)
      .filter(Boolean);

    if (!lines.length) process.exit(0);

    const block = `[RECALL] Relevant context from memory:\n${lines.join('\n')}`;
    process.stdout.write(JSON.stringify({ additionalContext: block }));
  } catch {
    // Recall unavailable — silent fail
  }

  process.exit(0);
}

main();

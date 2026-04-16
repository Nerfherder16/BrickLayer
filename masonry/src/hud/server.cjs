'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PORT = parseInt(process.env.HUD_PORT || '7824', 10);
const PID_FILE = '/tmp/hud-server.pid';
const POLL_INTERVAL_MS = 2000;

// DATA_ROOT lets tests inject a mock directory instead of .autopilot/
const DATA_ROOT = process.env.DATA_ROOT
  ? path.resolve(process.env.DATA_ROOT)
  : path.join(process.cwd(), '.autopilot');

const CONFIDENCE_FILE = path.join(DATA_ROOT, 'pattern-confidence.json');
const TELEMETRY_FILE = path.join(DATA_ROOT, 'telemetry.jsonl');

// In-memory state
let agentRecords = [];
let lastStateJson = '';
const sseConnections = new Set();

/**
 * Read and parse pattern-confidence.json.
 * Returns a map: agentName → { confidence, uses, lastUsed }
 */
function readConfidence() {
  try {
    const raw = fs.readFileSync(CONFIDENCE_FILE, 'utf8');
    const data = JSON.parse(raw);
    const result = {};
    for (const [name, val] of Object.entries(data)) {
      if (typeof val === 'number') {
        result[name] = { confidence: val, uses: 0, lastUsed: '' };
      } else if (val && typeof val === 'object') {
        result[name] = {
          confidence: typeof val.confidence === 'number' ? val.confidence : 0,
          uses: typeof val.uses === 'number' ? val.uses : 0,
          lastUsed: typeof val.last_used === 'string' ? val.last_used : '',
        };
      }
    }
    return result;
  } catch (err) {
    // Missing or unreadable file — return empty, keep last known state
    return null;
  }
}

/**
 * Read telemetry.jsonl and return a map: agentName → most-recent phase:post entry
 * { success, duration_ms, timestamp }
 */
function readTelemetry() {
  try {
    const raw = fs.readFileSync(TELEMETRY_FILE, 'utf8');
    const lines = raw.split('\n').filter(Boolean);
    // We want the most recent post entry per agent — iterate in order, overwrite
    const latest = {};
    for (const line of lines) {
      try {
        const rec = JSON.parse(line);
        if (rec.phase === 'post' && rec.agent) {
          // Keep overwriting — last occurrence wins (most recent in append-only log)
          latest[rec.agent] = {
            success: rec.success === true,
            duration_ms: typeof rec.duration_ms === 'number' ? rec.duration_ms : 0,
            timestamp: rec.timestamp || '',
          };
        }
      } catch (_) {
        process.stderr.write(`[hud] malformed telemetry line: ${line}\n`);
      }
    }
    return latest;
  } catch (_) {
    return {};
  }
}

/**
 * Rebuild AgentRecord[] from disk.
 * If confidence file is missing, keep last known agentRecords.
 */
function rebuildRecords() {
  const confidenceMap = readConfidence();
  if (confidenceMap === null) {
    // Keep last known — don't wipe state on transient read error
    return;
  }

  const telemetryMap = readTelemetry();

  const records = Object.entries(confidenceMap).map(([name, conf]) => {
    const tel = telemetryMap[name];
    return {
      name,
      confidence: conf.confidence,
      uses: conf.uses,
      lastResult: tel ? (tel.success ? 'pass' : 'fail') : 'unknown',
      lastDurationMs: tel ? tel.duration_ms : 0,
      lastUsed: conf.lastUsed,
    };
  });

  // Sort by confidence descending
  records.sort((a, b) => b.confidence - a.confidence);
  agentRecords = records;
}

/** Push update to all SSE clients if state changed */
function pollAndPush() {
  rebuildRecords();
  const newJson = JSON.stringify(agentRecords);
  if (newJson !== lastStateJson) {
    lastStateJson = newJson;
    const payload = JSON.stringify({ type: 'update', agents: agentRecords }) + '\n';
    for (const res of sseConnections) {
      try {
        res.write(payload);
      } catch (_) {
        sseConnections.delete(res);
      }
    }
  }
}

// ─── HTML page ───────────────────────────────────────────────────────────────

const HUD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BrickLayer HUD</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', system-ui, monospace; font-size: 14px; padding: 24px; }
  h1 { color: #58a6ff; margin-bottom: 16px; font-size: 18px; letter-spacing: 0.05em; }
  #status { color: #8b949e; margin-bottom: 12px; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; }
  thead tr { border-bottom: 2px solid #30363d; }
  th { text-align: left; padding: 8px 12px; color: #8b949e; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
  tbody tr { border-bottom: 1px solid #21262d; transition: background 0.1s; }
  tbody tr:hover { background: #161b22; }
  td { padding: 8px 12px; vertical-align: middle; }
  .bar-wrap { display: flex; align-items: center; gap: 8px; }
  .bar-bg { flex: 1; height: 6px; background: #21262d; border-radius: 3px; min-width: 60px; }
  .bar-fill { height: 100%; border-radius: 3px; }
  .bar-fill.green { background: #3fb950; }
  .bar-fill.yellow { background: #d29922; }
  .bar-fill.red { background: #f85149; }
  .pct { font-variant-numeric: tabular-nums; min-width: 42px; text-align: right; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
  .badge.pass { background: #1a3329; color: #3fb950; border: 1px solid #3fb95040; }
  .badge.fail { background: #3d1a1a; color: #f85149; border: 1px solid #f8514940; }
  .badge.unknown { background: #21262d; color: #8b949e; border: 1px solid #30363d; }
  .dur { font-variant-numeric: tabular-nums; color: #8b949e; }
  .agent-name { font-family: monospace; color: #e6edf3; }
  .ts { color: #8b949e; font-size: 12px; }
</style>
</head>
<body>
<h1>BrickLayer Agent HUD</h1>
<div id="status">Connecting…</div>
<table>
  <thead><tr>
    <th>Agent</th>
    <th>Confidence %</th>
    <th>Result</th>
    <th>Duration</th>
    <th>Last Used</th>
  </tr></thead>
  <tbody id="tbody"></tbody>
</table>
<script>
function fmtDur(ms) {
  if (!ms) return '—';
  if (ms < 1000) return ms + 'ms';
  if (ms < 60000) return (ms / 1000).toFixed(1) + 's';
  return (ms / 60000).toFixed(1) + 'm';
}
function fmtTs(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleString(); } catch(_) { return s; }
}
function barClass(pct) {
  if (pct >= 80) return 'green';
  if (pct >= 50) return 'yellow';
  return 'red';
}
function render(agents) {
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = agents.map(a => {
    const pct = Math.round(a.confidence * 100);
    const cls = barClass(pct);
    return \`<tr>
      <td class="agent-name">\${a.name}</td>
      <td>
        <div class="bar-wrap">
          <div class="bar-bg"><div class="bar-fill \${cls}" style="width:\${pct}%"></div></div>
          <span class="pct">\${pct}%</span>
        </div>
      </td>
      <td><span class="badge \${a.lastResult}">\${a.lastResult}</span></td>
      <td class="dur">\${fmtDur(a.lastDurationMs)}</td>
      <td class="ts">\${fmtTs(a.lastUsed)}</td>
    </tr>\`;
  }).join('');
}

const es = new EventSource('/events');
const status = document.getElementById('status');
es.onopen = () => { status.textContent = 'Live'; };
es.onerror = () => { status.textContent = 'Reconnecting…'; };
es.onmessage = (e) => {
  try {
    const msg = JSON.parse(e.data);
    if (msg.type === 'update') render(msg.agents);
  } catch(_) {}
};
// Also seed from /agents on load
fetch('/agents').then(r => r.json()).then(render).catch(() => {});
</script>
</body>
</html>`;

// ─── HTTP server ──────────────────────────────────────────────────────────────

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  if (req.method === 'GET' && url === '/health') {
    const body = JSON.stringify({ ok: true, port: PORT, agentCount: agentRecords.length });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
    return;
  }

  if (req.method === 'GET' && url === '/agents') {
    const body = JSON.stringify(agentRecords);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
    return;
  }

  if (req.method === 'GET' && url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/plain',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    });
    // Send current state immediately so client doesn't wait up to 2s
    res.write(JSON.stringify({ type: 'update', agents: agentRecords }) + '\n');
    sseConnections.add(res);
    req.on('close', () => sseConnections.delete(res));
    res.on('close', () => sseConnections.delete(res));
    return;
  }

  if (req.method === 'GET' && url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(HUD_HTML);
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'not found' }));
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    process.stderr.write(`port ${PORT} in use — is another HUD running?\n`);
    process.exit(1);
  }
  throw err;
});

// ─── Lifecycle ────────────────────────────────────────────────────────────────

function cleanup() {
  try { fs.unlinkSync(PID_FILE); } catch (_) {}
  process.exit(0);
}
process.on('SIGTERM', cleanup);
process.on('SIGINT', cleanup);

// Initial load then start polling
rebuildRecords();
lastStateJson = JSON.stringify(agentRecords);

server.listen(PORT, '127.0.0.1', () => {
  fs.writeFileSync(PID_FILE, String(process.pid));
  process.stdout.write(`HUD server listening on port ${PORT}\n`);
});

const pollTimer = setInterval(pollAndPush, POLL_INTERVAL_MS);
// Don't let the timer keep the process alive if server closes
pollTimer.unref();

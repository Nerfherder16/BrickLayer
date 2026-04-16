'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PID_FILE = '/tmp/brainstorm-server.pid';

// Chronicle DB (optional — server works without it)
const db = (() => {
  try { return require('./chronicle-db'); } catch (e) {
    console.error('chronicle-db unavailable:', e.message); return null;
  }
})();

// In-memory state
const state = {
  sections: new Map(),
  events: [],
  sessionId: null,
};

// SSE-style event stream clients
const eventClients = new Set();

function broadcastEvent(event) {
  const line = JSON.stringify(event) + '\n';
  for (const res of eventClients) {
    try {
      res.write(line);
    } catch (_) {
      eventClients.delete(res);
    }
  }
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks).toString()));
    req.on('error', reject);
  });
}

function serveHTML(res) {
  const templatePath = path.join(__dirname, 'frame-template.html');
  const helperPath = path.join(__dirname, 'helper.js');

  let html = fs.readFileSync(templatePath, 'utf8');
  const helperJS = fs.readFileSync(helperPath, 'utf8');

  // Inline helper.js into the template
  html = html.replace('/* HELPER_JS_INLINE */', helperJS);

  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    ...corsHeaders(),
  });
  res.end(html);
}

function handleRequest(req, res) {
  const url = new URL(req.url, `http://localhost`);
  const pathname = url.pathname;

  // Handle preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, corsHeaders());
    res.end();
    return;
  }

  if (req.method === 'GET' && pathname === '/') {
    serveHTML(res);
    return;
  }

  if (req.method === 'GET' && pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
    res.end(JSON.stringify({ ok: true, port: parseInt(process.env.BRAINSTORM_PORT || '7823') }));
    return;
  }

  if (req.method === 'GET' && pathname === '/state') {
    const sections = Array.from(state.sections.values());
    const lastUpdated = sections.length > 0
      ? sections.reduce((a, b) => a.updated_at > b.updated_at ? a : b).updated_at
      : null;
    res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
    res.end(JSON.stringify({ sections, last_updated: lastUpdated }));
    return;
  }

  if (req.method === 'POST' && pathname === '/section') {
    readBody(req).then((body) => {
      let data;
      try {
        data = JSON.parse(body);
      } catch (_) {
        res.writeHead(400, { 'Content-Type': 'application/json', ...corsHeaders() });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }

      const { id, title, content, status } = data;
      if (!id || !title) {
        res.writeHead(400, { 'Content-Type': 'application/json', ...corsHeaders() });
        res.end(JSON.stringify({ error: 'id and title are required' }));
        return;
      }

      const validStatuses = ['draft', 'approved', 'flagged'];
      const sectionStatus = validStatuses.includes(status) ? status : 'draft';

      const now = new Date().toISOString();
      const section = {
        id,
        title,
        content: content || '',
        status: sectionStatus,
        updated_at: now,
      };

      state.sections.set(id, section);

      // Persist to chronicle DB if session is active
      if (state.sessionId) {
        db?.addSection(state.sessionId, {
          section_id: id, title, content: content || '',
          status: sectionStatus, posted_at: now,
        });
      }

      const event = { ts: now, type: 'section_update', section_id: id, action: null };
      state.events.push(event);
      broadcastEvent(event);

      res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ ok: true, section }));
    }).catch((err) => {
      res.writeHead(500, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ error: err.message }));
    });
    return;
  }

  if (req.method === 'POST' && pathname === '/click') {
    readBody(req).then((body) => {
      let data;
      try {
        data = JSON.parse(body);
      } catch (_) {
        res.writeHead(400, { 'Content-Type': 'application/json', ...corsHeaders() });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }

      const { section_id, action } = data;
      if (!section_id || !action) {
        res.writeHead(400, { 'Content-Type': 'application/json', ...corsHeaders() });
        res.end(JSON.stringify({ error: 'section_id and action are required' }));
        return;
      }

      const validActions = ['approve', 'flag', 'expand'];
      if (!validActions.includes(action)) {
        res.writeHead(400, { 'Content-Type': 'application/json', ...corsHeaders() });
        res.end(JSON.stringify({ error: 'action must be approve, flag, or expand' }));
        return;
      }

      const now = new Date().toISOString();

      // Update section status based on action
      if (state.sections.has(section_id)) {
        const section = state.sections.get(section_id);
        if (action === 'approve') {
          section.status = 'approved';
          section.updated_at = now;
        } else if (action === 'flag') {
          section.status = 'flagged';
          section.updated_at = now;
        } else if (action === 'expand') {
          section.content = (section.content || '') + '\n[expand requested]';
          section.updated_at = now;
        }
        state.sections.set(section_id, section);
      }

      // Persist status to chronicle DB
      if (state.sessionId && (action === 'approve' || action === 'flag')) {
        db?.updateSectionStatus(state.sessionId, section_id,
          action === 'approve' ? 'approved' : 'flagged');
      }

      const event = { ts: now, type: 'click', section_id, action };
      state.events.push(event);
      broadcastEvent(event);

      res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ ok: true }));
    }).catch((err) => {
      res.writeHead(500, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ error: err.message }));
    });
    return;
  }

  if (req.method === 'GET' && pathname === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      ...corsHeaders(),
    });

    // Stream all existing events
    for (const event of state.events) {
      res.write(JSON.stringify(event) + '\n');
    }

    // Register as streaming client
    eventClients.add(res);

    // Remove on disconnect
    res.on('close', () => {
      eventClients.delete(res);
    });

    return;
  }

  // POST /session — start a new chronicle session
  if (req.method === 'POST' && pathname === '/session') {
    readBody(req).then((body) => {
      let data = {};
      try { data = JSON.parse(body); } catch (_) {}
      const slug = (data.slug || 'unnamed').replace(/[^a-z0-9-]/gi, '-').toLowerCase();
      const sessionId = db?.createSession(slug) ?? null;
      state.sessionId = sessionId;
      if (sessionId) {
        try {
          fs.writeFileSync(
            path.join(process.cwd(), '.autopilot', 'current-session-id'),
            String(sessionId)
          );
        } catch (_) {}
      }
      res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ ok: true, sessionId }));
    }).catch((err) => {
      res.writeHead(500, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ error: err.message }));
    });
    return;
  }

  // GET /chronicle — list all sessions
  if (req.method === 'GET' && pathname === '/chronicle') {
    const sessions = db?.getSessions() ?? [];
    res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
    res.end(JSON.stringify(sessions));
    return;
  }

  // GET /chronicle/:id — full session detail
  if (req.method === 'GET' && /^\/chronicle\/\d+$/.test(pathname)) {
    const id = parseInt(pathname.split('/')[2], 10);
    const detail = db?.getSession(id) ?? null;
    if (!detail) {
      res.writeHead(404, { 'Content-Type': 'application/json', ...corsHeaders() });
      res.end(JSON.stringify({ error: 'Session not found' }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json', ...corsHeaders() });
    res.end(JSON.stringify(detail));
    return;
  }

  // 404
  res.writeHead(404, { 'Content-Type': 'application/json', ...corsHeaders() });
  res.end(JSON.stringify({ error: 'Not found' }));
}

function startServer(port) {
  const server = http.createServer(handleRequest);

  return new Promise((resolve, reject) => {
    server.on('error', reject);
    server.listen(port, '127.0.0.1', () => {
      resolve(server);
    });
  });
}

// Standalone entry point
if (require.main === module) {
  const port = parseInt(process.env.BRAINSTORM_PORT || '7823');

  startServer(port).then((server) => {
    // Write PID file
    fs.writeFileSync(PID_FILE, String(process.pid));

    console.log(`Brainstorm server running at http://localhost:${port}`);

    function shutdown() {
      try { fs.unlinkSync(PID_FILE); } catch (_) {}
      server.close();
      process.exit(0);
    }

    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  }).catch((err) => {
    console.error('Failed to start server:', err.message);
    process.exit(1);
  });
}

module.exports = { startServer, state };

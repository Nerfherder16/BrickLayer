'use strict';
const http = require('http');
const WebSocket = require('ws');
const pty = require('node-pty');
const { verifyJwt, wsAuthMiddleware } = require('../../shared/auth');

const PORT = 3001;
const REPLAY_BUFFER_SIZE = 100 * 1024; // 100KB

// HTTP server for health endpoint
const httpServer = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy' }));
    return;
  }
  res.writeHead(404);
  res.end();
});

// WebSocket server
const wss = new WebSocket.Server({ server: httpServer });

// Session store for reconnection support
const sessions = new Map();

wss.on('connection', (ws, req) => {
  let ptyProcess = null;
  let sessionId = null;
  let replayBuffer = [];
  let ackCounter = 0;
  let heartbeat = null;

  // Heartbeat: ping every 30s
  heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.ping();
    }
  }, 30000);

  ws.on('pong', () => {
    // Connection alive
  });

  ws.once('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());

      // JWT validation from first message
      if (!msg.token) {
        ws.close(4001, 'Authentication required');
        return;
      }

      let payload;
      try {
        payload = verifyJwt(msg.token);
      } catch (e) {
        ws.close(4001, 'Invalid token: ' + e.message);
        return;
      }

      // Check for reconnection
      if (msg.session_id && sessions.has(msg.session_id)) {
        const session = sessions.get(msg.session_id);
        sessionId = msg.session_id;
        ptyProcess = session.ptyProcess;
        replayBuffer = session.replayBuffer;

        // Replay buffer
        if (replayBuffer.length > 0) {
          ws.send(JSON.stringify({ type: 'replay', data: replayBuffer.join('') }));
        }
      } else {
        // New session
        sessionId = Math.random().toString(36).substr(2, 9);

        ptyProcess = pty.spawn('bash', [], {
          name: 'xterm-color',
          cols: msg.cols || 80,
          rows: msg.rows || 24,
          cwd: process.env.HOME || '/tmp',
          env: process.env,
        });

        sessions.set(sessionId, { ptyProcess, replayBuffer });

        ptyProcess.onData((data) => {
          // Add to replay buffer (cap at 100KB)
          const totalSize = replayBuffer.reduce((s, d) => s + d.length, 0);
          if (totalSize + data.length > REPLAY_BUFFER_SIZE) {
            while (
              replayBuffer.length > 0 &&
              replayBuffer.reduce((s, d) => s + d.length, 0) + data.length > REPLAY_BUFFER_SIZE
            ) {
              replayBuffer.shift();
            }
          }
          replayBuffer.push(data);

          ackCounter++;
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'data', id: ackCounter, data }));
          }
        });

        ptyProcess.onExit(() => {
          sessions.delete(sessionId);
          if (ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        });
      }

      ws.send(JSON.stringify({ type: 'connected', session_id: sessionId }));

      // Handle subsequent messages
      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data.toString());
          if (msg.type === 'data' && ptyProcess) {
            ptyProcess.write(msg.data);
          } else if (msg.type === 'resize' && ptyProcess) {
            ptyProcess.resize(msg.cols || 80, msg.rows || 24);
          } else if (msg.type === 'ack') {
            // Flow control acknowledgment
          }
        } catch (e) {}
      });
    } catch (e) {
      ws.close(4001, 'Invalid message format');
    }
  });

  ws.on('close', () => {
    clearInterval(heartbeat);
    if (ptyProcess && sessionId) {
      // Graceful shutdown: SIGHUP -> 5s -> SIGKILL
      try {
        ptyProcess.kill('SIGHUP');
        setTimeout(() => {
          try {
            ptyProcess.kill('SIGKILL');
          } catch (e) {}
          sessions.delete(sessionId);
        }, 5000);
      } catch (e) {}
    }
  });
});

httpServer.listen(PORT, () => {
  console.log(`ptyHost listening on port ${PORT}`);
});

module.exports = { httpServer, wss };

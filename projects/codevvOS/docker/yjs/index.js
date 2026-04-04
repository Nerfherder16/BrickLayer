'use strict';
const http = require('http');
const WebSocket = require('ws');

const PORT = 1234;

const { verifyJwt } = require('../../shared/auth');

const httpServer = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy' }));
    return;
  }
  res.writeHead(404);
  res.end();
});

const wss = new WebSocket.Server({ server: httpServer });

const docs = new Map();

wss.on('connection', (ws) => {
  ws.once('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());
      if (!msg.token) { ws.close(4001, 'Auth required'); return; }
      try { verifyJwt(msg.token); } catch (e) { ws.close(4001, 'Invalid token'); return; }

      const room = msg.room || 'default';
      ws.send(JSON.stringify({ type: 'connected', room }));

      ws.on('message', (update) => {
        wss.clients.forEach(c => {
          if (c !== ws && c.readyState === WebSocket.OPEN) c.send(update);
        });
      });
    } catch (e) { ws.close(4001, 'Bad format'); }
  });
});

httpServer.listen(PORT, () => console.log('Yjs server on port ' + PORT));
module.exports = { httpServer, wss };

'use strict';
const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');

function getSecret() {
  const secretPath = '/run/secrets/jwt_secret';
  try {
    if (fs.existsSync(secretPath)) {
      return fs.readFileSync(secretPath, 'utf8').trim();
    }
  } catch (e) {}
  return process.env.JWT_SECRET || 'dev-jwt-secret-change-in-prod';
}

function createJwt(userId, tenantId, role, expiresIn = '1h') {
  return jwt.sign(
    { user_id: userId, tenant_id: tenantId, role },
    getSecret(),
    { algorithm: 'HS256', expiresIn }
  );
}

function verifyJwt(token) {
  // Check algorithm before verification
  const decoded = jwt.decode(token, { complete: true });
  if (!decoded) throw new Error('Invalid token format');
  if (decoded.header && decoded.header.alg && decoded.header.alg.toLowerCase() === 'none') {
    throw new Error("Algorithm 'none' is not allowed");
  }
  return jwt.verify(token, getSecret(), { algorithms: ['HS256'] });
}

function wsAuthMiddleware(ws, req, next) {
  let reCheckInterval = null;

  ws.once('message', (data) => {
    try {
      const msg = typeof data === 'string' ? JSON.parse(data) : JSON.parse(data.toString());
      if (!msg.token) {
        ws.close(4001, 'Authentication required');
        return;
      }
      const payload = verifyJwt(msg.token);
      ws.user = payload;

      // Re-check token expiry every 60 seconds
      reCheckInterval = setInterval(() => {
        try {
          verifyJwt(msg.token);
        } catch (e) {
          ws.close(4001, 'Token expired');
        }
      }, 60000);

      ws.on('close', () => {
        if (reCheckInterval) clearInterval(reCheckInterval);
      });

      if (typeof next === 'function') next();
    } catch (e) {
      ws.close(4001, 'Invalid token: ' + e.message);
    }
  });
}

module.exports = { createJwt, verifyJwt, wsAuthMiddleware };

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');
const https = require('https');
const { execSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');

function httpRequest(urlStr, options, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const lib = url.protocol === 'https:' ? https : http;

    const reqOptions = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname + url.search,
      method: options.method || 'GET',
      headers: options.headers || {},
    };

    const req = lib.request(reqOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (_err) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function callPython(code, inputObj) {
  const tmpDir = os.tmpdir();
  const scriptFile = path.join(tmpDir, `masonry-mcp-${process.pid}-${Date.now()}.py`);
  const inputFile = path.join(tmpDir, `masonry-mcp-${process.pid}-${Date.now()}.json`);

  const script = [
    'import sys, json',
    `sys.path.insert(0, ${JSON.stringify(REPO_ROOT)})`,
    `args = json.loads(open(${JSON.stringify(inputFile)}).read())`,
    code,
  ].join('\n');

  try {
    fs.writeFileSync(scriptFile, script, 'utf8');
    fs.writeFileSync(inputFile, JSON.stringify(inputObj), 'utf8');
    const result = execSync(`python "${scriptFile}"`, {
      timeout: 15000,
      encoding: 'utf8',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
    });
    return JSON.parse(result.trim());
  } catch (err) {
    return { error: err.stderr || err.message || 'Python subprocess failed' };
  } finally {
    try { fs.unlinkSync(scriptFile); } catch (_) {}
    try { fs.unlinkSync(inputFile); } catch (_) {}
  }
}

module.exports = { httpRequest, callPython, REPO_ROOT };

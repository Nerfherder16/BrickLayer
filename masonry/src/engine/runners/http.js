'use strict';
// engine/runners/http.js — Simple HTTP request runner.
//
// Port of bl/runners/http.py to Node.js.

const { cfg } = require('../config');

const _URL_RE = /https?:\/\/\S+/;
const _METHOD_RE = /^\s*(GET|POST|PUT|DELETE|PATCH)\s+/i;

function _parseHttpSpec(testField) {
  const spec = {
    method: 'GET',
    url: null,
    body: null,
    expectStatus: 200,
    expectBody: null,
    latencyMs: 2000,
    useAuth: false,
  };

  for (const line of testField.split('\n')) {
    const stripped = line.trim();
    if (!stripped) continue;
    const low = stripped.toLowerCase();

    if (low.startsWith('expect_status:')) {
      const val = parseInt(stripped.slice(stripped.indexOf(':') + 1).trim(), 10);
      if (!isNaN(val)) spec.expectStatus = val;
      continue;
    }
    if (low.startsWith('expect_body:')) {
      spec.expectBody = stripped.slice(stripped.indexOf(':') + 1).trim();
      continue;
    }
    if (low.startsWith('latency_threshold_ms:')) {
      const val = parseInt(stripped.slice(stripped.indexOf(':') + 1).trim(), 10);
      if (!isNaN(val)) spec.latencyMs = val;
      continue;
    }
    if (low.startsWith('auth:') && low.includes('bearer')) {
      spec.useAuth = true;
      continue;
    }

    const urlMatch = stripped.match(_URL_RE);
    if (urlMatch && spec.url === null) {
      spec.url = urlMatch[0].replace(/[/.,;]+$/, '');
      const methodMatch = stripped.match(_METHOD_RE);
      if (methodMatch) {
        spec.method = methodMatch[1].toUpperCase();
      }
      const remainder = stripped.slice(urlMatch.index + urlMatch[0].length).trim();
      if (remainder) {
        spec.body = remainder;
      }
    }
  }

  if (spec.url === null) {
    spec.url = (cfg.baseUrl || 'http://localhost:8200').replace(/\/+$/, '') + '/health';
  }

  return spec;
}

function _buildHttpVerdict({ method, url, statusCode, elapsedMs, responseBody, expectStatus, latencyThreshold, expectBody }) {
  let verdict = 'HEALTHY';
  const failureReasons = [];

  if (statusCode !== expectStatus) {
    verdict = 'FAILURE';
    failureReasons.push(`status ${statusCode} != expected ${expectStatus}`);
  }

  if (elapsedMs > latencyThreshold) {
    verdict = 'FAILURE';
    failureReasons.push(`latency ${elapsedMs}ms > threshold ${latencyThreshold}ms`);
  } else if (verdict === 'HEALTHY' && elapsedMs > latencyThreshold * 0.7) {
    verdict = 'WARNING';
    failureReasons.push(`latency ${elapsedMs}ms approaching threshold ${latencyThreshold}ms (>70%)`);
  }

  if (expectBody !== null && !responseBody.includes(expectBody)) {
    verdict = 'FAILURE';
    failureReasons.push(`expected body substring '${expectBody}' not found`);
  }

  let summary = `HTTP ${method} ${url} → ${statusCode} in ${elapsedMs}ms`;
  if (failureReasons.length) {
    summary += ' | ' + failureReasons.join('; ');
  }

  return {
    verdict,
    summary,
    data: {
      method,
      url,
      status_code: statusCode,
      elapsed_ms: elapsedMs,
      latency_threshold_ms: latencyThreshold,
      body_preview: responseBody.slice(0, 200),
    },
    details: `Status: ${statusCode} (expected ${expectStatus})\nLatency: ${elapsedMs}ms (threshold: ${latencyThreshold}ms)\nBody: ${responseBody.slice(0, 300)}`,
  };
}

async function runHttp(question) {
  const testField = question.test || question.Test || '';
  const spec = _parseHttpSpec(testField);

  const { method, url, expectStatus, latencyMs: latencyThreshold, expectBody } = spec;

  const headers = { 'Content-Type': 'application/json' };
  let body = null;
  if (spec.body) {
    try {
      body = JSON.parse(spec.body);
    } catch {
      body = spec.body;
    }
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), (cfg.requestTimeout || 30) * 1000);

    const fetchOpts = { method, headers, signal: controller.signal };
    if (body && method !== 'GET') {
      fetchOpts.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    const start = Date.now();
    const resp = await fetch(url, fetchOpts);
    const elapsedMs = Date.now() - start;
    clearTimeout(timeoutId);

    const responseBody = await resp.text();

    return _buildHttpVerdict({
      method, url,
      statusCode: resp.status,
      elapsedMs,
      responseBody,
      expectStatus,
      latencyThreshold,
      expectBody,
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      return {
        verdict: 'INCONCLUSIVE',
        summary: `HTTP ${method} ${url} — timeout after ${cfg.requestTimeout || 30}s`,
        data: { method, url, error: 'timeout' },
        details: `Request timed out after ${cfg.requestTimeout || 30}s`,
      };
    }
    return {
      verdict: 'INCONCLUSIVE',
      summary: `HTTP ${method} ${url} — ${err.message}`,
      data: { method, url, error: err.message },
      details: `Error: ${err.message}`,
    };
  }
}

module.exports = {
  runHttp,
  _parseHttpSpec,
  _buildHttpVerdict,
};

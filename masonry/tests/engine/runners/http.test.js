import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/http — parseHttpSpec', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'http.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should parse GET request with URL', () => {
    const spec = mod._parseHttpSpec('GET http://localhost:8200/health');
    expect(spec.method).toBe('GET');
    expect(spec.url).toBe('http://localhost:8200/health');
  });

  it('should parse POST request', () => {
    const spec = mod._parseHttpSpec('POST http://localhost:8200/api/search {"query":"test"}');
    expect(spec.method).toBe('POST');
    expect(spec.url).toBe('http://localhost:8200/api/search');
    expect(spec.body).toBe('{"query":"test"}');
  });

  it('should parse directive lines', () => {
    const spec = mod._parseHttpSpec(
      'GET http://localhost/test\nexpect_status: 201\nexpect_body: success\nlatency_threshold_ms: 500',
    );
    expect(spec.expectStatus).toBe(201);
    expect(spec.expectBody).toBe('success');
    expect(spec.latencyMs).toBe(500);
  });

  it('should detect auth: bearer', () => {
    const spec = mod._parseHttpSpec('GET http://localhost/api\nauth: bearer');
    expect(spec.useAuth).toBe(true);
  });

  it('should default method to GET', () => {
    const spec = mod._parseHttpSpec('http://localhost:8200/health');
    expect(spec.method).toBe('GET');
    expect(spec.url).toBe('http://localhost:8200/health');
  });

  it('should use default values for missing directives', () => {
    const spec = mod._parseHttpSpec('http://localhost/x');
    expect(spec.expectStatus).toBe(200);
    expect(spec.latencyMs).toBe(2000);
    expect(spec.expectBody).toBeNull();
    expect(spec.useAuth).toBe(false);
  });

  it('should strip trailing punctuation from URL', () => {
    const spec = mod._parseHttpSpec('GET http://localhost/path,');
    expect(spec.url).toBe('http://localhost/path');
  });
});

describe('engine/runners/http — buildHttpVerdict', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'http.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return HEALTHY when all checks pass', () => {
    const result = mod._buildHttpVerdict({
      method: 'GET',
      url: 'http://localhost/health',
      statusCode: 200,
      elapsedMs: 50,
      responseBody: 'ok',
      expectStatus: 200,
      latencyThreshold: 2000,
      expectBody: null,
    });
    expect(result.verdict).toBe('HEALTHY');
  });

  it('should return FAILURE on status mismatch', () => {
    const result = mod._buildHttpVerdict({
      method: 'GET',
      url: 'http://localhost/health',
      statusCode: 500,
      elapsedMs: 50,
      responseBody: '',
      expectStatus: 200,
      latencyThreshold: 2000,
      expectBody: null,
    });
    expect(result.verdict).toBe('FAILURE');
    expect(result.summary).toContain('500');
  });

  it('should return FAILURE on latency exceeded', () => {
    const result = mod._buildHttpVerdict({
      method: 'GET',
      url: 'http://localhost/health',
      statusCode: 200,
      elapsedMs: 3000,
      responseBody: '',
      expectStatus: 200,
      latencyThreshold: 2000,
      expectBody: null,
    });
    expect(result.verdict).toBe('FAILURE');
  });

  it('should return WARNING on latency approaching threshold (>70%)', () => {
    const result = mod._buildHttpVerdict({
      method: 'GET',
      url: 'http://localhost/health',
      statusCode: 200,
      elapsedMs: 1500,
      responseBody: '',
      expectStatus: 200,
      latencyThreshold: 2000,
      expectBody: null,
    });
    expect(result.verdict).toBe('WARNING');
  });

  it('should return FAILURE when expected body missing', () => {
    const result = mod._buildHttpVerdict({
      method: 'GET',
      url: 'http://localhost/health',
      statusCode: 200,
      elapsedMs: 50,
      responseBody: 'error occurred',
      expectStatus: 200,
      latencyThreshold: 2000,
      expectBody: 'success',
    });
    expect(result.verdict).toBe('FAILURE');
  });
});

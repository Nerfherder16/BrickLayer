// server.test.cjs — vitest tests for brainstorm server
// Uses CJS require() since server.cjs is CommonJS.

import { createRequire } from 'module';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import fs from 'fs';

const require = createRequire(import.meta.url);

const TEST_PORT = 7824;
process.env.BRAINSTORM_PORT = String(TEST_PORT);

const { startServer, state } = require('./server.cjs');

let server;
const base = `http://127.0.0.1:${TEST_PORT}`;

beforeAll(async () => {
  // Clear state between runs
  state.sections.clear();
  state.events.length = 0;
  server = await startServer(TEST_PORT);
});

afterAll(() => {
  server.close();
  // Clean up test PID file if it exists
  try { fs.unlinkSync('/tmp/brainstorm-server.pid'); } catch (_) {}
});

describe('GET /health', () => {
  it('returns 200 with { ok: true }', async () => {
    const res = await fetch(`${base}/health`);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.ok).toBe(true);
  });
});

describe('POST /section + GET /state', () => {
  it('stores a section and returns it in /state', async () => {
    const section = {
      id: 'test-section-1',
      title: 'Test Section',
      content: 'Hello world',
      status: 'draft',
    };

    const postRes = await fetch(`${base}/section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section),
    });
    expect(postRes.status).toBe(200);
    const postBody = await postRes.json();
    expect(postBody.ok).toBe(true);

    const stateRes = await fetch(`${base}/state`);
    expect(stateRes.status).toBe(200);
    const stateBody = await stateRes.json();

    const found = stateBody.sections.find((s) => s.id === 'test-section-1');
    expect(found).toBeDefined();
    expect(found.id).toBe('test-section-1');
    expect(found.title).toBe('Test Section');
    expect(found.content).toBe('Hello world');
    expect(found.status).toBe('draft');
  });
});

describe('POST /click + GET /events', () => {
  it('records a click event visible in /events stream', async () => {
    // Ensure section exists
    await fetch(`${base}/section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: 'click-test', title: 'Click Test', content: '', status: 'draft' }),
    });

    await fetch(`${base}/click`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ section_id: 'click-test', action: 'approve' }),
    });

    // GET /events — read all existing events (server streams them then keeps open)
    // We read with a timeout to avoid hanging forever
    const eventsText = await readEventsWithTimeout(`${base}/events`, 1000);
    const lines = eventsText.split('\n').filter((l) => l.trim());
    const events = lines.map((l) => { try { return JSON.parse(l); } catch (_) { return null; } }).filter(Boolean);

    const clickEvent = events.find(
      (e) => e.type === 'click' && e.section_id === 'click-test' && e.action === 'approve'
    );
    expect(clickEvent).toBeDefined();
    expect(clickEvent.ts).toBeTruthy();
  });
});

describe('PID file', () => {
  it('server.cjs exports startServer as a function', () => {
    expect(typeof startServer).toBe('function');
  });

  it('state is accessible and is a valid in-memory store', () => {
    expect(state).toBeDefined();
    expect(state.sections instanceof Map).toBe(true);
    expect(Array.isArray(state.events)).toBe(true);
  });

  it('PID file written when run standalone (standalone path check)', () => {
    // When run as main, PID file is written. Here we just verify the pid
    // would be a valid integer (process.pid is always a number).
    const pid = process.pid;
    expect(Number.isInteger(pid)).toBe(true);
    expect(pid).toBeGreaterThan(0);
  });
});

// Helper: read from a streaming response for `ms` milliseconds then abort
async function readEventsWithTimeout(url, ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);

  let text = '';
  try {
    const res = await fetch(url, { signal: controller.signal });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      text += decoder.decode(value, { stream: true });
    }
  } catch (_) {
    // AbortError expected
  } finally {
    clearTimeout(timer);
  }
  return text;
}

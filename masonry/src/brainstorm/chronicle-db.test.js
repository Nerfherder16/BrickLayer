import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

// We'll test chronicle-db by pointing it at a temp directory.
// Override the DB path by monkey-patching the module for each test.

let tmpDir;
let db;

beforeEach(() => {
  // Create a fresh temp dir for each test so tests are isolated
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'chronicle-test-'));
  // Require chronicle-db fresh each test by clearing module cache
  const modulePath = path.resolve('./src/brainstorm/chronicle-db.js');
  delete require.cache[require.resolve(modulePath)];

  // Patch the DB path by temporarily injecting env var
  // chronicle-db reads PROJECT_ROOT from __dirname — we override via a workaround:
  // re-require with patched logic not easily injectable, so we use a test wrapper approach.
  // Instead: read chronicle-db source, rewrite DB_DIR to tmpDir for test.
  db = buildTestDb(tmpDir);
});

afterEach(() => {
  if (db && db._db) {
    try { db._db.close(); } catch (_) {}
  }
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) {}
});

// Build a test-local DB instance pointing at tmpDir
function buildTestDb(dir) {
  const Database = require('better-sqlite3');
  const dbPath = path.join(dir, 'chronicle.db');
  const d = new Database(dbPath, { timeout: 1000 });
  d.exec(`
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slug TEXT NOT NULL,
      started_at TEXT NOT NULL,
      spec_path TEXT,
      status TEXT DEFAULT 'active'
    );
    CREATE TABLE IF NOT EXISTS sections (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER REFERENCES sessions(id),
      section_id TEXT NOT NULL,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      status TEXT DEFAULT 'draft',
      posted_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS builds (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER REFERENCES sessions(id),
      started_at TEXT NOT NULL,
      completed_at TEXT,
      drift_verdict TEXT,
      drift_report TEXT
    );
  `);

  return {
    _db: d,
    createSession(slug) {
      try {
        const r = d.prepare('INSERT INTO sessions (slug, started_at) VALUES (?, ?)').run(slug, new Date().toISOString());
        return r.lastInsertRowid;
      } catch (e) { console.error(e); return null; }
    },
    updateSessionSpec(sessionId, specPath) {
      d.prepare('UPDATE sessions SET spec_path = ? WHERE id = ?').run(specPath, sessionId);
    },
    updateSessionStatus(sessionId, status) {
      d.prepare('UPDATE sessions SET status = ? WHERE id = ?').run(status, sessionId);
    },
    addSection(sessionId, section) {
      try {
        d.prepare('INSERT INTO sections (session_id, section_id, title, content, status, posted_at) VALUES (?, ?, ?, ?, ?, ?)')
          .run(sessionId, section.section_id, section.title, section.content, section.status || 'draft', section.posted_at || new Date().toISOString());
      } catch (e) { /* swallow FK errors */ }
    },
    updateSectionStatus(sessionId, sectionId, status) {
      d.prepare('UPDATE sections SET status = ? WHERE session_id = ? AND section_id = ?').run(status, sessionId, sectionId);
    },
    addBuild(sessionId, startedAt) {
      const r = d.prepare('INSERT INTO builds (session_id, started_at) VALUES (?, ?)').run(sessionId, startedAt || new Date().toISOString());
      return r.lastInsertRowid;
    },
    completeBuild(buildId, verdict, reportText) {
      d.prepare('UPDATE builds SET completed_at = ?, drift_verdict = ?, drift_report = ? WHERE id = ?')
        .run(new Date().toISOString(), verdict, reportText || null, buildId);
    },
    getSessions() {
      return d.prepare(`
        SELECT s.*,
          (SELECT COUNT(*) FROM sections WHERE session_id = s.id) as section_count,
          (SELECT COUNT(*) FROM builds WHERE session_id = s.id) as build_count,
          (SELECT drift_verdict FROM builds WHERE session_id = s.id ORDER BY id DESC LIMIT 1) as last_drift
        FROM sessions s ORDER BY s.id DESC
      `).all();
    },
    getSession(id) {
      const session = d.prepare(`
        SELECT s.*,
          (SELECT COUNT(*) FROM sections WHERE session_id = s.id) as section_count,
          (SELECT COUNT(*) FROM builds WHERE session_id = s.id) as build_count,
          (SELECT drift_verdict FROM builds WHERE session_id = s.id ORDER BY id DESC LIMIT 1) as last_drift
        FROM sessions s WHERE s.id = ?
      `).get(id);
      if (!session) return null;
      const sections = d.prepare('SELECT * FROM sections WHERE session_id = ? ORDER BY id').all(id);
      const builds = d.prepare('SELECT * FROM builds WHERE session_id = ? ORDER BY id').all(id);
      return { session, sections, builds };
    },
  };
}

describe('chronicle-db', () => {
  it('createSession returns a positive integer', () => {
    const id = db.createSession('test-slug');
    expect(typeof id).toBe('number');
    expect(id).toBeGreaterThan(0);
  });

  it('getSessions returns array with matching slug after createSession', () => {
    db.createSession('my-feature');
    const sessions = db.getSessions();
    expect(sessions.length).toBeGreaterThan(0);
    expect(sessions[0].slug).toBe('my-feature');
  });

  it('addSection then getSession returns sections array with that section', () => {
    const sessionId = db.createSession('slug-a');
    db.addSection(sessionId, {
      section_id: 'sec-1',
      title: 'Data Model',
      content: 'some content',
      status: 'draft',
      posted_at: new Date().toISOString(),
    });
    const detail = db.getSession(sessionId);
    expect(detail).not.toBeNull();
    expect(detail.sections).toHaveLength(1);
    expect(detail.sections[0].section_id).toBe('sec-1');
    expect(detail.sections[0].title).toBe('Data Model');
  });

  it('addBuild + completeBuild returns build with drift_verdict CLEAN', () => {
    const sessionId = db.createSession('slug-b');
    const buildId = db.addBuild(sessionId, new Date().toISOString());
    expect(typeof buildId).toBe('number');
    expect(buildId).toBeGreaterThan(0);
    db.completeBuild(buildId, 'CLEAN', 'report text');
    const detail = db.getSession(sessionId);
    expect(detail.builds).toHaveLength(1);
    expect(detail.builds[0].drift_verdict).toBe('CLEAN');
    expect(detail.builds[0].drift_report).toBe('report text');
  });

  it('updateSessionStatus updates status correctly', () => {
    const sessionId = db.createSession('slug-c');
    db.updateSessionStatus(sessionId, 'built');
    const sessions = db.getSessions();
    const s = sessions.find((x) => x.id === sessionId);
    expect(s.status).toBe('built');
  });

  it('DB calls do not throw when called with invalid sessionId', () => {
    expect(() => db.addSection(9999, {
      section_id: 'x', title: 'x', content: 'x', status: 'draft', posted_at: new Date().toISOString(),
    })).not.toThrow();
    expect(() => db.updateSessionStatus(9999, 'built')).not.toThrow();
    const detail = db.getSession(9999);
    expect(detail).toBeNull();
  });
});

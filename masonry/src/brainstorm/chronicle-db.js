'use strict';

const fs = require('fs');
const path = require('path');

// Project root is 3 levels up from masonry/src/brainstorm/
const PROJECT_ROOT = path.resolve(__dirname, '../../../');
const DB_DIR = path.join(PROJECT_ROOT, '.brainstorm');
const DB_PATH = path.join(DB_DIR, 'chronicle.db');

let db = null;

function getDb() {
  if (db) return db;
  try {
    fs.mkdirSync(DB_DIR, { recursive: true });
    const Database = require('better-sqlite3');
    db = new Database(DB_PATH, { timeout: 1000 });
    createTables(db);
    return db;
  } catch (e) {
    console.error('chronicle-db: failed to open DB:', e.message);
    return null;
  }
}

function createTables(d) {
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
}

function createSession(slug) {
  try {
    const d = getDb();
    if (!d) return null;
    const stmt = d.prepare('INSERT INTO sessions (slug, started_at) VALUES (?, ?)');
    const result = stmt.run(slug, new Date().toISOString());
    return result.lastInsertRowid;
  } catch (e) {
    console.error('chronicle-db createSession:', e.message);
    return null;
  }
}

function updateSessionSpec(sessionId, specPath) {
  try {
    const d = getDb();
    if (!d) return;
    d.prepare('UPDATE sessions SET spec_path = ? WHERE id = ?').run(specPath, sessionId);
  } catch (e) {
    console.error('chronicle-db updateSessionSpec:', e.message);
  }
}

function updateSessionStatus(sessionId, status) {
  try {
    const d = getDb();
    if (!d) return;
    d.prepare('UPDATE sessions SET status = ? WHERE id = ?').run(status, sessionId);
  } catch (e) {
    console.error('chronicle-db updateSessionStatus:', e.message);
  }
}

function addSection(sessionId, section) {
  try {
    const d = getDb();
    if (!d) return;
    d.prepare(
      'INSERT INTO sections (session_id, section_id, title, content, status, posted_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).run(
      sessionId,
      section.section_id,
      section.title,
      section.content,
      section.status || 'draft',
      section.posted_at || new Date().toISOString()
    );
  } catch (e) {
    console.error('chronicle-db addSection:', e.message);
  }
}

function updateSectionStatus(sessionId, sectionId, status) {
  try {
    const d = getDb();
    if (!d) return;
    d.prepare(
      'UPDATE sections SET status = ? WHERE session_id = ? AND section_id = ?'
    ).run(status, sessionId, sectionId);
  } catch (e) {
    console.error('chronicle-db updateSectionStatus:', e.message);
  }
}

function addBuild(sessionId, startedAt) {
  try {
    const d = getDb();
    if (!d) return null;
    const result = d.prepare(
      'INSERT INTO builds (session_id, started_at) VALUES (?, ?)'
    ).run(sessionId, startedAt || new Date().toISOString());
    return result.lastInsertRowid;
  } catch (e) {
    console.error('chronicle-db addBuild:', e.message);
    return null;
  }
}

function completeBuild(buildId, verdict, reportText) {
  try {
    const d = getDb();
    if (!d) return;
    d.prepare(
      'UPDATE builds SET completed_at = ?, drift_verdict = ?, drift_report = ? WHERE id = ?'
    ).run(new Date().toISOString(), verdict, reportText || null, buildId);
  } catch (e) {
    console.error('chronicle-db completeBuild:', e.message);
  }
}

function getSessions() {
  try {
    const d = getDb();
    if (!d) return [];
    return d.prepare(`
      SELECT s.*,
        (SELECT COUNT(*) FROM sections WHERE session_id = s.id) as section_count,
        (SELECT COUNT(*) FROM builds WHERE session_id = s.id) as build_count,
        (SELECT drift_verdict FROM builds WHERE session_id = s.id ORDER BY id DESC LIMIT 1) as last_drift
      FROM sessions s ORDER BY s.id DESC
    `).all();
  } catch (e) {
    console.error('chronicle-db getSessions:', e.message);
    return [];
  }
}

function getSession(id) {
  try {
    const d = getDb();
    if (!d) return null;
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
  } catch (e) {
    console.error('chronicle-db getSession:', e.message);
    return null;
  }
}

module.exports = {
  createSession,
  updateSessionSpec,
  updateSessionStatus,
  addSection,
  updateSectionStatus,
  addBuild,
  completeBuild,
  getSessions,
  getSession,
};

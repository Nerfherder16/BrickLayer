-- Recall 2.0 initial schema
-- SQLite side: structured queries, migration tracking, analytics

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS memories (
    uuid            TEXT PRIMARY KEY,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    tags            TEXT NOT NULL DEFAULT '[]',  -- JSON array
    importance      REAL NOT NULL DEFAULT 0.5,
    provenance      TEXT NOT NULL DEFAULT 'Derived',
    metadata        TEXT NOT NULL DEFAULT '{}',  -- JSON object
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    access_count    INTEGER NOT NULL DEFAULT 0,
    last_accessed   TEXT
);

CREATE INDEX idx_memories_content_hash ON memories(content_hash);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_memories_provenance ON memories(provenance);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_last_accessed ON memories(last_accessed);

CREATE TABLE IF NOT EXISTS co_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    a_id        TEXT NOT NULL,
    b_id        TEXT NOT NULL,
    session_id  TEXT,
    source      TEXT NOT NULL DEFAULT 'organic',  -- 'organic' | 'BootstrapMigration'
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (a_id) REFERENCES memories(uuid),
    FOREIGN KEY (b_id) REFERENCES memories(uuid)
);

CREATE INDEX idx_co_events_a_id ON co_events(a_id);
CREATE INDEX idx_co_events_b_id ON co_events(b_id);
CREATE INDEX idx_co_events_session ON co_events(session_id);

CREATE TABLE IF NOT EXISTS health_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    s1_topk_consistency REAL,
    s2_edge_density     REAL,
    s3_bootstrap_bias   REAL,
    s4_write_latency_p95_ms REAL,
    memory_count        INTEGER,
    edge_count          INTEGER,
    captured_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Record initial migration
INSERT INTO schema_migrations (version, name) VALUES (1, '001_initial');

# Spec: Project Chronicle
Date: 2026-04-16
Status: DRAFT

## Problem Statement
Each feature designed in a brainstorm session, built via /build, and validated by the drift detector produces disconnected artifacts: canvas sections, a spec file, a drift report. There is no way to view the full lifecycle of a feature in one place — to answer "what did we design, what got built, and how accurately?" Project Chronicle links these artifacts into a persistent timeline.

## Chosen Approach
**Approach A — SQLite in `.brainstorm/chronicle.db`, viewer tab in the brainstorm canvas.** Uses `better-sqlite3` which is already in `masonry/package.json`. No new dependencies. The chronicle DB is written by two existing components (brainstorm server, drift detector) via a shared module. The viewer lives as a new tab in the existing canvas rather than a separate UI.

## Data Model

SQLite database at `.brainstorm/chronicle.db`. Three tables:

```sql
CREATE TABLE sessions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT NOT NULL,
  started_at  TEXT NOT NULL,
  spec_path   TEXT,
  status      TEXT DEFAULT 'active'
  -- status values: active | spec_written | built | drifted
);

CREATE TABLE sections (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  INTEGER REFERENCES sessions(id),
  section_id  TEXT NOT NULL,
  title       TEXT NOT NULL,
  content     TEXT NOT NULL,
  status      TEXT DEFAULT 'draft',
  -- status values: draft | approved | flagged
  posted_at   TEXT NOT NULL
);

CREATE TABLE builds (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id    INTEGER REFERENCES sessions(id),
  started_at    TEXT NOT NULL,
  completed_at  TEXT,
  drift_verdict TEXT,
  -- drift_verdict values: CLEAN | DRIFT_DETECTED | null (in-progress)
  drift_report  TEXT
  -- full contents of drift-report.md, stored at build completion
);
```

## API / Interface Contract

New endpoints added to the existing brainstorm server (port 7823):

```
GET /chronicle
Response: SessionSummary[]  (newest first)
[
  {
    "id": 1,
    "slug": "hud-widget",
    "startedAt": "2026-04-16T02:00:00Z",
    "specPath": "docs/specs/2026-04-16-hud-spec.md",
    "status": "built",
    "sectionCount": 8,
    "buildCount": 1,
    "lastDrift": "CLEAN"
  }
]

GET /chronicle/:id
Response: {
  "session": { ...SessionSummary },
  "sections": [ ...Section[] ],
  "builds": [ ...Build[] ]
}
```

**Shared DB module:** `masonry/src/brainstorm/chronicle-db.js`

Exported functions:
```
createSession(slug)                           → session id (integer)
updateSessionSpec(sessionId, specPath)
updateSessionStatus(sessionId, status)
addSection(sessionId, sectionObj)
updateSectionStatus(sessionId, sectionId, status)
addBuild(sessionId, startedAt)               → build id (integer)
completeBuild(buildId, verdict, reportText)
getSessions()                                → SessionSummary[]
getSession(id)                               → { session, sections, builds }
```

The brainstorm server calls the session/section functions. The drift detector calls the build functions. The server reads via `getSessions()` / `getSession()` to serve the `/chronicle` endpoints.

The active session id is written to `.autopilot/current-session-id` by the brainstorm server when a session is created, so the drift detector can find it without a server roundtrip.

## User / System Flow

**When /brainstorm session starts (Step 3 — after clarifying questions answered):**
1. Server calls `createSession(slug)` — slug derived from the feature name answer
2. Session id stored in server memory and written to `.autopilot/current-session-id`

**As design sections are posted:**
3. Each `POST /section` also calls `addSection(sessionId, section)`
4. Each `POST /click` (approve/flag) calls `updateSectionStatus(sessionId, sectionId, status)`
5. `sessions.status` stays `"active"`

**When spec is written (Step 6 of /brainstorm):**
6. Server calls `updateSessionSpec(id, specPath)` and `updateSessionStatus(id, "spec_written")`

**When /build starts:**
7. Drift detector reads `.autopilot/current-session-id`
8. Calls `addBuild(sessionId, now)` → build row created with `completed_at = null`
9. `updateSessionStatus(sessionId, "built")`

**When /build completes and drift detection runs:**
10. Drift detector calls `completeBuild(buildId, verdict, reportText)`
11. If `verdict === "DRIFT_DETECTED"`: `updateSessionStatus(sessionId, "drifted")`

**Chronicle tab in canvas:**
12. User clicks "Chronicle" tab → canvas calls `GET /chronicle`
13. Timeline renders: session slug → spec file link → build result → drift verdict
14. User clicks a row → `GET /chronicle/:id` → full section history shown inline

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| `.brainstorm/` dir missing | `fs.mkdirSync` on module load | Auto-created, no user action needed |
| `better-sqlite3` not installed | `require()` throws | Print "Run: npm install in masonry/", exit 1 |
| DB file corrupt / unreadable | SQLite throws on open | Log error to stderr; brainstorm server continues without chronicle; sections still post to canvas |
| `createSession` fails | DB write throws | Log to stderr; `session_id` = null; sections post normally, not persisted |
| `current-session-id` missing when drift runs | `fs.existsSync` | Skip chronicle write; drift report still written to `.autopilot/drift-report.md` |
| `addBuild` or `completeBuild` fails | DB write throws | Log to stderr; drift report still written normally |
| `GET /chronicle` error | HTTP 500 | Canvas shows "Chronicle unavailable" message; rest of canvas unaffected |
| DB locked by concurrent write | SQLite busy timeout (1s configured on open) | Throw → treated as DB write failure above |

**Core principle:** Chronicle persistence is always additive and optional. If the DB fails at any point, the brainstorm session and drift detection continue unaffected.

## Out of Scope
- Querying or searching chronicle across sessions (view only)
- Exporting chronicle to external formats (Markdown, JSON)
- Linking a single build to multiple specs
- Chronicle entries for builds run without a preceding brainstorm session
- Editing or deleting chronicle entries

## Open Questions
_(none)_

# Spec: BrickLayer Dev Tools — HUD, Drift Detector, Project Chronicle

## Goal
Add three developer experience tools to BrickLayer: a live Agent Performance HUD for monitoring agent confidence during builds, a Spec Drift Detector that compares what was built against what was specced, and a Project Chronicle that links brainstorm sessions → specs → builds → drift reports in a persistent SQLite timeline.

## Success Criteria
- [ ] `masonry/src/hud/` server starts on port 7824, serves a live agent table reading from `pattern-confidence.json` + `telemetry.jsonl`, updates every 2s
- [ ] `masonry/src/hooks/drift-detector.js` runs after /build, computes matched/onlyInSpec/onlyInDiff sets, writes `.autopilot/drift-report.md` and `.autopilot/drift-summary.txt`, exits 0/1/2
- [ ] `/drift` skill invokes drift-detector.js on demand
- [ ] `masonry-session-start.js` injects last-build drift summary into fresh sessions
- [ ] `masonry/src/brainstorm/chronicle-db.js` provides a `better-sqlite3` DB module with session/section/build tables
- [ ] Brainstorm server gains `GET /chronicle` and `GET /chronicle/:id` endpoints
- [ ] Brainstorm canvas gains a "Chronicle" tab that renders the timeline
- [ ] All vitest tests pass: 0 failures across hud, drift-detector, chronicle-db

## Tasks

- [ ] **Task 1** — Build HUD server
  **Files:**
  - `masonry/src/hud/server.cjs` (create)
  - `masonry/src/hud/start-server.sh` (create)
  - `masonry/src/hud/stop-server.sh` (create)
  - `masonry/src/hud/server.test.cjs` (create)

  **What to build:**
  Zero-dependency Node.js HTTP server (only `http`, `fs`, `path`, `os` builtins). Port 7824, configurable via `HUD_PORT` env var. PID written to `/tmp/hud-server.pid` on start, deleted on SIGTERM/SIGINT.

  Data sources (both paths relative to `process.cwd()` at server start — must be run from project root):
  - `.autopilot/pattern-confidence.json` — shape: `{ "<agent>": { confidence: number, uses: number, last_used: string } }`
  - `.autopilot/telemetry.jsonl` — one JSON per line, use only `phase: "post"` lines, shape: `{ agent: string, success: boolean, duration_ms: number, timestamp: string }`

  In-memory AgentRecord (keyed by agent name, rebuilt every 2s):
  ```
  { name, confidence, uses, lastResult: "pass"|"fail"|"unknown", lastDurationMs, lastUsed }
  ```
  For each agent name, find the most recent `phase: "post"` telemetry line to get `lastResult` and `lastDurationMs`. If no telemetry line for that agent, set `lastResult: "unknown"`, `lastDurationMs: 0`.

  Endpoints:
  - `GET /health` → `{ ok: true, port: 7824, agentCount: N }`
  - `GET /agents` → `AgentRecord[]` sorted by `confidence` descending
  - `GET /events` → `text/plain` keep-alive JSONL stream; push `{ type: "update", agents: AgentRecord[] }` on each poll cycle where state changed (compare JSON.stringify of previous vs current)
  - `GET /` → self-contained HUD HTML page (dark theme: `#0d1117` bg, `#30363d` border, `#58a6ff` accent). Table columns: Agent | Confidence % (with a colored bar: green ≥80%, yellow 50–79%, red <50%) | Result (pass=green badge, fail=red badge, unknown=gray) | Duration | Last Used. Page auto-subscribes to `/events`, re-renders rows on each update. No external CDN — all CSS/JS inline.

  Error handling:
  - `pattern-confidence.json` missing: skip file, keep last known values
  - `telemetry.jsonl` missing: all agents show `lastResult: "unknown"`
  - Malformed JSON line in telemetry: skip that line, log to stderr, continue
  - `EADDRINUSE` on start: print `"port 7824 in use — is another HUD running?"` and exit 1

  `start-server.sh`: check `/tmp/hud-server.pid` with `kill -0`; if stale, remove; start `node server.cjs` in background from `masonry/src/hud/`; poll `GET /health` up to 3s; print `"HUD running at http://localhost:7824"`.
  `stop-server.sh`: read PID, SIGTERM, delete PID file, print `"HUD stopped"`.

  **Tests required (`masonry/src/hud/server.test.cjs`):**
  - `GET /health` returns `{ ok: true }` with status 200
  - `POST` is not a valid route — returns 404
  - `GET /agents` returns an array (may be empty when source files absent)
  - `GET /events` returns a keep-alive response with `Content-Type: text/plain`
  - AgentRecord merge: given mock `pattern-confidence.json` with `developer: { confidence: 0.9, uses: 10, last_used: "..." }` and mock `telemetry.jsonl` with one `phase: "post"` line for `developer` with `success: true, duration_ms: 5000`, `GET /agents` returns a record with `name: "developer"`, `confidence: 0.9`, `lastResult: "pass"`, `lastDurationMs: 5000`
  - Run: `cd masonry && node node_modules/vitest/vitest.mjs run src/hud/server.test.cjs` — 0 failures

- [ ] **Task 2** — Build Spec Drift Detector script
  **Files:**
  - `masonry/src/hooks/drift-detector.js` (create)
  - `masonry/src/hooks/drift-detector.test.js` (create)
  - `~/.claude/skills/drift/SKILL.md` (create)

  **What to build:**
  Node.js script. Entry point: `node masonry/src/hooks/drift-detector.js [optional-spec-path]`.

  Step-by-step logic:
  1. Read optional CLI arg as spec path. If absent, read `.autopilot/spec-path`. If still absent, find most recently modified `*.md` file in `docs/specs/` using `fs.readdirSync` + `fs.statSync` sort. If no files found: print `"No spec file found — skipping drift check"` and exit 0.
  2. Read `.autopilot/build-start-sha`. If missing: print `"No build baseline — run /build first"` and exit 2.
  3. Read and parse the spec file. Extract file paths using these patterns (in order):
     - Lines inside fenced code blocks (``` ``` ```) that contain `/` or `.` and look like file paths
     - Bullet list items that start with `-` or `*` and contain a path-like token (contains `/` or starts with a known extension pattern: `.js`, `.ts`, `.py`, `.md`, `.json`, `.sh`, `.cjs`)
     - Content under headings containing "Files", "Modified", "Changed", "Created"
     Deduplicate extracted paths. Strip leading/trailing backticks and whitespace.
  4. Run: `git diff --name-only <build-start-sha> HEAD` via `child_process.execSync`. Split on newlines, filter empty.
  5. Compute:
     - `matched` = intersection of claimedFiles and changedFiles
     - `onlyInSpec` = claimedFiles not in changedFiles
     - `onlyInDiff` = changedFiles not in claimedFiles
  6. Verdict: `CLEAN` if `onlyInSpec.length === 0 && onlyInDiff.length === 0`, else `DRIFT_DETECTED`.
  7. Write `.autopilot/drift-report.md`:
     ```markdown
     # Drift Report
     Generated: <ISO timestamp>
     Spec: <specFile>
     Verdict: CLEAN | DRIFT_DETECTED

     ## Matched (N files)
     - file1
     ...

     ## Only in Spec — not touched (N files)
     - file1
     ...

     ## Only in Diff — not in spec (N files)
     - file1
     ...
     ```
  8. Write `.autopilot/drift-summary.txt`: one line, e.g.:
     - `"✓ CLEAN — 7 files matched, 0 drift"` (CLEAN)
     - `"⚠ DRIFT: 2 unspecced files changed, 1 spec claim untouched"` (DRIFT_DETECTED)
  9. Print the same line to stdout.
  10. Exit 0 (CLEAN) or 1 (DRIFT_DETECTED).

  Error handling:
  - `git diff` exits non-zero: print git's stderr, exit 2
  - Spec file unreadable: print path + error message, exit 2
  - `.autopilot/drift-report.md` unwritable: warn to stderr, still print summary to stdout and exit normally

  `~/.claude/skills/drift/SKILL.md`:
  ```markdown
  # /drift — Run Spec Drift Detector

  Runs the drift detector against the most recent build.

  Usage: /drift [spec-file]

  Steps:
  1. If a spec file path was provided as an argument, pass it to drift-detector.js
  2. Run: node /home/nerfherder/Dev/Bricklayer2.0/masonry/src/hooks/drift-detector.js [spec-file]
  3. Show the output to the user
  4. If DRIFT_DETECTED: display the full contents of .autopilot/drift-report.md
  5. If CLEAN: confirm "No drift detected — build matched spec"
  ```

  **Tests required (`masonry/src/hooks/drift-detector.test.js`):**
  - Parses file paths from a spec string containing a fenced code block with file paths — returns correct array
  - Parses file paths from a spec string with a "## Files" section containing bullet list paths — returns correct array
  - Deduplicates repeated paths — result has no duplicates
  - `computeDrift(claimed, changed)` with `claimed=["a.js","b.js"]`, `changed=["b.js","c.js"]` → `{ matched:["b.js"], onlyInSpec:["a.js"], onlyInDiff:["c.js"], verdict:"DRIFT_DETECTED" }`
  - `computeDrift(claimed, changed)` with identical arrays → `{ verdict: "CLEAN" }`
  - Run: `cd masonry && node node_modules/vitest/vitest.mjs run src/hooks/drift-detector.test.js` — 0 failures

- [ ] **Task 3** — Wire drift summary into session start
  **Files:**
  - `masonry/src/hooks/masonry-session-start.js` (modify)
  - `masonry/src/hooks/session/drift-inject.js` (create)
  - `masonry/src/hooks/session/drift-inject.test.js` (create)

  **What to build:**
  New module `session/drift-inject.js` with a single export:
  ```js
  function getDriftSummary(projectRoot) {
    // Returns string or null
    // Reads <projectRoot>/.autopilot/drift-summary.txt
    // If file exists and is non-empty: return its trimmed contents prefixed with "[Last build] "
    // If file missing or empty: return null
  }
  module.exports = { getDriftSummary };
  ```

  In `masonry-session-start.js`: add `const { getDriftSummary } = require("./session/drift-inject");` with the other requires. After Phase 0.5 (skills directive), add Phase 0.6:
  ```js
  // Phase 0.6: Drift summary from last build
  const driftSummary = getDriftSummary(process.cwd());
  if (driftSummary) lines.push(driftSummary);
  ```
  This must only run on fresh sessions (same resume check as Phase 0.5 — skip if `input.startup_type === "resume"` or `input.is_resume === true`). Pass `input` to the check or gate both phases together.

  `masonry-session-start.js` must remain under 120 lines after this change.

  **Tests required (`masonry/src/hooks/session/drift-inject.test.js`):**
  - File exists with content `"✓ CLEAN — 7 files matched"` → returns `"[Last build] ✓ CLEAN — 7 files matched"`
  - File missing → returns null
  - File exists but empty → returns null
  - Run: `cd masonry && node node_modules/vitest/vitest.mjs run src/hooks/session/drift-inject.test.js` — 0 failures

- [ ] **Task 4** [depends:1,2,3] — Build Project Chronicle DB module and extend brainstorm server
  **Files:**
  - `masonry/src/brainstorm/chronicle-db.js` (create)
  - `masonry/src/brainstorm/server.cjs` (modify — add `/chronicle` endpoints, Chronicle tab, DB wiring)
  - `masonry/src/brainstorm/chronicle-db.test.js` (create)

  **What to build:**

  `chronicle-db.js` — `better-sqlite3` wrapper module:
  ```js
  // DB path: <projectRoot>/.brainstorm/chronicle.db
  // projectRoot determined by: path.resolve(__dirname, '../../../../') from masonry/src/brainstorm/
  // Creates .brainstorm/ dir if missing (fs.mkdirSync with recursive: true)
  // Opens DB with busyTimeout: 1000
  // Creates tables on first open (CREATE TABLE IF NOT EXISTS)

  // Exports:
  function createSession(slug)                        // INSERT → returns id (integer)
  function updateSessionSpec(sessionId, specPath)     // UPDATE sessions SET spec_path
  function updateSessionStatus(sessionId, status)     // UPDATE sessions SET status
  function addSection(sessionId, section)             // INSERT into sections; section = { section_id, title, content, status, posted_at }
  function updateSectionStatus(sessionId, sectionId, status) // UPDATE sections SET status WHERE session_id AND section_id
  function addBuild(sessionId, startedAt)             // INSERT into builds → returns id (integer)
  function completeBuild(buildId, verdict, reportText) // UPDATE builds SET completed_at, drift_verdict, drift_report
  function getSessions()                              // SELECT sessions with counts; returns SessionSummary[]
  function getSession(id)                             // returns { session: SessionSummary, sections: Section[], builds: Build[] }
  ```

  All DB calls wrapped in try/catch — on error: log to stderr, return null (never throw to callers).

  Schema:
  ```sql
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
  ```

  `getSessions()` query:
  ```sql
  SELECT s.*,
    (SELECT COUNT(*) FROM sections WHERE session_id = s.id) as section_count,
    (SELECT COUNT(*) FROM builds WHERE session_id = s.id) as build_count,
    (SELECT drift_verdict FROM builds WHERE session_id = s.id ORDER BY id DESC LIMIT 1) as last_drift
  FROM sessions s ORDER BY s.id DESC
  ```

  **Modifications to `server.cjs`:**
  1. At top: `const db = (() => { try { return require('./chronicle-db'); } catch(e) { console.error('chronicle-db unavailable:', e.message); return null; } })();`
  2. `POST /section` handler: after updating in-memory state Map, also call `db?.addSection(state.sessionId, { section_id: body.id, title: body.title, content: body.content, status: body.status, posted_at: new Date().toISOString() })` — only if `state.sessionId` is set.
  3. `POST /click` handler: also call `db?.updateSectionStatus(state.sessionId, body.section_id, body.action === 'approve' ? 'approved' : 'flagged')` — only if `state.sessionId` is set.
  4. New `POST /session` endpoint: body `{ slug }` → calls `db?.createSession(slug)` → stores result in `state.sessionId` → writes session id to `.autopilot/current-session-id` → returns `{ ok: true, sessionId }`.
  5. New `GET /chronicle` endpoint: calls `db?.getSessions()` → returns JSON array (or `[]` if db null).
  6. New `GET /chronicle/:id` endpoint: calls `db?.getSession(id)` → returns JSON object (or 404 if not found).
  7. `GET /` HTML page: add a "Chronicle" tab button in the sidebar. When clicked, calls `GET /chronicle`, renders a table: Slug | Status | Sections | Builds | Last Drift | Started. Clicking a row calls `GET /chronicle/:id` and renders the section history inline below the table. Tab switching is CSS/JS only — no page reload.

  **Tests required (`masonry/src/brainstorm/chronicle-db.test.js`):**
  - `createSession("test-slug")` returns a positive integer
  - `getSessions()` after createSession returns array with matching slug
  - `addSection(sessionId, {...})` then `getSession(id)` returns sections array with that section
  - `addBuild(sessionId, now)` returns a positive integer; `completeBuild(buildId, "CLEAN", "report text")` then `getSession(id)` returns builds array with `drift_verdict: "CLEAN"`
  - `updateSessionStatus(id, "built")` then `getSessions()` returns session with `status: "built"`
  - DB calls do not throw when called with invalid sessionId — returns null gracefully
  - Run: `cd masonry && node node_modules/vitest/vitest.mjs run src/brainstorm/chronicle-db.test.js` — 0 failures

## Out of Scope
- Historical graphs or trend lines in the HUD
- Alerting or notifications when confidence drops
- Semantic diff (comparing behavior, not file names) in drift detector
- Blocking builds when drift is detected (report only)
- Searching or filtering chronicle entries
- Exporting chronicle to external formats
- Chronicle entries for builds without a preceding brainstorm session

## Notes
- Project root: `/home/nerfherder/Dev/Bricklayer2.0`
- Source root: `masonry/src/` (hooks + brainstorm server), `masonry/src/hud/` (new HUD server)
- Test root: vitest, run via `node node_modules/vitest/vitest.mjs run <file>` from `masonry/` dir
- Suggested strategy: /build --strategy balanced
- `better-sqlite3` is already in `masonry/package.json` — no new dependencies needed
- `masonry/src/brainstorm/server.cjs` is currently 262 lines — Task 4 will push it over 400 lines. Split the Chronicle tab HTML into a helper or keep HTML minimal (table only, no inline styles beyond what fits). Hard limit: 600 lines.
- `masonry/src/hooks/masonry-session-start.js` is currently 110 lines — Task 3 adds ~5 lines, stays well under 120
- Test runner confirmed working: `node /home/nerfherder/Dev/Bricklayer2.0/masonry/node_modules/vitest/vitest.mjs run <file>`
- Existing brainstorm tests: `server.test.cjs` (6 tests), `helper.test.js` (5 tests) — Task 4 must not break these
- HUD server must be run from project root (not from `masonry/src/hud/`) so relative paths to `.autopilot/` resolve correctly. `start-server.sh` should `cd` to project root before starting node.
- `.autopilot/current-session-id` is written by the brainstorm server's `POST /session` endpoint — drift-detector.js reads it to link builds to chronicle sessions

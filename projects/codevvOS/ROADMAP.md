# CodeVV OS — Roadmap

Tracks planned work across project phases. Derived from `project-brief.md` and validated by research (2026-04-01).

---

## Build Status

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| Phase 0 | **COMPLETE** | 2026-04-02 | 13 tasks. All scaffolding and config delivered. |
| Phase 1 | **COMPLETE** | 2026-04-02 | 25 tasks. 258 tests passing (108 Phase 0 + 150 Phase 1). |
| Phase 2 | **IN PROGRESS** | started 2026-04-02 | Spec written (spec-phase2.md, 8 tasks). Build started. |

---

## Phase 0: Pre-Build Security & Architecture Requirements

> These must be resolved in design before Phase 1 build starts. No code until these are decided.

### 0a. Security Pre-Requirements (CRITICAL — resolve before coding)
- [x] **Non-superuser Postgres role:** Create `codevv_app` role with `NOBYPASSRLS NOINHERIT`. All FastAPI connections use this role. Superuser bypasses all RLS — never use it for app queries.
- [x] **SET ROLE per connection:** Explicitly execute `SET ROLE codevv_app` at the start of every SQLAlchemy session via an `@event.listens_for(engine, "connect")` hook. Do NOT rely on the connection string user alone — RLS is bypassed if SET ROLE is omitted.
- [x] **Internal-only ports:** Use `expose:` (Docker-internal) not `ports:` for Postgres, Redis, Yjs, FastAPI. Only Nginx exposes `:443` to the LAN. Nothing else. _(ARCHITECTURE.md updated to match — was showing all ports as LAN-exposed)_
- [x] **BrickLayer sidecar auth:** Internal shared secret (`BL_INTERNAL_SECRET` env var) required on all `bl/server.py` endpoints. Network-isolated to `backend` Docker network only.
- [x] **Masonry MCP auth:** Even within the Docker network, masonry-mcp endpoints must validate `BL_INTERNAL_SECRET`. Backend sets this header on all masonry-mcp calls.
- [x] **Shared JWT auth library:** Single `auth.js` / `auth.py` used identically by backend, Yjs server, ptyHost, **and tldraw-sync**. No service implements its own JWT logic. Validate JWT on connection AND on a 60s expiry timer.
- [x] **JWT algorithm pinning:** Explicitly pin to `HS256` (or `RS256` if asymmetric keys). Reject tokens with `alg: none` or any algorithm not in the allowlist. Configure `algorithms=["HS256"]` in PyJWT / `jose` — never omit this parameter, which would allow alg:none attacks.
- [x] **Brute force protection on /auth/login:** Apply `slowapi` rate limiting to `POST /auth/login` specifically — e.g., 10 attempts per user per minute. Return `429 Too Many Requests`. Without this, credential stuffing hits an unlimited endpoint.
- [x] **Redis session store decision:** Explicitly define whether JWTs are independently verifiable (signature-only validation, no Redis lookup per request) or Redis-required per request. If Redis is required for every auth check, Redis downtime = all users logged out instantly. Recommended: verify by signature; Redis only for explicit revocation (logout, admin force-signout).
- [x] **Recall API auth:** Fresh Recall instance deployed from scratch on GPU VM — configure API key auth at deployment time. Store as `RECALL_API_KEY` Docker secret. No pre-existing instance to audit.
- [x] **Claude API key encryption:** Decided — `pgcrypto` (`pgp_sym_encrypt`) with key from Docker secret.
- [x] **Path traversal dependency:** Create `verify_path_in_workspace(path, user_workspace_root)` FastAPI dependency using `os.path.realpath()`. Apply to ALL file endpoints — not just the tree endpoint.

### 0b. Architecture Pre-Requirements
- [x] **docker.sock resolution:** Remove from `backend`. Mount **only** on `sandbox-manager` service via `tecnativa/docker-socket-proxy`. Scope must allow full container lifecycle: `containers` (create/start/stop/rm), `exec` (exec into running containers), `images` (pull sandbox images). `exec`-only scope is insufficient — sandbox-manager must create and destroy containers. ptyHost calls sandbox-manager API for container ops — never touches Docker directly.
- [x] **tldraw sync decision:** tldraw v2 uses `@tldraw/sync-core` (not Yjs). Two options:
  - Use tldraw's native sync: add `tldraw-sync` Docker service
  - Use community `tldraw-yjs` adapter (unofficial, unsupported)
  - **Decided:** tldraw native sync + `tldraw-sync` service. ADR still needed. _Data migration risk: existing tldraw documents stored as Yjs blobs are incompatible with tldraw-sync format — decide at Phase 3.5-d: wipe or build export tool via `getSnapshot()` API._
- [x] **Univer collab decision:** Univer does NOT use Yjs. Its collab stack requires `univer-server` Docker service. **V1 decision: single-user Univer only** (no `univer-server`). Multi-user Excel collab is V2.
- [x] **Pydantic v2 → JSONForms adapter:** `GET /api/settings/schema` must post-process Pydantic v2 output (draft 2020-12) to JSON Schema draft 7 before returning. Write `to_draft7()` utility: `$defs` → `definitions`, rewrite `$ref` paths, flatten `Optional` `anyOf`.
- [x] **Artifact Panel CSP:** Use `srcdoc` iframe (null origin) with `sandbox="allow-scripts"` — NO `allow-same-origin`. Server-side compile Claude output to `React.createElement()` calls (no JSX, no `unsafe-eval`). Bundle React UMD + charting libraries into the iframe runtime.
- [x] **ARQ worker service:** Add `worker` service to Docker Compose (same backend image, `command: arq app.worker.WorkerSettings`). Without it, all background jobs enqueue to Redis but never execute. _ARQ scope: short/medium jobs only (notifications, digests, polling). Never route long-running BrickLayer agent runs through ARQ — use `POST /agent/spawn` on bricklayer sidecar directly. ARQ default `job_timeout=300s` will kill 30-60min agent runs._
- [x] **`pydantic-settings` package:** Add `pip install pydantic-settings` to requirements. Pydantic v2 split settings into a separate package — easy miss.

### 0e. Design System (reference before any frontend work)
- [x] **Authority document:** `docs/design-system.md` is the Tier 2 UI ground truth. All frontend builders reference it before writing any component.
- [x] **Palette:** Derived from 5 source colors — `#0D160B` (warm green near-black), `#655560` (muted mauve), `#FCF7FF` (lavender near-white), `#4F87B3` (steel blue accent), `#ED474A` (coral red). "Obsidian Shell" aesthetic.
- [x] **Tailwind v4:** Implement `@layer base` CSS custom properties from design-system.md §9 before Phase 2 frontend shell starts. All components use token names — never hardcode hex values.
- [x] **Self-host fonts:** Inter + JetBrains Mono in `/public/fonts/` — LAN kiosk has no Google Fonts CDN access.
- [x] **Per-workspace accent:** Apply `.workspace-dev`, `.workspace-brainstorm`, `.workspace-review`, `.workspace-planning`, `.workspace-meeting` classes on the workspace container. Shell chrome is unaffected by accent changes.
- [x] **UX specs:** `docs/superpowers/specs/codevvos-experience-design.md` sections §29–§38 cover all previously-unspecced features (mobile, login, dock, branch environments, guest links, inline AI edit, live preview, dep scanner, spec gate, KG first-run). Read before building those features.

### 0c. Baseline Docker Compose (author before Phase 1 coding starts)
- [x] Write `docker-compose.yml` encoding all Phase 0 decisions: `expose:` vs `ports:`, Docker secrets, `codevv_app` role env, named networks (`frontend`/`backend`), resource limits, `depends_on: condition: service_healthy`, `restart: unless-stopped`
- [x] This is the single source of truth for service topology — developers modify it, agents reference it
- [x] Write CI/CD workflow files (GitHub Actions): `fast-check.yml` (lint + unit tests, runs on every push), `integration.yml` (integration tests, runs on PR), `build-check.yml` (Docker build verification). See BUILD_BIBLE.md §4 for full pipeline spec. These are Phase 0 deliverables — without them the build loop has no gate.
- [x] **Masonry-MCP architecture decision (resolve before writing compose):** ARCHITECTURE.md previously listed masonry-mcp as a separate container (`expose: 3003`). ROADMAP Technology Decisions says `npm install masonry-mcp` inside the CodeVV Docker image. **Decided: npm install masonry-mcp inside the backend image.** No separate masonry-mcp container. Masonry MCP server runs as a subprocess within the backend container, communicated via the MCP protocol over stdio. Update ARCHITECTURE.md service list to remove masonry-mcp as a standalone service (13 core services, not 14).

### 0d. Known Time Bombs (from stack-validator analysis — prevent before they bite)
- [x] **bricklayer container entrypoint:** Must start tmux daemon before uvicorn (`tmux new-session -d -s main`). Add health check that verifies tmux is running. `spawn_agent()` fails silently if tmux server is not up.
- [x] **sandbox-manager:** Use `aiodocker` (async) or Go for Docker API calls. Do NOT use `docker-py` (sync) in an async FastAPI service — every container operation blocks the event loop.
- [x] **livekit-agents base image:** Use `python:3.12-slim-bookworm`, NOT Alpine. `opuslib` and audio codec deps fail to compile against Alpine musl libc.
- [x] **yjs-server / tldraw-sync:** Lock to `node:22-alpine` base image. Do NOT switch to Bun or Deno — tldraw-sync has no published Bun compatibility guarantees and y-websocket has edge cases at scale.
- [x] **`spawn_agent()` in async routes:** Enforce `asyncio.to_thread()` wrapping everywhere. Consider a linter rule or wrapper function that makes the sync-to-async boundary explicit.
- [x] **dockview layout versioning:** Store `{ version: 1, layout: {...} }` from day one. No layout schema versioning = painful migration when users have saved layouts.

---

## Phase 1: Infrastructure & Backend (no frontend dependency)

### 1a. Docker Compose Hardening
- [x] Add native Docker HEALTHCHECK per service (`pg_isready`, `redis-cli ping`, `curl /health`)
- [x] Replace `wait-for-healthy.sh` with `depends_on: condition: service_healthy`
- [x] Add Docker network isolation: `frontend` (exposed) + `backend` (internal)
- [x] Add log rotation on all services (`max-size: 10m`, `max-file: 3`)
- [x] Add resource limits (memory + CPU) per service
- [x] Add Docker secrets for passwords/keys (replace env vars)
- [x] Remove docker.sock mount from backend container (security fix)
- [x] Add `restart: unless-stopped` on all long-running services

### 1b. Node.js ptyHost Service (NEW)
- [x] Dedicated Node.js + `node-pty` microservice for per-user terminal PTY
- [x] WebSocket transport with ACK-based flow control — define message schema upfront: `{type:"data",id,data}` / `{type:"ack",id}` / `{type:"resize",cols,rows}`
- [x] ReconnectingPTY pattern: session persistence via replay buffer per session (cap at 100KB — VS Code pattern)
- [x] **Per-user container sandboxing via sandbox-manager API (HARD DEPENDENCY on sandbox-manager):** Terminal sessions must run shells INSIDE per-user sandbox containers, NOT on the ptyHost container filesystem. ptyHost calls `POST /sandbox/exec` on sandbox-manager to get a PTY inside a sandboxed container. Phase 1b is NOT done until this integration is working — a ptyHost that spawns shells on its own filesystem is a security hole.
- [x] Shell cleanup on disconnect: SIGHUP -> timeout -> SIGKILL -> waitpid -> close FDs
- [x] Heartbeat monitoring with crash recovery (VS Code ptyHost pattern)
- [x] JWT validation on WebSocket connection using shared `auth.js` library (see Phase 0a)
- [x] Add HEALTHCHECK to ptyHost service in Docker Compose: `curl --fail http://localhost:PORT/health || exit 1`

### 1c. Nginx Reverse Proxy (NEW)
- [x] Per-service WebSocket location blocks: Yjs (`/yjs`), ptyHost (`/pty`), LiveKit (`/livekit`), **tldraw-sync (`/tldraw`)**, SSE (`/api/stream`, `/api/files/watch`), BrickLayer agent streams (`/bl/agent/*/stream`)
- [x] tldraw-sync location block requires `proxy_buffering off` and `proxy_read_timeout 3600s` — long-idle canvas connections time out without it
- [x] `proxy_read_timeout 3600s` + ping/pong every 30s for long-lived WebSocket
- [x] SSL termination (self-signed for LAN; Let's Encrypt optional)
- [x] `proxy_buffering off` for WebSocket and SSE paths
- [x] HTTP/2 for static assets (WebSocket falls back to HTTP/1.1 automatically)
- [x] Artifact Panel iframe: `X-Frame-Options SAMEORIGIN` + CSP header with `sandbox` attribute on iframe responses
- [x] LiveKit UDP port range `50000-60000` published (required for WebRTC media — fallback to TURN relay otherwise)

### 1d. Backend API Extensions (FastAPI)
- [x] `GET /api/files/tree?path=` — Lazy-load directory listing with `verify_path_in_workspace` dependency (Phase 0a)
- [x] `PATCH /api/files/{path:path}` — File operations scoped to user workspace. Use `{path:path}` for slash-containing paths. Apply `verify_path_in_workspace` dependency.
- [x] File watch via `watchfiles` (Rust-backed) pushing changes over SSE — fan-out via async generator, not per-connection watcher (inotify exhaustion risk)
- [x] `GET /api/settings/schema` — JSON Schema from Pydantic models, post-processed to draft 7 via `to_draft7()` (see Phase 0b)
- [x] `GET/PUT /api/settings/user` — Per-user settings CRUD
- [x] `GET/PUT /api/admin/settings` — Admin-only settings with `require_role("admin")` dependency
- [x] `GET /api/notifications?limit=50&before_id=` — Cursor-paginated notification history
- [x] `PATCH /api/notifications/{id}/read` — Mark notification read
- [x] Add `slowapi` rate limiting on all `/api/ai` and assistant endpoints (per-user limits — prevent trigger automation exhausting org API key)
- [x] Use `expire_on_commit=False` on all SQLAlchemy async sessions to prevent `MissingGreenlet` errors
- [x] Wrap all `spawn_agent()` calls in `asyncio.to_thread()` — blocking tmux dispatch must not block FastAPI event loop
- [x] System metrics endpoints: read from cgroup v2 (`/sys/fs/cgroup/memory.current` etc.) not `psutil` — Docker containers report misleading host-level data via psutil

### 1e. PostgreSQL Multi-Tenant & Schema
- [x] Enable Row-Level Security (RLS) on all shared tables
- [x] Create `codevv_app` role: `NOLOGIN NOBYPASSRLS NOINHERIT` — all app connections use this role
- [x] Composite indexes on tenant-scoped tables: `(tenant_id, id)`, `(tenant_id, created_at DESC)` — bare `(tenant_id)` alone is insufficient
- [x] Add admin role to user model
- [x] Remove `pgvector` extension — no defined use case in CodeVV (Recall uses Qdrant for vector search)
- [x] **Split Alembic migrations into two revisions:** (1) core tables only (`tenants`, `users`, `projects`, `workspace_templates`, `activity_events`, `agent_runs`) — must pass CI before any feature work starts; (2) feature tables in a separate revision. Monolithic initial migrations fail in unexpected ways and are hard to roll back.
- [x] Add Redis AOF persistence: set `appendonly yes` + `appendfsync everysec` in redis.conf. Without persistence, all ARQ job queues and session data are lost on Redis restart. Mount redis.conf via Docker bind mount.

#### Core tables (must exist before any feature work):
```
tenants           id, name, created_at
users             id, tenant_id, email, role, display_name, ...
projects          id, tenant_id, name, description, status, github_repo, created_by, ...
workspace_templates id, tenant_id, name, base_type, layout_json, shortcut_profile, accent_color, is_system, is_team_default, created_by
activity_events   id, tenant_id, project_id, user_id, type, title, payload, recall_ref, created_at
agent_runs        id, tenant_id, project_id, agent_id (BrickLayer agent_id), status, started_at, finished_at, output_ref
```

#### Feature tables (add per phase as features are built):
```
tasks             id, tenant_id, project_id, title, status, assignee_id, spec_ref, git_commit_sha, ...
task_assignments  task_id, user_id, assigned_at
ideas             id, tenant_id, project_id, title, description, source, status, promoted_task_id, recall_node_id
assumptions       id, tenant_id, project_id, statement, status (unconfirmed/confirmed/invalidated/accepted_risk), ...
premortem_sessions id, tenant_id, project_id, trigger_ref, conducted_at, summary
premortem_risks   id, session_id, description, likelihood, impact, mitigation, status
custom_agents     id, tenant_id, project_id, name, system_prompt, tool_loadout, crucible_score, ...
session_handoffs  id, user_id, tenant_id, summary, recall_ref, dismissed, created_at
push_subscriptions id, user_id, tenant_id, endpoint, p256dh, auth, created_at
backup_configs    id, tenant_id, project_id, destination, schedule_cron, scope, enabled, last_run_at
projector_configs id, tenant_id, name, url_slug, doc_id, created_at
yjs_updates       doc_id, clock (BIGSERIAL), data (BYTEA), ts
yjs_snapshots     doc_id, data (BYTEA), clock_high, updated_at
```

### 1f. Claude AI Auth Migration (CRITICAL)
- [x] **Remove OAuth PKCE flow** — Anthropic bans third-party apps from using subscription OAuth tokens (enforced server-side since Jan 2026)
- [x] Remove `claude_auth.py` OAuth PKCE logic (authorize URL, token exchange, refresh)
- [x] Repurpose `claude_credentials` table for encrypted per-user API keys (or remove if using org key only)
- [x] Keep shared API key path (`ANTHROPIC_API_KEY` env var) — already works, compliant
- [x] Add per-user API key option: user provides Console API key via Settings panel, stored encrypted in PostgreSQL
- [x] Evaluate Claude Agent SDK (`pip install claude-agent-sdk`) — gives Claude Code's full tool suite (Read, Write, Edit, Bash, Grep, Glob) built-in alongside CodeVV's 19 custom tools
- [x] SSE streaming: no change needed — works identically with API key auth
- [x] Frontend: remove "Connect Claude" OAuth redirect, replace with API key input in Settings

---

## Phase 2: Frontend Shell (depends on Phase 1)

### 2a. Desktop Shell — dockview
- [ ] Replace sidebar+page navigation with `dockview-react` panel manager
- [ ] Tiling-first layout with floating escape hatch for transient panels
- [ ] JSON-serializable layout state: `api.toJSON()` / `api.fromJSON()`
- [ ] Layout persistence per user in PostgreSQL
- [ ] Wrap `fromJSON()` in try/catch with default layout fallback
- [ ] Store schema version alongside layout JSON for migration

### 2b. Dock / Taskbar
- [ ] Persistent bar (outside dockview layout tree) with app launcher icons
- [ ] App registry: `{ id, label, icon, componentFactory }` per launchable app
- [ ] Click icon -> `api.addPanel()` or focus if already open
- [ ] Active panel indicator via `onDidActivePanelChange` subscription
- [ ] Built with React + Tailwind + Framer Motion

### 2c. OS-Style Login Screen
- [ ] Full-screen login UI replacing default app entry
- [ ] Connects to existing FastAPI `/auth/login` -> JWT
- [ ] Session management via Redis with TTL matching JWT expiry

---

## Phase 3: Frontend Features (depends on Phase 2)

### 3a. Code File Browser
- [ ] `@headless-tree/react` + `@tanstack/react-virtual` v3 for virtualized tree (NOT react-window — unmaintained, no React 19 support)
- [ ] Lazy-load children on directory expand (never full tree fetch)
- [ ] Connected to `GET /api/files/tree?path=` backend API
- [ ] Real-time updates via SSE file watch channel
- [ ] Inline rename, drag-and-drop, context menus, keyboard navigation
- [ ] Exclude `.git/` from file watching
- [ ] Debounce file events 100-300ms

### 3b. Terminal Upgrade
- [ ] Connect `SharedTerminal.tsx` to new ptyHost WebSocket service
- [ ] Addon loading order (critical): `new Terminal()` → `terminal.open(domEl)` → `loadAddon(webgl)` → `loadAddon(fit)` → `fitAddon.fit()`. Must call `open()` first — WebGL requires a DOM node.
- [ ] Add xterm.js addons: `@xterm/addon-webgl` (primary renderer), `@xterm/addon-fit`, `@xterm/addon-serialize`, `@xterm/addon-web-links`, `@xterm/addon-search`
- [ ] Remove deprecated canvas addon (deprecated in xterm.js v6)
- [ ] Debounce `fitAddon.fit()` 150-200ms with `ResizeObserver`
- [ ] Per-user terminal sessions with reconnection (session ID-based)
- [ ] Multiple terminal tabs within dockview panel
- [ ] WebGL context loss fallback: `webglAddon.onContextLoss(() => { webglAddon.dispose(); terminal.loadAddon(new CanvasAddon()); })`
- [ ] Always call `terminal.dispose()` on unmount (dispose addons first, then terminal)

### 3c. Settings Panel
- [ ] `@jsonforms/react` auto-rendered from Pydantic-generated JSON Schema
- [ ] Layered: user settings override system defaults
- [ ] Admin-only section for user management, network info, system metrics
- [ ] Network info via `/proc/net/`, system metrics via **cgroup v2** (`/sys/fs/cgroup/memory.current`, `/sys/fs/cgroup/cpu.stat`) — **NOT psutil**. psutil reads host-level data from `/proc`; inside a Docker container this reports the entire host's memory/CPU, not the container's limits. This contradicts Phase 1d which correctly specifies cgroup v2 — keep them consistent.
- [ ] Display/resolution via browser `window.screen` API

### 3e. Inline AI Editing (Cmd+K) — NEW
- [ ] Inline AI edit shortcut: `Cmd+K` / `Ctrl+K` opens inline prompt above current selection in CodeMirror — **fires only when CodeMirror has focus**. Command palette is `Cmd+Shift+K` (global). This resolves the shortcut collision with 3.5-TH.
- [ ] Claude receives: selected code + surrounding context (±20 lines) + active file path + current task
- [ ] Returns a unified diff applied inline with `+`/`-` highlighting (not a full rewrite)
- [ ] Accept (`Tab`) / Reject (`Esc`) / Regenerate (`Cmd+Enter`) actions on the inline diff
- [ ] Prompt history: up/down arrow cycles recent inline prompts
- [ ] Works without selection: cursor position used as insertion point
- [ ] Distinct from chat panel — inline edits do not appear in AI chat history

### 3f. Live Preview Panel — NEW
- [ ] Hot-reload iframe panel (dockview) for web project output
- [ ] Auto-detects dev server port from `package.json` scripts or `vite.config.ts`
- [ ] Proxied through Nginx to avoid CORS issues
- [ ] Refresh on file save (debounced 300ms)
- [ ] Mobile viewport simulator: toggle between desktop / tablet / mobile breakpoints
- [ ] Error overlay: compilation errors render in the preview panel, not just the terminal

### 3d. Notification Center Upgrade
- [ ] Swap toast implementation to Sonner (zero deps, simplest API)
- [ ] Notification center dropdown with history (PostgreSQL-backed)
- [ ] Read/unread tracking with `PATCH /api/notifications/{id}/read`
- [ ] SSE push for real-time delivery + `GET /api/notifications` for missed on page load

---

## Phase 3.5: Experience Design & Product (from Superpowers spec 2026-04-01)

> Full design decisions in `docs/superpowers/specs/codevvos-experience-design.md`

### 3.5-UX: Team Dashboard
- [ ] Team-wide panel: all active projects, per-member presence, project health indicators
- [ ] Personal panel: assigned projects, tasks, personal AI assistant quick-access, catch-up digest
- [ ] Activity feed: recent commits, decisions, AI conversations, canvas changes — filterable
- [ ] **Dashboard must be non-closable:** place `TeamDashboard` outside the main dockview layout tree as a fixed-width left panel. Panels to the right represent open workspaces. This makes "always anchored" structural, not a policy that can be overridden by drag.
- [ ] Workspace switcher: `WorkspaceChip` in dock opens `WorkspaceSwitcherModal` (5 template cards with accent swatch, layout preview, default shortcuts)
- [ ] Admin-configurable visibility restrictions for fractional hires
- [ ] Catch-up digest gate: only show if `(time since last login > 2h) AND (feed has > 5 new events)`. Store `last_seen_digest_at` server-side.

### 3.5-WS: Workspace Type System
- [ ] Five workspace templates: Brainstorm, Planning, Development, Review, Meeting
- [ ] Each template: default dockview panel layout + keyboard shortcut profile + accent color
- [ ] Users pick templates manually; work type suggests but never auto-switches
- [ ] Admin-defined team-wide templates
- [ ] Template customization and save per user

### 3.5-KG: Knowledge Graph

> **Phase 3.5 ordering dependency:** 3.5-KG must ship before 3.5-TI (team intelligence features that link to graph nodes) and 3.5-II (decision archaeology, assumption tracker).

- [ ] Graph model: people, projects, tasks, decisions, files, canvas nodes, conversations, Recall memories
- [ ] AI-maintained: Claude + Recall update graph continuously as work happens
- [ ] Navigable: click node → open related item (file, canvas, task, conversation)
- [ ] Manually editable: add nodes, draw connections, annotate relationships
- [ ] Dedicated Knowledge Graph panel (launchable from dock)
- [ ] Inline citations: when Claude references a decision, it links to the graph node
- [ ] **First-run / empty state:** On a brand-new project with empty Recall, the graph is empty. Define what a new user sees: skeleton nodes for each team member + the project itself, placeholder "start brainstorming to populate" prompt, and a "seed from codebase" action that runs an initial Recall ingestion of the existing git repo. Without this, the graph panel is a blank screen on day one.
- [ ] **Visualization library decision (must choose before build):** Select one: D3-force, react-force-graph, Cytoscape.js, or VisX. Each has different trade-offs (bundle size, WebGL support, interaction model). Document the choice in the Technology Decisions table.
- [ ] **Multi-tenant Recall isolation:** CodeVV is multi-tenant (RLS). Recall is a shared instance. Verify that Recall namespaces memories by tenant_id before 3.5-KG build starts. A query for "project decisions" must not return results from another tenant. For single-team deployments this doesn't matter; for multi-tenant SaaS it's a critical data leak.

### 3.5-PA: Personal AI Assistant (Per User)

> **Phase 3.5 ordering dependency:** 3.5-PA (BrickLayer agent invocation) depends on 3.5-BL.

- [ ] Per-user named assistant with persistent personality and memory (Recall user-scoped)
- [ ] Learns working style, preferences, domain knowledge over time — grows every session
- [ ] Configurable tool loadout: Recall, file system, GitHub, canvas, BrickLayer, open MCP
- [ ] Open MCP: user connects any MCP server (email, calendar, Slack, home automation, etc.)
- [ ] Dev tasks: code assist, debugging, code review, BrickLayer agent invocation
- [ ] Managerial tasks: email (read/draft/send), calendar, task tracking, standup summaries
- [ ] Trigger-based automation: new PR → draft review email, build failed → notify team, task overdue → reassign suggestion
- [ ] Scheduled automation: daily/weekly jobs (summaries, nudges, reports). **Scheduled job auth:** scheduled jobs run when the user is offline. User JWTs are session-scoped and may be expired. Implement as ARQ jobs using a long-lived service account token (not the user's JWT). Store service token as Docker secret. Session handoff (`POST /auth/logout` → write to Recall) must fire as ARQ fire-and-forget, not synchronously during logout response.
- [ ] Public invocation: owner @mentions assistant in team contexts
- [ ] Proxy mode (opt-in): teammates can ask assistant about owner's work when owner is away
- [ ] Personality persists across sessions and machines via Recall sync

### 3.5-CA: Custom Team Agents

> **Phase 3.5 ordering dependency:** 3.5-CA depends on 3.5-BL (BrickLayer sidecar must expose `/crucible/scores` endpoint).

- [ ] Build from presets (researcher, coder, reviewer, security auditor) or from scratch
- [ ] System prompt + tool loadout configuration per agent
- [ ] Shareable with team or kept private — stored in project (version-controlled)
- [ ] All custom agents run through BrickLayer crucible: benchmarked, scored, promoted/retired
- [ ] Team builds living, improving agent fleet over time

### 3.5-AM: AI Agent Mode (BrickLayer Build Panel)

> **Phase 3.5 ordering dependency:** 3.5-AM depends on 3.5-BL.

- [ ] Live log stream panel: terminal-style output of agent activity in real time
- [ ] Live diff preview panel: code changes appear as agents write them
- [ ] Interruptible: any team member can pause agent run, redirect Claude, resume
- [ ] Build status visible on dashboard (project health indicator)

### 3.5-OB: Onboarding & Offboarding
- [ ] New user onboarding: Claude-guided tour (project history, decisions, progress, team)
- [ ] Tour is Recall-backed — accurate from real project history, not generic copy
- [ ] Offboarding: admin revokes access → Claude generates knowledge transfer summary
- [ ] Claude suggests task reassignment for departing member's open tasks
- [ ] Recall purge option: admin can remove personal memories while keeping project contributions

### 3.5-PJ: Projector Casting
- [ ] W3C Presentation API integration for browser-native casting
- [ ] Dedicated `/projector` route: stripped-down canvas view mirrored live via Yjs
- [ ] Admin configures projector URL → physical display mapping

### 3.5-BL: BrickLayer & Masonry Integration

> **Phase 3.5 ordering dependency:** 3.5-BL must ship before 3.5-AM, 3.5-CA, 3.5-PA, and 3.5-SIM. All four depend on BrickLayer endpoints. Do not decompose these as parallel tasks.

- [ ] **Masonry:** `npm install masonry-mcp` in CodeVV Docker image (Node.js — legitimate npm package). Runs as subprocess within backend container — no separate masonry-mcp service.
- [ ] **BrickLayer shared volume:** Add a named Docker volume `project_files` shared between `backend` and `bricklayer` services. BrickLayer `spawn_agent(cwd="/projects/...")` requires access to the same filesystem the backend manages. Without this shared volume, all agent spawns run against an empty directory — hard blocker.
- [ ] **BrickLayer:** Docker sidecar service — same pattern as Recall
  - [ ] Add `bl/server.py` — thin FastAPI wrapper exposing:
    - `POST /agent/spawn` → `asyncio.to_thread(spawn_agent, name, prompt, cwd)` — returns `{agent_id}` immediately
    - `GET /agent/{id}/stream` → **SSE stream** of stdout from tmux pane (required for live log panel — polling is wrong)
    - `GET /agent/{id}` → one-shot status check (running/complete/failed)
    - `POST /agent/{id}/interrupt` → SIGINT to agent pane (required for interruptible builds)
    - `POST /agent/{id}/kill` → SIGKILL
    - `GET /agent/list` → active agents (required for dashboard build status)
    - `POST /wave/spawn` → parallel multi-agent dispatch, returns `{wave_id}`
    - `POST /wave/{id}/abort` → abort all agents in a wave
    - `GET /crucible/scores` → agent benchmark scores
    - `POST /sim/run` → returns `{run_id}` immediately (simulations are long-running)
    - `GET /sim/{run_id}/stream` → SSE stream of simulation progress + result
    - All endpoints require `BL_INTERNAL_SECRET` header (see Phase 0a)
  - [ ] Add `Dockerfile` for BrickLayer image (Python + tmux + claude CLI)
  - [ ] Add `bricklayer` service to CodeVV Docker Compose (version-pinned image tag)
  - [ ] CodeVV backend calls `http://bricklayer:8300/` — no direct Python import
  - [ ] Version updates: bump image tag in `docker-compose.yml` + `docker compose pull`
  - [ ] Add HEALTHCHECK to bricklayer service: verify tmux is running AND uvicorn is responding
  - [ ] Security review: bricklayer container runs `claude` CLI (executes arbitrary code). Verify it cannot reach Postgres, Redis, or any internal service other than its designated endpoints. Network isolation is critical.
- [ ] AI Agent Mode panel surfaces BrickLayer: live log + live diff + interruptible
- [ ] **BrickLayer crash semantics:** Frontend must distinguish "agent died" (SSE EOF with no graceful close) from "network drop" (WebSocket reconnect). A retry on agent died would spawn a duplicate agent — implement `{type:"agent_died",agent_id}` close event so frontend can show "Build failed" rather than attempting reconnect.
- [ ] Custom agents run through BrickLayer routing and crucible

### 3.5-GS: Global Search
- [ ] Single search bar with scope filter: this file / this project / all projects / Recall memory
- [ ] File/code: ripgrep-backed
- [ ] Canvas + docs: index canvas nodes and uploaded project documents
- [ ] Recall: semantic search across all conversations, decisions, meetings, findings

### 3.5-EX: Export & Backup
- [ ] Manual export: canvas (PNG/SVG), documents (PDF/Markdown), full project archive (zip)
- [ ] Scheduled automated backups to configurable destination (local path, S3, mounted storage)
- [ ] Backup scope: code + canvas + docs + task history + AI conversation logs + DB snapshots

### 3.5-TH: Theming & UX Polish
- [ ] Dark mode + light mode toggle
- [ ] Per-workspace accent colors (part of workspace template definition)
- [ ] **Command palette shortcut: `Cmd+Shift+K` (not `Cmd+K`)** — `Cmd+K` is reserved for inline AI editing in CodeMirror (Phase 3e). Resolved: command palette uses `Cmd+Shift+K` everywhere; `Cmd+K` is CodeMirror-context-only (fires only when CodeMirror has focus). Document both in keyboard shortcuts reference.
- [ ] Opinionated default keyboard shortcuts + full remapping (VS Code-style)
- [ ] Per-workspace shortcut profiles defined in workspace templates

### 3.5-ST: Settings & Preferences
- [ ] Settings stored in PostgreSQL — sync across all machines on login
- [ ] Layered: user overrides system defaults; admin sets org-wide defaults
- [ ] Export/import: portable JSON config file

### 3.5-AP: Artifact Panel
- [ ] `srcdoc` null-origin iframe with `sandbox="allow-scripts"` only — NO `allow-same-origin` (would let iframe access parent DOM)
- [ ] Server-side compile Claude output to `React.createElement()` calls — eliminates `unsafe-eval` requirement entirely
- [ ] Bundle React UMD + recharts/D3/Chart.js into the iframe runtime as a local static bundle
- [ ] **postMessage nonce:** srcdoc null-origin iframes have `event.origin === "null"` — any other null-origin iframe on the page could spoof postMessage. Include a cryptographic nonce in every postMessage payload, generated on iframe create and embedded in the srcdoc at compile time. Validate nonce in both directions.
- [ ] postMessage communication: parent → iframe (inject content), iframe → parent (resize, events). Validate `event.origin` AND nonce on all messages.
- [ ] Inline code editing (CodeMirror strip, collapsed by default) → **re-run server-side compiler on save** (not just re-render — inline edits change JSX source that must be re-compiled to React.createElement() before injection)
- [ ] Interactive output (click, hover, input on rendered content)
- [ ] `RenderChip` in chat messages: after Claude generates renderable content, chip appears → click to render in panel
- [ ] Artifact persistence: saved to project + ingested into Recall
- [ ] Type badges: Chart / React / Table / Diagram / Simulation (content-type colors, not workspace accent)
- [ ] CSP `connect-src 'none'` — artifact iframes cannot make network requests

### 3.5-SB: Sandbox (Three Modes)
- [ ] **Mode 1 — Code Scratchpad:** isolated execution (Node.js, Python, bash), results inline, zero project file access
- [ ] **Mode 2 — Environment Clone:** Docker container snapshot of current project, promote or discard changes
- [ ] **Mode 3 — Artifact Sandbox:** Claude generates runnable code → executes in sandbox → output to Artifact Panel
- [ ] Language runtime containers: Node.js, Python pre-built sandbox images
- [ ] Sandbox panel switchable between modes via tab

### 3.5-SIM: Simulation Sandbox

> **Phase 3.5 ordering dependency:** 3.5-SIM depends on 3.5-BL.

- [ ] **Data simulations:** feed dataset (CSV/JSON/DB query) + define variables → Claude generates sim code → runs in sandbox → charts in Artifact Panel
- [ ] **System simulations:** describe architecture → BrickLayer simulate runner models behavior → latency curves, failure rates, bottleneck identification
- [ ] Tweak inputs, re-run, compare outputs side by side
- [ ] Simulation results stored in Recall as project findings

### 3.5-FV: File Viewers & Editors
- [ ] **PDF:** PDF.js dockview panel, annotation support (highlights/comments → Recall), text extraction for global search
- [ ] **DOCX:** `docx-preview` for viewing, mammoth.js + TipTap for editing, DOCX export round-trip
- [ ] **Excel:** Univer editor (formulas, charts, formatting), `@univerjs/sheets-import-xlsx` for .xlsx import/export (**not SheetJS** — Univer has its own xlsx engine)
- [ ] **Excel collab: V1 = single-user only.** Univer multi-user collab requires `univer-server` Docker service → deferred to V2
- [ ] Excel data readable by Claude as conversation context
- [ ] Excel charts render to Artifact Panel
- [ ] All document types: text extracted on open → indexed in Recall → searchable globally
- [ ] Optional: ONLYOFFICE Docker service for full native DOCX/Excel fidelity — if deployed, isolate to its own Docker network, set JWT secret, pin image version, never expose to LAN directly

### 3.5-TI: Team Intelligence

> **Phase 3.5 ordering dependency:** 3.5-TI team intelligence features that link to graph nodes depend on 3.5-KG.

> **Recall availability:** GPU VM going down = Recall unavailable. Features that hard-depend on Recall (session handoff, catch-up digest, decision archaeology, all team intelligence features) must have graceful degrade: show a dismissable "Recall unavailable — some features are offline" banner rather than silently hanging or throwing 500 errors. Implement via a `recall_available` health flag checked on each Recall call.

- [ ] **Ambient terminal watching:** Claude observes terminal output, proactively explains errors inline, dismissable
- [ ] **Session handoff:** on session end, Claude writes handoff note to Recall via ARQ fire-and-forget (not synchronous during logout). `POST /auth/logout` enqueues the ARQ job immediately and returns 200 — the write to Recall happens asynchronously.
- [ ] **Decision archaeology:** before decisions, Claude searches Recall across all projects for relevant past decisions
- [ ] **Architecture drift detection:** BrickLayer diffs codebase vs. approved spec post-build; drift → task
- [ ] **Cross-project intelligence:** Claude detects duplicate work across projects, suggests shared modules
- [ ] **Impact analysis:** before PR merge/task completion, Claude surfaces downstream risk (imports, tests, shared projects)
- [ ] **Live module documentation:** BrickLayer maintains living prose doc per module in Recall; auto-updates on change
- [ ] **Sprint retrospective:** AI-generated from git + task + Recall data, delivered as digest at sprint end

### 3.5-CI: Competitive Feature Additions (from competitive analysis 2026-04-02)

#### Branch Auto-Environments
- [ ] Auto-spin an isolated Docker container snapshot when a new git branch is created
- [ ] Each branch gets its own environment (extends Sandbox Mode 2 to be automatic)
- [ ] Branch environment destroyed on branch delete or after configurable TTL
- [ ] Switch between branch environments from the git panel without manual clone

#### AI-Generated PR Descriptions & Commit Messages
- [ ] `git-nerd` agent drafts PR description from: diff, related tasks, spec, Recall context
- [ ] Inline commit message suggestion in git panel (one-click accept/edit)
- [ ] PR description includes: what changed, why, related decisions cited from Recall, test summary
- [ ] Configurable template per project

#### Guest / Shareable Links
- [ ] Admin can generate a shareable read-only link for a canvas, spec, or project dashboard
- [ ] Guest access: no account required, scoped to a single document or canvas
- [ ] Guest link has configurable expiry (1h / 24h / 7d / permanent)
- [ ] Guest sees: canvas view, spec view, or dashboard (read-only). No code access, no terminal.
- [ ] Guest activity not stored in Recall

#### Lightweight Spec Gate UI
- [ ] Spec approval must feel like Linear (one-click), not JIRA (5 required fields)
- [ ] Driver sees: spec preview + `[Approve & Build]` button + optional comment field
- [ ] Approval recorded in Recall with timestamp and approver identity
- [ ] Rejected spec goes back to canvas with driver's comment visible as a canvas annotation
- [ ] No workflow configuration required — gate is always single-click approval

#### Dependency Vulnerability Scanning
- [ ] Integrated npm/pip dependency audit in the development workspace
- [ ] Triggered on: `package.json` / `requirements.txt` save, manual scan from dock
- [ ] Results panel: severity (CRITICAL/HIGH/MEDIUM/LOW), package, version, CVE link
- [ ] Claude suggests fix: `npm update X` or pinned safe version
- [ ] Findings stored as project tasks (auto-create task for CRITICAL/HIGH)

### 3.5-II: Ideation Intelligence

> **Phase 3.5 ordering dependency:** 3.5-II (code archaeology, decision archaeology) depends on 3.5-KG (knowledge graph).

- [ ] **Idea backlog:** dedicated idea bank separate from tasks; Claude resurfaces contextually when relevant
- [ ] **Assumption tracker:** Claude captures assumptions explicitly; tracks validation status; surfaces before build
- [ ] **Pre-mortem:** structured failure-mode session before every build triggers; outputs → risk tracking in knowledge graph
- [ ] **Parallel spike dispatch:** BrickLayer runs throwaway parallel implementations; benchmarks reported back; decision + results stored in Recall
- [ ] **Code archaeology:** full provenance panel — code → task → brainstorm → meeting, via Recall + git
- [ ] **Rubber duck mode:** Claude listens + asks only (no suggestions); user switches to "give me your take" explicitly
- [ ] **Constraint-aware ideation:** during brainstorm, Claude surfaces buildable minimal version of each idea given real team constraints
- [ ] **Weekly brief:** Monday morning dashboard digest — shipped, planned, blockers, decisions needed, velocity trend. **ARQ timeout risk:** weekly brief generation (Recall query across all projects + Claude synthesis) may approach or exceed ARQ's default 300s `job_timeout`. Set `job_timeout=600` in `WorkerSettings` specifically for the weekly brief job, OR route it through BrickLayer (no timeout constraint). Do not leave this at ARQ default.

---

## Phase 3.5: Collaboration & Intelligence (extends existing CodeVV features)

### 3.5a. Shared AI Sessions (Group Claude Chat)
- [ ] Multiple users participate in the same Claude conversation in real-time
- [ ] Yjs shared type for conversation messages — all connected clients see messages, tool calls, responses live
- [ ] **SSE fan-out design (must be spec'd before building):** The backend receives an Anthropic SSE stream (token by token). For shared sessions, each token must be written as a Yjs update and broadcast to all participants via yjs-server. Design the fan-out bridge: `anthropic_sse_stream → yjs_doc_writer → yjs-server → all clients`. This component does not exist in the current architecture and must be designed before 3.5a build starts.
- [ ] User attribution on each message (who asked, who followed up)
- [ ] Context injection: AI sees what each user has open (active file, terminal, canvas) via Yjs awareness
- [ ] Recall integration: AI cites past team decisions, meetings, and conversations
- [ ] Extend existing `AIChatContext.tsx` + `/api/ai` routes for multi-participant mode
- [ ] Driver/observer roles: one user can "drive" the AI, others observe and can interject

### 3.5b. LiveKit AI Meeting Assistant
- [ ] AI agent joins LiveKit rooms as a participant (LiveKit Agents framework)
- [ ] Real-time transcription via Deepgram/Whisper STT plugin
- [ ] Speaker attribution on transcripts with timestamps
- [ ] Auto-generated meeting summaries: action items, decisions, code references
- [ ] Summaries auto-stored in Recall via existing `push_to_recall` tool
- [ ] Push-to-talk AI: voice question → Claude processes → text response in chat panel
- [ ] Searchable meeting history integrated with existing knowledge graph

### 3.5c. Recall Institutional Memory
- [ ] Auto-capture: every AI conversation, meeting transcript, decision, brainstorm → Recall
- [ ] Extend existing `get_knowledge_context` tool to synthesize across all interaction types
- [ ] AI onboarding assistant: "I'm new to this project, what should I know?" → answer from accumulated team memory
- [ ] "Why did we choose X?" → AI cites the meeting, ADR, and conversation where it was decided
- [ ] Auto-generated Architecture Decision Records (ADRs) from conversation patterns
- [ ] Decision detection: Claude flags "we decided to..." moments, drafts ADR for team review
- [ ] ADRs stored in Recall with metadata tags, cited in future AI conversations

### 3.5d. AI-Powered Canvas Brainstorming (tldraw-sync persistence required)

> **Pre-condition:** Define tldraw-sync persistence store before any canvas work. tldraw-sync needs a PostgreSQL persistence layer (custom `IRecord`-based store writing to a `tldraw_records` table, or the official `@tldraw/sync-core` server-side store). Without it, canvas state is lost on container restart. This is distinct from Recall — Recall gets semantic content; tldraw-sync persists operational state (shape positions, connections).
>
> **Data migration decision:** Existing tldraw Yjs-blob documents are incompatible with tldraw-sync format. Decide before any Phase 3.5 canvas development: wipe canvas data at cutover OR build a one-time export tool via `tldraw.getSnapshot()`. Making this decision after canvas features are built means discarding all test data.

- [ ] Claude generates sticky notes, diagrams, and clusters directly on tldraw canvas
- [ ] Structured brainstorming protocols: SCAMPER, Six Thinking Hats, brainwriting with AI facilitation
- [ ] "Organize these ideas" → AI clusters sticky notes by theme on canvas
- [ ] "Draw the architecture for X" → AI generates diagram shapes via tldraw API
- [ ] Architecture diagrams linked to actual code modules (bidirectional: diagram ↔ codebase)
- [ ] AI devil's advocate mode: challenges assumptions, suggests alternatives
- [ ] All canvas brainstorm outputs captured in Recall for future reference

### 3.5e. Follow Mode & Rich Presence
- [ ] Click teammate's avatar → your panel layout mirrors theirs in real-time (Figma-style follow)
- [ ] Before entering follow mode: call `dockviewApi.toJSON()` and store snapshot in a ref. On unfollow: restore from snapshot. Follow mode must not destroy unsaved panel state.
- [ ] Opt-in presentation mode: one person drives, team follows
- [ ] "Unfollow" to return to your own layout — guaranteed by snapshot restore
- [ ] Cross-panel presence indicators via Yjs awareness:
  - Collaborator avatars on file tree items (who has this file open)
  - Collaborator cursors in code editor (CodeMirror 6 + Yjs awareness)
  - "N people viewing" badges on canvas rooms
  - Who's in which terminal session
  - Who's in which AI conversation
- [ ] User status: online, away, focused, in meeting, do not disturb
- [ ] Throttle awareness updates to 5-10 FPS to prevent network spam

### 3.5f. "What Happened While I Was Away" Digest
- [ ] AI-generated summary of team activity since last login
- [ ] Covers: commits, AI conversations, decisions made, canvas changes, new tasks, meetings
- [ ] Powered by Recall + existing activity feed
- [ ] Presented on login as a dismissable panel
- [ ] Extend existing `EventStreamContext.tsx` for digest delivery

### 3.5g. Shared Terminal Sessions (Mob Programming)
- [ ] Extend existing `SharedTerminal.tsx` for multi-user input
- [ ] Driver/navigator roles: one person types, others observe with live cursor
- [ ] Role switching: "pass the keyboard" via click or shortcut
- [ ] Session recording for async review

---

## Phase 4: Integration & Polish

- [ ] End-to-end testing across all panel types
- [ ] Admin panel: user management, system settings, resource monitoring
- [ ] Layout persistence stress testing (10+ panels, page refresh, reconnection)
- [ ] Performance profiling: memory per terminal, panel mount/unmount leaks
- [ ] Security audit: path traversal, RLS bypass, WebSocket auth, RBAC enforcement
- [ ] BrickLayer Audit campaign: `bl run --project codevvOS --mode audit --questions phase4-compliance.md`

**Parallelism note:** Phase 5 (ISO build) can run in parallel with Phase 4. ISO work is OS-level and independent of feature completeness — assign to a separate track.

---

## Phase 4.5: Migration Checklist — Apply During Phases 1–3

> **IMPORTANT:** This checklist must be worked through during Phases 1–3, not after Phase 4. The numbered placement here is for reference only. Building Phase 1+ against the wrong baseline from the existing CodeVV codebase will result in incorrect assumptions throughout the project. Cross-reference this section at the start of each Phase 1, 2, and 3 task.
>
> Source: `https://github.com/Nerfherder16/Codevv`

### Frontend Migration
- [ ] **REUSE:** React 19 setup, Tailwind v4, Vite config, LiveKit client
- [ ] **PORT:** AIChatContext + /api/ai routes (extend for multi-participant), Yjs client, SharedTerminal (reconnect to ptyHost), login screen
- [ ] **REWRITE:** Sidebar → dockview (largest single UI change — feature branch, not incremental refactor), OAuth PKCE UI → API key input, file browser → @headless-tree/react + @tanstack/react-virtual v3
- [ ] dockview replacement is **incompatible** with existing navigation model — do on a dedicated `feat/dockview-shell` branch

### Backend Migration
- [ ] **REUSE:** FastAPI scaffold, middleware, CORS, SSE streaming, 8 AI tools, Recall integration
- [ ] **PORT:** SQLAlchemy async sessions (add `expire_on_commit=False`), Pydantic models (add multi-tenant fields), file endpoints (add `verify_path_in_workspace`)
- [ ] **DELETE:** `claude_auth.py` OAuth PKCE module — remove entirely, do not patch. Purge all stored OAuth tokens before deploying.
- [ ] **REWRITE:** PostgreSQL schema (multi-tenant RLS, new tables, composite indexes, remove pgvector)

### Auth Migration
- [ ] **KEEP:** `/auth/login` JWT user auth — correct and working
- [ ] **DELETE:** `claude_auth.py` — entire file. The `claude_credentials` table: repurpose for encrypted API keys or drop.
- [ ] JWT secret: if moving to Docker secret, all active sessions invalidate — plan maintenance window

### Data Migration Risks
- [ ] **tldraw documents:** Yjs blob format → tldraw-sync format incompatible. Decide before Phase 3.5-d: wipe canvas data at cutover OR build one-time export tool via `tldraw.getSnapshot()`
- [ ] **pgvector:** Drop columns + extension cleanly. Verify with `\dx` before dropping.
- [ ] **OAuth tokens:** Purge `claude_credentials` table before deploying auth migration
- [ ] **dockview layout:** No existing layouts to migrate at launch, but version from day one

---

## Phase 5: Boot-to-Browser ISO (DEFERRED — after Phases 1-4 validated)

### 5a. Alpine Linux Base
- [ ] Minimal Alpine Linux rootfs (~235MB with Chromium kiosk stack)
- [ ] systemd-boot (UEFI direct, skip GRUB for faster boot)
- [ ] Read-only root filesystem (overlayroot or `mount -o ro`)
- [ ] Persistent partition for `/var/lib/docker` (overlay2 incompatible with overlayroot)
- [ ] Partition layout: EFI (256MB) + rootfs (2-4GB, ro) + docker (8-20GB) + data (remaining)

### 5b. Kiosk Compositor
- [ ] Cage (single-app Wayland kiosk compositor) + Chromium `--kiosk --ozone-platform=wayland`
- [ ] systemd service with `Restart=always` for crash recovery
- [ ] Disable DPMS/screen blanking: `consoleblank=0`, `IdleAction=ignore`
- [ ] Scheduled Chromium restart every 6-12h (memory leak mitigation)

### 5c. Boot Chain
- [ ] Docker Compose auto-start on boot via systemd/OpenRC
- [ ] Native health checks gate browser launch (don't start Cage until services healthy)
- [ ] Loading splash page that auto-refreshes until app responds
- [ ] Target boot time: 8-15 seconds to browser on SSD

### 5d. ISO Build Pipeline
- [ ] Alpine `mkimage` with custom `mkimg.profile.sh`
- [ ] Docker images pre-loaded on persistent partition (not pulled on first boot)
- [ ] CI/CD: containerized build in GitHub Actions

### 5e. Update Mechanism
- [ ] Container-based updates: OS immutable, `docker compose pull && docker compose up -d`
- [ ] OS-level updates via full ISO replacement (rare)
- [ ] Rollback via pinned Docker image tags

---

## Phase 6: Production Deployment

### 6a. Proxmox Setup
- [ ] Verify IOMMU groups with enumeration script before committing slot layout
- [ ] BIOS: enable SVM, IOMMU, Above 4G Decoding. Disable ReBAR, CSM, Secure Boot
- [ ] Kernel params: `amd_iommu=on iommu=pt video=efifb:off`
- [ ] Bind GPUs to vfio-pci at boot (blacklist nouveau/nvidia)
- [ ] Prepare VBIOS ROM dump for RTX 3090 Ampere reset bug workaround

### 6b. GPU Passthrough
- [ ] GPU VM: q35 machine type, OVMF UEFI, `cpu: host`, `balloon: 0`
- [ ] Pass 1x RTX 3090 with `pcie=1,rombar=1` (second GPU reserved for future use)
- [ ] Install NVIDIA driver with `--dkms` inside VM
- [ ] Install `nvidia-container-toolkit` for Docker GPU access
- [ ] NVLink bridge optional — only needed if both GPUs are passed through later

### 6c. GPU VM Services (Recall + Ollama)
- [ ] **Hostname resolution strategy:** `http://gpu-vm:8200` requires that `gpu-vm` resolves to the GPU VM's IP from inside the backend Docker container. Two separate Proxmox VMs cannot rely on Docker DNS. Options: (a) add static `extra_hosts: ["gpu-vm:192.168.x.x"]` to the backend service in docker-compose.yml, or (b) configure Proxmox/LAN DNS. Choose one and document it — without this, all Recall calls fail at deployment time even if Recall is running.
- [ ] Deploy fresh Recall instance from scratch (not migrated from existing personal Recall)
- [ ] Ollama with `nomic-embed-text` (embeddings) + `qwen3:14b` (NL tasks) — light workload, 1x RTX 3090 sufficient
- [ ] Recall Docker stack: Qdrant, Neo4j, PostgreSQL, Redis, ARQ — all in GPU VM
- [ ] Recall talks to Ollama locally within VM (localhost:11434)
- [ ] Configure Recall API key auth on first deploy — store `RECALL_API_KEY` as Docker secret in CodeVV compose
- [ ] CodeVV-OS VM talks to Recall via network (http://gpu-vm:8200) using API key header
- [ ] Claude Code (Teams account) is the primary AI — cloud-based, no local GPU needed
- [ ] CodeVV backend does NOT call Ollama directly — only through Recall's API

### 6d. ZFS Storage Pools
- [ ] Boot mirror: 2x NVMe, ashift=12, lz4, recordsize=128K
- [ ] AI pool mirror: 2x NVMe, ashift=12, lz4, recordsize=1M, primarycache=metadata
- [ ] Data pool: 1x NVMe 8TB, lz4, copies=2 (single-drive protection)
- [ ] Limit ARC to 16GB (`zfs_arc_max=17179869184`)
- [ ] WARNING: Monitor Samsung 990 PRO 4TB SMART health — documented reliability issues

### 6e. Backup & DR
- [ ] Proxmox Backup Server for incremental VM snapshots
- [ ] pgBackRest for PostgreSQL PITR
- [ ] Sanoid for automated ZFS snapshots (hourly/daily/weekly/monthly)
- [ ] Pre-snapshot PostgreSQL CHECKPOINT hook
- [ ] Syncoid for offsite replication

### 6f. Thermal & Power
- [ ] CPU: sTR5 full-coverage 360mm AIO (SilverStone XE360-TR5 or Enermax LIQTECH XTR)
- [ ] GPUs: Water cooling recommended for 700W in 12U rack (or source blower RTX 3090s)
- [ ] PSU: 1600W minimum (1800W recommended) with 4x PCIe 8-pin connectors
- [ ] Target: < 25C ambient in rack room

### 6g. Networking & Access
- [ ] mkcert for LAN SSL (generate CA, distribute to devices)
- [ ] Apache Guacamole for remote access fallback
- [ ] Monitoring: Grafana + Prometheus + dcgm-exporter (GPU metrics from VM)

---

## Phase 7: Polish & Distribution

- [ ] Custom branding and boot splash
- [ ] Bare-metal installer
- [ ] End-user documentation

---

## Technology Decisions (Research-Validated)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Excel editor | Univer + `@univerjs/sheets-import-xlsx` | Open-source, full formula/chart support. V1 single-user only. V2 adds univer-server collab. |
| DOCX viewer/editor | docx-preview + mammoth.js + TipTap | View + edit + export round-trip. ONLYOFFICE optional for full fidelity |
| PDF viewer | PDF.js (already in Chromium) | Zero-overhead, annotations stored in Recall |
| Full office suite (optional) | ONLYOFFICE Docker service (isolated network) | Isolated, JWT secret required, pinned version. Never LAN-exposed. |
| Virtualized tree | `@tanstack/react-virtual` v3 | Replaces react-window (unmaintained, no React 19). Native pairing with @headless-tree/react |
| Artifact Panel | `srcdoc` null-origin iframe + `allow-scripts` only | Server-side compile to React.createElement(). No unsafe-eval. No allow-same-origin. |
| Code sandbox runtime | Docker container (Node.js + Python) via sandbox-manager | sandbox-manager owns docker.sock. Backend never touches Docker directly. Go preferred for sandbox-manager; Python with `aiodocker` (async) acceptable. Never `docker-py` sync. |
| Environment clone sandbox | Docker container snapshot via sandbox-manager | Auto-triggered per branch (branch auto-environments) or manual |
| Simulation engine | BrickLayer simulate runner + Artifact Panel | Data sims + system sims, results as interactive charts |
| Interactive charts | recharts / D3 / Chart.js (Claude selects) | Claude picks library based on data shape |
| Inline AI editing | CodeMirror 6 + `Cmd+K` inline prompt (CodeMirror focus only) | Fires only when CodeMirror is focused. Elsewhere, `Cmd+Shift+K` opens command palette. Resolved Cmd+K collision. |
| Live preview | Hot-reload iframe panel proxied through Nginx | Auto-detects dev server port. Viewport simulator. Error overlay. |
| BrickLayer integration | Docker sidecar service + `bl/server.py` FastAPI wrapper | SSE streaming endpoints + interrupt/kill. asyncio.to_thread() wrapping. |
| Masonry integration | `npm install masonry-mcp` in CodeVV Docker image (no separate container) | Node.js MCP server — subprocess within backend container. No masonry-mcp service in compose. 13 core services, not 14. |
| Background jobs | ARQ worker service (same backend image, separate command) | Required for digests, scheduled automation, notifications, polling |
| GitHub webhooks | Polling-first (ARQ, 60s interval) + Tailscale Funnel opt-in | LAN-only: GitHub can't reach the server. Polling is correct default. |
| tldraw sync | `@tldraw/sync-core` + `tldraw-sync` Docker service | tldraw v2 uses its own sync, not Yjs. Add tldraw-sync service. |
| Push notifications | pywebpush in worker service + VAPID keys in Docker secrets | No separate service for V1. Promote to push-notifier service if volume grows. |
| Pydantic settings | `pip install pydantic-settings` (separate package) | Pydantic v2 split settings into a separate PyPI package |

#### Complete Docker Compose Service List

```
Phase 0/1 (Core):
  postgres          postgres:16-alpine (no pgvector — not needed)
  redis             redis:7-alpine
  backend           codevv/backend:{version}
  frontend          codevv/frontend:{version}  (static, served via nginx)
  yjs               codevv/yjs:{version}
  nginx             nginx:alpine
  worker            codevv/backend:{version}   (ARQ, different command)

Phase 1b:
  sandbox-manager   codevv/sandbox-manager:{version}  (owns docker.sock via socket-proxy)
  ptyhost           codevv/ptyhost:{version}

Phase 3.5:
  livekit           livekit/livekit-server        (UDP 50000-60000 published)
  livekit-agents    codevv/livekit-agents:{version}
  tldraw-sync       codevv/tldraw-sync:{version}
  bricklayer        codevv/bricklayer:{version}   (port 8300, internal only)

Optional (Compose profiles):
  onlyoffice        onlyoffice/documentserver     (profile: onlyoffice, isolated network)
  univer-server     univer/collaboration-server   (profile: univer-collab, V2)

External (not in Compose):
  Recall            http://gpu-vm:8200
  Ollama            http://gpu-vm:11434  (Recall uses internally; CodeVV never calls directly)
```
**Total: 13 services core + 2 optional profiles**
| Personal AI assistant | Per-user Recall-scoped memory + open MCP tool loadout | Persistent personality, grows over time, proxy mode optional |
| Custom agents | BrickLayer crucible | Benchmarked, scored, promoted/retired based on performance |
| Knowledge graph | Recall (Neo4j) + AI-maintained | Live map of project — navigable, manually editable |
| Global search | ripgrep (code) + Recall semantic (memory/docs) | Scoped: file / project / all / Recall |
| Projector casting | W3C Presentation API + dedicated /projector Yjs-mirrored URL | Both modes — native cast + fallback URL |
| Canvas | tldraw (existing) + AI placement (ask-before-place) | Structured templates + freeform + code-linked diagrams |
| Workspace templates | dockview layouts + shortcut profiles + accent colors | Five templates: Brainstorm / Planning / Dev / Review / Meeting |
| Personal assistant automation | Trigger-based + scheduled MCP jobs | New PR, build failures, overdue tasks, daily/weekly digests |
| Settings persistence | PostgreSQL user settings + JSON export/import | Sync across machines on login |
| Mobile access | Responsive web via Tailscale + push notifications | No native app needed |
| Offboarding | Claude knowledge transfer summary + Recall purge option | Clean handoff, optional memory removal |
| Panel manager | `dockview-react` v5.2.0 | Zero deps, React 19, tabs+dock+float+serialize, most actively maintained |
| File tree | `@headless-tree/react` | 9.5kB, virtualized, accessible, successor to react-complex-tree |
| Terminal PTY | Node.js + `node-pty` | Production standard (VS Code, Theia, Gitpod). Python pty lacks flow control |
| Terminal frontend | xterm.js v6 + WebGL addon | Production standard, GPU-accelerated rendering |
| File watching | `watchfiles` (Rust-backed) | Faster, lower memory than Python watchdog |
| Settings UI | `@jsonforms/react` | Auto-rendered from Pydantic JSON Schema |
| Toast notifications | Sonner | Zero deps, simplest API, smallest footprint |
| Notification transport | SSE (separate from Yjs WebSocket) | Auto-reconnect, one-way fits notifications, don't multiplex on Yjs |
| PostgreSQL multi-tenant | Row-Level Security (RLS) | DB-enforced isolation, simpler than schema-per-user |
| Collab code editor | CodeMirror 6 + `y-codemirror.next` | For pair sessions. code-server stays for individual work |
| Yjs persistence | `y-postgresql` (update-row pattern) | Replace single-blob with per-update rows + periodic compaction |
| Offline resilience | `y-indexeddb` | Browser-side persistence for offline editing and instant page reload |
| Primary AI | Claude via Console API key (NOT subscription OAuth) | Org-level or per-user API keys. OAuth PKCE flow must be removed — banned for third-party apps since Jan 2026 |
| AI SDK | Claude Agent SDK (`claude-agent-sdk`) or raw `anthropic` SDK | Agent SDK recommended — gives Claude Code tools built-in. Both use API key auth |
| Local LLM | Ollama (GPU VM) | Serves Recall 1.0 only — `nomic-embed-text` + `qwen3:14b`. Light workload, 1x RTX 3090 sufficient |
| Semantic memory | Recall (GPU VM, fresh deploy) | Qdrant + Neo4j + PostgreSQL + Redis + ARQ. Fresh instance built for this project. CodeVV calls Recall API, not Ollama directly |
| Secrets management | Docker Compose file-based secrets + Pydantic `SecretsSettingsSource` | `/run/secrets/` with env var fallback. No wrapper needed |
| SSL (LAN) | mkcert | Generate CA once, distribute to devices, zero browser warnings |
| Container security | `read_only: true` + tmpfs + `no-new-privileges` | All services can run read-only. PostgreSQL needs `user: "999:999"` to bypass gosu |
| WebSocket auth | JWT in first message + in-band refresh | Not in query params (appears in logs). Refresh before expiry on long-lived connections |
| OS base | Alpine Linux | Smallest footprint (~235MB), Docker-native, proven kiosk use |
| Kiosk compositor | Cage | Purpose-built single-app Wayland compositor, VT switching blocked by default |
| ISO build | Alpine mkimage | Most maintainable for small team, CI-friendly |
| Update mechanism | Container-based | OS immutable, only containers change |
| Orchestration | Docker Compose | Right level for single-server 5-20 users |
| WebSocket transport | Raw WebSocket (not Socket.IO) | Lowest latency, production standard for terminals |
| ZFS tuning | ashift=12, lz4, ARC capped at 16GB | No SLOG/L2ARC needed for all-NVMe. Monitor 990 PRO health |
| Backup | PBS + pgBackRest + Sanoid | ZFS rollback < 30s, PITR in minutes, automated snapshots |

---

## Hardware Warnings (From Research)

| Item | Risk | Mitigation |
|------|------|-----------|
| Samsung 990 PRO 4TB | Documented rapid health degradation, drives disappearing under load | Monitor SMART weekly. Consider enterprise NVMe (Micron 7450, Samsung PM9A3) |
| RTX 3090 passthrough | Ampere reset bug — GPU fails to reset after VM shutdown | Bind to vfio-pci at boot, dump VBIOS ROM, disable ReBAR |
| RTX 3090 cooling in rack | 700W open-air heat in 12U enclosure | Water-cool GPUs or source rare blower variants |
| Enermax LIQTECH XTR | History of pump clogging/failure | Alternative: SilverStone XE360-TR5 (purpose-built sTR5) |
| Memory ballooning | Breaks with GPU passthrough | Disable ballooning on all passthrough VMs (`balloon: 0`) |

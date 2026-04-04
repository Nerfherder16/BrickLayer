# CodeVV OS — BUILD_BIBLE.md

**Authority: Tier 2 — Human + Agent**
**Last updated: 2026-04-02**
**Status: ACTIVE — applies to all phases from Phase 0 onward**

---

## Purpose

This document is the single authoritative source for how CodeVV OS gets built, tested, reviewed, deployed, and maintained. Every developer, every agent, every CI job follows what is written here. Ambiguity in this document is a bug — file an issue.

---

## 1. Repository & Branch Strategy

### Branch Naming

```
main              Production-ready. Protected. Never commit directly.
dev               Integration branch. All feature branches merge here first.
feat/<ticket>     New features. Branch from dev.
fix/<ticket>      Bug fixes. Branch from dev (or main for hotfixes).
chore/<ticket>    Infrastructure, deps, CI, non-behavioral changes.
phase/<n>         Long-lived phase branch (e.g., phase/1-infrastructure).
hotfix/<ticket>   Emergency fix. Branch from main. Merges to main + dev.
```

### Branch Rules

- `main` requires: passing CI, one human approval, no merge conflicts.
- `dev` requires: passing CI, one review (agent reviews count for non-critical paths).
- Feature branches live max 5 days before they must be rebased onto dev or closed.
- Phase branches (`phase/1-infrastructure`) act as a staging area; individual `feat/` branches merge into the phase branch, phase branch merges to `dev` when the phase is complete.
- Delete branches on merge — no branch graveyard.

### Commit Format (Conventional Commits)

```
<type>(<scope>): <subject>

Types: feat | fix | chore | refactor | test | docs | perf | security | ci
Scope: backend | frontend | yjs | ptyhost | nginx | worker | sandbox | bricklayer | db | iso

Examples:
feat(backend): add verify_path_in_workspace FastAPI dependency
fix(ptyhost): send SIGHUP on disconnect before SIGKILL timeout
security(backend): remove docker.sock from backend container
test(frontend): add dockview layout persistence unit tests
```

Commit body required when the change is non-obvious. Reference ROADMAP items: `Implements ROADMAP 1b.`

---

## 2. PR Size Limits & Review Policy

### Size Limits

| Category | Limit | Action if Exceeded |
|----------|-------|--------------------|
| Lines changed (non-test) | ≤ 400 lines | Split PR before review |
| Files touched | ≤ 15 files | Split PR before review |
| Migrations included | ≤ 1 per PR | One migration per PR |
| New services added | ≤ 1 per PR | One Docker service per PR |

These are hard limits. The PR author splits before requesting review — reviewers do not split PRs.

### Review Policy

- All PRs require at least one human review before merging to `dev` or `main`.
- Security-tagged PRs (`security(...)` commits or touching `auth.py`, `auth.js`, JWT logic, RLS policies, path traversal dependencies, Docker secrets) require Tim's explicit approval.
- Agent-authored PRs (BrickLayer/rough-in output) require human review before merge to `dev`. Agents may auto-merge to phase branches only.
- Migrations require human review with no exceptions — they are irreversible.

### What Reviewers Check

1. Does the implementation match the ROADMAP item specification exactly?
2. Are Phase 0 security pre-requirements violated? (RLS bypassed, docker.sock mounted, JWT skipped, etc.)
3. Are performance budgets respected?
4. Are tests present, meaningful, and red-before-green verified?
5. Does the PR touch a Tier 1 file (`project-brief.md`, `ARCHITECTURE.md`)? If so, reject — agents do not edit Tier 1.

---

## 3. Testing Strategy

### The Pyramid

```
                    ▲
                   /E2E\          5%  — Playwright (cross-service flows)
                  /──────\
                 / Integ  \      20%  — pytest + httpx / Vitest + MSW
                /──────────\
               /    Unit    \    75%  — pytest / Vitest (isolated, fast)
              ──────────────────
```

**Target ratio: 75 / 20 / 5.** Any PR that inverts this (heavy on E2E, light on unit) is returned for rebalancing.

**Total test suite must pass in < 5 minutes on CI.** E2E suite runs in a separate CI job (`test:e2e`) triggered only on PRs to `dev` and `main`.

---

### 3a. FastAPI Backend (Python)

**Framework:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient`
**Fixtures:** `conftest.py` per service package — shared DB session, Redis mock, JWT factory
**Coverage tool:** `pytest-cov` — minimum 80% line coverage per module, enforced in CI

#### Unit Tests (per endpoint/dependency)

```bash
# Run unit tests only (no DB, no Redis — everything mocked)
pytest tests/unit/ -x -q --timeout=30

# With coverage
pytest tests/unit/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

Pattern per endpoint:
```python
# tests/unit/test_files_api.py
async def test_get_file_tree_rejects_path_traversal(client, jwt_token):
    """verify_path_in_workspace blocks ../../etc/passwd attempts"""
    resp = await client.get(
        "/api/files/tree?path=../../etc/passwd",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert resp.status_code == 400

async def test_get_file_tree_returns_directory_listing(client, jwt_token, tmp_workspace):
    resp = await client.get(
        f"/api/files/tree?path={tmp_workspace}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert resp.status_code == 200
    assert "children" in resp.json()
```

TDD sequence for every new endpoint:
1. Write test → `pytest` → RED (404 or AttributeError)
2. Implement route → `pytest` → GREEN
3. Add integration test with real DB → GREEN
4. Never skip step 1 — hooks enforce this

#### Integration Tests (real DB, real Redis)

```bash
# Requires running postgres + redis (docker compose -f docker-compose.test.yml up -d)
pytest tests/integration/ -x -q --timeout=60
```

Use `pytest-postgresql` for ephemeral Postgres, not the production instance:
```bash
pip install pytest-postgresql
# conftest.py: fixture `pg` → isolated database per test session
```

RLS tests are integration-only — they require a real Postgres with policies applied:
```python
async def test_rls_blocks_cross_tenant_project_access(pg, codevv_app_role_session):
    """codevv_app role must not read another tenant's projects"""
    tenant_a_project = await create_project(pg, tenant_id="tenant-a")
    async with codevv_app_role_session(tenant_id="tenant-b") as session:
        result = await session.execute(select(Project).where(Project.id == tenant_a_project.id))
        assert result.scalar() is None
```

#### SSE Endpoint Tests

```python
async def test_file_watch_sse_emits_on_change(client, jwt_token, tmp_workspace):
    """SSE /api/files/watch emits an event within 500ms of file modification"""
    async with client.stream("GET", f"/api/files/watch?path={tmp_workspace}",
                              headers={"Authorization": f"Bearer {jwt_token}"}) as resp:
        # modify file in background
        asyncio.create_task(modify_file_after_delay(tmp_workspace / "test.py", delay=0.1))
        async for line in resp.aiter_lines():
            if line.startswith("data:"):
                event = json.loads(line[5:])
                assert event["type"] == "change"
                break
```

#### Slowapi Rate Limit Tests

```python
async def test_ai_endpoint_rate_limited_per_user(client, jwt_tokens):
    """POST /api/ai must return 429 after limit is exceeded"""
    for _ in range(10):
        resp = await client.post("/api/ai", json={...}, headers={"Authorization": f"Bearer {jwt_tokens[0]}"})
    assert resp.status_code == 429
    # Different user should still succeed
    resp = await client.post("/api/ai", json={...}, headers={"Authorization": f"Bearer {jwt_tokens[1]}"})
    assert resp.status_code == 200
```

---

### 3b. React Frontend (TypeScript)

**Framework:** Vitest + `@testing-library/react` + `@testing-library/user-event`
**MSW:** `msw` v2 for API mocking in browser and Node environments
**E2E:** Playwright (separate suite)

```bash
# Unit/integration tests
npx vitest run --reporter=verbose

# Watch mode (dev)
npx vitest

# Coverage
npx vitest run --coverage --coverage.thresholds.lines=75
```

#### Component Unit Tests

Every new component gets a test file. Test behavior, not implementation.

```typescript
// src/components/FileBrowser/FileBrowser.test.tsx
describe("FileBrowser", () => {
  it("should render directory listing from API response", async () => {
    server.use(
      http.get("/api/files/tree", () =>
        HttpResponse.json({ children: [{ name: "src", type: "dir" }] })
      )
    );
    render(<FileBrowser path="/workspace" />);
    expect(await screen.findByText("src")).toBeInTheDocument();
  });

  it("should expand directory on click", async () => {
    // ...
  });
});
```

#### dockview Layout Tests

```typescript
describe("DockviewLayout", () => {
  it("should serialize and restore layout", () => {
    const { result } = renderHook(() => useDockviewLayout());
    const layout = result.current.api.toJSON();
    expect(() => result.current.api.fromJSON(layout)).not.toThrow();
  });

  it("should fall back to default layout on invalid JSON", () => {
    const { result } = renderHook(() => useDockviewLayout());
    expect(() => result.current.api.fromJSON(null)).not.toThrow();
    // Default layout panels must exist
    expect(result.current.panels).toHaveLength(DEFAULT_PANEL_COUNT);
  });
});
```

#### Hooks Tests

```typescript
// src/hooks/useWebSocket.test.ts
describe("useWebSocket", () => {
  it("should reconnect after server close", async () => {
    const { result } = renderHook(() => useWebSocket("/pty/session-1"));
    await waitFor(() => expect(result.current.readyState).toBe(WebSocket.OPEN));
    server.simulateClose("/pty/session-1");
    await waitFor(() => expect(result.current.readyState).toBe(WebSocket.OPEN), {
      timeout: 5000,
    });
  });
});
```

#### xterm.js Terminal Tests

xterm.js requires a real DOM and WebGL. Unit tests use `canvas` mock; E2E validates the actual renderer.

```typescript
// tests/unit/Terminal.test.tsx — lightweight, no WebGL
it("should dispose terminal and addons on unmount", () => {
  const { unmount } = render(<SharedTerminal sessionId="test" />);
  const disposeSpy = vi.spyOn(Terminal.prototype, "dispose");
  unmount();
  expect(disposeSpy).toHaveBeenCalled();
});
```

#### Artifact Panel / iframe Tests

```typescript
it("should NOT include allow-same-origin in sandbox attribute", () => {
  const { container } = render(<ArtifactPanel content="<div>test</div>" />);
  const iframe = container.querySelector("iframe");
  expect(iframe?.getAttribute("sandbox")).toContain("allow-scripts");
  expect(iframe?.getAttribute("sandbox")).not.toContain("allow-same-origin");
});

it("should validate postMessage origin before processing", () => {
  // verify event.origin check exists
});
```

---

### 3c. ARQ Background Workers (Python)

Workers run the same Python codebase. Test them as async functions, not via Redis queue.

```bash
pytest tests/workers/ -x -q --timeout=60
```

```python
# tests/workers/test_notification_worker.py
async def test_push_notification_worker_sends_web_push(mock_webpush, user_with_subscription):
    """Worker must call pywebpush for subscribed users"""
    await send_push_notification(user_id=user_with_subscription.id, payload={"title": "Test"})
    mock_webpush.assert_called_once()

async def test_scheduled_digest_only_fires_when_stale(db, user):
    """Digest gate: only show if last login > 2h and feed has > 5 new events"""
    user.last_seen_digest_at = datetime.utcnow() - timedelta(hours=1)
    result = await should_show_digest(user, event_count=10)
    assert result is False

    user.last_seen_digest_at = datetime.utcnow() - timedelta(hours=3)
    result = await should_show_digest(user, event_count=10)
    assert result is True
```

---

### 3d. Database Migrations (Alembic)

**Rule: every migration requires a down migration (`downgrade`). No `pass` in downgrade.**

```bash
# Generate
alembic revision --autogenerate -m "add_tasks_table"

# Apply (test DB)
alembic upgrade head

# Verify rollback
alembic downgrade -1
alembic upgrade head

# Test migration in CI
pytest tests/migrations/ -x -q
```

Migration test pattern:
```python
# tests/migrations/test_rls_policies.py
def test_codevv_app_role_cannot_bypass_rls(pg_with_migrations):
    """After all migrations, codevv_app role must have NOBYPASSRLS"""
    result = pg_with_migrations.execute(
        "SELECT rolbypassrls FROM pg_roles WHERE rolname = 'codevv_app'"
    )
    assert result.scalar() is False

def test_composite_indexes_exist_on_tenant_tables(pg_with_migrations):
    """Tenant-scoped tables need (tenant_id, id) composite index"""
    for table in ["projects", "tasks", "activity_events"]:
        result = pg_with_migrations.execute(
            f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}' "
            f"AND indexdef LIKE '%tenant_id%id%'"
        )
        assert result.fetchone() is not None, f"Missing composite index on {table}"
```

---

### 3e. WebSocket / SSE Endpoints

These require real transport testing at the integration level. Do not test with mocks alone.

**Tools:** `websockets` Python library (for ptyHost WS tests), `httpx` SSE streaming, Playwright for E2E terminal validation.

```python
# tests/integration/test_ptyhost_ws.py
import websockets

async def test_ptyhost_rejects_connection_without_jwt():
    with pytest.raises(websockets.exceptions.InvalidStatusCode) as exc:
        async with websockets.connect("ws://localhost:3001/pty/new"):
            pass
    assert exc.value.status_code == 401

async def test_ptyhost_sends_data_message_on_input(valid_jwt):
    async with websockets.connect(
        "ws://localhost:3001/pty/new",
        extra_headers={"Authorization": f"Bearer {valid_jwt}"}
    ) as ws:
        # ack-based flow: send ACK for each received data message
        await ws.send(json.dumps({"type": "data", "data": "echo hello\n"}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
        assert msg["type"] == "data"
        assert "hello" in msg["data"]
```

---

### 3f. End-to-End Tests (Playwright)

**Location:** `tests/e2e/`
**Trigger:** PR to `dev` or `main` only (not every commit)
**Target:** `https://localhost` (local Docker Compose stack)

```bash
# Start test stack
docker compose -f docker-compose.test.yml up -d

# Run E2E
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug --headed
```

Critical E2E flows (one test per flow):

| Test | File | Coverage |
|------|------|----------|
| Login + JWT session | `e2e/auth.spec.ts` | OS-style login, JWT cookie, session |
| Dashboard renders on login | `e2e/dashboard.spec.ts` | Team panel, personal panel, activity feed |
| File browser tree expand | `e2e/files.spec.ts` | Lazy-load, SSE update, path traversal blocked |
| Terminal connect + echo | `e2e/terminal.spec.ts` | WebGL render, WS connect, PTY echo, resize |
| dockview layout persist across reload | `e2e/layout.spec.ts` | Serialize, reload, restore |
| Artifact Panel sandbox isolation | `e2e/artifact.spec.ts` | srcdoc iframe, no allow-same-origin, postMessage |
| Multi-user Yjs sync | `e2e/collab.spec.ts` | Two browser contexts, shared doc update |
| BrickLayer agent stream | `e2e/bricklayer.spec.ts` | SSE stream from `/bl/agent/*/stream`, live log panel |

E2E tests must not share state between tests. Each test gets a fresh user, fresh session.

---

## 4. CI/CD Pipeline

### Pipeline Overview

```
push to feat/* or fix/*
    └─ [fast-check]  lint + type-check + unit tests (< 3 min)

PR to dev
    ├─ [fast-check]
    ├─ [integration]  real DB + Redis (< 5 min)
    ├─ [e2e]          Playwright full stack (< 10 min)
    ├─ [security]     bandit + semgrep + dependency audit
    └─ [build-check]  docker build all images (< 8 min)

merge to dev
    └─ [deploy-dev]  push to dev environment (if configured)

PR to main
    ├─ all above +
    └─ [perf-check]  Lighthouse + bundle size check

merge to main
    └─ [deploy-prod] tag + push images + deploy
```

### Stage: fast-check

```yaml
# .github/workflows/fast-check.yml
jobs:
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: mypy backend/app --strict --ignore-missing-imports

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: npm ci
        working-directory: frontend/
      - run: npx tsc --noEmit
        working-directory: frontend/
      - run: npx eslint src/ --max-warnings=0
        working-directory: frontend/

  unit-backend:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements.txt pytest pytest-asyncio pytest-cov
      - run: pytest tests/unit/ -x -q --timeout=30 --cov=app --cov-fail-under=80

  unit-frontend:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci && npx vitest run --coverage --coverage.thresholds.lines=75
        working-directory: frontend/
```

### Stage: integration

```yaml
  integration-backend:
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: codevv_test }
        options: --health-cmd pg_isready
      redis:
        image: redis:7-alpine
        options: --health-cmd "redis-cli ping"
    steps:
      - run: alembic upgrade head
        env: { DATABASE_URL: "postgresql+asyncpg://postgres:test@postgres/codevv_test" }
      - run: pytest tests/integration/ -x -q --timeout=60
      - run: pytest tests/migrations/ -x -q
```

### Stage: security

```bash
# backend static analysis
bandit -r backend/app/ -ll -f json -o bandit-report.json
semgrep --config=p/python --config=p/fastapi backend/ --error

# frontend dependency audit
npm audit --audit-level=high
cd frontend && npm audit --audit-level=high

# Python dependencies
pip-audit -r requirements.txt --fail-on-severity high

# Secret scan (block commits with secrets)
trufflehog filesystem . --fail --no-update
```

### Stage: build-check

```bash
# Build all images, verify they start and pass healthcheck
docker compose -f docker-compose.yml build --no-cache
docker compose -f docker-compose.yml up -d
sleep 10
docker compose ps | grep -v "healthy" | grep -v "Exited 0" | wc -l
# must be 0

# Image size check (see performance budgets below)
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | grep codevv
```

### Stage: perf-check (PRs to main)

```bash
# Bundle size analysis
cd frontend && npm run build
npx bundlesize  # reads from package.json bundlesize config

# Lighthouse via Playwright
npx playwright test tests/perf/lighthouse.spec.ts
```

---

## 5. Performance Budgets

These are enforced in CI. A PR that violates a budget fails CI.

### Frontend

| Metric | Budget | Tool | Enforcement |
|--------|--------|------|-------------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | Lighthouse (Playwright) | CI perf-check |
| FCP (First Contentful Paint) | ≤ 1.0s | Lighthouse | CI perf-check |
| TTI (Time to Interactive) | ≤ 3.5s | Lighthouse | CI perf-check |
| Lighthouse Performance Score | ≥ 85 | Lighthouse | CI perf-check |
| JS bundle (initial, gzipped) | ≤ 250KB | bundlesize | CI perf-check |
| JS bundle (total vendor, gzipped) | ≤ 500KB | bundlesize | CI perf-check |
| CSS bundle (gzipped) | ≤ 30KB | bundlesize | CI perf-check |
| xterm.js addon chunk | ≤ 120KB | bundlesize | CI perf-check |
| dockview chunk | ≤ 80KB | bundlesize | CI perf-check |

`bundlesize` config in `frontend/package.json`:
```json
"bundlesize": [
  { "path": "./dist/assets/index-*.js", "maxSize": "250 kB" },
  { "path": "./dist/assets/vendor-*.js", "maxSize": "500 kB" },
  { "path": "./dist/assets/index-*.css", "maxSize": "30 kB" }
]
```

Yjs awareness throttle: Vitest unit test must assert awareness updates fire at ≤ 10 FPS (100ms debounce minimum). `fitAddon.fit()` must debounce at 150–200ms via `ResizeObserver` — unit test must assert this.

### Backend API (FastAPI)

| Endpoint Class | p95 Latency | p99 Latency | Tool |
|----------------|-------------|-------------|------|
| Auth endpoints (`/auth/*`) | ≤ 100ms | ≤ 250ms | k6 |
| File tree (`GET /api/files/tree`) | ≤ 200ms | ≤ 500ms | k6 |
| Settings CRUD | ≤ 150ms | ≤ 300ms | k6 |
| Notifications list | ≤ 100ms | ≤ 200ms | k6 |
| AI endpoints (`/api/ai`) — first SSE byte | ≤ 800ms | ≤ 2000ms | k6 |
| BrickLayer agent spawn | ≤ 500ms | ≤ 1500ms | k6 |

Load test script (run before major releases, not every PR):
```bash
k6 run tests/perf/api-load.js --vus=20 --duration=60s
# Must report: p95 < thresholds, 0% error rate
```

### Docker Image Sizes

| Image | Max Compressed Size | Notes |
|-------|---------------------|-------|
| `codevv/backend` | ≤ 400MB | Python 3.12-slim base, no dev deps |
| `codevv/frontend` | ≤ 50MB | nginx:alpine serving static build |
| `codevv/yjs` | ≤ 150MB | Node.js 22-alpine |
| `codevv/ptyhost` | ≤ 200MB | Node.js 22-alpine + node-pty |
| `codevv/sandbox-manager` | ≤ 200MB | Node.js 22-alpine + docker socket proxy |
| `codevv/bricklayer` | ≤ 600MB | Python + tmux + claude CLI |
| `codevv/livekit-agents` | ≤ 300MB | Python + LiveKit Agents SDK |

Enforce in `build-check` CI stage:
```bash
MAX_BACKEND=400
SIZE=$(docker image inspect codevv/backend --format='{{.Size}}' | awk '{print int($1/1024/1024)}')
if [ "$SIZE" -gt "$MAX_BACKEND" ]; then echo "IMAGE TOO LARGE: ${SIZE}MB > ${MAX_BACKEND}MB"; exit 1; fi
```

### ISO / Boot

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Alpine rootfs compressed | ≤ 250MB | 400MB |
| Boot to browser (NVMe, cold) | ≤ 15s | 30s |
| Docker Compose service healthy (all) | ≤ 45s | 90s |
| Memory per terminal session (xterm.js) | ≤ 15MB | 30MB |
| Memory per Yjs document connection | ≤ 5MB | 10MB |

---

## 6. TDD Strategy Per Service Type (Summary Table)

| Service | Test Framework | Mocking Layer | DB Strategy | SSE/WS Strategy |
|---------|---------------|---------------|-------------|-----------------|
| FastAPI backend | pytest + pytest-asyncio | unittest.mock, pytest fixtures | pytest-postgresql (ephemeral) | httpx streaming client |
| ARQ workers | pytest + pytest-asyncio | mock pywebpush, mock Redis | pytest-postgresql | n/a |
| Alembic migrations | pytest + sqlalchemy | none — real PG required | dedicated test DB | n/a |
| React components | Vitest + RTL | msw v2 | n/a (API mocked) | msw WebSocket handler |
| React hooks | Vitest + renderHook | msw v2, vi.mock | n/a | msw WebSocket handler |
| ptyHost (Node.js) | Jest + `ws` mock | ws mock server | n/a | ws mock |
| ptyHost WS (integration) | pytest websockets | none — real ptyHost | n/a | real WebSocket |
| Yjs server | Jest | none (test real Yjs) | y-postgresql mock | real WebSocket |
| Nginx config | `nginx -t` + curl smoke | none | n/a | curl --no-buffer SSE |
| E2E full stack | Playwright | none — real stack | real test DB | real WebSocket |

---

## 7. BrickLayer Build Orchestration

BrickLayer drives every build phase. This section defines exactly how the tool maps to the project lifecycle.

### Phase 0 — Security & Architecture Pre-Checks

Before any Phase 1 code is written, BrickLayer runs a **Validate** campaign against the ROADMAP Phase 0 checklist.

```bash
# From BrickLayer 2.0 root
bl run --project codevvOS --mode validate --questions phase0-security.md
```

Each Phase 0 item becomes a BrickLayer question with a `HEALTHY` / `FAILURE` verdict. **Build does not proceed to Phase 1 if any Phase 0 question returns `FAILURE`.** This is enforced by Trowel — the campaign conductor.

Campaign questions example:
```
Q: Does the Docker Compose config use `expose:` (not `ports:`) for postgres/redis/yjs/backend?
Q: Is there a codevv_app Postgres role with NOBYPASSRLS?
Q: Does verify_path_in_workspace use os.path.realpath()?
Q: Is docker.sock absent from the backend service definition?
```

The campaign produces findings in `projects/codevvOS/findings/phase0/`. Mortar reviews findings and gates Phase 1 start.

### Phase 1 — Infrastructure & Backend (TDD-driven build)

**Entry point:** `/build` on a Phase 1 spec. BrickLayer orchestrates via the **rough-in → Queen Coordinator → workers** pipeline.

**rough-in** decomposes the Phase 1 ROADMAP into discrete build tasks:
- Each ROADMAP item becomes one or two tasks (test task + implementation task)
- Tasks have explicit dependencies (e.g., Docker healthcheck task before depends_on task)
- Maximum 8 tasks dispatched in parallel per wave

**Queen Coordinator** dispatches up to 8 worker agents per wave:
- `test-writer` writes FAILING tests first (never sees the spec — context-isolated)
- `developer` implements to pass tests (never sees the spec directly)
- `code-reviewer` reviews after developer completes
- `security` agent checks all auth/path/RLS implementations
- `git-nerd` commits each completed task with conventional commit message

**Trowel** runs parallel research when workers encounter unknowns (e.g., ARQ worker config, yjs-postgresql update pattern).

Worker dispatch example for Phase 1d (Backend API Extensions):
```python
# bl/tmux/wave.py
tasks = [
    {"agent": "test-writer",  "prompt": "Write FAILING tests for GET /api/files/tree with path traversal validation"},
    {"agent": "test-writer",  "prompt": "Write FAILING tests for PATCH /api/files/{path:path} operations"},
    {"agent": "test-writer",  "prompt": "Write FAILING tests for GET /api/settings/schema Pydantic→draft7 conversion"},
    {"agent": "test-writer",  "prompt": "Write FAILING tests for slowapi rate limiting on /api/ai endpoints"},
]
wave = spawn_wave(tasks, aggregation="all_complete")
wait_for_wave(wave)

# Then dispatch developer agents for each
```

**Heal loop** handles failures:
- If `developer` fails to pass tests after 2 attempts → `diagnose-analyst` → `fix-implementer`
- Maximum 3 heal cycles per task before escalating to Tim

### Phase 2 — Frontend Shell

Same pipeline as Phase 1 but frontend-focused:
- `test-writer` uses Vitest + RTL
- `developer` implements React components
- `code-reviewer` checks bundle size impact + accessibility
- `uiux-master` reviews visual output via Playwright screenshot comparison

BrickLayer runs a **Benchmark** campaign before Phase 2 merge:
```bash
bl run --project codevvOS --mode benchmark --questions frontend-perf.md
```
Questions: LCP, FCP, bundle sizes, dockview layout serialize/restore cycle time.
A `UNCALIBRATED` verdict blocks merge.

### Phase 3 — Frontend Features

Each feature (3a–3f) is its own BrickLayer task batch. Features are independent — dispatched in parallel across separate tmux panes.

**xterm.js (3b)** gets a dedicated `test-writer` prompt that emphasizes the addon loading order invariant:
```
Write tests that assert:
1. Terminal.open(el) is called before any addon.attach()
2. WebGL context loss triggers CanvasAddon fallback
3. terminal.dispose() is called on React component unmount
```

**Artifact Panel (3.5-AP)** gets a `security` agent review in addition to standard code review, focused exclusively on:
- `allow-same-origin` absent from sandbox attribute
- `connect-src 'none'` in CSP
- `event.origin` validated on all postMessage handlers

### Phase 3.5 — Experience & Product Features

Complex, multi-service features. BrickLayer uses **swarm runners** with majority aggregation for verdicts on contested implementation questions:

```bash
# Example: dispute over tldraw sync strategy (ADR required)
bl run --project codevvOS --mode frontier --questions tldraw-sync-decision.md
# Runner: swarm, aggregation: majority
# Produces: ADR stored in docs/adr/
```

**Custom agents (3.5-CA)** go through BrickLayer crucible automatically:
- Each new agent definition → `masonry_pattern_store` + `masonry_agent_health` check
- Crucible benchmarks against reference tasks before agent is added to fleet
- Score below 0.6 → agent is flagged, not retired immediately → one retry cycle

**BrickLayer sidecar (3.5-BL)** is built by BrickLayer itself — self-referential:
- `bl/server.py` written via rough-in pipeline
- All `spawn_agent()` calls wrapped in `asyncio.to_thread()` — enforced by test:
```python
async def test_spawn_agent_does_not_block_event_loop(client):
    """bl/server.py spawn endpoint must not block for more than 50ms"""
    start = time.monotonic()
    resp = await client.post("/agent/spawn", json={"name": "test", "prompt": "echo hello"})
    elapsed = time.monotonic() - start
    assert resp.status_code == 200
    assert elapsed < 0.05  # asyncio.to_thread() wrapping verified
```

### Phase 4 — Integration & Polish

BrickLayer runs a full **Audit** campaign:
```bash
bl run --project codevvOS --mode audit --questions phase4-compliance.md
```

Audit questions cover:
- All Phase 0 security requirements still satisfied (regression check)
- RLS policies unchanged and correct
- All E2E tests passing
- Performance budgets not regressed
- No `docker.sock` mounts outside `sandbox-manager`

`NON_COMPLIANT` on any security question → no Phase 5 start.

### Phase 5 — ISO Build

ISO build runs in GitHub Actions, not local BrickLayer. BrickLayer generates the build specification:
```bash
bl run --project codevvOS --mode validate --questions iso-build.md
# Produces: build/iso-spec.md consumed by mkimage pipeline
```

CI job:
```yaml
  iso-build:
    runs-on: ubuntu-latest
    steps:
      - name: Build Alpine ISO
        run: |
          docker run --privileged alpinelinux/alpine-sdk:latest \
            sh -c "git clone https://gitlab.alpinelinux.org/alpine/aports.git && \
                   cp scripts/mkimg.codevv.sh aports/scripts/ && \
                   cd aports && sh scripts/mkimage.sh \
                     --profile codevv \
                     --outdir /output \
                     --arch x86_64"
      - name: Check ISO size
        run: |
          SIZE=$(du -sm output/*.iso | cut -f1)
          [ "$SIZE" -lt 500 ] || (echo "ISO too large: ${SIZE}MB" && exit 1)
      - name: Boot smoke test (QEMU)
        run: |
          qemu-system-x86_64 -m 2G -boot d -cdrom output/*.iso \
            -display none -serial stdio -no-reboot \
            -timeout 60 | grep "CodeVV OS ready"
```

### BrickLayer ↔ CodeVV Integration (Phase 3.5-BL)

Once `bl/server.py` is deployed as a Docker sidecar, BrickLayer orchestrates builds **from inside CodeVV**:

1. User approves spec in CodeVV UI (hard gate — see experience design)
2. CodeVV backend calls `POST http://bricklayer:8300/agent/spawn` with spec content
3. `bl/server.py` calls `asyncio.to_thread(spawn_agent, "rough-in", spec, cwd)` — non-blocking
4. Returns `{agent_id}` immediately to backend
5. Backend opens SSE stream: `GET http://bricklayer:8300/agent/{id}/stream`
6. Frontend AI Agent Mode panel subscribes to SSE → live log
7. Live diff panel receives file change events via existing `watchfiles` SSE channel
8. Any team member can `POST http://bricklayer:8300/agent/{id}/interrupt` → SIGINT
9. On completion: `git-nerd` commits → BrickLayer `masonry_checkpoint` records build state

**Authentication:** All `bricklayer:8300` calls from CodeVV backend must include `BL_INTERNAL_SECRET` header (Docker secret, not env var). Requests without this header return 403.

### Wave Simulation (Research & Pre-Build)

Before any Phase 3.5 feature that touches data modeling (Knowledge Graph, Recall schema, workspace templates), BrickLayer runs a simulation:

```bash
bl run --project codevvOS --mode simulate --questions data-model-sim.md
# Runner: simulate
# Produces: latency estimates, schema bottleneck identification
# Verdict: CALIBRATED → proceed; UNCALIBRATED → refine model first
```

---

## 8. Security Build Rules (Non-Negotiable)

These apply to every PR. CI `security` stage enforces them automatically; reviewers check manually.

1. **docker.sock** must appear ONLY in `sandbox-manager` via `tecnativa/docker-socket-proxy`. Semgrep rule: flag any `docker.sock` in non-sandbox-manager service definition.

2. **JWT validation** must use the shared `auth.js` / `auth.py` library. No service may implement its own JWT parse logic. Semgrep rule: flag `PyJWT.decode(` outside `auth.py`.

3. **Path traversal** — every file endpoint must depend on `verify_path_in_workspace`. `bandit` B101 + custom rule: flag `open(` or `os.path.join(` in route handlers that lack `verify_path_in_workspace` in the dependency chain.

4. **Claude API key** — `ANTHROPIC_API_KEY` must never appear in `docker-compose.yml` as plaintext. Must be a Docker secret reference. CI checks: `grep -r "ANTHROPIC_API_KEY" docker-compose.yml` must return empty.

5. **OAuth PKCE removal** — `claude_auth.py` OAuth authorize/token/refresh endpoints must not exist. If found by semgrep → CI failure.

6. **Postgres role** — All FastAPI database sessions must use `codevv_app` role. Migration test verifies `codevv_app` has `NOBYPASSRLS`. Integration test verifies cross-tenant RLS blocks.

7. **Artifact Panel** — `allow-same-origin` must never appear in any iframe sandbox attribute. Vitest unit test + semgrep rule both enforce this.

8. **Secrets in code** — `trufflehog filesystem . --fail` runs on every PR. Any detected secret = immediate CI failure. No exceptions, no ignore flags without Tim's approval.

---

## 9. Service-Level Health Check Requirements

Every Docker service must have a native HEALTHCHECK. No service is considered buildable without one.

```dockerfile
# backend/Dockerfile
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# ptyhost/Dockerfile
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1
```

`docker-compose.yml` must use `depends_on: condition: service_healthy` — `wait-for-healthy.sh` is removed in Phase 1a. CI `build-check` stage verifies all services reach `healthy` state within 90 seconds.

---

## 10. Code File Size Enforcement

All production code files (excluding tests) must stay under 400 lines. Hard limit: 600 lines.

CI check (runs in `fast-check`):
```bash
# Find files over 400 lines (warning)
find backend/app frontend/src -name "*.py" -o -name "*.ts" -o -name "*.tsx" | \
  xargs wc -l | sort -rn | awk '$1 > 400 && $2 != "total" {print "WARNING:", $0}'

# Find files over 600 lines (failure)
OVER=$(find backend/app frontend/src -name "*.py" -o -name "*.ts" -o -name "*.tsx" | \
  xargs wc -l | awk '$1 > 600 && $2 != "total" {print $0}')
if [ -n "$OVER" ]; then echo "FILES EXCEED 600 LINE LIMIT:"; echo "$OVER"; exit 1; fi
```

---

## Quick Reference

| What you want | Command |
|---------------|---------|
| Run all unit tests (backend) | `pytest tests/unit/ -x -q` |
| Run all unit tests (frontend) | `cd frontend && npx vitest run` |
| Run integration tests | `pytest tests/integration/ -x -q` |
| Run E2E tests | `npx playwright test` |
| Check coverage | `pytest --cov=app --cov-fail-under=80` |
| Lint backend | `ruff check backend/ && mypy backend/app --strict` |
| Lint frontend | `npx tsc --noEmit && npx eslint src/ --max-warnings=0` |
| New migration | `alembic revision --autogenerate -m "description"` |
| Apply migrations | `alembic upgrade head` |
| Rollback migration | `alembic downgrade -1` |
| Check image sizes | `docker images --format "{{.Repository}} {{.Size}}" \| grep codevv` |
| Start BrickLayer build | `bl run --project codevvOS --mode validate` (Phase 0) |
| Security scan | `bandit -r backend/app/ -ll && semgrep --config=p/fastapi backend/` |
| Bundle analysis | `cd frontend && npm run build && npx bundlesize` |

---

*This document is updated by the build team as decisions solidify. All changes require a PR. Tier 1 files (`project-brief.md`, `ARCHITECTURE.md`) take precedence over this document in case of conflict.*



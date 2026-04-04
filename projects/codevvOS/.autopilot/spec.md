# CodeVV OS — Build Spec (Phase 0 + Phase 1)

**Generated:** 2026-04-02
**Source authority:** `project-brief.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `BUILD_BIBLE.md`, `docs/design-system.md`, `docs/superpowers/specs/codevvos-experience-design.md`
**Scope:** Phase 0 (pre-build configuration) and Phase 1 (infrastructure + backend). No frontend. No Phase 2+.

---

## Project Summary

CodeVV OS is a boot-to-browser operating system experience built on CodeVV, a collaborative AI-assisted software design platform. It wraps CodeVV in a minimal Alpine Linux distribution that boots into a kiosk-mode Chromium browser, serving multiple users via a single Docker Compose deployment on a Proxmox Threadripper PRO server. The stack is React 19 + FastAPI + PostgreSQL 16 + Redis 7 + Yjs, with Claude AI (Console API key) and Recall (GPU VM) providing AI and semantic memory.

---

## How to Use This Spec

Each task below follows TDD (test-driven development). The build cycle for every task is:

1. **Read the task card** — understand what to build, acceptance criteria, and test contract.
2. **Write the failing test(s)** described in the test contract. Run the test. Verify it fails for the expected reason.
3. **Implement the minimum code** to make the test pass. No more.
4. **Run all tests** — the new test and all existing tests must pass.
5. **Verify acceptance criteria** — every checkbox must be satisfiable with evidence.
6. **Mark the task complete.**

Phase 0 tasks produce configuration files, not production code. Their "tests" are structural validations (file exists, config parses, lint passes). Phase 1 tasks produce production code with real unit/integration tests.

Dependencies between tasks are explicit. Do not start a task until all tasks listed in "Depends on" are complete.

---

## Phase 0 — Pre-Build Configuration

> No production code. These tasks produce project scaffolding, configuration files, Docker Compose definitions, CI pipelines, and design token setup. Phase 1 cannot start until all Phase 0 tasks pass.

---

### Task 0.1 — Monorepo Directory Structure

**Service/Target:** Repository root
**Depends on:** none

**What to build:**
Create the monorepo directory structure for CodeVV OS. This includes top-level directories for backend (Python/FastAPI), frontend (React/TypeScript), shared libraries, Docker configs, CI workflows, database migrations, and test directories. Create skeleton files (`pyproject.toml`, `package.json`, `.gitignore`, `requirements.txt`) so that linters and package managers can run against the empty project. Add a `Makefile` or `justfile` with common commands (lint, test, build).

**Acceptance criteria:**
- [ ] `backend/` directory exists with `app/` subdirectory, `__init__.py`, `pyproject.toml`, `requirements.txt`
- [ ] `frontend/` directory exists with `package.json`, `tsconfig.json`, `vite.config.ts` skeletons
- [ ] `shared/` directory exists with `auth.py` and `auth.js` placeholder files (shared JWT library — Phase 0a requirement)
- [ ] `migrations/` directory exists with Alembic `env.py` and `alembic.ini` skeleton
- [ ] `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/migrations/`, `tests/workers/` directories exist
- [ ] `.gitignore` covers Python (`__pycache__`, `.venv`, `*.pyc`), Node (`node_modules`, `dist`), Docker, IDE files, `.env`
- [ ] `docker/` directory exists for per-service Dockerfiles
- [ ] `.github/workflows/` directory exists (empty workflow files created in Task 0.7)

**Test contract:**
- Test file: `tests/unit/test_project_structure.py`
- Assertions: each required directory exists (`os.path.isdir`), each required skeleton file exists (`os.path.isfile`), `pyproject.toml` parses without error (`tomllib.loads`), `package.json` parses as valid JSON, `.gitignore` contains `node_modules` and `__pycache__`

---

### Task 0.2 — Security Decisions Codified as Configuration

**Service/Target:** `backend/app/core/security.py`, `shared/auth.py`, `shared/auth.js`
**Depends on:** 0.1

**What to build:**
Create the security configuration constants and stubs required by ROADMAP Phase 0a. This is not implementation — it is the configuration that Phase 1 will use. Specifically: (1) Create `backend/app/core/security.py` with constants for JWT algorithm pinning (`HS256`), brute force rate limit config (10 attempts/user/minute), and the `codevv_app` Postgres role name. (2) Create `shared/auth.py` with a stub `verify_jwt()` function that raises `NotImplementedError` (implementation is Phase 1). (3) Create `shared/auth.js` with a stub `verifyJwt()` function that throws. (4) Create `backend/app/dependencies/path_security.py` with a stub `verify_path_in_workspace()` FastAPI dependency.

**Acceptance criteria:**
- [ ] `backend/app/core/security.py` defines `JWT_ALGORITHM = "HS256"`, `RATE_LIMIT_LOGIN = "10/minute"`, `DB_APP_ROLE = "codevv_app"`
- [ ] `shared/auth.py` exports `verify_jwt(token: str) -> dict` that raises `NotImplementedError`
- [ ] `shared/auth.js` exports `verifyJwt(token)` that throws `Error("Not implemented")`
- [ ] `backend/app/dependencies/path_security.py` exports `verify_path_in_workspace(path: str, workspace_root: str) -> str` that raises `NotImplementedError`
- [ ] No hardcoded secrets anywhere in the codebase

**Test contract:**
- Test file: `tests/unit/test_security_config.py`
- Assertions: `JWT_ALGORITHM == "HS256"`, `DB_APP_ROLE == "codevv_app"`, calling `verify_jwt("any")` raises `NotImplementedError`, calling `verify_path_in_workspace("/etc/passwd", "/workspace")` raises `NotImplementedError`

---

### Task 0.3 — Docker Compose Scaffold (Baseline)

**Service/Target:** `docker-compose.yml`, `docker/` Dockerfiles
**Depends on:** 0.1, 0.2

**What to build:**
Author the baseline `docker-compose.yml` encoding all Phase 0 security and architecture decisions. This compose file defines all Phase 0/1 core services: `postgres`, `redis`, `backend`, `frontend`, `yjs`, `nginx`, `worker`. Services use `expose:` (Docker-internal) not `ports:` — only `nginx` exposes `:443`. Define two named networks: `frontend` (for nginx, frontend) and `backend` (for all internal services). Use Docker secrets for all passwords and keys (not environment variables). Add `depends_on: condition: service_healthy` stubs. Add `restart: unless-stopped` on all services. Add resource limits (memory + CPU) per service. Add log rotation (`max-size: 10m`, `max-file: 3`). Create stub Dockerfiles in `docker/` for each custom service (backend, frontend, yjs, worker). The compose file references `codevv_app` role in Postgres environment.

**Acceptance criteria:**
- [ ] `docker-compose.yml` exists and is valid YAML (parseable)
- [ ] Only `nginx` service uses `ports:` — all others use `expose:` only
- [ ] Two named networks defined: `frontend` and `backend`
- [ ] Docker secrets defined for: `jwt_secret`, `postgres_password`, `anthropic_api_key`, `recall_api_key`, `bl_internal_secret`
- [ ] `ANTHROPIC_API_KEY` does NOT appear as plaintext in the compose file
- [ ] All services have `restart: unless-stopped`
- [ ] All services have memory limits defined under `deploy.resources.limits`
- [ ] All services have logging config with `max-size` and `max-file`
- [ ] `postgres` service environment references `codevv_app` role
- [ ] `redis` service mounts a custom `redis.conf` with `appendonly yes`
- [ ] `worker` service uses same image as `backend` with different `command`
- [ ] `backend` service does NOT mount `docker.sock`
- [ ] `depends_on` with `condition: service_healthy` is used (not `wait-for-healthy.sh`)
- [ ] Stub Dockerfiles exist in `docker/` for: `backend`, `frontend`, `yjs`, `nginx`, `worker`

**Test contract:**
- Test file: `tests/unit/test_docker_compose.py`
- Parse `docker-compose.yml` with PyYAML. Assert: only `nginx` has `ports` key, all services have `restart` key, all services have `logging` key, secrets section exists with expected names, no service other than future `sandbox-manager` references `docker.sock`, `backend` networks include `backend`, `nginx` networks include `frontend`, `postgres` env references `codevv_app`

---

### Task 0.4 — Redis Configuration

**Service/Target:** `docker/redis/redis.conf`
**Depends on:** 0.1

**What to build:**
Create a Redis configuration file that enables AOF persistence (`appendonly yes`, `appendfsync everysec`) as required by ROADMAP 1e. Without AOF, all ARQ job queues and session data are lost on Redis restart. The compose file (Task 0.3) will bind-mount this file into the Redis container.

**Acceptance criteria:**
- [ ] `docker/redis/redis.conf` exists
- [ ] Contains `appendonly yes`
- [ ] Contains `appendfsync everysec`
- [ ] Contains `maxmemory-policy allkeys-lru` (sensible default)

**Test contract:**
- Test file: `tests/unit/test_redis_config.py`
- Read `docker/redis/redis.conf`, assert it contains the three required directives as substrings

---

### Task 0.5 — Tailwind v4 + Obsidian Shell Design Tokens

**Service/Target:** `frontend/src/styles/global.css`
**Depends on:** 0.1

**What to build:**
Create the Tailwind v4 CSS-first configuration with all Obsidian Shell design tokens from `docs/design-system.md`. This includes: `@import "tailwindcss"`, a `@layer base` block declaring all CSS custom properties (surfaces, borders, text tiers, accent system with workspace classes, semantic status colors, typography scale, spacing, border radius, elevation/shadow, motion tokens, terminal theme tokens, component tokens). Include light mode overrides under `.theme-light`. Include workspace accent classes (`.workspace-dev`, `.workspace-brainstorm`, `.workspace-review`, `.workspace-planning`, `.workspace-meeting`). Include the `@theme` block mapping CSS custom properties into Tailwind utility classes. Include base element resets (box-sizing, root height, scrollbar styling, selection color). Use the palette from `docs/design-system.md` section 2 (derived from five source colors: `#0D160B`, `#655560`, `#FCF7FF`, `#4F87B3`, `#ED474A`).

**Acceptance criteria:**
- [ ] `frontend/src/styles/global.css` exists
- [ ] Contains `@import "tailwindcss"`
- [ ] Contains `@layer base` with `:root` declaring all surface tokens (`--color-base` through `--color-surface-5`)
- [ ] Contains all border tokens (`--color-border-subtle` through `--color-border-strong`)
- [ ] Contains all text tier tokens (`--color-text-primary` through `--color-text-inverse`)
- [ ] Contains workspace accent classes for all five workspace types
- [ ] Contains semantic status colors (success, warning, error, info) with muted variants
- [ ] Contains severity tokens (`--color-severity-critical`, `--color-severity-high`, `--color-severity-medium`, `--color-severity-low`)
- [ ] Contains `.theme-light` override block
- [ ] Contains `@theme` block mapping tokens to Tailwind utilities
- [ ] Contains typography tokens (`--font-sans`, `--font-mono`, type scale `--text-xs` through `--text-4xl`)
- [ ] Contains spacing scale (`--space-0` through `--space-24`)
- [ ] Contains border radius tokens (`--radius-none` through `--radius-full`)
- [ ] Contains shadow/elevation tokens (`--shadow-0` through `--shadow-5`)
- [ ] Contains glass/blur variant tokens
- [ ] Contains motion tokens (durations and easing functions)
- [ ] Contains terminal theme tokens (`--terminal-background`, `--terminal-foreground`, etc.)
- [ ] Contains component tokens (panels, sidebar, dock bar, buttons, inputs, badges, toasts)
- [ ] Contains icon size tokens (`--icon-xs` through `--icon-3xl`) and stroke width tokens
- [ ] Contains base element resets (scrollbar, selection, box-sizing, root)
- [ ] No hardcoded hex values appear in any component file — only token references
- [ ] Default accent is `#4F87B3` (steel blue), not violet

**Test contract:**
- Test file: `tests/unit/test_design_tokens.py`
- Read `frontend/src/styles/global.css` as text. Assert it contains each required token name as a substring. Assert it contains `@import "tailwindcss"`. Assert `.workspace-dev` and `.workspace-meeting` classes are defined. Assert `#4F87B3` appears as the default accent. Assert `@theme` block exists.

---

### Task 0.6 — Self-Hosted Fonts

**Service/Target:** `frontend/public/fonts/`
**Depends on:** 0.1

**What to build:**
Download and self-host Inter (weights 400, 500, 600) and JetBrains Mono (weights 400, 500) in `frontend/public/fonts/`. Create `@font-face` declarations in a dedicated `frontend/src/styles/fonts.css` file. The LAN kiosk has no Google Fonts CDN access, so fonts must be served locally. Import `fonts.css` from `global.css`. Do NOT use Google Fonts `@import url()` directives.

**Acceptance criteria:**
- [ ] `frontend/public/fonts/` contains Inter woff2 files for weights 400, 500, 600
- [ ] `frontend/public/fonts/` contains JetBrains Mono woff2 files for weights 400, 500
- [ ] `frontend/src/styles/fonts.css` exists with `@font-face` declarations for each font/weight
- [ ] `global.css` imports `fonts.css` (or `fonts.css` is imported at the app entry point)
- [ ] No `@import url('https://fonts.googleapis.com/...')` exists anywhere in the frontend

**Test contract:**
- Test file: `tests/unit/test_fonts.py`
- Assert font files exist on disk. Assert `fonts.css` contains `@font-face` for `Inter` and `JetBrains Mono`. Grep the entire `frontend/src/` directory for `fonts.googleapis.com` — must return zero matches.

---

### Task 0.7 — CI/CD Pipeline Configuration

**Service/Target:** `.github/workflows/`
**Depends on:** 0.1, 0.3

**What to build:**
Create the three CI workflow files specified in BUILD_BIBLE.md section 4: (1) `fast-check.yml` — runs on every push to `feat/*` and `fix/*` branches; jobs: lint-backend (ruff + mypy), lint-frontend (tsc + eslint), unit-backend (pytest), unit-frontend (vitest). (2) `integration.yml` — runs on PRs to `dev` and `main`; uses postgres and redis service containers; runs integration tests + migration tests. (3) `build-check.yml` — runs on PRs to `dev` and `main`; builds all Docker images, verifies healthchecks, checks image sizes against BUILD_BIBLE budgets. Also add the `security` stage from BUILD_BIBLE (bandit + semgrep + pip-audit + trufflehog + npm audit). Add file size enforcement check (400 line warning, 600 line hard fail) in `fast-check.yml`.

**Acceptance criteria:**
- [ ] `.github/workflows/fast-check.yml` exists with lint + unit test jobs
- [ ] `.github/workflows/integration.yml` exists with postgres + redis service containers
- [ ] `.github/workflows/build-check.yml` exists with Docker build + healthcheck + size check
- [ ] Security stage is defined (bandit, semgrep, pip-audit, trufflehog, npm audit)
- [ ] File size enforcement (600 line hard limit) is in `fast-check.yml`
- [ ] `fast-check.yml` triggers on push to `feat/**` and `fix/**`
- [ ] `integration.yml` and `build-check.yml` trigger on PRs to `dev` and `main`
- [ ] All workflow files are valid YAML

**Test contract:**
- Test file: `tests/unit/test_ci_config.py`
- Parse each workflow YAML with PyYAML. Assert `fast-check.yml` has `on.push.branches` containing `feat/**`. Assert `integration.yml` has service definitions for postgres and redis. Assert `build-check.yml` references `docker compose build`. Assert security jobs reference `bandit` and `trufflehog`.

---

### Task 0.8 — Python Linting + Formatting Configuration

**Service/Target:** `backend/pyproject.toml`, `ruff.toml`
**Depends on:** 0.1

**What to build:**
Configure Ruff as the Python linter and formatter. Add Ruff configuration to `pyproject.toml` (or a top-level `ruff.toml`) with rules appropriate for a FastAPI project (enable `E`, `F`, `W`, `I` (isort), `UP` (pyupgrade), `B` (flake8-bugbear), `S` (bandit), `ASYNC` rules). Configure `mypy` for strict mode in `pyproject.toml`. Set Python target to 3.12. Configure line length to 100.

**Acceptance criteria:**
- [ ] Ruff configuration exists in `pyproject.toml` or `ruff.toml`
- [ ] Rules enabled: `E`, `F`, `W`, `I`, `UP`, `B`, `S`, `ASYNC`
- [ ] Line length set to 100
- [ ] Python target version is 3.12
- [ ] `mypy` section in `pyproject.toml` with `strict = true`
- [ ] Running `ruff check backend/` on the skeleton files produces zero errors
- [ ] Running `mypy backend/app` on the skeleton files produces zero errors (or only expected stub errors)

**Test contract:**
- Test file: `tests/unit/test_lint_config.py`
- Parse `pyproject.toml` with `tomllib`. Assert `[tool.ruff]` or `[tool.ruff.lint]` section exists. Assert `line-length` is 100. Assert `target-version` is `"py312"`. Assert `[tool.mypy]` section exists with `strict = true`.

---

### Task 0.9 — Frontend Linting + Formatting Configuration

**Service/Target:** `frontend/eslint.config.js`, `frontend/.prettierrc`
**Depends on:** 0.1

**What to build:**
Configure ESLint (flat config format) and Prettier for the React 19 + TypeScript frontend. ESLint rules should include `@typescript-eslint/recommended`, `react-hooks`, and `react/recommended`. Prettier config: single quotes, no semicolons (or semi — match the CodeVV upstream convention), 100 print width. Add `frontend/tsconfig.json` with strict mode enabled, React JSX transform, path aliases. Ensure `npx eslint --max-warnings=0` and `npx tsc --noEmit` pass on the empty project.

**Acceptance criteria:**
- [ ] `frontend/eslint.config.js` exists (ESLint flat config)
- [ ] `frontend/.prettierrc` exists
- [ ] `frontend/tsconfig.json` exists with `strict: true` and `jsx: "react-jsx"`
- [ ] ESLint config includes TypeScript and React rules
- [ ] Running `npx eslint src/ --max-warnings=0` on the empty project produces zero warnings
- [ ] Running `npx tsc --noEmit` on the empty project produces zero errors

**Test contract:**
- Test file: `tests/unit/test_frontend_lint_config.py`
- Assert `eslint.config.js` exists. Assert `tsconfig.json` parses as valid JSON with `strict: true`. Assert `.prettierrc` exists and parses.

---

### Task 0.10 — Test Framework Setup (Backend)

**Service/Target:** `backend/conftest.py`, `tests/conftest.py`
**Depends on:** 0.1, 0.8

**What to build:**
Set up pytest with `pytest-asyncio`, `pytest-cov`, and `httpx.AsyncClient` for FastAPI testing as specified in BUILD_BIBLE section 3a. Create a root `conftest.py` with shared fixtures: `jwt_token` factory (returns a test JWT signed with a test secret), `client` fixture (httpx.AsyncClient against the FastAPI app), `tmp_workspace` fixture (creates a temp directory for file operation tests). Add `pytest.ini` or `pyproject.toml` pytest section with `asyncio_mode = "auto"`, `timeout = 30` default. Add `requirements-test.txt` with all test dependencies.

**Acceptance criteria:**
- [ ] `tests/conftest.py` exists with `client`, `jwt_token`, and `tmp_workspace` fixtures
- [ ] `pyproject.toml` or `pytest.ini` configures `asyncio_mode = "auto"` and default timeout
- [ ] `requirements-test.txt` lists: pytest, pytest-asyncio, pytest-cov, httpx, pytest-timeout
- [ ] Running `pytest --co` (collect only) succeeds with zero errors
- [ ] Coverage is configured with minimum 80% threshold

**Test contract:**
- Test file: `tests/unit/test_conftest_fixtures.py`
- Write a test that imports the `jwt_token` fixture and asserts it returns a non-empty string. Write a test that imports the `tmp_workspace` fixture and asserts it returns a `Path` to an existing directory. Run `pytest tests/unit/test_conftest_fixtures.py` — must pass.

---

### Task 0.11 — Test Framework Setup (Frontend)

**Service/Target:** `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`
**Depends on:** 0.1, 0.9

**What to build:**
Set up Vitest with `@testing-library/react`, `@testing-library/user-event`, and `msw` v2 as specified in BUILD_BIBLE section 3b. Create `vitest.config.ts` with jsdom environment, coverage thresholds (75% line minimum), and path aliases matching `tsconfig.json`. Create `frontend/src/test/setup.ts` with MSW server setup (start before all, reset after each, close after all). Add test dependencies to `package.json`.

**Acceptance criteria:**
- [ ] `frontend/vitest.config.ts` exists with jsdom environment
- [ ] Coverage thresholds configured at 75% lines
- [ ] `frontend/src/test/setup.ts` exists with MSW server lifecycle
- [ ] `package.json` devDependencies include: vitest, @testing-library/react, @testing-library/user-event, msw, @vitest/coverage-v8
- [ ] Running `npx vitest run` succeeds (even with zero test files — no config errors)

**Test contract:**
- Test file: `frontend/src/test/vitest-setup.test.ts`
- Write a test that asserts `import.meta.env` exists (proves Vitest is configured). Run `npx vitest run` — must pass.

---

### Task 0.12 — Alembic Migration Scaffold

**Service/Target:** `migrations/`, `alembic.ini`
**Depends on:** 0.1, 0.10

**What to build:**
Initialize Alembic for async SQLAlchemy (asyncpg driver). Configure `alembic.ini` to read the database URL from the `DATABASE_URL` environment variable. Create `migrations/env.py` configured for async operations with `run_async_migrations()`. Ensure `alembic upgrade head` and `alembic downgrade -1` both run without error on an empty migration set. The `env.py` must import the SQLAlchemy `Base` metadata from the backend models module (create a stub `backend/app/models/base.py` with `Base = declarative_base()`).

**Acceptance criteria:**
- [ ] `alembic.ini` exists, references `migrations/` directory
- [ ] `alembic.ini` reads `DATABASE_URL` from env (not hardcoded connection string)
- [ ] `migrations/env.py` exists, configured for async with asyncpg
- [ ] `backend/app/models/base.py` exists with `Base = declarative_base()`
- [ ] `alembic check` or `alembic heads` runs without error

**Test contract:**
- Test file: `tests/unit/test_alembic_config.py`
- Parse `alembic.ini` and assert `script_location = migrations`. Import `migrations.env` and assert it defines `run_migrations_online`. Import `backend.app.models.base` and assert `Base` has a `metadata` attribute.

---

### Task 0.13 — Known Time Bombs Documentation

**Service/Target:** `docker/bricklayer/entrypoint.sh` (stub), documentation in compose
**Depends on:** 0.3

**What to build:**
Address the ROADMAP 0d "Known Time Bombs" as configuration. Create a stub `docker/bricklayer/entrypoint.sh` that starts tmux before uvicorn (`tmux new-session -d -s main && exec uvicorn...`). Add comments in `docker-compose.yml` at each relevant service referencing the time bomb and its mitigation. Specifically: (1) bricklayer entrypoint must start tmux first, (2) sandbox-manager must use aiodocker (not docker-py), (3) livekit-agents must use `python:3.12-slim-bookworm` not Alpine, (4) yjs/tldraw-sync must use `node:22-alpine`, (5) dockview layout must include version field from day one.

**Acceptance criteria:**
- [ ] `docker/bricklayer/entrypoint.sh` exists with tmux start before uvicorn
- [ ] Compose file has comments noting each time bomb mitigation at the relevant service
- [ ] `livekit-agents` service in compose specifies `python:3.12-slim-bookworm` base (not Alpine)
- [ ] `yjs` and `tldraw-sync` services specify `node:22-alpine` base

**Test contract:**
- Test file: `tests/unit/test_time_bombs.py`
- Read `docker/bricklayer/entrypoint.sh` and assert it contains `tmux new-session`. Parse `docker-compose.yml` and assert `livekit-agents` image reference does not contain `alpine`. Assert `yjs` image reference contains `node:22-alpine` or references a Dockerfile that uses it.

---

## Phase 1 — Infrastructure & Backend

> Production code. Each task follows strict TDD: write failing test, implement, pass test. No frontend tasks. All tasks build on the Phase 0 scaffold.

---

### Task 1.1 — Docker Compose Healthchecks

**Service/Target:** `docker-compose.yml`, service Dockerfiles
**Depends on:** 0.3

**What to build:**
Add native Docker HEALTHCHECK directives to every service Dockerfile and verify they work in the compose file. Postgres: `pg_isready -U postgres`. Redis: `redis-cli ping`. Backend: `curl -f http://localhost:8000/health`. Yjs: `curl -f http://localhost:1234/health`. Nginx: `curl -f -k https://localhost/health`. Worker: same as backend health endpoint. Remove any `wait-for-healthy.sh` scripts. Ensure `depends_on: condition: service_healthy` is used for service ordering.

**Acceptance criteria:**
- [ ] Every service Dockerfile has a `HEALTHCHECK` instruction
- [ ] `docker-compose.yml` uses `depends_on: condition: service_healthy` (not scripts)
- [ ] No `wait-for-healthy.sh` file exists in the repository
- [ ] `backend` has a `GET /health` endpoint returning 200
- [ ] `yjs` has a `GET /health` endpoint returning 200
- [ ] All services reach `healthy` state within 90 seconds after `docker compose up`

**Test contract:**
- Test file: `tests/unit/test_healthchecks.py`
- Parse each Dockerfile in `docker/` and assert it contains `HEALTHCHECK`. Parse `docker-compose.yml` and assert no service references `wait-for-healthy.sh`. Assert `backend` service has `depends_on` with `condition: service_healthy` for postgres and redis.
- Integration test: `tests/integration/test_compose_health.py` — run `docker compose up -d`, wait 90s, assert all services show `healthy` in `docker compose ps`.

---

### Task 1.2 — Docker Network Isolation

**Service/Target:** `docker-compose.yml`
**Depends on:** 0.3, 1.1

**What to build:**
Enforce Docker network isolation with two named networks: `frontend` (nginx, frontend) and `backend` (all internal services). Nginx bridges both networks. No internal service is reachable from outside the Docker network. Add log rotation (`max-size: 10m`, `max-file: 3`) to every service. Add resource limits per service (memory caps based on BUILD_BIBLE section 5 image size budgets as a rough guide).

**Acceptance criteria:**
- [ ] `frontend` network defined, used by `nginx` and `frontend` services
- [ ] `backend` network defined, used by `postgres`, `redis`, `backend`, `yjs`, `worker`
- [ ] `nginx` is on both `frontend` and `backend` networks
- [ ] No internal service (`postgres`, `redis`, `yjs`, `backend`, `worker`) is on the `frontend` network
- [ ] Every service has `logging` config with `max-size: 10m` and `max-file: "3"`
- [ ] Every service has `deploy.resources.limits.memory` defined

**Test contract:**
- Test file: `tests/unit/test_network_isolation.py`
- Parse `docker-compose.yml`. Assert `postgres` networks list does not contain `frontend`. Assert `nginx` networks list contains both `frontend` and `backend`. Assert every service has a `logging` key. Assert every service has `deploy.resources.limits.memory`.

---

### Task 1.3 — Docker Secrets Configuration

**Service/Target:** `docker-compose.yml`, `docker/secrets/`
**Depends on:** 0.3, 1.2

**What to build:**
Replace all sensitive environment variables with Docker file-based secrets. Create placeholder secret files in `docker/secrets/` (gitignored). Configure services to read secrets from `/run/secrets/`. The backend must use `pydantic-settings` with `SecretsSettingsSource` to read from `/run/secrets/` with env var fallback. Create a `backend/app/core/config.py` using `pydantic-settings.BaseSettings` that reads: `jwt_secret`, `postgres_password`, `anthropic_api_key`, `recall_api_key`, `bl_internal_secret`.

**Acceptance criteria:**
- [ ] `docker/secrets/` directory exists and is in `.gitignore`
- [ ] Placeholder files exist for each secret: `jwt_secret`, `postgres_password`, `anthropic_api_key`, `recall_api_key`, `bl_internal_secret`
- [ ] `docker-compose.yml` `secrets` section defines all secrets with `file:` references
- [ ] Services that need secrets have `secrets:` arrays
- [ ] `backend/app/core/config.py` uses `BaseSettings` with `SecretsSettingsSource`
- [ ] `pydantic-settings` is in `requirements.txt`
- [ ] No plaintext `ANTHROPIC_API_KEY` value in `docker-compose.yml`

**Test contract:**
- Test file: `tests/unit/test_secrets_config.py`
- Import `backend.app.core.config.Settings`. Assert it has fields: `jwt_secret`, `postgres_password`, `anthropic_api_key`, `recall_api_key`, `bl_internal_secret`. Assert `Settings` uses `SecretsSettingsSource` (check `model_config`). Grep `docker-compose.yml` for the literal string `ANTHROPIC_API_KEY=` — must not be found (env var assignment with a value).

---

### Task 1.4 — PostgreSQL Multi-Tenant Schema (Core Tables)

**Service/Target:** `migrations/versions/001_core_tables.py`, `backend/app/models/`
**Depends on:** 0.12, 1.3

**What to build:**
Create the first Alembic migration with core tables as specified in ROADMAP 1e: `tenants`, `users`, `projects`, `workspace_templates`, `activity_events`, `agent_runs`. Create the `codevv_app` role with `NOLOGIN NOBYPASSRLS NOINHERIT`. Enable RLS on all tables. Create RLS policies that restrict queries to the current tenant (via `current_setting('app.current_tenant_id')`). Create composite indexes on `(tenant_id, id)` and `(tenant_id, created_at DESC)` for all tenant-scoped tables. Create corresponding SQLAlchemy models in `backend/app/models/`. Remove pgvector extension if present. The migration must have a working `downgrade()` function — no `pass`.

**Acceptance criteria:**
- [ ] Migration `001_core_tables.py` exists in `migrations/versions/`
- [ ] Tables created: `tenants`, `users`, `projects`, `workspace_templates`, `activity_events`, `agent_runs`
- [ ] `codevv_app` role created with `NOLOGIN NOBYPASSRLS NOINHERIT`
- [ ] RLS enabled on all six tables
- [ ] RLS policies use `current_setting('app.current_tenant_id')` for tenant filtering
- [ ] Composite indexes exist: `(tenant_id, id)` on all tenant-scoped tables
- [ ] Composite indexes exist: `(tenant_id, created_at DESC)` on tables with `created_at`
- [ ] `downgrade()` drops all tables, policies, indexes, and the role (no `pass`)
- [ ] SQLAlchemy models exist in `backend/app/models/` for each table
- [ ] `users` model has `role` field (member/admin)
- [ ] No pgvector references anywhere

**Test contract:**
- Test file: `tests/migrations/test_001_core_tables.py`
- Run migration against a real test Postgres. Assert all six tables exist. Assert `codevv_app` role has `NOBYPASSRLS` (`SELECT rolbypassrls FROM pg_roles WHERE rolname = 'codevv_app'` returns False). Assert composite indexes exist. Assert RLS is enabled (`SELECT relrowsecurity FROM pg_class WHERE relname = 'projects'` returns True). Run downgrade and assert tables are dropped.
- Test file: `tests/integration/test_rls_isolation.py`
- Create two tenants. Insert a project for tenant A. Query as tenant B using `SET app.current_tenant_id`. Assert tenant B cannot see tenant A's project.

---

### Task 1.5 — SQLAlchemy Async Session with SET ROLE

**Service/Target:** `backend/app/db/session.py`
**Depends on:** 1.4

**What to build:**
Create the async SQLAlchemy session factory as specified in ROADMAP 0a and 1d. The factory must: (1) use asyncpg driver, (2) set `expire_on_commit=False` on all sessions to prevent `MissingGreenlet` errors, (3) execute `SET ROLE codevv_app` on every new connection via `@event.listens_for(engine, "connect")` hook, (4) set `app.current_tenant_id` per request via a middleware or dependency. Create a FastAPI dependency `get_db()` that yields the session.

**Acceptance criteria:**
- [ ] `backend/app/db/session.py` exports `get_db()` async generator
- [ ] `expire_on_commit=False` is set on the session factory
- [ ] `SET ROLE codevv_app` is executed on every connection via event listener
- [ ] `app.current_tenant_id` is set per-request (via dependency or middleware)
- [ ] Connection string reads from `Settings.postgres_password` (Docker secret)

**Test contract:**
- Test file: `tests/integration/test_db_session.py`
- Get a session via `get_db()`. Execute `SELECT current_setting('role')` and assert it returns `codevv_app`. Execute `SHOW role` and verify. Assert `session.expire_on_commit` is `False`.

---

### Task 1.6 — Shared JWT Auth Library (Python)

**Service/Target:** `shared/auth.py`
**Depends on:** 0.2, 1.3

**What to build:**
Implement the shared JWT auth library for Python services as specified in ROADMAP 0a. Replace the stub from Task 0.2 with a real implementation. Functions: `create_jwt(user_id, tenant_id, role, expires_delta)` and `verify_jwt(token) -> dict`. Pin algorithm to `HS256` — explicitly pass `algorithms=["HS256"]` to `jwt.decode()`. Reject tokens with `alg: none`. Read the JWT secret from Docker secrets (`/run/secrets/jwt_secret`) with env var fallback. Include a `require_role(role)` FastAPI dependency factory.

**Acceptance criteria:**
- [ ] `shared/auth.py` exports `create_jwt()`, `verify_jwt()`, `require_role()`
- [ ] `jwt.decode()` is called with `algorithms=["HS256"]` — never without
- [ ] Tokens with `alg: none` are rejected (raises exception)
- [ ] `verify_jwt()` returns dict with `user_id`, `tenant_id`, `role`, `exp`
- [ ] `require_role("admin")` returns a FastAPI dependency that raises 403 for non-admin users
- [ ] Secret is read from `/run/secrets/jwt_secret` with env var fallback

**Test contract:**
- Test file: `tests/unit/test_jwt_auth.py`
- Create a JWT, verify it, assert payload matches. Create a JWT with wrong secret, verify fails. Create a token with `alg: none` header, verify raises. Test `require_role("admin")` rejects a `member` role token (raises HTTPException 403). Test expired token is rejected.

---

### Task 1.7 — Shared JWT Auth Library (Node.js)

**Service/Target:** `shared/auth.js`
**Depends on:** 0.2, 1.3

**What to build:**
Implement the shared JWT auth library for Node.js services (ptyHost, Yjs server, tldraw-sync) as specified in ROADMAP 0a. Replace the stub from Task 0.2. Functions: `createJwt(userId, tenantId, role, expiresIn)` and `verifyJwt(token) -> payload`. Pin algorithm to `HS256`. Read secret from `/run/secrets/jwt_secret` with env var fallback. Include WebSocket auth middleware: validate JWT from first message (not query params — they appear in logs). Include a 60-second expiry re-check timer for long-lived WebSocket connections.

**Acceptance criteria:**
- [ ] `shared/auth.js` exports `createJwt()`, `verifyJwt()`, `wsAuthMiddleware()`
- [ ] Algorithm pinned to `HS256` in verify call
- [ ] `alg: none` tokens rejected
- [ ] WebSocket middleware validates JWT from first message payload, not query params
- [ ] 60-second re-check timer terminates connection if JWT has expired
- [ ] Secret read from `/run/secrets/jwt_secret` with `process.env.JWT_SECRET` fallback

**Test contract:**
- Test file: `shared/auth.test.js` (Jest)
- Create and verify JWT round-trip. Verify wrong-secret token fails. Verify `alg: none` token fails. Test WebSocket middleware rejects connection without valid JWT in first message. Test 60-second timer closes connection with expired JWT (use fake timers).

---

### Task 1.8 — Path Traversal Security Dependency

**Service/Target:** `backend/app/dependencies/path_security.py`
**Depends on:** 0.2

**What to build:**
Implement the `verify_path_in_workspace()` FastAPI dependency as specified in ROADMAP 0a. Replace the stub from Task 0.2. The function takes a `path` parameter and a `workspace_root`, resolves both with `os.path.realpath()`, and asserts the resolved path starts with the resolved workspace root. Raise `HTTPException(400)` on path traversal attempt. This dependency must be applied to ALL file endpoints (enforced by convention and code review — Task 1.11 will use it).

**Acceptance criteria:**
- [ ] `verify_path_in_workspace(path, workspace_root)` resolves both paths with `os.path.realpath()`
- [ ] Returns the resolved path on success
- [ ] Raises `HTTPException(400)` when resolved path escapes workspace root
- [ ] Handles symlink attacks (realpath resolves symlinks before comparison)
- [ ] Handles `..`, `./`, and URL-encoded traversal attempts

**Test contract:**
- Test file: `tests/unit/test_path_security.py`
- Valid path within workspace returns resolved path. Path with `../../etc/passwd` raises HTTPException 400. Symlink pointing outside workspace raises HTTPException 400. URL-encoded `%2e%2e%2f` raises HTTPException 400. Null bytes in path raise HTTPException 400.

---

### Task 1.9 — Login Endpoint with Rate Limiting

**Service/Target:** `backend/app/api/auth.py`
**Depends on:** 1.4, 1.5, 1.6

**What to build:**
Implement `POST /auth/login` as specified in ROADMAP 0a and the existing CodeVV auth pattern. Accept `email` and `password`. Validate against the `users` table (password hashed with bcrypt). Return a JWT on success. Apply `slowapi` rate limiting: 10 attempts per user (by email) per minute, returning 429 on excess. Add `POST /auth/logout` (invalidate session — token added to Redis blacklist with TTL matching token expiry).

**Acceptance criteria:**
- [ ] `POST /auth/login` accepts `{email, password}`, returns `{token, user}` on success
- [ ] Passwords stored as bcrypt hashes (never plaintext)
- [ ] Returns 401 on invalid credentials
- [ ] Returns 429 after 10 failed attempts from the same email within 1 minute
- [ ] Different users are rate-limited independently
- [ ] `POST /auth/logout` adds the token to Redis blacklist
- [ ] `verify_jwt()` checks Redis blacklist before accepting a token

**Test contract:**
- Test file: `tests/unit/test_auth_api.py`
- Test successful login returns 200 + JWT. Test wrong password returns 401. Test 11 rapid failed logins returns 429 on the 11th. Test different user is not rate limited by first user's attempts. Test logout invalidates the token (subsequent use returns 401).
- Integration test: `tests/integration/test_auth_flow.py`
- Against real DB + Redis: create user, login, use token for authenticated request, logout, use token again (should fail).

---

### Task 1.10 — Backend Health Endpoint

**Service/Target:** `backend/app/api/health.py`
**Depends on:** 1.5

**What to build:**
Create a `GET /health` endpoint for the backend service. It must check: (1) PostgreSQL is reachable (execute `SELECT 1`), (2) Redis is reachable (`PING`). Return 200 with `{"status": "healthy", "postgres": true, "redis": true}` when all checks pass. Return 503 with the failing component when any check fails. This endpoint is unauthenticated (healthchecks run before any user logs in).

**Acceptance criteria:**
- [ ] `GET /health` returns 200 when postgres and redis are reachable
- [ ] `GET /health` returns 503 with failure details when a dependency is down
- [ ] Endpoint is unauthenticated (no JWT required)
- [ ] Response includes individual component status

**Test contract:**
- Test file: `tests/unit/test_health.py`
- Mock postgres as reachable, mock redis as reachable: assert 200. Mock postgres as unreachable: assert 503 with `"postgres": false`. Mock redis as unreachable: assert 503 with `"redis": false`.
- Integration test: `tests/integration/test_health.py`
- Against real DB + Redis: hit `/health`, assert 200.

---

### Task 1.11 — File Tree API Endpoint

**Service/Target:** `backend/app/api/files.py`
**Depends on:** 1.5, 1.6, 1.8

**What to build:**
Implement `GET /api/files/tree?path=` as specified in ROADMAP 1d. Returns a lazy-loaded directory listing (one level deep). Requires JWT authentication. Uses `verify_path_in_workspace` dependency for path traversal protection. Response schema: `{name, type ("file"|"dir"), size, modified, children: [...]}` where children is only populated for the requested directory (not recursive). Exclude `.git/` from results.

**Acceptance criteria:**
- [ ] `GET /api/files/tree?path=<dir>` returns directory listing
- [ ] Response includes `name`, `type`, `size`, `modified` for each entry
- [ ] Only one level deep (lazy-load, not recursive)
- [ ] `.git/` directory excluded from results
- [ ] Path traversal attempts return 400 (via `verify_path_in_workspace`)
- [ ] Unauthenticated requests return 401
- [ ] Non-existent path returns 404

**Test contract:**
- Test file: `tests/unit/test_files_api.py`
- Create a temp workspace with known files/dirs. Request tree: assert correct entries returned. Request with `../../etc/passwd`: assert 400. Request without JWT: assert 401. Request non-existent path: assert 404. Assert `.git/` is excluded when present in temp workspace.

---

### Task 1.12 — File Operations API Endpoint

**Service/Target:** `backend/app/api/files.py`
**Depends on:** 1.11

**What to build:**
Implement `PATCH /api/files/{path:path}` as specified in ROADMAP 1d. Supports operations: `read` (return file content), `write` (update file content), `rename`, `delete`, `create_dir`. Uses `{path:path}` parameter type for slash-containing paths. All operations scoped to user workspace via `verify_path_in_workspace`.

**Acceptance criteria:**
- [ ] `PATCH /api/files/{path:path}` with `{"action": "read"}` returns file content
- [ ] `PATCH /api/files/{path:path}` with `{"action": "write", "content": "..."}` updates file
- [ ] `PATCH /api/files/{path:path}` with `{"action": "rename", "new_name": "..."}` renames
- [ ] `PATCH /api/files/{path:path}` with `{"action": "delete"}` deletes file/dir
- [ ] `PATCH /api/files/{path:path}` with `{"action": "create_dir"}` creates directory
- [ ] All operations validate path via `verify_path_in_workspace`
- [ ] Requires JWT authentication
- [ ] Returns appropriate error codes (404 for missing, 400 for bad action)

**Test contract:**
- Test file: `tests/unit/test_file_operations.py`
- Create file, read it back: content matches. Write to file, read: updated content. Rename file: old path 404, new path 200. Delete file: subsequent read 404. Create dir: directory exists. Path traversal in any operation: 400.

---

### Task 1.13 — File Watch SSE Endpoint

**Service/Target:** `backend/app/api/files.py`
**Depends on:** 1.11

**What to build:**
Implement file watch via `watchfiles` (Rust-backed) pushing changes over SSE as specified in ROADMAP 1d. Endpoint: `GET /api/files/watch?path=<dir>`. Uses async generator for fan-out — one watcher per directory, not per connection (prevents inotify exhaustion). SSE events: `{"type": "change"|"create"|"delete", "path": "relative/path"}`. Exclude `.git/` from watching. Debounce events 100-300ms.

**Acceptance criteria:**
- [ ] `GET /api/files/watch?path=<dir>` returns SSE stream
- [ ] File creation emits `create` event within 500ms
- [ ] File modification emits `change` event within 500ms
- [ ] File deletion emits `delete` event within 500ms
- [ ] `.git/` changes are excluded
- [ ] Multiple SSE connections to the same directory share one watcher (no inotify exhaustion)
- [ ] Events are debounced (100-300ms)
- [ ] Requires JWT authentication

**Test contract:**
- Test file: `tests/integration/test_file_watch.py`
- Open SSE stream, modify a file in the watched directory, assert a `change` event is received within 500ms. Create a file, assert `create` event. Delete a file, assert `delete` event. Modify a file inside `.git/`, assert no event is emitted.

---

### Task 1.14 — Settings Schema API Endpoint

**Service/Target:** `backend/app/api/settings.py`, `backend/app/core/settings_schema.py`
**Depends on:** 1.5, 1.6

**What to build:**
Implement `GET /api/settings/schema` as specified in ROADMAP 0b and 1d. Create a Pydantic v2 model for user settings (`UserSettings`) and system settings (`SystemSettings`). The endpoint returns JSON Schema generated from these models, post-processed to JSON Schema draft 7 via a `to_draft7()` utility function (converts `$defs` to `definitions`, rewrites `$ref` paths, flattens `Optional` `anyOf`). Also implement `GET/PUT /api/settings/user` (per-user CRUD) and `GET/PUT /api/admin/settings` (admin-only with `require_role("admin")`).

**Acceptance criteria:**
- [ ] `GET /api/settings/schema` returns valid JSON Schema (draft 7 compatible)
- [ ] Schema uses `definitions` not `$defs` (draft 7)
- [ ] `$ref` paths are rewritten from `$defs` to `definitions`
- [ ] `Optional` fields are flattened (no `anyOf` with null)
- [ ] `GET /api/settings/user` returns current user settings
- [ ] `PUT /api/settings/user` updates current user settings
- [ ] `GET /api/admin/settings` requires admin role (returns 403 for members)
- [ ] `PUT /api/admin/settings` requires admin role

**Test contract:**
- Test file: `tests/unit/test_settings_api.py`
- Request schema: assert it parses as valid JSON Schema, assert `definitions` key exists (not `$defs`), assert no `anyOf` with `null` type. Test user settings CRUD: put then get returns updated values. Test admin settings with member token: assert 403. Test admin settings with admin token: assert 200.

---

### Task 1.15 — Notification API Endpoints

**Service/Target:** `backend/app/api/notifications.py`
**Depends on:** 1.5, 1.6

**What to build:**
Implement notification endpoints as specified in ROADMAP 1d: `GET /api/notifications?limit=50&before_id=` (cursor-paginated notification history) and `PATCH /api/notifications/{id}/read` (mark notification as read). Notifications are stored in PostgreSQL. Add a `notifications` table to a new migration. The table is tenant-scoped with RLS.

**Acceptance criteria:**
- [ ] `notifications` table exists with: `id`, `tenant_id`, `user_id`, `type`, `title`, `body`, `read`, `created_at`
- [ ] RLS enabled on `notifications` table
- [ ] `GET /api/notifications` returns paginated list, default limit 50
- [ ] Cursor pagination via `before_id` parameter (not offset)
- [ ] `PATCH /api/notifications/{id}/read` marks notification as read
- [ ] Users can only see their own notifications (RLS enforced)
- [ ] Requires JWT authentication

**Test contract:**
- Test file: `tests/unit/test_notifications_api.py`
- Create 60 notifications for a user. Request with default limit: assert 50 returned. Request with `before_id` of the 50th: assert next 10 returned. Mark one read: assert `read: true` on subsequent fetch. Test cross-user: user B cannot see user A's notifications.

---

### Task 1.16 — Rate Limiting on AI Endpoints

**Service/Target:** `backend/app/api/ai.py`
**Depends on:** 1.6, 1.9

**What to build:**
Apply `slowapi` rate limiting to all `/api/ai` and assistant endpoints as specified in ROADMAP 1d. Per-user limits to prevent trigger automation from exhausting the org API key. Default limit: 30 requests per user per minute for `/api/ai` endpoints. This is separate from the `/auth/login` rate limit (Task 1.9).

**Acceptance criteria:**
- [ ] `slowapi` rate limiter applied to all `/api/ai/*` routes
- [ ] Limit: 30 requests per user per minute (configurable)
- [ ] Returns 429 when limit exceeded
- [ ] Rate limit is per-user, not global
- [ ] Different users have independent rate limits

**Test contract:**
- Test file: `tests/unit/test_ai_rate_limit.py`
- Send 31 requests to an `/api/ai` endpoint with user A token: assert 429 on the 31st. Send 1 request with user B token: assert 200 (not affected by A's limit).

---

### Task 1.17 — System Metrics Endpoint (cgroup v2)

**Service/Target:** `backend/app/api/system.py`
**Depends on:** 1.6

**What to build:**
Implement system metrics endpoints that read from cgroup v2 as specified in ROADMAP 1d and 3c. Read memory from `/sys/fs/cgroup/memory.current` and `/sys/fs/cgroup/memory.max`, CPU from `/sys/fs/cgroup/cpu.stat`. Do NOT use psutil — it reports host-level data inside Docker containers. Return: `{"memory_used_bytes", "memory_limit_bytes", "cpu_usage_usec"}`. Requires admin role.

**Acceptance criteria:**
- [ ] `GET /api/system/metrics` returns memory and CPU stats
- [ ] Reads from cgroup v2 paths, not psutil
- [ ] Returns 403 for non-admin users
- [ ] Gracefully handles missing cgroup files (returns partial data with nulls)

**Test contract:**
- Test file: `tests/unit/test_system_metrics.py`
- Mock cgroup file reads to return known values. Assert endpoint returns correct parsed values. Mock missing cgroup files: assert endpoint returns nulls without crashing. Test with member token: assert 403.

---

### Task 1.18 — ARQ Worker Service Configuration

**Service/Target:** `backend/app/worker.py`, `docker-compose.yml`
**Depends on:** 1.3, 1.5

**What to build:**
Create the ARQ worker entry point as specified in ROADMAP 0b. The worker service uses the same backend Docker image with a different command (`arq app.worker.WorkerSettings`). Create `backend/app/worker.py` with `WorkerSettings` class defining: Redis connection, job functions list (initially empty — jobs added per feature), `job_timeout=300` default, and `max_jobs=10`. Add the `worker` service to `docker-compose.yml` (already stubbed in Task 0.3 — add the actual command). Create a sample health-check job to verify the worker processes jobs.

**Acceptance criteria:**
- [ ] `backend/app/worker.py` exists with `WorkerSettings` class
- [ ] `WorkerSettings` defines Redis connection, timeout, max_jobs
- [ ] `worker` service in compose uses same image as backend with `command: arq app.worker.WorkerSettings`
- [ ] A sample job can be enqueued and processed
- [ ] Worker reads Redis connection from Docker secrets

**Test contract:**
- Test file: `tests/workers/test_worker_config.py`
- Import `WorkerSettings`, assert `job_timeout == 300`, `max_jobs == 10`. Create a simple async job function, enqueue it, assert the worker picks it up and completes it (integration test with real Redis).

---

### Task 1.19 — ptyHost WebSocket Service Scaffold

**Service/Target:** `docker/ptyhost/`, `shared/auth.js`
**Depends on:** 1.7

**What to build:**
Create the Node.js ptyHost service as specified in ROADMAP 1b. This is the WebSocket-based terminal PTY service using `node-pty`. Phase 1 scope: (1) WebSocket server on port 3001 with `/health` HTTP endpoint. (2) JWT validation on WebSocket connection using `shared/auth.js` — token in first message, not query params. (3) PTY spawn on authenticated connection (bash shell). (4) ACK-based flow control message schema: `{type:"data",id,data}` / `{type:"ack",id}` / `{type:"resize",cols,rows}`. (5) Shell cleanup on disconnect: SIGHUP -> 5s timeout -> SIGKILL. (6) Heartbeat ping every 30s. (7) ReconnectingPTY pattern with 100KB replay buffer per session. Note: sandbox-manager integration (running shells inside sandbox containers) is deferred — Phase 1 ptyHost spawns shells directly on the ptyHost container.

**Acceptance criteria:**
- [ ] `docker/ptyhost/` contains `package.json`, `index.js` (or `src/index.ts`), `Dockerfile`
- [ ] WebSocket server runs on port 3001
- [ ] `GET /health` returns 200
- [ ] JWT required in first WebSocket message — connection without JWT is rejected (close code 4001)
- [ ] PTY spawns on successful auth, data flows bidirectionally
- [ ] Message schema follows ACK-based flow control spec
- [ ] Shell receives SIGHUP on disconnect, SIGKILL after 5s timeout
- [ ] Heartbeat ping every 30s, close on pong timeout
- [ ] Replay buffer (100KB cap) enables reconnection to existing session
- [ ] Dockerfile uses `node:22-alpine` base with `HEALTHCHECK`

**Test contract:**
- Test file: `docker/ptyhost/src/__tests__/ptyhost.test.js` (Jest)
- Test: connect without JWT in first message → connection closed with 4001. Test: connect with valid JWT → PTY spawns, echo command returns expected output. Test: resize message changes PTY dimensions. Test: disconnect triggers shell cleanup (mock process signals).
- Integration test: `tests/integration/test_ptyhost_ws.py` (Python websockets library)
- Connect with valid JWT, send `echo hello\n`, assert response contains `hello`. Connect without JWT, assert connection rejected.

---

### Task 1.20 — Nginx Reverse Proxy Configuration

**Service/Target:** `docker/nginx/nginx.conf`, `docker/nginx/Dockerfile`
**Depends on:** 1.1, 1.19

**What to build:**
Create the Nginx reverse proxy configuration as specified in ROADMAP 1c. Location blocks for: `/api/` (FastAPI backend), `/yjs` (Yjs WebSocket), `/pty` (ptyHost WebSocket), `/health` (backend health). WebSocket upgrade support with `proxy_read_timeout 3600s` and ping/pong every 30s. SSL termination with self-signed cert for LAN (generate with `openssl` in Dockerfile build). `proxy_buffering off` for WebSocket and SSE paths. HTTP/2 for static assets. `X-Frame-Options SAMEORIGIN` header. Static file serving for the frontend build (`/` location).

**Acceptance criteria:**
- [ ] `docker/nginx/nginx.conf` exists with all location blocks
- [ ] `/api/` proxies to `backend:8000`
- [ ] `/yjs` proxies to `yjs:1234` with WebSocket upgrade
- [ ] `/pty` proxies to `ptyhost:3001` with WebSocket upgrade
- [ ] `proxy_read_timeout 3600s` set on WebSocket locations
- [ ] `proxy_buffering off` set on WebSocket and SSE locations
- [ ] SSL configured (self-signed cert generation in Dockerfile)
- [ ] `X-Frame-Options SAMEORIGIN` set globally
- [ ] HTTP/2 enabled
- [ ] `nginx -t` passes on the config file
- [ ] Dockerfile uses `nginx:alpine` base with HEALTHCHECK

**Test contract:**
- Test file: `tests/unit/test_nginx_config.py`
- Run `nginx -t -c /path/to/nginx.conf` (via Docker or locally if nginx available): assert exit code 0. Parse the config file as text: assert `/api/` location exists, `/yjs` location exists, `/pty` location exists, `proxy_read_timeout 3600s` appears, `proxy_buffering off` appears, `X-Frame-Options` appears.
- Integration test: `tests/integration/test_nginx_proxy.py`
- With compose stack running: `curl -k https://localhost/health` returns 200. `curl -k https://localhost/api/health` returns 200.

---

### Task 1.21 — Claude AI Auth Migration (Remove OAuth PKCE)

**Service/Target:** `backend/app/api/`, `backend/app/models/`
**Depends on:** 1.4, 1.6

**What to build:**
Remove the OAuth PKCE flow as specified in ROADMAP 1f. Delete any `claude_auth.py` file containing OAuth authorize URL, token exchange, and refresh logic. Repurpose the `claude_credentials` table (or create a new table) for storing per-user encrypted API keys. Encryption uses `pgcrypto` (`pgp_sym_encrypt`) with the encryption key from Docker secrets. Create endpoints: `PUT /api/settings/claude-key` (store encrypted key), `DELETE /api/settings/claude-key` (remove key). The shared org key (`ANTHROPIC_API_KEY` Docker secret) remains the default. Add an Alembic migration for the `claude_credentials` table changes.

**Acceptance criteria:**
- [ ] No file named `claude_auth.py` exists with OAuth PKCE logic
- [ ] No OAuth authorize URL, token exchange, or refresh endpoints exist
- [ ] `claude_credentials` table stores encrypted API keys via `pgp_sym_encrypt`
- [ ] Encryption key read from Docker secrets (not hardcoded)
- [ ] `PUT /api/settings/claude-key` encrypts and stores the user's API key
- [ ] `DELETE /api/settings/claude-key` removes the stored key
- [ ] `GET /api/ai/config` returns whether user has a personal key (boolean, never the key itself)
- [ ] Org-level `ANTHROPIC_API_KEY` Docker secret remains the default fallback
- [ ] SSE streaming works with both org key and per-user key paths

**Test contract:**
- Test file: `tests/unit/test_claude_auth.py`
- Store a key via PUT: assert 200. Retrieve config via GET: assert `has_personal_key: true`. Delete key: assert 200. Retrieve config: assert `has_personal_key: false`. Assert no endpoint matches `oauth`, `authorize`, or `token_exchange` patterns. Grep the codebase for `claude_auth.py` — must not exist (or must not contain OAuth logic).
- Integration test: `tests/integration/test_claude_key_encryption.py`
- Against real Postgres with pgcrypto: store a key, read it back decrypted, assert it matches. Assert the raw database column is NOT the plaintext key.

---

### Task 1.22 — Backend asyncio.to_thread Wrapper for spawn_agent

**Service/Target:** `backend/app/core/bricklayer_client.py`
**Depends on:** 1.3

**What to build:**
Create a BrickLayer client module that wraps all calls to the BrickLayer sidecar (`http://bricklayer:8300/`) in `asyncio.to_thread()` as specified in ROADMAP 1d. The sidecar doesn't exist yet (Phase 3.5-BL), but the client establishes the async-safe calling pattern now. Functions: `spawn_agent(name, prompt, cwd)`, `get_agent_status(agent_id)`, `stream_agent(agent_id)`. All include `BL_INTERNAL_SECRET` header from Docker secrets. If bricklayer service is unavailable, return a graceful error (not an unhandled exception).

**Acceptance criteria:**
- [ ] `backend/app/core/bricklayer_client.py` exports `spawn_agent()`, `get_agent_status()`, `stream_agent()`
- [ ] All HTTP calls to bricklayer are wrapped in `asyncio.to_thread()` or use `httpx.AsyncClient`
- [ ] `BL_INTERNAL_SECRET` header included on all requests
- [ ] Graceful error handling when bricklayer service is unavailable (returns error dict, not exception)
- [ ] Connection timeout of 5 seconds, read timeout of 30 seconds

**Test contract:**
- Test file: `tests/unit/test_bricklayer_client.py`
- Mock the HTTP calls. Assert `spawn_agent()` sends POST to `http://bricklayer:8300/agent/spawn` with correct headers. Assert timeout values are set. Mock connection refused: assert function returns error dict without raising. Assert the calling coroutine does not block the event loop for more than 50ms (time the call).

---

### Task 1.23 — Yjs Server Health Endpoint

**Service/Target:** `docker/yjs/`
**Depends on:** 1.7

**What to build:**
Create the Yjs WebSocket server as a Node.js service. Phase 1 scope is minimal: (1) WebSocket server on port 1234 handling Yjs document sync via `y-websocket`. (2) `GET /health` HTTP endpoint returning 200. (3) JWT validation on WebSocket connection using `shared/auth.js`. (4) Dockerfile using `node:22-alpine` with HEALTHCHECK. Full persistence (y-postgresql) is deferred to Phase 3.

**Acceptance criteria:**
- [ ] `docker/yjs/` contains `package.json`, `index.js`, `Dockerfile`
- [ ] WebSocket server on port 1234
- [ ] `GET /health` returns 200
- [ ] JWT validation on WebSocket connection via `shared/auth.js`
- [ ] Dockerfile uses `node:22-alpine` with HEALTHCHECK
- [ ] Yjs document sync works between two connected clients

**Test contract:**
- Test file: `docker/yjs/src/__tests__/yjs-server.test.js`
- Test: `GET /health` returns 200. Test: WebSocket without JWT is rejected. Test: two clients connect to the same document, one writes, the other receives the update.
- Integration test: `tests/integration/test_yjs_server.py`
- Connect two websocket clients to the same doc room with valid JWTs, assert sync works.

---

### Task 1.24 — Sandbox Manager Scaffold

**Service/Target:** `docker/sandbox-manager/`
**Depends on:** 1.1

**What to build:**
Create the sandbox-manager service scaffold as specified in ROADMAP 0b and 1b. This service owns `docker.sock` access via `tecnativa/docker-socket-proxy`. Phase 1 scope: (1) HTTP API on port 3002 with `POST /sandbox/exec` (create exec session in a container) and `GET /health`. (2) Docker socket access via socket-proxy (not direct mount). (3) Use `aiodocker` (async Python) or a Node.js equivalent — NOT `docker-py` (sync, blocks event loop). (4) HEALTHCHECK. The full sandbox functionality (three modes) is Phase 3.5-SB, but the scaffold must exist for ptyHost integration.

**Acceptance criteria:**
- [ ] `docker/sandbox-manager/` contains service code and Dockerfile
- [ ] `POST /sandbox/exec` endpoint exists (returns container exec ID or error)
- [ ] `GET /health` returns 200
- [ ] Docker socket accessed via `tecnativa/docker-socket-proxy`, not direct mount
- [ ] Uses async Docker client (aiodocker or equivalent), NOT docker-py
- [ ] `docker-compose.yml` includes `sandbox-manager` service with socket-proxy sidecar
- [ ] socket-proxy scoped to: `containers`, `exec`, `images` (not full Docker API)
- [ ] No other service in compose mounts `docker.sock`

**Test contract:**
- Test file: `tests/unit/test_sandbox_manager.py`
- Assert `GET /health` returns 200. Assert Docker client is async (not docker-py). Parse `docker-compose.yml`: assert only `sandbox-manager` (via socket-proxy) has docker.sock access. Assert socket-proxy environment enables `containers`, `exec`, `images`.

---

### Task 1.25 — Integration Test: Full Compose Stack

**Service/Target:** `tests/integration/test_full_stack.py`, `docker-compose.test.yml`
**Depends on:** 1.1, 1.2, 1.9, 1.10, 1.19, 1.20, 1.23

**What to build:**
Create a `docker-compose.test.yml` (extends the main compose with test-specific overrides) and a full-stack integration test that validates all Phase 1 services work together. The test: (1) brings up all services, (2) waits for all healthchecks, (3) creates a user via direct DB insert, (4) logs in via `/auth/login`, (5) uses the JWT to hit `/api/files/tree`, (6) connects to ptyHost WebSocket, (7) connects to Yjs WebSocket, (8) hits `/health` on all services. This is the Phase 1 graduation test.

**Acceptance criteria:**
- [ ] `docker-compose.test.yml` exists with test-specific config (test DB, no volumes)
- [ ] All services reach `healthy` within 90 seconds
- [ ] Login flow works end-to-end (create user, login, receive JWT)
- [ ] Authenticated file tree request succeeds
- [ ] ptyHost WebSocket connection with JWT succeeds
- [ ] Yjs WebSocket connection with JWT succeeds
- [ ] All `/health` endpoints return 200

**Test contract:**
- Test file: `tests/integration/test_full_stack.py`
- Start compose stack, run the full flow described above. Assert each step succeeds. Tear down after. This test runs in CI `integration` stage.

---

*End of spec. Phase 2+ is not planned here. All tasks above are grounded in the authority documents: ROADMAP.md, ARCHITECTURE.md, BUILD_BIBLE.md, design-system.md, and codevvos-experience-design.md.*

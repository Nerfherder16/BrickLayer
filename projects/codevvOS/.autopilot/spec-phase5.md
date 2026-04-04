# Spec: CodeVV OS — Phase 5 (Roadmap 3e / 3f / 3.5-BL / 3.5-AP / 3.5-KG)

**Created**: 2026-04-03
**Project**: codevvOS
**Branch**: autopilot/phase5-20260403

## Decisions (confirmed before build)

- **BL sidecar packaging**: self-contained copy of `bl/` shipped inside `bl-sidecar/` directory — no bind mount
- **Inline AI edit LLM**: Ollama via Tailscale (`http://100.70.195.84:11434`) — configured via `OLLAMA_BASE_URL` env var, model via `OLLAMA_MODEL` (default: `llama3.1`)
- **Knowledge Graph**: included in this phase

## Goal

Complete all remaining Phase 3 / 3.5 features: CodeMirror 6 inline AI editing, live preview panel, BrickLayer sidecar Docker service with SSE streaming, artifact rendering panel, and Neo4j-backed knowledge graph panel.

## Stack

- **Frontend**: React 19, TypeScript, Vite 6, dockview, Zustand, Tailwind v4
- **Backend**: Python 3.11, FastAPI, sse-starlette, neo4j async driver, httpx
- **New frontend deps**: `@codemirror/state`, `@codemirror/view`, `@codemirror/lang-javascript`, `@codemirror/lang-python`, `@codemirror/theme-one-dark`, `@react-sigma/core`, `graphology`, `graphology-layout-forceatlas2`, `ansi-to-html`
- **New backend deps**: `neo4j`, `httpx` (already present), `esbuild` (binary, installed in Dockerfile)
- **Test runner (frontend)**: `cd frontend && npx vitest run`
- **Test runner (backend)**: `cd backend && python -m pytest tests/`
- **Type check**: `cd frontend && npx tsc --noEmit`
- **Lint**: `cd frontend && npx eslint src/ --max-warnings=0`

## Constraints

- No hardcoded hex colors — always `var(--color-*)` design tokens
- Artifact iframe: `sandbox="allow-scripts"` only — NO `allow-same-origin`
- Inline AI sends ONLY the current document, never the full project tree
- Neo4j credentials hardcoded for dev (`neo4j/codevvos`) — prod auth is out of scope
- esbuild runs as subprocess (CLI binary) — backend stays Python-only
- File size limit: 400 lines per production file (600 hard limit)
- Do NOT modify existing chat, notification, or file explorer functionality

---

## Wave 1 — All independent, dispatch simultaneously

### Task 5.1 — CodeMirror 6 Base Integration

**Description**: Install CM6 packages and create a `CodeMirrorEditor` React component wrapping `EditorView` with language detection, dark theme, and controlled value. Replaces Monaco in `EditorPanel` behind feature flag `useCodeMirror` (default `true`).

**New deps (install with --legacy-peer-deps if needed)**:
```
@codemirror/state @codemirror/view @codemirror/lang-javascript @codemirror/lang-python @codemirror/theme-one-dark
```

**Files**:
- `frontend/src/components/Editor/CodeMirrorEditor.tsx`
- `frontend/src/components/Editor/useCodeMirrorLanguage.ts`
- `frontend/src/components/Panels/EditorPanel.tsx` (modify — add feature flag)
- `frontend/src/__tests__/codemirror-editor.test.tsx`

**TDD contracts**:
- `data-testid="codemirror-editor"` present when rendered
- `onChange` fires when content is programmatically set via dispatch
- Language extension swaps when `language` prop changes (js → python)
- `useEffect` cleanup destroys `EditorView` on unmount (no leak)
- Feature flag `false` renders Monaco fallback

**Parallel**: yes
**Dependencies**: none

---

### Task 5.3 — Inline Edit Backend Endpoint

**Description**: `POST /api/ai/inline-edit` accepts `{prompt, document, language}`, streams edited document via SSE to `OLLAMA_BASE_URL`. Rate limited 5 req/min per session. Document max 100KB. Final event: `event: done`.

**Files**:
- `backend/app/api/ai_edit.py`
- `backend/app/services/llm_service.py`
- `backend/app/main.py` (modify — register router)
- `backend/tests/unit/test_ai_edit.py`

**TDD contracts**:
- Missing fields → 422
- Document > 100KB → 413
- Valid request → `Content-Type: text/event-stream`
- 6th request in 60s window → 429
- Final SSE event is `event: done`
- LLM service uses `OLLAMA_BASE_URL` env var (mock in tests)

**Parallel**: yes
**Dependencies**: none

---

### Task 5.4 — Live Preview Panel

**Description**: `LivePreviewPanel` dockview panel with sandboxed iframe loading `http://localhost:{previewPort}` (from Zustand `previewStore`). Toolbar: refresh, viewport selector (1440/768/375px), URL bar. Auto-reloads on `preview-reload` SSE event. Error overlay on iframe load failure.

**Files**:
- `frontend/src/components/Panels/LivePreviewPanel.tsx`
- `frontend/src/components/Preview/ViewportToolbar.tsx`
- `frontend/src/components/Preview/ErrorOverlay.tsx`
- `frontend/src/stores/previewStore.ts`
- `frontend/src/__tests__/live-preview-panel.test.tsx`

**TDD contracts**:
- `data-testid="live-preview-iframe"` renders with `src` from store
- Viewport selector changes iframe `style.width` to 1440/768/375px
- Refresh button reassigns iframe `src`
- `data-testid="preview-error-overlay"` appears on iframe onerror
- Error overlay hides on retry click
- `preview-reload` SSE event triggers src refresh

**Parallel**: yes
**Dependencies**: none

---

### Task 5.5 — Nginx Preview + Sidecar + Neo4j Proxy Routes

**Description**: Add proxy routes to `nginx/default.conf`: `/preview/` → configurable dev server port (env `PREVIEW_PORT`, default 5173), `/bl-sidecar/` → `bl-sidecar:8300`, `/neo4j/` → `neo4j:7474`. All routes include WebSocket upgrade headers for HMR support.

**Files**:
- `nginx/default.conf` (modify)
- `tests/integration/test_nginx_proxy.sh` (curl smoke tests)

**TDD contracts**:
- `/preview/` returns 502 when no upstream (not 404)
- `/bl-sidecar/health` proxies to sidecar
- `/neo4j/` proxies to Neo4j HTTP API
- `Upgrade` and `Connection` headers forwarded for `/preview/`

**Parallel**: yes
**Dependencies**: none

---

### Task 5.6 — BrickLayer Sidecar Docker Service

**Description**: Self-contained FastAPI service in `bl-sidecar/`. Ships a copy of BrickLayer's `bl/` directory. Endpoints: `GET /health`, `POST /run` (SSE stream), `POST /interrupt` (SIGINT running command), `GET /status`. Long-running ops use `asyncio.to_thread()`. Runs on port 8300.

**Files**:
- `bl-sidecar/server.py`
- `bl-sidecar/Dockerfile`
- `bl-sidecar/requirements.txt`
- `docker-compose.yml` (modify — add bl-sidecar service, internal network only)
- `bl-sidecar/tests/test_server.py`

**TDD contracts**:
- `GET /health` → 200 `{"status": "ok"}`
- `POST /run` with valid command → `text/event-stream` response
- `POST /run` with unknown command → 400
- `POST /interrupt` while command running → 200
- `POST /interrupt` while idle → 409
- `GET /status` → `{"active": false}` when idle
- Concurrent `/health` call during long `/run` returns within 100ms (non-blocking)

**Parallel**: yes
**Dependencies**: none

---

### Task 5.8 — Artifact JSX Compile Endpoint

**Description**: `POST /api/artifacts/compile` accepts `{jsx, dependencies[]}`. Runs `esbuild` subprocess to transform JSX → `React.createElement`. Validates: JSX < 50KB, deps from allowlist (`react`, `react-dom`, `recharts`, `lucide-react`). Returns `{compiled, error}`.

**Files**:
- `backend/app/api/artifacts.py`
- `backend/app/services/jsx_compiler.py`
- `backend/app/main.py` (modify — register router)
- `backend/Dockerfile` (modify — install esbuild binary)
- `backend/tests/unit/test_artifacts.py`

**TDD contracts**:
- Valid JSX → compiled output contains `React.createElement`
- JSX > 50KB → 413
- Dependency not in allowlist → 400
- JSX syntax error → 200 with `error` field populated
- Empty JSX → 400
- esbuild binary callable from test env

**Parallel**: yes
**Dependencies**: none

---

### Task 5.11 — Docker Compose — Neo4j Service

**Description**: Add Neo4j 5.x to `docker-compose.yml`. Auth: `NEO4J_AUTH=neo4j/codevvos`. Expose Bolt (7687) and HTTP (7474) internally only. Health check on HTTP. Init script creates base schema: `(:Decision)`, `(:Assumption)`, `(:Evidence)`, `(:CodeFile)` nodes with `[:BASED_ON]`, `[:CONTRADICTS]`, `[:SUPPORTS]`, `[:REFERENCES]` relationships.

**Files**:
- `docker-compose.yml` (modify — add neo4j service)
- `neo4j/init-cypher.sh`
- `neo4j/constraints.cypher`
- `tests/integration/test_neo4j_health.sh`

**TDD contracts**:
- Neo4j service has health check configured
- Init script creates all 4 node labels
- Init script creates all 4 relationship types
- Bolt port 7687 reachable from backend network
- HTTP port 7474 reachable from nginx network

**Parallel**: yes
**Dependencies**: none

---

## Wave 2 — After their dependencies from Wave 1

### Task 5.2 — Inline AI Prompt (`Cmd+K`)

**Description**: CM6 extension intercepting `Cmd+K` (Mac) / `Ctrl+K` (other). Opens a floating `Decoration.widget` input at cursor. On submit, calls `POST /api/ai/inline-edit` and streams SSE. Spinner during stream. On completion, renders unified diff decorations (green added / red removed lines). Action bar: Accept, Reject, Regenerate. Widget dismisses on Escape.

**Files**:
- `frontend/src/components/Editor/extensions/inlineAIPrompt.ts`
- `frontend/src/components/Editor/extensions/diffDecorations.ts`
- `frontend/src/components/Editor/InlinePromptWidget.tsx`
- `frontend/src/components/Editor/DiffActionBar.tsx`
- `frontend/src/__tests__/inline-ai-prompt.test.tsx`

**TDD contracts**:
- Keybinding triggers `data-testid="inline-prompt-input"` at cursor
- Submission calls `POST /api/ai/inline-edit` with `{prompt, document, language}`
- Diff decorations: added lines have `cm-line-added` class, removed have `cm-line-removed`
- Accept applies new content to editor state
- Reject restores original content
- Regenerate re-submits same prompt
- Escape dismisses widget without change

**Parallel**: no
**Dependencies**: 5.1 (CodeMirror base), 5.3 (backend endpoint)

---

### Task 5.7 — BrickLayer Sidecar Frontend Integration

**Description**: Zustand `sidecarStore` with `runCommand(cmd, args)` (SSE stream → output array), `interrupt()`, `getStatus()`. `SidecarOutputPanel` dockview panel with ANSI color rendering (`ansi-to-html`), run/stop toolbar, command input.

**New deps**: `ansi-to-html`

**Files**:
- `frontend/src/stores/sidecarStore.ts`
- `frontend/src/components/Panels/SidecarOutputPanel.tsx`
- `frontend/src/components/Sidecar/CommandToolbar.tsx`
- `frontend/src/components/Sidecar/AnsiOutput.tsx`
- `frontend/src/__tests__/sidecar-store.test.ts`
- `frontend/src/__tests__/sidecar-output-panel.test.tsx`

**TDD contracts**:
- `runCommand` opens `EventSource` to `/bl-sidecar/run`
- SSE data events accumulate in `output` array in store
- `interrupt` calls `POST /bl-sidecar/interrupt`
- `SidecarOutputPanel` renders output lines from store
- ANSI escape codes render as `<span style="color:...">` elements
- Stop button is disabled when no command running
- Panel shows `data-testid="sidecar-connecting"` before first event

**Parallel**: no
**Dependencies**: 5.6 (sidecar service must exist)

---

### Task 5.9 — Artifact Panel Frontend Renderer

**Description**: `ArtifactPanel` dockview panel with `srcdoc` iframe (`sandbox="allow-scripts"` — NO `allow-same-origin`). PostMessage with `crypto.randomUUID()` nonce per render. `RenderChip` inline component for chat messages. Zustand `artifactStore` holds `{id, title, jsx, compiled}`.

**Files**:
- `frontend/src/components/Panels/ArtifactPanel.tsx`
- `frontend/src/components/Artifacts/IframeSandbox.tsx`
- `frontend/src/components/Artifacts/RenderChip.tsx`
- `frontend/src/stores/artifactStore.ts`
- `frontend/src/components/Panels/ChatPanel.tsx` (modify — render RenderChip)
- `frontend/src/__tests__/artifact-panel.test.tsx`
- `frontend/src/__tests__/render-chip.test.tsx`

**TDD contracts**:
- `data-testid="artifact-iframe"` has `sandbox` attr containing `allow-scripts` but NOT `allow-same-origin`
- `srcdoc` contains nonce value
- `RenderChip` renders for messages with `artifact` metadata
- Clicking `RenderChip` sets active artifact in store
- `artifactStore` persists across panel open/close
- Error postMessage from iframe renders `data-testid="artifact-error-overlay"`

**Parallel**: no
**Dependencies**: 5.8 (compile endpoint must exist)

---

### Task 5.12 — Knowledge Graph Backend API

**Description**: FastAPI router `/api/graph/` — `GET /nodes`, `POST /nodes`, `POST /edges`, `GET /neighborhood/{nodeId}` (2-hop), `GET /decisions`. Uses `neo4j` async Python driver. Connection via `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` env vars.

**Files**:
- `backend/app/api/graph.py`
- `backend/app/services/neo4j_client.py`
- `backend/app/main.py` (modify — register router)
- `backend/tests/unit/test_graph_api.py`

**TDD contracts**:
- `GET /nodes` → empty list when graph empty
- `POST /nodes` → returns node ID on success
- `POST /edges` → creates relationship between two nodes
- `GET /neighborhood/{id}` → node + 2-hop neighbors
- `GET /decisions` → Decision nodes with BASED_ON chains
- Invalid node type → 400
- Neo4j connection error → 503

**Parallel**: no
**Dependencies**: 5.11 (Neo4j service must exist)

---

## Wave 3 — After Wave 2

### Task 5.10 — Artifact Persistence to Recall

**Description**: `POST /api/artifacts/persist` stores artifact to Recall via HTTP. Frontend fetches artifact history on ArtifactPanel mount. `ArtifactHistory` dropdown in panel toolbar.

**Files**:
- `backend/app/api/artifacts.py` (modify — add persist endpoint)
- `backend/app/services/recall_client.py`
- `frontend/src/components/Artifacts/ArtifactHistory.tsx`
- `frontend/src/components/Panels/ArtifactPanel.tsx` (modify)
- `backend/tests/unit/test_artifact_persistence.py`
- `frontend/src/__tests__/artifact-history.test.tsx`

**TDD contracts**:
- Persist endpoint calls Recall at `RECALL_BASE_URL` env var
- Returns artifact ID on success
- History endpoint returns list sorted by timestamp desc
- `ArtifactHistory` renders artifact titles
- Selecting history item loads artifact into panel
- Recall connection error → empty list (graceful degradation)

**Recall base URL**: `http://100.70.195.84:8200` (env var `RECALL_BASE_URL`)

**Parallel**: no
**Dependencies**: 5.8, 5.9

---

### Task 5.13 — Knowledge Graph Frontend Panel

**Description**: `KnowledgeGraphPanel` using `@react-sigma/core` + `graphology` force-directed layout. Node colors: Decision=blue, Assumption=amber, Evidence=green, CodeFile=gray. Click → side detail pane. Toolbar: type filter, search, Add Decision button.

**New deps**: `@react-sigma/core`, `graphology`, `graphology-layout-forceatlas2`

**Files**:
- `frontend/src/components/Panels/KnowledgeGraphPanel.tsx`
- `frontend/src/components/Graph/GraphCanvas.tsx`
- `frontend/src/components/Graph/NodeDetail.tsx`
- `frontend/src/components/Graph/AddDecisionForm.tsx`
- `frontend/src/stores/graphStore.ts`
- `frontend/src/__tests__/knowledge-graph-panel.test.tsx`
- `frontend/src/__tests__/graph-store.test.ts`

**TDD contracts**:
- Panel renders `data-testid="graph-canvas"` without crashing with empty data
- Decision nodes have blue fill color token
- Type filter toggle hides nodes of that type
- Search input filters nodes by title substring
- Clicking node sets `selectedNode` in store and shows `data-testid="node-detail"`
- `AddDecisionForm` submits to `POST /api/graph/nodes`
- Store fetches from `/api/graph/nodes` on mount

**Parallel**: no
**Dependencies**: 5.12

---

## Wave 4 — All panels must exist

### Task 5.14 — Panel Registration + Dock Integration

**Description**: Register `LivePreviewPanel`, `SidecarOutputPanel`, `ArtifactPanel`, `KnowledgeGraphPanel` in dockview panel factory (App.tsx) and Dock component. Add keyboard shortcuts: `Cmd+Shift+P` (preview), `Cmd+Shift+B` (sidecar), `Cmd+Shift+A` (artifacts), `Cmd+Shift+G` (graph).

**Files**:
- `frontend/src/App.tsx` (modify — panel factory)
- `frontend/src/components/Dock/Dock.tsx` (modify — icons + labels)
- `frontend/src/components/Dock/appRegistry.ts` (modify — add 4 new entries)
- `frontend/src/__tests__/panel-registration.test.tsx`

**TDD contracts**:
- Panel factory creates each new panel type without error
- `APP_REGISTRY` has entries for all 4 new panels
- Each panel has `id`, `label`, `icon`, `componentKey`
- Keyboard shortcuts open correct panels via `registerShortcut`
- All panels render without console errors

**Parallel**: no
**Dependencies**: 5.4, 5.7, 5.9, 5.13

---

## Wave 5 — Integration gate

### Task 5.15 — Integration Smoke Tests

**Description**: End-to-end integration tests verifying cross-component data flow. Frontend component integration tests + backend integration smoke tests.

**Files**:
- `frontend/src/__tests__/phase5-graduation.test.tsx`
- `tests/integration/test_phase5_smoke.py`

**TDD contracts**:
- CodeMirror editor mounts with feature flag enabled
- Inline prompt widget appears on simulated Cmd+K
- `LivePreviewPanel` renders iframe with src from store
- `SidecarOutputPanel` renders with SSE mock
- `ArtifactPanel` renders iframe with `allow-scripts` sandbox
- `KnowledgeGraphPanel` renders graph canvas
- `APP_REGISTRY` includes all 4 new panel keys
- All panels coexist in dockview without errors

**Parallel**: no
**Dependencies**: 5.1–5.14 (all prior tasks)

---

## Wave Summary

| Wave | Tasks | Can run simultaneously |
|------|-------|------------------------|
| 1 | 5.1, 5.3, 5.4, 5.5, 5.6, 5.8, 5.11 | YES — all 7 in parallel |
| 2 | 5.2, 5.7, 5.9, 5.12 | YES — all 4 in parallel |
| 3 | 5.10, 5.13 | YES — both in parallel |
| 4 | 5.14 | single task |
| 5 | 5.15 | single task |

## Definition of Done

- All 15 tasks complete with passing tests
- `cd frontend && npx vitest run` → 0 failures
- `cd frontend && npx tsc --noEmit` → 0 errors
- `cd frontend && npx eslint src/ --max-warnings=0` → 0 warnings
- `cd backend && python -m pytest tests/` → 0 failures
- `docker compose build` → exits 0 for all services
- `dist/sw.js` present after `npm run build` (PWA)
- No regressions — all Phase 3/4 tests still pass

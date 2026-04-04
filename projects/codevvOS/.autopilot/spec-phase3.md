# CodeVV OS — Build Spec (Phase 3: Frontend Features)

**Generated:** 2026-04-03
**Source authority:** `ROADMAP.md`, `ARCHITECTURE.md`, `docs/design-system.md`, `BUILD_BIBLE.md`, `spec-phase2.md`
**Scope:** Phase 3 only. Covers: Terminal panel, File Tree panel, AI Chat panel, Dock integration, panel persistence (COMPONENTS registry), and backend `/api/ai/chat` SSE endpoint. Does NOT include Settings panel (3c), Notification Center (3d), Inline AI Editing (3e), Live Preview (3f), or any Phase 3.5 features.
**Depends on:** Phase 0 + Phase 1 + Phase 2 complete. DockviewShell, Dock, LayoutContext, LoginScreen, and layout persistence API all functional.

---

## Project Summary

Phase 3 brings the first real panel implementations to the DockviewShell. Where Phase 2 delivered the empty shell (dock + dockview + login), Phase 3 fills it with three working panels: a full xterm.js terminal connected to ptyHost via WebSocket, a file tree browser backed by the existing `/api/files/tree` endpoint, and an AI chat panel with SSE streaming from a new `/api/ai/chat` endpoint. The dock icons (Terminal, Files, MessageSquare) open these panels via `dockviewApi.addPanel()`. All new panel components are registered in the `COMPONENTS` map on `DockviewShell.tsx` so `fromJSON` can restore them on reload.

---

## How to Use This Spec

Each task follows strict TDD:

1. **Read the task card** — understand what to build, acceptance criteria, and test contract.
2. **Write the failing test(s)** from the test contract. Run the test. Verify it fails for the expected reason.
3. **Implement the minimum code** to make the test pass. No more.
4. **Run all tests** — new test and all existing tests must pass.
5. **Verify acceptance criteria** — every checkbox must be satisfiable with evidence.
6. **Mark the task complete.**

Dependencies are explicit. Do not start a task until all tasks in "Depends on" are complete.

**Parallel opportunities are called out explicitly.** Tasks 3.1, 3.2, and 3.3 run in parallel (terminal, file tree, AI chat backend — they share no code). Task 3.4 depends on 3.3. Task 3.5 depends on 3.1, 3.2, and 3.4 (dock wiring). Task 3.6 depends on 3.5 (COMPONENTS registry). Task 3.7 is the graduation gate requiring all prior tasks.

---

## Phase 3 — Frontend Features

> All tasks produce production code with real tests. Design tokens from `frontend/src/styles/global.css` are used throughout — never hardcode hex values in component files. Panel CSS goes in separate `.css` files alongside the component, using CSS custom properties only.

---

### Task 3.1 — Terminal Panel (xterm.js + WebSocket)

**Service/Target:** `frontend/src/components/Panels/TerminalPanel.tsx`, `frontend/src/components/Panels/TerminalPanel.css`, `frontend/src/hooks/usePtyWebSocket.ts`
**Depends on:** Phase 2 complete (DockviewShell exists)
**Can run in parallel with:** Tasks 3.2, 3.3

**What to build:**
A dockview panel that renders an xterm.js terminal connected to the ptyHost WebSocket service at `ws://localhost:3001` (proxied through Nginx at `/pty`). The terminal supports full PTY: input forwarding, ANSI rendering, resize, and addon loading in the correct order per ROADMAP 3b.

1. **Install production dependencies** into `frontend/package.json`:
   - `@xterm/xterm` (xterm.js v6 core)
   - `@xterm/addon-fit` (auto-resize terminal to container)
   - `@xterm/addon-webgl` (GPU-accelerated rendering — primary renderer)
   - `@xterm/addon-web-links` (clickable URLs)
   - `@xterm/addon-search` (Ctrl+F search in terminal output)

2. **`usePtyWebSocket.ts`** hook:
   - Accepts `sessionId: string` parameter
   - Opens WebSocket to `/pty/${sessionId}` with JWT in first message: `{type: "auth", token: getStoredToken()}`
   - Sends data to ptyHost: `{type: "data", data: string}`
   - Receives data from ptyHost: `{type: "data", id: number, data: string}` — writes `data` to xterm
   - Sends ACK for each received data message: `{type: "ack", id: number}`
   - Sends resize events: `{type: "resize", cols: number, rows: number}`
   - Reconnection: on close/error, retry with exponential backoff (1s, 2s, 4s, max 30s). Max 10 retries then show "Connection lost" in terminal.
   - Returns `{ ws: WebSocket | null, readyState: number, send: (data: string) => void, sendResize: (cols: number, rows: number) => void }`
   - Cleanup: close WebSocket on unmount

3. **`TerminalPanel.tsx`:**
   - Accepts `IDockviewPanelProps` from dockview (standard panel component signature)
   - Creates `Terminal` instance with theme from design-system.md section 7 Terminal tokens:
     ```
     background: var(--terminal-background) → '#0A0A0D'
     foreground: var(--terminal-foreground) → '#CCCCCC'
     cursor: var(--terminal-cursor) → read from CSS custom property at runtime
     cursorAccent: '#0A0A0D'
     selectionBackground: 'rgba(107, 102, 248, 0.3)'
     black/red/green/yellow/blue/magenta/cyan/white: per design-system.md section 7
     fontFamily: read from CSS var(--font-mono) at runtime
     fontSize: 13
     lineHeight: 1.4
     ```
   - **Addon loading order** (CRITICAL — per ROADMAP 3b):
     1. `new Terminal(options)` — create instance
     2. `terminal.open(containerRef.current)` — attach to DOM (MUST happen before addon load)
     3. `terminal.loadAddon(webglAddon)` — GPU renderer
     4. `terminal.loadAddon(fitAddon)` — auto-resize
     5. `terminal.loadAddon(webLinksAddon)` — clickable URLs
     6. `terminal.loadAddon(searchAddon)` — search
     7. `fitAddon.fit()` — initial resize
   - **WebGL context loss fallback** (per ROADMAP 3b): `webglAddon.onContextLoss(() => { webglAddon.dispose(); /* no canvas fallback in v6 — falls back to DOM renderer automatically */ })`
   - **ResizeObserver** on the container div: debounce `fitAddon.fit()` at 150ms
   - Wire `terminal.onData()` → `ws.send()` (user keystrokes to ptyHost)
   - Wire incoming WS data → `terminal.write()` (ptyHost output to screen)
   - Wire `terminal.onResize()` → `sendResize(cols, rows)` (inform ptyHost of terminal dimensions)
   - Generate unique `sessionId` per panel instance: `crypto.randomUUID()`
   - **Dispose on unmount:** dispose addons first (fit, webgl, webLinks, search), then `terminal.dispose()`. Wrapped in a `useEffect` cleanup function.

4. **`TerminalPanel.css`:**
   - Container: `width: 100%; height: 100%; overflow: hidden; background: var(--terminal-background);`
   - The xterm.js container div: no border-radius (`var(--radius-none)` per design-system.md section 5 strict rules)
   - Import xterm.js CSS: `@import '@xterm/xterm/css/xterm.css';`

**Acceptance criteria:**
- [ ] `TerminalPanel.tsx` renders an xterm.js terminal without errors
- [ ] Addon loading order: `open()` before any `loadAddon()` call
- [ ] WebGL addon loaded as primary renderer
- [ ] `fitAddon.fit()` debounced at 150ms via ResizeObserver
- [ ] WebSocket connects to `/pty/{sessionId}` and sends auth message
- [ ] User keystrokes are forwarded to ptyHost via `{type: "data", data}`
- [ ] ptyHost output is written to terminal via `terminal.write()`
- [ ] Resize events sent to ptyHost via `{type: "resize", cols, rows}`
- [ ] ACK sent for each received data message
- [ ] Reconnection with exponential backoff on disconnect
- [ ] All addons disposed before terminal on unmount
- [ ] No hardcoded hex values in `.tsx` file (theme values read from CSS vars or design-system constants)
- [ ] Terminal background is `#0A0A0D` (from design-system.md terminal tokens via CSS var)
- [ ] Font is `var(--font-mono)` (JetBrains Mono)

**Test contract:**
- Test file: `frontend/src/components/Panels/__tests__/TerminalPanel.test.tsx`
  - Mock `@xterm/xterm` Terminal class. Render `<TerminalPanel />` with mock dockview panel props. Assert `Terminal` constructor was called. Assert `terminal.open()` was called with a DOM element. Assert `terminal.loadAddon()` called at least 2 times (fit + webgl). Assert `open()` was called BEFORE any `loadAddon()` call (check call order on spy).
  - Assert `terminal.dispose()` is called on unmount.
  - Assert component renders a container div with `data-testid="terminal-panel"`.
- Test file: `frontend/src/hooks/__tests__/usePtyWebSocket.test.ts`
  - Mock WebSocket globally. Call hook with `sessionId: "test-session"`. Assert WebSocket constructor called with URL containing `/pty/test-session`. Assert first message sent is `{type: "auth", token: ...}`.
  - Simulate receiving `{type: "data", id: 1, data: "hello"}`. Assert ACK `{type: "ack", id: 1}` is sent back.
  - Call `sendResize(80, 24)`. Assert message `{type: "resize", cols: 80, rows: 24}` sent.
  - Simulate WebSocket close. Assert reconnection attempt after 1s (mock timers).
  - Call cleanup (unmount). Assert WebSocket `.close()` called.

---

### Task 3.2 — File Tree Panel

**Service/Target:** `frontend/src/components/Panels/FileTreePanel.tsx`, `frontend/src/components/Panels/FileTreePanel.css`, `frontend/src/hooks/useFileTree.ts`, `frontend/src/api/files.ts`
**Depends on:** Phase 2 complete (DockviewShell exists), Phase 1 backend (`GET /api/files/tree`, `PATCH /api/files/{path}`)
**Can run in parallel with:** Tasks 3.1, 3.3

**What to build:**
A dockview panel that renders a tree view of the project file system, connected to the existing backend `/api/files/tree` and `/api/files/{path}` endpoints. Click on a file to preview its content in an adjacent detail pane within the same panel.

1. **`files.ts`** (API client module):
   - `fetchTree(path: string): Promise<TreeNode>` — calls `GET /api/files/tree?path={path}` with JWT auth header. Returns `{name, type, size?, modified?, children?}`.
   - `fetchFileContent(path: string): Promise<string>` — calls `PATCH /api/files/{path}` with `{action: "read"}` and JWT auth header. Returns file content as string.
   - Both functions use `getStoredToken()` for auth.

2. **`useFileTree.ts`** hook:
   - State: `tree: TreeNode | null`, `loading: boolean`, `error: string | null`, `expandedPaths: Set<string>`, `selectedFile: {path: string, content: string} | null`
   - `rootPath` parameter (defaults to env `WORKSPACE_ROOT` or `/workspace`)
   - On mount: calls `fetchTree(rootPath)` to get top-level directory listing
   - `expandDir(path: string)`: if not in `expandedPaths`, call `fetchTree(path)` to get children, merge into tree, add to `expandedPaths`. If already expanded, remove from `expandedPaths` (collapse).
   - `selectFile(path: string)`: calls `fetchFileContent(path)`, stores result in `selectedFile`.
   - Returns `{ tree, loading, error, expandedPaths, selectedFile, expandDir, selectFile }`

3. **`FileTreePanel.tsx`:**
   - Accepts `IDockviewPanelProps`
   - Two-zone layout within the panel:
     - **Left zone (tree):** 200px min-width, resizable via CSS `resize: horizontal`, `overflow: auto`
     - **Right zone (preview):** fills remaining width, shows file content when a file is selected
   - Tree rendering (recursive):
     - Each directory node: `ChevronRight` icon (rotated 90deg when expanded) + `FolderTree` icon + name. Click toggles expand/collapse.
     - Each file node: file icon (from lucide — `FileText` for generic) + name. Click selects and previews.
     - Indentation: `padding-left: calc(var(--space-4) * depth)` where `depth` is nesting level
     - Hover state: `var(--color-surface-3)` background, `var(--duration-instant)` transition
     - Selected file: `var(--color-accent-muted)` background, `var(--color-accent)` text
     - Directory expand/collapse: no animation (instant, per design-system.md section 8 — never animate content that updates at >10 FPS)
   - File preview zone:
     - Displays file content in `<pre>` with `var(--font-mono)`, `var(--text-code-md)` (14px)
     - Scrollable (`overflow: auto`)
     - Header bar: file name in `var(--text-sm) var(--font-weight-medium)`, file size in `var(--text-xs) var(--color-text-tertiary)`
     - Empty state when no file selected: "Select a file to preview" in `var(--color-text-tertiary)`
   - Loading state: skeleton placeholder or spinner in `var(--color-accent)`
   - Error state: error message in `var(--color-error)`

4. **`FileTreePanel.css`:**
   - Panel container: `display: flex; height: 100%; background: var(--color-surface-1);`
   - Tree zone: `min-width: 200px; max-width: 50%; border-right: 1px solid var(--color-border-subtle); overflow-y: auto;`
   - Tree item: `height: var(--sidebar-item-height)` (28px), `display: flex; align-items: center; gap: var(--space-1-5); padding: 0 var(--space-2); cursor: pointer;`
   - Tree item text: `font-size: var(--text-sm); color: var(--color-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`
   - Icons: `var(--icon-xs)` (12px), `var(--icon-stroke-dense)` (1px), `color: var(--color-text-secondary)`
   - Preview zone: `flex: 1; overflow: auto; padding: var(--space-3);`
   - Preview code: `font-family: var(--font-mono); font-size: var(--text-code-md); line-height: var(--leading-normal); color: var(--color-text-primary); white-space: pre; tab-size: 4;`

**Acceptance criteria:**
- [ ] `FileTreePanel.tsx` renders a file tree from `/api/files/tree` response
- [ ] Directories expand/collapse on click (lazy-loads children on first expand)
- [ ] Files show a content preview in the right zone on click
- [ ] Tree items use `var(--sidebar-item-height)` (28px) height
- [ ] Selected file has `var(--color-accent-muted)` background
- [ ] Hover state uses `var(--color-surface-3)`
- [ ] Indentation increases with depth via `var(--space-4)` multiplier
- [ ] Icons are 12px (`var(--icon-xs)`) with 1px stroke
- [ ] File preview uses `var(--font-mono)` at 14px (`var(--text-code-md)`)
- [ ] Empty state shows "Select a file to preview"
- [ ] Loading state shows while tree is being fetched
- [ ] Error state displays error message in `var(--color-error)`
- [ ] No hardcoded hex values in component files
- [ ] Panel background is `var(--color-surface-1)`

**Test contract:**
- Test file: `frontend/src/api/__tests__/files.test.ts`
  - Mock `fetch` via MSW. `fetchTree("/workspace")`: mock `GET /api/files/tree?path=/workspace` to return `{name: "workspace", type: "dir", children: [{name: "src", type: "dir"}, {name: "readme.md", type: "file", size: 100}]}`. Assert returned object matches.
  - `fetchFileContent("/workspace/readme.md")`: mock `PATCH /api/files/readme.md` to return `{content: "# Hello"}`. Assert returned content is `"# Hello"`.
  - `fetchTree` without valid token (mock `getStoredToken` to return null): assert fetch is still called (endpoint handles 401).
- Test file: `frontend/src/hooks/__tests__/useFileTree.test.ts`
  - Mock `fetchTree` and `fetchFileContent`. Render hook. Assert initial state: `loading: true`, `tree: null`.
  - After fetch resolves: assert `tree` is populated, `loading: false`.
  - Call `expandDir("/workspace/src")`: assert `fetchTree` called with `/workspace/src`. After resolve, assert `/workspace/src` is in `expandedPaths`.
  - Call `expandDir("/workspace/src")` again: assert path removed from `expandedPaths` (collapse).
  - Call `selectFile("/workspace/readme.md")`: assert `fetchFileContent` called. After resolve, assert `selectedFile` has `path` and `content`.
  - Mock `fetchTree` to throw: assert `error` state is set.
- Test file: `frontend/src/components/Panels/__tests__/FileTreePanel.test.tsx`
  - Mock `useFileTree` to return a populated tree. Render `<FileTreePanel />` with mock dockview props. Assert "src" directory item renders. Assert "readme.md" file item renders.
  - Click on "src" directory: assert `expandDir` was called.
  - Click on "readme.md" file: assert `selectFile` was called. With selectedFile in mock, assert preview zone shows file content.
  - With `selectedFile: null`: assert "Select a file to preview" message visible.
  - Assert component renders a container with `data-testid="file-tree-panel"`.

---

### Task 3.3 — Backend: `/api/ai/chat` SSE Endpoint

**Service/Target:** `backend/app/api/ai.py` (extend existing file)
**Depends on:** Phase 1 complete (FastAPI, auth, rate limiting)
**Can run in parallel with:** Tasks 3.1, 3.2

**What to build:**
A new SSE streaming endpoint for AI chat completions using Ollama (or a configured LLM provider). The endpoint receives a message and optional history, then streams tokens back via Server-Sent Events.

1. **Extend `backend/app/api/ai.py`:**
   - New Pydantic models:
     ```python
     class ChatMessage(BaseModel):
         role: str  # "user" or "assistant"
         content: str

     class ChatRequest(BaseModel):
         message: str
         history: list[ChatMessage] = []
     ```
   - New endpoint: `POST /api/ai/chat`
     - Requires JWT auth (same pattern as existing `/api/ai/status`)
     - Rate limited: reuse existing `RATE_LIMIT_AI` ("30/minute" per user)
     - Reads `OLLAMA_BASE_URL` from env (default: `http://gpu-vm:8200/api`). Per ARCHITECTURE.md, CodeVV calls Recall's API, which proxies to Ollama. If `OLLAMA_BASE_URL` is not set, return 503 with `{"detail": "AI service not configured"}`.
     - Reads `OLLAMA_MODEL` from env (default: `llama3.2`)
     - Constructs message list from `history` + new `message`
     - Calls Ollama chat completion endpoint (via httpx async streaming): `POST {OLLAMA_BASE_URL}/chat` with `{"model": model, "messages": messages, "stream": true}`
     - Streams response as SSE:
       - Each token: `data: {"token": "<text>"}\n\n`
       - On completion: `data: [DONE]\n\n`
     - Error handling:
       - Ollama unreachable: yield `data: {"error": "AI service unavailable"}\n\n` then `data: [DONE]\n\n`
       - Ollama returns error: yield `data: {"error": "<detail>"}\n\n` then `data: [DONE]\n\n`
     - Response headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no` (Nginx SSE compatibility)

2. **Add `httpx` to backend requirements** (if not already present):
   - `httpx` for async HTTP client (streaming support)

**Acceptance criteria:**
- [ ] `POST /api/ai/chat` endpoint exists and returns SSE stream
- [ ] Request body validated: `message` required, `history` optional
- [ ] JWT required — 401 without valid token
- [ ] Rate limited at 30/minute per user (reuses existing limiter)
- [ ] Streams tokens as `data: {"token": "..."}\n\n`
- [ ] Stream ends with `data: [DONE]\n\n`
- [ ] Returns 503 if `OLLAMA_BASE_URL` not configured
- [ ] Graceful error handling when Ollama is unreachable
- [ ] Response has `Content-Type: text/event-stream` header
- [ ] Response has `X-Accel-Buffering: no` header
- [ ] `raise X from e` used in all except blocks (ruff clean)
- [ ] No bare `except: pass`

**Test contract:**
- Test file: `tests/unit/test_ai_chat.py`
  - `POST /api/ai/chat` without JWT: assert 401.
  - `POST /api/ai/chat` with empty body: assert 422 (validation error — `message` required).
  - `POST /api/ai/chat` with valid request, mock Ollama response: mock `httpx.AsyncClient.stream` to yield `{"message": {"content": "Hello"}}` chunks. Assert SSE stream contains `data: {"token": "Hello"}` and ends with `data: [DONE]`.
  - `POST /api/ai/chat` with Ollama unreachable (mock httpx to raise `httpx.ConnectError`): assert SSE stream contains `data: {"error": "AI service unavailable"}` followed by `data: [DONE]`.
  - `POST /api/ai/chat` with `OLLAMA_BASE_URL` unset: assert 503 response.
  - `POST /api/ai/chat` with history: assert message list sent to Ollama includes history messages plus the new message.
  - Rate limiting: send 31 requests in rapid succession with same user JWT. Assert 31st returns 429.

---

### Task 3.4 — AI Chat Panel (Frontend)

**Service/Target:** `frontend/src/components/Panels/AIChatPanel.tsx`, `frontend/src/components/Panels/AIChatPanel.css`, `frontend/src/hooks/useAIChat.ts`, `frontend/src/api/ai.ts`
**Depends on:** 3.3 (backend endpoint must exist)
**Can run in parallel with:** Nothing (needs 3.3)

**What to build:**
A dockview panel that renders an AI chat interface — message list, text input, streaming response display. Each panel instance maintains its own independent chat session (scoped per panel).

1. **`ai.ts`** (API client module):
   - `streamChat(message: string, history: ChatMessage[]): AsyncGenerator<{token?: string, error?: string, done?: boolean}>` — calls `POST /api/ai/chat` with JWT auth. Parses the SSE response stream line by line. Yields `{token}` for each token event, `{error}` for error events, `{done: true}` for `[DONE]`.
   - Type: `ChatMessage = {role: "user" | "assistant", content: string}`

2. **`useAIChat.ts`** hook:
   - State: `messages: ChatMessage[]`, `isStreaming: boolean`, `currentResponse: string` (accumulates tokens for the in-progress assistant message)
   - `sendMessage(text: string)`: appends `{role: "user", content: text}` to messages. Sets `isStreaming: true`. Calls `streamChat(text, messages)`. As tokens arrive, appends to `currentResponse`. On `[DONE]`, appends `{role: "assistant", content: currentResponse}` to messages, resets `currentResponse`, sets `isStreaming: false`.
   - `abortController` ref: allows cancelling the in-flight request. Exposed as `cancelStream()`.
   - Each hook instance is independent (scoped per panel — no shared state).
   - Returns `{ messages, isStreaming, currentResponse, sendMessage, cancelStream }`

3. **`AIChatPanel.tsx`:**
   - Accepts `IDockviewPanelProps`
   - Layout: flex-column, full panel height
     - **Message list** (scrollable area, `flex: 1; overflow-y: auto`):
       - User messages: right-aligned, `var(--color-accent-muted)` background, `var(--radius-md)` corners, `var(--space-2) var(--space-3)` padding
       - Assistant messages: left-aligned, `var(--color-surface-3)` background, same radius/padding
       - Message text: `var(--text-md)` (14px), `var(--color-text-primary)`, `var(--leading-normal)` line height
       - Timestamp: `var(--text-xs)`, `var(--color-text-tertiary)`, below each message
       - Auto-scroll to bottom on new messages (only if user is already at bottom — respect manual scroll position)
     - **Thinking indicator** (visible when `isStreaming` and `currentResponse` is empty):
       - Three dots pulsing animation: `var(--color-text-tertiary)`, CSS `@keyframes` — each dot fades in/out offset by 200ms. Total cycle 1.2s.
       - Text: "Thinking..." in `var(--text-sm) var(--color-text-tertiary)`
     - **Streaming response** (visible when `isStreaming` and `currentResponse` has content):
       - Renders `currentResponse` progressively in the assistant message bubble style
       - Cursor indicator: `|` blinking at end of text in `var(--color-accent)`
     - **Input area** (fixed at bottom):
       - `<textarea>` auto-growing (1 line min, 6 lines max), `var(--input-bg)`, `var(--input-border)`, `var(--input-border-focus)` on focus, `var(--radius-sm)`
       - Send button: `var(--color-accent)` icon (lucide `Send`), `var(--btn-height-md)`, disabled when input empty or streaming
       - Enter sends message (without Shift). Shift+Enter inserts newline.
       - During streaming: send button changes to stop icon (lucide `Square`), clicking calls `cancelStream()`
   - Empty state (no messages): centered text "Start a conversation" in `var(--color-text-tertiary)`, icon `MessageSquare` at `var(--icon-3xl)`

4. **`AIChatPanel.css`:**
   - Panel container: `display: flex; flex-direction: column; height: 100%; background: var(--color-surface-1);`
   - Message list: `flex: 1; overflow-y: auto; padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3);`
   - User message bubble: `align-self: flex-end; max-width: 80%; background: var(--color-accent-muted); border-radius: var(--radius-md); padding: var(--space-2) var(--space-3);`
   - Assistant message bubble: `align-self: flex-start; max-width: 80%; background: var(--color-surface-3); border-radius: var(--radius-md); padding: var(--space-2) var(--space-3);`
   - Input area: `border-top: 1px solid var(--color-border-subtle); padding: var(--space-2) var(--space-3); display: flex; gap: var(--space-2); align-items: flex-end;`
   - Thinking dots keyframes and streaming cursor blink keyframes

**Acceptance criteria:**
- [ ] `AIChatPanel.tsx` renders a chat interface in the dockview panel
- [ ] User messages display right-aligned with `var(--color-accent-muted)` background
- [ ] Assistant messages display left-aligned with `var(--color-surface-3)` background
- [ ] Streaming tokens appear progressively in assistant bubble
- [ ] Thinking indicator (three dots) shows when waiting for first token
- [ ] Blinking cursor at end of streaming response
- [ ] Auto-scroll to bottom on new messages (respects manual scroll-up)
- [ ] Textarea auto-grows from 1 to 6 lines
- [ ] Enter sends, Shift+Enter inserts newline
- [ ] Send button disabled when input empty or streaming
- [ ] Stop button visible during streaming, calls `cancelStream()`
- [ ] Empty state shows "Start a conversation"
- [ ] Each panel instance has independent chat state
- [ ] No hardcoded hex values in component files

**Test contract:**
- Test file: `frontend/src/api/__tests__/ai.test.ts`
  - Mock fetch SSE response. Call `streamChat("hello", [])`. Collect yielded values. Assert at least one `{token: "..."}` and final `{done: true}`.
  - Mock fetch SSE with error event. Assert `{error: "..."}` yielded.
  - Assert fetch called with correct URL (`/api/ai/chat`), method POST, and Authorization header.
- Test file: `frontend/src/hooks/__tests__/useAIChat.test.ts`
  - Mock `streamChat`. Render hook. Assert initial `messages: []`, `isStreaming: false`.
  - Call `sendMessage("hello")`: assert `isStreaming: true`. Assert user message added to `messages`. After stream completes, assert assistant message added and `isStreaming: false`.
  - Call `cancelStream()` during streaming: assert streaming stops.
- Test file: `frontend/src/components/Panels/__tests__/AIChatPanel.test.tsx`
  - Mock `useAIChat`. Render `<AIChatPanel />` with mock dockview props. Assert empty state "Start a conversation" visible.
  - With mock messages (1 user, 1 assistant): assert both message bubbles render. Assert user message is right-aligned (check CSS class or data attribute). Assert assistant message is left-aligned.
  - With `isStreaming: true, currentResponse: ""`: assert thinking indicator dots visible.
  - With `isStreaming: true, currentResponse: "partial"`: assert streaming text "partial" visible.
  - Type "test" in textarea, press Enter: assert `sendMessage` called with "test".
  - Assert textarea is empty after send.
  - With `isStreaming: true`: assert send button shows stop icon. Click stop button: assert `cancelStream` called.
  - Assert component has `data-testid="ai-chat-panel"`.

---

### Task 3.5 — Dock Integration (Wire Panels to Dock Icons)

**Service/Target:** `frontend/src/components/Dock/Dock.tsx` (modify existing), `frontend/src/components/Dock/appRegistry.ts` (new file), `frontend/src/components/Shell/DockviewShell.tsx` (modify COMPONENTS)
**Depends on:** 3.1, 3.2, 3.4

**What to build:**
Wire the three new panel components into the dock system. Clicking a dock icon opens the corresponding panel in DockviewShell. Add a Settings placeholder icon.

1. **`appRegistry.ts`** (extracted from Dock.tsx — single source of truth):
   - Type:
     ```typescript
     interface AppDefinition {
       id: string
       label: string
       icon: LucideIcon
       componentKey: string  // maps to COMPONENTS key in DockviewShell
     }
     ```
   - Registry entries:
     ```
     { id: "terminal",  label: "Terminal",  icon: Terminal,       componentKey: "TerminalPanel" }
     { id: "files",     label: "Files",     icon: FolderTree,     componentKey: "FileTreePanel" }
     { id: "ai-chat",   label: "AI Chat",   icon: MessageSquare,  componentKey: "AIChatPanel" }
     { id: "settings",  label: "Settings",  icon: Settings,       componentKey: "SettingsPanel" }
     ```
   - Exported as `const APP_REGISTRY: AppDefinition[]`
   - Settings is a placeholder — `SettingsPanel` will be a simple "Coming in Phase 3c" panel

2. **Update `DockviewShell.tsx` COMPONENTS map:**
   - Add all new panel components:
     ```typescript
     const COMPONENTS: Record<string, React.FunctionComponent<IDockviewPanelProps>> = {
       WelcomePanel,
       TerminalPanel,
       FileTreePanel,
       AIChatPanel,
       SettingsPanel,
     }
     ```
   - Import the new components

3. **Update `Dock.tsx`:**
   - Import `APP_REGISTRY` from `./appRegistry`
   - Render one icon button per `APP_REGISTRY` entry
   - Read `dockviewApi` from `LayoutContext`
   - **Click behavior** (per Phase 2 spec, now with real panels):
     - Panel not open → `dockviewApi.addPanel({ id: app.id, component: app.componentKey, title: app.label })`
     - Panel open but not focused → `dockviewApi.getPanel(app.id)?.focus()`
     - Panel already focused → no-op
   - **Active panel tracking:**
     - Subscribe to `dockviewApi.onDidActivePanelChange` via `useEffect`
     - Track `openPanelIds: Set<string>` from `dockviewApi.panels` (read on each layout change via `onDidLayoutChange`)
     - Track `activePanelId: string | null` from active panel change events
   - **Icon states** (per design-system.md section 7 Dock Bar):
     - Default: icon `var(--color-text-secondary)`
     - Hover: `var(--color-surface-3)` bg, `var(--duration-instant)` transition
     - Active (panel open): 3px `var(--color-accent)` dot below icon, icon color `var(--color-accent)`
   - **Tooltip:** app label appears on hover after 500ms delay (simple `title` attribute is acceptable for Phase 3 — upgrade to custom tooltip in Phase 3.5-TH)
   - Dock layout: left-aligned icon group, right side shows clock (keep existing)

4. **`SettingsPanel.tsx`** (placeholder):
   - Simple centered message: "Settings — Coming in Phase 3c"
   - Uses `var(--color-text-tertiary)`, `var(--text-sm)`, lucide `Settings` icon at `var(--icon-3xl)`

**Acceptance criteria:**
- [ ] `APP_REGISTRY` has 4 entries: Terminal, Files, AI Chat, Settings
- [ ] Each registry entry has `id`, `label`, `icon`, `componentKey`
- [ ] `DockviewShell.tsx` COMPONENTS map includes all 5 panels (Welcome + 4 new)
- [ ] Dock renders 4 icon buttons (one per registry entry)
- [ ] Clicking Terminal icon: opens TerminalPanel in dockview
- [ ] Clicking Files icon: opens FileTreePanel in dockview
- [ ] Clicking AI Chat icon: opens AIChatPanel in dockview
- [ ] Clicking Settings icon: opens SettingsPanel placeholder
- [ ] Clicking already-focused panel icon: no duplicate panel created
- [ ] Clicking open-but-unfocused panel: focuses it
- [ ] Active panel icon shows 3px `var(--color-accent)` dot below
- [ ] Active panel icon color is `var(--color-accent)`
- [ ] No hardcoded hex values in component files

**Test contract:**
- Test file: `frontend/src/components/Dock/__tests__/Dock.test.tsx` (update existing)
  - Import `APP_REGISTRY`. Assert it has exactly 4 entries. Assert each entry has `id`, `label`, `icon`, `componentKey`.
  - Render `<Dock />` with mock `LayoutContext` providing mock `dockviewApi`. Assert 4 icon buttons render.
  - Click "Terminal" icon when panel not open (mock `panels` to have no "terminal" panel): assert `addPanel` called with `{id: "terminal", component: "TerminalPanel", title: "Terminal"}`.
  - Click "Terminal" icon when panel exists but not focused (mock `getPanel("terminal")` to return a panel object): assert `focus()` called.
  - Click "Terminal" icon when it is the active panel: assert `addPanel` NOT called, `focus` NOT called again (no-op).
  - Assert active panel icon has accent styling (check data attribute `data-active="true"` or CSS class).
- Test file: `frontend/src/components/Dock/__tests__/appRegistry.test.ts`
  - Import `APP_REGISTRY`. Assert array. Assert each entry has required fields. Assert `componentKey` values are valid strings.
  - Assert no duplicate `id` values in registry.

---

### Task 3.6 — Panel Persistence (COMPONENTS Registry for fromJSON)

**Service/Target:** `frontend/src/components/Shell/DockviewShell.tsx` (verify), integration test
**Depends on:** 3.5

**What to build:**
Ensure all new panel types are properly registered in the `COMPONENTS` map so that `dockviewApi.fromJSON()` can restore them when the user reloads the page. This task is primarily a verification and integration test — the COMPONENTS were added in 3.5, but this task validates the save/restore cycle works end-to-end.

1. **Verify COMPONENTS registry completeness:**
   - `COMPONENTS` map in `DockviewShell.tsx` must contain keys exactly matching the `componentKey` values from `APP_REGISTRY`: `WelcomePanel`, `TerminalPanel`, `FileTreePanel`, `AIChatPanel`, `SettingsPanel`
   - Add an import-time assertion or development-mode console warning if a registry entry references a component key not in COMPONENTS

2. **Test the save/restore cycle:**
   - Open a panel (e.g., TerminalPanel) → layout auto-saves via `onDidLayoutChange` → reload → `fromJSON` restores → TerminalPanel appears in the restored layout
   - The existing layout persistence (Phase 2) already handles the `toJSON/fromJSON` cycle. This task ensures the new panel types don't break it.

3. **Fallback behavior:**
   - If a saved layout references a component key not in COMPONENTS (e.g., future panel type from Phase 3.5 that was once opened then the user downgraded), `fromJSON` throws. The existing try/catch in `DockviewShell.tsx` already falls back to `DEFAULT_LAYOUT`. Verify this still works.

**Acceptance criteria:**
- [ ] All `componentKey` values from `APP_REGISTRY` have matching entries in `COMPONENTS`
- [ ] `DockviewShell.tsx` imports all 5 panel components (Welcome, Terminal, FileTree, AIChat, Settings)
- [ ] `api.toJSON()` serializes a layout containing TerminalPanel, FileTreePanel, and AIChatPanel
- [ ] `api.fromJSON()` restores that layout without error
- [ ] Unknown component key in saved layout triggers fallback to `DEFAULT_LAYOUT` (no crash)

**Test contract:**
- Test file: `frontend/src/components/Shell/__tests__/DockviewShell.test.tsx` (extend existing)
  - Import `APP_REGISTRY` from dock. Import `COMPONENTS` (or the component keys) from DockviewShell. Assert every `componentKey` in APP_REGISTRY exists as a key in COMPONENTS.
  - Mock `GET /api/layout` to return a layout JSON containing panels with `component: "TerminalPanel"` and `component: "FileTreePanel"`. Render DockviewShell. Assert `fromJSON` was called (spy). Assert no error thrown.
  - Mock `GET /api/layout` to return a layout JSON with `component: "NonExistentPanel"`. Render DockviewShell. Assert fallback to DEFAULT_LAYOUT (WelcomePanel renders). Assert no crash.

---

### Task 3.7 — Phase 3 Graduation Integration Test

**Service/Target:** `tests/integration/test_phase3_features.py`, `frontend/src/__tests__/phase3-graduation.test.tsx`
**Depends on:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

**What to build:**
The Phase 3 graduation test validates the complete panel flow: dock icons open real panels, panels connect to backend APIs, and layout persistence includes the new panel types.

1. **Backend integration test** (`tests/integration/test_phase3_features.py`):
   - **AI Chat endpoint tests (with real HTTP calls):**
     - Create test user, get JWT
     - `POST /api/ai/chat` with `{"message": "hello", "history": []}` and JWT → assert SSE response (`Content-Type: text/event-stream`). Read at least the first event or timeout at 5s.
     - `POST /api/ai/chat` without JWT → assert 401
     - `POST /api/ai/chat` with empty body → assert 422
   - **File tree endpoint tests (confirm still working):**
     - `GET /api/files/tree?path=/workspace` with JWT → assert 200, response has `children`
     - `GET /api/files/tree?path=../../etc/passwd` with JWT → assert 400 (path traversal blocked)
   - **Layout persistence with new panel types:**
     - `PUT /api/layout` with layout JSON containing `"component": "TerminalPanel"` → assert 200
     - `GET /api/layout` → assert layout returned matches with TerminalPanel reference intact

2. **Frontend integration test** (`frontend/src/__tests__/phase3-graduation.test.tsx`):
   - Full component integration test with MSW mocks
   - Step 1: Render `<App />` with valid JWT in sessionStorage. Assert dock renders.
   - Step 2: Assert 4 dock icons present (Terminal, Files, AI Chat, Settings).
   - Step 3: Click Terminal dock icon. Assert TerminalPanel renders (check `data-testid="terminal-panel"`).
   - Step 4: Click Files dock icon. Assert FileTreePanel renders (check `data-testid="file-tree-panel"`). Mock `/api/files/tree` to return test tree. Assert tree items render.
   - Step 5: Click AI Chat dock icon. Assert AIChatPanel renders (check `data-testid="ai-chat-panel"`). Assert "Start a conversation" empty state visible.
   - Step 6: Click Terminal dock icon again (already open). Assert no duplicate panel created. Assert terminal panel is focused.
   - Step 7: Click Settings dock icon. Assert "Settings — Coming in Phase 3c" placeholder renders.
   - This test is the definition of "Phase 3 done."

**Acceptance criteria:**
- [ ] Backend integration test passes against live compose stack
- [ ] Frontend graduation test passes all 7 steps
- [ ] `npm test` from `frontend/` reports 0 failures across all test files (Phase 2 + Phase 3)
- [ ] `pytest tests/` reports 0 failures (Phase 1 + Phase 2 + Phase 3)
- [ ] `npm run build` from `frontend/` produces a clean dist/ with no type errors (`tsc --noEmit`)
- [ ] `ruff check backend/` produces 0 errors
- [ ] All new files under 400 lines

**Test contract:**
The test files above ARE the test contract. Both test files must pass with zero failures. No skips. The graduation test is the definition of Phase 3 complete.

---

## Dependency Graph

```
Phase 2 (complete)
  ├── 3.1 Terminal Panel ──────────────────────┐
  │                                              │
  ├── 3.2 File Tree Panel ────────────────────→ 3.5 Dock Integration
  │                                              ↑
  └── 3.3 AI Chat Backend ──→ 3.4 AI Chat Panel─┘
                                                   │
                                              3.6 Panel Persistence
                                                   │
                                              3.7 Graduation Test
```

**Parallel tracks:**
- Start 3.1, 3.2, and 3.3 simultaneously (terminal, file tree, AI chat backend — no overlap)
- After 3.3 is done, start 3.4 (AI chat frontend depends on backend endpoint)
- After 3.1, 3.2, and 3.4 are done, start 3.5 (dock wiring needs all panels)
- After 3.5 is done, start 3.6 (persistence verification)
- 3.7 requires all of 3.1–3.6

---

## New Dependencies Summary

Install in `frontend/`:

```bash
# Production — xterm.js v6 + addons
npm install @xterm/xterm @xterm/addon-fit @xterm/addon-webgl @xterm/addon-web-links @xterm/addon-search
```

Install in `backend/`:

```bash
# httpx for async streaming HTTP client (if not already in requirements)
uv pip install httpx
```

No new database migrations are required for Phase 3.

---

## Design Token Enforcement

All components must use CSS custom properties from `global.css`. No hex values in `.tsx` files. Cheat sheet for Phase 3:

| Need | Token |
|------|-------|
| Panel background | `var(--color-surface-1)` |
| Terminal background | `var(--terminal-background)` → `#0A0A0D` |
| Terminal foreground | `var(--terminal-foreground)` → `#CCCCCC` |
| Terminal font | `var(--font-mono)` |
| File tree item height | `var(--sidebar-item-height)` = 28px |
| File tree hover | `var(--color-surface-3)` |
| Selected file bg | `var(--color-accent-muted)` |
| Selected file text | `var(--color-accent)` |
| Tree icon size | `var(--icon-xs)` = 12px |
| Tree icon stroke | `var(--icon-stroke-dense)` = 1px |
| Chat user bubble bg | `var(--color-accent-muted)` |
| Chat assistant bubble bg | `var(--color-surface-3)` |
| Chat text size | `var(--text-md)` = 14px |
| Input bg | `var(--input-bg)` |
| Input border | `var(--input-border)` |
| Input focus border | `var(--input-border-focus)` = `var(--color-accent)` |
| Dock active dot | `var(--color-accent)` |
| Panel border-radius | `var(--radius-none)` |
| Button radius | `var(--radius-sm)` |
| Message bubble radius | `var(--radius-md)` |
| Error text | `var(--color-error)` |
| Placeholder text | `var(--color-text-tertiary)` |

---

## Out of Scope for Phase 3

The following are explicitly NOT part of this spec. Any attempt to add them is scope creep:

- Settings panel with JSONForms (Phase 3c — only a placeholder here)
- Notification center / Sonner toasts (Phase 3d)
- Inline AI editing / Cmd+K (Phase 3e)
- Live Preview panel (Phase 3f)
- Multiple terminal tabs within a single panel (Phase 3.5 — users can open multiple Terminal panels from dock instead)
- File tree SSE live updates from `watchfiles` (Phase 3a full spec — this phase does click-to-refresh only)
- File tree inline rename, drag-and-drop, context menus, keyboard navigation (Phase 3a full spec)
- Terminal session reconnection via replay buffer (Phase 3.5 — basic reconnect is sufficient)
- Markdown rendering in chat messages (Phase 3.5 — raw text for now)
- Any Phase 3.5 features (canvas, KG, custom agents, LiveKit, etc.)

---

## Files Created or Modified (Estimated)

| File | Action |
|------|--------|
| `frontend/src/components/Panels/TerminalPanel.tsx` | CREATE |
| `frontend/src/components/Panels/TerminalPanel.css` | CREATE |
| `frontend/src/components/Panels/FileTreePanel.tsx` | CREATE |
| `frontend/src/components/Panels/FileTreePanel.css` | CREATE |
| `frontend/src/components/Panels/AIChatPanel.tsx` | CREATE |
| `frontend/src/components/Panels/AIChatPanel.css` | CREATE |
| `frontend/src/components/Panels/SettingsPanel.tsx` | CREATE |
| `frontend/src/components/Panels/__tests__/TerminalPanel.test.tsx` | CREATE |
| `frontend/src/components/Panels/__tests__/FileTreePanel.test.tsx` | CREATE |
| `frontend/src/components/Panels/__tests__/AIChatPanel.test.tsx` | CREATE |
| `frontend/src/components/Dock/appRegistry.ts` | CREATE |
| `frontend/src/components/Dock/__tests__/appRegistry.test.ts` | CREATE |
| `frontend/src/hooks/usePtyWebSocket.ts` | CREATE |
| `frontend/src/hooks/useFileTree.ts` | CREATE |
| `frontend/src/hooks/useAIChat.ts` | CREATE |
| `frontend/src/hooks/__tests__/usePtyWebSocket.test.ts` | CREATE |
| `frontend/src/hooks/__tests__/useFileTree.test.ts` | CREATE |
| `frontend/src/hooks/__tests__/useAIChat.test.ts` | CREATE |
| `frontend/src/api/files.ts` | CREATE |
| `frontend/src/api/ai.ts` | CREATE |
| `frontend/src/api/__tests__/files.test.ts` | CREATE |
| `frontend/src/api/__tests__/ai.test.ts` | CREATE |
| `frontend/src/components/Dock/Dock.tsx` | MODIFY |
| `frontend/src/components/Dock/__tests__/Dock.test.tsx` | MODIFY (or CREATE) |
| `frontend/src/components/Shell/DockviewShell.tsx` | MODIFY |
| `frontend/src/components/Shell/__tests__/DockviewShell.test.tsx` | MODIFY |
| `frontend/src/__tests__/phase3-graduation.test.tsx` | CREATE |
| `backend/app/api/ai.py` | MODIFY |
| `tests/unit/test_ai_chat.py` | CREATE |
| `tests/integration/test_phase3_features.py` | CREATE |
| `frontend/package.json` | MODIFY (add xterm deps) |

---

*End of Phase 3 spec. All tasks are grounded in ROADMAP.md sections 3a-3b, ARCHITECTURE.md, design-system.md, and BUILD_BIBLE.md. Phase 3.5+ is not planned here.*

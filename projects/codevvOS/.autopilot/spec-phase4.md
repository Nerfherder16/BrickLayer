# CodeVV OS — Build Spec (Phase 4: Settings, Notifications & Polish)

**Generated:** 2026-04-03
**Source authority:** `ROADMAP.md`, `ARCHITECTURE.md`, `docs/design-system.md`, `spec-phase3.md`
**Branch:** `autopilot/phase4-polish-20260403`
**Scope:** Phase 4 only. Covers: Settings Panel (ROADMAP 3c), Notification Center (ROADMAP 3d), Command Palette (ROADMAP 3.5-TH), Keyboard Shortcut Registry (ROADMAP 3.5-TH), Theme Toggle, and PWA manifest. Does NOT include Inline AI Editing (3e — requires CodeMirror 6), Live Preview (3f — requires dev server detection), BrickLayer sidecar (3.5-BL), or Knowledge Graph (3.5-KG). Those are Phase 5+.
**Depends on:** Phase 3 complete. DockviewShell, Dock, TerminalPanel, FileTreePanel, AIChatPanel, SettingsPanel stub, layout persistence API, `/api/ai/chat`, `/api/files/*` all functional. 101 frontend tests passing.

---

## Goal

Fill in the SettingsPanel stub, add real-time notification delivery (Sonner toasts + history dropdown), wire a global command palette (Cmd+Shift+K), add a keyboard shortcut registry, implement the dark/light theme toggle, and ship a PWA manifest so the OS can be installed on kiosk devices. All within the existing tech stack — no new runtime dependencies beyond what ROADMAP specifies.

## Architecture

### What changes
- **SettingsPanel.tsx** — replace placeholder with JsonForms rendering Pydantic-generated schema
- **NotificationCenter** — new Dock-area dropdown + Sonner toast delivery; backed by `/api/notifications` endpoints (already planned in ROADMAP 1d — will be built in Tasks 4.1–4.2)
- **CommandPalette** — new global overlay (Framer Motion); shortcut: Cmd+Shift+K
- **useKeyboardShortcuts** — global registry singleton, per-context overrides
- **Theme toggle** — CSS class swap on `<html>`, persisted to user settings
- **PWA** — `vite-plugin-pwa` + `public/manifest.webmanifest`, service worker for offline shell

### What stays the same
- DockviewShell, AppRegistry, all Phase 3 panels
- All Phase 0–3 backend endpoints
- Design token system (`global.css`)

### Key files
| Role | Path |
|------|------|
| Settings panel impl | `frontend/src/components/Panels/SettingsPanel.tsx` |
| Notifications backend | `backend/app/api/notifications.py` |
| Notification store | `frontend/src/stores/notificationStore.ts` |
| Notification center | `frontend/src/components/Dock/NotificationCenter.tsx` |
| Command palette | `frontend/src/components/CommandPalette/CommandPalette.tsx` |
| Shortcut registry | `frontend/src/hooks/useKeyboardShortcuts.ts` |
| Theme context | `frontend/src/contexts/ThemeContext.tsx` |
| Vite config (PWA) | `frontend/vite.config.ts` |
| PWA manifest | `frontend/public/manifest.webmanifest` |

---

## Tasks

### Task 4.1 — Notifications Backend (API + DB migration)

**Description:** Add the `notifications` table to PostgreSQL and implement the two notification endpoints from ROADMAP 1d. This is a backend-only task.

Create `migrations/versions/002_notifications.py` adding:
```sql
notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  user_id UUID NOT NULL REFERENCES users(id),
  type TEXT NOT NULL,           -- 'mention', 'system', 'agent_complete', 'comment'
  title TEXT NOT NULL,
  body TEXT,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
)
```
Enable RLS. Policy: `user_id = current_user_id()` (same pattern as existing tables). Add index `(tenant_id, user_id, created_at DESC)` and `(tenant_id, user_id, read)`.

Implement in `backend/app/api/notifications.py`:
- `GET /api/notifications?limit=50&before_id=<uuid>` — cursor-paginated; returns `{items: [...], has_more: bool}`. Default limit 50.
- `PATCH /api/notifications/{id}/read` — set `read = true`, return 204.
- `POST /api/notifications` — internal endpoint (requires `BL_INTERNAL_SECRET` header, NOT user JWT) for agent/system to create notifications.

Both user-facing endpoints require JWT. `POST /api/notifications` requires `BL_INTERNAL_SECRET`.

**Mode:** python
**Files:**
- Implementation: `backend/app/api/notifications.py`, `migrations/versions/002_notifications.py`
- Tests: `tests/unit/test_notifications_api.py`, `tests/migrations/test_002_notifications.py`

**Test strategy:**
- Insert 60 notifications for user A. GET with default limit → 50 returned, `has_more: true`. GET with `before_id` of last item → remaining 10. PATCH read on one → 204, subsequent GET shows `read: true`. POST as user (no BL_INTERNAL_SECRET) → 403. User B cannot see user A's notifications (RLS).
- Migration: run up, assert table + indexes exist, run down, assert table gone.

**Parallel:** no — Task 4.2 depends on this

---

### Task 4.2 — Notification Store + Sonner Toasts (Frontend)

**Description:** Wire real-time notification delivery to the frontend. Install `sonner` (zero-deps toast library, ROADMAP 3d). Create a Zustand store for notification state. Poll `GET /api/notifications` on mount (no SSE yet — SSE push is Phase 5). Render toasts on new notifications.

1. Install `sonner` into `frontend/package.json`
2. Add `<Toaster />` to `App.tsx` root (or `DockviewShell.tsx` — outside the panel tree)
3. Create `frontend/src/stores/notificationStore.ts` with Zustand:
   - State: `items: Notification[]`, `unread_count: number`, `loading: boolean`
   - Actions: `fetchRecent()`, `markRead(id)`, `addToast(notification)` (fires Sonner)
   - `fetchRecent()` calls `GET /api/notifications?limit=20`, merges with local state
4. Create `frontend/src/hooks/useNotifications.ts` — thin hook wrapping the store, starts polling on mount (30s interval via `setInterval`)
5. Create `frontend/src/components/Dock/NotificationCenter.tsx` — bell icon button in Dock with `unread_count` badge. Click opens a dropdown showing last 20 notifications with mark-as-read. Uses `framer-motion` `AnimatePresence` for open/close.

**Mode:** typescript
**Files:**
- Implementation: `frontend/src/stores/notificationStore.ts`, `frontend/src/hooks/useNotifications.ts`, `frontend/src/components/Dock/NotificationCenter.tsx`
- Tests: `frontend/src/stores/__tests__/notificationStore.test.ts`, `frontend/src/components/Dock/__tests__/NotificationCenter.test.tsx`

**Test strategy:**
- Store: mock `GET /api/notifications` via MSW, call `fetchRecent()`, assert store state updated. Call `markRead(id)` → MSW patches → store flips item to `read: true`.
- NotificationCenter: renders bell with `data-testid="notification-bell"`. With 3 unread, badge shows "3". Click bell → dropdown opens with notification items. Click "Mark all read" → all items read.

**Parallel:** no — depends on Task 4.1 (needs real API contract); can mock MSW handlers once 4.1 types are finalized

---

### Task 4.3 — Settings Panel (JsonForms + Pydantic Schema)

**Description:** Replace the SettingsPanel stub with a real settings UI auto-rendered by `@jsonforms/react` from the Pydantic-generated `GET /api/settings/schema` endpoint (built in ROADMAP 1d Task 1.14, assumed complete from Phase 1 build).

1. Install `@jsonforms/react`, `@jsonforms/core`, `@jsonforms/vanilla-renderers` into `frontend/package.json`
2. Create `frontend/src/hooks/useSettings.ts`:
   - Fetches schema from `GET /api/settings/schema`
   - Fetches current values from `GET /api/settings/user`
   - Saves via `PUT /api/settings/user`
   - State: `schema`, `uiSchema`, `data`, `loading`, `saving`
3. Replace `SettingsPanel.tsx` placeholder with full implementation:
   - Renders `<JsonForms schema={schema} data={data} onChange={handleChange} renderers={vanillaRenderers}>`
   - "Save" button triggers `PUT /api/settings/user`
   - Theme toggle section (see Task 4.5 for ThemeContext) — rendered as a custom cell renderer so it's not just a boring checkbox
   - Admin-only section rendered if user role is `admin` (fetched from JWT claims)
   - Loading spinner while schema fetches; error state if schema endpoint returns non-200
4. Apply Obsidian Shell design tokens to the JsonForms output via CSS overrides in `SettingsPanel.css`

**Mode:** typescript
**Files:**
- Implementation: `frontend/src/components/Panels/SettingsPanel.tsx`, `frontend/src/components/Panels/SettingsPanel.css`, `frontend/src/hooks/useSettings.ts`
- Tests: `frontend/src/components/Panels/__tests__/SettingsPanel.test.tsx`, `frontend/src/hooks/__tests__/useSettings.test.ts`

**Test strategy:**
- `useSettings`: MSW handler for schema and user settings. Assert schema loads, data loads. Simulate change + save → PATCH called with new data.
- `SettingsPanel`: renders `data-testid="settings-panel"`. Loading state shows spinner (`data-testid="settings-loading"`). After load, JsonForms renders with data. Save button calls `PUT /api/settings/user`. Error state shows `data-testid="settings-error"`.

**Parallel:** yes — independent of Tasks 4.1, 4.2 (different API endpoint; different component)

---

### Task 4.4 — Keyboard Shortcut Registry

**Description:** Create a global keyboard shortcut registry. Components register shortcuts; the registry handles conflicts and context priority (e.g., CodeMirror shortcuts only fire when editor has focus; global shortcuts fire everywhere). Per ROADMAP 3.5-TH: command palette is `Cmd+Shift+K`, inline AI edit is `Cmd+K` (CodeMirror-context-only, Phase 5).

1. Create `frontend/src/hooks/useKeyboardShortcuts.ts`:
   - `registerShortcut(id, keybinding, handler, context?)` — adds to registry
   - `unregisterShortcut(id)` — removes (called from `useEffect` cleanup)
   - `getShortcuts()` — returns all registered shortcuts (used by command palette)
   - Context: `'global'` | `'editor'` | `'terminal'` — only global fires everywhere; others fire only when their container has focus
   - Keybinding format: `'cmd+shift+k'`, `'ctrl+p'`, etc. (platform-normalized — `cmd` = `⌘` on Mac, `ctrl` on Linux/Windows)
   - Global listener on `window` `keydown`; checks active focus context before firing
2. Create `frontend/src/contexts/KeyboardContext.tsx` — provides `registerShortcut`, `unregisterShortcut`, `getShortcuts` via React context
3. Pre-register default shortcuts:
   - `cmd+shift+k` → open command palette (registered in `App.tsx`)
   - `cmd+,` → open settings panel (registered in `App.tsx`)
   - `cmd+\`` → focus terminal panel
4. Add `KeyboardContext.Provider` to `App.tsx` wrapping the whole app

**Mode:** typescript
**Files:**
- Implementation: `frontend/src/hooks/useKeyboardShortcuts.ts`, `frontend/src/contexts/KeyboardContext.tsx`
- Tests: `frontend/src/hooks/__tests__/useKeyboardShortcuts.test.ts`

**Test strategy:**
- Register a global shortcut. Simulate `keydown` event with matching keys → handler called. Unregister → handler NOT called. Register two shortcuts for same keybinding in same context → second registration throws or warns. Context filtering: `'editor'` shortcut doesn't fire when focus is not in editor container.

**Parallel:** yes — independent of Tasks 4.1, 4.2, 4.3

---

### Task 4.5 — Command Palette (Cmd+Shift+K)

**Description:** Global command palette overlay. Opens with Cmd+Shift+K (via shortcut from Task 4.4). Fuzzy searches over: all keyboard-registered shortcuts + dock app launcher actions. Uses Framer Motion for open/close animation.

1. Create `frontend/src/components/CommandPalette/CommandPalette.tsx`:
   - Full-screen translucent backdrop (click outside → close)
   - Centered modal card (Obsidian Shell glass style — `backdrop-filter: blur(8px)`, `var(--color-surface-2)` background)
   - Text input with autofocus, `data-testid="command-palette-input"`
   - Reads registered shortcuts from `KeyboardContext` + app registry from `APP_REGISTRY`
   - Fuzzy filter: match input against command `label` and `description` (simple substring or regex, no external lib)
   - Keyboard navigation: `ArrowUp`/`ArrowDown` to move through results, `Enter` to execute, `Escape` to close
   - Each result row: icon + label + keybinding hint (right-aligned)
   - Empty state: "No commands found" when search returns 0 results
2. Create `frontend/src/components/CommandPalette/useCommandPalette.ts` — open/close state, result list computed from registry
3. Mount `<CommandPalette />` in `App.tsx` (alongside `<Toaster />` — outside the panel tree), shown/hidden via `useCommandPalette` state
4. Register `cmd+shift+k` shortcut in `App.tsx` → `commandPalette.open()`

**Mode:** typescript
**Files:**
- Implementation: `frontend/src/components/CommandPalette/CommandPalette.tsx`, `frontend/src/components/CommandPalette/useCommandPalette.ts`
- Tests: `frontend/src/components/CommandPalette/__tests__/CommandPalette.test.tsx`

**Test strategy:**
- Render `CommandPalette` in open state. `data-testid="command-palette-input"` exists and is focused. Type "term" → results filtered to terminal-related commands. `ArrowDown` moves selection. `Enter` on selected item calls handler and closes. `Escape` closes. Click backdrop closes. Empty search shows full list.

**Parallel:** yes — independent of Tasks 4.1, 4.2, 4.3; depends on Task 4.4 (needs KeyboardContext)

---

### Task 4.6 — Theme Toggle (Dark/Light Mode)

**Description:** Wire the dark/light mode toggle per ROADMAP 3.5-TH. The CSS already has `.theme-light` overrides in `global.css` (Phase 0.5). Toggle adds/removes `theme-light` class on `<html>`. Persist to `localStorage` and optionally to user settings.

1. Create `frontend/src/contexts/ThemeContext.tsx`:
   - State: `theme: 'dark' | 'light'`
   - `toggleTheme()` — flips class on `document.documentElement`, saves to `localStorage`
   - On mount: read from `localStorage` (`theme-dark` or `theme-light`), default `dark`
   - Provide via React context
2. Add `ThemeContext.Provider` to `App.tsx`
3. Add `ThemeToggle` button to the Dock (sun/moon icon via Lucide)
4. In `SettingsPanel.tsx` (Task 4.3) — connect the theme section to `ThemeContext` instead of a raw checkbox

**Mode:** typescript
**Files:**
- Implementation: `frontend/src/contexts/ThemeContext.tsx`
- Tests: `frontend/src/contexts/__tests__/ThemeContext.test.tsx`

**Test strategy:**
- Default theme is `dark` — `document.documentElement` does NOT have `theme-light` class. Call `toggleTheme()` → class added. Call again → removed. Reload (simulate by re-reading `localStorage`) → theme persists. `ThemeToggle` button click fires `toggleTheme`.

**Parallel:** yes — independent of all other tasks in this phase

---

### Task 4.7 — PWA Manifest + Service Worker

**Description:** Make the app installable as a PWA per ROADMAP 3.5-TH requirements. The kiosk Chromium can install the app via Add to Home Screen. Use `vite-plugin-pwa` (Workbox-based).

1. Install `vite-plugin-pwa` as a devDependency
2. Create `frontend/public/manifest.webmanifest`:
   ```json
   {
     "name": "CodeVV OS",
     "short_name": "CodeVV",
     "start_url": "/",
     "display": "standalone",
     "background_color": "#0f0d1a",
     "theme_color": "#4F87B3",
     "icons": [...]
   }
   ```
3. Add placeholder icons: `frontend/public/icons/icon-192.png` and `icon-512.png` (can be solid-color placeholders for now — real icons in Phase 5 design pass)
4. Configure `vite-plugin-pwa` in `frontend/vite.config.ts`:
   - `registerType: 'autoUpdate'`
   - Precache: `index.html`, CSS bundle, JS bundle, font files
   - `workbox.navigateFallback: '/index.html'` (SPA)
   - `workbox.runtimeCaching` for `/api/*` → NetworkFirst (always try network, fallback to cache)
5. Add `<meta name="theme-color" content="#4F87B3">` and PWA `<link>` tags to `index.html`

**Mode:** devops
**Files:**
- Implementation: `frontend/vite.config.ts`, `frontend/public/manifest.webmanifest`, `frontend/public/icons/icon-192.png`, `frontend/public/icons/icon-512.png`
- Tests: `tests/unit/test_pwa_config.py`

**Test strategy:**
- Python test: parse `manifest.webmanifest` as JSON. Assert `name`, `short_name`, `start_url`, `display: "standalone"`, `theme_color: "#4F87B3"` are set. Assert icon files exist. Parse `vite.config.ts` as text: assert `vite-plugin-pwa` is imported, assert `registerType: 'autoUpdate'` appears.
- Build test: run `npm run build` in CI, assert `dist/sw.js` exists (service worker generated by Workbox).

**Parallel:** yes — independent of all other tasks

---

### Task 4.8 — Phase 4 Graduation Test

**Description:** Integration smoke test verifying all Phase 4 components work together in the rendered app.

Write a Vitest test (using `@testing-library/react`) that renders the full `App` component with all providers (`ThemeContext`, `KeyboardContext`, notification store, MSW handlers for all APIs). Assert:

1. `SettingsPanel` opens from Dock click → `data-testid="settings-panel"` visible
2. Command palette opens on Cmd+Shift+K → `data-testid="command-palette-input"` focused
3. Notification bell shows in Dock → `data-testid="notification-bell"` rendered
4. Theme toggle flips `theme-light` class on `<html>`
5. All prior Phase 3 panels still render without regression (render TerminalPanel, FileTreePanel, AIChatPanel — check for their `data-testid` attributes)

**Mode:** default
**Files:**
- Tests: `frontend/src/test/phase4-graduation.test.tsx`

**Test strategy:** Full app render with all providers. Assert data-testid elements for each Phase 4 feature. Assert no console errors during render. All assertions must pass with `vitest run`.

**Parallel:** no — graduation gate; depends on Tasks 4.1–4.7

---

## Tech Stack

- **Language:** TypeScript 5.0+, Python 3.12
- **Frontend framework:** React 19, Vite 6
- **State:** Zustand (notification store) + React context (Theme, Keyboard)
- **UI:** Tailwind v4 (token-based, no hardcoded hex), Lucide icons, Framer Motion 12
- **Forms:** @jsonforms/react + @jsonforms/vanilla-renderers
- **Toasts:** sonner
- **PWA:** vite-plugin-pwa (Workbox)
- **Backend:** FastAPI, SQLAlchemy 2 async, Alembic
- **Test runner (frontend):** `npm test` (`vitest run`)
- **Test runner (backend):** `pytest tests/`
- **Type check:** `npx tsc --noEmit`
- **Lint:** `npx eslint src/` (frontend), `ruff check backend/` (backend)

## Agent Hints

- **Test command (frontend):** `cd projects/codevvOS/frontend && npm test`
- **Test command (backend):** `cd projects/codevvOS && pytest tests/`
- **Type check:** `cd projects/codevvOS/frontend && npx tsc --noEmit`
- **Lint (frontend):** `cd projects/codevvOS/frontend && npx eslint src/`
- **Lint (backend):** `cd projects/codevvOS && ruff check backend/`
- **Key shared files:** `frontend/src/styles/global.css` (design tokens — all components use CSS vars from here), `frontend/src/components/Dock/appRegistry.ts` (add NotificationCenter to Dock), `frontend/src/App.tsx` (provider wrapping, shortcut registration)
- **Platform:** Linux (WSL2)
- **Design rule:** NEVER hardcode hex values in component files — use `var(--color-*)` tokens only
- **JsonForms install note:** `@jsonforms/react` depends on React ≤18 in its peer deps — use `--legacy-peer-deps` when installing. This is a known issue; the library works fine with React 19 at runtime.

## Known Issues

- `@jsonforms/react` peer dep lists React ≤18: use `npm install --legacy-peer-deps` — addressed in Task 4.3 description
- `vite-plugin-pwa` requires Vite 5+; current project uses Vite 6 — compatible, no issue
- Sonner: `<Toaster />` must be placed OUTSIDE the dockview layout tree or it will be removed when panels reload from JSON — addressed in Task 4.2 (mount in `App.tsx` at root)

## Constraints

- Do NOT add CodeMirror, Yjs, or y-websocket — those are Phase 5 (Inline AI Editing)
- Do NOT implement SSE push for notifications — polling (30s interval) is sufficient for Phase 4; SSE push is Phase 5
- Do NOT build the Knowledge Graph panel, BrickLayer Agent Mode, or Personal AI Assistant — those are Phase 5+
- Settings panel must render from the Pydantic schema — do NOT hardcode fields
- All design tokens from `global.css` — no hardcoded colors anywhere

## Definition of Done

- All 8 tasks complete with passing tests
- `npx tsc --noEmit` → 0 errors
- `npx eslint src/` → 0 warnings (max-warnings=0)
- `pytest tests/` → 0 failures
- Phase 4 graduation test (`phase4-graduation.test.tsx`) → passes
- PWA build test: `npm run build` produces `dist/sw.js`
- No regressions — all Phase 3 tests still pass

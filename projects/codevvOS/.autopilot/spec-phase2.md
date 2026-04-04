# CodeVV OS — Build Spec (Phase 2: Frontend Shell)

**Generated:** 2026-04-02
**Source authority:** `ROADMAP.md`, `ARCHITECTURE.md`, `docs/design-system.md`, `docs/superpowers/specs/codevvos-experience-design.md`, `frontend/package.json`, `frontend/src/styles/global.css`
**Scope:** Phase 2 only. No Phase 3 features (no file browser, no terminal, no editor, no canvas, no AI chat, no KG). Phase 2 graduation test: app boots → login screen → user logs in → dockview shell renders with dock.
**Depends on:** Phase 0 + Phase 1 complete (258 tests passing).

---

## Project Summary

Phase 2 converts the scaffold from Phase 0/1 into a living frontend. The output is an OS-like browser shell with three components: (1) a full-screen login screen styled after macOS's user-picker, (2) a `dockview-react` tiling panel manager as the main desktop surface, and (3) a persistent 48px dock bar outside the layout tree. The shell uses the "Obsidian Shell" design system already installed in `frontend/src/styles/global.css`. All CSS custom properties are already declared — no design tokens will be hardcoded in components.

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

**Parallel opportunities are called out explicitly.** Tasks 2.1 and 2.2 run in parallel (frontend bootstrap vs. backend API). After 2.1 completes, tasks 2.3 and 2.5 run in parallel (dockview shell vs. login screen — they are independent). Task 2.6 depends on 2.5. Task 2.7 depends on 2.4. Task 2.8 is the final integration gate.

---

## Phase 2 — Frontend Shell

> All tasks produce production code with real tests. Design tokens from `frontend/src/styles/global.css` are used throughout — never hardcode hex values in component files.

---

### Task 2.1 — Frontend App Bootstrap

**Service/Target:** `frontend/` (vite.config.ts, src/main.tsx, src/App.tsx, src/styles/)
**Depends on:** Phase 0 + Phase 1 complete (no Phase 2 tasks)
**Can run in parallel with:** Task 2.2

**What to build:**
Bootstrap the React 19 application shell so the Vite dev server renders something with correct design tokens applied. Specifically:

1. **Install production dependencies** into `frontend/package.json`:
   - `dockview-react@5.2.0` — panel manager (pinned, per Technology Decisions table)
   - `framer-motion` — dock animations, login transitions
   - `lucide-react` — icon set per design-system.md §9
   - Move `react` and `react-dom` from `devDependencies` to `dependencies` (required for production bundle)

2. **Install Tailwind v4 Vite integration:**
   - `@tailwindcss/vite` and `tailwindcss` as devDependencies
   - `@tailwindcss/postcss` is NOT needed — Tailwind v4 uses the Vite plugin directly

3. **Update `frontend/vite.config.ts`:**
   - Add `@vitejs/plugin-react` (install as devDependency)
   - Add `@tailwindcss/vite` plugin
   - Add path alias: `@` → `src/`
   - Set `build.outDir` to `dist`
   - Configure jsdom environment passthrough (vitest already configured in its own config)

4. **Create `frontend/src/main.tsx`:**
   - Mount `<App />` to `#root`
   - Import `./styles/global.css`
   - Import `./styles/fonts.css` (self-hosted fonts from Phase 0.6)
   - React 19 `createRoot` pattern — no `ReactDOM.render`
   - `StrictMode` wrapper

5. **Create `frontend/src/App.tsx`:**
   - Minimal placeholder: renders a `<div>` with `bg-[var(--color-base)] text-[var(--color-text-primary)]` applying base styles, containing `<p>CodeVV OS loading...</p>`
   - Imports `dockview-react/dist/styles/dockview.css` (dockview's own stylesheet — required for correct panel rendering)
   - No routing yet (that is Task 2.6)

6. **Create `frontend/index.html`:**
   - Standard Vite entry point with `<div id="root">` and `<script type="module" src="/src/main.tsx">`
   - `lang="en"`, `meta charset="UTF-8"`, `meta viewport` — standard HTML5 shell
   - Dark background color in `<head>` style to prevent flash: `background-color: #0D160B`

**Acceptance criteria:**
- [ ] `npm run dev` starts without errors
- [ ] `npm run build` produces a dist/ directory without errors
- [ ] `npm test` runs with zero test failures (existing Phase 0 tests still pass)
- [ ] `dockview-react`, `framer-motion`, `lucide-react` are in `dependencies` (not devDependencies)
- [ ] `react` and `react-dom` are in `dependencies`
- [ ] `@tailwindcss/vite` and `tailwindcss` are in `devDependencies`
- [ ] `vite.config.ts` has React plugin, Tailwind plugin, and `@` path alias
- [ ] `src/main.tsx` exists with `createRoot` and `StrictMode`
- [ ] `src/App.tsx` exists, imports dockview CSS
- [ ] `index.html` exists at `frontend/` root
- [ ] `global.css` is imported and design tokens resolve (body background is `#0D160B` in browser)
- [ ] No hardcoded hex values in any `.tsx` or `.ts` source file

**Test contract:**
- Test file: `frontend/src/__tests__/App.test.tsx`
- Test: render `<App />` with React Testing Library, assert document body has non-zero height (proves mount worked without crash). Assert no error is thrown on render (pure smoke test).
- Test: import `dockview-react` and assert the module exports `DockviewReact` — verifies the package is installed and importable.
- Run: `npm test` from `frontend/` — must report 0 failures.

---

### Task 2.2 — Layout Persistence Backend API

**Service/Target:** `backend/app/api/layout.py`, new Alembic migration `002_feature_tables.py`
**Depends on:** Phase 1 tasks 1.4 (core schema), 1.5 (session), 1.6 (JWT auth)
**Can run in parallel with:** Task 2.1

**What to build:**
Create the backend API for persisting dockview layout JSON per user, and the database table that backs it. The layout schema must include a version field from day one (ROADMAP 0d time bomb — schema versioning from the start).

1. **Alembic migration `002_feature_tables.py`:**
   - Table: `user_layouts` — columns: `id` (UUID), `user_id` (FK to `users.id`), `tenant_id` (FK to `tenants.id`), `layout_json` (JSONB), `layout_version` (INTEGER, default 1), `updated_at` (TIMESTAMP with timezone, auto-updated)
   - Unique constraint: `(user_id, tenant_id)` — one layout per user per tenant
   - RLS enabled on `user_layouts` (users can only see their own layout)
   - RLS policy: `current_setting('app.current_tenant_id')`
   - `downgrade()` drops the table (no `pass`)

2. **SQLAlchemy model** `backend/app/models/layout.py`:
   - `UserLayout` model mapping to `user_layouts` table
   - JSONB column type for `layout_json`

3. **FastAPI endpoints** `backend/app/api/layout.py`:
   - `GET /api/layout` — returns current user's layout or `null` if no saved layout exists yet. Response: `{"layout_version": int, "layout": dict | null}`
   - `PUT /api/layout` — accepts `{"layout_version": int, "layout": dict}`, upserts (INSERT ON CONFLICT UPDATE) for the current user. Returns 200 on success.
   - Both endpoints require JWT auth. Extract `user_id` and `tenant_id` from the verified JWT.
   - Layout version mismatch handling: if client sends `layout_version` < 1, return 422 with message "Unsupported layout version".

**Acceptance criteria:**
- [ ] Migration `002_feature_tables.py` exists with `user_layouts` table
- [ ] JSONB column type used for `layout_json`
- [ ] `layout_version` column defaults to 1
- [ ] RLS enabled and policy restricts to matching `tenant_id`
- [ ] Unique constraint on `(user_id, tenant_id)`
- [ ] `downgrade()` drops `user_layouts` completely (no pass)
- [ ] `GET /api/layout` returns `{"layout_version": null, "layout": null}` when no layout saved
- [ ] `PUT /api/layout` saves layout and returns 200
- [ ] `GET /api/layout` after `PUT` returns the saved layout
- [ ] `PUT /api/layout` with `layout_version: 0` returns 422
- [ ] Both endpoints return 401 without valid JWT

**Test contract:**
- Test file: `tests/migrations/test_002_feature_tables.py`
  - Run migration against test Postgres. Assert `user_layouts` table exists. Assert `layout_version` column has default 1. Assert RLS is enabled. Assert unique constraint exists. Run downgrade, assert table dropped.
- Test file: `tests/unit/test_layout_api.py`
  - `GET /api/layout` with no saved layout: assert `{"layout_version": null, "layout": null}`.
  - `PUT /api/layout` with `{"layout_version": 1, "layout": {"orientation": "HORIZONTAL"}}`: assert 200.
  - `GET /api/layout` after PUT: assert layout matches.
  - `PUT /api/layout` with `layout_version: 0`: assert 422.
  - `GET /api/layout` without JWT: assert 401.
  - `PUT /api/layout` without JWT: assert 401.
  - Cross-user isolation: PUT as user A, GET as user B (different user, same tenant) — assert B gets null layout (RLS).

---

### Task 2.3 — Dockview Desktop Shell

**Service/Target:** `frontend/src/components/Shell/DockviewShell.tsx`, `frontend/src/contexts/LayoutContext.tsx`
**Depends on:** 2.1, 2.2
**Blocked by:** 2.2 (cannot persist layout without the API)

**What to build:**
The main desktop shell using `dockview-react@5.2.0`. This is the post-login surface that fills the screen. The dock bar (Task 2.4) will be rendered outside this component — the shell takes up all available space minus the 48px dock height.

1. **`DockviewShell.tsx`:**
   - Renders `<DockviewReact />` filling `calc(100vh - 48px)` (leaves room for dock at bottom)
   - `onReady` callback receives the `DockviewApi` — stored in `LayoutContext`
   - On mount: calls `GET /api/layout`, calls `api.fromJSON()` with saved layout if present, wrapped in `try/catch` — on any error, falls back to `DEFAULT_LAYOUT`
   - On layout change (`api.onDidLayoutChange`): debounce 1000ms, then calls `PUT /api/layout` with `{version: 1, layout: api.toJSON()}`
   - `DEFAULT_LAYOUT` is a hardcoded minimum layout: one panel titled "Welcome" with a `WelcomePanel` component
   - React 19 StrictMode compatible: no double-initialization bugs (dockview v5 is React 19 safe)
   - Panel background: `var(--color-surface-1)` via dockview theme override CSS
   - No `border-radius` on panel frames — `var(--radius-none)` per design-system.md §5 strict rules

2. **`WelcomePanel.tsx`** (placeholder panel for Day 1):
   - Displays a centered message: "Welcome to CodeVV OS. Open an app from the dock below."
   - Uses design tokens: `var(--color-text-secondary)`, `var(--text-sm)`

3. **`LayoutContext.tsx`:**
   - React context that holds `dockviewApi: DockviewApi | null`
   - `setDockviewApi` setter
   - Consumed by the Dock (Task 2.4) to call `api.addPanel()` and `api.getPanel()`

4. **Dockview CSS theming:**
   - Create `frontend/src/styles/dockview-theme.css`
   - Override dockview CSS variables to use shell tokens:
     - Panel background → `var(--color-surface-1)`
     - Panel header background → `var(--color-surface-2)`
     - Tab active border color → `var(--color-accent)` (2px top)
     - Tab inactive text → `var(--color-text-secondary)`
     - Separator/resize handle → `var(--color-border-muted)`
   - Import in `App.tsx` after `dockview.css`

**Acceptance criteria:**
- [ ] `DockviewShell.tsx` renders `<DockviewReact />` without errors
- [ ] Shell height is `calc(100vh - 48px)` — never full viewport (dock space reserved)
- [ ] `onReady` stores `DockviewApi` in `LayoutContext`
- [ ] On mount, `GET /api/layout` is called; if layout present, `api.fromJSON()` is used
- [ ] `fromJSON()` is wrapped in try/catch; corrupt JSON falls back to `DEFAULT_LAYOUT`
- [ ] `DEFAULT_LAYOUT` includes at least one panel (`WelcomePanel`)
- [ ] `api.toJSON()` called on layout change, debounced 1000ms, saved via `PUT /api/layout`
- [ ] Saved layout includes `{version: 1, layout: ...}` wrapper
- [ ] Panel frames have no border-radius (`var(--radius-none)`)
- [ ] Panel header background is `var(--color-surface-2)`
- [ ] Active tab has 2px `var(--color-accent)` top border
- [ ] No hardcoded color values in any component file

**Test contract:**
- Test file: `frontend/src/components/Shell/__tests__/DockviewShell.test.tsx`
  - Mock `GET /api/layout` via MSW to return `{layout_version: null, layout: null}`.
  - Render `<DockviewShell />` wrapped in `LayoutContext`. Assert the `WelcomePanel` text appears ("Welcome to CodeVV OS"). Assert no error is thrown.
  - Mock `GET /api/layout` to return a valid layout JSON. Assert `fromJSON` is called (spy on `DockviewApi.fromJSON`).
  - Mock `GET /api/layout` to return a corrupted JSON (`{layout: "not-valid"}`). Assert the component still renders (fallback to DEFAULT_LAYOUT, no crash).
  - Test layout persistence: trigger a layout change event on the mock `DockviewApi`. After 1000ms, assert `PUT /api/layout` was called with `{version: 1, layout: ...}`.
  - Test context: after render, assert `LayoutContext` value has a non-null `dockviewApi`.

---

### Task 2.4 — Dock / Taskbar

**Service/Target:** `frontend/src/components/Dock/Dock.tsx`, `frontend/src/registry/appRegistry.ts`
**Depends on:** 2.3 (needs `LayoutContext`)

**What to build:**
The persistent 48px dock bar that sits at the screen bottom, outside the dockview layout tree. It is a sibling to `DockviewShell` in the DOM, not a child panel.

1. **`appRegistry.ts`:**
   - Type: `AppDefinition { id: string; label: string; icon: LucideIcon; panelComponent: React.ComponentType }`
   - Initial registry (Phase 2 only — panels that exist by Phase 2):
     ```
     { id: "welcome",      label: "Welcome",    icon: LayoutDashboard, panelComponent: WelcomePanel }
     ```
   - Exported as a `const APP_REGISTRY: AppDefinition[]`
   - Additional apps will be added in Phase 3 (file browser, terminal, etc.) — do not add Phase 3 panels now

2. **`Dock.tsx`:**
   - Full-width bar, `height: var(--dock-height)` (48px per design-system.md §7 component tokens)
   - Background: `var(--dock-bg)` → `var(--color-surface-2)`
   - Top border: `1px solid var(--color-border-subtle)`
   - Position: `fixed bottom-0 left-0 right-0` — always on top, never inside dockview
   - `z-index: 100` to stay above dockview panels
   - Three zones separated by 1px `var(--color-border-subtle)` vertical dividers:
     - **Left zone:** App launcher icons from `APP_REGISTRY`
     - **Center zone:** Workspace indicator chip (static in Phase 2 — shows "Default")
     - **Right zone:** System clock (HH:MM, updates every minute), User avatar placeholder
   - Icon containers: 36×36px, `var(--radius-sm)`, 6px padding, 4px gap between icons
   - Reads `dockviewApi` from `LayoutContext`

3. **Icon states (see design-system.md §7 Dock Bar and experience-design.md §31):**
   - **Default:** icon `var(--color-text-secondary)`, no background
   - **Hover:** `var(--color-surface-3)` bg, 100ms `var(--ease-default)`, icon `var(--color-text-primary)`
   - **Active (panel open):** 3px `var(--color-accent)` dot centered below the icon, icon color `var(--color-accent)`
   - **Bounce-in** (when app panel first opens): Framer Motion `scale` animation — `0.8 → 1.1 → 1.0` over 200ms, `ease: var(--ease-spring)` equivalent in Framer Motion (`type: "spring", stiffness: 500, damping: 25`)

4. **Click behavior (per experience-design.md §31):**
   - Panel already open + focused → do nothing (or brief panel-tab pulse)
   - Panel open but not focused → `dockviewApi.getPanel(id)?.focus()`
   - Panel closed → `dockviewApi.addPanel({ id, component: appDef.panelComponent, title: appDef.label })`
   - Determine active state via `dockviewApi.onDidActivePanelChange` subscription — track which panel IDs are open

5. **Active panel tracking:**
   - Subscribe to `dockviewApi.onDidLayoutChange` in a `useEffect` to get the list of open panel IDs
   - Active (focused) panel tracked via `dockviewApi.onDidActivePanelChange`
   - Store both sets in local state: `openPanelIds: Set<string>`, `activePanelId: string | null`

6. **Tooltip:**
   - Appears above icon after 500ms hover delay
   - Dark tooltip: `var(--color-surface-5)` bg, `var(--shadow-2)`, `var(--radius-xs)`, `var(--text-xs)` font
   - Implemented with a simple CSS `::after` pseudo-element or small `<span>` — no external tooltip library

**Acceptance criteria:**
- [ ] Dock renders as a `position: fixed` bar at the bottom, 48px tall
- [ ] Dock is NOT inside the dockview layout tree (sibling in DOM, not a panel)
- [ ] `APP_REGISTRY` array is defined with at least the Welcome app
- [ ] Icon containers are 36×36px with `var(--radius-sm)`
- [ ] Hover state transitions at 100ms using `var(--ease-default)`
- [ ] Active dot (3px, `var(--color-accent)`) visible when panel is open
- [ ] Clicking a closed app: `dockviewApi.addPanel()` is called
- [ ] Clicking an open-but-unfocused app: `dockviewApi.getPanel(id).focus()` is called
- [ ] Clicking an already-focused app: no duplicate panel created
- [ ] Framer Motion bounce animation fires on panel open
- [ ] System clock in right zone shows current HH:MM and updates each minute
- [ ] Workspace chip in center zone displays "Default"
- [ ] No hardcoded hex values

**Test contract:**
- Test file: `frontend/src/components/Dock/__tests__/Dock.test.tsx`
  - Render `<Dock />` with a mock `LayoutContext` providing a mock `dockviewApi` (jest/vitest mock object with spies on `addPanel`, `getPanel`, `onDidActivePanelChange`, `onDidLayoutChange`).
  - Assert dock renders with `data-testid="dock"` (add this attribute).
  - Assert at least one icon button renders per `APP_REGISTRY` entry.
  - Click the "Welcome" icon when panel is not open (mock `getPanel` returns `undefined`): assert `addPanel` was called with `{id: "welcome", ...}`.
  - Click the "Welcome" icon when panel is open but not focused: assert `focus()` was called on the returned panel mock.
  - Click the "Welcome" icon when panel is already focused: assert `addPanel` was NOT called again.
  - Assert the system clock renders a time string matching `HH:MM` format.
  - Test `appRegistry.ts`: import `APP_REGISTRY`, assert it's an array of at least 1 entry, each entry has `id`, `label`, `icon`, `panelComponent`.

---

### Task 2.5 — OS-Style Login Screen

**Service/Target:** `frontend/src/components/Login/LoginScreen.tsx`, `frontend/src/api/auth.ts`
**Depends on:** 2.1
**Can run in parallel with:** 2.3

**What to build:**
A full-screen login experience before the shell loads, styled per experience-design.md §30.

1. **`auth.ts`** (API client module):
   - `listUsers(): Promise<UserSummary[]>` — `GET /api/auth/users` (new endpoint, see backend note below)
   - `login(userId: string, password: string): Promise<{token: string, user: User}>` — `POST /auth/login`
   - `getStoredToken(): string | null` — reads JWT from `sessionStorage` (not `localStorage` — session only)
   - `storeToken(token: string): void` — writes to `sessionStorage`
   - `clearToken(): void` — removes from `sessionStorage`

   **Backend note:** Add `GET /api/auth/users` endpoint in `backend/app/api/auth.py`. Returns `[{id, display_name, avatar_initials}]` for all users in the current tenant (no password). Used only by the login screen's user picker. Unauthenticated (before login). Rate-limit: same as `/auth/login`. This endpoint is NOT a Phase 1 task — it is a Phase 2 backend addition.

2. **`LoginScreen.tsx`:**
   - Full-viewport (`100vw × 100vh`), `position: fixed`, `z-index: 200`
   - Background: `var(--color-base)` (#0D160B)
   - **Animated gradient layer** (Layer 1): absolute-positioned div behind the card, CSS `@keyframes` animation — a slow radial gradient in `#4F87B340` (accent at 25% opacity) that translates across the screen over 20s in a loop. `pointer-events: none`. Use CSS animation, not Framer Motion (CSS is sufficient and more performant for this).
   - **Center card** (Layer 2): 480px wide, `var(--radius-lg)` (8px), `var(--shadow-5)`, background `var(--color-surface-1)`. Vertically + horizontally centered using flexbox on the wrapper.
   - **Footer** (Layer 3): fixed bottom bar — "CodeVV OS" left, `HH:MM` clock right. Font: `var(--font-mono)`, size `var(--text-sm)`, color `var(--color-text-tertiary)`.

3. **Phase A — User Picker (multi-user):**
   - On mount: call `listUsers()`. If loading, show a centered spinner (`var(--color-accent)` color, 24px).
   - User cards in a centered row (up to 4 across; wraps to 2-column grid if 5+ users)
   - Each card: 80px avatar circle (initials if no photo), display name below in `var(--text-sm) var(--font-weight-medium)`
   - Card hover: `var(--color-surface-3)` background, 100ms transition
   - If only one user: skip picker, go directly to Phase B
   - If zero users (first boot): show "Create admin account" form instead (a minimal form with display_name + email + password fields, submit to `POST /api/auth/register-admin`)

4. **Phase B — Password Entry** (after user selected):
   - Framer Motion slide transition: picker fades out (150ms), password phase slides in from right (200ms, `ease: [0.2, 0, 0, 1]`)
   - Selected user's avatar (64px) at top of card, display name below
   - Password input: full-width, `var(--input-height)` (32px), `var(--input-bg)`, `var(--input-border)`, auto-focused, `type="password"`
   - "Sign in" button: full-width, accent fill (`var(--btn-primary-bg)`), `var(--btn-height-md)` (32px), `var(--btn-radius)`
   - "← Other user" ghost button (if >1 user): returns to picker
   - Submit on Enter key or button click

5. **Error states** (per experience-design.md §30):
   - **Wrong password:** input border → `var(--color-error)`, card shakes (CSS keyframe: `translateX(4px → -4px → 3px → -3px → 0)`, 400ms), error message in `var(--color-error) var(--text-sm)`, input clears + refocuses
   - **Account locked (5 failures from server):** input disabled, message in `var(--color-warning)`: "Account locked. Contact your admin."
   - **Network error:** message "Unable to reach CodeVV. Check that services are running." with Retry button

6. **On success:**
   - Store JWT via `storeToken(token)`
   - Call `onLoginSuccess(token)` callback prop — parent (App.tsx) handles routing to shell

**Acceptance criteria:**
- [ ] `LoginScreen.tsx` renders full-screen with `var(--color-base)` background
- [ ] Animated gradient layer visible (CSS animation, not static)
- [ ] Center card is 480px wide with `var(--shadow-5)` and `var(--color-surface-1)` background
- [ ] Footer shows "CodeVV OS" and live clock in `var(--font-mono)`
- [ ] Multi-user picker shows user cards; single user skips to password phase
- [ ] Framer Motion slide transition between picker and password phase
- [ ] Password input is auto-focused when Phase B renders
- [ ] Wrong password triggers card shake animation (CSS keyframe) and `var(--color-error)` border
- [ ] Account locked state disables input
- [ ] Network error state shows retry button
- [ ] On success: JWT stored in `sessionStorage`, `onLoginSuccess` callback fired
- [ ] Backend `GET /api/auth/users` endpoint added and returns user list
- [ ] No hardcoded hex values in component

**Test contract:**
- Test file: `frontend/src/components/Login/__tests__/LoginScreen.test.tsx`
  - Mock `GET /api/auth/users` via MSW: return `[{id: "u1", display_name: "Tim", avatar_initials: "T"}]`.
  - Render `<LoginScreen onLoginSuccess={mockFn} />`. Assert loading spinner appears, then user card with "Tim" appears.
  - With one user: assert password input is shown directly (no picker). Assert input is auto-focused.
  - With two users: assert user cards shown. Click first user → assert slide transition begins (check Framer Motion state) → assert password input appears.
  - Mock `POST /auth/login` to return `{token: "test-jwt", user: {...}}`. Fill password, submit. Assert `mockFn` called with `"test-jwt"`. Assert `sessionStorage.getItem(...)` has the token.
  - Mock `POST /auth/login` to return 401. Submit form. Assert card shake animation class is applied. Assert error message contains "Incorrect password".
  - Mock `GET /api/auth/users` to return network error. Assert error message "Unable to reach CodeVV" shown.
- Test file: `tests/unit/test_auth_users_endpoint.py`
  - `GET /api/auth/users` with existing users in DB: assert list returned with `id`, `display_name`, `avatar_initials`. Assert no passwords or secrets in response.
  - `GET /api/auth/users` with empty DB: assert empty list `[]`.

---

### Task 2.6 — Auth Router & Session Guard

**Service/Target:** `frontend/src/App.tsx`, `frontend/src/hooks/useAuth.ts`
**Depends on:** 2.1, 2.5

**What to build:**
Replace the placeholder `App.tsx` with the auth-aware root component that switches between `LoginScreen` and `DockviewShell` based on JWT presence.

1. **`useAuth.ts`** hook:
   - Reads `getStoredToken()` on init
   - State: `{ token: string | null, isAuthenticated: boolean }`
   - `login(token: string)`: calls `storeToken(token)`, updates state
   - `logout()`: calls `clearToken()`, resets state

2. **Updated `App.tsx`:**
   - Uses `useAuth()` hook
   - If `!isAuthenticated`: render `<LoginScreen onLoginSuccess={login} />`
   - If `isAuthenticated`: render the shell layout — `<DockviewShell />` + `<Dock />` as siblings in a flex-column container
   - Shell layout: `display: flex; flex-direction: column; height: 100vh; overflow: hidden`
   - `DockviewShell` gets `flex: 1; overflow: hidden` (fills remaining space above dock)
   - `Dock` gets `flex-shrink: 0; height: 48px` (fixed at bottom)
   - Wrap both in `LayoutContext.Provider`
   - Import `dockview-react/dist/styles/dockview.css` and `./styles/dockview-theme.css` here (once, at app level)

3. **JWT validation on app boot:**
   - On mount, if token exists in `sessionStorage`, verify it is not expired by checking the `exp` claim in the JWT payload (decode the base64 payload — no crypto needed, just checking expiry)
   - If expired, call `logout()` immediately (shows login screen)
   - If valid, show shell directly (no re-login required for this session)

**Acceptance criteria:**
- [ ] `App.tsx` shows `LoginScreen` when no valid JWT in sessionStorage
- [ ] `App.tsx` shows `DockviewShell` + `Dock` when valid JWT present
- [ ] Shell layout is flex-column, 100vh, no scroll at root
- [ ] `DockviewShell` and `Dock` are siblings (not nested)
- [ ] `LayoutContext.Provider` wraps both `DockviewShell` and `Dock`
- [ ] Expired JWT in sessionStorage triggers logout (shows login screen)
- [ ] `login()` from `useAuth` stores token and switches view to shell
- [ ] `logout()` clears token and switches view to login screen

**Test contract:**
- Test file: `frontend/src/hooks/__tests__/useAuth.test.ts`
  - `useAuth` with no sessionStorage token: `isAuthenticated` is `false`.
  - `useAuth.login("valid-jwt")`: `isAuthenticated` becomes `true`.
  - `useAuth.logout()`: `isAuthenticated` becomes `false`, sessionStorage cleared.
  - `useAuth` with an expired JWT in sessionStorage (manufacture one with past `exp`): `isAuthenticated` is `false` after mount.
- Test file: `frontend/src/__tests__/App.test.tsx` (update existing):
  - With no sessionStorage token: assert `LoginScreen` renders (check for "CodeVV OS" footer text).
  - After calling `login("test-token")`: assert shell renders (check for dock's `data-testid="dock"`).
  - With expired token in sessionStorage: assert `LoginScreen` renders.

---

### Task 2.7 — Mobile Shell (< 768px)

**Service/Target:** `frontend/src/components/Mobile/MobileShell.tsx`, `frontend/src/hooks/useBreakpoint.ts`
**Depends on:** 2.4 (needs APP_REGISTRY and panel concepts)

**What to build:**
The responsive alternative to the dockview desktop shell for narrow viewports, per experience-design.md §29.

1. **`useBreakpoint.ts`** hook:
   - Listens to `window.innerWidth` via `ResizeObserver` or `window.matchMedia`
   - Returns `{ isMobile: boolean, isTablet: boolean, isDesktop: boolean }`
   - `isMobile`: `window.innerWidth < 768`
   - `isTablet`: `768 <= window.innerWidth < 1024`
   - `isDesktop`: `window.innerWidth >= 1024`
   - Debounce resize events 150ms

2. **`MobileShell.tsx`:**
   - Renders when `isMobile` is true (detected by `App.tsx` via `useBreakpoint`)
   - Full-screen layout: a single panel visible at a time + fixed 56px bottom tab bar
   - Active panel state: `useState<string>("dashboard")` — default is Dashboard
   - Panel content area: `height: calc(100vh - 56px - env(safe-area-inset-bottom))` to respect iOS safe area
   - **Bottom tab bar** (5 tabs, fixed at bottom):
     ```
     [ Dashboard ] [ Files ] [ Terminal ] [ AI Chat ] [ More ▾ ]
     ```
     - Tab bar height: 56px (not 48px — mobile is slightly larger per §29)
     - Active tab: 2px `var(--color-accent)` top border on the tab icon, icon color `var(--color-accent)`
     - Inactive tab: icon `var(--color-text-secondary)`
     - "More ▾" tab: opens a bottom sheet listing remaining panels (Canvas, Git, Settings, etc.) — panels that don't exist yet in Phase 2 are listed as disabled items greyed out with `var(--color-text-tertiary)`
   - **Panel rendering:** each tab renders a full-screen panel component:
     - Dashboard tab → `<WelcomePanel />` (placeholder for Phase 3.5 team dashboard)
     - Files tab → `<ComingSoonPanel label="Files" />`
     - Terminal tab → `<ComingSoonPanel label="Terminal" />`
     - AI Chat tab → `<ComingSoonPanel label="AI Chat" />`
   - **`ComingSoonPanel.tsx`:** Simple placeholder — centered text "Coming in Phase 3" in `var(--color-text-tertiary)`, icon `LayoutDashboard` at `var(--icon-3xl)`

3. **App.tsx update:**
   - After existing auth check, also check `isMobile` from `useBreakpoint`
   - If authenticated AND mobile → render `<MobileShell />`
   - If authenticated AND not mobile → render `<DockviewShell />` + `<Dock />` (existing)

**Acceptance criteria:**
- [ ] `useBreakpoint` returns `isMobile: true` when viewport < 768px
- [ ] `useBreakpoint` returns `isMobile: false` at ≥ 768px
- [ ] `MobileShell` renders when `isMobile` is true and user is authenticated
- [ ] `DockviewShell` + `Dock` renders when `isDesktop` is true and user is authenticated
- [ ] Bottom tab bar in `MobileShell` is 56px tall and fixed at bottom
- [ ] Uses `env(safe-area-inset-bottom)` for iOS compatibility
- [ ] Active tab has `var(--color-accent)` top border
- [ ] Five tabs: Dashboard, Files, Terminal, AI Chat, More
- [ ] Clicking a tab changes the visible panel
- [ ] "More" tab opens a bottom sheet with additional panel options
- [ ] No dockview dependency in MobileShell (mobile does not use dockview)

**Test contract:**
- Test file: `frontend/src/hooks/__tests__/useBreakpoint.test.ts`
  - Mock `window.innerWidth = 375`. Assert `isMobile: true, isDesktop: false`.
  - Mock `window.innerWidth = 1280`. Assert `isMobile: false, isDesktop: true`.
  - Mock `window.innerWidth = 900`. Assert `isTablet: true`.
- Test file: `frontend/src/components/Mobile/__tests__/MobileShell.test.tsx`
  - Render `<MobileShell />`. Assert 5 tab buttons render.
  - Assert first tab (Dashboard) is active by default (has active class or aria-selected).
  - Click "Files" tab. Assert Files panel content area is visible.
  - Assert tab bar has `position: fixed` and is at bottom (check computed styles or test-id).
  - Assert the panel content area height accounts for tab bar (check inline style or class has `calc`).

---

### Task 2.8 — Phase 2 Graduation Integration Test

**Service/Target:** `tests/integration/test_phase2_shell.py`, `frontend/src/__tests__/graduation.test.tsx`
**Depends on:** 2.3, 2.4, 2.5, 2.6, 2.7

**What to build:**
The Phase 2 graduation test validates the complete boot-to-shell flow. Two test files:

1. **Backend integration test** (`tests/integration/test_phase2_shell.py`):
   - Uses the running compose stack (same pattern as Task 1.25)
   - Creates a test user in the DB
   - Calls `GET /api/auth/users` — asserts user appears in the list
   - Calls `POST /auth/login` with correct credentials — asserts JWT returned
   - Uses JWT to call `GET /api/layout` — asserts `{layout_version: null, layout: null}` (no saved layout yet)
   - Calls `PUT /api/layout` with a test layout — asserts 200
   - Calls `GET /api/layout` again — asserts the saved layout is returned correctly

2. **Frontend integration test** (`frontend/src/__tests__/graduation.test.tsx`):
   - Full component integration test (not end-to-end Playwright — that is Phase 4)
   - MSW mocks all API calls
   - Step 1: Render `<App />`. Assert `LoginScreen` is visible (look for footer "CodeVV OS").
   - Step 2: Mock `GET /api/auth/users` → one user "Tim". Assert user card renders.
   - Step 3: Mock `POST /auth/login` → `{token: "test-jwt", user: {id: "u1"}}`. Mock `GET /api/layout` → null. Fill password "correct", click Sign in.
   - Step 4: Assert `LoginScreen` is no longer visible. Assert `data-testid="dock"` is visible.
   - Step 5: Assert `DockviewShell` is rendered (look for the WelcomePanel text).
   - Step 6: Assert dock icon for "Welcome" is present and clickable.
   - Step 7: Click a dock icon when panel is already shown — assert no crash, no duplicate panel.
   - This test is the definition of "Phase 2 done."

**Acceptance criteria:**
- [ ] Backend integration test passes against live compose stack
- [ ] Frontend graduation test passes all 7 steps
- [ ] `npm test` from `frontend/` reports 0 failures across all test files
- [ ] `pytest tests/` reports 0 failures
- [ ] `npm run build` from `frontend/` produces a clean dist/ with no type errors (`tsc --noEmit`)
- [ ] `ruff check backend/` produces 0 errors
- [ ] `mypy backend/app` produces 0 errors

**Test contract:**
The test files above ARE the test contract. Both test files must pass with zero failures. No skips. The graduation test is the definition of Phase 2 complete.

---

## Dependency Graph

```
Phase 1 (complete)
  ├── 2.1 Frontend App Bootstrap ──────────────────────────────────┐
  │                                                                  │
  └── 2.2 Layout Persistence API ──────────────┐                   │
                                                ↓                   ↓
                                           2.3 Dockview Shell    2.5 Login Screen
                                                ↓                   ↓
                                           2.4 Dock/Taskbar      2.6 Auth Router
                                                ↓                   ↓
                                           2.7 Mobile Shell ─────→ 2.8 Graduation Test
```

**Parallel tracks:**
- Start 2.1 and 2.2 simultaneously (frontend bootstrap + backend API — no overlap)
- After 2.1 is done, start 2.3 and 2.5 simultaneously (dockview shell + login — no overlap)
- After 2.5 is done, start 2.6 (depends only on 2.1 + 2.5)
- After 2.3 is done, start 2.4 (depends only on 2.3)
- After 2.4 is done, start 2.7 (depends only on 2.4)
- 2.8 requires all of 2.3, 2.4, 2.5, 2.6, 2.7

---

## New Dependencies Summary

Install in `frontend/`:

```bash
# Production
npm install dockview-react@5.2.0 framer-motion lucide-react

# Move to production (from devDependencies)
npm install react react-dom

# Dev
npm install -D @tailwindcss/vite tailwindcss @vitejs/plugin-react
```

No new backend Python dependencies are required beyond what Phase 1 already installed.

---

## Design Token Enforcement

All components must use CSS custom properties from `global.css`. No hex values. Cheat sheet:

| Need | Token |
|------|-------|
| App background | `var(--color-base)` |
| Panel bg | `var(--color-surface-1)` |
| Panel header bg | `var(--color-surface-2)` |
| Hover state | `var(--color-surface-3)` |
| Tooltip bg | `var(--color-surface-4)` |
| Default border | `var(--color-border-muted)` |
| Primary text | `var(--color-text-primary)` |
| Label/metadata | `var(--color-text-secondary)` |
| Placeholder | `var(--color-text-tertiary)` |
| Accent (interactive) | `var(--color-accent)` |
| Error | `var(--color-error)` |
| Warning | `var(--color-warning)` |
| Fast transition | `var(--duration-fast)` (100ms) |
| Normal transition | `var(--duration-normal)` (200ms) |
| Default easing | `var(--ease-default)` |
| Dock height | `var(--dock-height)` = 48px |
| Button radius | `var(--radius-sm)` |
| Panel radius | `var(--radius-none)` |

---

## Out of Scope for Phase 2

The following are explicitly NOT part of this spec. Any attempt to add them is scope creep:

- File browser (Phase 3a)
- Terminal connection to ptyHost (Phase 3b)
- AI chat panel (Phase 3.5-PA)
- Settings panel with JSONForms (Phase 3c)
- Knowledge graph (Phase 3.5-KG)
- Canvas / tldraw (Phase 3.5-d)
- Notification center (Phase 3d)
- Team dashboard content (Phase 3.5-UX)
- Workspace templates (Phase 3.5-WS)
- LiveKit video (Phase 3.5b)
- Branch auto-environments (Phase 3.5-CI)

---

*End of Phase 2 spec. Phase 3+ is not planned here. All tasks are grounded in ROADMAP.md, ARCHITECTURE.md, design-system.md, and codevvos-experience-design.md.*

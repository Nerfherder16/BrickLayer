# Spec: Kiln Token Insights — Refresh + Date Persistence

**Created**: 2026-04-06T14:00:00Z
**Project**: BrickLayerHub (Kiln)
**Branch**: autopilot/kiln-refresh-persist-20260406

## Goal
Make the Token Insights page auto-refresh data every 60 seconds (with a manual refresh button), and persist the "Compare Since" date picker value across both page refreshes and full app exit/reopen cycles.

## Architecture
The current `TokenInsights.tsx` has a `refreshAll()` function but no button or interval calling it. The `compareDate` state is ephemeral (useState only). We need:

1. A 60-second `setInterval` in `TokenInsights.tsx` that calls `refreshAll()`, plus a visible refresh button
2. An IPC channel pair (`get-setting` / `set-setting`) in main process that reads/writes a JSON settings file to `app.getPath('userData')/kiln-settings.json`
3. A preload bridge exposure for the new IPC channels
4. `TokenInsights.tsx` loads `compareDate` from persisted settings on mount, and writes it back on change

No new npm dependencies — we use Node `fs` in main process (already available) and the existing IPC pattern.

## Tasks

### Task 1: Add settings persistence IPC in main process + preload bridge
**Description**: Create a simple key-value settings store in the main process. Add two IPC handlers: `get-setting` (takes key, returns value or null) and `set-setting` (takes key + value, writes to disk). The store file is `kiln-settings.json` in Electron's `app.getPath('userData')`. Use synchronous JSON read/write with try-catch (file may not exist on first run). Expose both channels through the preload bridge (`window.api.getSetting(key)` and `window.api.setSetting(key, value)`).

Implementation details:
- In `src/main/ipc.ts`: add `ipcMain.handle('get-setting', ...)` and `ipcMain.handle('set-setting', ...)`
- Settings file path: `path.join(app.getPath('userData'), 'kiln-settings.json')`
- `get-setting`: read file, parse JSON, return `data[key] ?? null`. If file doesn't exist, return null.
- `set-setting`: read file (or `{}`), set `data[key] = value`, write file back.
- In `src/preload/index.ts`: add `getSetting: (key: string) => ipcRenderer.invoke('get-setting', key)` and `setSetting: (key: string, value: unknown) => ipcRenderer.invoke('set-setting', key, value)` to the `api` object.
- In `src/preload/index.d.ts`: add type declarations for both new methods on `ElectronAPI`.

**Mode**: typescript
**Files**:
  - Implementation: `src/main/ipc.ts`, `src/preload/index.ts`, `src/preload/index.d.ts`
  - Tests: `src/main/__tests__/settings.test.ts`
**Test strategy**: Unit test the settings read/write logic. Mock `app.getPath` and `fs` operations. Test: (1) get-setting returns null when file doesn't exist, (2) set-setting creates file and stores value, (3) get-setting retrieves previously set value, (4) set-setting preserves other keys when updating one key.
**Parallel**: no (foundational — task 2 depends on this)

### Task 2: Add auto-refresh interval, refresh button, and persisted date picker
**Description**: In `TokenInsights.tsx`:

1. **Refresh button**: Add a circular-arrow refresh button (Unicode ↻ or SVG) in the page header area near the title. On click, call `refreshAll()`. Show a brief spin animation (CSS rotate) during refresh. Style: ghost button matching existing dark theme (`#1e1e2e` background, `#cdd6f4` text, `#45475a` border on hover).

2. **Auto-refresh**: Add a `useEffect` with a 60-second `setInterval` that calls `refreshAll()`. Clean up on unmount. The interval should reset when the user manually refreshes (so they always get a full 60s after manual refresh).

3. **Date persistence**: On mount, call `window.api.getSetting('compareDate')`. If a value is returned, use it as the initial `compareDate` state instead of the default 30-days-ago. When the user changes the date picker, call `window.api.setSetting('compareDate', newValue)` to persist it. The date is stored as an ISO date string (`YYYY-MM-DD`).

4. **Refresh indicator**: Add a subtle "Last updated: X seconds ago" text near the refresh button. Use a `lastRefreshed` state (Date) updated after each `refreshAll()` completes, and a 1-second display interval to show elapsed seconds.

**Mode**: typescript
**Files**:
  - Implementation: `src/renderer/src/pages/TokenInsights.tsx`
  - Tests: `src/renderer/src/__tests__/TokenInsights.test.tsx`
**Test strategy**: (1) Test that `setSetting` is called when date picker value changes. (2) Test that the refresh button exists and calls the refetch functions when clicked. (3) Test that `getSetting` is called on mount to load persisted date. (4) Test that auto-refresh interval is set up (mock timers, advance 60s, verify refetch called). Use vitest + React Testing Library. Mock `window.api` methods.
**Parallel**: no (depends on task 1 for the IPC bridge)

## Tech Stack
- Language: TypeScript 5.x
- Framework: Electron 35 + React 19 + electron-vite
- Test runner: `npx vitest run`
- Type checker: `npx tsc --noEmit`
- Lint: `npx eslint .`

## Agent Hints
- Test command: `npx vitest run`
- Type check command: `npx tsc --noEmit`
- Lint command: `npx eslint .`
- Key shared files: `src/preload/index.ts` (bridge), `src/preload/index.d.ts` (types), `src/main/ipc.ts` (handlers)
- Platform: Windows (WSL accessing `/mnt/c/` — path separators are forward-slash in code, but the app runs on Windows)
- Project root: `/mnt/c/Users/trg16/Dev/BrickLayerHub`
- Inline styles only — no Tailwind, no CSS modules
- React 19 — no `defaultProps`, use default parameters
- The `useIPC` hooks return `{ data, loading, error, refetch }` — use `refetch()` for refresh

## Constraints
- No new npm dependencies — use Node built-in `fs` and `path` for settings
- Inline styles only — no CSS files or Tailwind
- Do not modify the IPC data-fetching hooks (`useIPC.ts`) — refresh is handled by calling `refetch()` from the consumer
- Do not change the sidebar navigation or app-level routing
- Settings file format is a flat JSON object (no nesting needed for now)
- The date picker remains an `<input type="date">` — no third-party date picker

## Definition of Done
Tests pass (`npx vitest run`), types clean (`npx tsc --noEmit`), lint clean (`npx eslint .`). Manual verification: refresh button triggers data reload, auto-refresh fires every 60s, date picker value survives page navigation and app restart.

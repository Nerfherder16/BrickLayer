# Spec: Kiln Token Insights — Enhanced Analytics

**Created**: 2026-04-06T19:30:00Z
**Project**: BrickLayerHub (Kiln)
**Branch**: autopilot/kiln-token-insights-20260406

## Goal

Add five analytics features to the existing Token Insights page in Kiln: a "What Changed" week-over-week panel, cache cliff detection with warning badges on the trend chart, project-level cost breakdown, hook latency tracking surfaced from `hook-timing.jsonl`, and a top-files-read table from `read-log.jsonl`. All features integrate into the existing page using Kiln's inline-styles-only convention and retro pixel-art aesthetic.

## Architecture

Existing data flow: `tokenReader.ts (main) → ipc.ts → preload/index.ts → useIPC.ts → TokenInsights.tsx`

New files:
- `src/main/readLogReader.ts` — reads `~/.mas/read-log.jsonl`
- `src/main/hookTimingReader.ts` — reads `~/.claude/monitors/hook-timing.jsonl`
- `src/renderer/src/pages/TokenInsightsAnalytics.tsx` — new widget components

Modified files:
- `src/main/tokenReader.ts` — add `getWeekOverWeek()` and `detectCacheCliffs()`
- `src/main/ipc.ts` — 4 new IPC handlers
- `src/preload/index.ts` — 4 new bridge methods
- `src/renderer/src/hooks/useIPC.ts` — 4 new hooks
- `src/renderer/src/pages/TokenInsightsWidgets.tsx` — cache cliff badges on CostTrendChart
- `src/renderer/src/pages/TokenInsights.tsx` — compose new widgets

## Tasks

### Task 1: Week-over-week + cache cliff data [mode:typescript]
**Description**: Add `getWeekOverWeek()` to `tokenReader.ts` — computes this-week vs last-week deltas for session count, total cost, avg effective/session, cache hit rate, total turns. Returns `{ metric, thisWeek, lastWeek, delta, improved }[]`. Also add `detectCacheCliffs()` — scans sessions chronologically, flags any where `cache_read_tokens` dropped >50% vs prior session, returns `{ session_id, ts, dropPct }[]`.
**Files**: `src/main/tokenReader.ts`, `src/main/__tests__/tokenReader.test.ts`
**Test strategy**: Mock session arrays spanning 2 weeks. Assert correct deltas and improved flags. Test cliff detection with >50% drops and normal sessions.
**Parallel**: no (foundational — tasks 4, 9 depend on this)

### Task 2: Read-log reader [mode:typescript]
**Description**: Create `src/main/readLogReader.ts`. Reads `~/.mas/read-log.jsonl` (WSL fallback). Each line: `{ ts, file, bytes }`. Exports `readReadLog()` (raw array) and `getTopFiles(limit=20)` (aggregated by file path, sorted by readCount desc). Same path-candidate pattern as tokenReader.ts.
**Files**: `src/main/readLogReader.ts`, `src/main/__tests__/readLogReader.test.ts`
**Test strategy**: Mock fs.readFile with sample JSONL. Assert parse, skip malformed, correct aggregation.
**Parallel**: yes — independent of tasks 1, 3

### Task 3: Hook timing reader [mode:typescript]
**Description**: Create `src/main/hookTimingReader.ts`. Reads `~/.claude/monitors/hook-timing.jsonl` (WSL fallback). Each line: `{ ts, hook, ms, exit }`. Exports `readHookTiming()` (raw) and `getHookLatencyStats(limit=25)` — aggregates by hook name: `{ hook, count, avgMs, p95Ms, maxMs, errorCount }[]` sorted by avgMs desc.
**Files**: `src/main/hookTimingReader.ts`, `src/main/__tests__/hookTimingReader.test.ts`
**Test strategy**: Mock timing data with varying latencies and error exits. Assert avg, p95, max, error counts.
**Parallel**: yes — independent of tasks 1, 2

### Task 4: IPC + preload wiring [depends:1,2,3] [mode:typescript]
**Description**: Register 4 new IPC handlers in `ipc.ts`: `token:getWeekOverWeek`, `token:getCacheCliffs`, `token:getTopFiles`, `token:getHookLatency`. Expose in `preload/index.ts`. Follow existing dynamic import pattern.
**Files**: `src/main/ipc.ts`, `src/preload/index.ts`
**Test strategy**: Verified indirectly via reader tests + task 11 smoke test.
**Parallel**: no (depends on 1,2,3)

### Task 5: Renderer hooks [depends:4] [mode:typescript]
**Description**: Add 4 hooks to `useIPC.ts`: `useWeekOverWeek()`, `useCacheCliffs()`, `useTopFiles()`, `useHookLatency()`. Define interfaces: `WeekOverWeekItem`, `CacheCliff`, `TopFile`, `HookLatencyStat`. Follow `useTokenSessions()` pattern exactly.
**Files**: `src/renderer/src/hooks/useIPC.ts`
**Test strategy**: Mock window.api methods. Assert loading/data/error states.
**Parallel**: no (depends on 4)

### Task 6: WhatChangedPanel widget [depends:5] [mode:typescript]
**Description**: Create `WhatChangedPanel` in new `TokenInsightsAnalytics.tsx`. Takes `changes: WeekOverWeekItem[]`. PixelCard wrapper, title "What Changed This Week". Each row: metric name, this-week, last-week, delta with arrow, green if improved / red if worsened. Inline styles only.
**Files**: `src/renderer/src/pages/TokenInsightsAnalytics.tsx`
**Test strategy**: Render with sample data. Assert metric names, green/red coloring, delta arrows.
**Parallel**: yes — independent of tasks 7, 8

### Task 7: ProjectBreakdown widget [depends:5] [mode:typescript]
**Description**: Add `ProjectBreakdown` to `TokenInsightsAnalytics.tsx`. Takes `sessions: TokenSession[]`. Groups by `cwd`, computes per-project: session count, total cost, total effective, avg cache rate. RetroTable sorted by cost desc. Show last 2 path segments only. PixelCard title "Cost by Project".
**Files**: `src/renderer/src/pages/TokenInsightsAnalytics.tsx`
**Test strategy**: Render with 3 different cwds. Assert all projects, sort order, path truncation.
**Parallel**: yes — independent of tasks 6, 8

### Task 8: HookLatencyTable + TopFilesTable widgets [depends:5] [mode:typescript]
**Description**: Add to `TokenInsightsAnalytics.tsx`:
1. `HookLatencyTable` — RetroTable in PixelCard "Hook Latency". Columns: hook, calls, avg ms, p95 ms, max ms, errors. Amber avg >100ms, red >500ms. Red errors if >0.
2. `TopFilesTable` — RetroTable in PixelCard "Most-Read Files". Columns: file, reads, bytes. Truncate to last 3 path segments. Amber if >10 reads. Hint text: "Files read often → .claudeignore or jCodeMunch".
**Files**: `src/renderer/src/pages/TokenInsightsAnalytics.tsx`
**Test strategy**: Assert color coding for slow hooks and high-read files. Assert hint text renders.
**Parallel**: yes — independent of tasks 6, 7

### Task 9: Cache cliff badges on CostTrendChart [depends:1] [mode:typescript]
**Description**: Modify `CostTrendChart` in `TokenInsightsWidgets.tsx` to accept optional `cacheCliffs: CacheCliff[]`. When a bar's session_id matches a cliff, render red triangle above bar + "CACHE CLIFF: -XX%" in tooltip.
**Files**: `src/renderer/src/pages/TokenInsightsWidgets.tsx`
**Test strategy**: Render with matching cliff data. Assert red triangles appear. Assert tooltip contains "CACHE CLIFF".
**Parallel**: no (depends on task 1 for CacheCliff type)

### Task 10: Compose into TokenInsights page [depends:5,6,7,8,9] [mode:typescript]
**Description**: Update `TokenInsights.tsx` — import new widgets, add 4 hooks, layout: What Changed (full width) → Project Breakdown (full width) → Hook Latency + Top Files (2-col grid). Pass cacheCliffs to CostTrendChart. Independent loading states per section.
**Files**: `src/renderer/src/pages/TokenInsights.tsx`
**Test strategy**: Mock all hooks. Assert all section headers appear.
**Parallel**: no (depends on 5-9)

### Task 11: Smoke test [depends:10] [phase_end]
**Description**: Run `npm run typecheck` and `npm run test` in BrickLayerHub directory. Verify 0 errors.
**Files**: none (verification only)
**Test strategy**: Both commands exit 0.
**Parallel**: no (final gate)

## Tech Stack
- Language: TypeScript 5.x
- Framework: Electron + React 19 (electron-vite)
- Test runner: `cd /mnt/c/Users/trg16/Dev/BrickLayerHub && npx vitest run`
- Type checker: `cd /mnt/c/Users/trg16/Dev/BrickLayerHub && npm run typecheck`
- Lint: `cd /mnt/c/Users/trg16/Dev/BrickLayerHub && npm run lint`

## Agent Hints
- Test command: `powershell.exe -c "cd C:\Users\trg16\Dev\BrickLayerHub; npx vitest run"`
- Type check: `powershell.exe -c "cd C:\Users\trg16\Dev\BrickLayerHub; npm run typecheck"`
- Style: inline styles ONLY. CSS variables from globals.css. Retro pixel aesthetic.
- Components: use PixelCard (card wrapper) and RetroTable (generic typed table)
- IPC pattern: dynamic import in handler (`const { fn } = await import('./reader')`)
- Path handling: check Windows path first, WSL fallback second
- Files must stay under 600 lines

## Constraints
- All features go in existing Token Insights page (no new routes)
- Inline styles only — no Tailwind, no CSS modules
- Main process handles all file I/O
- No new npm dependencies
- Keep each file under 600 lines
- Handle both Windows and WSL path formats in cwd truncation

## Definition of Done
- `npm run typecheck` exits 0
- `npm run test` exits 0
- All 5 new features visible on Token Insights page
- No files exceed 600 lines

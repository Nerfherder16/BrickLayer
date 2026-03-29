# Campaign Context — masonry-48h-validation

## Campaign Type
Validation campaign — verify correctness of changes made in the last 48 hours across Masonry hooks, template, and Recall hooks. No simulate.py — pure code audit.

## Change Scope (committed, last 48 hours)

### 1. masonry-context-monitor.js (Stop hook, position 6, timeout: 5s)
- **Ollama AbortSignal.timeout reduced**: 5000ms → 3000ms
- **git status timeout reduced**: 5000ms → 2000ms
- **process.exit(0) replaced with return**: main() now ends naturally
- **Session-scoped dirty file check**: New logic that reads session activity log to narrow dirty file detection to THIS session only

### 2. masonry-pre-compact.js (PreCompact hook, timeout: 10s)
- **Output channel**: `hookSpecificOutput` → `systemMessage`

### 3. masonry-prompt-router.js (UserPromptSubmit hook, timeout: 5s)
- **Output channel**: changed to `additionalContext`
- **Hint format rewrite**: imperative routing instruction

### 4. masonry-session-start.js (SessionStart hook, timeout: 8s)
- **Output channel**: `hookSpecificOutput` → `systemMessage`

### 5. masonry-teammate-idle.js (TeammateIdle/TaskCompleted hook, timeout: 5s)
- **Output channel**: `hookSpecificOutput` → `systemMessage`

### 6. session/build-state.js (SessionStart module)
- **Output channel**: `hookSpecificOutput` → `systemMessage`

### 7. template/program.md
- **RETRO-H1**: Added Confidence field (0.0-1.0) as required in finding format
- **RETRO-H2**: Added pre-flight scan step before Wave 1
- **RETRO-H3**: Added Files to change section required for FAILURE/High findings
- **Peer review template**: Added Peer Review section to finding format

## Uncommitted Changes (working tree)

### 8. Recall hooks (C:/Users/trg16/Dev/Recall/hooks/)
- recall-retrieve.js, recall-session-summary.js, observe-edit.js, session-save.js
- Timeout reductions + process.exit(0) → return fixes

## Settings.json Timeout Budgets

| Hook | Event | Timeout | Internal sum |
|------|-------|---------|-------------|
| masonry-session-start.js | SessionStart | 8s | stdin 3s + git status 5s |
| masonry-prompt-router.js | UserPromptSubmit | 5s | stdin 2s |
| masonry-pre-compact.js | PreCompact | 10s | stdin 2s + Recall checkpoint |
| masonry-teammate-idle.js | TeammateIdle | 5s | stdin 2s |
| masonry-context-monitor.js | Stop | 5s | readStdin + git status 2s + Ollama 3s |

## Target Files

| Changed File | Path |
|---|---|
| masonry-context-monitor.js | masonry/src/hooks/masonry-context-monitor.js |
| masonry-pre-compact.js | masonry/src/hooks/masonry-pre-compact.js |
| masonry-prompt-router.js | masonry/src/hooks/masonry-prompt-router.js |
| masonry-session-start.js | masonry/src/hooks/masonry-session-start.js |
| masonry-teammate-idle.js | masonry/src/hooks/masonry-teammate-idle.js |
| session/build-state.js | masonry/src/hooks/session/build-state.js |
| template/program.md | template/program.md |

## Pre-Analysis Flags (from Mortar)

1. **context-monitor timeout budget is TIGHT** — readStdin + git 2s + Ollama 3s may exceed 5s budget
2. **session-start still uses process.exit(0)** on lines 44 and 101
3. **teammate-idle has 5 process.exit(0) calls** — lines 49, 51, 55, 75, 85 (not migrated)
4. **prompt-router additionalContext** — needs verification that Claude Code consumes this from UserPromptSubmit hooks

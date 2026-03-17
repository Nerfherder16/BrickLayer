# Changelog

## [Unreleased]

### Added
- Initial spec: MASONRY-SPEC.md
- Project scaffold: README, package.json, .gitignore
- Directory structure: bin/, src/core/, src/hooks/, skills/, packs/

## [0.1.0-phase1] — 2026-03-17

### Added — Phase 1: Core hooks + installer

**Core modules**
- `src/core/config.js` — Config loader (~/.masonry/config.json with defaults)
- `src/core/state.js` — Per-project masonry-state.json read/write
- `src/core/recall.js` — Recall HTTP client (storeMemory, searchMemory, isAvailable)

**Hooks**
- `src/hooks/masonry-register.js` — UserPromptSubmit: Recall context injection, resume detection, guard flush
- `src/hooks/masonry-observe.js` — PostToolUse async: finding detection → Recall, activity log
- `src/hooks/masonry-guard.js` — PostToolUse async: 3-strike error fingerprinting
- `src/hooks/masonry-stop.js` — Stop: session summary via Ollama → Recall, temp cleanup
- `src/hooks/masonry-handoff.js` — Detached handoff: packages loop state + findings → Recall at 70% context
- `src/hooks/masonry-statusline.js` — StatusLine: ANSI 24-bit campaign bar with progress, verdicts, context %

**Installer**
- `bin/masonry-setup.js` — Interactive setup wizard: writes ~/.masonry/config.json, merges hooks into ~/.claude/settings.json, smoke-checks Recall; supports --dry-run and --uninstall
- `bin/masonry-mcp.js` — MCP server stub (Phase 2)

**Skills**
- `skills/masonry-run.md` — /masonry-run: launch or resume campaign
- `skills/masonry-status.md` — /masonry-status: campaign health summary
- `skills/masonry-init.md` — /masonry-init: Phase 2 stub

**Config**
- `hooks.json` — Hook manifest (UserPromptSubmit, PostToolUse ×2, Stop, statusLine)

# Masonry Hooks Changelog

Audit trail of hook fleet changes. Each entry documents what changed, why, and when.

---

## 2026-03-28 — Hook Fleet Optimization

### Removed from settings.json (dead/redundant)
- **masonry-recall-check.js** (UserPromptSubmit async): Pinged Recall /health and wrote to `/tmp/masonry-recall-status.json`. Nobody read that file — masonry-statusline.js has its own inline health check. Zero value, pure overhead. File archived.
- **masonry-guard.js** (PostToolUse async Write|Edit): Fingerprinted error patterns and wrote to a guard queue NDJSON. masonry-tool-failure.js (PostToolUseFailure) already does 3-strike error tracking with proper state. Duplicate functionality, different event. File archived.
- **permission-mode-watcher.js** (PostToolUse async Write|Edit): Registered in settings.json but the file `C:/Users/trg16/.claude/hooks/permission-mode-watcher.js` never existed. Dead entry.

### Merged
- **masonry-config-protection.js + masonry-secret-scanner.js → masonry-content-guard.js**
  - Both are PreToolUse Write|Edit blockers. Combined into one process spawn per edit.
  - Secret scan runs first (fast pattern match, exits 2 on match). Config protection runs second.
  - Both originals archived.

- **masonry-lint-check.js + masonry-design-token-enforcer.js → masonry-style-checker.js**
  - Both are PostToolUse Write|Edit hooks. Combined into one process spawn per edit.
  - Lint check runs first (ruff/prettier/eslint). Token enforcer runs second (only when .ui/ exists).
  - Both originals archived.

- **masonry-pre-edit.js + masonry-session-lock.js → masonry-pre-protect.js**
  - Both are PreToolUse Write|Edit hooks. Combined into one process spawn per edit.
  - Session lock runs first (may block). Backup runs second (never blocks).
  - Both originals archived.

### Net result
- 8 hook registrations removed/merged → 3 combined hooks
- PreToolUse Write|Edit: 4 spawns → 3 spawns (removed 1 dead, merged 2 pairs)
- PostToolUse Write|Edit: 10 spawns → 9 spawns (removed 2 dead, merged 1 pair → but still counts as fewer process spawns since they were separate)
- UserPromptSubmit: 4 → 3 (removed recall-check)

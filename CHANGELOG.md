# Changelog

All notable changes documented here.
Maintained automatically by BrickLayer post-commit hook and karen agent.

---

## [Unreleased]

---

## [2026-04-04]

### Added
- `[feat]` Learning loop: `toolPatternPromote` (+20% headroom) and `toolPatternDemote` (-15%, floor 0.1) in `masonry/src/tools/impl-patterns.js`
- `[feat]` MCP tool definitions for `masonry_pattern_promote` and `masonry_pattern_demote` in `schema-advanced.js`; dispatch cases in `masonry-mcp.js`
- `[feat]` `masonry-build-outcome.js` — PostToolUse:Write hook watches `.autopilot/progress.json` for DONE/FAILED transitions and calls promote/demote; infers agent type from `[mode:X]` annotations
- `[feat]` Session-start pattern decay — `context-data.js` auto-runs `toolPatternDecay` at every session start; injects top-5 agents by confidence score as context hint
- `[feat]` 108 new tests across 4 test files covering learning loop behavior
- `[feat]` Add tmux terminal profiles for Tim and Nick in VS Code (`fd3a7a33`)
- `[feat]` Add Proxmox skill; update homelab skill with ubuntu-claude; fix deploy-claude.sh atomic write (`aaecd2d7`)
- `[feat]` Sync mcpServers from ~/.claude.json via deploy-claude.sh (`a3f54e53`)
- `[feat]` Sync ~/.claude assets — skills, plugins, monitors, deploy script (`317479d6`)

### Fixed
- `[fix]` codevvOS: fix recall_client endpoint calls (`f89d562a`)
- `[fix]` masonry-prompt-inject: add auth header and fix threshold (`d8597571`)
- `[fix]` Redact secrets from mcp-servers.json (`c4450772`)
- `[fix]` Restore masonry/bin/masonry-mcp.js (deleted in cleanup) (`024ab87d`)

### Changed
- `[docs]` CLAUDE.md delegation rules rewritten — dev tasks now route to rough-in directly; Mortar is entry point for campaigns/research and docs only (`cd3dc405`)
- `[docs]` Update network map: ubuntu-claude Tailscale SSH, code.streamy.tube backend, workspace path (`32338569`)

### Automated
- `[autopilot]` masonry-mortar-enforcer.js updated to allow direct specialist spawns from main session, aligning with new routing rules (`cd3dc405`)
- `[autopilot]` masonry-prompt-router.js: added `@agent-name:` self-invoke bypass — any prompt starting with `@agentname:` skips all routing and spawns that agent directly (`cd3dc405`)

---

## [2026-04-03]

### Added
- `[feat]` Terminal tab titles — Tim=octoface, Nick=diamond; color-coded terminal profiles (`4d58259d`, `83b1be5e`, `05eb4434`)
- `[feat]` User attribution — terminal profiles + CLAUDE_USER tagging in Recall (`50dffee3`)
- `[feat]` git-sync script for cross-machine repo sync (`16879647`)
- `[feat]` Automation recommendations from codebase analysis (`cca491f6`)

### Fixed
- `[fix]` Nick terminal icon — diamond → ruby (valid codicon) (`465b5688`)
- `[fix]` codevvOS Docker build + LXC deployment fixes (`9a732e70`)
- `[fix]` version-check uses dynamic path, works on any machine (`5cd6772f`)

### Changed
- `[chore]` Preserve executable bit on scripts (`d5977def`)
- `[chore]` Gitignore .claude settings backups to prevent secret leaks (`9b819bc1`)
- `[chore]` Expand developer skills registry + symlink Windows skills to WSL (`e79b24c1`)
- `[chore]` Expand agent tool access and enforce jcodemunch-first pattern (`9ba722ca`)
- `[chore]` Versioning + VS Code daily check (`8e46b03b`)

---

## [Wave 14 — Evolve] (complete as of 2026-04-02)

### Engine Fixes
- `bl/tmux/core.py` — per-spawn gate (`BL_GATE_FILE`) added
- `bl/tmux/pane.py` — `capture-pane` uses `$TMUX_PANE`
- `bl/runners/correctness.py` — Linux + Windows path regex
- `bl/recall_bridge.py` — dead `decay_conflicting_memories()` removed
- `bl/config.py` — `recall_src` reads `RECALL_SRC` env var

### Masonry Hook Fixes
- `masonry-mortar-enforcer.js` — `BL_GATE_FILE` env var
- `masonry-routing-gate.js` — `BL_GATE_FILE` env var
- `session/mortar-gate.js` — dynamic loader from `agent_registry.yml` + frontmatter

### Agent Fixes
- `mortar.md` — WSL-portable paths
- `trowel.md` — `RECALL_HOST` env var
- `bl-verifier.md`, `e2e.md` — WSL paths

---

## [Wave 1 — Initial Campaign]

- Campaign initialized

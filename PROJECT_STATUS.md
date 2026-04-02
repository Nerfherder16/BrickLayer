# BrickLayer 2.0 — Project Status

Last updated: 2026-04-02

---

## Engine (`bl/`)

| Module | Status |
|--------|--------|
| `bl/tmux/core.py` | Stable. Per-spawn gate (`BL_GATE_FILE`) since 2026-04-02 |
| `bl/tmux/pane.py` | Stable. `capture-pane` uses `$TMUX_PANE` since 2026-04-02 |
| `bl/tmux/wave.py` | Stable |
| `bl/tmux/helpers.py` | Stable |
| `bl/runners/agent.py` | Stable |
| `bl/runners/swarm.py` | Stable (added 2026-03-31) |
| `bl/runners/scout.py` | Stable (added 2026-03-31) |
| `bl/runners/correctness.py` | Stable. Linux + Windows path regex since 2026-04-02 |
| `bl/recall_bridge.py` | Stable. Dead `decay_conflicting_memories()` removed 2026-04-02 |
| `bl/config.py` | Stable. `recall_src` reads `RECALL_SRC` env var since 2026-04-02 |
| `bl/frontmatter.py` | Stable (added 2026-03-31) |
| `bl/healloop.py` | Stable |
| `bl/crucible.py` | Stable |

---

## Masonry Hooks (`masonry/src/hooks/`)

| Hook | Status |
|------|--------|
| `session/mortar-gate.js` | Stable. Dynamic loader from `agent_registry.yml` + frontmatter since 2026-04-02 |
| `masonry-mortar-enforcer.js` | Stable. `BL_GATE_FILE` env var since 2026-04-02 |
| `masonry-routing-gate.js` | Stable. `BL_GATE_FILE` env var since 2026-04-02 |
| `masonry-pre-protect.js` | Stable. `BL_GATE_FILE` env var since 2026-04-02 |
| `masonry-subagent-tracker.js` | Stable. `BL_GATE_FILE` env var since 2026-04-02 |
| `masonry-prompt-router.js` | Stable. `BL_GATE_FILE` env var since 2026-04-02 |
| `masonry-session-end.js` | Stable. Dead `decay_conflicting_memories` block removed 2026-04-02 |

---

## Agents (`.claude/agents/`)

| Agent | Status |
|-------|--------|
| `mortar.md` | Stable. WSL-portable paths since 2026-04-02 |
| `trowel.md` | Stable. `RECALL_HOST` env var since 2026-04-02 |
| `bl-verifier.md` | Stable. WSL paths since 2026-04-02 |
| `e2e.md` | Stable. WSL paths since 2026-04-02 |

---

## Campaign (`bricklayer-v2/`)

Current wave: **Wave 14 Evolve** (complete)

| Open Item | Verdict | Summary |
|-----------|---------|---------|
| E14.9 | WARNING | Full-corpus live eval 0.58 (20/36); INCONCLUSIVE over-fires; cross-family generalization gap |
| E14.8 | WARNING | improve_agent.py UnicodeDecodeError in subprocess reader; encoding fix needed |
| E14.1 | WARNING | E12.1-live-15 persistent (HEALTHY predicted WARNING); needs calibration example |
| E14.6 | WARNING | quantitative-analyst static 0.40 unreliable; live eval needed |
| E-mid.1 | PENDING_EXTERNAL | karen prompt optimization — manual Git Bash run needed |

---

## Environment Requirements

| Variable | Purpose | Default |
|----------|---------|---------|
| `RECALL_SRC` | Path to the Recall source repo | `None` (optional) |
| `RECALL_HOST` | Recall API base URL used by trowel agent | None |
| `BL_GATE_FILE` | Per-spawn Masonry gate file path (injected automatically by `spawn_agent`) | `/tmp/masonry-gate-{agent_id}.json` |
| `BL_MASONRY_STATE` | Override path for `masonry-state.json` (used by mortar agent) | `process.cwd()/masonry/masonry-state.json` |

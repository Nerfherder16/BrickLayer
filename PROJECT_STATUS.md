# Project Status — BrickLayer Research HQ

**Last updated**: 2026-03-29
**Maintained by**: karen + Tim (update whenever something changes)
**Current branch**: `bricklayer-v2/mar24-parallel`

> One place to see everything.

---

## Branch Status

| Branch | Local | Remote | Notes |
|--------|-------|--------|-------|
| `bricklayer-v2/mar24-parallel` | ✅ | ✅ | Active — 66 commits ahead of remote, push needed |
| `master` | ✅ | ✅ | 1152 commits behind this branch — merge pending |
| `autopilot/signal-quality-20260323` | ✅ | ❌ | Local only — unpushed |
| `autopilot/stop-hook-fixes-20260323` | ✅ | ❌ | Local only — unpushed |
| `autopilot/mas-folder-20260323` | ✅ | ✅ | Pushed |
| `bl-audit/mar22`, `bl-audit/mar21` | ✅ | ❌ | Audit branches, local only |

**Action**: Push `bricklayer-v2/mar24-parallel` — 66 commits are unsynced.

---

## Platform Health

| Component | Status | Details |
|-----------|--------|---------|
| `masonry/bin/masonry-mcp.js` | 🟢 | 171 lines (post-split), syntax clean |
| `masonry/src/tools/` | 🟢 | 14 modules, all pass `node --check` |
| Hooks (40 total) | 🟢 | All 4 new hooks wired in `~/.claude/settings.json` |
| Agent registry | 🟢 | 101 entries: 26 trusted · 10 candidate · 65 draft |
| Global agents (`~/.claude/agents/`) | 🟢 | 79 agents |
| Project agents (`.claude/agents/`) | 🟢 | 37 agents |
| Skills (`~/.claude/skills/`) | 🟢 | fork.md, status.md, + full catalog |
| Pattern lifecycle | 🟢 | `masonry_pattern_use/quality/promote/demote` — 7 tests passing |
| Extra tools | 🟢 | `masonry_daemon`, `masonry_checkpoint` — tests passing |

---

## Campaign Projects

| Project | PENDING | Status | Last Commit |
|---------|---------|--------|-------------|
| `adbp/` | **38** | 🟡 | Paused — large queue, ready to run |
| `recall-arch-frontier/` | **9** | 🟡 | Paused — frontier questions queued |
| `projects/bl2/` | **3** | 🟡 | Paused — 3 follow-up questions |
| `recall/` | **2** | 🟡 | Near complete — 2 remaining |
| `bricklayer-meta/` | **2** | 🟡 | Near complete — 2 remaining |
| `recall-2.0/` | **0** | ⚪ | Complete or no questions.md |
| `recall-competitive/` | **0** | ⚪ | Complete or no questions.md |

---

## Platform Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | BL 2.0 Core + Masonry Foundation | ✅ |
| Phase 2 | Ecosystem Expansion (HUD, fleet CLI, plugins) | ✅ |
| Phase 3 | Runner Breadth (browser, benchmark, document, contract) | ✅ |
| Phase 4 | Recall Integration | ✅ |
| Phase 5 | Autonomy (NL entry, self-improving banks, Kiln, MCP) | ✅ |
| Phase 6 | Dev Execution Loop Upgrades (agents, hooks, skills) | ✅ |
| Phase 12 | Mortar/Trowel Split | ✅ |
| Phase 16 | Full-Fleet DSPy Training | ✅ |
| Phase 13 | BL Structural Gaps (model log, versioning, sweep gate) | 📋 |
| Phase 14 | Campaign Working Memory (14.03 only remaining) | 🔄 |
| Phase 15 | Session Intelligence (hot-path tracker, dead-ref audit) | 📋 |
| Phase 6 (original) | Campaign Quality Intelligence | 📋 |
| Phase 10 | FastMCP 3.1 Python MCP Tools | 💡 |
| Phase 11 | ADBP Monte Carlo (Rust) | 💡 |

---

## What BL 2.0 Has (as of 2026-03-29)

- **Research engine**: BL 2.0 campaign loop, 10 operational modes, adaptive follow-up, verdict history
- **Dev execution**: `/build`, `/plan`, `/verify`, `/fix`, `/ultrawork`, `/pipeline`, `/masonry-team`
- **Agent fleet**: 101 registry entries, 79 global agents, DSPy prompt optimization loop
- **Hooks**: 40 hooks wired — session, checkpoint, prompt injection, pre-compact, style, TDD, file-size, etc.
- **MCP server**: `masonry-mcp.js` 171 lines, 35+ tools across 11 focused modules
- **Pattern lifecycle**: Usage tracking + quality-gated tier promotion (draft→promoted→stale)
- **Recall integration**: Observe-edit, session summaries, cross-project memory, prompt injection
- **Kiln (BrickLayerHub)**: Desktop app for campaign monitoring, agent registry UI
- **Skills**: `/fork`, `/status`, `/build`, `/plan`, `/verify`, plus full catalog

---

## Cleanup Checklist

- [ ] Push `bricklayer-v2/mar24-parallel` (66 commits unsynced)
- [ ] Decide fate of `autopilot/signal-quality-20260323` and `autopilot/stop-hook-fixes-20260323` (local only)
- [ ] Run `adbp` campaign (38 PENDING questions waiting)
- [ ] Promote the 65 draft agents in registry via eval/optimize loop
- [ ] Phase 14.03: wire Pointer agent into Trowel every-8-questions sentinel
- [ ] Phase 15: hot-path tracker + dead-reference audit in session-start

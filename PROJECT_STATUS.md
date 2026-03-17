# Project Status — BrickLayer Research HQ

**Last updated**: 2026-03-18
**Maintained by**: git-nerd + Tim (update whenever something changes)

> One place to see everything. Run `/project-status` to regenerate from live state.

---

## Active Branches

| Branch | On GitHub | Purpose | Status |
|--------|-----------|---------|--------|
| `master` | ✅ | BL engine + all merged work | Current — work here by default |
| `recall/design` | ✅ | Recall 2.0 design workspace + frontier campaign | Pushed 2026-03-17 — safe |
| `recall/mar14` | ✅ | Recall 1.x campaign work (Wave 33+) | Pushed 2026-03-18 — safe |

**Stale remote branches to delete:**
- `origin/bl2/mar16` — merged into master via PR #1 (already deleted)

---

## Projects

### 🟢 BrickLayer 2.0 Engine — `bl/`, `template/`, `projects/bl2/`
**What it is**: The research loop engine. Agents run question campaigns against codebases.
**Status**: ACTIVE — on `master`, production-ready
**What's built**:
- 9-mode lifecycle (diagnose/fix/audit/research/validate/benchmark/evolve/monitor/predict/frontier)
- Self-healing loop (`BRICKLAYER_HEAL_LOOP=1`)
- Agent performance DB (`bl/agent_db.py`) — scores agents, flags underperformers
- Skill forge (`bl/skill_forge.py`) — distills findings → `~/.claude/skills/`
- Meta-agent fleet: overseer, skill-forge, mcp-advisor, synthesizer-bl2, git-nerd
- 10 self-audit waves complete, 14 bugs found and fixed
**Open roadmap items**: Tier 1.9, 1.10 (minor), Tier 2 (parallel execution, dashboard BL 2.0 view)
**Next action**: Start a new campaign on a real target (recall/, recall-arch-frontier/)

---

### 🟡 Recall 1.x Campaign — `recall/`
**What it is**: BrickLayer research campaign against the deployed Recall memory system.
**Status**: PAUSED — Wave 33-36 done, 2 PENDING questions remain
**Branch**: `recall/mar14` ✅ (pushed to GitHub)
**Pending questions**: 2
**Key open issues**: double-decay bug (24 consecutive FAILUREs as of Wave 33)
**Next action**: Either fix double-decay or close out this campaign (branch is safe on GitHub)

---

### 🔵 Recall 2.0 Design — `recall-2.0/`
**What it is**: Full architecture design for Recall 2.0 — built from first principles before writing code.
**Status**: PRE-FRONTIER — design complete, ready to start empirical research
**Branch**: `recall/design` ✅ (safe on GitHub)
**What's done**:
- Vision + 9 locked principles
- Full architecture docs (substrate, retrieval, decay, consolidation, consistency, injection, health)
- Competitive analysis vs mem0/Zep/MemGPT/MemGPT
- 12 open decisions, 6 rejected approaches
- 47 Frontier questions + 18 research questions ready to run
**Next action**: Fire `recall-arch-frontier/` Frontier campaign against these open decisions

---

### 🔵 Recall Architecture Frontier — `recall-arch-frontier/`
**What it is**: BrickLayer Frontier-mode campaign empirically testing Recall architecture decisions.
**Status**: IN PROGRESS — Waves 1-30 complete, 62 PENDING questions remain
**Branch**: `recall/design` ✅ (safe on GitHub)
**Total questions**: 242 across 10 domains
**Custom agents**: adversarial-pair, taboo-architect, physics-ceiling, absence-mapper, convergence-analyst, time-shifted
**Next action**: Resume from Wave 31 — `DISABLE_OMC=1 claude --dangerously-skip-permissions` in `recall-arch-frontier/`

---

### 🟡 Recall Competitive Analysis — `recall-competitive/`
**What it is**: BL campaign analyzing competing memory systems.
**Status**: EARLY — 1 question answered, 337 in bank
**Branch**: `recall/design` ✅
**Next action**: Low priority — revisit after Recall 2.0 architecture is locked

---

### ⚪ ADBP — `adbp/`
**What it is**: American Dream Benefits Program research campaign.
**Status**: DORMANT — 38 PENDING questions, no recent commits
**Branch**: Not in git (local only)
**Next action**: Decide if this campaign is still active or archive it

---

### ⚪ BrickLayer Meta-Research — `bricklayer-meta/`
**What it is**: BL campaign researching BrickLayer itself (pre-BL 2.0).
**Status**: DONE — Wave 1 complete, superseded by BL 2.0 self-audit (`projects/bl2/`)
**Next action**: Archive / no action needed

---

### ⚪ bricklayer-v2/, template-frontier/
**What they are**: Early scaffolding directories from BL 2.0 development, now superseded.
**Status**: SUPERSEDED — everything in these is in `master` now
**Next action**: Can be deleted or archived

---

## What BL 2.0 Has (Quick Reference)

Since it's easy to forget — here's what exists in the engine right now:

### Core engine (`bl/`)
`campaign.py` · `questions.py` · `findings.py` · `healloop.py` · `fixloop.py`
`config.py` · `recall_bridge.py` · `agent_db.py` · `skill_forge.py`
`runners/` (agent, http, subprocess, correctness) · `synthesizer.py` · `hypothesis.py`

### 9 Modes (`template/modes/`)
diagnose · fix · research · audit · validate · benchmark · evolve · monitor · predict · frontier

### Agent Fleet (`template/.claude/agents/`) — 22 agents
**Domain agents** (run questions): diagnose-analyst, fix-implementer, compliance-auditor,
research-analyst, quantitative-analyst, regulatory-researcher, competitive-analyst,
benchmark-engineer, cascade-analyst, design-reviewer, evolve-optimizer, health-monitor

**Utility agents** (BL 1.x): question-designer, hypothesis-generator, forge, agent-auditor, fix-agent, synthesizer

**BL 2.0 agents**: question-designer-bl2, hypothesis-generator-bl2

**Meta-agents** (fleet management): overseer, skill-forge, mcp-advisor, synthesizer-bl2, git-nerd

### Skills (`~/.claude/skills/`)
`bl-init` · `bl-run` · `bl-status`

### What auto-runs at wave end
1. `synthesizer-bl2` — writes synthesis.md + updates CHANGELOG/ARCHITECTURE/ROADMAP + commits
2. `overseer` — audits agent scores, repairs underperformers
3. `skill-forge` — distills findings → skills
4. `mcp-advisor` — maps tooling gaps → MCP recommendations
5. `git-nerd` — commits remaining changes + creates/updates PR + writes GITHUB_HANDOFF.md

---

## What's NOT Built Yet (Roadmap)

| Item | Priority | Description |
|------|----------|-------------|
| Tier 1.9 | Low | Move `_STORE_VERDICTS` to `constants.py` |
| Tier 1.10 | Low | Move `_reactivate_pending_external()` to `questions.py` |
| **Tier 2.1** | **High** | Parallel campaign execution (4-8x throughput) |
| **Tier 2.2** | **High** | Dashboard BL 2.0 view (agent scores, heal loop, skills) |
| Tier 2.3 | Med | Skill self-healing loop |
| Tier 2.4 | Med | MCP auto-installer skill |
| Tier 3.x | Future | Cross-campaign knowledge, BL 3.0 multi-campaign |

---

## Cleanup Needed

- [x] Delete remote branch `origin/bl2/mar16` (deleted 2026-03-17)
- [x] Push `recall/mar14` to GitHub (pushed 2026-03-18)
- [ ] Commit `recall-arch-frontier/simulate.py` (was excluded due to hook false-positive)
- [ ] Decide fate of `adbp/` — active or archive?
- [ ] Delete or archive `bricklayer-meta/`, `bricklayer-v2/`, `template-frontier/`
- [ ] Fix `.omc/state/` files that were accidentally committed to git (see GITHUB_HANDOFF.md)

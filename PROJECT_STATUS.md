# Project Status — BrickLayer Research HQ

**Last updated**: 2026-03-21
**Maintained by**: karen + Tim (update whenever something changes)
**Current branch**: `bricklayer-meta/mar21`

> One place to see everything.

---

## Active Branches

| Branch | On GitHub | Purpose | Status |
|--------|-----------|---------|--------|
| `master` | Yes | BL engine + all merged work | Current |
| `bricklayer-meta/mar21` | Yes | Masonry self-research campaign Wave 2 + docs update | Active |
| `recall/design` | Yes | Recall 2.0 design workspace + frontier campaign | Pushed — safe |
| `recall/mar14` | Yes | Recall 1.x campaign work (Wave 33+) | Pushed — safe |

---

## Projects

### BrickLayer 2.0 Engine — `bl/`, `template/`, `masonry/`
**Status**: ACTIVE — production-ready on `master`
**What's built**:
- 10-mode lifecycle (simulate/diagnose/fix/research/audit/validate/benchmark/evolve/monitor/predict/frontier)
- Self-healing loop (`BRICKLAYER_HEAL_LOOP=1`)
- Agent performance tracking (`bl/agent_db.py`) — score 0.0–1.0, underperformer threshold 0.40
- Skill forge (`bl/skill_forge.py`) — distills findings into `~/.claude/skills/`
- Masonry bridge: 22 hooks, four-layer routing, Pydantic v2 payload schemas
- DSPy MIPROv2 prompt optimization pipeline — full-fleet training from campaign findings
- MCP server with 7 tools (dual-transport: SDK + raw JSON-RPC 2.0 fallback)
- Plugin pack architecture (`packs/masonry-core/`, `packs/masonry-frontier/`)
- Agent registry (`masonry/agent_registry.yml`) with auto-onboarding via hook
- 30+ agents in `.claude/agents/` covering research, dev workflow, meta-fleet, and utility roles

**Recent completions (2026-03-21)**:
- Phase 16: Full-fleet DSPy training pipeline (training extractor, MIPROv2 optimizer, drift detector, 60 DSPy stubs generated)
- Hook kill switch wired (`DISABLE_OMC=1`) + auto-detection of BL project context
- `masonry-agent-onboard.js` hook + `onboard_agent.py` auto-onboarding pipeline
- MCP server expanded: 5 new tools (route, optimization_status, onboard, drift_check, registry_list)
- Four-layer routing engine: deterministic + semantic (Ollama) + LLM (Haiku) + fallback
- Pydantic v2 payload schemas: QuestionPayload, FindingPayload, RoutingDecision, DiagnosePayload, DiagnosisPayload, AgentRegistryEntry
- Three-layer agent management architecture overhaul
- **Agent** field now required in finding format for DSPy training attribution

---

### Masonry Campaign — `masonry/`
**What it is**: BL research campaign researching Masonry's own agent management architecture.
**Status**: Wave 2 COMPLETE — 28 findings, synthesis written
**Branch**: `bricklayer-meta/mar21`
**Synthesis verdict**: STOP — agent management overhaul complete, move to Phase 6
**Key findings**: Agent tier system validated; DSPy pipeline working; routing accuracy confirmed;
  hook kill switch required for campaign subprocess isolation
**Next action**: Archive this campaign, start Phase 6 (Campaign Quality Intelligence) or Recall 2.0

---

### Recall 1.x Campaign — `recall/`
**What it is**: BL research campaign against the deployed Recall memory system.
**Status**: PAUSED — Wave 33-36 done, 2 PENDING questions remain
**Branch**: `recall/mar14` (pushed to GitHub)
**Key open issue**: double-decay bug (24 consecutive FAILUREs as of Wave 33)
**Next action**: Either fix double-decay or close out this campaign

---

### Recall 2.0 Design — `recall-2.0/`
**What it is**: Full architecture design for Recall 2.0, built from first principles.
**Status**: PRE-FRONTIER — design complete, ready for empirical research
**Branch**: `recall/design` (safe on GitHub)
**What's done**: Vision + 9 locked principles, full architecture docs, competitive analysis,
  12 open decisions, 47 frontier questions + 18 research questions ready to run
**Next action**: Fire `recall-arch-frontier/` Frontier campaign against the open decisions

---

### Recall Architecture Frontier — `recall-arch-frontier/`
**What it is**: BL Frontier-mode campaign testing Recall architecture decisions empirically.
**Status**: STOP (wave 34 complete) — build Recall 2.0 now
**Branch**: `recall/design` (safe on GitHub)
**Total questions**: 242 across 10 domains

---

### ADBP — `adbp/`
**What it is**: American Dream Benefits Program simulation and research (multi-session MC campaign).
**Status**: Recent work 2026-03-21 — ADBP3 simulation expanded, Section 12 complete
**Key deliverable**: `ADBP_Research_Findings.docx` with 9 campaign sections
**Branch**: On `master` (recent commits)
**Next action**: Review findings document for delivery

---

### bricklayer-meta Campaign — `bricklayer-meta/`
**What it is**: BL research campaign researching the BrickLayer/Masonry platform itself.
**Status**: Wave 2 complete (28 findings, see Masonry Campaign above)
**Next action**: Archive — superseded by Phase 16 implementation

---

## What BL 2.0 Has (Quick Reference)

### Core engine (`bl/`)
`campaign.py` · `questions.py` · `findings.py` · `healloop.py` · `fixloop.py`
`config.py` · `recall_bridge.py` · `agent_db.py` · `skill_forge.py`
`runners/` (agent, http, subprocess, correctness, performance) · `synthesizer.py` · `hypothesis.py`
`followup.py` · `crucible.py` · `goal.py` · `history.py`

### 10 Modes (`template/modes/`)
simulate · diagnose · fix · research · audit · validate · benchmark · evolve · monitor · predict · frontier

### Agent Fleet (30+ agents in `.claude/agents/`)
**Domain agents**: quantitative-analyst · regulatory-researcher · competitive-analyst ·
benchmark-engineer · diagnose-analyst · fix-implementer · research-analyst · compliance-auditor ·
design-reviewer · evolve-optimizer · health-monitor · cascade-analyst · frontier-analyst

**Meta-agents**: overseer · skill-forge · mcp-advisor · synthesizer-bl2 · git-nerd ·
planner · question-designer-bl2 · hypothesis-generator-bl2

**Dev workflow**: spec-writer (trowel) · mortar · code-reviewer · peer-reviewer · agent-auditor ·
forge-check · pointer · karen · kiln-engineer

**Utility/BL 1.x**: question-designer · hypothesis-generator · synthesizer · retrospective

### Masonry Layer
- 22 hooks in `masonry/src/hooks/`
- Four-layer routing engine in `masonry/src/routing/`
- Pydantic v2 payload schemas in `masonry/src/schemas/`
- DSPy pipeline in `masonry/src/dspy_pipeline/` (60 generated stubs)
- MCP server in `masonry/mcp_server/server.py` (7 tools)
- Agent registry `masonry/agent_registry.yml` with auto-onboarding
- Plugin packs in `masonry/packs/`

### What auto-runs at wave end
1. `synthesizer-bl2` — writes synthesis.md + updates CHANGELOG/ARCHITECTURE/ROADMAP + commits
2. `overseer` — audits agent scores, repairs underperformers
3. `skill-forge` — distills findings → skills
4. `mcp-advisor` — maps tooling gaps → MCP recommendations
5. `git-nerd` — commits remaining changes + creates/updates PR + writes GITHUB_HANDOFF.md

---

## What's NOT Built Yet

| Item | Priority | Description |
|------|----------|-------------|
| **Phase 6.01** | High | Verdict confidence tiers — `confidence` field + `needs_human` flag |
| **Phase 6.02** | High | LLM-as-Judge peer reviewer scoring, re-queue low-quality INCONCLUSIVEs |
| **Phase 6.03** | Med | Question sharpening — retroactively narrow PENDING questions from INCONCLUSIVE findings |
| **Phase 6.04** | Med | Shared campaign context injection (campaign-context.md at wave start) |
| **Phase 6.05** | Med | Agent performance time-series in agent_db.json + Kiln sparklines |
| **Phase 6.06** | Low | MCP Tool Manifest — canonical tool list, agent `tools:` declaration |
| **Phase 10** | Future | FastMCP 3.1 Python MCP tools (masonry_karen, masonry_retrospective, etc.) |

---

## Cleanup Needed

- [ ] Delete or archive `bricklayer-v2/`, `template-frontier/` (superseded)
- [ ] Fix `.omc/state/` files accidentally committed to git (see GITHUB_HANDOFF.md)
- [ ] Commit `recall-arch-frontier/simulate.py` (excluded due to hook false-positive)
- [ ] Decide fate of `adbp/` — deliver findings document, then archive or continue
- [ ] Consider deleting legacy `dashboard/` (superseded by Kiln) or marking clearly as legacy

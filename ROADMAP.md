# BrickLayer 2.0 — Roadmap

**Last updated**: 2026-03-16

Items are ordered by impact within each tier. ✅ = done, 🔧 = in progress / partially done, 📋 = designed/planned, 💡 = ideated/not designed.

---

## Tier 1 — Near-Term (Known Bugs + Quick Wins)

These are concrete, bounded changes. All should be done before starting major new campaigns.

| # | Item | What | File(s) | Notes |
|---|------|------|---------|-------|
| 1.1 | ✅ `_verdict_from_agent_output` coverage | Accepts all 30 BL 2.0 verdicts | `runners/agent.py` | Fixed in bl2 Wave 2 (F2.1) |
| 1.2 | ✅ `_NON_FAILURE_VERDICTS` completeness | DEGRADED, ALERT, UNKNOWN, BLOCKED added | `findings.py` | Fixed in bl2 Wave 2 (F2.2) |
| 1.3 | ✅ `healloop.py` alias bug | `dict(fix_result)` copy not alias | `healloop.py` | Fixed (D2.3) |
| 1.4 | ✅ `healloop.py` EXHAUSTED cycle count | `last_cycle` tracker vs hardcoded `max_cycles` | `healloop.py` | Fixed (D2.6) |
| 1.5 | ✅ `healloop.py` heal ID short_type | `_synthetic_question()` uses `"diag"` | `healloop.py` | Fixed (D2.5) |
| 1.6 | ✅ `campaign.py` heal result propagation | Identity check `healed_result is not result` | `campaign.py` | Fixed (D2.4) |
| 1.7 | ✅ `config.py` agents_dir | Set `{project_dir}/.claude/agents/` in `init_project()` | `config.py` | Fixed this session |
| 1.8 | ✅ `config.py` recall_src field | Support both `recall_src` and legacy `target_git` | `config.py` | Fixed this session |
| 1.9 | 📋 `_STORE_VERDICTS` in constants.py | Move `_STORE_VERDICTS` from `recall_bridge.py` local scope to `constants.py` | `recall_bridge.py`, `constants.py` | D7/M2.1 WARNING — no enforcement test, low risk but tidy |
| 1.10 | 📋 `_reactivate_pending_external` location | Move from `campaign.py` to `questions.py` to match spec | `questions.py`, `campaign.py` | D4 FAILURE — works where it is but violates project-brief.md |

---

## Tier 2 — Medium-Term (Features Designed, Not Yet Built)

These are planned features where the architecture is understood. Buildable in a focused session each.

### ✅ 2.0 — Git/GitHub Specialist Agent (`git-nerd`)

**What**: GitHub specialist agent that enforces proper Git workflows. Tim's described workflow was reckless commits and force-pushes — this agent teaches and enforces best practices.

**Implemented**: `template/.claude/agents/git-nerd.md`

**Covers**: branching strategy (trunk-based, BrickLayer `{project}/{mmdd}` convention), conventional commits format, PR workflow (draft → review → squash merge), protecting main, rebase vs merge vs squash decisions, release tagging (semver, annotated), pre-commit and pre-push checklists, repository hygiene (.gitignore, stale branch cleanup), emergency procedures (undo, recover deleted branch, nuke local changes).

**BrickLayer-specific**: documents campaign branch convention, synthesizer-bl2 commit format, and when to merge a campaign PR to main.

---

### 2.1 — Parallel Campaign Execution (Agent Swarm Mode)

**What**: `run_campaign_parallel()` — runs independent questions concurrently instead of sequentially. Questions with no data dependencies (different parts of the codebase, different domains) run simultaneously via Python `asyncio` or `ThreadPoolExecutor`.

**Design sketch**:
```python
# In campaign.py
def run_campaign_parallel(max_workers: int = 4) -> None:
    """Run PENDING questions in parallel where dependency graph allows."""
    # 1. Build dependency graph from question `requires:` field
    # 2. Topological sort → batches that can run simultaneously
    # 3. ThreadPoolExecutor(max_workers) per batch
    # 4. Sentinel checks between batches
```

**Requires**: Add `requires: [Q1, Q2]` field to questions.md format so dependencies are explicit. Questions without `requires` are fully parallel.

**Impact**: 4–8x throughput on large question banks. Critical for campaigns > 50 questions.

**Files**: `campaign.py`, `questions.py` (requires field parser), `program.md` update

---

### 2.2 — Dashboard BL 2.0 View

**What**: The existing React dashboard doesn't know about BL 2.0 concepts — it shows raw verdicts without mode context, doesn't display agent scores, doesn't show heal loop status.

**New dashboard panels needed**:
- **Mode distribution** — pie chart: how many questions per operational_mode
- **Agent scorecard** — reads `agent_db.json`, shows score + verdict history per agent
- **Heal loop trace** — for questions with heal cycle notes, show the state machine path
- **Skill inventory** — reads `skill_registry.json`, lists campaign-created skills with links
- **MCP recommendations** — displays `MCP_RECOMMENDATIONS.md` if present

**Files**: `dashboard/frontend/src/`, `dashboard/backend/main.py` (new endpoints for agent_db, skill_registry)

---

### 2.3 — Skill Self-Healing Loop

**What**: Skills created by skill-forge can go stale. The overseer already has a step to review registered skills, but there's no automatic trigger when a skill produces a bad result.

**Design**: Add a `skill_db` entry for each skill usage (similar to `agent_db`). When a user invokes `/wrong` or `/learn` immediately after using a skill, record a "correction" signal. The overseer picks up correction signals and rewrites the skill.

**Files**:
- `bl/skill_forge.py` — add `record_usage()`, `record_correction()` to registry
- `~/.claude/hooks/` — post-skill hook to capture correction signals
- `template/.claude/agents/overseer.md` — already has skill review step, add correction-signal detection

---

### 2.4 — MCP Auto-Installer

**What**: `MCP_RECOMMENDATIONS.md` is advisory — a human has to read it and install manually. This could be a skill `/bl-mcp-install` that reads the recommendations and applies them to `~/.claude.json`.

**Files**:
- `~/.claude/skills/bl-mcp-install/SKILL.md` — new skill
- Reads `{project}/MCP_RECOMMENDATIONS.md`
- For each critical/high-impact recommendation, adds the MCP config to `~/.claude.json`
- Requires user confirmation per MCP (interactive)

---

### 2.5 — Campaign Dependency Graph

**What**: Visual representation of question relationships — which questions caused followups, which fix waves addressed which failures, heal loop paths. Currently all implicit in `results.tsv`.

**Design**: Export `findings_graph.json` from results.tsv (parent IDs parseable from question IDs: `D1`, `D1.1`, `D1.1.R`, `F2.1`, etc.). Render as D3 force graph in dashboard.

**Files**: `bl/graph.py` (new — builds adjacency from results.tsv), `dashboard/frontend/` (new graph panel)

---

### 2.6 — RECALL_STORE_VERDICTS Constant

**What**: Small but important — `_STORE_VERDICTS` in `recall_bridge.py` is an internal set not enforced by `constants.py`. If someone adds a new significant verdict to BL 2.0, it won't auto-store to Recall until someone manually updates `recall_bridge.py`.

**Fix**: Add `RECALL_STORE_VERDICTS` frozenset to `constants.py`, import in `recall_bridge.py`.

**Files**: `constants.py` (autosearch root, not project), `recall_bridge.py`

---

## Tier 3 — Long-Term (Future Vision)

These require design work before implementation. Not tied to any specific campaign.

### 3.1 — Cross-Campaign Knowledge Transfer

**What**: Right now each campaign is isolated — `session-context.md` resets, `agent_db.json` is per-project. There's no mechanism to say "the bl2 campaign found that fix-implementer fails when the target file path is relative — carry that knowledge to the adbp campaign."

**Design**: When a finding reaches FIXED and the fix involved an agent rewrite, the overseer stores an abstract "lesson" in Recall under `domain=bricklayer-meta`. The next campaign's question-designer reads those lessons and incorporates them as context.

**Depends on**: Recall (operational), overseer lesson extraction

---

### 3.2 — BL 3.0: Multi-Campaign Coordination

**What**: Multiple campaigns running simultaneously, coordinated by a global overseer. Campaign A is researching the codebase, Campaign B is fixing what A finds, Campaign C is writing the test suite for B's fixes. Campaigns communicate via Recall and handoff files.

**Design sketch**:
- `bl/coordinator.py` — orchestrates multiple campaign processes
- Campaigns signal each other via `handoffs/handoff-{project}-{date}.md` (already exists for cross-project handoffs)
- Global Recall domain `bricklayer-coordination` for cross-campaign signals
- Priority queue — Campaign B waits for A's DIAGNOSIS_COMPLETE findings

---

### 3.3 — Dynamic Mode Ontology

**What**: The 9 modes are hardcoded in `project-brief.md` and `modes/` files. A `mode-designer` agent could discover new modes needed by a specific domain and create the mode program file + register it. E.g., a campaign against a financial system might need a `compliance-sox` mode distinct from the generic `audit` mode.

**Design**: `template/.claude/agents/mode-designer.md` — reads project-brief.md, analyzes what question types are being asked, proposes new mode program files, creates them in `modes/`.

---

### 3.4 — Frontier Mode Full Support

**What**: The `frontier` mode (PROMISING / BLOCKED / WEAK / INCONCLUSIVE) is designed for novel mechanism discovery — finding things that might be true but nobody has tested yet. Currently the `cascade-analyst.md` handles `predict` mode but there's no dedicated frontier investigator.

**Gap**: No `frontier-investigator.md` agent yet. The mode program exists but campaigns using `frontier` mode will get a generic agent response.

**Action**: Create `template/.claude/agents/frontier-investigator.md`

---

### 3.5 — Campaign Replay

**What**: Given a `results.tsv` from a past campaign, re-run only the questions that have changed dependencies (file hash changed, or a fix was applied). Like `make` for campaigns — don't re-run what hasn't changed.

**Design**:
- `bl/replay.py` — computes file hashes for `recall_src` targets referenced in findings
- If hash unchanged since last run: skip question (result is still valid)
- If hash changed: mark PENDING, re-run

---

### 3.6 — Benchmark Mode Persistence

**What**: `benchmark` mode produces CALIBRATED/UNCALIBRATED verdicts but there's no mechanism to store baselines across campaigns. If you benchmark an endpoint at 45ms p95 in one campaign and 62ms p95 in the next, the system doesn't automatically flag the regression.

**Design**: `bl/benchmarks.py` — stores baselines in `benchmarks.json`. `evolve-optimizer.md` reads previous baselines before running. Campaign result = delta from baseline, not absolute.

**Note**: `projects/bl2/benchmarks.json` already exists (empty) — the schema placeholder is there.

---

## Won't Do (Explicitly Out of Scope)

| Item | Why |
|------|-----|
| GUI question editor | Dashboard exists; questions.md format is intentionally text-first |
| Real-time streaming campaign output | Adds complexity; stderr tail covers it |
| Multi-tenant / SaaS BrickLayer | Self-hosted only — Tim's preference |
| LLM model selection per question | All agents use Claude — consistency over flexibility |
| Automatic git push of fixes | Too risky to auto-push; campaign commits but doesn't push |

---

## Dependency Map

```
Tier 1 (bugs/fixes)
  └─ all should be done ──→ enables Tier 2

Tier 2.1 (parallel execution)
  └─ requires questions.md `requires:` field (small format change)
  └─ independently buildable

Tier 2.2 (dashboard BL 2.0 view)
  └─ requires agent_db.py ✅ and skill_forge.py ✅
  └─ independently buildable

Tier 2.3 (skill self-healing)
  └─ requires skill_forge.py ✅
  └─ requires hook mechanism (lightweight)

Tier 2.4 (MCP auto-installer)
  └─ requires mcp-advisor.md ✅
  └─ independently buildable (skill only)

Tier 2.5 (campaign graph)
  └─ independently buildable
  └─ nice to have for large campaigns

Tier 3.1 (cross-campaign knowledge)
  └─ requires Recall operational ✅
  └─ requires overseer ✅
  └─ requires Tier 2 maturity

Tier 3.2 (BL 3.0 multi-campaign)
  └─ requires 3.1 ──→ requires Tier 2 maturity

Tier 3.3 (dynamic mode ontology)
  └─ independently buildable (agent only)

Tier 3.4 (frontier-investigator agent)
  └─ independently buildable ← quick win, 1 agent file
```

---

## Quick Reference: What to Build Next

**If you have 30 minutes**: Tier 1.9 or 1.10 (move `_STORE_VERDICTS` to constants.py, or relocate `_reactivate_pending_external`)

**If you have 2 hours**: Tier 3.4 — `frontier-investigator.md` agent (1 file, closes the only mode without a dedicated agent)

**If you have a half-day**: Tier 2.4 — `/bl-mcp-install` skill (reads recommendations, updates `~/.claude.json` with confirmation)

**If you have a full day**: Tier 2.1 — parallel campaign execution (highest throughput impact)

**If you want to run another campaign**: The engine is solid — Wave 4 closed all critical bugs. Run a new project and use BL 2.0 features (modes, heal loop, agent scores) in production.

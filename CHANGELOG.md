# Changelog

All notable changes to BrickLayer are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versions follow campaign waves, not semver — BrickLayer is a research framework, not a library.

**Update policy**:
- `Added` / `Changed` / `Fixed` / `Removed` entries appended by synthesizer at each wave end
- Engine-level entries (new `bl/` modules, new agents) appended by overseer when they ship
- Roadmap completions noted under `Changed` with link to finding ID

---

## [Unreleased]

*(Items built this session, not yet in a named wave)*

### Added
- `bl/agent_db.py` — agent performance tracking. Score 0.0–1.0 per agent, verdict history, underperformer detection (threshold 0.40, min 3 runs)
- `bl/skill_forge.py` — skill registry. Tracks campaign-created skills in `skill_registry.json`, provides `write_skill()` / `list_project_skills()` API
- `template/.claude/agents/overseer.md` — fleet manager meta-agent. Repairs underperforming agents, reviews stale skills, creates missing agents from FORGE_NEEDED.md, writes OVERSEER_REPORT.md
- `template/.claude/agents/skill-forge.md` — knowledge crystallization agent. Distills wave findings into `~/.claude/skills/` reusable procedures
- `template/.claude/agents/mcp-advisor.md` — tooling gap analyst. Maps INCONCLUSIVE/FAILURE patterns to missing MCP servers, writes MCP_RECOMMENDATIONS.md
- `~/.claude/skills/bl-init/` — Bootstrap new BL 2.0 project (mode selection, template copy, question design invocation)
- `~/.claude/skills/bl-run/` — Detect active project, print exact launch command with env vars
- `~/.claude/skills/bl-status/` — Show questions.md progress table + open items
- `ARCHITECTURE.md` — BL engine architecture reference (modules, agents, modes, invariants)
- `ROADMAP.md` — Tiered feature roadmap (Tier 1 bugs → Tier 3 long-term vision)
- `CHANGELOG.md` — this file
- `template/.claude/agents/synthesizer-bl2.md` — BL 2.0 wave synthesizer replacing generic synthesizer; maintains CHANGELOG/ARCHITECTURE/ROADMAP and commits at wave end
- `template/.claude/agents/git-nerd.md` — Autonomous GitHub operations agent; auto-spawned at wave end; commits remaining changes, creates/updates campaign PR, writes `GITHUB_HANDOFF.md` with exactly what Tim needs to do (usually one command or nothing)

### Changed
- `bl/config.py` — `init_project()` now sets `cfg.agents_dir = {project_dir}/.claude/agents/` (was always pointing to autosearch root `agents/`). Added dual-key support for `recall_src` / `target_git` in project.json
- `bl/campaign.py` — agent_db recording after each agent run; overseer spawned every 10 questions if underperformers found; overseer + skill-forge + mcp-advisor spawned at wave end
- `template/.claude/agents/overseer.md` — added Step 5 (skill review), skills section in OVERSEER_REPORT

---

## [BL 2.0 — Wave 4] — 2026-03-16

Self-audit campaign (`projects/bl2/`) Wave 4: critical parse_questions regex fix + 5 secondary fixes.

### Fixed
- `bl/questions.py` — parse_questions() regex was failing to parse multi-word operational modes (D3.1)
- Multiple secondary fixes applied in Wave 4 (see `projects/bl2/findings/` for D3.x, D4.x findings)

---

## [BL 2.0 — Wave 3] — 2026-03-16

Self-audit campaign Wave 3: `_STORE_VERDICTS` extraction, print fix, end-to-end validation.

### Fixed
- `bl/recall_bridge.py` — extracted `_STORE_VERDICTS` from inside `store_finding()` function scope to module level (M2.1 partial — not yet in constants.py)
- Minor print/stderr output fix

### Changed
- End-to-end heal loop validated — all 6 Wave 2 fixes confirmed working together

---

## [BL 2.0 — Wave 2] — 2026-03-16

Self-audit campaign Wave 2: 6 critical bugs fixed by the BL 2.0 engine fixing itself.

### Fixed
- `bl/runners/agent.py` — `_verdict_from_agent_output()` now accepts all 30 BL 2.0 verdicts via `_ALL_VERDICTS` frozenset. Was only accepting 4 legacy verdicts — all BL 2.0 verdicts fell through to INCONCLUSIVE (D1 / F2.1)
- `bl/findings.py` — DEGRADED, ALERT, UNKNOWN, BLOCKED added to `_NON_FAILURE_VERDICTS`. Monitor/Frontier mode verdicts were being misclassified as failures (D2 / F2.2)
- `bl/healloop.py` — `current_result = dict(fix_result)` — was alias assignment; mutating `current_result["verdict"]` was silently mutating `fix_result`, causing wrong return value (D6 / F2.3)
- `bl/campaign.py` — heal loop result propagation changed to identity check `healed_result is not result` — verdict-comparison check was discarding enriched context (D9 / F2.4)
- `bl/healloop.py` — `_synthetic_question()` now uses `short_type = "diag" if "diagnose" in agent_name else "fix"` — was hardcoded, causing agent context ID mismatch with written finding ID (D3 / F2.5)
- `bl/healloop.py` — `last_cycle` tracker added; EXHAUSTED note now reports actual exit cycle instead of always reporting `max_cycles` on early break (D5 / F2.6)

---

## [BL 2.0 — Wave 1] — 2026-03-16

Self-audit campaign Wave 1: 22 questions run against the BL engine itself. 7 FAILUREs, 1 WARNING, 1 NON_COMPLIANT found.

### Fixed *(in subsequent waves)*
- See Wave 2 entries above

### Added *(audit findings)*
- Confirmed compliant: A1 (PARKED_STATUSES), A3 (heal loop termination), A4 (Recall graceful-fail), A5 (session-context append-only), A6 (operational_mode default), A7 (agent existence checks), A8 (mode_context injection order), A9 (session_ctx prompt order), A10 (heal ID collision safety), A11 (intermediates in results.tsv), A12 (BL 1.x independence)
- Non-compliant: A2 — `_NON_FAILURE_VERDICTS` missing 4 verdicts (fixed in Wave 2)

---

## [BL 2.0 — Initial Build] — 2026-03-16

Full BL 2.0 engine implementation on top of BL 1.x foundation.

### Added
- `bl/healloop.py` — self-healing state machine. FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED/FIX_FAILED loop. Activated by `BRICKLAYER_HEAL_LOOP=1`
- `bl/recall_bridge.py` — optional Recall memory bridge. Graceful-fail: `_HTTPX_AVAILABLE` flag, 2s health timeout, 5s op timeout
- `bl/questions.py` — BL 2.0 fields: `operational_mode` (default `"diagnose"`), `resume_after` (ISO-8601), `_PARKED_STATUSES` (12 terminal verdicts), `_reactivate_pending_external()`
- `bl/findings.py` — `_NON_FAILURE_VERDICTS` frozenset (18 verdicts), `severity_map` (32 entries), `_VERDICT_CLARITY` (35 entries)
- `bl/campaign.py` — BL 2.0 additions: `_load_mode_context()`, session-context accumulator (last 2000 chars), Recall bridge integration, heal loop wiring
- `bl/runners/agent.py` — `session_ctx_block` injected between `mode_ctx_block` and `doctrine_prefix`
- `template/modes/` — 9 mode program files (diagnose, fix, research, audit, validate, benchmark, evolve, monitor, predict, frontier)
- `template/.claude/agents/` — 10 new BL 2.0 agents: diagnose-analyst, fix-implementer, research-analyst, compliance-auditor, design-reviewer, evolve-optimizer, health-monitor, cascade-analyst, question-designer-bl2, hypothesis-generator-bl2
- `projects/bl2/` — BL 2.0 self-audit campaign targeting the BL engine itself

---

## [BL 1.x — Baseline] — pre-2026-03-16

BL 1.x engine. Sequential campaign loop, single-mode (diagnose), optional fix loop via `BRICKLAYER_FIX_LOOP=1`.

Core: `campaign.py`, `questions.py`, `findings.py`, `runners/`, `history.py`, `synthesizer.py`, `hypothesis.py`, `followup.py`

Agent fleet: forge, forge-check, peer-reviewer, agent-auditor, fix-agent, retrospective, question-designer, hypothesis-generator, quantitative-analyst, regulatory-researcher, competitive-analyst, benchmark-engineer

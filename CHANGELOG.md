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
- `bl/agent_db.py` — agent performance tracking. Score 0.0-1.0 per agent, verdict history, underperformer detection (threshold 0.40, min 3 runs)
- `bl/skill_forge.py` — skill registry. Tracks campaign-created skills in `skill_registry.json`, provides `write_skill()` / `list_project_skills()` API
- `template/.claude/agents/overseer.md` — fleet manager meta-agent. Repairs underperforming agents, reviews stale skills, creates missing agents from FORGE_NEEDED.md, writes OVERSEER_REPORT.md
- `template/.claude/agents/skill-forge.md` — knowledge crystallization agent. Distills wave findings into `~/.claude/skills/` reusable procedures
- `template/.claude/agents/mcp-advisor.md` — tooling gap analyst. Maps INCONCLUSIVE/FAILURE patterns to missing MCP servers, writes MCP_RECOMMENDATIONS.md
- `~/.claude/skills/bl-init/` — Bootstrap new BL 2.0 project (mode selection, template copy, question design invocation)
- `~/.claude/skills/bl-run/` — Detect active project, print exact launch command with env vars
- `~/.claude/skills/bl-status/` — Show questions.md progress table + open items
- `ARCHITECTURE.md` — BL engine architecture reference (modules, agents, modes, invariants)
- `ROADMAP.md` — Tiered feature roadmap (Tier 1 bugs -> Tier 3 long-term vision)
- `CHANGELOG.md` — this file
- `template/.claude/agents/synthesizer-bl2.md` — BL 2.0 wave synthesizer replacing generic synthesizer; maintains CHANGELOG/ARCHITECTURE/ROADMAP and commits at wave end
- `template/.claude/agents/git-nerd.md` — Autonomous GitHub operations agent; auto-spawned at wave end; commits remaining changes, creates/updates campaign PR, writes `GITHUB_HANDOFF.md` with exactly what Tim needs to do (usually one command or nothing)

### Changed
- `bl/config.py` — `init_project()` now sets `cfg.agents_dir = {project_dir}/.claude/agents/` (was always pointing to autosearch root `agents/`). Added dual-key support for `recall_src` / `target_git` in project.json
- `bl/campaign.py` — agent_db recording after each agent run; overseer spawned every 10 questions if underperformers found; overseer + skill-forge + mcp-advisor spawned at wave end
- `template/.claude/agents/overseer.md` — added Step 5 (skill review), skills section in OVERSEER_REPORT

---

## [BL 2.0 -- Wave 25] -- 2026-03-17

Scorer calibration wave: 4 questions. Frontmatter-position guards applied to design-reviewer and fix-implementer scorers.

### Fixed
- `F25.1` -- `_score_design_reviewer` bare regex replaced with frontmatter-position guard (`bl/crucible.py`)
- `F25.2` -- `_score_fix_implementer` FIXED guard replaced with frontmatter-position check; weak fallback dropped (`bl/crucible.py`)

### Found (open)
- `D25.1` [DIAGNOSIS_COMPLETE] -- `check_block()` uses BL 1.x field names (`Test:`, `Hypothesis:`); BL 2.0 uses `**Method**:` and `**Hypothesis**:`; weight 0.30 zeroed

### Healthy
- V25.1 -- fix-implementer 0.9708 (up from 0.9643), design-reviewer 0.7104 (expected narrowing), no regression

---

## [BL 2.0 -- Wave 24] -- 2026-03-17

Scorer calibration: hypothesis-generator field name fix, compliance-auditor frontmatter guard.

### Fixed
- `F24.1` -- `_score_hypothesis_generator` now accepts "Motivated by" (BL 2.0) alongside "Derived from" (BL 1.x); score 0.15->0.37 (`bl/crucible.py`)
- `F24.2` -- `_score_compliance_auditor` NON_COMPLIANT guard replaced with frontmatter-position check (`bl/crucible.py`)

### Found (open)
- `A24.1` [NON_COMPLIANT] -- design-reviewer and fix-implementer scorers use bare verdict scans (fixed in Wave 25)

### Healthy
- V24.1 -- hypothesis-generator score verified: 0.15->0.37, delta matches predicted weight contribution

---

## [BL 2.0 -- Wave 23] -- 2026-03-17

Scorer audit: synthesizer mid-campaign behavior, hypothesis-generator field mismatch root cause.

### Found (open)
- `D23.1` [DIAGNOSIS_COMPLETE] -- hypothesis-generator "Derived from" vs "Motivated by" field mismatch (fixed in Wave 24)
- `A23.1` [NON_COMPLIANT] -- compliance-auditor bare substring scan (fixed in Wave 24)

### Healthy
- V23.1 -- synthesizer score=0.0 expected mid-campaign (synthesis.md absent by design)
- D23.2 -- 12 pre-template findings missing Fix Spec is historical gap, not defect

---

## [BL 2.0 -- Wave 22] -- 2026-03-17

Frontmatter-position guard for diagnose-analyst; fix-implementer prefix guard verified.

### Fixed
- `F22.1` -- frontmatter-position guard applied to `_score_diagnose_analyst`; false positives excluded (`bl/crucible.py`)

### Healthy
- V22.1 -- fix-implementer score stable (0.9628); D-mid.4 excluded from fix_rows
- V22.2 -- HEAL_EXHAUSTED badge renders correctly in dashboard

---

## [BL 2.0 -- Wave 21] -- 2026-03-17

Dashboard BL 2.0 status colors and fix-implementer scoping.

### Fixed
- `F21.1` -- QuestionQueue STATUS_COLORS updated with HEAL_EXHAUSTED and 7 BL 2.0 statuses (`dashboard/frontend`)
- `F21.2` -- `_score_fix_implementer` fix_rows scoped via `_is_fix_row()` F-prefix guard (`bl/crucible.py`)

### Found (open)
- `D21.1` [DIAGNOSIS_COMPLETE] -- fix_spec_completeness=0.29 root cause: 12 pre-template findings + 4 false positives

---

## [BL 2.0 -- Wave 20] -- 2026-03-17

Scorer verification and dashboard audit.

### Found (open)
- `A20.1` [NON_COMPLIANT] -- QuestionQueue missing HEAL_EXHAUSTED status (fixed in Wave 21)
- `A20.2` [NON_COMPLIANT] -- fix-implementer fix_rows has no F-prefix guard (fixed in Wave 21)

### Healthy
- V20.1, V20.2 -- `_is_bl2_diag_row()` edge cases correct; DIAGNOSIS_COMPLETE frontmatter coverage verified
- D20.1 -- dc_rate=1.00 post-F19.1 benchmark verified

---

## [BL 2.0 -- Wave 19] -- 2026-03-17

Crucible scorer scoping: dc_rate BL 1.x contamination and fix_spec false positive elimination.

### Fixed
- `F19.1` -- `_score_diagnose_analyst` dc_rate scoped to BL 2.0 D-prefix rows via `_is_bl2_diag_row()` (`bl/crucible.py`)
- `F19.2` -- fix_spec_completeness guard changed to exact `**Verdict**: DIAGNOSIS_COMPLETE` match (`bl/crucible.py`)

---

## [BL 2.0 -- Waves 18] -- 2026-03-17

Scorer verification: parse_questions hoist confirmed, HEAL_EXHAUSTED writeback verified.

### Found (open)
- `V18.1` [NON_COMPLIANT] -- dc_rate denominator includes BL 1.x FAILURE rows (fixed in Wave 19)
- `V18.2` [NON_COMPLIANT] -- fix_spec substring match admits false positives (fixed in Wave 19)

### Healthy
- A18.1 -- parse_questions() hoist confirmed at lines 396-398
- D18.1 -- HEAL_EXHAUSTED writeback path complete
- D18.2 -- fix_rows scoped correctly for current campaign

---

## [BL 2.0 -- Wave 17] -- 2026-03-16

BL 2.0 crucible scorers implemented; mid-wave fixes verified; performance hoist applied.

### Fixed
- `F17.1` -- 4 BL 2.0 scorer functions added to `crucible.py` and registered in `_SCORERS` (`bl/crucible.py`)

### Found (open)
- `A17.1` [NON_COMPLIANT] -- parse_questions() called inside per-finding loop; O(N) parses (fixed in same session)

### Healthy
- V17.1 -- all 5 Wave-mid fixes verified; no BL 1.x regressions
- D17.1 -- background spawns are mode-insensitive by design
- D17.2 -- _ALL_VERDICTS contains all BL 2.0 verdicts

---

## [BL 2.0 -- Wave 16 (mid)] -- 2026-03-16

Mid-wave fix cycle: 5 critical fixes applied for heal loop, peer-reviewer, text parsing, summary extraction.

### Fixed
- `F-mid.1` -- healloop.py exhausted path now calls `update_results_tsv(original_qid, HEAL_EXHAUSTED)`; HEAL_EXHAUSTED added to frozensets in 4 files (`bl/healloop.py`, `bl/findings.py`, `bl/questions.py`, `bl/history.py`)
- `F-mid.2` -- peer-reviewer spawn guarded by `mode != code_audit` (`bl/campaign.py`)
- `F-mid.3` -- `_parse_text_output()` else clause for BL 2.0 agents; regex extraction for `^verdict:` and `^summary:` (`bl/runners/agent.py`)
- `D-mid.4` -- `_summary_from_agent_output()` early-return for `output.get("summary")` (`bl/runners/agent.py`)
- `F-mid.5` -- pending-list refresh documented as intentional design (`bl/campaign.py`)

---

## [BL 2.0 -- Wave 16] -- 2026-03-16

Deep heal loop and campaign loop audit: 5 diagnoses, crucible scorer design validation.

### Found (open)
- `D16.1` [DIAGNOSIS_COMPLETE] -- healloop exhausted path never calls update_results_tsv (fixed in Wave 16-mid)
- `D16.2` [DIAGNOSIS_COMPLETE] -- peer-reviewer spawned unconditionally for code_audit (fixed in Wave 16-mid)
- `D16.3` [DIAGNOSIS_COMPLETE] -- `_parse_text_output()` no else clause for BL 2.0 (fixed in Wave 16-mid)
- `A16.1` [NON_COMPLIANT] -- enumerate iterator bound to original pending list (documented as intentional)

### Healthy
- V16.1 -- `_SCORERS` dict and `AgentScore` fields validated for BL 2.0 scorer additions

---

## [BL 2.0 -- Wave 15] -- 2026-03-16

crucible.py and questions.py BL 2.0 compat fixes. 5 questions, 2 critical fixes.

### Fixed
- `F15.1` -- `questions.py` sync_status sentinel changed from `"\n## Q"` to `"\n## "` (`bl/questions.py`)
- `F15.2` -- `crucible.py`: _KNOWN_AGENTS +4 BL 2.0 agents; domains_covered uses prefix detection; synthesizer regex and qa glob fixed (`bl/crucible.py`)

### Found (open)
- `A15.1` [NON_COMPLIANT] -- _KNOWN_AGENTS missing BL 2.0 agents (fixed by F15.2)
- `D15.2` [DIAGNOSIS_COMPLETE] -- question_designer domains_covered D1-D6 hardwired
- `D15.3` [DIAGNOSIS_COMPLETE] -- synthesizer regex and qa glob score 0 on BL 2.0

### Healthy
- D15.4 -- agent_db.py verdict handling covers all 30 BL 2.0 verdicts

---

## [BL 2.0 -- Wave 14] -- 2026-03-16

goal.py + synthesizer.py BL 2.0 compat fixes. 5 questions, 2 critical fixes.

### Fixed
- `F14.1` -- goal.py wave-index scans BL 2.0 headers; focus default and prompt examples use BL 2.0 operational modes (`bl/goal.py`)
- `F14.2` -- synthesizer.py writes to `findings/synthesis.md`; DIAGNOSIS_COMPLETE and FIX_FAILED added to _HIGH_SEVERITY (`bl/synthesizer.py`)

### Healthy
- V14.1 -- skill_forge.py and quality.py have no BL version-specific logic

---

## [BL 2.0 -- Wave 13] -- 2026-03-16

followup.py sub-question quality fixes. 4 questions, 2 fixes.

### Fixed
- `F13.1` -- `_build_followup_prompt()` uses `or` fallback for agent_name; `**Operational Mode**` field added to sub-question template (`bl/followup.py`)
- `F13.2` -- `_parse_followup_blocks()` bracket tag injection uses `_OP_MODE_TO_TAG` from Operational Mode field (`bl/followup.py`)

---

## [BL 2.0 -- Wave 12] -- 2026-03-16

Regression detection, failure classification, follow-up coverage. 5 questions, 3 fixes.

### Fixed
- `F12.1` -- 8 BL 2.0 regression pairs added to `_REGRESSIONS` (`bl/history.py`)
- `F12.2` -- `classify_failure_type_local()` handles NON_COMPLIANT/REGRESSION; _SYSTEM_PROMPT updated (`bl/findings.py`)
- `F12.3` -- NON_COMPLIANT added to C-04 follow-up guards (`bl/campaign.py`, `bl/followup.py`)

---

## [BL 2.0 -- Wave 11] -- 2026-03-16

crucible.py scorer patterns, sync_status preservation, findings corpus bias. 4 questions, 3 fixes.

### Fixed
- `F11.1` -- crucible.py scorers use wave-number extraction from IDs and \w+-prefixed block regex (`bl/crucible.py`)
- `F11.2` -- `sync_status_from_results()` preserve set extended with FAILURE/NON_COMPLIANT/WARNING/REGRESSION/ALERT (`bl/questions.py`)
- `F11.3` -- `_build_findings_corpus()` sorts by severity (FAILURE first), drops low-severity first under budget (`bl/synthesizer.py`)

---

## [BL 2.0 -- Wave 10] -- 2026-03-16

Hypothesis generation BL 2.0 compat. 4 questions, 2 fixes.

### Fixed
- `F10.1` -- `_parse_question_blocks()` regex accepts BL 2.0 ID prefixes (`bl/hypothesis.py`)
- `F10.2` -- `parse_recommendation()` scans only after "Recommended Next Action" header (`bl/hypothesis.py`)

### Found (open)
- `A10.1` [NON_COMPLIANT] -- `pop(0)` on alphabetical sort drops A*/D* findings before V* under budget pressure

---

## [BL 2.0 -- Wave 9] -- 2026-03-16

Wave detection and agent tracking BL 2.0 compat. 4 questions, 2 fixes.

### Fixed
- `F9.1` -- `_QUESTION_BLOCK_HEADER` regex changed to `[\w][\w.-]*`; wave detection returns correct wave number (`bl/hypothesis.py`)
- `F9.2` -- agent_db condition expanded to `mode in ("agent","code_audit")` (`bl/campaign.py`)

### Healthy
- A9.1 -- "DONE" in _SUCCESS_VERDICTS is dead code but harmless

---

## [BL 2.0 -- Wave 8] -- 2026-03-16

Override injection and status preservation. 4 questions, 2 fixes.

### Fixed
- `F8.1` -- `glob("Q*.md")` changed to `glob("*.md")` for override peer review scanning (`bl/campaign.py`)
- `F8.2` -- FAILURE/NON_COMPLIANT/WARNING/REGRESSION/ALERT added to `_PRESERVE_AS_IS` (`bl/questions.py`)

### Healthy
- A8.1 -- all 10 BL 2.0 operational mode files present; `_load_mode_context()` silent fallback acceptable

---

## [BL 2.0 -- Wave 7] -- 2026-03-16

Verdict extraction else-branch and C-04 adaptive drill-down. 4 questions, 2 fixes.

### Fixed
- `F7.1` -- `self_verdict_early` checked first in else-branch; BL 2.0 agent verdicts now surfaced (`bl/runners/agent.py`)
- `F7.2` -- `_is_leaf_id()` else-branch uses dot-count for BL 2.0 IDs (`bl/followup.py`)

### Healthy
- A7.1 -- followup sub-question IDs, block headers, mode fields all BL 2.0 compatible

---

## [BL 2.0 -- Wave 6] -- 2026-03-16

Runner dispatch and results.tsv format. 4 questions, 2 fixes.

### Fixed
- `F6.1` -- `register("code_audit", run_agent)` added to `_register_builtins()` (`bl/runners/__init__.py`)
- `F6.2` -- results.tsv rewritten in BL 2.0 format (qid first) (`projects/bl2/results.tsv`)

---

## [BL 2.0 -- Wave 5] -- 2026-03-16

Question Mode dispatch and bracket tag classification. 3 questions, 1 fix.

### Fixed
- `F5.1` -- `parse_questions()` uses `fields.get("mode", mode_raw)` for body Mode field dispatch (`bl/questions.py`)

### Healthy
- A5.1 -- all BL 2.0 bracket tags correctly classified; no C-30 cap misfire
- V5.1 -- all 7 BL 2.0 pipeline stages verified correct after Waves 1-5

---

## [BL 2.0 -- Wave 4] -- 2026-03-16

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

# Changelog

All notable changes to BrickLayer 2.0 / Masonry are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versions follow campaign waves and milestone builds, not semver — this is a research framework.

**Update policy:**
- `Added` / `Changed` / `Fixed` / `Removed` entries appended by synthesizer at each wave end
- Engine-level entries (new `bl/` modules, new agents) appended by overseer when they ship
- Roadmap completions noted under `Changed` with link to finding ID

---

## [Unreleased]

*Items in the working tree — committed but awaiting the next named release or wave.*

### Added
- `bl/agent_db.py` — agent performance tracking. Score 0.0–1.0 per agent, verdict history, underperformer detection (threshold 0.40, min 3 runs)
- `bl/skill_forge.py` — skill registry. Tracks campaign-created skills in `skill_registry.json`, provides `write_skill()` / `list_project_skills()` API
- `bl/tracer.py` — introspection decorator. Per-step trace `{thought, tool_call, result, tokens, latency, confidence, error_type}` written to Recall
- `template/.claude/agents/overseer.md` — fleet manager meta-agent. Repairs underperforming agents, reviews stale skills, creates missing agents from FORGE_NEEDED.md, writes OVERSEER_REPORT.md
- `template/.claude/agents/skill-forge.md` — knowledge crystallization agent. Distills wave findings into `~/.claude/skills/` reusable procedures
- `template/.claude/agents/mcp-advisor.md` — tooling gap analyst. Maps INCONCLUSIVE/FAILURE patterns to missing MCP servers, writes MCP_RECOMMENDATIONS.md
- `template/.claude/agents/git-nerd.md` — autonomous GitHub operations agent. Commits remaining changes, creates/updates campaign PR, writes `GITHUB_HANDOFF.md`
- `template/.claude/agents/synthesizer-bl2.md` — BL 2.0 wave synthesizer replacing generic synthesizer. Maintains CHANGELOG/ARCHITECTURE/ROADMAP and commits at wave end
- `template/.claude/agents/frontier-analyst.md` — exploration-mode agent. Possibility mapping, analogue identification, feasibility tiers. `FRONTIER_VIABLE/PARTIAL/BLOCKED` verdicts
- `template/.claude/agents/kiln-engineer.md` — specialist agent for Kiln (BrickLayerHub Electron app) changes
- `template/.claude/agents/planner.md` — pre-campaign strategic planner. D1–D6 domain risk ranking, writes CAMPAIGN_PLAN.md
- `template/.claude/agents/mortar.md` — campaign conductor agent. Owns the loop, routes questions, fires sentinels, handles OVERRIDE re-queuing
- `template/.claude/agents/code-reviewer.md` — pre-commit quality gate. Diff review, lint, regression check, APPROVED/NEEDS_REVISION/BLOCKED
- `template/docs/question-schema.md` — canonical BL 2.0 question schema reference. All fields, Mode routing table, common mistakes
- `template/docs/design-philosophy.md` — Masonry design principles and architectural patterns
- `dashboard/frontend/src/components/AgentFleet.tsx` — agent fleet tab with tier filter pills, score cards, summary footer
- `masonry/` — Masonry package scaffold. Phase 1 hooks, installer, skills; Phase 2 spec written
- `masonry/src/hooks/masonry-statusline.js` — ANSI 24-bit campaign statusline with progress, verdicts, context %
- `masonry/src/hooks/masonry-register.js` — UserPromptSubmit hook: Recall context injection, resume detection, guard flush
- `masonry/src/hooks/masonry-observe.js` — PostToolUse async: finding detection → Recall, activity log
- `masonry/src/hooks/masonry-guard.js` — PostToolUse async: 3-strike error fingerprinting
- `masonry/src/hooks/masonry-stop.js` — Stop hook: session summary via Ollama → Recall, temp cleanup
- `masonry/bin/masonry-setup.js` — interactive setup wizard. Writes config, merges hooks into settings.json, smoke-checks Recall
- `masonry/skills/masonry-run.md`, `masonry-status.md`, `masonry-init.md` — core Masonry skills
- `masonry/.autopilot/spec.md` — ecosystem expansion spec (ultrawork, pipeline, masonry-team, fleet CLI, rich HUD, packs)
- `~/.claude/skills/bl-init/`, `bl-run/`, `bl-status/` — global BL 2.0 convenience skills
- `tests/test_goal.py`, `test_results_tsv_eval_score.py`, `test_runner_registry.py`, `test_tracer.py` — new test coverage
- `ARCHITECTURE.md` — BL engine architecture reference (modules, agents, modes, invariants)
- `GITHUB_HANDOFF.md` — git-nerd output: campaign PR state and next human action
- `recall-arch-frontier/` — Recall 2.0 architecture research campaign (Waves 1–34)
- `projects/recall2/` — Recall 2.0 Rust codebase scaffold
- `projects/MarchMadness/` — new research project

### Changed
- `bl/campaign.py` — agent_db recording after each agent run; overseer spawned every 10 questions if underperformers found; overseer + skill-forge + mcp-advisor spawned at wave end
- `bl/config.py` — `init_project()` now sets `cfg.agents_dir = {project_dir}/.claude/agents/`. Added dual-key support for `recall_src` / `target_git` in project.json
- `bl/goal.py` — wave-index scans BL 2.0 headers; focus default and prompt examples updated for BL 2.0 operational modes
- `bl/runners/agent.py` — `_read_frontmatter_model()` added; `--model <full-id>` passed to every `claude -p` subprocess; `session_ctx_block` injected between `mode_ctx_block` and `doctrine_prefix`; self_verdict_early checked first in else-branch
- `dashboard/backend/main.py` — `GET /api/agents` endpoint added for agent fleet data
- `dashboard/frontend/src/App.tsx` — tab bar added (Findings | Agents)
- `dashboard/frontend/src/components/QuestionQueue.tsx` — STATUS_COLORS updated with HEAL_EXHAUSTED and all BL 2.0 statuses
- `dashboard/frontend/src/lib/api.ts` — fleet agent API client
- `template/.claude/agents/overseer.md` — added Step 5 (skill review), skills section in OVERSEER_REPORT
- All 12 BL 1.x template agents upgraded with `## Inputs`, `## Output contract`, `## Recall` sections and BL 2.0 verdicts
- All 27 template agents updated with `model:` frontmatter (opus/sonnet/haiku)
- Planner → QD-BL2 interface repaired: planner writes BL 2.0 Mode Allocation table; question-designer-bl2 reads CAMPAIGN_PLAN.md pre-flight
- CLAUDE.md project instructions updated with planner → qd-bl2 two-step workflow and expanded agent reference table
- `MASONRY-FRAMEWORK.md` removed (superseded by `masonry/` package)
- Repo renamed: `autosearch` → `Bricklayer2.0`. All hardcoded paths updated

### Fixed
- `D25.1` — `check_block()` in `_score_hypothesis_generator` used BL 1.x field names (`Test:`, `Hypothesis:`); updated to BL 2.0 (`**Method**:`, `**Hypothesis**:`)
- `A10.1` — `_build_findings_corpus()` alphabetical sort bias; severity sort now applied before trimming (F11.3)
- `agent-meta/simulate.py` — block scalar description parser handles `description: >` multi-line YAML blocks
- `agent-meta/simulate.py` — `score_agent()` two-phase heading+body scan; `len(body_text) < 10` → -20 penalty (hollow section bypass fix)
- 3 bare `except Exception: pass` → logged stderr warnings across the codebase

---
- `ce5609e` fix(masonry-register): parallelize Recall calls to fit within 8s hook budget (2026-03-21)
- `55d27f6` feat(masonry): OMC gap fills — plan approval UX, SessionEnd, PreCompact hooks (2026-03-21)
- `cd8abfd` fix(masonry): add fetch timeouts to recall.js + extend mortar to handle dev requests (2026-03-21)
- `6d42ae2` feat(session-start): auto-detect BL projects and inject run commands (2026-03-21)
- `2d9e25c` feat(adbp3): extend MC to 240mo, multi-seed, stochastic employee growth (2026-03-20)
- `1e91afc` fix(wiring): resolve all BL 2.0 framework wiring gaps from audit (2026-03-20)
- `4490835` chore: session cleanup — template updates, frontier agents, new global agents (2026-03-20)
- `a7255ba` feat: parallel BL campaign launcher for Windows (2026-03-20)
- `7c4c86e` chore: session files — CHANGELOG + ADBP3 system rules doc (2026-03-20)
- `8a0b1a7` docs(adbp3): add System Rules v3 as editable Word document (2026-03-20)
- `732e489` docs(adbp3): regenerate PDF with clean original-style formatting (2026-03-20)
- `f604d19` docs(adbp3): apply user edits to System Rules v3 markdown (2026-03-20)
- `c7616fe` docs(adbp3): generate System Rules v3 PDF (2026-03-20)
- `63f7aad` docs(adbp3): add System Rules v3 reflecting confirmed model mechanics (2026-03-20)
- `e35839b` feat(adbp3): init project + MC campaign findings + final model (2026-03-20)
- `143f0a5` fix(adbp2): replace stale admin_fees_paid ref with operator_revenue in plot_charts (2026-03-20)
- `86e97c8` chore(adbp2): extend simulation to 120 months + updated results (2026-03-20)
- `36dda5e` chore: update results snapshot (2026-03-20)
- `71169a2` chore: update results snapshot (2026-03-20)
- `3e6ffdd` fix: zero-burn guard when minting is paused (emergency protocol) (2026-03-20)
- `25b2bd9` chore: update results snapshot (2026-03-20)
- `19791d7` fix(tasks9-13): replace phantom admin_fee_floor/cap with fee_to_operator_pct in all Python test params, fix ruff/clippy lint errors, fix _make_params_dict to self-import constants — 56/56 tests passing (2026-03-20)
- `59c4001` feat(task10): MC + stats Rust updates + simulate.py sync (2026-03-20)
- `87b9818` feat(task9): stats tests + parity test updates (2026-03-20)
- `369910c` feat(rust+tests): MC engine updates + test suite sync for 65/35 model (2026-03-20)
- `f5a5b08` feat(rust): update params + sim engine for 65/35 fee split model (2026-03-20)
- `f292cbf` feat(task8): MC parity tests + test scaffolding + results snapshot (2026-03-20)
- `be0ee3a` feat(model): lock in 65/35 fee split — escrow/operator, remove dynamic admin fee (2026-03-20)
- `f60a3e9` feat(task7): Monte Carlo orchestrator + output tests + results snapshot (2026-03-20)
- `1dfba59` feat(task6): MC Python fallback + fallback tests (2026-03-20)
- `abc066d` feat(task5+7+8): stats/MC runner modules + complete lib.rs exports (2026-03-20)
- `d366025` feat(task4-5): MC sampling + stats modules; fix build guard session isolation (2026-03-20)
- `6e6847f` feat(task3+6): Rust simulation engine + full parity tests (2026-03-20)
- `de1f30b` feat(task3): Rust deterministic sim engine + parity test scaffold (2026-03-20)
- `61c33e6` feat(task2): SimParams + MCDistributionConfig structs with PyO3 bindings (2026-03-20)
- `0631e0b` feat(task2): SimParams + MCDistributionConfig structs + changelog update (2026-03-20)
- `edcbe8e` feat(task1): Rust crate scaffolding — Cargo.toml + pyproject.toml + stub lib.rs (2026-03-20)
- `16aa905` chore: commit stale findings file from prior session (2026-03-20)
- `a1b6ac6` fix: quantitative-analyst wave-partitioned findings path (2026-03-20)
- `2dfa504` autopilot: tasks #5 #6 — Recall orchestrator hook + JSON validation gate (2026-03-20)
- `d18fd29` autopilot: task #6 — JSON output validation gate (2026-03-20)
- `8211ed6` autopilot: task #4 — wave-partitioned findings paths across agent files (2026-03-20)
- `8969d77` autopilot: task #3 — Trowel pointer sentinel + selective context injection (2026-03-20)
- `2e0d8e7` autopilot: tasks #1 #2 — scratch.md signal board + pointer agent (2026-03-20)
- `f8bfdd1` chore(phase14): stage scratch.py, pointer agent, and test stubs (2026-03-20)
- `94313fa` chore(adbp2): add Rust build artifacts and .autopilot to .gitignore (2026-03-20)
- `567d79e` docs(roadmap): add Phase 15 — Session Intelligence (hot path tracking + dead ref audit) (2026-03-19)
- `d589ce7` fix(hooks): scope tool-failure error state per-project; drop dead OMC refs (2026-03-19)
- `5db1466` research: similar repos structural comparison — BL 2.0 is Pattern C, confirmed correct foundation (2026-03-19)
- `4a6c2f0` roadmap: add Phase 14 — Campaign Working Memory (pointer agent + scratch.md) (2026-03-19)
- `6a0b83d` research: shared scratchpad patterns for multi-agent pipelines (2026-03-19)
- `9dc86c5` fix(trowel): placeholder check at startup — auto-invoke question-designer if questions.md is template (2026-03-19)
- `e415dbc` feat(bl2): Mortar/Trowel ecosystem sync + permissions fix (2026-03-19)
- `a6f3d46` feat(agents): Mortar/Trowel split — lean router + campaign conductor (2026-03-19)
- `f941882` fix(lint-hook): warn-only, remove ruff --fix during active development (2026-03-19)
- `4061a09` feat(roadmap): add Phase 11 ADBP Monte Carlo simulation engine (2026-03-19)
- `c5d20fd` feat(mortar): wire /hats skill for strategic campaign decisions (2026-03-19)
- `13c921f` chore: remove BL 1.x question-designer and unused bl/campaign.py (2026-03-19)
- `dcfebff` fix(wiring): sync mortar.md to all project copies + Phase 10 FastMCP roadmap (2026-03-19)
- `8b07cf3` feat(kiln-os): init project folder — AI OS ideation + roadmap (2026-03-19)
- `1fd7a58` autopilot: phase9 — mortar.md wiring updates (2026-03-19)
- `177b634` chore: update CHANGELOG [skip-hook] (2026-03-19)
- `a23f45f` feat(hooks): auto-resume interrupted build on session start (2026-03-19)
- `45e0385` chore: CHANGELOG.md post-hook entries (2026-03-18)
- `d68c6a2` feat(phase9): Task 7 — Kiln typecheck clean + build success (2026-03-18)
- `a240251` autopilot: Phase 9 complete — update CHANGELOG.md (2026-03-18)
- `fb588ec` feat(phase9): Task 6 — activate global git hooks path (2026-03-18)
- `4749f10` autopilot: phase9 task 6 — activate global hooks path + pytest.ini (2026-03-18)

## [BL 2.0 — Wave 25] — 2026-03-17

Scorer calibration wave: 4 questions. Frontmatter-position guards applied to design-reviewer and fix-implementer scorers.

### Fixed
- `F25.1` — `_score_design_reviewer` bare regex replaced with frontmatter-position guard (`bl/crucible.py`)
- `F25.2` — `_score_fix_implementer` FIXED guard replaced with frontmatter-position check; weak fallback dropped (`bl/crucible.py`)

### Found (open)
- `D25.1` [DIAGNOSIS_COMPLETE] — `check_block()` uses BL 1.x field names (`Test:`, `Hypothesis:`); BL 2.0 uses `**Method**:` and `**Hypothesis**:`; weight 0.30 zeroed

### Healthy
- V25.1 — fix-implementer 0.9708 (up from 0.9643), design-reviewer 0.7104 (expected narrowing), no regression

---

## [BL 2.0 — Wave 24] — 2026-03-17

Scorer calibration: hypothesis-generator field name fix, compliance-auditor frontmatter guard.

### Fixed
- `F24.1` — `_score_hypothesis_generator` now accepts "Motivated by" (BL 2.0) alongside "Derived from" (BL 1.x); score 0.15→0.37 (`bl/crucible.py`)
- `F24.2` — `_score_compliance_auditor` NON_COMPLIANT guard replaced with frontmatter-position check (`bl/crucible.py`)

### Found (open)
- `A24.1` [NON_COMPLIANT] — design-reviewer and fix-implementer scorers used bare verdict scans (fixed in Wave 25)

### Healthy
- V24.1 — hypothesis-generator score verified: 0.15→0.37, delta matches predicted weight contribution

---

## [BL 2.0 — Wave 23] — 2026-03-17

Scorer audit: synthesizer mid-campaign behavior, hypothesis-generator field mismatch root cause.

### Found (open)
- `D23.1` [DIAGNOSIS_COMPLETE] — hypothesis-generator "Derived from" vs "Motivated by" field mismatch (fixed in Wave 24)
- `A23.1` [NON_COMPLIANT] — compliance-auditor bare substring scan (fixed in Wave 24)

### Healthy
- V23.1 — synthesizer score=0.0 expected mid-campaign (synthesis.md absent by design)
- D23.2 — 12 pre-template findings missing Fix Spec is historical gap, not defect

---

## [BL 2.0 — Wave 22] — 2026-03-17

Frontmatter-position guard for diagnose-analyst; fix-implementer prefix guard verified.

### Fixed
- `F22.1` — frontmatter-position guard applied to `_score_diagnose_analyst`; false positives excluded (`bl/crucible.py`)

### Healthy
- V22.1 — fix-implementer score stable (0.9628); D-mid.4 excluded from fix_rows
- V22.2 — HEAL_EXHAUSTED badge renders correctly in dashboard

---

## [BL 2.0 — Wave 21] — 2026-03-17

Dashboard BL 2.0 status colors and fix-implementer scoping.

### Fixed
- `F21.1` — QuestionQueue STATUS_COLORS updated with HEAL_EXHAUSTED and 7 BL 2.0 statuses (`dashboard/frontend`)
- `F21.2` — `_score_fix_implementer` fix_rows scoped via `_is_fix_row()` F-prefix guard (`bl/crucible.py`)

### Found (open)
- `D21.1` [DIAGNOSIS_COMPLETE] — fix_spec_completeness=0.29 root cause: 12 pre-template findings + 4 false positives

---

## [BL 2.0 — Wave 20] — 2026-03-17

Scorer verification and dashboard audit.

### Found (open)
- `A20.1` [NON_COMPLIANT] — QuestionQueue missing HEAL_EXHAUSTED status (fixed in Wave 21)
- `A20.2` [NON_COMPLIANT] — fix-implementer fix_rows has no F-prefix guard (fixed in Wave 21)

### Healthy
- V20.1, V20.2 — `_is_bl2_diag_row()` edge cases correct; DIAGNOSIS_COMPLETE frontmatter coverage verified
- D20.1 — dc_rate=1.00 post-F19.1 benchmark verified

---

## [BL 2.0 — Wave 19] — 2026-03-17

Crucible scorer scoping: dc_rate BL 1.x contamination and fix_spec false positive elimination.

### Fixed
- `F19.1` — `_score_diagnose_analyst` dc_rate scoped to BL 2.0 D-prefix rows via `_is_bl2_diag_row()` (`bl/crucible.py`)
- `F19.2` — fix_spec_completeness guard changed to exact `**Verdict**: DIAGNOSIS_COMPLETE` match (`bl/crucible.py`)

---

## [BL 2.0 — Wave 18] — 2026-03-17

Scorer verification: parse_questions hoist confirmed, HEAL_EXHAUSTED writeback verified.

### Found (open)
- `V18.1` [NON_COMPLIANT] — dc_rate denominator includes BL 1.x FAILURE rows (fixed in Wave 19)
- `V18.2` [NON_COMPLIANT] — fix_spec substring match admits false positives (fixed in Wave 19)

### Healthy
- A18.1 — parse_questions() hoist confirmed at lines 396–398
- D18.1 — HEAL_EXHAUSTED writeback path complete
- D18.2 — fix_rows scoped correctly for current campaign

---

## [BL 2.0 — Wave 17] — 2026-03-16

BL 2.0 crucible scorers implemented; mid-wave fixes verified; performance hoist applied.

### Fixed
- `F17.1` — 4 BL 2.0 scorer functions added to `crucible.py` and registered in `_SCORERS` (`bl/crucible.py`)

### Found (open)
- `A17.1` [NON_COMPLIANT] — parse_questions() called inside per-finding loop; O(N) parses (fixed same session)

### Healthy
- V17.1 — all 5 Wave-mid fixes verified; no BL 1.x regressions

---

## [BL 2.0 — Wave 16 (mid)] — 2026-03-16

Mid-wave fix cycle: 5 critical fixes for heal loop, peer-reviewer, text parsing, summary extraction.

### Fixed
- `F-mid.1` — healloop.py exhausted path now calls `update_results_tsv(original_qid, HEAL_EXHAUSTED)`; HEAL_EXHAUSTED added to frozensets in 4 files
- `F-mid.2` — peer-reviewer spawn guarded by `mode != code_audit`
- `F-mid.3` — `_parse_text_output()` else clause for BL 2.0 agents; regex extraction for `^verdict:` and `^summary:`
- `D-mid.4` — `_summary_from_agent_output()` early-return for `output.get("summary")`
- `F-mid.5` — pending-list refresh documented as intentional design

---

## [BL 2.0 — Wave 16] — 2026-03-16

Deep heal loop and campaign loop audit: 5 diagnoses, crucible scorer design validation.

### Found (open)
- `D16.1` [DIAGNOSIS_COMPLETE] — healloop exhausted path never calls update_results_tsv (fixed Wave 16-mid)
- `D16.2` [DIAGNOSIS_COMPLETE] — peer-reviewer spawned unconditionally for code_audit (fixed Wave 16-mid)
- `D16.3` [DIAGNOSIS_COMPLETE] — `_parse_text_output()` no else clause for BL 2.0 (fixed Wave 16-mid)
- `A16.1` [NON_COMPLIANT] — enumerate iterator bound to original pending list (documented as intentional)

### Healthy
- V16.1 — `_SCORERS` dict and `AgentScore` fields validated for BL 2.0 scorer additions

---

## [BL 2.0 — Wave 15] — 2026-03-16

crucible.py and questions.py BL 2.0 compat fixes. 5 questions, 2 critical fixes.

### Fixed
- `F15.1` — `questions.py` sync_status sentinel changed from `"\n## Q"` to `"\n## "` (`bl/questions.py`)
- `F15.2` — `crucible.py`: _KNOWN_AGENTS +4 BL 2.0 agents; domains_covered uses prefix detection; synthesizer regex and qa glob fixed

### Found (open)
- `A15.1` [NON_COMPLIANT] — _KNOWN_AGENTS missing BL 2.0 agents (fixed by F15.2)
- `D15.2` [DIAGNOSIS_COMPLETE] — question_designer domains_covered D1–D6 hardwired
- `D15.3` [DIAGNOSIS_COMPLETE] — synthesizer regex and qa glob score 0 on BL 2.0

### Healthy
- D15.4 — agent_db.py verdict handling covers all 30 BL 2.0 verdicts

---

## [BL 2.0 — Wave 14] — 2026-03-16

goal.py + synthesizer.py BL 2.0 compat fixes. 5 questions, 2 critical fixes.

### Fixed
- `F14.1` — goal.py wave-index scans BL 2.0 headers; focus default and prompt examples use BL 2.0 operational modes
- `F14.2` — synthesizer.py writes to `findings/synthesis.md`; DIAGNOSIS_COMPLETE and FIX_FAILED added to _HIGH_SEVERITY

### Healthy
- V14.1 — skill_forge.py and quality.py have no BL version-specific logic

---

## [BL 2.0 — Wave 13] — 2026-03-16

followup.py sub-question quality fixes. 4 questions, 2 fixes.

### Fixed
- `F13.1` — `_build_followup_prompt()` uses `or` fallback for agent_name; `**Operational Mode**` field added to sub-question template
- `F13.2` — `_parse_followup_blocks()` bracket tag injection uses `_OP_MODE_TO_TAG` from Operational Mode field

---

## [BL 2.0 — Wave 12] — 2026-03-16

Regression detection, failure classification, follow-up coverage. 5 questions, 3 fixes.

### Fixed
- `F12.1` — 8 BL 2.0 regression pairs added to `_REGRESSIONS` (`bl/history.py`)
- `F12.2` — `classify_failure_type_local()` handles NON_COMPLIANT/REGRESSION; _SYSTEM_PROMPT updated (`bl/findings.py`)
- `F12.3` — NON_COMPLIANT added to C-04 follow-up guards (`bl/campaign.py`, `bl/followup.py`)

---

## [BL 2.0 — Wave 11] — 2026-03-16

crucible.py scorer patterns, sync_status preservation, findings corpus bias. 4 questions, 3 fixes.

### Fixed
- `F11.1` — crucible.py scorers use wave-number extraction from IDs and `\w+`-prefixed block regex
- `F11.2` — `sync_status_from_results()` preserve set extended with FAILURE/NON_COMPLIANT/WARNING/REGRESSION/ALERT
- `F11.3` — `_build_findings_corpus()` sorts by severity (FAILURE first), drops low-severity first under budget

---

## [BL 2.0 — Wave 10] — 2026-03-16

Hypothesis generation BL 2.0 compat. 4 questions, 2 fixes.

### Fixed
- `F10.1` — `_parse_question_blocks()` regex accepts BL 2.0 ID prefixes (`bl/hypothesis.py`)
- `F10.2` — `parse_recommendation()` scans only after "Recommended Next Action" header (`bl/hypothesis.py`)

### Found (open)
- `A10.1` [NON_COMPLIANT] — `pop(0)` on alphabetical sort drops A*/D* findings before V* under budget pressure

---

## [BL 2.0 — Wave 9] — 2026-03-16

Wave detection and agent tracking BL 2.0 compat. 4 questions, 2 fixes.

### Fixed
- `F9.1` — `_QUESTION_BLOCK_HEADER` regex changed to `[\w][\w.-]*`; wave detection returns correct wave number
- `F9.2` — agent_db condition expanded to `mode in ("agent","code_audit")`

### Healthy
- A9.1 — "DONE" in _SUCCESS_VERDICTS is dead code but harmless

---

## [BL 2.0 — Wave 8] — 2026-03-16

Override injection and status preservation. 4 questions, 2 fixes.

### Fixed
- `F8.1` — `glob("Q*.md")` changed to `glob("*.md")` for override peer review scanning
- `F8.2` — FAILURE/NON_COMPLIANT/WARNING/REGRESSION/ALERT added to `_PRESERVE_AS_IS`

### Healthy
- A8.1 — all 10 BL 2.0 operational mode files present; `_load_mode_context()` silent fallback acceptable

---

## [BL 2.0 — Wave 7] — 2026-03-16

Verdict extraction else-branch and C-04 adaptive drill-down. 4 questions, 2 fixes.

### Fixed
- `F7.1` — `self_verdict_early` checked first in else-branch; BL 2.0 agent verdicts now surfaced
- `F7.2` — `_is_leaf_id()` else-branch uses dot-count for BL 2.0 IDs

### Healthy
- A7.1 — followup sub-question IDs, block headers, mode fields all BL 2.0 compatible

---

## [BL 2.0 — Wave 6] — 2026-03-16

Runner dispatch and results.tsv format. 4 questions, 2 fixes.

### Fixed
- `F6.1` — `register("code_audit", run_agent)` added to `_register_builtins()`
- `F6.2` — results.tsv rewritten in BL 2.0 format (qid first)

---

## [BL 2.0 — Wave 5] — 2026-03-16

Question Mode dispatch and bracket tag classification. 3 questions, 1 fix.

### Fixed
- `F5.1` — `parse_questions()` uses `fields.get("mode", mode_raw)` for body Mode field dispatch

### Healthy
- A5.1 — all BL 2.0 bracket tags correctly classified; no C-30 cap misfire
- V5.1 — all 7 BL 2.0 pipeline stages verified correct after Waves 1–5

---

## [BL 2.0 — Wave 4] — 2026-03-16

Critical parse_questions regex fix + 5 secondary fixes.

### Fixed
- `bl/questions.py` — parse_questions() regex was failing to parse multi-word operational modes (D3.1)
- Multiple secondary fixes applied in Wave 4 (see `projects/bl2/findings/` for D3.x, D4.x findings)

---

## [BL 2.0 — Wave 3] — 2026-03-16

`_STORE_VERDICTS` extraction, print fix, end-to-end validation.

### Fixed
- `bl/recall_bridge.py` — extracted `_STORE_VERDICTS` from inside `store_finding()` to module level
- Minor print/stderr output fix

### Changed
- End-to-end heal loop validated — all 6 Wave 2 fixes confirmed working together

---

## [BL 2.0 — Wave 2] — 2026-03-16

6 critical bugs fixed by the BL 2.0 engine fixing itself.

### Fixed
- `bl/runners/agent.py` — `_verdict_from_agent_output()` now accepts all 30 BL 2.0 verdicts via `_ALL_VERDICTS` frozenset. Was only accepting 4 legacy verdicts (F2.1)
- `bl/findings.py` — DEGRADED, ALERT, UNKNOWN, BLOCKED added to `_NON_FAILURE_VERDICTS` (F2.2)
- `bl/healloop.py` — `current_result = dict(fix_result)` — alias assignment bug fixed; heap mutation eliminated (F2.3)
- `bl/campaign.py` — heal loop result propagation changed to identity check `healed_result is not result` (F2.4)
- `bl/healloop.py` — `_synthetic_question()` now uses `short_type = "diag" if "diagnose" in agent_name else "fix"` (F2.5)
- `bl/healloop.py` — `last_cycle` tracker added; EXHAUSTED note reports actual exit cycle (F2.6)

---

## [BL 2.0 — Wave 1] — 2026-03-16

Self-audit campaign Wave 1: 22 questions run against the BL engine itself. 7 FAILUREs, 1 WARNING, 1 NON_COMPLIANT found.

### Fixed *(in subsequent waves)*
- See Wave 2 entries above

### Added *(audit findings)*
- Confirmed compliant: A1 (PARKED_STATUSES), A3 (heal loop termination), A4 (Recall graceful-fail), A5 (session-context append-only), A6 (operational_mode default), A7 (agent existence checks), A8 (mode_context injection order), A9 (session_ctx prompt order), A10 (heal ID collision safety), A11 (intermediates in results.tsv), A12 (BL 1.x independence)
- Non-compliant: A2 — `_NON_FAILURE_VERDICTS` missing 4 verdicts (fixed in Wave 2)

---

## [BL 2.0 — Phase 2 Complete] — 2026-03-17

Masonry Phase 2: full dev workflow parity with OMC replaced. BL 2.0 runner upgrades.

### Added
- `bl/tracer.py` — introspection decorator and full trace recording
- Masonry hooks: masonry-lint-check.js, masonry-design-token-enforcer.js, masonry-approver.js, masonry-context-safety.js, masonry-stop-guard.js, masonry-build-guard.js, masonry-ui-compose-guard.js, masonry-context-monitor.js, masonry-tool-failure.js, masonry-subagent-tracker.js
- Masonry skills: `/plan`, `/build`, `/verify`, `/fix`, `/ui-init`, `/ui-compose`, `/ui-review`, `/ui-fix`, `/masonry-code-review`, `/masonry-security-review`
- Dashboard Agent Fleet tab: `GET /api/agents` + `AgentFleet.tsx`

### Changed
- OMC fully removed from Tim's Claude Code environment — Masonry is the sole orchestration layer
- All Masonry hooks registered in `~/.claude/settings.json`
- `~/.claude/CLAUDE.md` updated with full Masonry agent routing, skills catalog, and hook reference

---

## [BL 2.0 — Initial Build] — 2026-03-16

Full BL 2.0 engine implementation on top of BL 1.x foundation.

### Added
- `bl/healloop.py` — self-healing state machine. FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED/FIX_FAILED loop
- `bl/recall_bridge.py` — optional Recall memory bridge. Graceful-fail: `_HTTPX_AVAILABLE` flag, 2s health timeout, 5s op timeout
- `bl/questions.py` — BL 2.0 fields: `operational_mode`, `resume_after`, `_PARKED_STATUSES` (12 terminal verdicts), `_reactivate_pending_external()`
- `bl/findings.py` — `_NON_FAILURE_VERDICTS` frozenset (18 verdicts), `severity_map` (32 entries), `_VERDICT_CLARITY` (35 entries)
- `bl/campaign.py` — BL 2.0 additions: `_load_mode_context()`, session-context accumulator, Recall bridge integration, heal loop wiring
- `bl/runners/agent.py` — `session_ctx_block` injected between `mode_ctx_block` and `doctrine_prefix`
- `template/modes/` — 10 mode program files: diagnose, fix, research, audit, validate, benchmark, evolve, monitor, predict, frontier
- BL 2.0 specialist agents: diagnose-analyst, fix-implementer, research-analyst, compliance-auditor, design-reviewer, evolve-optimizer, health-monitor, cascade-analyst, question-designer-bl2, hypothesis-generator-bl2
- `projects/bl2/` — BL 2.0 self-audit campaign targeting the BL engine itself

---

## [BL 1.x — Masonry Phase 1] — 2026-03-17

Masonry package scaffold and Phase 1 core hooks.

### Added
- `masonry/src/core/config.js` — config loader (~/.masonry/config.json with defaults)
- `masonry/src/core/state.js` — per-project masonry-state.json read/write
- `masonry/src/core/recall.js` — Recall HTTP client
- Core hooks: masonry-register.js, masonry-observe.js, masonry-guard.js, masonry-stop.js, masonry-handoff.js, masonry-statusline.js
- `masonry/bin/masonry-setup.js` — interactive setup wizard

---

## [BL 1.x — Agent Fleet & Dashboard] — 2026-03-17

### Added
- `forge-check.md`, `agent-auditor.md`, `peer-reviewer.md` — quality gate agents
- `mortar.md` — campaign conductor (BL 1.x version)
- `planner.md`, `code-reviewer.md` — planning and review agents
- Dashboard Agent Fleet tab with tier-filtered card view
- `projects/agent-meta/` — meta-campaign stress-testing the agent fleet; 28/28 HEALTHY, 96.1/100 avg score at baseline

---

## [BL 1.x — Eval Harness & Model Routing] — 2026-03-17

### Added
- Eval/scoring harness: `score_result()` wired into `update_results_tsv()` — `eval_score` column on every result
- Agent model routing: `model:` frontmatter on all template agents; `_read_frontmatter_model()` + `_MODEL_MAP` in `runners/agent.py`
- `frontier-analyst` agent: FRONTIER_VIABLE/PARTIAL/BLOCKED verdicts, exploration epistomology
- Mortar Phase 2 hardening: WM1 startup validation, finding validation stub, global sentinel, overseer escalation on FLEET_UNDERPERFORMING
- `template/docs/question-schema.md` — canonical BL 2.0 question schema reference
- QUICKSTART.md + CLAUDE.md updated with planner → qd-bl2 two-step workflow

---

## [BL 1.x — Baseline] — pre-2026-03-16

BL 1.x engine. Sequential campaign loop, single-mode (diagnose), optional fix loop via `BRICKLAYER_FIX_LOOP=1`.

### Added
- Core: `campaign.py`, `questions.py`, `findings.py`, `runners/`, `history.py`, `synthesizer.py`, `hypothesis.py`, `followup.py`
- Agent fleet: forge, forge-check, peer-reviewer, agent-auditor, fix-agent, retrospective, question-designer, hypothesis-generator, quantitative-analyst, regulatory-researcher, competitive-analyst, benchmark-engineer
- Dashboard: React + FastAPI monitoring UI (port 3100 / 8100)
- Failure taxonomy: `classify_failure_type()` — `syntax|logic|hallucination|tool_failure|timeout|unknown`
- Confidence signaling: `classify_confidence()` + `CONFIDENCE_ROUTING` — `high|medium|low|uncertain` → `accept|validate|escalate|re-run`
- Runner registry: `Runner(Protocol)` plugin interface; http, subprocess, static runners
- Goal-directed campaigns via `goal.md`
- Adaptive follow-up: FAILURE/WARNING auto-generates drill-down sub-questions (Q2.4 → Q2.4.1)
- Verdict history + regression detection
- Fix loop: FAILURE → fix agent → re-run → HEALTHY
- Pre-commit hook: `scripts/pre-commit.py` — lint-guard + commit-reviewer + noqa escape
- FastMCP gateway: `mcp_gateway.py` proxying recall/github/context7/firecrawl/exa on port 8350

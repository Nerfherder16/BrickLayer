# Changelog

## [Unreleased]

## [Wave 38] -- 2026-03-24

5 questions answered (3 fix, 2 validate). Two of three interacting cascades (P2 corpus, P3 rubric) fully remediated. F12.1 drift scoring inversion confirmed NOT implemented -- single remaining blocker before MIPROv2 optimization is safe.

### Fixed
- `F-mid.1` -- Karen rubric contamination cleared: stripped research-analyst rubric from `~/.claude/agents/karen.md`; added signature-conditional rubric selection (`_RUBRIC_RESEARCH`, `_RUBRIC_KAREN`, `_FOCUS_RESEARCH`, `_FOCUS_KAREN`) to `_build_prompt()` in `optimize_with_claude.py`; threaded `signature` parameter through `run()`, `_main()`, `run_optimize()` (`masonry/scripts/optimize_with_claude.py`, `masonry/scripts/improve_agent.py`)
- `F-mid.2` -- Mock campaign corpus cleaned: removed 135 `source: "mock_campaign"` records from `scored_all.jsonl` (9x larger than estimated 15); added `_EXCLUDED_SOURCES` set and source-filter guard to `_load_records()` (`masonry/scripts/optimize_with_claude.py`, `masonry/training_data/scored_all.jsonl`)
- `F-mid.3` -- MIN_VERDICTS_FOR_AUTO_OPTIMIZE=10 guard added to `_tool_masonry_drift_check()` auto_trigger loop; benchmark-engineer (2 verdicts) now excluded from premature auto-trigger (`masonry/mcp_server/server.py`)

### Found (open)
- `V-mid.1` [FAIL] -- F12.1 confidence-based drift metric NOT implemented; `_score_verdicts()` has no confidence parameter; research-analyst at 45.2% CRITICAL drift; CASCADE_ACTIVE
- `V-mid.2` [WARNING] -- P5 primary trigger closed (F3.1 verified); two residual risks: build-guard cross-session exits 0 with stderr-only message; stop-guard auto-commits without test-pass or IN_PROGRESS task gate

### Healthy
- F3.1 confirmed end-to-end: `hooks/hooks.json` empty, SessionStart registered once, double-fire cascade path permanently closed
- P2 corpus clean: 471+ legitimate training records remain after mock_campaign purge
- P3 rubric injection: signature-conditional selection confirmed working for both research-analyst and karen paths

## [Wave 37] -- 2026-03-24

7 predict-mode questions answered. Three independently active failure cascades identified in the optimization feedback loop (P6 drift inversion + P3 karen rubric + P2 mock corpus). Campaign recommendation changed to STOP with conditions.

### Found (open)
- `P6` [CONFIRMED, Critical] -- Drift scoring treats FAILURE=0.0; 4 agents at CRITICAL drift (45-100%); auto_trigger=true would optimize best performers
- `P3` [CONFIRMED, High] -- Karen optimization ran with research-analyst rubric; contaminated instructions live on all machines
- `P1` [CONFIRMED, High] -- Ollama offline cascade; 15s blocking per non-deterministic route; SEMANTIC_ROUTING_ENABLED constant missing
- `P2` [WARNING, High] -- Mock campaign corpus (15 records estimated) degrading held-out eval
- `P5` [CONFIRMED, High] -- Interrupted-build cascade imminent; double-fire output collision
- `P4` [WARNING, Medium] -- Pre-agent tracker one-slot collision at 16.7% rate
- `P7` [WARNING, Low] -- AgentRegistryEntry.optimized_prompt is a dead schema field

### Healthy
- All 7 predict-mode hypotheses confirmed as real mechanisms (zero false alarms)
- Routing pipeline (L1-L4) operational; hook double-fire fix (F3.1) in place; training data pipeline functional

## [Wave 24] -- 2026-03-22

7 questions answered. Training data attribution gap closed (+603 recoverable records), CLI optimization flags shipped, Phase 17 metric ceiling revised to 70-73% (verdict accuracy is binding constraint), karen confirmed incompatible with ResearchAgentSig (KarenSig required).

### Fixed
- `F24.1` -- `--num-trials` and `--valset-size` CLI flags added to `run_optimization.py`, wired through `run()` into `optimize_agent()` into `optimizer.compile()` (`masonry/scripts/run_optimization.py`, `masonry/src/dspy_pipeline/optimizer.py`)
- `D24.1` -- `_AGENT_RE` regex added to `extract_finding()` in `training_extractor.py`; `**Agent**:` field is now primary attribution source; 137/162 masonry findings attributed, 603 cross-project records recoverable (`masonry/src/dspy_pipeline/training_extractor.py`)
- `D24.3` -- `expanduser()` added to `detect_stale_registry_entries()` line 106; 14 false-positive stale entries on Windows eliminated (`masonry/scripts/onboard_agent.py`)

### Changed
- `M24.1` -- `monitor-targets.md` updated with `dspy_optimization_wall_time_minutes` (WARNING=120min, FAILURE=480min) and `dspy_bootstrap_failure_rate` thresholds
- ROADMAP Phase 17 metric target revised from 75-80% to 70-73% based on R24.1 evidence

### Found (open)
- `D24.2` [DIAGNOSIS_COMPLETE] -- `score_routing.py` line 112 awards 70pts by checking if dispatched agent is recognized (trivially true), not comparing against ground-truth target_agent; all 17 routing records provide zero training signal
- `R24.1` [WARNING] -- Phase 17 metric changes yield +1-4pts not +5-8pts; verdict accuracy (~35-40%) is the binding constraint; severity validation and verdict-conditioned confidence are counterproductive
- `V24.1` [NOT_VALIDATED] -- karen's 191 training records use ops-domain schema (commit_subject/doc_files_written), structurally incompatible with ResearchAgentSig; KarenSig + metric + loader required before optimization

### Healthy
- F24.1: CLI flags verified end-to-end; existing callers (Kiln OPTIMIZE button) unaffected by defaults
- D24.1: Agent field extraction confirmed working; masonry attribution 134 to 137 findings
- D24.3: expanduser() fix zero-regression; 14 false positives eliminated

## [Wave 22] -- 2026-03-21

4/5 questions answered (R22.2 deferred by user). DSPy + Ollama pipeline end-to-end FUNCTIONAL: smoke test passed with qwen3:14b producing valid structured output. Confidence calibration cliff diagnosed with fix spec complete.

### Fixed
- `F22.1` -- Ollama backend wired into `configure_dspy()`, `optimize_agent()`, `optimize_all()` with `backend="ollama"` parameter; `--backend` CLI flag added to `run_optimization.py`; MCP server handler updated (`masonry/src/dspy_pipeline/optimizer.py`, `masonry/scripts/run_optimization.py`, `masonry/mcp_server/server.py`)

### Found (open)
- `R22.1` [WARNING] -- `configure_dspy(backend="ollama")` defaults to model="claude-sonnet-4-6" (Anthropic model name); Ollama rejects with 404; caller must pass `model="qwen3:14b"` explicitly; 1-line fix needed in optimizer.py:38
- `D22.1` [DIAGNOSIS_COMPLETE] -- confidence_calibration band [0.5, 0.95] in `score_findings.py:178` creates 30-point cliff for confidence > 0.95; 40 training records suppressed (14.4%); fix spec: widen to [0.5, 1.0]
- `R22.2` [PENDING] -- Full MIPROv2 trial deferred; blocked on configure_dspy default model fix

### Healthy
- R22.1: DSPy + Ollama smoke test PASSED -- qwen3:14b produces valid structured output via ChainOfThought(ResearchAgentSig); all 5 output fields populated
- F22.1: All three optimizer entry points (Python API, CLI, MCP tool) verified with backend="ollama" parameter

## [Wave 21] -- 2026-03-21

4 questions answered. VIGIL HEALTHY milestone: fleet reaches 0 thorns for the first time. Stale masonry/masonry/ path artifact fixed. DSPy Ollama integration spec complete (2 config changes).

### Fixed
- `D21.1`/`F21.1` -- Stale `masonry/masonry/training_data/` CWD artifact: deleted stale directory, applied dual-path detection to `score_all_agents.py:215` and `run_optimization.py:105` matching existing `run_vigil.py` pattern (`masonry/scripts/score_all_agents.py`, `masonry/scripts/run_optimization.py`)
- `R21.2` -- Vigil unknown thorn: excluded `synthesis*.md` meta-files from `parse_findings_dir()` in `run_vigil.py`; fleet transitions WARNING to HEALTHY (`masonry/scripts/run_vigil.py`)

### Found (open)
- `R21.1` [WARNING] -- DSPy MIPROv2 + Ollama qwen3:14b structurally feasible (2 config changes), but qwen3:14b structured output reliability under bootstrapping is unverified; smoke-run needed before full optimization trial

### Healthy
- R21.2: Fleet HEALTHY -- 7 roses, 10 buds, 0 thorns (first clean fleet assessment)
- R21.1: DSPy Ollama integration path confirmed -- `dspy.LM("ollama_chat/qwen3:14b")` + `build_dataset()` training path fully compatible

## [Wave 20] -- 2026-03-21

4 questions answered. Routing session_id collision fixed (100pt records 3 to 9), masonry findings scoring unlocked (training corpus 61 to 271), overall corpus 435 records (+71%). Campaign STOP recommended.

### Fixed
- `D20.1`/`F20.1` -- score_routing flat dict collision: compound (session_id, agent) key replaces flat session_id dict; agent alias normalization map added; `general-purpose` added to AGENT_CATEGORIES (`masonry/scripts/score_routing.py`, `masonry/src/scoring/rubrics.py`)
- `F20.2` -- score_findings masonry exclusion: removed `"masonry"` from discovery blocklist, fixed `_extract_section` regex to not stop at `###` subsections, added `FIX_APPLIED`/`COMPLETE` to VALID_VERDICTS (`masonry/scripts/score_findings.py`)

### Healthy
- R20.1: Training corpus health confirmed -- 435 merged records, 9 routing 100pt records, 6 agents with 10+ records, vigil WARNING (7 roses, 10 buds, 1 thorn)

## [Wave 19] -- 2026-03-21

4 questions answered. Vigil calibration fixed (false Thorns eliminated), routing reliability mapped at 60%, score_findings masonry extension specified.

### Fixed
- `D19.1`/`F19.1` -- Vigil false Thorn classifications: overlaid scored_all rubric percentages onto confidence-based pass_rate; gated OVERCONFIDENT check on `rubric_based` flag (`masonry/scripts/run_vigil.py`)
- `F19.1` -- score_all_agents `agents_covered` for score_routing populated from `dispatched_agent` field instead of hardcoded empty list (`masonry/scripts/score_all_agents.py`)

### Found (open)
- `R19.1` [WARNING] -- score_routing session_id collision causes last-write-wins matching; fix-implementer/general-purpose missing from AGENT_CATEGORIES; 60% 100pt record rate
- `R19.2` [WARNING] -- score_findings.py needs 3 changes to score masonry findings (discovery blocklist, regex subsection fix, FIX_APPLIED in VALID_VERDICTS); domain contamination risk without source-tagging

### Healthy
- Vigil fleet verdict now WARNING (1 genuine Thorn: `unknown`) instead of false CRITICAL (5 Thorns). 7 Roses, 6 Buds confirmed.

## [Wave 18] -- 2026-03-21

4 questions answered. Session ID pairing confirmed, vigil fully operational, DSPy blockers identified.

### Fixed
- `D18.1` -- 84% of findings lacked `**Agent**:` field; backfill script patched 103 files
- `F18.1` -- `load_scored_all` dual-path detection fixed; vigil now augments with 248 scored records

### Found (open)
- `R18.2` [WARNING] -- DSPy trial blocked: no ANTHROPIC_API_KEY, all 36 QA records at score floor (60/100)

### Healthy
- R18.1: Agent tool dispatch produces matching session ID pairs; first 100pt routing record generated

### Added — Phase 3: Scoring, validation, and fleet tooling

**Scoring pipeline** (`src/scoring/`, `scripts/`)
- `src/scoring/rubrics.py` — Canonical rubric definitions per agent category (findings, code, ops, routing); hardcoded invariants, human-review required to change
- `scripts/score_findings.py` — Scores findings-category agents from campaign finding files against rubric dimensions
- `scripts/score_code_agents.py` — Scores code-category agents (developer, test-writer, fix-implementer, refactorer)
- `scripts/score_ops_agents.py` — Scores ops-category agents (git-nerd, karen, forge-check, overseer)
- `scripts/score_routing.py` — Scores routing decisions against expected targets
- `scripts/score_all_agents.py` — Unified scorer: aggregates all signal types, writes scored_all.jsonl, updates last_score in agent_registry.yml

**Agent validation**
- `scripts/validate_agents.py` — Validates agent .md files against canonical frontmatter schema; checks required fields, value validity, naming consistency; reports without modifying

**Registry maintenance**
- `scripts/backfill_agent_fields.py` — Backfills missing runtime state fields (dspy_status, drift_status, last_score) into existing registry entries
- `scripts/backfill_registry.py` — Backfills the full agent_registry.yml from agent .md frontmatter; idempotent batch refresh

**Vigil monitor**
- `scripts/run_vigil.py` — Vigil: continuous health monitor that polls agent_db, runs drift checks, writes alerts

**CLI tools**
- `bin/masonry-fleet-cli.js` — Fleet management CLI: status, add, retire, regen subcommands over registry.json + agent_db.json
- `bin/masonry-init-wizard.js` — Interactive `/masonry-init` wizard: project scaffold, questions.md template, simulate.py stub

### Added — Phase 2: Python routing engine + MCP server + DSPy pipeline

**Four-layer routing engine** (`src/routing/`)
- `src/routing/router.py` — Orchestrating router: chains all four layers, always returns a RoutingDecision; logs resolved layer to stderr
- `src/routing/deterministic.py` — Layer 1: zero-LLM routing via slash commands, .autopilot/mode, masonry-state.json, .ui/mode, and question **Mode**: field extraction; confidence=1.0 on any match
- `src/routing/semantic.py` — Layer 2: Ollama embedding similarity (qwen3-embedding:0.6b) with module-level session cache; batch embeds all agents in a single Ollama call; threshold=0.70; falls through on Ollama unavailability
- `src/routing/llm_router.py` — Layer 3: Claude haiku subprocess call with JSON-constrained output; 8s timeout; Windows shell=True workaround; confidence=0.6; falls through on any failure

**Typed payload schemas** (`src/schemas/`)
- `src/schemas/payloads.py` — Pydantic v2 models with extra="forbid": QuestionPayload (12 modes), FindingPayload (severity + verdict + confidence), RoutingDecision, DiagnosePayload, DiagnosisPayload, AgentRegistryEntry (draft/candidate/trusted/retired tier system); 30 valid verdict strings
- `src/schemas/registry_loader.py` — YAML registry loader: parses agent_registry.yml into validated AgentRegistryEntry list; helpers get_agents_for_mode, get_agent_by_name; graceful on parse errors

**DSPy optimization pipeline** (`src/dspy_pipeline/`)
- `src/dspy_pipeline/signatures.py` — DSPy Signature classes: ResearchAgentSig, DiagnoseAgentSig, SynthesizerSig, QuestionDesignerSig
- `src/dspy_pipeline/optimizer.py` — MIPROv2 optimization: heuristic metric (verdict_match 0.4 + evidence_quality 0.4 + confidence_calibration 0.2); requires >= 5 examples; saves optimized module JSON to optimized_prompts/; falls back to unoptimized on failure
- `src/dspy_pipeline/training_extractor.py` — Extracts DSPy training examples from BL2 finding .md files; quality-weighted by agent score (gold >= 0.8, silver >= 0.5, excluded < 0.5); supports wave subdirectories
- `src/dspy_pipeline/drift_detector.py` — Drift detection: scores recent verdicts against baseline, produces DriftReport with alert_level (ok/warning/critical) and recommendation; run_drift_check scans all registry agents with verdict history

**MCP server** (`mcp_server/`)
- `mcp_server/server.py` — Full MCP server with dual transport: MCP SDK (stdio, primary) and raw JSON-RPC 2.0 (fallback, zero deps); 14 tools exposed: masonry_status, masonry_questions, masonry_nl_generate, masonry_weights, masonry_git_hypothesis, masonry_run_question, masonry_fleet, masonry_recall_search, masonry_route, masonry_optimization_status, masonry_onboard, masonry_drift_check, masonry_registry_list; importable as `python -m masonry.mcp_server.server`

**Auto-onboarding pipeline** (`scripts/`)
- `scripts/onboard_agent.py` — Full onboarding pipeline: detect_new_agents, extract_agent_metadata (frontmatter-only, no body inference), generate_registry_entry, upsert_registry_entry (idempotent), generate_dspy_signature_stub; runtime state fields written for new entries only; CLI supports single-file and batch modes

**Agent registry** (`agent_registry.yml`)
- 46 agents registered across two sources: project-local agents/ and ~/.claude/agents/; tier assignments: trusted (quantitative-analyst, test-writer, mortar, spec-writer, developer), candidate (peer-reviewer, agent-auditor, forge-check, retrospective, karen, security, architect, prompt-engineer, refactorer), draft (all others); diagnose-analyst registered with DiagnosePayload/DiagnosisPayload schemas

**Core modules** (extended)
- `src/core/registry.js` — Agent registry generator: scans .claude/agents/*.md, parses YAML frontmatter (including block scalars), writes registry.json; no external deps
- `src/core/skill-surface.js` — Recall skill retriever: queries Recall for masonry:skill tagged memories, deduplicates project-scoped vs. global results, returns markdown-formatted skill list

**Hooks** (extended)
- `src/hooks/masonry-session-start.js` — SessionStart: restores autopilot/UI/campaign context, auto-resumes interrupted builds, detects BL pending questions and suggests run commands, snapshots dirty files for stop-guard diffing; silent inside BL subprocesses (program.md + questions.md detection)
- `src/hooks/masonry-approver.js` — PreToolUse: auto-approves Write/Edit/Bash when build or UI mode active; uses progress.json freshness guard (30 min) to avoid stale-mode false approvals; walks up to 15 directory levels to find .autopilot/ or .ui/
- `src/hooks/masonry-stop-guard.js` — Stop: blocks on uncommitted session files; uses session snapshot (session-start) for primary detection, mtime fallback; skips gitignored files; normalizes Git Bash paths on Windows; BL-silent
- `src/hooks/masonry-build-guard.js` — Stop: blocks stop when .autopilot/mode = build and pending tasks remain
- `src/hooks/masonry-context-safety.js` — PreToolUse on ExitPlanMode: blocks when autopilot build active OR context >= 80%
- `src/hooks/masonry-lint-check.js` — PostToolUse: ruff format (background) + ruff check (warn-only) on .py files; prettier + eslint (both background) on .ts/.tsx/.js/.jsx; skips in build/fix mode; skips masonry/, hooks/, node_modules/, dist/; tsc removed (caused VS Code crashes)
- `src/hooks/masonry-design-token-enforcer.js` — PostToolUse: warns on hardcoded hex colors and banned fonts in UI files (.tsx/.css/.ts in projects with .ui/); silent during compose/fix mode; exit 0 always
- `src/hooks/masonry-tdd-enforcer.js` — PostToolUse: blocks (exit 2) in build mode when implementation file has no corresponding test; warns-only outside build mode; respects TDD exemption patterns (configs, types, migrations, __init__.py)
- `src/hooks/masonry-tool-failure.js` — PostToolUseFailure: per-project + per-tool error fingerprinting; 2-minute retry window; 3-strike escalation to diagnose-analyst; writes state to ~/.masonry/state/{project-slug}-{tool}.json
- `src/hooks/masonry-agent-onboard.js` — PostToolUse: triggers onboard_agent.py as detached subprocess when Write/Edit touches a direct child of any agents/ directory
- `src/hooks/masonry-subagent-tracker.js` — SubagentStart: writes agent activity to ~/.masonry/state/agents.json; 1-hour stale eviction; updates masonry-state.json active_agent in campaign mode
- `src/hooks/masonry-context-monitor.js` — PostToolUse async: estimates context window size from transcript file size; warns when approaching limits
- `src/hooks/masonry-session-end.js` — Session cleanup hook
- `src/hooks/masonry-session-summary.js` — Generates session summary
- `src/hooks/masonry-recall-check.js` — Checks Recall availability
- `src/hooks/masonry-pre-compact.js` — Pre-compact handler

**Skills** (extended)
- `skills/masonry-build.md` — /build: agent-mode TDD build workflow
- `skills/masonry-plan.md` — /plan: spec-writer invocation
- `skills/masonry-fix.md` — /fix: targeted fix workflow
- `skills/masonry-verify.md` — /verify: independent verification
- `skills/masonry-fleet.md` — /masonry-fleet: fleet health display
- `skills/masonry-code-review.md` — /masonry-code-review: comprehensive review
- `skills/masonry-security-review.md` — /masonry-security-review: OWASP audit
- `skills/masonry-pipeline.md` — /pipeline: DAG-based agent chaining
- `skills/masonry-team.md` — /masonry-team: parallel Claude instance coordination
- `skills/masonry-ultrawork.md` — /ultrawork: high-throughput parallel build
- `skills/masonry-nl.md` — /masonry-nl: natural language question generation

### Added
- Initial spec: MASONRY-SPEC.md
- Project scaffold: README, package.json, .gitignore
- Directory structure: bin/, src/core/, src/hooks/, skills/, packs/

## [0.1.0-phase1] — 2026-03-17

### Added — Phase 1: Core hooks + installer

**Core modules**
- `src/core/config.js` — Config loader (~/.masonry/config.json with defaults)
- `src/core/state.js` — Per-project masonry-state.json read/write
- `src/core/recall.js` — Recall HTTP client (storeMemory, searchMemory, isAvailable)

**Hooks**
- `src/hooks/masonry-register.js` — UserPromptSubmit: Recall context injection, resume detection, guard flush
- `src/hooks/masonry-observe.js` — PostToolUse async: finding detection → Recall, activity log
- `src/hooks/masonry-guard.js` — PostToolUse async: 3-strike error fingerprinting
- `src/hooks/masonry-stop.js` — Stop: session summary via Ollama → Recall, temp cleanup
- `src/hooks/masonry-handoff.js` — Detached handoff: packages loop state + findings → Recall at 70% context
- `src/hooks/masonry-statusline.js` — StatusLine: ANSI 24-bit campaign bar with progress, verdicts, context %

**Installer**
- `bin/masonry-setup.js` — Interactive setup wizard: writes ~/.masonry/config.json, merges hooks into ~/.claude/settings.json, smoke-checks Recall; supports --dry-run and --uninstall
- `bin/masonry-mcp.js` — MCP server stub (Phase 2)

**Skills**
- `skills/masonry-run.md` — /masonry-run: launch or resume campaign
- `skills/masonry-status.md` — /masonry-status: campaign health summary
- `skills/masonry-init.md` — /masonry-init: Phase 2 stub

**Config**
- `hooks.json` — Hook manifest (UserPromptSubmit, PostToolUse ×2, Stop, statusLine)

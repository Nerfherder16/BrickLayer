# Research Questions — BrickLayer 2.0

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Domain 1 — Architecture (Diagnose: how should bl/ be extended?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q1.1 | diagnose | DONE | What is the minimal change to `bl/campaign.py` to support mode dispatch — reading `mode:` from each question and loading the corresponding `modes/{mode}.md` as loop context? |
| Q1.2 | diagnose | DONE | How should `questions.md` represent the new `mode:` field (operational mode) without breaking the existing `mode:` field (which currently means runner type)? What rename is required? |
| Q1.3 | diagnose | DONE | What new verdict types need to be added to `bl/findings.py` and `bl/quality.py` — specifically DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, FIXED, PROMISING, WEAK, BLOCKED, COMPLIANT, NON_COMPLIANT, CALIBRATED? |
| Q1.4 | diagnose | DONE | How should DIAGNOSIS_COMPLETE suppression work in `bl/questions.py`? What is the mechanism to park a question and re-activate it when code changes? |
| Q1.5 | diagnose | DONE | How should PENDING_EXTERNAL + `resume_after:` work in the campaign loop? Does it require changes to `bl/campaign.py` or only to `bl/questions.py`? |

---

## Domain 2 — Mode Implementation (Validate: does each mode spec work?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q2.1 | validate | DONE | Does the Frontier mode program (`modes/frontier.md`) produce a complete, actionable loop? What questions would Wave 1 look like for the "Uncreated App" project? |
| Q2.2 | validate | WARNING | Does the Fix mode program (`modes/fix.md`) correctly prevent scope creep? Is the pre-flight checklist sufficient to catch an underspecified DIAGNOSIS_COMPLETE finding? |
| Q2.3 | validate | DONE | Does the Monitor mode program (`modes/monitor.md`) correctly distinguish itself from a scheduled Diagnose run? What is the exact operational difference? |
| Q2.4 | validate | WARNING | Does the Predict mode program (`modes/predict.md`) have a sound methodology? Can the IMMINENT/PROBABLE/POSSIBLE/UNLIKELY verdict set be objectively assigned, or is it inherently SUBJECTIVE? |
| Q2.5 | validate | WARNING | Does the cross-mode handoff table in `program.md` cover all meaningful transitions? Are there handoffs that are missing or incorrect? |

---

## Domain 3 — Per-Project Application (Research: applying to Tim's active projects)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q3.1 | research | DONE | For Recall: which of the 5 open deployment blockers should be addressed via Fix mode first? Run Predict mode logic on the current open findings to produce the priority order. |
| Q3.2 | research | DONE | For ADBP: what mode should ADBP start in? Read `adbp/project-brief.md` and `adbp/findings/synthesis.md` to determine current stage and most valuable next mode. |
| Q3.3 | frontier | DONE | For the Uncreated App: what is it? Run 3 Frontier questions to generate candidate concepts based on Tim's skills, infrastructure, and gaps in his current tool stack. |
| Q3.4 | research | INCONCLUSIVE | For Legal: what regulatory domain is this? What is the realistic research landscape for whatever legal project is being contemplated? |
| Q3.5 | audit | DONE | For UI/UX: given the `figma-designer-guide.md` and `frontend-design-philosophy.md` in Tim's global rules, define an audit checklist for any new frontend component. What are the top 10 compliance checks? |

---

## Domain 4 — Template Evolution (Evolve: what should the template/ become?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q4.1 | evolve | DONE | What changes are required to `template/` to support BrickLayer 2.0's mode system? Should `template/` become `template-diagnose/` with sibling templates for each domain (template-research/, template-frontier/, etc.)? |
| Q4.2 | evolve | DONE | What should the new project bootstrap sequence look like? Currently: copy template, edit project-brief, run question-designer. With modes: what's the right first question to ask? |
| Q4.3 | evolve | DONE | Should `simulate.py` be renamed `evaluate.py` in the new template, or kept as-is for backward compatibility? What does the new template's evaluate.py stub look like? |

---

## Wave 1 — Evolve (E1): Mode Specification Improvements

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E1.1 | evolve | DONE | Should `modes/monitor.md` add a `DEGRADED_TRENDING` verdict for metrics that are trending toward a threshold across multiple consecutive runs but haven't yet crossed it? What are the exact decision criteria and how does it feed into Predict mode? |
| E1.2 | evolve | DONE | Should `modes/validate.md` explicitly document FAILURE routing — new-system FAILURE → Research, deployed-system FAILURE → Diagnose — so agents reading validate.md alone don't miss the handoff? |
| E1.3 | evolve | DONE | Karen agent accuracy is 0.55 (target 0.85). All 20 eval examples show `predicted.action = "skipped"` regardless of input context. What is the root cause and what specific prompt change raises accuracy to ≥0.85? |

---

## Wave 2 — Evolve (E2): Karen Training Data Fix

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E2.1 | evolve | DONE | Karen eval score dropped from 0.55 (Wave 1 baseline) to 0.30 after the commit-type-first prompt fix. The prompt IS applied correctly. What is the root cause of the regression and what does it reveal about the training data? |
| E2.2 | evolve | DONE | In `masonry/scripts/score_ops_agents.py:_score_karen()`, the `input.files_modified` field captures the doc files karen WROTE, not the source files that TRIGGERED the update. Fix the pipeline to use the parent commit's source files as `files_modified`. Also fix `build_karen_metric._derive_expected()` to correctly label "chore: update CHANGELOG for <hash>" commits as expected="skipped". |
| E2.3 | evolve | DONE | After fixing the training data pipeline (E2.2), regenerate karen records from git history and re-run the eval. What is the new score? Does it reach the 0.85 target? |

---

## Wave 3 — Evolve (E3): Eval Pipeline Coverage + Optimizer Audit

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E3.1 | evolve | DONE | Merging `scored_all_wave13.jsonl` into `scored_all.jsonl` (with dedup) should make research-analyst, synthesizer-bl2, and 4 other agents eval-able for the first time. Execute the merge and verify record counts per agent. |
| E3.2 | evolve | DONE | After the wave13 merge, run eval on `quantitative-analyst` (80 records). What is the baseline score? If score <0.50, the metric signature or training labels are wrong. |
| E3.3 | evolve | DONE | After the wave13 merge, run eval on `research-analyst` (5 records, all HEALTHY). What is the baseline score? Are the 5 records sufficient for a meaningful eval or is the score artificially high? |
| E3.4 | evolve | DONE | Audit the `optimizer.py` write-back mechanism that overwrote `karen.md` in Wave 2. Does it have a guard to prevent overwriting non-optimizer content? Is the overwrite scope limited to the DSPy section only? |

---

## Wave 4 — Evolve (E4): Eval Instruction Fix + Optimizer Guard

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E4.1 | evolve | DONE | Adding `_RESEARCH_JSON_INSTRUCTION` with explicit field list to `eval_agent.py` should raise quantitative-analyst eval score from 0.10 to >0.50 by eliminating wrong-schema predictions (routing decisions, question payloads). |
| E4.2 | evolve | DONE | Adding `target_paths` optional parameter to `writeback_optimized_instructions()` and defaulting to [source_md_path] in `optimize_with_claude.py` should prevent cross-file contamination without breaking sync when explicitly requested. |

---

## Wave 5 — Evolve (E5): PROMISING Verdict + Regulatory Baseline

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E5.1 | evolve | DONE | Adding `PROMISING` to the allowed verdict set in `_RESEARCH_JSON_INSTRUCTION` should allow quantitative-analyst to match 26/61 training records (42%) that have PROMISING expected output — currently forced to mismatch. Does this push eval score from 0.70 to ≥0.85? |
| E5.2 | evolve | DONE | After E5.1 eval run, establish baseline for regulatory-researcher (12 records, avg=60). Does the eval infrastructure work for this agent, or does it exhibit the same eval-design-mismatch as research-analyst? |

---

## Wave 6 — Evolve (E6): Remaining Agent Baselines + Research-Analyst Strategy

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E6.1 | evolve | DONE | Establish synthesizer-bl2 eval baseline (6 records, standard research schema, HEALTHY/INCONCLUSIVE/WARNING verdicts). Does the eval infrastructure work correctly, similar to regulatory-researcher? |
| E6.2 | evolve | DONE | Establish competitive-analyst eval baseline (6 records, mostly INCONCLUSIVE). Does the model correctly output INCONCLUSIVE for these records? |
| E6.3 | evolve | DONE | Design a training data generation plan for research-analyst that produces 20+ diverse records with varied verdicts. What questions would generate WARNING/FAILURE/INCONCLUSIVE records? How should the eval be restructured for an agentic researcher? |

---

## Wave 7 — Evolve (E7): synthesizer-bl2 Fix + Research-Analyst Pilot Data

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E7.1 | evolve | DONE | synthesizer-bl2 Record 4 (Q6.7 / empty evidence) is a data quality defect that causes persistent eval failure at 0.45. Remove this record from scored_all.jsonl and re-run eval. Does the score reach 1.00 (5/5)? |
| E7.2 | evolve | DONE | Execute the E6.3 pilot: generate 10 research-analyst training records using WARNING and INCONCLUSIVE question templates from E6.3, targeting bricklayer-v2 and masonry/scripts. What verdicts does the agent produce? Does the pilot validate the question-framing approach? |

---

## Wave 8 — Evolve (E8): 2-Stage Eval + Research-Analyst Scale-Up

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E8.1 | evolve | DONE | Implement a 2-stage eval in `eval_agent.py` for research-analyst: Stage 1 scores evidence quality for prose responses (currently 0.00 due to JSON parse failure), Stage 2 scores verdict match for clean JSON. Does this raise research-analyst score from ~0.45 to >0.65? |
| E8.2 | evolve | DONE | Generate 8 more reasoning-style research-analyst training records targeting diverse topics: program.md design soundness, campaign yield rates, agent routing decision quality, synthesis completeness. Produce 4×HEALTHY + 2×WARNING + 1×PROMISING + 1×INCONCLUSIVE. Does the score reach 0.65+ with 18 total records? |
| E8.3 | evolve | DONE | Add 5 synthesizer-bl2 training records extracted from recall, masonry, and bricklayer-meta campaign sessions (different project contexts, diverse verdict types). Does the synthesizer-bl2 score stabilize at ≥0.90 with 10 total records? |
| E8.4 | evolve | DONE | Fix `masonry-guard.js` `hasErrorSignal()` to scope error signal detection to `newString` content only (not the entire `JSON.stringify(response)` which includes `oldString`). Does the false-positive rate drop to 0? Verify with a test edit that would previously trigger a false warning. |

---

## Wave 9 — Evolve (E9): research-analyst Curation + Metric Fix

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E9.1 | evolve | DONE | Remove 3 code-inspection records from research-analyst training data (E7.2-pilot-2, E7.2-pilot-3, E7.2-pilot-4) that always produce prose output (0.40 max score, below 0.50 threshold). Replace with 3 pure reasoning records targeting HEALTHY/WARNING/FAILURE verdicts. Does eval score stabilize at ≥0.65 with 18 clean reasoning records? |
| E9.2 | evolve | DONE | Add a verdict_match prerequisite gate to `build_metric()` in `eval_agent.py`: if `verdict_match == 0.0`, cap total score at 0.2 regardless of evidence quality. This prevents the calibration inversion (wrong verdict + good evidence = 0.60 false pass). Does this correctly reject wrong-verdict predictions while keeping correct-verdict scores unchanged? |
| E9.3 | evolve | DONE | Remove 4 misaligned Q4.x records (Q4.2/4.3/4.5/4.6) from research-analyst training data — they are task descriptions producing INCONCLUSIVE instead of the expected HEALTHY. Replace with 4 reasoning records where HEALTHY is the natural agent output (confirmed system designs, validated patterns). Does eval score rise above 0.50 with the Q4.x records removed? |
| E9.4 | evolve | DONE | After E9.3 curation, add 5 records covering the remaining failing patterns: PROMISING (E7.2-pilot-5 replacement), WARNING off-by-one (rec-6 fix), and context-rich HEALTHY records where the question text justifies the verdict without historical outcome context. Does eval reach ≥0.65 with the cleaned dataset? |

---

## Wave 10 — Evolve (E10): synthesizer-bl2 Calibration Exposure + Data Fix

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E10.1 | evolve | DONE | synthesizer-bl2 score dropped from ~0.45 to 0.20 after the E9.2 calibration inversion fix. Which specific records now fail, and is this the same structural mismatch (HEALTHY verdicts requiring tool access) as research-analyst? Diagnose per-record with predicted vs expected verdicts. |
| E10.2 | evolve | DONE | synthesizer-bl2 has 5 HEALTHY-expected records that score 0.00 (Q6.1, Q6.3, Q6.6, E8.3-synth-2, E8.3-synth-4). Remove or replace these records with WARNING/FAILURE records that have clear evidence the tool-free agent can reason about. Does score reach ≥0.50 with fixed dataset? |
| E10.3 | evolve | DONE | After the synthesizer-bl2 training data fix in E10.2, apply optimize_with_claude.py to synthesizer-bl2. Does the prompt optimization produce measurably better instructions, and does the eval score improve vs E10.2 baseline? |

---

## Wave 11 — Evolve (E11): Live Eval Prototype + Final Data Quality

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E11.1 | evolve | DONE | Design and prototype a live eval harness (Path B) for research-analyst: run eval with tools enabled so the agent can read files, search code, and produce evidence-backed verdicts. Does a tool-enabled agent score ≥0.85 on the existing 18 test questions? What infrastructure changes are required? |
| E11.2 | evolve | DONE | Fix 3 remaining synthesizer-bl2 data quality issues: (1) change E8.3-synth-5 expected verdict from PROMISING to INCONCLUSIVE (agent consistently predicts INCONCLUSIVE), (2) replace Q6.5 prose-producer with a self-evident WARNING record, (3) add 2 records targeting the stochastic INCONCLUSIVE/WARNING edge. Does synthesizer-bl2 score reach ≥0.60? |

---

## Wave 12 — Evolve (E12): Live Eval Recalibration

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E12.1 | evolve | DONE | Generate 20 live-eval-calibrated training records for research-analyst: questions where the current codebase has a clear answer a tool-enabled agent will find. Run each through eval_agent_live.py to bootstrap expected verdicts from tool-enabled agent outputs. What is the new live eval score with 20 calibrated records? |
| E12.2 | evolve | DONE | After E12.1, identify which of the existing 18 research-analyst tool-free records have INCONCLUSIVE expected verdicts that re-classify to WARNING/FAILURE with tool access (calibration gap records). How many records need re-labeling, and what is the corrected live eval score after re-labeling? |
| E12.3 | evolve | DONE | Apply the same live eval recalibration approach to synthesizer-bl2: generate 10 live-calibrated records (questions about campaign synthesis quality, finding completeness, multi-project synthesis). Does synthesizer-bl2 reach ≥0.60 on live-calibrated data? |

---

## Wave 13 — Evolve (E13): Calibration Cleanup + Optimization

**Generated from**: E12.1, E11.2, E11.1
**Mode transitions**: E12.1 IMPROVEMENT (path forward: severity re-labels + prose record fix + optimize on 38-record dataset) → E13.1/E13.2/E13.3; eval_agent_live.py agent-hardcoding gap → E13.4; E11.2 INCONCLUSIVE ceiling → E13.5 post-E12.3 followup; no routing baseline in 12 prior waves → E13.6/E13.7; candidate agents last_score=null → E13.8/E13.9; improve_agent.py convergence unknown → E13.10

| ID | Mode | Status | Question |
|----|------|--------|---------|
| E13.1 | evolve | DONE | E12.1 identified 2 FAILURE→WARNING severity disagreements (E12.1-live-5 and E12.1-live-16) where WARNING is the defensible verdict. Re-label both records' expected verdicts from FAILURE to WARNING in scored_all.jsonl. Does live eval score rise from 0.84 to ≥0.90 (17/20 → 19/20 pass rate)? |
| E13.2 | evolve | DONE | E12.1-live-14 is a stochastic prose producer (synthesis.md accuracy check) that scores ~0.40 partial across runs. Replace this record with a cleaner verification question targeting a specific measurable property of synthesis.md (e.g., verdict count by type, section completeness). Does the replacement record score ≥0.90 consistently across 3 runs? |
| E13.3 | evolve | PENDING | After E13.1+E13.2 fixes, run `improve_agent.py research-analyst --loops 2` on the 38-record dataset. Does prompt optimization produce measurably better instructions, and does live eval score exceed 0.84 baseline? What is the new live eval score? |
| E13.4 | evolve | DONE | `eval_agent_live.py` hardcodes `research-analyst` in its record loader — it cannot evaluate any other agent, blocking E12.3 synthesizer-bl2 live recalibration. Generalize: add `--agent` CLI flag (default `research-analyst`), rename the loader function, update record filter to `r.get("agent") == agent_name`. Verify with `--agent synthesizer-bl2 --eval-size 5`. |
| E13.5 | evolve | PENDING | After E12.3 produces 10 live-calibrated synthesizer-bl2 records (4 with PROSE gold labels), re-label the 4 PROSE records from their re-run verdicts (WARNING/FAILURE), then run `improve_agent.py synthesizer-bl2 --loops 2` on the combined 21-record dataset. Does live eval score exceed the E12.3 baseline of 0.62? |
| E13.6 | evolve | DONE | Establish a routing accuracy baseline for the Masonry four-layer router: create `masonry/scripts/score_routing.py` that runs 20 routing queries through `masonry/src/routing/router.py` and scores deterministic vs semantic vs LLM layer hit rates. What is the current deterministic layer coverage (target ≥60%)? |
| E13.7 | evolve | WARNING | Audit the deterministic routing layer keyword coverage in `masonry/src/routing/router.py`: list all registered slash-command patterns and mode-keyword patterns. Are there any commonly-used BrickLayer commands missing from the deterministic layer that require LLM fallback unnecessarily? |
| E13.8 | evolve | PENDING | Three candidate-tier agents — peer-reviewer, agent-auditor, and retrospective — have `last_score: null` in agent_registry.yml and no records in scored_all.jsonl. Generate 5 training records each (15 total) using the live record generation approach validated in E12.1. What baseline eval scores do these agents achieve on first run? |
| E13.9 | evolve | WARNING | Audit optimization-ready agents in `masonry/agent_registry.yml`: which agents have a non-null `last_score` but have not been optimized since their last score was recorded? For each, what is the estimated gain from running `improve_agent.py`? |
| E13.10 | evolve | PENDING_EXTERNAL | Run `improve_agent.py research-analyst --loops 3` on the cleaned 38-record dataset (after E13.1+E13.2). Does the optimization converge (score plateaus) or oscillate (score varies across loops)? What is the final score after 3 loops vs 1 loop? |

---

## Wave-mid

**Generated from findings**: Q1.1, Q1.5, Q2.2, Q2.4, E2.3
**Mode transitions applied**: Q1.1 DIAGNOSIS_COMPLETE → F-mid.1 Fix (mode dispatch in CI runner); Q1.5 DIAGNOSIS_COMPLETE → F-mid.2 Fix (PENDING_EXTERNAL normalization); Q2.2 WARNING → M-mid.1 Monitor (Fix mode scope-creep rate); Q2.4 WARNING → M-mid.2 Monitor (Predict subjectivity rate); E2.3 IMPROVEMENT → E-mid.1 Evolve (karen prompt optimization now unblocked)

### F-mid.1: Implement mode dispatch in `bl/ci/run_campaign.py` and `bl/runners/agent.py` as specified in Q1.1

**Status**: PENDING
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: Q1.1 — DIAGNOSIS_COMPLETE with a complete fix specification (~20 lines across 2 files); no mode context is injected into CI runner agent calls today
**Hypothesis**: Adding `_load_mode_context()` to `_dispatch()` and consuming `mode_context` in `run_agent()` will make CI-runner-dispatched agents mode-aware with zero regression to projects without `modes/` directories
**Method**: fix-implementer
**Success criterion**: `python -m bl.ci.run_campaign --project bricklayer-v2 --max-questions 1 --output /tmp/test.json` produces a result whose agent prompt contains the mode program text; existing projects without `modes/` produce identical output to pre-change

---

### F-mid.2: Fix `bl/ci/run_campaign.py` to handle `PENDING_EXTERNAL` and all BL 2.0 terminal statuses as specified in Q1.5

**Status**: PENDING
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: Q1.5 — DIAGNOSIS_COMPLETE; current normalization at line 67-68 silently converts `PENDING_EXTERNAL` → `PENDING`, causing parked questions to be re-run; also `_parse_questions_table()` regex silently drops rows with BL 2.0 status values
**Hypothesis**: Expanding `_TERMINAL_STATUSES` frozenset and fixing `_parse_questions_table()` regex will prevent parked questions from re-running and will correctly parse all BL 2.0 status values without data loss
**Method**: fix-implementer
**Success criterion**: A `questions.md` containing a `PENDING_EXTERNAL` question with a future `resume_after` is parsed by the CI runner without that question appearing in the pending list; all BL 2.0 status values (`DIAGNOSIS_COMPLETE`, `FIXED`, `FIX_FAILED`, `COMPLIANT`, `NON_COMPLIANT`, `CALIBRATED`) are preserved after parsing

---

### M-mid.1: Add Fix mode scope-creep risk to `monitor-targets.md` — track pre-flight checklist failure rate across Fix mode runs

**Status**: PENDING
**Operational Mode**: Monitor
**Priority**: MEDIUM
**Motivated by**: Q2.2 — WARNING; Fix mode pre-flight checklist was judged insufficient to catch underspecified DIAGNOSIS_COMPLETE findings; scope creep in Fix mode is a recurring risk that needs a surveillance metric
**Hypothesis**: Defining a monitor target for "Fix question rejected at pre-flight" rate will surface Fix mode quality issues before they cause wasted agent work; the appropriate WARNING threshold is ≥0.20 and FAILURE threshold is ≥0.40
**Method**: quantitative-analyst
**Success criterion**: `monitor-targets.md` gains a `fix_preflight_rejection_rate` entry with WARNING and FAILURE thresholds defined, plus measurement method: "count Fix findings with verdict=FIX_FAILED at pre-flight gate divided by total Fix questions run per wave"

---

### M-mid.2: Add Predict mode subjectivity rate to `monitor-targets.md` — track SUBJECTIVE verdicts as a fraction of total Predict outputs

**Status**: PENDING
**Operational Mode**: Monitor
**Priority**: MEDIUM
**Motivated by**: Q2.4 — WARNING; Predict mode verdict assignment (IMMINENT/PROBABLE/POSSIBLE/UNLIKELY) was found to be inherently SUBJECTIVE without a probability calibration protocol; unchecked subjectivity degrades campaign signal quality
**Hypothesis**: Tracking the fraction of Predict mode outputs that receive a SUBJECTIVE qualifier (vs a concrete tier assignment) will reveal whether the Predict mode program produces actionable verdicts or defaults to hedge language; WARNING threshold at ≥0.30
**Method**: quantitative-analyst
**Success criterion**: `monitor-targets.md` gains a `predict_subjectivity_rate` entry with WARNING threshold ≥0.30 and FAILURE threshold ≥0.60, with measurement method defined as counting Predict findings where agent marks verdict reasoning as SUBJECTIVE per wave

---

### E-mid.1: After karen reaching 1.00 eval score (E2.3), run `improve_agent.py karen` to optimize the prompt and verify it holds at ≥0.85 post-optimization

**Status**: PENDING
**Operational Mode**: evolve
**Priority**: MEDIUM
**Motivated by**: E2.3 — IMPROVEMENT (karen eval 1.00); optimization was blocked by training data bugs through Wave 2; now that the signal is clean, prompt optimization may produce more robust instructions that generalize beyond the 20-record eval set
**Hypothesis**: Running `improve_agent.py karen --loops 2` on the 379-record clean dataset will either improve or maintain ≥0.85 eval score; if score regresses, the optimizer auto-reverts and confirms 1.00 is the natural ceiling without further tuning
**Method**: quantitative-analyst (script execution + score comparison)
**Success criterion**: `improve_agent.py karen --loops 2` completes without regression; final eval score on held-out set is ≥0.85; `masonry/agent_snapshots/karen/history/` contains a run record showing the optimization trajectory

---

## Domain 5 — Frontier: BrickLayer's next evolution beyond 2.0

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q5.1 | frontier | DONE | If BrickLayer 2.0 had a multi-agent variant — where multiple modes run in parallel on the same project — what would the coordination mechanism look like? What prevents mode conflicts? |
| Q5.2 | frontier | DONE | What would a visual BrickLayer dashboard look like that shows all projects, their current mode, open findings, and the lifecycle stage progress? What is the most useful single-screen view? |

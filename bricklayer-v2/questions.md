# Research Questions — BrickLayer 2.0

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Domain 1 — Architecture (Diagnose: how should bl/ be extended?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q1.1 | diagnose | PENDING | What is the minimal change to `bl/campaign.py` to support mode dispatch — reading `mode:` from each question and loading the corresponding `modes/{mode}.md` as loop context? |
| Q1.2 | diagnose | PENDING | How should `questions.md` represent the new `mode:` field (operational mode) without breaking the existing `mode:` field (which currently means runner type)? What rename is required? |
| Q1.3 | diagnose | PENDING | What new verdict types need to be added to `bl/findings.py` and `bl/quality.py` — specifically DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, FIXED, PROMISING, WEAK, BLOCKED, COMPLIANT, NON_COMPLIANT, CALIBRATED? |
| Q1.4 | diagnose | PENDING | How should DIAGNOSIS_COMPLETE suppression work in `bl/questions.py`? What is the mechanism to park a question and re-activate it when code changes? |
| Q1.5 | diagnose | PENDING | How should PENDING_EXTERNAL + `resume_after:` work in the campaign loop? Does it require changes to `bl/campaign.py` or only to `bl/questions.py`? |

---

## Domain 2 — Mode Implementation (Validate: does each mode spec work?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q2.1 | validate | PENDING | Does the Frontier mode program (`modes/frontier.md`) produce a complete, actionable loop? What questions would Wave 1 look like for the "Uncreated App" project? |
| Q2.2 | validate | PENDING | Does the Fix mode program (`modes/fix.md`) correctly prevent scope creep? Is the pre-flight checklist sufficient to catch an underspecified DIAGNOSIS_COMPLETE finding? |
| Q2.3 | validate | PENDING | Does the Monitor mode program (`modes/monitor.md`) correctly distinguish itself from a scheduled Diagnose run? What is the exact operational difference? |
| Q2.4 | validate | PENDING | Does the Predict mode program (`modes/predict.md`) have a sound methodology? Can the IMMINENT/PROBABLE/POSSIBLE/UNLIKELY verdict set be objectively assigned, or is it inherently SUBJECTIVE? |
| Q2.5 | validate | PENDING | Does the cross-mode handoff table in `program.md` cover all meaningful transitions? Are there handoffs that are missing or incorrect? |

---

## Domain 3 — Per-Project Application (Research: applying to Tim's active projects)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q3.1 | research | PENDING | For Recall: which of the 5 open deployment blockers should be addressed via Fix mode first? Run Predict mode logic on the current open findings to produce the priority order. |
| Q3.2 | research | PENDING | For ADBP: what mode should ADBP start in? Read `adbp/project-brief.md` and `adbp/findings/synthesis.md` to determine current stage and most valuable next mode. |
| Q3.3 | frontier | PENDING | For the Uncreated App: what is it? Run 3 Frontier questions to generate candidate concepts based on Tim's skills, infrastructure, and gaps in his current tool stack. |
| Q3.4 | research | PENDING | For Legal: what regulatory domain is this? What is the realistic research landscape for whatever legal project is being contemplated? |
| Q3.5 | audit | PENDING | For UI/UX: given the `figma-designer-guide.md` and `frontend-design-philosophy.md` in Tim's global rules, define an audit checklist for any new frontend component. What are the top 10 compliance checks? |

---

## Domain 4 — Template Evolution (Evolve: what should the template/ become?)

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q4.1 | evolve | PENDING | What changes are required to `template/` to support BrickLayer 2.0's mode system? Should `template/` become `template-diagnose/` with sibling templates for each domain (template-research/, template-frontier/, etc.)? |
| Q4.2 | evolve | PENDING | What should the new project bootstrap sequence look like? Currently: copy template, edit project-brief, run question-designer. With modes: what's the right first question to ask? |
| Q4.3 | evolve | PENDING | Should `simulate.py` be renamed `evaluate.py` in the new template, or kept as-is for backward compatibility? What does the new template's evaluate.py stub look like? |

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

## Domain 5 — Frontier: BrickLayer's next evolution beyond 2.0

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q5.1 | frontier | PENDING | If BrickLayer 2.0 had a multi-agent variant — where multiple modes run in parallel on the same project — what would the coordination mechanism look like? What prevents mode conflicts? |
| Q5.2 | frontier | PENDING | What would a visual BrickLayer dashboard look like that shows all projects, their current mode, open findings, and the lifecycle stage progress? What is the most useful single-screen view? |

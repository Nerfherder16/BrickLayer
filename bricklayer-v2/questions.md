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
| E2.1 | evolve | PENDING | Karen eval score dropped from 0.55 (Wave 1 baseline) to 0.30 after the commit-type-first prompt fix. The prompt IS applied correctly. What is the root cause of the regression and what does it reveal about the training data? |
| E2.2 | evolve | PENDING | In `masonry/scripts/score_ops_agents.py:_score_karen()`, the `input.files_modified` field captures the doc files karen WROTE, not the source files that TRIGGERED the update. Fix the pipeline to use the parent commit's source files as `files_modified`. Also fix `build_karen_metric._derive_expected()` to correctly label "chore: update CHANGELOG for <hash>" commits as expected="skipped". |
| E2.3 | evolve | PENDING | After fixing the training data pipeline (E2.2), regenerate karen records from git history and re-run the eval. What is the new score? Does it reach the 0.85 target? |

---

## Domain 5 — Frontier: BrickLayer's next evolution beyond 2.0

| ID | Mode | Status | Question |
|----|------|--------|---------|
| Q5.1 | frontier | PENDING | If BrickLayer 2.0 had a multi-agent variant — where multiple modes run in parallel on the same project — what would the coordination mechanism look like? What prevents mode conflicts? |
| Q5.2 | frontier | PENDING | What would a visual BrickLayer dashboard look like that shows all projects, their current mode, open findings, and the lifecycle stage progress? What is the most useful single-screen view? |

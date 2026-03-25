# Agent Fleet Audit Report -- BrickLayer v2

**Date**: 2026-03-24  
**Auditor**: agent-auditor  
**Inputs**: agents_dir=`.claude/agents/` (10 agents), findings_dir=`findings/` (56 rows in results.tsv + subdirs)

---

## Executive Summary

The BrickLayer v2 agent fleet is structurally sound across 10 agents. All agents have complete frontmatter, explicit output contracts, and Recall integration. Three issues require attention:

1. **Missing frontier-analyst** (HIGH): No frontier-analyst.md for FR-prefix questions, blocking Frontier mode and 3 mode-transition rules
2. **research-analyst static ceiling** (MEDIUM): Tool-free eval ceiling 0.44-0.61; live eval required for >=0.85 accuracy
3. **9 agents unmeasured** (MEDIUM): Training data in scored_all.jsonl but last_score=null in registry

**Overall fleet verdict: WARNING**

---
## 1. Agent Inventory

| Agent | Mode | Verdict Set | Output Contract | Recall | Status |
|-------|------|-------------|-----------------|--------|--------|
| cascade-analyst | Predict (P) | IMMINENT/PROBABLE/POSSIBLE/UNLIKELY | JSON | Yes | PASS |
| compliance-auditor | Audit (A) | COMPLIANT/NON_COMPLIANT/PARTIAL/NOT_APPLICABLE | JSON | Yes | PASS |
| design-reviewer | Validate (V) | HEALTHY/WARNING/FAILURE/SUBJECTIVE | JSON | Yes | PASS |
| diagnose-analyst | Diagnose (D) | HEALTHY/WARNING/FAILURE/DIAGNOSIS_COMPLETE/INCONCLUSIVE/PENDING_EXTERNAL | JSON | Yes | PASS |
| evolve-optimizer | Evolve (E) | IMPROVEMENT/HEALTHY/WARNING/REGRESSION | JSON | Yes | PASS |
| fix-implementer | Fix (F) | FIXED/FIX_FAILED/INCONCLUSIVE | JSON | Yes | PASS |
| health-monitor | Monitor (M) | OK/DEGRADED/DEGRADED_TRENDING/ALERT/UNKNOWN | JSON | Yes | PASS |
| hypothesis-generator-bl2 | Meta (wave gen) | WAVE_GENERATED | JSON | Yes | PASS |
| question-designer-bl2 | Meta (init) | QUESTIONS_GENERATED | JSON | Yes | PASS |
| research-analyst | Research (R) | HEALTHY/WARNING/FAILURE/INCONCLUSIVE | JSON | Yes + DSPy | PASS |

All 10 agents: frontmatter complete (name, description), JSON output contract present, Recall integration present.

---
## 2. Agent Quality Assessment

### 2.1 Structural Completeness

All 10 agents pass every structural gate check:
- Frontmatter with name and description: all 10
- Pre-flight / evidence-gathering protocol: all 10
- Verdict decision rules with explicit named verdicts: all 10
- Output format section: all 10
- JSON output contract block: all 10
- Recall inter-agent memory section: all 10

### 2.2 Role Differentiation

No mode overlap detected. Each agent maps to a unique question prefix:

| Prefix | Agent | Handles |
|--------|-------|---------|
| D | diagnose-analyst | Root cause tracing -> DIAGNOSIS_COMPLETE |
| F | fix-implementer | Targeted repair -> FIXED/FIX_FAILED |
| R | research-analyst | Assumption stress-testing -> HEALTHY/WARNING/FAILURE |
| A | compliance-auditor | Checklist auditing -> COMPLIANT/NON_COMPLIANT |
| V | design-reviewer | Design validation -> HEALTHY/WARNING/FAILURE/SUBJECTIVE |
| E | evolve-optimizer | Metric improvement -> IMPROVEMENT/REGRESSION |
| M | health-monitor | Threshold monitoring -> OK/DEGRADED/ALERT |
| P | cascade-analyst | Cascade projection -> IMMINENT/PROBABLE/POSSIBLE/UNLIKELY |
| FR | (MISSING) | Frontier exploration -- NO AGENT IN FLEET |
| wave gen | hypothesis-generator-bl2 | Mode-transition question generation |
| init | question-designer-bl2 | Initial question bank |

**GAP: No frontier-analyst.md exists in .claude/agents/.** Both hypothesis-generator-bl2 and question-designer-bl2 reference frontier-analyst behavior but no agent file implements it. Frontier questions fall through to unstructured LLM response, losing the structured verdict system.

### 2.3 Verdict Set Integrity

| Agent | Completeness | Decision rules | Notes |
|-------|-------------|---------------|-------|
| diagnose-analyst | Full (6 verdicts) | Explicit | DIAGNOSIS_COMPLETE requires all 4 Fix Spec fields present |
| fix-implementer | Full (3 verdicts) | Explicit | Specificity gate blocks underspecified specs before touching code |
| research-analyst | Full (4 verdicts) | Explicit + DSPy | DSPy section added 2026-03-24, strictly additive |
| compliance-auditor | Full (4 item + 3 overall) | Explicit table | Structural violation auto-triggers overall NON_COMPLIANT |
| design-reviewer | Full (4 incl SUBJECTIVE) | Explicit + halt | SUBJECTIVE halts the loop and asks human |
| evolve-optimizer | Full (4 verdicts) | Explicit | >=5% threshold prevents noise from counting as IMPROVEMENT |
| health-monitor | Full (5 incl DEGRADED_TRENDING) | Explicit | DEGRADED_TRENDING requires 2+ data points -- prevents false early warnings |
| cascade-analyst | Full (4 verdicts) | Explicit quantitative | IMMINENT <=30d, PROBABLE 31-90d, POSSIBLE 91-180d, UNLIKELY >180d |
| hypothesis-generator-bl2 | WAVE_GENERATED | Mode-transition table | All 11 verdict->mode transitions defined |
| question-designer-bl2 | QUESTIONS_GENERATED | Mode selection guide | Mode selection rationale required in output |

Note: DEGRADED_TRENDING verdict confirmed in health-monitor.md. Consistent with E1.1 IMPROVEMENT (added to modes/monitor.md). Agent implementation matches mode spec.

### 2.4 Research-Analyst DSPy Section

DSPy Optimized Instructions section (added 2026-03-24) is strictly additive:
- Adds evidence hierarchy: Direct measurement > Primary source > Official > Industry analyst > Secondary
- Adds code inspection discipline with explicit bash commands
- Adds gap analysis pattern for claim-vs-implementation checking
- Adds self-nomination for specialist routing recommendations
- Delimiter correctly closed with /DSPy Optimized Instructions HTML comment
- No contradictions with base agent instructions

Only agent with DSPy optimization applied. Assessment: consistent and non-conflicting with base spec.

---
## 3. Campaign Performance Analysis

### 3.1 Results Distribution (results.tsv, 56 rows)

| Verdict | Count | Notes |
|---------|-------|-------|
| IMPROVEMENT | 22 | Dominant -- evolve-heavy campaign |
| WARNING | 13 | Active issues tracked with follow-up questions |
| HEALTHY | 6 | Baseline confirmations |
| DIAGNOSIS_COMPLETE | 5 | Q1.1-Q1.5, Wave 1, all with Fix Specifications |
| PROMISING | 3 | Q3.3 (Uncreated App), Q5.1 (multi-agent BL), Q5.2 (BL dashboard) |
| INCONCLUSIVE | 2 | Q3.4 (missing legal project), E11.2 (synthesizer structural ceiling) |
| REGRESSION | 1 | E2.1 -- fully root-caused and resolved in E2.2/E2.3 |

IMPROVEMENT:WARNING ratio = 22:13 = 1.7:1. Net-positive campaign. No unresolved FAILURE or REGRESSION verdicts remain open.

### 3.2 Key Findings Affecting Agent Quality

**E2.2 (IMPROVEMENT)**: Karen training pipeline had 3 compounding bugs fixed:
1. files_modified captured karen output files, not trigger source files (73% wrong input context)
2. 237/321 records mislabeled for bot commits
3. Windows cp1252 encoding silently truncated karen.md at Unicode arrow characters in --system-prompt argument
Karen eval reached 1.00 (20/20) in E2.3. Most impactful single finding in the Evolve wave.

**E9.2 (IMPROVEMENT)**: Calibration inversion fix in build_metric(). Verdict_match prerequisite gate was missing -- wrong verdicts scored up to 0.60 instead of capping at 0.00. Foundational correctness fix for the entire eval infrastructure. 4/4 unit tests pass.

**E11.1 (IMPROVEMENT)**: Live eval harness (eval_agent_live.py) implemented. WARNING records score 0.97-0.98 with tools, vs ~0.45 tool-free. Confirms tool-dependent agents require live eval for accurate measurement.

**E12.1 (IMPROVEMENT)**: Research-analyst live eval 0.84 (17/20), near 0.85 target. FAILURE/WARNING boundary calibration is the remaining gap.

**E12.3 (IMPROVEMENT)**: Synthesizer-bl2 live eval 0.62 (6/10), meeting >=0.60 target. Tool-free ceiling (0.55) broken by live eval path.

**E13.6/E13.7 (HEALTHY/WARNING)**: Routing deterministic coverage 75% (target >=60%, optimal >=90%). 4 coverage gaps with exact fixes in E13.7.

**E13.9 (WARNING)**: 9 agents with >=5 training records have last_score: null. Running in production unmeasured.

---
## 4. Open Issues

### 4.1 CRITICAL: Missing frontier-analyst agent

**Severity**: HIGH

No frontier-analyst.md in .claude/agents/. Frontier mode (FR prefix) questions have no designated runner. Three mode-transition rules in hypothesis-generator-bl2 (BLOCKED -> Diagnose, PROMISING + F_now >= 0.3 -> Research, PROMISING + F_now < 0.3 -> Validate) can never be triggered because no agent produces FR-prefix findings.

**Recommendation**: Create frontier-analyst.md with:
- PROMISING/BLOCKED/POSSIBLE verdict set
- Pre-flight reading project-brief.md + docs/ for context
- Framing from question-designer-bl2.md: remove constraints, draw analogies, maximum ambition exploration
- Output contract with JSON block including F_now (feasibility-now) field for PROMISING verdicts

### 4.2 WARNING: 9 agents have no eval baseline

**Severity**: MEDIUM

E13.9 confirms 9 agents with >=5 training records have last_score: null in agent_registry.yml.
Priority order for establishing baselines:
1. quantitative-analyst (76 records, last known ~0.70 at E4.1, may have drifted)
2. karen (379 records, clean training data post-E2.2 fix)
3. research-analyst (53 records, live eval 0.84 known, static baseline missing)
4. regulatory-researcher (22), mortar (15), architect (15), devops (14), competitive-analyst (14), refactorer (12)

### 4.3 WARNING: Deterministic routing layer has 4 coverage gaps

**Severity**: MEDIUM

E13.7 identifies 4 patterns missing from masonry/src/routing/deterministic.py:
- No _EVAL_PATTERN for eval/improve-agent workflow (highest frequency in active campaigns)
- _DIAGNOSE_PATTERN misses alternative phrasings of what-is-broken questions
- _ARCHITECT_PATTERN misses short-form phrasings like architect-a-X or design-a-X
- No _MODE_GUIDANCE_PATTERN for what-mode-should-I-use queries

These 4 gaps cause ~25 unnecessary LLM calls per 100 routing decisions.
Fix: 14 lines in deterministic.py -- exact regex patterns in E13.7.

### 4.4 WARNING: research-analyst structural ceiling on static eval

**Severity**: MEDIUM

Static eval ceiling is 0.44-0.61 regardless of prompt quality, because HEALTHY verdicts require tool access to verify.
Status: Live eval validated at 0.84 (E12.1). Confirmed architectural property, not a regression.
Recommendation: Use eval_agent_live.py only for research-analyst. Document in research-analyst.md or eval_agent.py.

### 4.5 WARNING: synthesizer-bl2 prose output stochasticity

**Severity**: LOW

Multi-file cross-reference questions cause synthesizer-bl2 to produce prose instead of JSON (~0.40 vs ~0.90 when JSON).
E13.2 demonstrates single-file count-check questions eliminate prose production entirely.
Status: E12.3 live eval target (>=0.60) met. Residual stochasticity confined to high-complexity records.
Recommendation: Avoid multi-file comparison records in synthesizer-bl2 training data.

---
## 5. Mode-Transition Integrity Check

hypothesis-generator-bl2.md defines 11 mode-transition rules. Agent availability check:

| From verdict | To mode | Target agent | Status |
|-------------|---------|--------------|--------|
| DIAGNOSIS_COMPLETE | Fix | fix-implementer.md | OK |
| FAILURE (Diagnose) | Diagnose narrow | diagnose-analyst.md | OK |
| FAILURE (Research) | Validate | design-reviewer.md | OK |
| WARNING (any) | Monitor | health-monitor.md | OK |
| PROBABLE/IMMINENT (Predict) | Monitor | health-monitor.md | OK |
| BLOCKED (Frontier) | Diagnose | diagnose-analyst.md | Target OK; source agent MISSING |
| PROMISING F_now>=0.3 (Frontier) | Research | research-analyst.md | Target OK; source agent MISSING |
| PROMISING F_now<0.3 (Frontier) | Validate | design-reviewer.md | Target OK; source agent MISSING |
| NON_COMPLIANT (Audit) | Diagnose | diagnose-analyst.md | OK |
| FIX_FAILED (Fix) | Diagnose | diagnose-analyst.md | OK |
| INCONCLUSIVE (any) | Same/Research | research-analyst.md | OK |

Frontier-originated transitions (rows 6-8) are structurally defined but unreachable -- no frontier-analyst agent exists to produce FR-prefix findings. Amplifies Issue 4.1.

---

## 6. Anti-Pattern Check

| Anti-pattern | Agent at risk | Status |
|-------------|--------------|--------|
| Assumed compliant without evidence | compliance-auditor | NOT PRESENT -- evidence required for every verdict |
| Scope creep during fix | fix-implementer | NOT PRESENT -- explicit anti-patterns section and specificity gate |
| Re-diagnosing DIAGNOSIS_COMPLETE issues | diagnose-analyst | MITIGATED -- suppression discipline + Recall session-start search |
| O(N^2) cascade pair analysis | cascade-analyst | MITIGATED -- top 3-5 most dangerous pairs only rule |
| Vague timelines | cascade-analyst | MITIGATED -- quantitative calculation or instance-count criterion required |
| Subjective probability assignment | cascade-analyst | MITIGATED -- explicit day-count thresholds for all 4 verdicts |
| Writing findings without measuring | health-monitor | MITIGATED -- UNKNOWN verdict if measurement fails; never infer |
| Re-checking DIAGNOSIS_COMPLETE | hypothesis-generator-bl2 | MITIGATED -- explicit do-not-re-check rule |

No active anti-patterns found across the fleet.

---
## 7. Recommendations by Priority

### Immediate (before next campaign wave)

1. **Create frontier-analyst.md** -- fleet has no agent for FR-prefix questions, blocking Frontier mode entirely and making 3 mode-transition rules unreachable.

2. **Document live-eval-only constraint for research-analyst** -- add note to research-analyst.md or eval_agent.py that static eval underestimates by ~40% and eval_agent_live.py must be used.

### Before Wave E14

3. **Establish eval baselines for untested agents**:
   - python masonry/scripts/eval_agent.py quantitative-analyst --eval-size 20
   - python masonry/scripts/eval_agent.py karen --eval-size 30

4. **Apply 4 deterministic routing pattern extensions** (E13.7, 14 lines in masonry/src/routing/deterministic.py).

5. **Run research-analyst optimization cycle** (53 live-calibrated records, first clean optimization run):
   - python masonry/scripts/improve_agent.py research-analyst --loops 2

### Ongoing

6. **Audit synthesizer-bl2 training records** before each eval wave. Replace multi-file comparison records with single-file equivalents per E13.2 pattern.

7. **Update agent_registry.yml last_score** after each eval run. Null scores are invisible gaps in fleet health.

---

## 8. Fleet Health Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Structural completeness | 10/10 | All 10 agents pass all structural gate checks |
| Role differentiation | 9/10 | Missing frontier-analyst for FR prefix |
| Verdict set integrity | 10/10 | All verdict sets complete and decision-rule-explicit |
| DSPy optimization coverage | 1/10 agents | Only research-analyst has baseline + optimization |
| Campaign outcome rate | 28/56 = 50% IMPROVEMENT+HEALTHY | Strong net-positive trend |
| Routing determinism | 75% (target 90%) | 4 known gaps with exact fixes ready |
| Eval coverage | 2/10 agents with known score | 8 agents unmeasured in production |

**Overall Fleet Grade: WARNING** -- Structurally sound, actively improving, with measurable gaps in frontier coverage, eval baselines, and routing determinism. No critical failures. Highest-severity gap is the missing frontier-analyst agent.

---

*Audit complete. Report written 2026-03-24.*
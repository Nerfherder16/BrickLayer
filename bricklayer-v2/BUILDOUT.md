# BrickLayer 2.0 — Build Out Instructions

**Status**: Wave 1 complete. All engine gaps diagnosed. Ready to implement.
**Source**: Wave 1 findings (Q1.1–Q5.2) + recall-arch-frontier session (2026-03-16)

---

## What's Already Done

The design layer is complete:
- `project-brief.md` — full mode system spec
- `program.md` — master runtime program
- `modes/*.md` — all 9 mode programs exist
- `findings/Q1.1–Q1.5.md` — DIAGNOSIS_COMPLETE specs for all 5 engine gaps
- `findings/synthesis.md` — Wave 1 synthesis

Nothing in `bl/` has been touched yet. All 5 fixes are small and independent once sequenced correctly.

---

## Implementation Sequence

Total estimated engineering: **~4 hours, ~7 files**.
Critical path: **Q1.2 → Q1.3 → Q1.1 → (Q1.4 + Q1.5 parallel)**

### Step 1 — Add `operational_mode` field to questions parser (Q1.2)
**File**: `bl/questions.py`
**Time**: 30 min
**Change**: Add `operational_mode` as a parsed field alongside the existing `mode` (runner type). Rename the internal variable for runner type to `runner` in the question dict to eliminate the collision. The `questions.md` format gets a new optional `operational_mode:` line — existing questions without it default to `"diagnose"`.

Key constraint: `mode:` in questions.md currently means runner type (agent, http, subprocess, correctness). The new operational mode field must use a different key — `operational_mode:` — to avoid breaking existing projects.

### Step 2 — Expand verdict types (Q1.3)
**Files**: `bl/findings.py`, `bl/questions.py`
**Time**: 30 min
**Change**: Add 23 new verdict strings to four data structures:

- `severity_map` in `findings.py` — maps each new verdict to High/Medium/Low/Info
- `_VERDICT_CLARITY` in `findings.py` — whether the verdict is actionable
- `classify_failure_type()` guard in `findings.py` — don't raise on unknown verdict
- `sync_status_from_results()` verdict list in `questions.py` — hardcoded list that blocks unrecognized verdicts

New verdict set by mode:
```
Frontier:   PROMISING, WEAK, BLOCKED
Benchmark:  CALIBRATED, UNCALIBRATED, NOT_MEASURABLE
Fix:        FIXED, FIX_FAILED
Audit:      COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE
Evolve:     IMPROVEMENT, REGRESSION
Predict:    IMMINENT, PROBABLE, POSSIBLE, UNLIKELY
Monitor:    OK, DEGRADED, ALERT, UNKNOWN
Any:        DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, SUBJECTIVE
```

### Step 3 — Mode dispatch in campaign.py (Q1.1)
**Files**: `bl/campaign.py`, `bl/runners/agent.py`
**Time**: 1 hour
**Depends on**: Step 1 (operational_mode field must exist)

Three additions:

**1. `_load_mode_context()` helper** (new function in `campaign.py`):
```python
def _load_mode_context(operational_mode: str) -> str:
    modes_dir = cfg.project_root / "modes"
    mode_file = modes_dir / f"{operational_mode}.md"
    if mode_file.exists():
        return mode_file.read_text(encoding="utf-8")
    return ""
```

**2. Inject mode context in `run_and_record()`** (before `run_question` call):
```python
op_mode = question.get("operational_mode", "")
if op_mode:
    question = dict(question)  # don't mutate original
    question["mode_context"] = _load_mode_context(op_mode)
```

**3. Agent runner reads `mode_context`** (in `runners/agent.py`, prepend to prompt):
```python
mode_ctx = question.get("mode_context", "")
if mode_ctx:
    prompt = f"## Mode Program\n\n{mode_ctx}\n\n---\n\n{prompt}"
```

No changes to runner registry, findings pipeline, or results.tsv format.

### Step 4a — DIAGNOSIS_COMPLETE suppression (Q1.4)
**Files**: `bl/questions.py`, `bl/campaign.py`, per-project `findings/` scan
**Time**: 1.5 hours
**Depends on**: Step 2 (verdict type must be registered)

When a finding has verdict `DIAGNOSIS_COMPLETE`, the corresponding question is parked — removed from the active question bank and not regenerated — until either:
- A relevant git commit is detected (code change in the diagnosed file)
- The human manually re-activates it (adds `recheck: true` to the question)

Implementation:
1. `questions.py`: add `suppressed: bool` field, set `True` when `sync_status_from_results()` sees DIAGNOSIS_COMPLETE
2. `campaign.py`: filter out `suppressed=True` questions before the loop
3. Git hook or campaign startup check: `git log --since=<finding_date> -- <target_file>` — if commits found, clear suppression

### Step 4b — PENDING_EXTERNAL with resume_after (Q1.5)
**Files**: `bl/questions.py`, `bl/campaign.py`
**Time**: 50 min
**Depends on**: Step 2 (verdict type must be registered)

When verdict is `PENDING_EXTERNAL`, the finding includes `resume_after: ISO-8601`. The campaign loop skips any question whose `resume_after` timestamp hasn't passed. No human intervention needed — the question automatically rejoins the active bank after the date.

Implementation:
1. `questions.py`: parse optional `resume_after:` field from questions.md (ISO-8601 string)
2. `campaign.py`: before dispatching a question, check `resume_after` against `datetime.now(UTC)` — skip if in future
3. Finding writer: extract `resume_after:` from the finding body and write it back to the question on sync

---

## Mode Spec Fixes (from Wave 1 WARNINGs)

These are fixes to `modes/*.md` content, not to `bl/` engine code.

### Fix mode pre-flight gate too permissive (Q2.2 WARNING)
**File**: `modes/fix.md`
Add a specificity gate before implementation begins. A DIAGNOSIS_COMPLETE finding must include all four:
- Target file: exact path
- Target location: line number or function name
- Concrete edit: diff-level description (not "improve performance")
- Verification command: runnable, produces pass/fail

If any are missing, Fix mode outputs `FIX_FAILED` with reason "Underspecified finding — return to Diagnose."

Also add: `FIX_FAILED` findings must include a "Root Cause Update" section — what the hypothesis was, why it was wrong, what the updated hypothesis is.

### Predict mode verdict calibration (Q2.4 WARNING)
**File**: `modes/predict.md`
Add objective decision criteria for POSSIBLE/UNLIKELY:
- `IMMINENT`: cascade completes in ≤30 days given current trajectory
- `PROBABLE`: cascade completes in 31–90 days
- `POSSIBLE`: cascade completes in 91–180 days, requires 2+ preconditions still pending
- `UNLIKELY`: cascade requires ≥3 preconditions none of which are active

### Cross-mode handoff gaps (Q2.5 WARNING)
**File**: `program.md` cross-mode handoff table
Three missing transitions:
- `Benchmark UNCALIBRATED → Diagnose` (can't measure → investigate why)
- `Monitor DEGRADED (sustained) → Predict` (degradation pattern → cascade risk)
- `Evolve REGRESSION → Fix` (improvement caused regression → treat as diagnosis)

---

## Frontier Mode: Lessons from recall-arch-frontier (2026-03-16)

177-question Frontier run on Recall architecture. Key lessons that should inform `modes/frontier.md`.

### Frontier produced the correct output — the evaluation framework was wrong

The recall-arch-frontier session was evaluated against "how many findings are directly buildable in the current Recall codebase." That's the wrong metric for Frontier mode. Frontier is a whitepaper generator. It produces ideal architecture from first principles. The gap between Frontier output and the current codebase IS the expected output — it defines the long-horizon roadmap, not the next sprint.

**Add to `modes/frontier.md`**:
> Frontier findings that don't map to the current codebase are not failures. The gap between the frontier ideal and the current system is the roadmap. Frontier is evaluated on the quality of the target architecture, not on immediate buildability.

### The 99% BREAKTHROUGH problem

493 of 496 ideas (99.4%) scored BREAKTHROUGH. When nearly everything is a BREAKTHROUGH, the classification is meaningless. The scoring formula (N×0.40 + E×0.35 + F×0.25) rewards novelty and field-analogy evidence heavily. Feasibility at 25% was scored against "could this work in principle" — not against current prerequisites.

**Fix for `modes/frontier.md`**: Split feasibility into two sub-scores:
- `F_principle`: can this work in a system like this in principle? (0.0–1.0)
- `F_now`: does the current codebase have the prerequisites to build this today? (0.0–1.0)

Report both. Use `F_principle` for the quality formula (Frontier is about ideal targets). Flag ideas where `F_now < 0.30` as `BLOCKED` regardless of overall quality score — they need foundation work first.

**Expected verdict distribution for a healthy Frontier session**:
- PROMISING: 40–60% (good ideas worth pursuing)
- WEAK: 20–30% (interesting but fundamental problems)
- BLOCKED: 20–30% (good ideas, prerequisites missing)

If PROMISING > 80%, the threshold is too loose. Re-run with tighter novelty criteria.

### Absence verification is the highest-ROI methodology

The most practically valuable findings in the 177-question session came from exhaustive absence checks: "does this mechanism actually exist in the codebase?" Q166 (CO_RETRIEVED absent from entire repo) and Q175 (SimHash absent) caught real production gaps — a health metric computing the wrong edge type, an outbox table with no consumer.

**Add to `modes/frontier.md`**:
> Before designing how a mechanism should work, verify whether it already exists. An absence proof (exhaustive grep/ast-grep of the codebase) is a valid Frontier finding that often outranks a full architectural design in practical value.

### Frontier → downstream mode handoff

Frontier findings feed into other modes. The handoff criteria need to be explicit:

| Frontier verdict | Handoff condition | Target mode |
|---|---|---|
| PROMISING | Human approves | Research — stress-test the idea |
| PROMISING (with F_now < 0.30) | Human approves | Validate — is the design right before building prerequisites? |
| WEAK | Fundamental flaw identified | Archive — revisit only if constraints change |
| BLOCKED | Prerequisite identified | Diagnose — what exactly is missing and how to build it? |

---

## Template Updates

Once `bl/` changes are implemented, update `template/` to reflect the new mode system.

- Add `modes/` directory to template with stub programs for all 9 modes
- Add `operational_mode:` field to the question template in `QUICKSTART.md`
- Add `ideas.md` stub (Frontier mode output file)
- Add `monitor-targets.md` stub (Monitor mode input file)
- Consider `template-frontier/` as a specialized template — pre-loaded with field-analogy question patterns and absence-verification question patterns

---

## What This Does NOT Change

Per project-brief.md invariants:
- `campaign.py` core loop — only adding mode dispatch, not replacing anything
- `questions.md` format — additive only (new `operational_mode:` field)
- `findings/` format — additive (new verdict types, same structure)
- `results.tsv` — additive (new verdict values accepted)
- `synthesis.md` — unchanged
- `bl/runners/` — additive only
- `constants.py` per project — unchanged
- All existing projects continue to work without modification (default `operational_mode: diagnose`)

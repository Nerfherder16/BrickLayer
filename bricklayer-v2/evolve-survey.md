# BrickLayer 2.0 — Evolve Survey (Wave 1)

**Session date**: 2026-03-24
**Mode**: evolve
**Survey completed before question generation**: yes

---

## Signal Sources Checked

1. **Finding history** — `findings/`, `results.tsv` (20 findings, Wave 1)
2. **Agent accuracy** — `masonry/agent_snapshots/karen/eval_latest.json`
3. **Git hotspots** — `git log --stat --since=60d`
4. **Recall signal** — not queried (no stale improvement flags found in scope)
5. **Test coverage** — not applicable (BL 2.0 is a documentation/program framework, not code-only)

---

## Completed Since Wave 1

The following WARNINGs from Wave 1 have already been resolved:

| Source finding | What was fixed | Confirmed |
|----------------|---------------|-----------|
| Q2.2 — Fix pre-flight too permissive | Specificity gate added to `modes/fix.md` (target file, line, diff-level edit, verification command, Root Cause Update) | ✓ Grep confirmed |
| Q2.4 — Predict POSSIBLE/UNLIKELY criteria | Quantitative + qualitative thresholds added to `modes/predict.md` | ✓ Grep confirmed |
| Q2.5 — Missing cross-mode handoffs | Benchmark→Evolve, Research→Validate, Fix→Monitor added to `program.md` | ✓ Grep confirmed |
| Q1.1–Q1.5 — bl/ engine mode dispatch | All implemented: operational_mode, verdict types, DIAGNOSIS_COMPLETE suppression, resume_after, mode_context injection | ✓ Code confirmed |

---

## Improvement Candidates

### Candidate 1: Monitor mode missing DEGRADED_TRENDING verdict
- **Source**: Q2.3 synthesis note ("Monitor missing DEGRADED_TRENDING verdict for metrics approaching threshold")
- **Current state**: `modes/monitor.md` verdict set is `OK | ALERT | DEGRADED | UNKNOWN`. No trending verdict.
- **Gap**: A metric can trend toward a threshold over multiple runs without ever triggering DEGRADED/ALERT in any single run. There is no verdict for "not yet degraded but moving that way."
- **Proposed change**: Add `DEGRADED_TRENDING` verdict with explicit decision rule (e.g., delta trend across 3+ consecutive runs moving toward WARNING threshold) + update cross-mode handoff to Predict.
- **ROI**: `estimated_impact=HIGH × implementation_ease=HIGH` → **Immediate target**
  - Impact: Enables proactive alert before threshold breach; prevents ALERT→fire-drill pattern
  - Ease: Text edit to `modes/monitor.md` + one line in `program.md` cross-mode table

### Candidate 2: Validate mode FAILURE lacks routing guidance
- **Source**: Q2.5 synthesis note ("Validate FAILURE should split on system existence")
- **Current state**: `modes/validate.md` has no guidance on what happens after FAILURE — the cross-mode handoff is in `program.md` but validate.md itself doesn't mention it.
- **Gap**: The validate.md session-end section produces a Go/No-Go recommendation but doesn't tell the agent where to route FAILURE findings (new system → Research; deployed system → Diagnose). Agents reading validate.md alone will miss this.
- **Proposed change**: Add a "FAILURE routing" section to `modes/validate.md` that documents the two-path split explicitly.
- **ROI**: `estimated_impact=MEDIUM × implementation_ease=HIGH` → **Immediate target**
  - Impact: Prevents misrouted fix work when validate fails on a deployed system vs. a design doc
  - Ease: Text edit to `modes/validate.md` (~6 lines)

### Candidate 3: Karen agent accuracy (0.55 → target 0.85)
- **Source**: `masonry/agent_snapshots/karen/eval_latest.json`
- **Current state**: score=0.55, eval_size=20, evaluated_at=2026-03-24T01:36:22Z. Gap to target: 0.30.
- **Failure pattern**: All 20 eval examples show `predicted.action = "skipped"` regardless of input. Karen is defaulting to "skipped" even when the example expects "updated" (doc_files_written > 0). This is a calibration failure, not a random error.
- **Root cause hypothesis**: The claude-p eval prompt for karen doesn't distinguish clearly enough between the "session-start probe" (no changes yet, skipped correct) and the "post-commit doc update" case (files changed, updated required).
- **Proposed change**: Audit karen prompt's trigger conditions. Add concrete examples of the "updated" signal (commit with feat/fix/refactor + non-doc files modified = should act) vs. "skipped" signal (no-op commit, probe-only = correct to skip).
- **ROI**: `estimated_impact=HIGH × implementation_ease=MEDIUM` → **Immediate target**
  - Impact: Karen fires on every session stop; 0.55 accuracy means half of doc update opportunities are missed
  - Ease: Read karen prompt → identify calibration gap → test targeted fix

### Candidate 4: Multi-agent BrickLayer (Q5.1 — PROMISING)
- **ROI**: `HIGH impact × HARD implementation` → **Plan target**
- Multi-wave parallel mode execution requires question ID namespacing + synthesis.md coordination protocol. Phase 1 (2 modes, no synthesis race) has zero code changes. Worth a dedicated design session.

### Candidate 5: BrickLayer dashboard (Q5.2 — PROMISING)
- **ROI**: `HIGH impact × HARD implementation` → **Plan target**
- Derivable from existing files, maps to `dashboard/` FastAPI+React. Deferred — not relevant to BL 2.0 spec quality.

---

## Wave 1 Question Targets

| Priority | Candidate | Question ID | Expected verdict |
|----------|-----------|-------------|-----------------|
| 1 | Monitor DEGRADED_TRENDING | E1.1 | IMPROVEMENT |
| 2 | Validate FAILURE routing | E1.2 | IMPROVEMENT |
| 3 | Karen accuracy analysis | E1.3 | IMPROVEMENT or WARNING |

---

## Skipped Candidates (this wave)

- Multi-agent BL (Q5.1): Plan target — deferred
- Dashboard (Q5.2): Plan target — deferred
- Legal project (Q3.4 INCONCLUSIVE): Human action required (create `legal/project-brief.md`)

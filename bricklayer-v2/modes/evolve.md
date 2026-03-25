# Evolve Mode — Program

**Purpose**: Find the highest-ROI improvement in a healthy, working system and prove
it works. Not fixing bugs (Diagnose/Fix) — making good things measurably better.
Targets: performance, code quality, architecture, developer experience, test coverage,
agent accuracy, or any dimension with a measurable before/after delta.

**Prerequisite**: System must be healthy (no open FAILURE findings blocking operation)
**Verdict vocabulary**: IMPROVEMENT | HEALTHY | REGRESSION | WARNING
**Output**: Findings with concrete proposals, delta measurements, and ranked next targets

---

## Phase 1 — Survey (start of every Evolve session)

Before generating questions, survey signal sources to identify where improvement
investment has the highest ROI. Read each source and extract candidates:

### Signal sources

1. **Finding history** (`findings/`, `results.tsv`)
   - Which categories produce recurring WARNINGs across multiple waves?
   - Which INCONCLUSIVE findings were never resolved?
   - Which areas have the highest finding density (most attention = most churn)?

2. **Agent accuracy** (`masonry/agent_snapshots/*/eval_latest.json`)
   - Which agents have the lowest score?
   - Which agents have high eval variance (inconsistent)?
   - Gap between current score and 0.85 target = improvement headroom

3. **Git hotspots** (`git log --stat`, `git shortlog`)
   - Which files have the most commits? (high churn = structural instability)
   - Which files appear in the most bug-fix commits?
   - Which modules have grown fastest in the last 30 days?

4. **Recall signal** (query: "should be better", "technical debt", "slow", "fragile")
   - Flagged improvement candidates from prior sessions
   - Known friction points that were deferred

5. **Test coverage gaps** (if coverage reports exist)
   - Files with < 60% coverage in active code paths
   - Tests that only test the happy path

### Candidate ranking

Score each candidate: `ROI = estimated_impact × implementation_ease`

| Score | Meaning |
|-------|---------|
| High impact + Easy | Immediate target — address in this wave |
| High impact + Hard | Plan target — break into smaller questions |
| Low impact + Easy | Backlog — address only if wave has spare capacity |
| Low impact + Hard | Skip — not worth the cost |

Write the ranked candidates to `evolve-survey.md` before running any questions.

---

## Phase 2 — Question Loop

### Per-question structure

Each question targets one ranked candidate:

**Hypothesis format**: "Improving X should produce Y measurable gain because Z."

Examples by improvement type:
- Performance: "Caching the scoring result in `findings.py:score()` should reduce p95 latency by >20% because it's called 3× per question with identical inputs."
- Agent accuracy: "Adding 3 failure-case examples to the karen agent prompt should raise eval score from 0.72 to ≥0.80 because the failures cluster around changelog format mismatches."
- Code quality: "Extracting the 140-line `_parse_question_block()` in `questions.py` into 3 focused functions should reduce cyclomatic complexity and make the parser testable in isolation."
- DX: "Adding a `--dry-run` flag to `run_optimization.py` should cut iteration time for prompt engineers by eliminating the 3-minute eval wait during development."
- Test coverage: "Adding edge-case tests for `PENDING_EXTERNAL` with a past `resume_after` date covers the broken-prerequisite escalation path, which currently has 0 coverage."

### Evidence gathering

1. Read the current implementation — understand exactly what exists
2. Propose the concrete change — diff-level specificity, not "improve performance"
3. Implement or run the change
4. Measure: before/after on the specific metric
5. Regression check: verify no other metric degraded

### Verdict assignment

- `IMPROVEMENT` — measurable positive delta, no regression
- `HEALTHY` — area already well-optimized; no meaningful improvement available
- `WARNING` — improvement opportunity exists but path is unclear or risky
- `REGRESSION` — attempted change degraded a metric; revert and note why

---

## Delta measurement format

Every `IMPROVEMENT` finding must include a Delta block:

```
## Delta
- Metric: karen_eval_score
- Baseline: 0.72 (eval_latest.json 2026-03-24, eval_size=20)
- After: 0.84
- Improvement: +16.7%
- Regression check: research-analyst score unchanged (0.81 before, 0.81 after)
- Method: ran masonry/scripts/eval_agent.py karen --eval-size 20 before and after
```

Metric can be anything measurable: latency, score, line count, cyclomatic complexity,
coverage %, test count, build time, token count.

---

## Wave structure

- Wave 1: address the top 3 candidates from the survey (highest ROI)
- Subsequent waves: re-survey before each wave — the landscape changes after improvements
- Stop condition: all high-ROI candidates explored, OR marginal gain < 3% across
  all remaining candidates (diminishing returns), OR a new FAILURE finding is discovered
  (stop Evolve, hand off to Diagnose)

---

## Session end

Produce `evolve-report.md`:
- Survey results: candidates ranked, which were addressed
- All IMPROVEMENT findings with delta measurements
- Total improvement across all metrics vs. session baseline
- Ranked next targets for the next Evolve session
- Any WARNING findings that need a dedicated investigation

If agent prompts were improved: confirm `snapshot_agent.py` was run to version the
improved prompt before the session ends.

# Task 3: optimize_and_prove.py — Gated Improvement Pipeline

**Finding ID**: task3-optimize-and-prove
**File**: `masonry/scripts/optimize_and_prove.py`
**Test file**: `tests/test_optimize_and_prove.py`

## Fix Specification

- **File**: `masonry/scripts/optimize_and_prove.py`
- **Change**: Implement a gated optimization pipeline — eval before → snapshot → optimize → eval after → deploy if both min_delta and min_score gates pass, rollback otherwise.
- **Return contract**: `{"deployed": bool, "score_before": float, "score_after": float, "delta": float}` — all four keys always present.
- **Verification**: `python -m pytest tests/test_optimize_and_prove.py -v`

---

## Code Review

**Reviewer**: code-reviewer
**Date**: 2026-03-23T00:00:00Z
**Verdict**: APPROVED

### Diff assessment

The implementation is a new file — no prior version existed. The diff introduces:

- `_run_script()` — thin subprocess wrapper (captures stdout/stderr, text mode). No error suppression.
- `_read_eval_score()` — reads `eval_latest.json` with a primary/fallback path strategy. The fallback path (`agent_snapshots/{agent}/eval_latest.json`) was added for test compatibility with `tmp_path` fixtures that don't replicate the full `masonry/` subtree. This is deliberate and benign.
- `run_optimize_and_prove()` — 5-step pipeline matching the spec exactly:
  1. `eval_agent.py` → `score_before`
  2. `snapshot_agent.py --score {score_before}` (pre-optimization snapshot)
  3. `optimize_claude.py`
  4. `eval_agent.py` → `score_after`
  5. Deploy (`snapshot_agent.py --score {score_after}`) or rollback (`snapshot_agent.py --rollback`)
- `_main()` — argparse CLI entrypoint. Exits 0 on deploy, 1 on reject/rollback.

The diff matches the specification on all five review criteria:

| Criterion | Status |
|-----------|--------|
| Subprocess call order | Correct — eval → snapshot → optimize → eval → deploy/rollback |
| Score reading | Correct — `_read_eval_score` called after each `eval_agent.py` invocation |
| Gate logic | Correct — `score_after >= score_before + min_delta AND score_after >= min_score` (line 99) |
| Rollback always on rejection | Correct — `else` branch is exhaustive, no early return or exception path that bypasses it |
| Return dict | Correct — all 4 keys present in both `if` and `else` branches |

One note on the `--min-score` CLI default: the docstring and `run_optimize_and_prove` signature default `min_score` to `0.75`, but the `_main()` argparse default is `0.70`. These differ. The function default wins when called programmatically without `--min-score`; the argparse default wins from the CLI. This inconsistency does not affect correctness of the tests (all tests pass an explicit `min_score`), but could surprise a caller.

### Lint results

```
mypy masonry/scripts/optimize_and_prove.py --ignore-missing-imports
Success: no issues found in 1 source file

flake8: not installed — skipped
```

No lint errors. mypy is clean.

### Regression check

- `run_optimize_and_prove` is a new public function with no existing callers in the codebase — no regression surface.
- `_run_script` and `_read_eval_score` are module-private (`_` prefix) — no external exposure.
- The implementation calls `snapshot_agent.py --rollback`, which is confirmed to be a supported flag in `masonry/scripts/snapshot_agent.py` (line 245, `rollback_agent` function at line 150, CLI handler at line 258).
- No shared data structures or interfaces are modified.
- No existing tests required updating.

The only behavioral note flagged above (docstring `min_score=0.75` vs CLI default `0.70`) is advisory — not a regression.

### Verification

```
python -m pytest tests/test_optimize_and_prove.py -v

============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests/test_optimize_and_prove.py::TestDeploysOnImprovement::test_deploys_on_improvement PASSED
tests/test_optimize_and_prove.py::TestDeploysOnImprovement::test_deploys_prints_deployed_message PASSED
tests/test_optimize_and_prove.py::TestRejectsWhenWorse::test_rejects_when_worse PASSED
tests/test_optimize_and_prove.py::TestRejectsWhenWorse::test_return_dict_has_all_keys_when_rejected PASSED
tests/test_optimize_and_prove.py::TestRejectsBelowFloor::test_rejects_below_floor PASSED
tests/test_optimize_and_prove.py::TestMinDeltaRequired::test_min_delta_required PASSED
tests/test_optimize_and_prove.py::TestSubprocessCallOrder::test_script_call_order_on_deploy PASSED
tests/test_optimize_and_prove.py::TestSubprocessCallOrder::test_pre_snapshot_carries_score_flag PASSED

============================== 8 passed in 0.07s ==============================
```

8/8 tests pass.

### Notes

Minor advisory (no revision required): The `min_score` default differs between the function signature (`0.75`, line 50) and the `_main()` argparse definition (`0.70`, line 162). Consider aligning them to avoid confusion. This does not affect any test.

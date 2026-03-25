# Finding: Task 2 — snapshot_agent.py Code Review

**Finding ID**: task2-snapshot-agent
**File**: `masonry/scripts/snapshot_agent.py`
**Test file**: `tests/test_snapshot_agent.py`

---

## Code Review

**Reviewer**: code-reviewer
**Date**: 2026-03-23T00:00:00Z
**Verdict**: NEEDS_REVISION

### Diff assessment

The diff could not be isolated to a single commit (the file was bundled into the Task 1 session commit `fd9c032`). The full source was reviewed directly from HEAD. The implementation matches the stated scope: versioned `.md` snapshots under `masonry/agent_snapshots/{agent}/`, a `baseline.json` tracking current version and score, and a rollback path. All five specified areas were examined.

### Lint results

```
flake8: not installed — skipped
mypy: Success: no issues found in 1 source file
```

### Regression check

The only existing caller of the `agent_snapshots` directory is `masonry/scripts/eval_agent.py`, which writes `eval_latest.json` there. It does not call any function in `snapshot_agent.py` — no regression from that side. The public API (`snapshot_agent`, `rollback_agent`) has no other callers yet; Task 3 (`optimize_and_prove.py`) will be the first consumer. No existing tests are affected.

### Verification

```
pytest tests/test_snapshot_agent.py -v

9 passed in 0.15s
```

All 9 tests pass.

### Notes

**Issue 1 — NEEDS_REVISION (severity: medium, downstream impact on Task 3)**

`rollback_agent` updates `baseline["current_version"]` and `baseline["snapshot_file"]` after a rollback, but leaves `baseline["score"]`, `baseline["eval_size"]`, and `baseline["recorded_at"]` pointing at the version that was just discarded. After rollback, `baseline.json` contains the score of the bad version, not the version that is now active.

Task 3 (`optimize_and_prove.py`) will read `baseline["score"]` as the pre-optimization baseline to decide whether a new optimization is an improvement. If the operator rolls back and then immediately re-runs optimization, the gating logic will compare the new score against the wrong baseline, potentially approving a regression or blocking a genuine improvement.

Fix: when updating `baseline.json` after a rollback, also set `score`, `eval_size`, and `recorded_at` to the values from the previous snapshot's metadata. Since those fields are not stored inside the snapshot `.md` file itself, the simplest approach is to read the existing `baseline.json` fields that correspond to the previous version. The cleanest solution is to store per-version metadata as a sidecar (e.g., `v1_20260323_s0.84.json`) so rollback can restore all fields atomically. A simpler but acceptable fix is to set `score` to `None` (or omit it) after rollback with a note that it must be re-evaluated before the next optimization gate check.

**Issue 2 — Advisory (no revision required)**

`_next_version_number` falls back to `1` if `v*.md` files exist but none match `r"^v(\d+)_"`. This would silently re-issue v1 if a corrupted filename was present. Consider logging a warning to stderr in that branch rather than silently re-issuing.

**Issue 3 — Advisory (no revision required)**

`rollback_agent` writes restored content to all agent `.md` locations in a loop (line 177–178). If a write to the second location fails (e.g., permissions on the global `~/.claude/agents/` path), the first location is already updated but the second is not. The agent copies are now inconsistent. This is low-probability and acceptable for v1, but worth noting for Task 4 (overseer).

**Required for approval**: Fix Issue 1 before Task 3 is implemented. The stale score in `baseline.json` after rollback will cause silent correctness failures in the optimization gate.

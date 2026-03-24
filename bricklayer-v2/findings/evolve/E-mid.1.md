# Finding: E-mid.1 — improve_agent.py karen: blocked by nested subprocess constraint

**Question**: Run `improve_agent.py karen --loops 2` now that E2.3 confirmed 1.00 eval score on clean data. Verify final score ≥0.85 post-optimization; confirm `masonry/agent_snapshots/karen/history/` contains the run record.
**Agent**: quantitative-analyst
**Verdict**: PENDING_EXTERNAL
**Severity**: Low
**Mode**: evolve
**Target**: `masonry/scripts/improve_agent.py`, `masonry/agent_snapshots/karen/`

## Summary

Cannot run `improve_agent.py karen --loops 2` from within this Claude session — each loop requires ~40 nested `claude -p` subprocess calls (eval-size 20 × 2 evals per loop), totalling ~20 minutes which exceeds the Bash tool timeout. CLAUDE.md explicitly advises: *"Run from Git Bash (not inside an active Claude session — avoids nested subprocess issues)."* Current baseline is confirmed at 1.00 (eval_latest.json). Post-optimization run must be executed manually from Git Bash.

## Evidence

### Current karen baseline

```json
// masonry/agent_snapshots/karen/eval_latest.json
{
  "score": 1.0,
  "eval_size": 20
}
```

Confirmed: karen is at 1.00 on the 20-record held-out eval. This was validated by E2.3.

### Training data

- 379 karen records in `masonry/training_data/scored_all.jsonl` (662 total records)
- Largest training set in the fleet

### Snapshot history

```
masonry/agent_snapshots/karen/
  baseline.json
  eval_latest.json
  v1_20260323_s0.00.json  ← initial (0.00 score)
  v2_20260323_s0.00.json
  v3_20260324_s0.70.json  ← improved to 0.70
  history/                ← run history from improve_agent.py loops
```

Score trajectory: 0.00 → 0.00 → 0.70 → 1.00 (eval_latest). The jump to 1.00 is from the live eval in E2.3.

### Why 1.00 may not reflect static-eval ground truth

`eval_agent_live.py` (used in E2.3) uses a different eval methodology than `improve_agent.py`:
- **live eval**: samples real project questions + real agent output
- **static eval**: runs agent against `scored_all.jsonl` held-out records

If `improve_agent.py karen --dry-run` returns 1.00 on the static dataset, the optimization is not useful (no room for improvement). If it returns a lower score (e.g., 0.70–0.85), then `--loops 2` will try to improve it.

### Estimated timing

| Component | Count | Time per call | Total |
|-----------|-------|--------------|-------|
| Pre-loop eval (eval_size=20) | 20 | ~15s (haiku) | ~5 min |
| optimize_with_claude.py (1x per loop) | 2 | ~30s | ~1 min |
| Post-loop eval (eval_size=20) | 20 | ~15s | ~5 min |
| **Per loop total** | — | — | **~11 min** |
| **2 loops total** | — | — | **~22 min** |

Bash tool max timeout = 600s (10 min). 22 minutes exceeds this by 2×.

## Verdict Threshold

PENDING_EXTERNAL: must run from Git Bash outside this session.

## Run Command

```bash
cd C:/Users/trg16/Dev/Bricklayer2.0

# Quick dry-run first to see current static-eval baseline
python masonry/scripts/improve_agent.py karen --dry-run

# Full 2-loop optimization (only if dry-run shows score <1.00)
python masonry/scripts/improve_agent.py karen --loops 2 --eval-size 20
```

### Expected outcomes

| Dry-run score | Next action |
|--------------|-------------|
| 1.00 | No optimization needed — karen is at static-eval ceiling. Mark E-mid.1 DONE. |
| 0.85–0.99 | Run `--loops 2`. Likely plateau after loop 1 (diminishing returns). |
| <0.85 | Run `--loops 2`. Loop 1 should improve; loop 2 may plateau. |

After running, update `masonry/agent_registry.yml` karen entry with `last_score` from the result.

## Open Follow-up Questions

If dry-run returns 1.00 on static eval: the live-eval / static-eval gap is worth investigating — why does karen score 1.00 on live eval but may score lower on static eval? This could indicate the static eval dataset doesn't represent the full range of karen's actual workload.

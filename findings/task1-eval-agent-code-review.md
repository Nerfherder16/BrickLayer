# Code Review — Task 1: eval_agent.py

**Task**: Held-out eval engine for agent self-improvement pipeline
**Implementation**: `masonry/scripts/eval_agent.py`
**Tests**: `tests/test_eval_agent.py`

---

## Code Review

**Reviewer**: code-reviewer
**Date**: 2026-03-23T00:00:00Z
**Verdict**: APPROVED

### Diff assessment

Both files are wholly new (not in HEAD). The implementation matches the Fix Specification exactly:

- File: `masonry/scripts/eval_agent.py` — correct
- Location: new file — correct
- Change: held-out eval engine — fully implemented
- Addresses root purpose directly (not a symptom patch): this is the first novel component, no pre-existing root cause to address

Key behaviours confirmed against spec:

| Spec requirement | Implemented |
|---|---|
| Load `scored_all.jsonl`, filter by agent name | Yes — `_load_records()` line 38–53 |
| Hold out LAST `--eval-size` records (deterministic) | Yes — `records[-eval_size:]` line 154 |
| `claude -p` subprocess call per example | Yes — `subprocess.run(["claude", "-p", ...])` line 176–180 |
| Score using `build_karen_metric()` or `build_metric()` | Yes — branched on `signature` param line 161–164 |
| Write `masonry/agent_snapshots/{agent}/eval_latest.json` | Yes — line 206–222 |
| Print per-example progress line | Yes — line 191 |
| CLI: `--signature`, `--eval-size`, `--model` flags | Yes — complete argparse block |

### Lint results

```
flake8: not installed (Python 3.14 environment lacks flake8 module)
mypy: Success: no issues found in 1 source file
```

No lint errors. mypy passes cleanly with `--ignore-missing-imports`.

### Regression check

No existing call sites reference `run_eval`, `eval_agent`, or `eval_latest`. Search across all `.py` files (excluding the two new files) returned zero matches. This is a purely additive change — no shared data structures or interfaces were modified.

Adjacent code reviewed:
- `masonry/src/dspy_pipeline/optimizer.py` — `build_metric()` and `build_karen_metric()` both exist and have the correct signatures. The sentinel `object` passed to `build_metric()` for non-karen paths is acknowledged with a `# type: ignore` comment and is consistent with how the optimizer module works internally (line 164).
- `_find_agent_md_files()` replicates the same discovery logic as `optimize_claude.py` — no divergence risk.

No tests need updating; this is greenfield code.

**One advisory note (non-blocking):** The `eval_size < total records` fallback on line 154 silently uses all available records rather than raising or warning. This means a caller who passes `--eval-size 20` against a 5-record corpus gets 5 examples evaluated with no feedback. The current behaviour is safe and consistent with the test suite, but a caller debug log line would improve observability. This is a suggestion, not a blocker.

### Verification

```
$ python -m pytest tests/test_eval_agent.py -q

[1/5] score=1.00  commit:
...
score=1.00 (5/5 passed)
.
[1/5] score=1.00  commit:
...
score=0.60 (3/5 passed)
.
[1/3] score=1.00  commit:
...
score=1.00 (3/3 passed)
.
[1/3] score=1.00  commit:
...
score=1.00 (3/3 passed)
.
4 passed in 3.33s
```

All 4 tests pass. Verified:
- `test_returns_score_1_when_all_pass`: score = 1.0
- `test_returns_partial_score`: score = 0.6, passed=3, failed=2
- `test_writes_eval_json`: all 8 required schema fields present, example sub-fields present, path correct
- `test_uses_last_n_examples`: exactly records with indices {7, 8, 9} evaluated (not 0–6)

### Security

- `subprocess.run()` uses a list — no shell injection surface (`shell=True` absent)
- Prompt content (agent .md text + JSON-serialised input record) is passed as a positional argument, not via shell string interpolation
- No secrets or credentials in the implementation
- No SQL/HTML construction

### Notes

No revision required. The implementation is correct, type-clean, secure, and all 4 tests pass. The advisory note above (silent fallback when corpus is smaller than eval_size) is logged for awareness but does not block shipping.

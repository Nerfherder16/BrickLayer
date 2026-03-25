# Task 4 — Overseer Agent + Trigger Mechanism

**Finding ID**: task4-overseer-trigger
**Agent**: code-reviewer
**Date**: 2026-03-23

---

## Code Review

**Reviewer**: code-reviewer
**Date**: 2026-03-23T00:00:00Z
**Verdict**: NEEDS_REVISION

### Diff assessment

The diff matches the Fix Specification for all four deliverables:

- `~/.claude/agents/overseer.md` — new file, correct location outside the repo (global agents dir). Frontmatter matches the agent pattern used by other trusted-tier agents. Procedure is complete and well-structured.
- `masonry/agent_registry.yml` — overseer entry updated from stale draft metadata (old `.claude/agents/overseer.md`, model opus, meta mode) to the current spec: `~/.claude/agents/overseer.md`, model sonnet, modes `[agent, audit]`, capabilities listed, `tier: trusted`. Missing optional DSPy tracking fields present on other entries (`dspy_status`, `drift_status`, `last_score`, `runs_since_optimization`) but this is consistent with how other recently-added trusted agents (e.g. `uiux-master`, `solana-specialist`) are registered — acceptable.
- `masonry/src/hooks/masonry-observe.js` — `handleObserveWrite` function added at lines 177–199, exported at line 199. Called from `main()` at lines 221–224, inside a try/catch (non-fatal). Logic: detects writes to `agents/**/*.md` or `findings/**`, increments `.invocation_count`, writes `overseer_trigger.flag` at threshold 10, resets counter to 0 immediately after. All correct.
- `masonry/src/hooks/masonry-stop-guard.js` — `checkOverseerTrigger` function added at lines 188–199, exported at line 201. Reads flag, writes notice to stderr (injectable for testing), deletes flag. Called at lines 247 and 293 on the two clean-exit paths.
- `tests/test_overseer_trigger.js` — new file, 4 tests, all passing.

### Lint results

```
No linter configured for this project (no .eslintrc, no package.json eslint config).
Node.js syntax check:
  node --check masonry/src/hooks/masonry-observe.js  → OK
  node --check masonry/src/hooks/masonry-stop-guard.js → OK
  node --check tests/test_overseer_trigger.js → OK
No lint errors found.
```

### Regression check

**Existing hook behavior — masonry-observe.js**: `handleObserveWrite` is called inside a try/catch at line 221–224 before the existing activity-log and findings logic. The non-fatal guard means no regression risk to the finding-detection or Recall-store paths even if the snapshots directory is missing or unwritable.

**Existing hook behavior — masonry-stop-guard.js**: `checkOverseerTrigger` is called only on the two `process.exit(0)` paths (lines 247 and 293) — the clean-exit paths. It is not called before `process.exit(2)` at line 304 (the blocked-stop path). This is a minor behavioral gap noted below, but it does not regress existing behavior — the stop-block output is unchanged.

**Counter reset**: Verified manually. After the 10th invocation the counter resets to `{ count: 0 }` before writing the flag, so subsequent invocations correctly accumulate toward the next trigger without double-firing.

**Registry**: The overseer entry was already present (as a stale draft entry pointing to the wrong file). The diff updates it in place — no duplicate entry was introduced.

**Call sites for `handleObserveWrite`**: The function is only called from `masonry-observe.js` itself. No other files import it, so no external call sites are affected.

**Call sites for `checkOverseerTrigger`**: Same — only internal to `masonry-stop-guard.js`.

### Verification

```
$ node --test tests/test_overseer_trigger.js

  ✔ test_invocation_count_increments — write to agents/karen.md bumps count from 0 to 1 (3.8ms)
  ✔ test_trigger_flag_written_at_threshold — flag file exists after 10th agent .md write (6.1ms)
  ✔ test_stop_guard_clears_flag — flag deleted and [overseer] notice written to stderr (1.6ms)
  ✔ test_stop_guard_no_flag_no_noise — no flag file means no overseer output in stderr (1.1ms)

tests 4 | pass 4 | fail 0
```

All 4 tests pass.

### Notes

**Issue 1 (minor): `checkOverseerTrigger` not called on blocked-stop path**

`checkOverseerTrigger` is called on both `process.exit(0)` paths but not before `process.exit(2)` at line 304. When the stop is blocked due to uncommitted files, the overseer flag accumulates until the user eventually gets a clean stop. In practice this is low-friction (the user must commit and re-stop anyway), but it means the notice is delayed indefinitely if the user frequently stops with dirty state. The flag is not a correctness problem — it is self-healing — but the notice timing is weaker than intended.

Suggested revision: add `checkOverseerTrigger(path.join(cwd, 'masonry', 'agent_snapshots'))` immediately before `process.stderr.write(output)` at line 303, so the overseer notice appears alongside the uncommitted-files warning. This is one line.

**Issue 2 (minor): overseer agent procedure — optimization trigger is one-shot, not idempotent**

Step D in `overseer.md` counts records since `baseline.created_at` and fires `optimize_and_prove.py` if count > 50, then marks status `optimized`. There is no guard against re-triggering on the next overseer run (the baseline `created_at` is not updated after optimization, so count > 50 will always be true until a new snapshot is taken). `optimize_and_prove.py` presumably writes a new snapshot, which resets the anchor — but this dependency is implicit and not stated in the procedure. If `optimize_and_prove.py` fails, the next overseer run will attempt optimization again (Step D fires again), which is the correct behavior for a retry — but the agent marks status `optimization_failed` and does not update the baseline, so subsequent runs will keep retrying. This is acceptable behavior but should be explicitly documented in the Error Handling section.

Neither issue is a blocker. Issue 1 is a one-line fix. Issue 2 is a documentation gap in the agent procedure.

**Revision instructions**: Fix Issue 1 (add `checkOverseerTrigger` before `process.exit(2)` in the blocked-stop branch). Clarify Issue 2 in `overseer.md` Error Handling section with a sentence: "After `optimize_and_prove.py` succeeds it writes a new baseline snapshot, which advances the `created_at` anchor and resets the optimization trigger. If it fails, the next overseer run will retry optimization."

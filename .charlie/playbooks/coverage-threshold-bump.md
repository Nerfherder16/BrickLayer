# Playbook: Coverage Threshold Bump

## Trigger

- **Schedule:** Every Wednesday at 09:00 (cron: `0 9 * * 3`)
- **Agent:** `mutation-tester`
- **Conductor ID:** `coverage-threshold-bump`

## Purpose

Ratchet the coverage requirement upward automatically when the test suite is healthy enough
to support it. Prevents coverage rot without requiring manual maintenance.

## Inputs

- **Test suite:** Full pytest run (`python -m pytest tests/`)
- **Coverage config:** `pytest.ini` or `.coveragerc` (whichever exists)
- **Mutation target:** all Python source files under `masonry/src/`

## Expected Output

The mutation-tester agent reports:

```
mutation_score: 74.3%
lines_tested: 1204
mutants_killed: 895
mutants_survived: 309
```

## Success Criteria

| Condition | Action |
|-----------|--------|
| Mutation score <= 70% | Log current score, no config change, exit |
| Mutation score > 70% | Bump `--cov-fail-under` by 2 percentage points |

## Config Change Procedure

1. Locate the coverage threshold line in `pytest.ini`:
   ```ini
   addopts = --cov=masonry --cov-fail-under=80
   ```
2. Parse the current value (e.g., `80`)
3. Write the bumped value (e.g., `82`) back to the same file
4. Run the full test suite to verify the bump does not cause failures

## Rollback

If the test suite fails after bumping:

1. Revert `pytest.ini` to the pre-bump value immediately
2. Log a warning: `Coverage bump reverted — test suite failed at threshold N`
3. Record the failed mutation score in `.charlie/reports/coverage-bump-YYYY-MM-DD.json`:
   ```json
   {
     "date": "YYYY-MM-DD",
     "mutation_score": 74.3,
     "attempted_threshold": 82,
     "reverted": true,
     "reason": "test suite failed after bump"
   }
   ```
4. Do NOT disable the schedule — retry next Wednesday

## Safety Rules

1. Never bump by more than 2 percentage points per run
2. Never bump above 95% (diminishing returns)
3. Always run the full test suite after bumping, before committing
4. If `pytest.ini` does not contain `--cov-fail-under`, skip the bump and log a notice

## Commit Format

If the bump succeeds and tests pass:

- **Message:** `chore: bump coverage threshold to N% (mutation score M%)`
- **Branch:** commit directly to the current branch (no separate PR needed)

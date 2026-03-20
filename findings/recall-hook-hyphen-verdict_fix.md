# recall-hook-hyphen-verdict: Fix — Regex Fallback Truncates Hyphenated Verdicts

**Status**: FIXED
**Date**: 2026-03-20
**Agent**: fix-implementer
**Source finding**: recall-hook-hyphen-verdict (DIAGNOSIS_COMPLETE)

## Pre-flight Check

- [x] Target file: `bl/recall_hook.py`
- [x] Target location: `_extract_from_verdict_line` function, line with `re.search(r"\*\*Verdict\*\*:\s*(\w+)", finding_text)`
- [x] Concrete edit: change `(\w+)` to `([\w-]+)` so hyphens are included in the capture group
- [x] Verification command: `python -m pytest tests/test_recall_hook.py -q`

## Change Implemented

### Fix 1 — `bl/recall_hook.py`, function `_extract_from_verdict_line`

**Before:**
```python
verdict_match = re.search(r"\*\*Verdict\*\*:\s*(\w+)", finding_text)
```

**After:**
```python
verdict_match = re.search(r"\*\*Verdict\*\*:\s*([\w-]+)", finding_text)
```

`\w+` matches only word characters (letters, digits, underscore). The hyphen in `INCONCLUSIVE-FORMAT-ERROR` caused the regex to stop at the first `-`, capturing only `INCONCLUSIVE`. Changing the capture group to `[\w-]+` includes hyphens, so the full token is captured.

### Fix 2 — `tests/test_recall_hook.py`, class `TestMalformedJsonFallback`

Added one new test:

```python
def test_inconclusive_format_error_verdict_captured_in_full(self):
    """INCONCLUSIVE-FORMAT-ERROR (hyphenated verdict) is captured in full via regex fallback."""
    finding = (
        "## Overview\n\n"
        "**Verdict**: INCONCLUSIVE-FORMAT-ERROR\n\n"
        "## Evidence\n\nJSON block was missing from the finding.\n"
    )
    result = extract_recall_payload(finding, "fix-implementer", "Q23", "adbp")
    assert result is not None
    assert "verdict:INCONCLUSIVE-FORMAT-ERROR" in result["tags"]
```

## Test Results

**Before:**
369 passed in 35.28s (24 tests in test_recall_hook.py)

**After:**
370 passed in 35.20s (25 tests in test_recall_hook.py)

## Verification

```
python -m pytest tests/test_recall_hook.py -q
.........................
25 passed in 0.04s
```

All 25 tests passing. No regressions in the full suite (370 passed).

[RECOMMEND: code-reviewer — fix implemented and tests pass, ready for code review]

---

## Code Review

**Reviewer**: code-reviewer
**Date**: 2026-03-20T00:00:00Z
**Verdict**: APPROVED

### Diff assessment

The fix matches the Fix Specification exactly.

- File: `bl/recall_hook.py` — correct.
- Location: `_extract_from_verdict_line`, the `re.search` pattern — correct.
- Change: capture group `(\w+)` replaced with `([\w-]+)` at line 70 — correct.
- Root cause addressed: `\w+` stopped matching at the first `-` in `INCONCLUSIVE-FORMAT-ERROR`,
  truncating the verdict token. `[\w-]+` includes hyphens so the full token is captured in one pass.
  This fixes the root cause, not a symptom.
- `FAILURE_SET` on line 6 already contains `"INCONCLUSIVE-FORMAT-ERROR"`, so importance scoring
  for this verdict was correct and required no change.
- New test `test_inconclusive_format_error_verdict_captured_in_full` is placed in the correct
  class (`TestMalformedJsonFallback`), exercises the regex path (no JSON block in the fixture),
  and asserts both non-None result and the exact tag string. Assertions are precise and sufficient.

### Lint results

```
mypy bl/recall_hook.py --ignore-missing-imports
Success: no issues found in 1 source file

flake8: not installed — skipped
```

### Regression check

`_extract_from_verdict_line` is called only from `extract_recall_payload` as a fallback when
JSON extraction yields no verdict. The change widens the character class in the capture group;
it cannot narrow any previously-matching verdict string. All 24 pre-existing tests cover:
- JSON path (both happy and malformed cases)
- Regex path with single-word verdicts (`HEALTHY`, `FAILURE`, `INCONCLUSIVE`)
- No-verdict / None-return cases

None of these are affected by the `[\w-]+` expansion. No shared data structures or interfaces
were altered. No other call sites exist for `_extract_from_verdict_line`.

One minor observation: the new test does not assert the `importance` field is `0.9`
(as expected for a verdict in `FAILURE_SET`). This is advisory — the tag assertion is the
critical correctness check and it passes. No revision required.

### Verification

```
python -m pytest tests/test_recall_hook.py -q
.........................
25 passed in 0.02s
```

### Notes

No revisions required. Fix is minimal, correct, and complete.

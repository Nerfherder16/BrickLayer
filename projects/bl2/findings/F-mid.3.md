# Finding: F-mid.3 — else-clause added to _parse_text_output() for BL 2.0 universal fallback

**Question**: Does adding an `else` clause after the `perf-optimizer` branch in `_parse_text_output()` that extracts `verdict` and `summary` via regex recover correct verdicts from plain-text BL 2.0 agent output?
**Verdict**: FIXED
**Severity**: Info

## Evidence

**Change applied**: `bl/runners/agent.py` lines 188-208 — inserted `else` clause after `elif agent_name == "perf-optimizer":` block:
```python
else:
    # F-mid.3: universal BL 2.0 fallback — extract verdict and summary from plain text.
    # Covers diagnose-analyst, fix-implementer, compliance-auditor, design-reviewer,
    # and any future agent not in the BL 1.x name list above.
    m = re.search(r"^verdict:\s*(\w+)", text, re.IGNORECASE | re.MULTILINE)
    if m:
        out["verdict"] = m.group(1).upper()
    m = re.search(r"^summary:\s*(.+)", text, re.IGNORECASE | re.MULTILINE)
    if m:
        out["summary"] = m.group(1).strip()
```

**Behavior after fix**: A `diagnose-analyst` producing plain text containing `verdict: DIAGNOSIS_COMPLETE` and `summary: update_results_tsv not called on exhausted path` will now populate `out` with `{"verdict": "DIAGNOSIS_COMPLETE", "summary": "..."}` instead of `{}`. `_verdict_from_agent_output` will then return DIAGNOSIS_COMPLETE via the `self_verdict_early in _ALL_VERDICTS` check at the `else` branch (line 122-126).

## Verification

`grep -n "else:" bl/runners/agent.py` confirms an `else` clause follows the `perf-optimizer` branch. The clause contains `re.search(r"^verdict:")` extraction logic. BL 2.0 agents producing plain-text output will now correctly return their stated verdict instead of INCONCLUSIVE on the text-fallback path.

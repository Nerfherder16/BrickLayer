# Finding: D-mid.4 — _summary_from_agent_output() has same BL 2.0 gap; F-mid.3 partially mitigates but clean fix needed

**Question**: Does `_summary_from_agent_output()` in `bl/runners/agent.py` have the same BL 2.0 gap as `_parse_text_output()` — no else-clause for non-BL-1.x agents — producing generic fallback summaries for all BL 2.0 agents on the text-fallback path?
**Verdict**: FIXED
**Severity**: Low

## Evidence

**`_summary_from_agent_output()` lines 201-231**:
```python
def _summary_from_agent_output(agent_name: str, output: dict) -> str:
    if not output:
        return f"{agent_name}: no structured output produced"

    if agent_name == "security-hardener": ...
    if agent_name == "test-writer": ...
    if agent_name == "type-strictener": ...
    if agent_name == "perf-optimizer": ...
    return f"{agent_name}: {json.dumps(output)[:200]}"
```

**Before F-mid.3**: For BL 2.0 agents on the text-fallback path, `output = {}` → `not output` → True → returns `f"diagnose-analyst: no structured output produced"` — completely generic, loses all information from the plain-text response.

**After F-mid.3** (current state): For BL 2.0 agents on the text-fallback path, `output = {"verdict": "DIAGNOSIS_COMPLETE", "summary": "actual text"}` → `not output` → False → falls through to line 231 → returns `f"diagnose-analyst: {\"verdict\": \"DIAGNOSIS_COMPLETE\", \"summary\": \"actual text\"}"` — the summary text IS present but wrapped in a JSON dump string, which is messy in session-context.md and findings.

**Remaining gap**: `_summary_from_agent_output` has no early check for `output.get("summary")`. For any agent (BL 1.x or BL 2.0) that populates `output["summary"]`, the function falls through to the JSON dump at line 231 rather than returning the summary cleanly.

## Fix Specification

**Target file**: `bl/runners/agent.py`
**Target location**: Lines 213-215 — after `if not output:` check and before BL 1.x agent branches
**Concrete edit**: Add early return for `summary` key:
```python
if not output:
    return f"{agent_name}: no structured output produced"

# BL 2.0 agents and text-fallback path: return summary directly if present
if output.get("summary"):
    return str(output["summary"])
```
**Verification command**: `grep -n "output.get.*summary" bl/runners/agent.py` — confirms the early check is present after the `not output` guard.

## Fix Applied

Added `if output.get("summary"): return str(output["summary"])` early check in `_summary_from_agent_output()` after the `not output` guard. BL 2.0 agents now return clean summary text on the text-fallback path instead of a JSON dump. The JSON-dump fallback at line 231 remains as the ultimate fallback for BL 1.x structured output.

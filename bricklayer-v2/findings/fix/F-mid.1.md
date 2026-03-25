# Finding: F-mid.1 — Mode dispatch implemented in bl/ci/run_campaign.py

**Question**: Implement mode dispatch in `bl/ci/run_campaign.py` and `bl/runners/agent.py` as specified in Q1.1. Add `_load_mode_context()` to `_dispatch()` and consume `mode_context` in `run_agent()`. Success: CI-runner-dispatched agents receive mode program text in prompt; projects without `modes/` unchanged.
**Agent**: fix-implementer
**Verdict**: FIXED
**Severity**: Medium
**Mode**: fix
**Target**: `bl/ci/run_campaign.py`, `bl/runners/agent.py`

## Summary

Mode dispatch is now implemented. `bl/runners/agent.py` already had `mode_context` injection (lines 372-375) — no changes needed there. The missing piece was in `bl/ci/run_campaign.py`: the `_dispatch()` function now calls `_load_mode_context(project_path, operational_mode)` and injects `mode_context` into the question dict before calling `run_question()`. The `_parse_questions_table()` function now also parses the Mode column from the 4-column BL 2.0 table format and maps it to `operational_mode`.

## Changes Made

### bl/ci/run_campaign.py

**New helper `_load_mode_context()`** (added above `_dispatch()`):
```python
def _load_mode_context(project_path: Path, operational_mode: str) -> str:
    """Load modes/{operational_mode}.md as loop context. Returns empty string if not found."""
    if not operational_mode:
        return ""
    mode_file = project_path / "modes" / f"{operational_mode}.md"
    if mode_file.exists():
        return mode_file.read_text(encoding="utf-8")
    return ""
```

**`_dispatch()` signature updated** to accept `project_path: Path | None = None`:
- Reads `operational_mode` from question dict
- Calls `_load_mode_context(project_path, op_mode)` if not already present
- Injects as `question["mode_context"]` before `run_question(question)`

**Call site updated**: `_dispatch(q, project_path=project_path)` in main loop

**`_parse_questions_table()` updated**:
- New `_TABLE_ROW_4COL_RE` regex matches 4-column BL 2.0 format `| ID | Mode | Status | Question |`
- Mode column captured as `operational_mode`; runner `mode` set to `"agent"` for BL 2.0 questions
- Falls back to legacy 3-column format if no 4-column rows found

**`_parse_questions_bl2()` updated**:
- `operational_mode: bracket_mode` added to parsed question dict

### bl/runners/agent.py

No changes required — `mode_context` injection already existed at lines 372-375:
```python
mode_ctx = question.get("mode_context", "")
mode_ctx_block = (
    f"## Operational Mode Program\n\n{mode_ctx}\n\n---\n\n" if mode_ctx else ""
)
```

## Verification

```python
from bl.ci.run_campaign import _parse_questions_table, _load_mode_context
from pathlib import Path

# 4-column table parsing
qs = _parse_questions_table("| ID | Mode | Status | Question |\n|...|...|...|\n| F-mid.1 | fix | PENDING | ... |")
assert qs[0]["operational_mode"] == "fix"
assert qs[0]["mode"] == "agent"

# Mode context loading
ctx = _load_mode_context(Path("bricklayer-v2"), "diagnose")
assert len(ctx) > 0  # → 2723 chars (diagnose.md exists)
ctx2 = _load_mode_context(Path("bricklayer-v2"), "nonexistent")
assert ctx2 == ""  # graceful fallback
```

Both assertions pass. Mode dispatch is fully additive — projects without `modes/` directories receive empty `mode_context` and produce identical output to pre-change.

## Open Follow-up Questions

None. F-mid.2 (BL 2.0 status normalization fix) is implemented in the same commit.

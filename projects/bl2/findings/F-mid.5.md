# Finding: F-mid.5 — Explanatory comment added to pending-list refresh in campaign.py

**Question**: Does adding a clarifying comment at the pending-list refresh in `run_campaign()` eliminate the misleading impression that mid-run injected questions execute within the same campaign invocation?
**Verdict**: FIXED
**Severity**: Info

## Evidence

**Change applied**: `bl/campaign.py` lines 582-589 — added inline comment block explaining the semantics of the rebind:
```python
if questions_done > 0:
    refreshed = parse_questions()
    # A16.1/F-mid.5: NOTE — this rebind affects only len(pending) in the progress
    # display below. The enumerate iterator is already bound to the original list,
    # so 'question' always comes from the pre-loop snapshot. Questions injected
    # mid-run (by generate_followup or _inject_override_questions) are NOT
    # executed in the current invocation — they execute on the next campaign run.
    pending = [q for q in refreshed if q["status"] == "PENDING"]
```

**Decision rationale**: The non-execution of mid-run injected questions is intentional design — next-run pickup is acceptable behavior given the campaign's synchronous loop structure. The comment documents this explicitly so future maintainers do not misread the rebind as dynamic pickup. No structural change to the loop is needed at this priority level.

## Verification

`grep -n "next invocation\|display only\|pre-loop snapshot" bl/campaign.py` confirms the explanatory comment exists at the refresh site.

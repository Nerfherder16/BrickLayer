# Finding: F-mid.2 — Mode guard added to peer-reviewer spawn in campaign.py

**Question**: Does adding `if question.get("mode") not in ("code_audit",):` guard before the peer-reviewer spawn in `run_campaign()` prevent spurious OVERRIDE verdicts and the .R question injection cascade for code_audit questions?
**Verdict**: FIXED
**Severity**: Info

## Evidence

**Change applied**: `bl/campaign.py` lines 593-604 — wrapped the `_spawn_agent_background("peer-reviewer", ...)` call with:
```python
if question.get("mode") not in ("code_audit",):
    _spawn_agent_background("peer-reviewer", ...)
```

The guard correctly:
- Suppresses peer-reviewer for `code_audit` mode questions (all BL 2.0 diagnose/fix/audit/validate questions whose test fields contain prose read-code instructions)
- Preserves peer-reviewer for `agent` mode questions (BL 1.x behavioral/simulation questions with executable test commands)
- Preserves peer-reviewer for `simulate` and other executable modes

## Verification

`grep -n "peer-reviewer\|code_audit" bl/campaign.py` confirms the spawn is inside `if question.get("mode") not in ("code_audit",)`. No existing `.R` re-exam questions in questions.md (confirmed by D16.2.F1.F1 audit: COMPLIANT).

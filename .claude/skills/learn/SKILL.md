---
name: learn
description: Use when Recall needs to be explicitly taught something — stores a high-importance memory with user intent signal
---

# /learn — Teach Recall Something

When invoked, store a specific fact, preference, or procedure that the system should know and surface automatically going forward.

## Steps

1. **Get the content to store**
   - If the user provided a fact after `/learn`, use it verbatim
   - If just `/learn`, ask: "What should I remember? Be as specific as possible."

2. **Classify it**:
   - Is this a **preference**? (how Tim likes things done)
   - **procedure**? (how to do something specific)
   - **fact**? (a piece of infrastructure/system knowledge)
   - **correction**? (use `/wrong` instead)

3. **Infer domain**: infrastructure, python, recall, preference, homelab, project-specific, etc.

4. **Store in Recall**
   ```bash
   curl -s -X POST http://192.168.50.19:8200/memory/store \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{
       "content": "<the fact/procedure/preference, written clearly as a statement>",
       "domain": "<inferred domain>",
       "tags": ["explicit-teach", "<type: preference|procedure|fact>"],
       "importance": 0.85
     }'
   ```

5. **Confirm**: echo back what was stored + the domain/tags assigned.

## Writing good memory content
- Write as a declarative statement, not a question
- Include enough context to be useful when retrieved cold: who, what, where, why
- Bad: "OPNsense firewall rules" → Good: "OPNsense WireGuard interface uses an explicit allowlist — every port the VPS (10.10.10.1) needs to reach on CasaOS (192.168.50.19) must have its own firewall rule. Port 80 was added 2026-02-25 for casa.streamy.tube."

## Example
User: "/learn the OPNsense WireGuard interface requires explicit per-port firewall rules"
Store with domain=infrastructure, tags=["explicit-teach", "fact"], importance=0.85

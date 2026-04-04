---
name: anchor
description: Use when a fact is ground truth that must ALWAYS surface when relevant — max importance, bypasses normal threshold filtering
---

# /anchor — Store as Ground Truth

For facts that are non-negotiable and must always be surfaced. Higher priority than `/learn`. Use when the failure mode is "Claude didn't know this when it was obvious it should."

## Examples of anchor-worthy facts
- Infrastructure access patterns (OPNsense WireGuard allowlist behavior)
- Architecture decisions that affect every session (deploy script, not scp -r)
- Service locations and auth (Recall API key, VPS IP, SSH users)
- "Always do X before Y" procedures that can't be missed

## Steps

1. **Get the content** — user provides the fact, or infer from current context

2. **Write as a complete, standalone statement** — it must make sense with zero surrounding context

3. **Store with max importance**
   ```bash
   curl -s -X POST http://192.168.50.19:8200/memory/store \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{
       "content": "<complete standalone fact>",
       "domain": "<inferred domain>",
       "tags": ["anchor", "ground-truth", "explicit-teach"],
       "importance": 1.0
     }'
   ```

4. **Also write it to MEMORY.md** if it's infrastructure/workflow-critical — belt and suspenders.
   - Open `C:\Users\trg16\.claude\projects\C--Users-trg16-Dev-System-Recall\memory\MEMORY.md`
   - Add to the relevant PINNED section

5. **Confirm** with: "Anchored — this will always surface when relevant."

## Difference from /learn
- `/learn` → importance 0.85, will surface when similarity is high
- `/anchor` → importance 1.0, surfaces even when similarity is moderate; also written to MEMORY.md

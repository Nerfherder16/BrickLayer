---
name: boost
description: Increase retrieval priority for memories about a topic that are in Recall but not surfacing reliably
---

# /boost — Increase Retrieval Priority

When something IS in Recall but consistently fails to inject into sessions, boost its importance score so it competes better at retrieval time.

## Steps

1. **Get the topic** from user or context

2. **Find matching memories**
   ```bash
   curl -s "http://192.168.50.19:8200/search/browse?query=<topic>&limit=10" \
     -H "X-API-Key: recall-admin-key-change-me"
   ```

3. **Identify candidates** — memories with score ≥ 0.55 that are relevant but have low importance (check `importance` field in response)

4. **Boost via admin rehabilitate** (raises importance for matching IDs):
   ```bash
   # If individual update endpoint available:
   curl -s -X PATCH http://192.168.50.19:8200/memory/<id> \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{"importance": 0.88}'

   # Fallback: re-store the memory with higher importance
   curl -s -X POST http://192.168.50.19:8200/memory/store \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{
       "content": "<original content>",
       "domain": "<same domain>",
       "tags": ["boosted", "<original tags>"],
       "importance": 0.88
     }'
   ```

5. **Report**: how many memories were boosted, new importance scores

## When to use /boost vs /anchor
- `/boost` → memory exists, importance just needs to be higher (0.85–0.90)
- `/anchor` → memory must ALWAYS surface, store fresh with importance=1.0 + write to MEMORY.md

## Diagnostic check first
If a memory has score 0.75+ and still didn't inject, the problem may not be importance — it may be:
- Getting crowded out by the 3-result injection cap → use `/anchor`
- Domain mismatch (hook filters by domain context) → use `/learn` to re-store with correct domain
- Similarity threshold too high (hook min=0.45) → unlikely if score is 0.75+

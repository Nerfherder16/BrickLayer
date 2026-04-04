---
name: show
description: Show what Recall currently knows about a topic — audit memories with scores, domains, and ages
---

# /show — Browse Recall's Knowledge

Displays what Recall knows about a given topic, with similarity scores, domains, and timestamps. Use for auditing, debugging retrieval, or just understanding current system state.

## Steps

1. **Get the topic** from the user or context

2. **Run two searches** — browse (fast) and optionally rehydrate (full content):
   ```bash
   # Standard browse — returns top matches with metadata
   curl -s "http://192.168.50.19:8200/search/browse?query=<topic>&limit=10" \
     -H "X-API-Key: recall-admin-key-change-me"
   ```

3. **Display results in a clear table**:
   ```
   Recall knows about "<topic>" — top 10 results:

   Score  Domain          Age        Content preview
   -----  --------------  ---------  --------------------------------------------------
   0.89   infrastructure  3 days     "OPNsense WireGuard interface uses explicit per-..."
   0.76   homelab         1 week     "VPS nginx routes *.streamy.tube → CasaOS via..."
   0.61   preference      2 weeks    "Always use docker compose not docker-compose..."
   ...
   ```

4. **Summarize**:
   - Total matches found
   - Highest score (if < 0.60: "weak coverage — consider /learn or /anchor")
   - Domains represented
   - Any gaps or inconsistencies noticed

5. **Optional follow-up actions** to suggest:
   - Score < 0.60 overall → suggest `/learn` to fill the gap
   - Score ≥ 0.60 but topic wasn't injected in session → suggest `/boost` or `/anchor`
   - Conflicting content across results → suggest `/wrong` to add a correction

## Quick version
If user just wants a fast check: top 3 results with scores only, no table formatting.

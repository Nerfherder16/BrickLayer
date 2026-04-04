---
name: exists
description: Use when something was overlooked that should have been obvious — diagnoses what Recall knows about a topic and fixes gaps
---

# /exists — "You Should Know This"

Diagnostic command. Searches Recall to show what it currently knows about a topic. If coverage is weak or missing, immediately stores it. Use this when Claude failed to recall something it clearly should have known.

## Steps

1. **Get the topic** — user names what should have been known, or infer from current context

2. **Search Recall for it**
   ```bash
   curl -s "http://192.168.50.19:8200/search/browse?query=<topic>&limit=8" \
     -H "X-API-Key: recall-admin-key-change-me"
   ```

3. **Evaluate coverage**:
   - Score ≥ 0.70 and content is accurate → "Recall knows this. Retrieval failed — may be a threshold or context mismatch."
   - Score 0.50–0.69 → "Weak signal — stored but not surfacing reliably. Use `/boost` to raise importance."
   - Score < 0.50 or no results → "Gap confirmed — not in Recall. Storing now."

4. **Report findings** to the user:
   ```
   Exists check: "<topic>"
   Found N results:
     [0.81] domain=infrastructure — "OPNsense WireGuard..."
     [0.64] domain=homelab — "..."

   Assessment: Weak signal (best score 0.64). Recommend /boost or /anchor.
   ```

5. **If gap confirmed** (score < 0.50 or empty): immediately transition to `/learn` flow — ask for the correct content and store it.

6. **If retrieval failure** (score ≥ 0.70 but wasn't injected): note that the hook threshold (min 0.45) may have been met but the topic lost to result cap (max 3 injected). Suggest `/anchor` to guarantee surfacing.

## This is also a system health check
If `/exists` reveals that important facts ARE in Recall but still didn't inject, that's a tuning issue — note it and consider adjusting the hook's similarity threshold or the memory's importance score.

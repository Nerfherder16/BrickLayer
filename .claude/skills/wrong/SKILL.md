---
name: wrong
description: Use when Claude did something incorrect — stores a correction in Recall with high importance so the mistake isn't repeated
---

# /wrong — Correct a Mistake

When invoked, capture what was wrong and store a correction memory so Recall learns from it.

## Steps

1. **Get the correction**
   - If the user described what was wrong, use that context
   - If they just typed `/wrong`, ask: "What did I do wrong? What's the correct behavior?"

2. **Infer domain** from the topic (infrastructure, python, recall, preference, etc.)

3. **Store the correction in Recall**
   ```bash
   curl -s -X POST http://192.168.50.19:8200/memory/store \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{
       "content": "CORRECTION: [what was wrong]. Correct behavior: [what should happen instead]. Context: [why this matters]",
       "domain": "<inferred domain>",
       "tags": ["correction", "wrong", "anti-pattern"],
       "importance": 0.92
     }'
   ```

4. **Also search** for any existing memories that encode the wrong behavior and note them for potential supersession:
   ```bash
   curl -s "http://192.168.50.19:8200/search/browse?query=<topic>&limit=5" \
     -H "X-API-Key: recall-admin-key-change-me"
   ```

5. **Confirm** by summarizing what was stored and what the correct behavior is going forward.

## Content format
Write the correction memory as: "CORRECTION: [wrong thing]. Correct: [right thing]." Be specific — vague corrections don't retrieve well.

## Example
User: "/wrong — you used `scp -r` to deploy the dashboard"
Store: "CORRECTION: Never use `scp -r` to deploy the Recall dashboard. Vite hashed filenames accumulate and stale assets get served. Correct: always run `bash deploy-dashboard.sh` which cleans remote assets first."

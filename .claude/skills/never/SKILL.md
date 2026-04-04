---
name: never
description: Use to store an absolute prohibition — something Claude must never do, stored as an anti-pattern with maximum inhibition weight
---

# /never — Store an Absolute Prohibition

Stores a standing "never do this" rule as an anti-pattern. Different from `/wrong` (which corrects a past mistake) — `/never` is a forward-looking permanent prohibition that fires whenever the pattern is about to be triggered.

## Steps

1. **Get the prohibition** — user states what must never happen
   - If unclear, ask: "What should never be done? And what should be done instead?"

2. **Write it with three parts**:
   - NEVER: [the forbidden action]
   - BECAUSE: [why it's harmful]
   - INSTEAD: [correct alternative]

3. **Store as anti-pattern**
   ```bash
   curl -s -X POST http://192.168.50.19:8200/memory/store \
     -H "Content-Type: application/json" \
     -H "X-API-Key: recall-admin-key-change-me" \
     -d '{
       "content": "NEVER: <forbidden action>. BECAUSE: <why harmful>. INSTEAD: <correct alternative>",
       "domain": "anti-pattern",
       "tags": ["never", "prohibition", "anti-pattern"],
       "importance": 0.95
     }'
   ```

4. **Confirm** by stating the rule back clearly.

## Examples

User: "/never use docker-compose, always docker compose"
Store: "NEVER: use `docker-compose` (hyphenated). BECAUSE: deprecated, not installed on CasaOS. INSTEAD: always use `docker compose` (space, V2 plugin)."

User: "/never scp -r the dashboard"
Store: "NEVER: deploy the Recall dashboard with `scp -r`. BECAUSE: Vite hashed filenames accumulate and stale assets get served — index.html may not overwrite correctly. INSTEAD: always run `bash deploy-dashboard.sh` which cleans remote assets before copying."

## Difference from /wrong
- `/wrong` → corrects a specific past mistake, importance 0.92
- `/never` → permanent standing rule, domain=anti-pattern, importance 0.95, written to fire before the mistake happens

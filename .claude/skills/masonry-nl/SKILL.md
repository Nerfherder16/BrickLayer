---
name: masonry-nl
description: Convert a plain English description of what just changed into targeted BrickLayer research questions
---

# /masonry-nl — Natural Language Campaign Entry

**Trigger:** User describes what they just changed, added, or fixed in plain English.

## Usage

```
/masonry-nl I just added concurrent Neo4j writes to the session store
/masonry-nl I fixed a race condition in the Redis session cache
/masonry-nl I refactored the FastAPI auth middleware to use JWT
/masonry-nl I migrated the Postgres schema to add a new index on user_id
```

## What happens

1. Calls `bl.nl_entry.parse_intent()` on the description — extracts intent category, technologies, and concerns using regex + word matching (no LLM)
2. Calls `bl.nl_entry.generate_from_description()` — generates 3-5 targeted BL 2.0 questions ranked by specificity (tech+concern questions first, generic fallbacks last)
3. Calls `bl.nl_entry.quick_campaign()` — appends the questions to `questions.md` as a new Wave NL block
4. Prints a preview via `bl.nl_entry.format_preview()` and the command to start the campaign

## Invocation

Run this in the project directory:

```python
from bl.nl_entry import quick_campaign, format_preview

result = quick_campaign(
    "I just added concurrent Neo4j writes to the session store",
    project_dir="."
)
print(format_preview(result["questions"]))
print()
print(result["next_step"])
```

Or directly from the command line (demo mode):

```bash
cd /path/to/project
python -m bl.nl_entry
```

## Output format

```
Generated 4 questions (~12 min):

  [high] NL-a3f2b1  diagnose/D4
  Does the concurrent write to neo4j in session store use explicit transaction
  boundaries? What is the isolation level, and can two writers produce a dirty
  or phantom read?

  [high] NL-b7c3d2  diagnose/D4
  Under 10+ simultaneous writers to neo4j in session store, is there a deadlock
  or write-skew failure mode? What is the retry policy?

  ...

Run /masonry-run to start the campaign.
```

## Question format in questions.md

Each generated question is written as a standard BL 2.0 block with:
- `**Mode**`: diagnose or validate (derived from intent)
- `**Domain**`: D4 (technical) or D2 (security/compliance)
- `**Priority**`: high (tech-specific) or medium (generic fallback)
- `**Source**`: nl_entry
- `**Status**`: PENDING
- `**Hypothesis**`: the full question text
- `**Test**`: read the relevant code and verify
- `**Verdict threshold**`: HEALTHY / FAILURE criteria

## Intent categories detected

| Input signal | Category | Mode |
|---|---|---|
| "just added", "implemented", "created" | new_feature | diagnose |
| "fixed", "patched", "resolved" | bug_fix | validate |
| "optimized", "cache", "latency" | performance | diagnose |
| "auth", "token", "permission", "encrypt" | security | validate |
| "schema", "migration", "index" | data_model | diagnose |
| "api", "webhook", "external" | integration | diagnose |
| "concurrent", "parallel", "async", "lock" | concurrency | diagnose |
| "config", "setting", "flag" | config | validate |
| "refactored", "restructured" | refactor | validate |
| "deployed", "container", "k8s" | deployment | diagnose |

## Technologies with concern templates

neo4j, redis, postgres, solana, fastapi, docker, ollama, websocket, kafka, celery,
elasticsearch, s3, jwt, sqlite, mongodb, qdrant

When a technology is matched, questions probe its specific known failure modes
(e.g., neo4j → transaction isolation, concurrent write, query performance, index).
When no technology is matched, generic templates for the intent category are used.

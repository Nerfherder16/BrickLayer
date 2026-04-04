# Phase 2B — Swarm Compaction Survival + Confidence-Scored Pattern Storage

## Tasks

- [ ] **Task 1** — Swarm compaction survival: update masonry-pre-compact.js to write in-flight task IDs to .autopilot/inflight-agents.json, update masonry-session-start.js to re-inject them as a systemMessage on resume

- [ ] **Task 2** — Add confidence float field to PatternRecord in masonry/src/schemas/payloads.py (default 0.7, range 0.0-1.0, include Bayesian update formulas in docstring)

- [ ] **Task 3** — Extend masonry/src/hooks/masonry-post-task.js with Bayesian confidence updates: on task success confidence += 0.20*(1-c), on failure confidence -= 0.15*c, read/write confidence from .autopilot/pattern-confidence.json keyed by pattern_id

- [ ] **Task 4** — Add masonry_pattern_decay tool to masonry/bin/masonry-mcp.js: reads .autopilot/pattern-confidence.json, applies time decay (-0.005 per hour since last_used), prunes entries below 0.2 threshold, returns pruned count and surviving patterns

- [ ] **Task 5** — Extend masonry/src/hooks/masonry-training-export.js to include confidence scores in the Recall export payload on Stop: read .autopilot/pattern-confidence.json, attach confidence deltas to each exported pattern record

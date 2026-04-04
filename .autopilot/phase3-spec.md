# Phase 3 — Long-Term Architectural Changes

## Wave 1 — Pure Python + Agent Files (parallel, no masonry-mcp.js)

- [ ] **Task 1** — Training pipeline core: create masonry/src/training/__init__.py (empty), masonry/src/training/collector.py (reads telemetry.jsonl, groups by task_type, computes EMA success rate per strategy using alpha=0.3, cold-start at 0.688), masonry/src/training/selector.py (given task_type returns optimal strategy from EMA history, falls back to balanced). Also extend masonry/src/hooks/masonry-pre-task.js to auto-call selector.py and write recommended strategy to .autopilot/strategy if not already set manually.

- [ ] **Task 2** — ReasoningBank core Python module: create masonry/src/reasoning/__init__.py (empty), masonry/src/reasoning/bank.py (SQLite metadata + hnswlib vectors for 2-3ms local retrieval). Bank stores pattern_id, content, domain, confidence, embedding. Exposes store(pattern) and query(text, top_k=5) methods. Uses sqlite3 (stdlib) + hnswlib-python. Falls back gracefully if hnswlib not installed (SQLite-only mode with text search). Include a requirements note at the top of the file.

- [ ] **Task 3** — Knowledge graph + PageRank: create masonry/src/reasoning/graph.py (Neo4j CITES edges — when task T succeeds using patterns A B C, create weighted edges between all three; project-scoped so patterns from one project don't bleed into another), masonry/src/reasoning/pagerank.py (run PageRank on graph, update confidence scores in pattern-confidence.json; connection details from env RECALL_HOST or fallback to http://100.70.195.84:8200). Both modules use the neo4j Python driver. Include graceful fallback if Neo4j unreachable.

- [ ] **Task 4** — Adaptive coordinator agent update: read C:/Users/trg16/.claude/agents/adaptive-coordinator.md, add a section explaining how to consume the topology recommendation from masonry_swarm_init output. Rules: all tasks independent = hierarchical (current default), tasks with shared code review = mesh, linear chain (N feeds N+1) = ring, mixed = hybrid. The agent should check for a topology field in the swarm_init result and route accordingly.

## Wave 2 — MCP Server + Session Start (sequential, single agent)

- [ ] **Task 5** — Add all Phase 3 MCP tools to masonry/bin/masonry-mcp.js and extend masonry/src/hooks/masonry-session-start.js:
  (a) masonry_training_update tool: triggers EMA recompute by calling collector.py via child_process, returns updated strategy recommendations per task_type
  (b) masonry_reasoning_query tool: queries ReasoningBank (bank.py) for top-5 patterns matching a query string, returns pattern list with confidence scores
  (c) masonry_reasoning_store tool: stores a new pattern in ReasoningBank with content, domain, and initial confidence 0.7
  (d) Extend masonry_swarm_init to analyze task dependency graph and append a topology field (hierarchical/mesh/ring/hybrid) to the return value based on task depends_on fields
  (e) Extend masonry-session-start.js to query ReasoningBank synchronously at session start and inject top-5 relevant patterns into the hookSpecificOutput content (query derived from current autopilot mode + project name)

# Masonry Wiring Fixes — Wave 1

All 5 tasks are independent and can run in parallel.

## Task 1 — Enable training export by default
File: `masonry/src/hooks/masonry-training-export.js`
Find where `BRICKLAYER_TRAINING_DB` env var is checked. Change the default from "disabled if not set" to `~/.mas/training.db`. Training data must flow automatically without requiring an env var. Verify the file write logic still works correctly with the default path.

## Task 2 — Wire ReasoningBank to post-task hook
File: `masonry/src/hooks/masonry-post-task.js`
After a successful task completion, call `masonry_graph_record` MCP tool (or call `masonry/src/reasoning/graph.py` CLI directly via child_process) with the task_id and any pattern_ids from the task context. Use fire-and-forget (child_process.spawn().unref()) — must not block the hook. Read graph.py to understand the CLI interface first.

## Task 3 — Wire DSPy optimization trigger
File: `masonry/src/hooks/masonry-score-trigger.js`  
After scoring completes, fire-and-forget spawn of `python masonry/scripts/run_optimization.py` only when: (a) score file count reaches a threshold (e.g., every 50 new examples) or (b) a `TRIGGER_DSPY` flag file exists in `.autopilot/`. Read the existing score-trigger hook to understand its current structure. Add threshold tracking to `.mas/dspy-trigger-count.json`.

## Task 4 — Confidence feedback to selector (70/30 blend)
File: `masonry/src/training/selector.py`
Currently reads only `ema_history.json`. Extend to also read `pattern-confidence.json` (keyed by pattern_id, value is confidence float 0-1). Blend: `final_score = 0.7 * ema_score + 0.3 * avg_confidence_for_strategy`. If `pattern-confidence.json` doesn't exist, fall back to EMA-only (no behavior change). Add a `--debug` flag that prints the blend calculation.

## Task 5 — PageRank trigger at Stop event
File: `C:/Users/trg16/.claude/settings.json` + new script
Add a Stop hook that fires `python masonry/src/reasoning/pagerank.py` via a lightweight wrapper script `masonry/src/hooks/masonry-pagerank-trigger.js`. The wrapper: reads `.mas/pagerank-last-run.json`, only triggers pagerank.py if >60 minutes since last run (avoid running every stop). Updates the timestamp on run. Fire-and-forget — must not block stop.

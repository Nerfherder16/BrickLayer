# Masonry Platform Gap Analysis

Date: 2026-03-28
Audit Status: COMPLETE

## EXECUTIVE SUMMARY

The Masonry platform has strong core infrastructure with 29 MCP tools, 36 hooks, and 81 agents, but suffers from critical DISCONNECTS between implemented features and their integration points.

## KEY FINDINGS

1. ReasoningBank (bank.py, graph.py, pagerank.py) - FULLY IMPLEMENTED but ORPHANED
   - No hook calls masonry_graph_record
   - No hook calls masonry_pagerank_run
   - Only accessible via MCP tools
   
2. DSPy Optimization - FULLY IMPLEMENTED but DISCONNECTED
   - run_optimization.py ready to execute
   - masonry-score-trigger.js never triggers it
   - No automatic DSPy feedback loop
   
3. Training Export - IMPLEMENTED but DISABLED BY DEFAULT
   - masonry-training-export.js only runs if BRICKLAYER_TRAINING_DB env var set
   - Default: NOT SET - no training data exported
   
4. Confidence Feedback - IMPLEMENTED but UNUSED
   - masonry-post-task.js updates pattern-confidence.json
   - Selector reads only EMA, not confidence
   - Confidence updates dead code

5. 39 Draft-Tier Agents - NO TRAINING DATA
   - No mechanism to collect training traces
   - No graduation path to candidate/trusted
   - Training export disabled by default

## RANKED FIXES

### CRITICAL (Week 1)

Fix #1: Connect ReasoningBank to post-task.js (15 min)
- File: masonry/src/hooks/masonry-post-task.js
- Add: masonry_graph_record call after success
- Impact: Enables pattern co-citation tracking

Fix #2: Wire DSPy trigger in score-trigger.js (20 min)
- File: masonry/src/hooks/masonry-score-trigger.js
- Add: Spawn run_optimization.py after scoring
- Impact: Closes EMA -> DSPy -> prompts loop

Fix #3: Enable training export by default (5 min)
- File: masonry/src/hooks/masonry-training-export.js
- Default: BRICKLAYER_TRAINING_DB = ~/.mas/training.db
- Impact: Training data flows automatically

### IMPORTANT (Week 2)

Fix #4: Confidence feedback to selector (30 min)
- File: masonry/src/training/selector.py
- Read: ema_history.json + pattern-confidence.json
- Blend: 70% EMA + 30% confidence
- Impact: Confidence updates influence strategy

Fix #5: Real embeddings for ReasoningBank (20 min)
- File: masonry/src/reasoning/bank.py line 172
- Replace: SHA512 stub with sentence-transformers
- Impact: Semantic vector search works

Fix #6: PageRank trigger in Stop event (10 min)
- File: .claude/settings.json
- Add: Hook to call masonry_pagerank_run
- Impact: Pattern ranking updates monthly

### STRATEGIC (Week 3)

Fix #7: Agent tier upgrades (1 hour)
- Track: Training samples per agent
- Promote: draft -> candidate (20 samples)
- Impact: Draft agents graduate to production

## FILE LOCATIONS

Core Training:
- masonry/src/training/collector.py
- masonry/src/training/selector.py
- masonry/src/hooks/masonry-pre-task.js
- masonry/src/hooks/masonry-post-task.js

Orphaned ReasoningBank:
- masonry/src/reasoning/bank.py (264 LOC)
- masonry/src/reasoning/graph.py (166 LOC)
- masonry/src/reasoning/pagerank.py (212 LOC)

Orphaned DSPy:
- masonry/src/dspy_pipeline/optimizer.py
- masonry/scripts/run_optimization.py

Configuration:
- .claude/settings.json (Stop event hooks, line 288-356)
- masonry/agent_registry.yml (81 agents, 39 draft)

## SUCCESS CRITERIA

Week 1: Confidence updates influence strategy selection
Week 2: DSPy optimization runs, prompts updated monthly
Week 3: Draft agents have training data, auto-promote

## STATUS: Ready for Implementation

# Agent Fleet Audit Report -- BrickLayer v2

**Date**: 2026-03-24
**Auditor**: agent-auditor
**Inputs**: agents_dir=.claude/agents/ (10 agents), findings_dir=findings/ (56 results), results_tsv=results.tsv (56 rows)

---

## Executive Summary

The BrickLayer v2 agent fleet is structurally sound across 10 agents. All agents have complete frontmatter, clear output contracts, and Recall integration. Three issues require attention: (1) no frontier-analyst agent exists for FR-prefix questions, blocking Frontier mode; (2) the research-analyst has a structural ceiling on tool-free eval, requiring live eval for >=0.85 accuracy; (3) 9 agents have training data but no last_score baseline in the registry and run in production unmeasured.

**Overall fleet verdict: WARNING**
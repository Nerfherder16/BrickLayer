# BrickLayer Agent Schema

Every agent in this directory is a self-contained specialist. Agents are prompt files with
structured frontmatter. Forge creates them. Crucible improves them. BrickLayer runs them.

---

## File Format

```
agents/
  {name}.md          — agent definition
  {name}.score.json  — benchmark scores across versions (Crucible writes this)
```

## Frontmatter Fields

```yaml
---
name: test-writer
version: 1.0.0
created_by: forge | human
last_improved: 2026-03-12
benchmark_score: 0.82
trigger:
  - "correctness test coverage < 70%"
  - "tests marked slow never run"
inputs:
  - finding_md: path to BrickLayer finding file
  - source_dir: path to source code directory
  - test_dir: path to test directory
outputs:
  - new test files written
  - pytest run result
  - coverage delta
metric: coverage_delta    # what Crucible uses to score this agent
mode: subprocess          # which BrickLayer runner validates the output
---
```

## Agent Body

The body is the system prompt given to the agent when it runs. It should include:

1. **Role**: what this agent is and what it optimizes for
2. **Inputs**: what it receives (findings, source files, targets)
3. **Process**: the exact steps it follows (the loop)
4. **Output contract**: what it must produce (structured, verifiable)
5. **Commit/revert rule**: when to keep vs discard the change

## Scoring

Crucible scores agents on three axes:
- **Precision**: does the agent's output actually improve the metric?
- **Safety**: does the agent's output break anything that was passing?
- **Efficiency**: how many iterations does the agent need to find an improvement?

Score = (precision * 0.5) + (safety * 0.3) + (efficiency * 0.2)
Range: 0.0 (useless) → 1.0 (perfect)

Agents with score < 0.4 are flagged for Crucible review.
Agents with score > 0.8 are promoted to the "trusted" tier and run without human approval.

## Tiers

| Tier | Score | Behavior |
|------|-------|----------|
| `draft` | < 0.4 | Created by Forge, not yet benchmarked |
| `candidate` | 0.4–0.8 | Benchmarked, requires human approval before commits |
| `trusted` | > 0.8 | Runs autonomously, commits without approval |
| `retired` | any | Superseded by a better version |

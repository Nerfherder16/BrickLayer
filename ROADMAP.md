# BrickLayer Roadmap

BrickLayer is an autonomous failure boundary research framework. It runs structured question campaigns against a live system, collects evidence, and identifies bugs — shifting the human role from writing tests to defining what matters.

The name comes from the idea: lay enough bricks (questions) and the wall (system behavior) reveals its cracks.

---

## Current State (v0.1 — March 2026)

Three modes against a live API target:

- **Performance**: httpx async load tests, latency percentiles, error rates
- **Correctness**: pytest subprocess runner, verdict from pass/fail counts
- **Quality**: source file reader feeding agent analysis for code patterns

Deliverables: `results.tsv` + per-question `findings/Qx.x.md` + `questions.md` campaign definition.

First campaign against Recall found:
- 2 critical bugs (reranker feature mismatch, embed_batch silent failure)
- 2 design gaps (slow-marked tests never running = invisible coverage)
- 1 false alarm understood (consolidation 429s = working rate limiter)
- 27 UTF-8 corrupted source files (fixed)

---

## Phase 1 — Foundation (Near-term)

### 1.1 Goal-Directed Campaigns
Replace static `questions.md` with a `goal.md`:
```
goal: find the reliability ceiling of the retrieval pipeline under load
constraints: no destructive writes, max 10 min runtime
```
BrickLayer generates its own question set from the goal, runs them, and reports findings. Human defines *what matters*, agent decides *what to ask*.

### 1.2 Adaptive Follow-up
When a question returns FAILURE or WARNING, BrickLayer auto-generates follow-up questions to drill down:
- Q2.4 FAILURE → "what is the exact Redis key format for stored weights?" → "can we patch the weight vector without retraining?"
- Q1.5 FAILURE (429) → "is the rate limit per-IP or global?" → "what's the burst window?"

Follow-ups run in the same session and appear as `Q2.4.1`, `Q2.4.2` in results.

### 1.3 Verdict History + Regression Detection
Store results across runs in a SQLite ledger. On each new run, flag any question that **regressed** (was HEALTHY, now FAILURE). This turns BrickLayer into a regression detector, not just a one-shot audit.

```
Q2.4  HEALTHY → FAILURE  [regression detected, 2026-03-15]
Q1.1  HEALTHY → HEALTHY  [stable]
```

### 1.4 Fix Loop Integration
After FAILURE verdicts, optionally spawn a fix agent. If fixes are applied, re-run the failing question to confirm resolution. Close the loop autonomously.

---

## Phase 2 — Depth (Medium-term)

### 2.1 Overnight Experimentation Mode
Set a program goal, let BrickLayer run a full campaign with parameterized variations, sleep, wake up to a ranked findings report:
```
program: maximize Recall search recall@10 while keeping p99 < 200ms
budget: 500 questions, 8 hours
```
BrickLayer varies consolidation thresholds, RRF k values, embedding cache TTLs, reranker blend weights — measures the effect — reports the Pareto frontier.

This is the "seed hacking" use case from the ML research framework pattern: hundreds of cheap experiments to find the configuration the human wouldn't have guessed.

### 2.2 Multi-Agent Swarm
Fan out parallel research directions:
- Agent A: finds performance boundaries (pushes load)
- Agent B: finds correctness boundaries (mutates inputs)
- Agent C: finds security boundaries (fuzzes payloads)
- Agent D: finds code quality issues (static analysis)

Each agent is autonomous. A synthesizer agent reads all four reports and produces a unified risk map.

### 2.3 Cross-Service Campaigns
Run questions across multiple services simultaneously. For ADBP: ask correctness questions about the Solana redemption program while asking performance questions about the platform API. Find the seam where they interact and probe it.

### 2.4 Baseline Anchoring
Lock a known-good baseline snapshot (response distributions, test pass rates, code metrics). Every future run diffs against the baseline. This makes BrickLayer useful as a pre-deploy gate:
```
run bricklayer --baseline v1.2.0 --target HEAD
→ 3 regressions found, 0 new HEALTHY, deploy blocked
```

---

## Phase 3 — Autonomy (Longer-term)

### 3.1 Self-Improving Question Banks
BrickLayer tracks which questions have found bugs historically. Questions with a high bug-hit rate get upweighted in future campaigns. Questions that never find anything get pruned or replaced. The question bank evolves toward maximum signal density.

### 3.2 Hypothesis Generation from Code Diffs
On each git commit, BrickLayer reads the diff and generates targeted questions:
```
diff: added session_arc_span to extract_features()
→ auto-generated: "Does the reranker weight vector match the new feature count?"
→ runs immediately → found mismatch → filed before it hit production
```

### 3.3 Cross-Project Knowledge Transfer
Findings from Recall campaigns inform question banks for other projects. A bug pattern found in Recall (silent exception swallow on embedding path) becomes a template question applied to every new project automatically.

### 3.4 Natural Language Interface
```
you: "I just added a new endpoint that does concurrent Neo4j writes"
bricklayer: "Running 4 questions: race conditions, N+1 patterns, error propagation, load ceiling"
→ returns findings in 3 minutes
```

---

## Design Principles

1. **Questions are the product.** The question bank is more valuable than any single run's output. Invest in question quality.

2. **Verdicts must be falsifiable.** Every HEALTHY verdict needs specific evidence. Every FAILURE needs a reproduction path. No handwavy summaries.

3. **Humans set goals, agents set questions.** The human knows what matters. The agent knows what to ask. Don't conflate them.

4. **Cheap questions at scale beat expensive questions occasionally.** 500 fast questions overnight beats 5 thorough questions once a quarter.

5. **The framework eats its own dog food.** BrickLayer should eventually run BrickLayer campaigns against itself.

---

## Current Integrations

- **Recall**: live API load testing + pytest runner + source analysis
- **MCP tools**: `mcp__exa__*` for research, `mcp__firecrawl__*` for documentation crawling
- **Recall memory**: session findings stored via `recall_store` for cross-session learning

## Planned Integrations

- **GitHub Actions**: run campaign on every PR, post findings as review comments
- **Solana programs**: static analysis questions against Anchor program IDL + source
- **Kotlin services**: correctness questions against Ktor route handlers

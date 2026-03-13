# BrickLayer Roadmap

BrickLayer is a **universal autonomous research framework**. It runs structured question campaigns against any target — live APIs, codebases, documents, ML models, business processes, smart contracts — collects evidence, and identifies failure boundaries.

The human defines what matters. The agent asks the questions, runs the experiments, and reports what it found.

The name comes from the idea: lay enough bricks and the wall reveals its cracks.

---

## Core Architecture (Target-Agnostic)

BrickLayer has three universal layers:

### 1. Campaign Layer
A `questions.md` (static) or `goal.md` (dynamic) defines what to investigate. Questions have:
- `id` — Q1.1, Q2.3, etc.
- `mode` — which runner handles it
- `target` — what to probe
- `verdict_threshold` — what counts as FAILURE vs WARNING vs HEALTHY

### 2. Runner Layer
Runners are target-specific executors. Any runner that returns a structured verdict can plug in:

| Runner | Target types |
|--------|-------------|
| `http` | REST APIs, GraphQL, WebSockets — latency, error rates, concurrent load |
| `subprocess` | pytest, cargo test, go test, jest, any test suite |
| `static` | Source files fed to agent analysis — code patterns, security, architecture |
| `benchmark` | ML model inference — accuracy, latency, throughput, ablation |
| `document` | Docs, specs, READMEs — completeness, accuracy, consistency |
| `simulation` | Business models, financial projections, game theory — stress variants |
| `contract` | Solana programs, EVM contracts — invariant checking, fuzzing |
| `browser` | Web UIs — Playwright-driven interaction testing |
| `llm-judge` | Arbitrary text/output quality — LLM-as-evaluator with rubric |

### 3. Verdict Layer
Every runner emits the same verdict envelope:
```json
{
  "question_id": "Q2.4",
  "verdict": "FAILURE | WARNING | HEALTHY | INCONCLUSIVE",
  "summary": "one-line evidence",
  "data": {},
  "details": "full evidence text"
}
```
`results.tsv` is always the same shape regardless of what was tested.

---

## Current State (v0.1 — March 2026)

Three runners implemented (`http`, `subprocess`, `static`) against a live FastAPI target (Recall).

First campaign found:
- 2 bugs fixed (reranker feature mismatch, embed_batch silent failure)
- 2 coverage gaps (correctness tests marked slow, never run in CI)
- 27 UTF-8 corrupted source files found and fixed
- 1 false alarm correctly identified (consolidation 429s = working rate limiter)

---

## Phase 1 — Universal Foundation (Near-term)

### 1.1 Runner Registry
Formalize the runner plugin interface so any runner can be added without touching core:
```python
class Runner(Protocol):
    mode: str
    def run(self, question: Question) -> Verdict: ...
```
Register runners by name. Campaign YAML references them by `mode:`. Drop a new `runners/browser.py` and it's available.

### 1.2 Goal-Directed Campaigns
Replace static `questions.md` with a `goal.md`:
```
target: FastAPI memory API at http://192.168.50.19:8200
goal: find the reliability ceiling under concurrent load
constraints: no destructive writes, max 10 min runtime
```
BrickLayer generates the question set from the goal using an agent, runs it, reports findings.
**Works for any target type** — same interface whether it's an API, a codebase, or a document set.

### 1.3 Adaptive Follow-up
When a question returns FAILURE or WARNING, BrickLayer auto-generates drill-down questions:
```
Q2.4 FAILURE → "Is the mismatch in Redis key format or feature extractor version?"
             → "Can the weight vector be padded without retraining?"
```
Follow-ups are numbered `Q2.4.1`, `Q2.4.2` and appear in the same results file.

### 1.4 Verdict History + Regression Detection
SQLite ledger across runs. Flag any question that regressed:
```
Q2.4  HEALTHY → FAILURE  [regression, 2026-03-15, commit abc123]
Q1.1  HEALTHY → HEALTHY  [stable, 14 runs]
```
Turns BrickLayer from one-shot audit into a living regression detector.

### 1.5 Fix Loop Integration
FAILURE verdict → spawn fix agent → re-run question → confirm HEALTHY. Close the loop without human intervention on clear-cut bugs.

---

## Phase 2 — Target Breadth (Medium-term)

This is where BrickLayer becomes truly universal. Each item adds a new class of targets.

### 2.1 ML Model Runner
Run ablation studies, benchmark comparisons, and hyperparameter sweeps against any model:
```yaml
mode: benchmark
target: ollama/qwen3:14b
question: Does increasing context window from 4k to 8k degrade MMLU accuracy?
metric: accuracy@MMLU, latency_p99
```
Overnight experimentation: set a goal (maximize recall@10 with p99 < 200ms), let BrickLayer sweep consolidation thresholds, RRF k values, embedding cache TTLs, report the Pareto frontier.

### 2.2 Document Runner
Probe documentation, specifications, READMEs, legal docs for:
- **Completeness**: are all API endpoints documented?
- **Accuracy**: does the doc match the code?
- **Consistency**: do two docs contradict each other?
- **Coverage gaps**: which edge cases aren't described?

```yaml
mode: document
target: docs/api/*.md + src/api/routes/*.py
question: Are all FastAPI route parameters documented in the corresponding .md file?
```

### 2.3 Smart Contract Runner
For Solana programs (Anchor) and EVM contracts:
- Invariant checking: does NonTransferable actually block transfers under all input combinations?
- Arithmetic edge cases: overflow at max spend cap values?
- Authority bypass: can a non-authorized caller reach privileged instructions?

```yaml
mode: contract
target: programs/benefit-credits/src/lib.rs
question: Can the spend cap be bypassed by splitting transactions below the per-tx limit?
```

### 2.4 Browser / UI Runner
Playwright-driven interaction testing against web UIs:
```yaml
mode: browser
target: http://localhost:5173
question: Does the employer dashboard correctly reflect a $0 balance after credit exhaustion?
```

### 2.5 Multi-Agent Swarm
Fan out parallel research directions simultaneously:
- Agent A: performance boundaries (pushes load)
- Agent B: correctness boundaries (mutates inputs, edge cases)
- Agent C: security boundaries (fuzzes payloads, injection)
- Agent D: code quality (static analysis, architecture)

Each agent is autonomous. A synthesizer reads all four reports and produces a unified risk map ranked by severity.

### 2.6 Baseline Anchoring + Deploy Gates
Lock a known-good snapshot. Every future run diffs against it:
```
bricklayer --baseline v1.2.0 --target HEAD
→ 3 regressions, deploy blocked
→ bricklayer --baseline v1.2.0 --target HEAD --fix
→ fixes applied, all HEALTHY, deploy unblocked
```

---

## Phase 3 — Autonomy (Longer-term)

### 3.1 Self-Improving Question Banks
Track which questions have found bugs historically. High bug-hit-rate questions get upweighted. Questions that never find anything get pruned or replaced. The bank evolves toward maximum signal density.

### 3.2 Hypothesis Generation from Diffs
On each git commit, read the diff and generate targeted questions:
```
diff: added session_arc_span to extract_features()
→ auto-generated: "Does the reranker weight vector match the new feature count?"
→ runs immediately → finds mismatch → filed before it reaches production
```

### 3.3 Cross-Project Knowledge Transfer
Bug patterns found in one project become template questions applied to all new projects:
```
Pattern discovered in Recall: "silent exception swallow on embedding path"
→ auto-applied to FamilyHub: "Does TTS synthesis swallow failures silently?"
→ auto-applied to ADBP platform: "Does KYC check swallow HTTP errors silently?"
```

### 3.4 Natural Language Entry Point
```
you: "I just added concurrent Neo4j writes to the store endpoint"
bricklayer: "Running 4 questions: race conditions, N+1 patterns, error propagation, load ceiling"
→ returns findings in 3 minutes, no questions.md required
```

### 3.5 BrickLayer audits BrickLayer
The framework runs campaigns against itself: correctness of verdict logic, performance of the runner dispatcher, quality of the question generation agent. Eats its own dog food.

---

## Design Principles

1. **Universal verdict envelope.** Every runner, every target, every question type produces the same `{verdict, summary, data, details}` shape. Dashboards, history, and regression detection work the same for all targets.

2. **Questions are the product.** The question bank has compounding value. A good question asked 100 times across 100 projects is worth more than 100 one-off tests.

3. **Humans set goals, agents set questions.** The human knows what matters to the business. The agent knows what to ask technically. Don't conflate them.

4. **Verdicts must be falsifiable.** HEALTHY requires specific evidence. FAILURE requires a reproduction path. INCONCLUSIVE means "agent saw the file but couldn't decide" — not a verdict, a request for more depth.

5. **Cheap at scale beats thorough occasionally.** 500 fast questions overnight finds more than 5 exhaustive questions quarterly.

6. **Failure boundaries, not pass/fail.** The goal isn't "does it work?" — it's "where does it stop working?" Knowing the ceiling is more valuable than knowing it clears the floor.

---

## Target Universe

BrickLayer is intended to work against any of these, with the right runner:

| Category | Examples |
|----------|---------|
| **APIs** | REST, GraphQL, WebSocket, gRPC |
| **Codebases** | Python, Rust, Kotlin, TypeScript, Solidity |
| **Test suites** | pytest, cargo test, jest, go test, anchor test |
| **ML models** | Ollama, OpenAI, HuggingFace — accuracy, latency, regression |
| **Documents** | API docs, READMEs, legal specs, architecture docs |
| **Smart contracts** | Anchor programs, EVM contracts, invariant checking |
| **Web UIs** | Playwright-driven interaction and visual regression |
| **Simulations** | Business models, financial projections, game theory |
| **Pipelines** | CI/CD, data pipelines, ETL — correctness and performance |
| **Infrastructure** | Docker, Kubernetes, Proxmox — health and configuration drift |

---

## Current Integrations

- **Recall** (FastAPI + Qdrant + Neo4j) — first full campaign, v0.1 validation target
- **Exa MCP** — semantic research for question generation and finding enrichment
- **Firecrawl MCP** — documentation crawling for document runner
- **Recall memory** — session findings stored for cross-session learning

## Planned Integrations

- **GitHub Actions** — run campaign on every PR, post findings as review comments
- **ADBP Solana programs** — contract runner against benefit-credits and redemption programs
- **ADBP Kotlin services** — subprocess runner against Ktor test suites
- **BrowserMCP** — browser runner for web portal testing

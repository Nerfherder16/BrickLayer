# Bricklayer — Roadmap

## Current State (Baseline)

- Karpathy-style autosearch architecture (prepare / train / program)
- Specialized agents (purpose-built per domain)
- Meta-agent for agent creation and lifecycle management
- Codebase structuring and efficiency optimization layer
- **Recall** (Python) as the persistent memory substrate
- ADBP system running against Bricklayer as the primary operational workload

---

## Operational Pipeline Model

Bricklayer is an operating system for a multi-phase business pipeline.
Every phase — research, code, sales, compliance, whatever comes next — runs the same loop:

```
Research (search, web_extract)
    → Validate (introspect, test_runner, critic)
        → Generate (code_exec, str_replace, tree_sitter)
            → Execute (shell, file_ops)
                → Measure (introspect + Recall write)
                    → Crystallize (Recall pattern promotion)
                        → Next phase starts warmer
```

### Pipeline Phases

**Phase 0 — Pre-Code Research & Validation**
- Validate ADBP rulesets against current Solana documentation and protocol specs
- Verify Solana metrics against live RPC endpoints and network benchmarks
- Vendor diligence: financials, security posture, regulatory history, recent news
- Adversarial critic review of all assumptions before any code is written
- Dominant tools: `search`, `web_extract`, `introspect`, `file_ops`
- Recall state after phase: validated assumptions, flagged vendors, shaky metrics tagged

**Phase 1 — Code Generation & Validation**
- Code generation informed by Phase 0 findings — agents never start cold
- Efficiency optimizer runs against generated code with Solana benchmark targets
- Critic reviews generated code before any commit
- Dominant tools: `code_exec`, `str_replace`, `tree_sitter`, `test_runner`, `shell`
- Recall state after phase: code patterns, test results, efficiency scores, failure taxonomy

**Phase 2 — Sales Campaign Execution**
- Market research agents build prospect intelligence from web sources
- ICP validator cross-references ideal customer profile rules against real market data
- Copy agent generates campaign assets; critic reviews before any send
- Response classifier reads incoming signals, categorizes, feeds back to Recall
- Dominant tools: `search`, `web_extract`, `file_ops`, `introspect`, `shell`
- Recall state after phase: copy performance, objection patterns, conversion signals

**Phase N — Ongoing Operations**
- Each new domain (compliance, partner evaluation, reporting) uses the same loop
- Recall compounds across phases — Phase 0 vendor intelligence informs Phase 2 targeting;
  Phase 1 code patterns inform future builds

---

## Full Agent Roster

### Always Active
| Agent | Role | Phase Affinity |
|---|---|---|
| Meta-Agent | Lifecycle, routing, spawning | All |
| Internal Critic | Adversarial review of all outputs | All |
| Introspection Agent | Trace capture, self-eval, Recall writes | All |

### Research & Validation (Phase 0)
| Agent | Role | Notes |
|---|---|---|
| Research Agent | General web research, document synthesis | |
| Ruleset Validator | ADBP ruleset cross-reference vs. current specs | |
| Metrics Verifier | Solana RPC, benchmark validation | |
| Vendor Intelligence Agent | Diligence: financial, security, regulatory | Recurring across phases |

### Code & Engineering (Phase 1)
| Agent | Role | Notes |
|---|---|---|
| Code Generator | Feature and module generation | Already operational |
| Efficiency Optimizer | Structure, performance, refactoring | Already operational |

### Sales & Operations (Phase 2)
| Agent | Role | Notes |
|---|---|---|
| Campaign Strategist | Market research, ICP validation | |
| Copy Agent | Campaign asset generation | |
| Response Classifier | Incoming signal classification | Ongoing after Phase 2 |

---

## Tool Registry (prepare.md)

Tools live in `prepare.md` by phase. Agents only see tools relevant to their phase.
Recall owns operational intelligence for each tool: usage history, failure patterns, performance scores.

### Current Stack — Optimized for Right Now

| Tool | Implementation | Phase | Rationale |
|---|---|---|---|
| `code_exec` | Docker Python SDK + resource limits | 1 | Self-hosted, no new infra, battle-tested, Python-native |
| `search` | SearXNG (Docker + Python client) | 0, 2 | Self-hosted, zero cost per query, privacy-first |
| `str_replace` | Custom Python (view/replace/create/insert) | 1 | Proven pattern, surgical edits, clean Recall records |
| `tree_sitter` | tree-sitter Python bindings (pip) | 1 | Best structural code analysis available in Python |
| `web_extract` | Trafilatura → readability → Playwright | 0, 2 | Trafilatura handles ~90%; Playwright only for JS-heavy pages |
| `shell` | Python subprocess + nsjail + whitelist | 1, 2 | Tiered permission model; whitelist lives in prepare.md |
| `file_ops` | Python pathlib + workspace chroot | All | 5 ops: read, write, list, search, metadata |
| `introspect` | Custom structured logging decorator (Python) | All | Per-step trace to Recall; OTel is overkill at this stage |
| `test_runner` | pytest + Hypothesis via shell tool | 1 | pytest for correctness; Hypothesis (PBT) for generated code |
| `knowledge_graph` | Kuzu (embedded graph DB, Python SDK) | 0, 1 | Proper graph DB — embedded, no server, Cypher queries, fast |

### Why These Choices Over the Alternatives

**Docker over E2B:** E2B requires either their cloud or running their own server infrastructure. Docker SDK is already on most systems, gives you full resource control (`mem_limit`, `cpu_quota`, `network_disabled`), and adds zero new moving parts.

**Kuzu over SQLite + NetworkX:** SQLite + NetworkX was a placeholder compromise. Kuzu is an actual embedded graph database — columnar storage, native Cypher, Apache 2.0, Python SDK, sub-millisecond traversals. For vendor relationship mapping, Solana dependency graphs, and cross-phase entity tracking, Kuzu does in one query what NetworkX needs 30 lines of Python to express. No server, no config, no migration needed.

**Custom introspection decorator over OpenTelemetry:** OTel is an enterprise observability framework designed for distributed system telemetry. What you need is structured per-step agent traces written to Recall. A Python decorator that captures `{thought, tool_call, tool_result, tokens_used, latency_ms, confidence, error_type}` and writes to Recall does exactly that, with no OTel SDK, no collector, no exporter, no config files.

### Phase-Aware Tool Access

```
[phase: research]
tools: search, web_extract, introspect, file_ops (read-only)

[phase: validation]
tools: search, web_extract, shell, test_runner, introspect

[phase: generation]
tools: code_exec, str_replace, tree_sitter, file_ops, shell

[phase: execution]
tools: shell, file_ops, code_exec, introspect

[phase: campaign]
tools: search, web_extract, file_ops, introspect, shell
```

---

## Phase 1 — Feedback Loop Closure
*Goal: Make the system self-evaluating, not just self-operating.*

### 1.1 Failure Mode Taxonomy
- Define a structured error schema: `syntax | logic | hallucination | tool_failure | timeout | unknown`
- Tag every failed run with a failure type before storing in Recall
- Meta-agent uses failure type to route retries to the correct specialist

### 1.2 Eval & Scoring Harness
- Lightweight scorer grading agent outputs: correctness, efficiency, style, completeness
- Scores persisted to Recall alongside the run that produced them
- Meta-agent references score history when selecting agents for a task

### 1.3 Confidence & Uncertainty Signaling
- Agents emit a confidence signal with every output: `high | medium | low | uncertain`
- Orchestrator decides: accept / validate / escalate / re-assign
- Critical for the efficiency optimizer — distinguishes safe refactors from risky ones

---

## Phase 2 — Collaboration & Communication
*Goal: Agents build on each other, not past each other.*

### 2.1 Shared Scratchpad / Message Bus
- Typed message schema for inter-agent communication
- Agents can read intermediate reasoning from peers, not just final outputs
- Enables sequential agent chains where each step builds on the last

### 2.2 Dynamic Tool Registry
- Tool registry lives in `prepare.md` — tools are environment config, not memory
- `prepare.md` defines: tool name, schema, requirements, phase affinity, initial state
- Recall owns the operational layer: usage history, performance scores, failure patterns, agent affinity
- Meta-agent reads availability from prepare, reads trustworthiness from Recall

### 2.3 Internal Critic Agent
- Adversarial agent active across all phases — research, code, and campaign outputs
- Critic verdicts are the highest-signal data written to Recall — flag and weight accordingly

---

## Phase 3 — Recall as Meta-Learning Substrate
*Goal: Each run makes the next run cheaper.*

### 3.1 Pattern Crystallization
- Recall detects when certain agent sequences reliably produce better outcomes
- Successful patterns promoted from episodic → procedural memory
- Meta-agent pulls from crystallized strategies before exploring new paths

### 3.2 Dead End Mapping
- Track approaches that appeared promising but consistently failed
- Recall builds the negative map — paths pre-pruned by experience
- Cross-phase: a Phase 0 dead end can inform Phase 2 targeting

### 3.3 Latent Feature / Unrealized Path Detection
- Track what was *adjacent* to successful runs but never attempted
- System flags: "We always succeed near Y but never try Y — evaluate Y"
- Engine for emergent feature discovery across all pipeline phases

### 3.4 Drift Detection
- Recall holds historical performance baselines per agent and task class
- Agents silently degrading get flagged before degradation compounds
- Critical for Metrics Verifier and Ruleset Validator — Solana protocol changes
  can silently invalidate previously correct logic

---

## Phase 4 — Resilience & Observability
*Goal: Long runs don't fail expensively.*

### 4.1 Checkpointing & Resumability
- Serialize agent state at each major decision point
- Failed runs resume from last checkpoint, not from zero
- Critical for multi-phase ADBP runs spanning research → code → campaign

### 4.2 Run Replay & Audit Trail
- Every run produces a structured trace: agent sequence, tool calls, scores, critic verdicts, Recall reads/writes
- Trace stored in Recall for post-mortem analysis

---

## Phase 5 — Compounding & Emergence
*Goal: Cumulative experience becomes the primary competitive advantage.*

### 5.1 Strategy Promotion Pipeline
- Formalize: raw run → pattern → crystallized strategy → default behavior
- Strategies versioned and tagged so regressions are detectable

### 5.2 Self-Directed Exploration
- System identifies underexplored regions from Phase 3.3 data
- Meta-agent schedules low-cost exploration runs during idle time
- Findings written to Recall as candidate strategies pending validation

### 5.3 Continuous Improvement Loop
- Recall, critic verdicts, eval scores, and drift signals form a closed feedback loop
- Each ADBP run teaches the system something — by the Nth run, Bricklayer navigates
  a pre-mapped space, not an unknown one

---

## Key Design Invariants

- **Recall is the single source of truth** for memory, patterns, scores, and history
- **prepare.md owns the tool registry** — what tools exist lives in prepare; how they perform lives in Recall
- **Tools are phase-aware** — agents only access tools for their current phase; enforced at the registry level
- **The three-file contract**: `prepare.md` = environment + tooling + agent roster, `train.md` = learning, `program.md` = execution
- **The critic's verdicts are the highest-signal data in the system** — weight and persist them above all else
- **Failures are labeled data, not just errors** — every failure mode is a training signal
- **Compounding is the moat** — each run costs less than the last

---

## Open Questions / Future Consideration

- Cross-phase memory scoping — should Phase 2 (sales) agents have full Recall read access to Phase 0 (technical) data, or scoped access only?
- Human-in-the-loop injection points for high-uncertainty decisions (especially Vendor Intelligence verdicts)
- Multi-instance Recall sync if Bricklayer scales to distributed runs
- Agent versioning — handling a specialist agent being retrained mid-project
- Exploration budget policy — how much idle-time self-exploration is acceptable

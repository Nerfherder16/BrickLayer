# Handoff — Bricklayer

## What You Are Working On

**Bricklayer** is a Karpathy-style autosearch system running ADBP as its primary operational workload. It is not just a coding tool — it is a multi-phase business pipeline covering pre-code research, code generation, sales campaign execution, and any operational domain that follows.

### Components Already Built and Operational
- **Specialized agents** — purpose-built per domain/task class
- **Meta-agent** — creates, manages, and routes work to specialized agents
- **Efficiency layer** — analyzes and optimizes codebase structure and code quality
- **Recall (Python)** — the persistent memory substrate; single source of truth for all memory, patterns, scores, and history

### The Three-File Contract
- `prepare.md` — environment, tool registry (phase-aware), agent roster
- `train.md` — agent learning
- `program.md` — execution

---

## Architecture Principles You Must Respect

1. **Recall is canonical.** All persistent state lives in Recall. Do not introduce secondary stores without explicit instruction.

2. **prepare.md owns the tool registry.** Tools are environment configuration, not memory. What tools exist and their phase affinity lives in prepare.md. What tools have done and how well they've performed lives in Recall. Never write tool definitions into Recall.

3. **Tools are phase-aware.** Agents only see tools appropriate to their current phase. Enforced at the registry level in prepare.md. Do not give research-phase agents access to `code_exec`. Do not give campaign-phase agents access to `str_replace`.

4. **The critic's verdicts are the highest-signal data in the system.** Critic output must be persisted to Recall with elevated weight/priority tagging. The critic is active across all phases.

5. **Failures are labeled data.** Every failed run must be tagged with a failure type before being written to Recall: `syntax | logic | hallucination | tool_failure | timeout | unknown`.

6. **Agents signal confidence.** Every agent output includes: `high | medium | low | uncertain`. The orchestrator uses this to decide: accept / validate / escalate / re-assign.

7. **The meta-agent reasons from Recall first.** Query Recall for historical patterns, dead ends, and crystallized strategies before spawning or exploring. Exploration is the fallback, not the default.

---

## Current Tool Stack

This stack is optimized for right now. No placeholders, no future-proofing — each tool is the best available choice for the current Python environment.

| Tool | Implementation | Phase |
|---|---|---|
| `code_exec` | Docker Python SDK + resource limits | 1 |
| `search` | SearXNG (Docker + Python client) | 0, 2 |
| `str_replace` | Custom Python (view/replace/create/insert) | 1 |
| `tree_sitter` | tree-sitter Python bindings (pip) | 1 |
| `web_extract` | Trafilatura → readability → Playwright fallback | 0, 2 |
| `shell` | Python subprocess + nsjail + whitelist | 1, 2 |
| `file_ops` | Python pathlib + workspace chroot | All |
| `introspect` | Custom structured logging decorator (Python) | All |
| `test_runner` | pytest + Hypothesis via shell tool | 1 |
| `knowledge_graph` | Kuzu (embedded graph DB, Python SDK) | 0, 1 |

### Key Implementation Notes

**`code_exec` — Docker Python SDK**
Use `docker.from_env()`, `client.containers.run()` with `mem_limit`, `cpu_quota`, `network_disabled=True`. Capture stdout/stderr. Enforce per-execution timeout with a threading timer. Never run agent-generated code outside a container. Store results as `{code_hash, stdout, stderr, exit_code, duration_ms}` in Recall.

**`knowledge_graph` — Kuzu**
Kuzu is an embedded graph database — no server, no config, installs via pip (`pip install kuzu`). Use Cypher for queries. Use it for: vendor relationship mapping, Solana dependency graphs, cross-phase entity tracking (a vendor flagged in Phase 0 should surface in Phase 2 targeting). Store entities and relationships; query with `MATCH` patterns. Do not replicate this data into Recall — Kuzu holds the graph, Recall holds episodic/operational memory. They complement each other.

**`introspect` — Structured logging decorator**
A Python decorator applied to every agent step that captures:
```python
{
  "agent": agent_name,
  "phase": current_phase,
  "thought": reasoning_step,
  "tool_call": tool_name,
  "tool_result": result_summary,
  "tokens_used": count,
  "latency_ms": duration,
  "confidence": signal,
  "error_type": taxonomy_tag_or_null,
  "timestamp": iso8601
}
```
Write this record to Recall after every step. This is the primary feed for pattern crystallization and drift detection. Do not use OpenTelemetry — it is an enterprise distributed tracing framework, not an agent introspection tool.

**`web_extract` — Trafilatura cascade**
Trafilatura first (pure Python, handles ~90% of pages). Fall back to readability-lxml if Trafilatura returns under `MIN_CONTENT_LENGTH` (200 chars). Fall back to Playwright only for JavaScript-rendered SPAs — Playwright is 200MB+ and should not be the default. Store as `{url, title, extracted_text, extraction_method, fetch_timestamp}` in Recall with deduplication check before writing.

**`shell` — Tiered permission model**
- Level 1 (read-only): always allowed — `ls`, `cat`, `grep`, `find`, `pwd`
- Level 2 (workspace-modifying): auto-allow within working directory — `mkdir`, `cp`, `mv`
- Level 3 (whitelisted commands): `git`, `python`, `pytest`, `cargo` — defined in prepare.md
- Level 4 (anything else): requires explicit meta-agent approval
Use `spawn()` directly, not `shell=True`. Validate all operators (`;`, `&&`, `||`, `|`) against the whitelist. Never allow `rm -rf`, `curl|sh`, or Docker socket access.

**`str_replace` — Core editing pattern**
Four operations: `view(path, start_line, end_line)`, `str_replace(path, old_str, new_str)`, `create(path, content)`, `insert(path, line_number, content)`. `old_str` must be unique in the file — include enough context lines. Run a linter after every edit and reject invalid syntax before writing. Back up files before modification. Store edit records as `{file_path, old_str_hash, new_str_hash, success, lint_result, timestamp}` in Recall.

---

## The Operational Pipeline

Every phase follows the same loop:
```
Research → Validate → Generate → Execute → Measure → Crystallize → Repeat (warmer)
```

### Phase 0 — Pre-Code Research & Validation
Before any code is written:
- Validate ADBP rulesets vs. current Solana docs and protocol specs
- Verify Solana metrics vs. live RPC endpoints and benchmarks
- Run vendor diligence (financials, security, regulatory, recent news)
- Critic reviews all assumptions adversarially

Tools: `search`, `web_extract`, `introspect`, `file_ops (read-only)`

### Phase 1 — Code Generation & Validation
Informed by Phase 0 — never starts cold.
Tools: `code_exec`, `str_replace`, `tree_sitter`, `test_runner`, `shell`

### Phase 2 — Sales Campaign Execution
Same loop, different domain.
Tools: `search`, `web_extract`, `file_ops`, `introspect`, `shell`

---

## Full Agent Roster

### Always Active
- **Meta-Agent** — lifecycle, routing, spawning *(already operational)*
- **Internal Critic** — adversarial review across all phases
- **Introspection Agent** — trace capture, self-eval, Recall writes

### Research & Validation
- **Research Agent** — general web research, document synthesis
- **Ruleset Validator** — ADBP ruleset cross-reference vs. current specs
- **Metrics Verifier** — Solana RPC, benchmark validation
- **Vendor Intelligence Agent** — diligence: financial, security, regulatory *(recurring)*

### Code & Engineering
- **Code Generator** — feature and module generation *(already operational)*
- **Efficiency Optimizer** — structure, performance, refactoring *(already operational)*

### Sales & Operations
- **Campaign Strategist** — market research, ICP validation
- **Copy Agent** — campaign asset generation
- **Response Classifier** — incoming signal classification *(ongoing)*

---

## Recall Storage Patterns

Run data:
```
domain: bricklayer
tags: [run, phase, agent_name, outcome, failure_type]
```

Critic verdicts:
```
domain: bricklayer
tags: [critic, verdict, phase, agent_name, severity (critical|warning|info)]
```

Tool operational data:
```
domain: bricklayer
tags: [tool, tool_name, phase, outcome, latency_ms, agent_name]
```

Introspection trace (per step):
```
domain: bricklayer
tags: [trace, phase, agent_name, tool_call, confidence, error_type]
```

Crystallized strategies:
```
domain: bricklayer
tags: [strategy, crystallized, phase, agent_sequence, task_class]
```

Kuzu handles entity/relationship graph.
Recall handles episodic/operational memory.
They do not overlap.

---

## Current Phase Priority

1. Formalize agent roster and tool registry in `prepare.md`
2. Implement **Phase 1 — Feedback Loop Closure** (failure taxonomy → scoring → confidence signaling)
3. Build the introspection decorator and wire it to all existing agents
4. Do not move to roadmap Phase 2 until Phase 1 is complete and tested

---

## Do Not Change Without Asking

- Recall's core architecture or storage model
- The meta-agent's agent creation/lifecycle logic *(already operational)*
- The efficiency layer's core analysis pipeline *(already operational)*
- Tool interfaces once established — if an implementation needs replacing, replace it; the interface stays
- Anything that introduces a second source of truth alongside Recall

---

## Working Style Notes

- Privacy-first, self-hosted. No cloud dependencies without explicit approval.
- Prefer low-dependency solutions. If a tool requires running a server, question whether it's worth it.
- Wire Recall integration before building feature logic — memory is not an afterthought.
- When choosing between two implementations, prefer the one that produces more useful data for Recall.
- If something isn't working well, cut it and recommend a better path. Don't defend a bad choice.

---

## Files to Reference

- `roadmap.md` — full phased feature plan, pipeline model, tool registry, agent roster
- `handoff.md` (this file) — constraints, context, and working instructions

---

## Current Status

| Item | Status |
|---|---|
| Tool registry formalized in prepare.md | 🔲 Not started |
| Agent roster formalized in prepare.md | 🔲 Partial (meta, code gen, efficiency operational) |
| Phase 0 research agents | 🔲 Not started |
| Phase 1 — Feedback Loop Closure | 🔲 Not started |
| Phase 2 — Collaboration & Communication | 🔲 Not started |
| Phase 3 — Recall as Meta-Learning Substrate | 🔲 Not started |
| Phase 4 — Resilience & Observability | 🔲 Not started |
| Phase 5 — Compounding & Emergence | 🔲 Not started |

Update this table as work progresses.

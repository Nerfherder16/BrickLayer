# Kiln OS — OS Component Deep Dive

Last updated: 2026-03-19

Deep analysis of the OS metaphor: which components exist, which are in progress, which are missing, and why the metaphor holds beyond the surface analogy.

---

## Why the OS Metaphor Holds

A traditional operating system does one thing at its core: it arbitrates access to shared resources between competing processes, provides abstractions that hide hardware complexity, and enforces isolation between processes that shouldn't interfere with each other.

Kiln OS does the same — for AI agents competing for compute resources, memory, tool access, and model inference capacity. The abstractions are different (A2A protocol instead of syscalls, semantic memory instead of virtual memory, YAML profiles instead of process permissions tables) but the function is identical.

This is not a forced analogy. It is a consequence of building a multi-agent system at sufficient complexity. Every multi-agent system eventually rediscovers OS primitives. The only question is whether you discover them accidentally or design them intentionally.

Kiln OS is the intentional version.

---

## Component Status Reference

| OS Primitive | Kiln OS Component | Built | Working | Needs Work | Missing |
|--------------|-------------------|-------|---------|------------|---------|
| Kernel | BrickLayer 2.0 | X | X | Phase 8 self-improvement | — |
| Process scheduler | nvidia-nat (A2A) | — | — | — | X (Phase 2) |
| Memory manager | Recall | X | X | Recall 2.0 (SourceTrust, retention, Privacy Router) | — |
| Virtual memory (paging) | Recall retention policy | — | — | Phase 4 | — |
| File system | Qdrant + Neo4j + PG | X | X | — | — |
| Device drivers | OpenShell profiles | — | — | — | X (Phase 1) |
| System calls | mcp_gateway.py | — | — | — | X (Phase 1+) |
| Shell | Claude Code | X | X | — | — |
| Secondary shell | Codevv | partial | partial | Phase 5 wiring | — |
| Package manager | Masonry | X | X | Enterprise pack (Phase 3) | — |
| Boot sequence | masonry-session-start.js | X | X | — | — |
| IPC | A2A protocol (nvidia-nat) | — | — | — | X (Phase 2) |
| Process table | agent_db.json + Mortar | partial | partial | Phase 8 | — |
| System monitor | Kiln / BrickLayerHub | partial | partial | nvidia-nat integration | — |
| Keychain | — | — | — | — | X (Phase 7) |
| Resource accounting | — | — | — | — | X (Phase 7) |
| Service mesh | — | — | — | — | X (Phase 7) |
| Health daemon | — | — | — | — | X (Phase 7) |
| Custom kernel modules | NeMo fine-tuned model | — | — | — | X (Phase 6) |

---

## Deep Dive: What's Built and Working

### BrickLayer 2.0 — Kernel

The kernel of an OS enforces the law. It is the one thing that runs at the highest privilege level and cannot be overridden by user processes. BL2.0 is the research kernel: `program.md` is the law, and agents cannot deviate from it.

The kernel handles the research loop:
1. Select next PENDING question from `questions.md`
2. Route to appropriate agent type (D1→quantitative, D2→regulatory, etc.)
3. Agent executes and writes findings
4. Loop continues — no stopping except catastrophic failure

Like a real kernel, BL2.0 is designed to run continuously, recover from failure (`git reset --hard HEAD` is the equivalent of a kernel panic recovery), and enforce invariants regardless of what individual agents try to do.

**Phase 8 current work:** The self-improvement loop (Mortar agent + agent_db.json) gives the kernel the ability to learn from agent performance and improve routing decisions. This is analogous to a kernel with adaptive scheduling — it notices that some agents consistently produce better findings and weights them higher.

### Recall — Memory Manager

The memory manager's job is to abstract storage: callers don't need to know whether they're reading from L1 cache, RAM, or disk. They ask for memory and get it.

Recall does the same for knowledge:
- Qdrant provides vector search (semantic proximity — like associative cache)
- Neo4j provides graph traversal (causal relationships — like memory-mapped I/O for relationships)
- PostgreSQL provides structured retrieval (exact lookup — like direct memory addressing)
- Redis provides hot cache (recently accessed memories — like L1/L2 cache)

The hooks (`recall-retrieve.js`, `observe-edit.js`) are the read/write interface — the equivalent of `malloc()` and `free()` for agent knowledge. Agents don't call Recall directly; the hooks intercept tool use and manage memory transparently.

The `DISABLE_OMC=1` problem is partly a memory isolation failure: BL2.0's subprocess agents and the parent Masonry session share the same hook-level memory interface. They shouldn't. OpenShell profiles fix this by giving each process its own isolated memory access profile.

### Masonry — Package Manager

The package manager handles distribution, installation, and dependency resolution. Masonry does this for:
- Agent definitions (`.claude/agents/*.md`)
- Skill definitions (`~/.claude/skills/*.md`)
- Hook scripts (node.js hooks in `settings.json`)
- Project templates (`template/` directory)

`masonry-mcp` v0.1.0 is the npm package. The equivalent of `apt-get install` is currently "copy from the template directory and run the setup script." Phase 3 makes this `npx masonry-init`.

### masonry-session-start.js — Boot Sequence

The boot sequence runs at system start, restores state from the last session, and hands control to the shell. `masonry-session-start.js` fires on SessionStart, reads `.autopilot/mode`, `.ui/mode`, and `masonry-state.json`, injects campaign context into the session, and restores interrupted build state.

This is exactly what `/etc/init.d/` or `systemd` does at boot: restore known state, start dependent services in order, hand control to the user session.

---

## Deep Dive: What's Missing and Why It Matters

### Missing: Credential Vault (Keychain)

**The gap:** Secrets are stored in `.env` files spread across developer machines, the Recall VM, and CasaOS Docker containers. No rotation. No audit trail. No centralized management.

**Why it matters:** A single compromised machine exposes all secrets across all services. The attack surface grows with every new service added. There is no way to rotate a secret without manually touching every file that uses it.

**The fix:** Infisical (self-hosted, open source, beautiful UI) or HashiCorp Vault. The integration point is OpenShell profiles: instead of injecting `ANTHROPIC_API_KEY` as an environment variable, the profile grants the agent a Vault token scoped to exactly the secret path it needs. The agent fetches the secret at runtime, uses it, and the token expires. No secret lives in any config file.

**Priority:** High. This is a security gap that grows worse with every new service.

### Missing: Per-Agent Resource Accounting

**The gap:** No data on how many tokens each BL2.0 agent consumes per question, per campaign, or per project. No way to measure agent efficiency. No way to set token budgets or detect runaway agents.

**Why it matters:** Cannot optimize what you cannot measure. If `kiln-research-v1` (fine-tuned model) produces equivalent findings to `qwen3:14b` at 30% lower token cost, that's measurable ROI from the fine-tuning investment. But only if you're tracking token usage.

**The fix:** Add `tokens_in`, `tokens_out`, `cost_usd` fields to AgentRun records in agent_db.json. Surface in Kiln monitor as efficiency score (CONFIRMED findings per 1K tokens). Set per-campaign token budgets in questions.md.

**Priority:** Medium. Does not block anything, but enables optimization decisions.

### Missing: Service Mesh

**The gap:** Each Kiln OS component (Recall, BL2.0 campaign runner, Kiln monitor, Codevv) is an island. There is no service discovery, no health endpoints, no automatic retry, no circuit breaker.

**The failure mode:** Recall goes down. masonry-observe.js tries to write a memory, fails silently, logs nothing. The session continues. The memory is lost. Nobody knows until Tim notices things aren't being remembered.

**Why it matters:** Silent failures are worse than loud failures. A service mesh makes failures visible, handles transient failures automatically (retry with backoff), and prevents cascade failures (circuit breaker).

**The fix:** Lightweight service registry (Consul, or even a static Nginx config with health probes). `/health` endpoints on every service. Circuit breaker in masonry-observe.js: if Recall fails 3 times in 30 seconds, queue writes locally and alert via Kiln.

**Priority:** Low for now (system is small), high at Phase 5+ scale.

### Missing: Health Monitoring Daemon

**The gap:** No proactive health monitoring. Service failures are discovered reactively (Tim notices something is wrong).

**Why it matters:** At Kiln OS scale (Recall VM + Ollama VM + CasaOS + developer machine + Codevv backend + nvidia-nat), the number of potential failure points grows with each phase. Manual monitoring does not scale.

**The fix:** A scheduled Masonry agent that runs hourly, pings all Kiln OS services, writes health status to Recall (machine-readable), and pushes alerts to Kiln monitor. The health data in Recall gives historical health trends — useful for capacity planning.

**Priority:** Medium. Implement in Phase 7 as part of the operational completeness pass.

### Missing: Fine-Tuned Domain Model

**The gap:** All inference uses base models (qwen3:14b via Ollama, Claude via API). The accumulated BL2.0 findings — structured research outputs representing domain-specific reasoning — are not used to improve the model that runs future campaigns.

**Why it matters:** The compounding research loop has a ceiling at the base model's reasoning quality. A domain-tuned model can produce higher CONFIRMED ratios, better failure boundary identification, and more rigorous methodology — because it has been trained on thousands of examples of doing exactly that.

**The fix:** Phase 6. Export high-SourceTrust findings as JSONL instruction pairs, LoRA fine-tune on qwen3:14b via NeMo Framework, package as NIM microservice, deploy on RTX 3090.

**Priority:** Low (Phase 6). Requires 500+ high-quality Recall entries as training data, which takes months to accumulate. The work happens in Phase 6; the preparation happens now (consistent Recall writes, SourceTrust scoring).

---

## The UNIX Origin Story Parallel

UNIX started as a side project. Ken Thompson wanted to play Space Travel on a PDP-7 with underutilized compute. To run Space Travel, he needed an operating environment. He wrote a file system. Then he needed to run programs. He wrote a process model. Then Dennis Ritchie needed to write programs easily, so they wrote a shell. Then they needed to share code. They wrote pipes and redirection.

None of these were "let's build an OS" decisions. They were "I need this tool to exist so I can do the thing I actually want to do" decisions. The OS emerged from the scaffolding.

Twenty-five years later, UNIX is everywhere. The tools converged.

Kiln OS is on the same trajectory. Tim needed to run autonomous research campaigns — BL2.0. He needed agents to remember things across sessions — Recall. He needed to manage hooks and skills across projects — Masonry. He needed to monitor campaign progress from the desktop — Kiln. He needed a collaborative interface for team development — Codevv.

None of these were "let's build an OS" decisions. The OS emerged.

The difference from UNIX: this happened in months, not years. And the tools are better than Thompson and Ritchie had — agents, LLMs, vector databases, and a GPU in a homelab server. The scaffolding is more powerful. The convergence is faster.

---

## Historical Analogies

### The OpenBSD Security Model

OpenBSD's design philosophy: every component is audited for security. Privilege separation means each daemon runs with the minimum permissions needed. Sound familiar? OpenShell profiles for BL2.0 agents are the same philosophy applied to AI agents.

The analogy extends: in OpenBSD, a compromised web server (httpd) cannot read the mail spool because they run as different users with different filesystem permissions. In Kiln OS with OpenShell, a compromised quantitative-analyst agent cannot read production credentials because the `bl-quantitative` profile doesn't grant access to the secrets vault path.

### The Docker Moment

Docker didn't invent containers. Linux namespaces and cgroups existed before Docker. What Docker did was package a complex set of Linux primitives into a simple, composable interface: `docker run`, `docker build`, `Dockerfile`. The complexity was hidden. The power was preserved.

OpenShell profiles for Kiln OS agents may be that moment for AI agent sandboxing. The underlying primitives (process isolation, filesystem namespacing) exist. The missing piece is a simple, composable interface that makes "define an agent's security boundary" as natural as writing a Dockerfile.

If OpenShell is that interface, Kiln OS adopts it immediately.

### The npm Moment

npm gave Node.js an ecosystem. Before npm, JavaScript libraries were manually downloaded, copied into projects, and updated manually. After npm: `npm install express` and you have the most-downloaded web framework in history.

Masonry enterprise packs (Phase 3) are the npm moment for AI agent ecosystems. `npx masonry-install defi-research` gives you a complete research agent fleet, trained question bank templates, fine-tuned profile configurations, and Recall integration — for a specific domain. The domain knowledge is the package. The research capability is the install.

---

## The Ceiling Metaphor — Explained Fully

Traditional team: each developer carries their own knowledge. When they leave, knowledge leaves. New developers start from zero (onboarding). The team's effective knowledge is capped by the overlap between individuals.

Kiln OS team: each agent run adds to Recall. When a developer leaves, their session summaries, corrections, and insights stay in Recall. New developers connect to Recall and immediately access the cumulative knowledge of every prior agent run. The team's effective knowledge grows monotonically with each campaign.

The "ceiling" metaphor: the current Recall state IS the ceiling. Every new developer starts at the ceiling instead of the floor. Their job is to push the ceiling higher — to run new campaigns, answer new questions, surface new findings, make new corrections. The ceiling rises. The next person starts even higher.

This only works if:
1. Recall never loses data (retention policy, no silent failures)
2. Trust is correctly scored (human corrections override agent outputs)
3. The Privacy Router keeps sensitive knowledge local
4. The system is queryable (cross-project semantic search, Phase 4)

All four are in the Recall 2.0 roadmap. This is not a nice-to-have. It is the core value proposition of Kiln OS.

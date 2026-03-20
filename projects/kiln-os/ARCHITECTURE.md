# Kiln OS — Architecture

Last updated: 2026-03-19

---

## OS Component Mapping

The core insight of Kiln OS is that the 22 Collective stack already implements OS primitives — it just didn't have a name for them. This table is the Rosetta Stone.

| Traditional OS | Kiln OS Component | Implementation | Status |
|----------------|-------------------|----------------|--------|
| Kernel | BrickLayer 2.0 | `bl/` package, `program.md` loop | Built |
| Process scheduler | nvidia-nat + A2A | `bl/campaign.py` → A2A dispatch | Planned |
| Memory manager | Recall / Recall 2.0 | Qdrant + Neo4j + PostgreSQL + Redis | Built (v1) |
| File system | Qdrant + Neo4j + PG | Under Recall abstraction | Built |
| Device drivers | OpenShell profiles | Per-agent YAML sandbox profiles | Planned |
| System calls | mcp_gateway.py | Port 8350, unified MCP tool surface | Planned |
| Shell | Claude Code + Codevv | Interactive user surface | Built |
| Package manager | Masonry | `masonry-mcp` npm package | Built (v0.1.0) |
| Boot sequence | masonry-session-start.js | Session restore hook | Built |
| IPC | A2A protocol (nvidia-nat) | Agent-to-agent message passing | Planned |
| Process table | agent_db.json + Mortar | Per-agent scores, run history | Phase 8 active |
| System monitor | Kiln / BrickLayerHub | Electron desktop app | Active dev |
| Keychain | (missing) | — | Gap |
| Resource accounting | (missing) | Token usage tracking | Gap |
| Service mesh | (missing) | Inter-service discovery | Gap |
| Health daemon | (missing) | System health monitoring agent | Gap |
| Custom modules | NeMo fine-tuned model | Domain checkpoint via NIM | Phase 6 |

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                             │
│                                                                     │
│   Claude Code (shell)          Codevv (collaborative IDE)           │
│   - Interactive sessions       - Pipeline page → nvidia-nat         │
│   - Masonry skills/agents      - Knowledge Graph → BL2.0 findings   │
│   - /plan /build /research     - Yjs real-time sync                 │
│                                - LiveKit voice/video                │
│                  Kiln / BrickLayerHub (system monitor)              │
│                  - Campaign status, agent pool, health              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ System calls (mcp_gateway.py :8350)
┌────────────────────────────▼────────────────────────────────────────┐
│                      PLATFORM LAYER (Masonry)                       │
│                                                                     │
│   Hooks: session-start, approver, lint-check, observe, stop-guard  │
│   Skills: /masonry-run, /plan, /build, /verify, /fix, /ui-*        │
│   Packs: agent bundles, skill sets, profile sets                    │
│   Registry: agent_db.json + Mortar scoring                         │
└──────┬──────────────────────────────────────────┬───────────────────┘
       │ Agent dispatch (A2A)                     │ Memory R/W
┌──────▼─────────────────────┐    ┌───────────────▼──────────────────┐
│   PROCESS SCHEDULER        │    │   MEMORY MANAGER                 │
│   nvidia-nat               │    │   Recall / Recall 2.0            │
│                            │    │                                  │
│   - A2A agent registry     │    │   - Qdrant (vector/semantic)      │
│   - OpenShell profiles     │    │   - Neo4j (graph, causal edges)  │
│   - Privacy Router         │    │   - PostgreSQL (structured data) │
│   - Per-user isolation     │    │   - Redis (cache, sessions)      │
│   - Agent health checks    │    │   - SourceTrust scoring          │
│                            │    │   - Retention policy engine      │
└──────┬─────────────────────┘    └───────────────┬──────────────────┘
       │ Sandboxed execution                       │ Findings storage
┌──────▼─────────────────────────────────────────────────────────────┐
│                      RESEARCH KERNEL                                │
│                      BrickLayer 2.0                                 │
│                                                                     │
│   program.md loop     questions.md bank     findings/ directory     │
│   simulate.py         constants.py          results.tsv             │
│   agent fleet:                                                      │
│     quantitative-analyst  regulatory-researcher  competitive-analyst│
│     benchmark-engineer    hypothesis-generator   synthesizer        │
│     planner               question-designer-bl2                    │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ Training data export
┌──────────────────────────────▼─────────────────────────────────────┐
│                    MODEL LAYER                                      │
│                                                                     │
│   Ollama (local)           NIM microservices (NVIDIA)              │
│   - qwen3:14b              - kiln-research-v1 (fine-tuned)         │
│   - qwen3-embedding:0.6b   - Parakeet (ASR for Sadie/ACE)          │
│                            - Domain-specific checkpoints           │
│                                                                     │
│   NeMo Framework (fine-tuning pipeline)                            │
│   - Findings → JSONL training data                                 │
│   - LoRA fine-tuning on qwen3:14b base                             │
│   - Checkpoint → NIM deployment                                    │
│                                                                     │
│   Triton Inference Server (backing NIM)                             │
└────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Research Campaign

A BL2.0 research campaign flows through Kiln OS as follows:

```
1. Human initiates:
   Claude Code shell → /masonry-run → reads masonry-state.json

2. Boot/restore:
   masonry-session-start.js → reads .autopilot/ state
   Recall hook → injects relevant memories into context

3. Campaign launch:
   bl/campaign.py → nvidia-nat A2A dispatch → bricklayer-research OpenShell profile
   Campaign subprocess: isolated filesystem + network surface

4. Research loop (per question):
   program.md → selects agent type → nvidia-nat routes to agent
   Agent → mcp_gateway.py (tool calls: search, simulate, web)
   Agent → writes to results.tsv, findings/*.md

5. Memory write:
   masonry-observe.js (PostToolUse) → extracts facts → Recall store
   SourceTrust score: agent-generated = 0.7

6. Synthesis:
   synthesizer agent → reads all findings → writes synthesis.md
   synthesis.md → Recall store (project namespace, permanent tier)

7. Monitoring:
   agent_db.json → Mortar scores update
   Kiln desktop → reads agent_db.json → displays in campaign monitor
   mcp_gateway.py → nvidia-nat → Kiln health status update

8. Fine-tuning (Phase 6):
   bl/export_training_data.py → filters Recall (SourceTrust >= 0.8)
   → JSONL training data → NeMo Framework → checkpoint → NIM
```

---

## Data Flow: Memory Query

When a Recall hook surfaces memories during a session:

```
UserPromptSubmit hook fires
→ recall-retrieve.js: extract query terms from user prompt
→ Recall API: semantic search (Qdrant) + graph traversal (Neo4j)
→ SourceTrust filter: exclude low-trust entries (< 0.5 default)
→ Privacy Router: check if any results trigger routing policy
→ Return: top-K relevant memories injected into context prefix
→ Masonry-session-start.js: autopilot/UI/campaign context restored separately
```

---

## Integration Points

### BrickLayer 2.0 ↔ Recall

- **Write path:** masonry-observe.js (PostToolUse) → Recall store API
- **Read path:** recall-retrieve.js (UserPromptSubmit) → Recall search API
- **Schema:** AgentRun, AgentFinding, HumanCorrection records
- **Namespace:** per-project (e.g., `bricklayer/adbp`, `bricklayer/kiln-os`)

### BrickLayer 2.0 ↔ nvidia-nat

- **Dispatch:** `bl/campaign.py` calls nvidia-nat A2A endpoint
- **Agent registry:** agent type manifests (YAML) registered with nvidia-nat
- **Profile enforcement:** OpenShell applies sandbox before agent execution
- **Telemetry:** agent_db.json scores → OpenTelemetry → Langfuse/Phoenix

### Masonry ↔ Kiln (Electron)

- **State files:** masonry-state.json, agent_db.json, .autopilot/progress.json
- **Polling:** Kiln reads state files on interval (no active push today)
- **Future:** WebSocket push from mcp_gateway.py for live updates

### Codevv ↔ nvidia-nat (Phase 5)

- **Pipeline page:** REST calls to mcp_gateway.py → A2A dispatch
- **Real-time:** Yjs-synced agent progress state (CRDT, no server coordination needed)
- **Findings feed:** WebSocket from Recall → Knowledge Graph live update

### Recall ↔ NeMo (Phase 6)

- **Export:** bl/export_training_data.py queries Recall API with SourceTrust filter
- **Format:** JSONL instruction-following pairs
- **Feedback loop:** NIM-served model results → new AgentRun records → back to Recall

---

## Security Boundaries

```
INTERNET
    │ (HTTPS only, outbound)
    │
HOME NETWORK (192.168.50.0/24)
    │
    ├── OPNsense firewall (192.168.50.1)
    │
    ├── Tailscale overlay (100.x.x.x/8)
    │       └── Recall VM (100.70.195.84)
    │
    ├── Ollama VM (192.168.50.62) — RTX 3090, local inference only
    │
    ├── CasaOS Docker host (192.168.50.19) — Recall + other services
    │
    └── Developer machine — Claude Code + Kiln + Codevv dev

TRUST BOUNDARIES
    - OpenShell profiles: per-agent filesystem + network surface
    - Privacy Router: policy-enforced local-vs-cloud routing
    - Credential vault (Phase 7): no secrets in env vars or config files
    - Recall SourceTrust: human corrections always override agent outputs
```

---

## Component Dependencies

```
Kiln OS (full)
├── BrickLayer 2.0 (kernel)          — standalone today
├── Masonry (platform)               — depends on BL2.0 for research mode
├── Recall (memory)                  — standalone today
├── Kiln / BrickLayerHub (monitor)   — depends on BL2.0 state files
├── Codevv (shell/IDE)               — depends on Recall, nvidia-nat (Phase 5)
├── nvidia-nat (scheduler)           — standalone (NVIDIA product)
│   └── OpenShell profiles           — depends on nvidia-nat
│   └── Privacy Router               — depends on nvidia-nat
├── NIM (model containers)           — standalone (NVIDIA product)
│   └── NeMo fine-tuned checkpoint   — depends on BL2.0 + Recall export
└── mcp_gateway.py (system calls)    — depends on nvidia-nat + Recall
```

---

## What Does NOT Exist Yet

These are the known gaps — OS primitives that the current stack lacks:

1. **Credential vault**: Secrets live in `.env` files and environment variables. No centralized vault, no rotation, no audit log. Risk: secret sprawl across multiple machines.

2. **Per-agent resource accounting**: No tracking of how many tokens each BL2.0 agent consumes per question, per campaign, per project. Cannot optimize cost without data.

3. **Service mesh**: Each Kiln OS component is independently running. There is no service registry, no automatic retry on failure, no circuit breaker. When Recall is down, the session silently loses memory writes.

4. **Health monitoring daemon**: No scheduled health checks across the ecosystem. Service failures are discovered when a human notices something is wrong, not proactively.

5. **Fine-tuned domain model**: All inference uses base models (qwen3:14b, Claude). The accumulated BL2.0 findings dataset is not yet used to improve inference quality. This is Phase 6.

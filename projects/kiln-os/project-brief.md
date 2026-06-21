# Kiln OS — Project Brief

**Authority: Tier 1 — Human Only**
Last updated: 2026-03-19

---

## What Kiln OS Is

Kiln OS is the emergent AI Operating System of the 22 Collective ecosystem. It was not designed top-down — it was discovered. Tim built tools that needed to exist: a project lifecycle engine, a memory system, a collaboration platform, a desktop monitor, an agent platform layer. When those tools were laid side by side, they mapped cleanly onto OS primitives. That convergence is Kiln OS.

It is not a product yet. It is a structural reality — a recognition that the stack already behaves like an OS, and that naming it as such unlocks a clearer development path, a cleaner integration story, and a compelling narrative for the NVIDIA enterprise AI ecosystem.

**The one-sentence pitch:** An AI operating system for agentic research and development, built self-hosted, running on your infrastructure, where every agent run compounds institutional knowledge that never decays.

---

## Core Thesis

Two things compound in traditional software companies: code and human knowledge. Code compounds via version control. Human knowledge doesn't — it lives in people's heads, leaks out when they leave, and cannot be shared across time.

Kiln OS changes this. Every agent run — every BrickLayer 2.0 research campaign, every Codevv pair-programming session, every Masonry build — writes to Recall. The semantic memory layer retains what the agents learned, what worked, what failed, and why. A new developer joining 22 Collective doesn't start from zero. They start at the ceiling.

The compounding loop:
1. Agent runs a research campaign
2. Findings write to Recall (structured memory)
3. Accumulated findings feed NeMo fine-tuning
4. Fine-tuned domain model runs BL2.0 campaigns better
5. Better campaigns generate richer findings
6. Loop accelerates

This is not a feature. It is the point of the entire system.

---

## Key Invariants

These must remain true as Kiln OS evolves:

1. **Self-hosted by default.** All core components run on Tim's infrastructure. Cloud inference is opt-in, never required. Privacy Router enforces this boundary.

2. **Memory persists and compounds.** Recall is the source of truth for accumulated knowledge. Nothing should delete or silently fail to write to it. Agent outcomes always flow to Recall.

3. **Agents are sandboxed.** Each agent type has a defined filesystem and network surface. BL2.0 research agents do not have write access to production services. OpenShell profiles enforce this.

4. **No lock-in to a single model.** NIM microservices provide swappable model containers. The system must work with Ollama today and NIM tomorrow. Interfaces are model-agnostic.

5. **Human stays in the loop on trust boundaries.** The Privacy Router may route to cloud inference — but the policy file is human-readable and human-controlled. No silent cloud egress.

6. **Kiln (desktop app) is the primary monitoring UI.** No web dashboard for campaign monitoring. All campaign UI goes through Kiln/BrickLayerHub.

7. **BrickLayer 2.0 program.md is the research law.** Agents in a BL2.0 campaign follow program.md exactly. They do not improvise loop structure.

---

## Non-Goals

- **Not a traditional OS.** Kiln OS does not manage CPU scheduling, process memory, or hardware interrupts. The "OS" framing is an architectural metaphor that maps agent primitives to OS primitives.
- **Not a product today.** Kiln OS is a project-level naming of an existing stack. It becomes a product when it has a clear interface for external customers — that is Phase 3+.
- **Not replacing Claude Code.** Claude Code is the shell. It is the interactive surface. Kiln OS runs beneath it.
- **Not a model company.** 22 Collective does not train foundational models. It fine-tunes narrow domain models using NeMo Framework on accumulated BL2.0 findings. The distinction matters.
- **Not cloud-first.** Never. See invariant #1.
- **Not a monolith.** Each component (Recall, BL2.0, Masonry, Codevv, Kiln) is independently deployable and independently useful. Kiln OS is the integration name, not a coupled codebase.

---

## Component Inventory

### Exists (Production or Near-Production)

| Component | Role in Kiln OS | Status |
|-----------|-----------------|--------|
| BrickLayer 2.0 | Kernel — project lifecycle engine, autonomous agent loop | Production |
| Masonry | Platform layer — agent/skill/profile distribution, hooks | Production (`masonry-mcp` v0.1.0) |
| Recall | Memory manager — semantic memory, Qdrant + Neo4j + PG | Deployed (VM, Tailscale) |
| Kiln / BrickLayerHub | System monitor — Electron desktop, campaign UI | Active development |
| Claude Code | Shell — interactive user interface | Production (COTS) |
| Codevv | Collaborative IDE surface — FastAPI + React 19 + Yjs + LiveKit | Development |
| mcp_gateway.py | System call interface — port 8350, unified MCP tool surface | Planned |
| masonry-session-start.js | Boot sequence — hook that restores context on session open | Production |

### In Progress

| Component | Role in Kiln OS | Status |
|-----------|-----------------|--------|
| Recall 2.0 | Memory manager v2 — SourceTrust, Privacy Router, retention policy | Design phase |
| Masonry enterprise pack | Package manager distribution — `npx masonry-init --template=enterprise` | Planned |
| agent_db.json / Mortar | Process accounting — per-agent scores, run history | Phase 8 active |

### Planned / Integration Targets

| Component | Role in Kiln OS | Status |
|-----------|-----------------|--------|
| nvidia-nat | Process scheduler — A2A agent dispatch, replaces subprocess.Popen | Planned integration |
| OpenShell | Device drivers — per-agent YAML sandbox profiles | Planned integration |
| Privacy Router | Security policy — local vs cloud routing policy enforcement | Planned integration |
| NIM | Model containers — swappable inference units | Planned integration |
| NeMo Framework | Fine-tuning pipeline — domain model training on BL2.0 findings | Planned integration |
| Triton Inference Server | Inference serving — NIM backing runtime | Planned (via NVIDIA) |
| Parakeet / ACE | Voice interface — Sadie family hub, potential ACE runtime | Planned |

### Missing (Identified Gaps)

| Missing Component | OS Analog | Priority |
|-------------------|-----------|----------|
| Credential/secrets vault | Keychain / `/etc/secrets` | High |
| Per-agent token usage tracking | Resource accounting / `top` | Medium |
| Service mesh (inter-service discovery) | Kernel IPC routing table | Low |
| System health monitoring agent | Health daemon / `systemd` watchdog | Medium |
| Fine-tuned domain model | Custom kernel modules | Low (Phase 6) |

---

## The Jensen Huang Inspiration

GTC 2026 shifted the framing. Jensen's announcement of NemoClaw — OpenShell profiles, nvidia-nat A2A dispatch, Privacy Router, NIM microservices — is not a competitor to what 22 Collective is building. It is the enterprise runtime layer that 22 Collective's stack can run on top of.

The insight: BrickLayer 2.0 agents are exactly the kind of agentic workloads NemoClaw was designed to orchestrate. OpenShell profiles solve the DISABLE_OMC=1 problem natively. nvidia-nat solves the subprocess.Popen multi-agent problem natively. Privacy Router solves the local-vs-cloud inference problem natively.

22 Collective is not behind. It is early. The self-hosted, self-improving, compounding-knowledge system it has built is a working prototype of what the NVIDIA enterprise AI stack is designed to enable at scale.

---

## The Name

**Kiln**: a furnace that transforms raw material into durable, functional form. BrickLayer builds the bricks. The Kiln fires them — transforms raw agent outputs into persistent knowledge, durable capabilities, and a system that compounds over time.

Kiln OS is the furnace for agentic intelligence.

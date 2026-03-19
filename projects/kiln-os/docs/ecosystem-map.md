# 22 Collective Ecosystem Map

Last updated: 2026-03-19

Full component inventory of everything in the 22 Collective AI ecosystem. Ground truth for understanding how Kiln OS fits together.

---

## BrickLayer 2.0

**Role in Kiln OS:** Kernel — the autonomous research engine

**What it does:**
- Runs adversarial stress-test campaigns on business models, technical hypotheses, and market questions
- Iterates scenario parameters in `simulate.py`, maps failure boundaries, generates structured findings
- Supports 5 question modes: D1 (quantitative simulation), D2 (regulatory/compliance), D3 (competitive/market), D4 (adversarial scenarios), D5 (sensitivity analysis)
- Maintains a question bank (`questions.md`), findings directory, and synthesis document
- Agent fleet: planner, question-designer-bl2, quantitative-analyst, regulatory-researcher, competitive-analyst, benchmark-engineer, hypothesis-generator, synthesizer

**Key files:**
- `bl/` — Python package (campaign orchestration)
- `template/` — Project template (copy to start a new research project)
- `program.md` — The research loop law (agents follow this exactly)
- `agent_db.json` — Per-agent scores and run history (written by Mortar)

**Status:** Production. Active in multiple research projects (ADBP, Kiln OS ideation).

**Current active work:** Phase 8 — self-improvement loop (Mortar agent, agent_db.json init, write-after-finding)

**GitHub:** Private (22 Collective internal)

---

## Masonry

**Role in Kiln OS:** Package manager / platform layer

**What it does:**
- Platform layer that wraps BL2.0, Recall, Teams, Mnemonics into a unified developer experience
- Provides hooks (session-start, approver, lint-check, observe, stop-guard, etc.) via `settings.json`
- Provides skills (slash commands: /plan, /build, /verify, /fix, /masonry-run, /ui-*)
- Provides agent routing to specialist agents (spec-writer, developer, code-reviewer, etc.)
- Manages autopilot state in `.autopilot/` directory
- Manages UI design system state in `.ui/` directory

**Published package:** `masonry-mcp` v0.1.0 (npm)

**Key components:**
- `~/.claude/CLAUDE.md` — Master context and agent routing table
- `~/.claude/agents/` — Specialist agent definitions
- `~/.claude/skills/` — Skill definitions (slash commands)
- `template/.claude/` — Per-project Masonry configuration
- `masonry-session-start.js` — Boot sequence hook
- `masonry-approver.js` — Auto-approval in build/fix/compose mode
- `masonry-observe.js` — Campaign state observation (async)

**Status:** Production. Installed on developer machines. v0.1.0 published.

**Roadmap:** Enterprise pack (Phase 3), Masonry Pack format, `npx masonry-init` scaffolding.

---

## Recall / Recall 2.0

**Role in Kiln OS:** Memory manager — semantic memory, structured knowledge, IPC backbone

**What it does (v1, current):**
- Self-hosted semantic memory system for Claude Code
- Stores and retrieves memories across sessions via hooks (recall-retrieve.js, observe-edit.js, recall-session-summary.js)
- Storage backends: Qdrant (vector search), Neo4j (graph), PostgreSQL (structured data), Redis (cache)
- Local inference: Ollama on homelab GPU VM (qwen3:14b + qwen3-embedding:0.6b)
- MCP server for tool-based access (recall_search, recall_store, recall_timeline)

**What it will do (v2, planned):**
- SourceTrust scoring: every memory has a source type and trust score
- Retention policy engine: TTL tiers, promotion rules, archival to cold store
- Privacy Router: policy-enforced local-vs-cloud inference routing
- Cross-project semantic search: BL2.0 findings searchable from any Codevv session

**Deployment:**
- VM on homelab (Tailscale: 100.70.195.84:8200)
- Dashboard: React + Vite + Tailwind + DaisyUI
- GitHub: https://github.com/Nerfherder16/System-Recall
- Local dev: `C:/Users/trg16/Dev/Recall`

**Status:** Deployed and operational (v1). Commercial roadmap in progress.

**Stack:** FastAPI + Qdrant + Neo4j + Redis + PostgreSQL + Ollama

---

## Codevv

**Role in Kiln OS:** Shell / collaborative IDE surface

**What it does:**
- Collaborative development platform with real-time sync (Yjs CRDT)
- Voice/video via LiveKit
- Claude integration (AI pair programming in the editor)
- Recall integration (memory sidebar, auto-store from editor)
- Pages: Pipeline (agent orchestration UI), Knowledge Graph (BL2.0 findings visualization), Editor, Chat, Settings

**Stack:** FastAPI (backend) + React 19 + Vite (frontend) + Yjs (CRDT sync) + LiveKit (voice/video) + Claude (AI) + Recall (memory)

**Status:** Active development. Pages exist; some are stubs pending Phase 5 integration.

**GitHub:** Private (22 Collective internal)

**Phase 5 goal:** Pipeline page wired to nvidia-nat; Knowledge Graph fed live from BL2.0 findings.

---

## BrickLayerHub / Kiln

**Role in Kiln OS:** System monitor / campaign management UI

**What it does:**
- Electron desktop app for monitoring BL2.0 research campaigns
- Views: campaign list, question bank, findings, agent status, agent_db scores
- Reads BL2.0 state files: `questions.md`, `results.tsv`, `findings/`, `agent_db.json`, `.autopilot/progress.json`
- Policy: the only UI for campaign monitoring (no web dashboard replacement)

**Status:** Active development. Core campaign views functional.

**Platform:** Electron (cross-platform desktop)

**Roadmap:** Live agent pool view (Phase 2), nvidia-nat health panel (Phase 2), pack browser (Phase 3), token usage dashboard (Phase 7).

---

## NemoClaw Stack (NVIDIA — Integration Target)

**Role in Kiln OS:** Process scheduler (nvidia-nat), device drivers (OpenShell), inference layer (NIM/NeMo/Triton)

### nvidia-nat
- A2A (Agent-to-Agent) protocol dispatch layer
- Agents are addressable network services, not forked processes
- Per-user isolation, agent registry, health checks
- Replaces subprocess.Popen in BL2.0 campaign launch

### OpenShell
- Per-agent YAML sandbox profiles
- Defines filesystem access + network surface per agent type
- Replaces DISABLE_OMC=1 workaround for BL2.0 subprocess isolation

### Privacy Router
- Policy-enforced local-vs-cloud inference routing
- YAML policy file (human-controlled)
- Intercepts inference calls, applies tag-based routing rules
- Audit log of all routing decisions

### NIM (NVIDIA Inference Microservices)
- Swappable model containers (Docker-based)
- Versioned, independently deployable
- Target: host fine-tuned `kiln-research-v1` checkpoint on RTX 3090

### NeMo Framework
- Fine-tuning pipeline for domain model training
- LoRA fine-tuning on `qwen3:14b` base model
- Input: BL2.0 findings exported as JSONL instruction pairs
- Output: domain checkpoint → NIM packaging

### Triton Inference Server
- Backing inference runtime for NIM containers
- GPU-optimized, handles batching and model loading

### Parakeet
- NVIDIA ASR model (speech recognition)
- Target use: Sadie family hub voice input (locally run on GPU VM)

### ACE (Avatar Cloud Engine)
- Voice + embodied agent runtime
- Target use: Sadie as an ACE agent with Recall memory backend

**Status:** All NVIDIA components announced at GTC 2026. Early access pending.

---

## Family Hub / Sadie

**Role in Kiln OS:** Voice interface (potential ACE agent)

**What it does:**
- Voice-first family AI assistant on homelab
- Speaker identification (knows which family member is speaking)
- Semantic memory via mem0 (to be replaced by Recall in Kiln OS integration)
- Voice synthesis via ElevenLabs

**Deployment:** CasaOS (192.168.50.19:7070)

**GitHub:** https://github.com/Nerfherder16/FamilyHub

**Kiln OS integration plan:** Parakeet for ASR (local, RTX 3090) + ACE runtime + Recall as memory backend (replacing mem0). All local — no cloud egress for family conversations (Privacy Router enforced).

---

## 22 Collective

**What it is:** The company/entity that Kiln OS serves. Tim's AI R&D ecosystem.

**Products under development:**
- BrickLayer 2.0 (internal tool → potential commercial offering)
- Masonry (platform layer → enterprise distribution, Phase 3)
- Recall 2.0 (self-hosted memory → commercial product)
- Codevv (collaborative IDE → team product)
- Relay AI Receptionist (AI phone receptionist — on hold, Twilio verification blocked)

**Infrastructure:**
- CasaOS Docker host: 192.168.50.19
- Ollama GPU VM: 192.168.50.62 (RTX 3090)
- Recall VM: 100.70.195.84 (Tailscale)
- Home Assistant: 192.168.50.20
- OPNsense router: 192.168.50.1
- Developer machines: Tim's workstation + casaclaude + proxyclaude (simultaneous Claude Code sessions)

---

## Homelab Infrastructure Summary

| Service | Host | Port | Notes |
|---------|------|------|-------|
| Recall API | 100.70.195.84 (Tailscale) | 8200 | FastAPI + Qdrant + Neo4j |
| Ollama | 192.168.50.62 | 11434 | RTX 3090, qwen3:14b |
| CasaOS | 192.168.50.19 | — | Docker host, primary services |
| Family Hub / Sadie | 192.168.50.19 | 7070 | Voice AI |
| mcp_gateway.py | localhost | 8350 | Planned — Phase 1+ |
| Kiln / BrickLayerHub | local desktop | — | Electron app |
| Codevv | local dev | — | React 19 + FastAPI |

---

## Dependency Graph

```
22 Collective
├── Kiln OS (the system)
│   ├── BrickLayer 2.0 (kernel)
│   │   └── agent_db.json / Mortar (accounting)
│   ├── Masonry (platform layer)
│   │   ├── hooks/ (session, approver, observe, guard)
│   │   └── skills/ (/plan, /build, /research, /ui-*)
│   ├── Recall / Recall 2.0 (memory)
│   │   ├── Qdrant (vectors)
│   │   ├── Neo4j (graph)
│   │   ├── PostgreSQL (structured)
│   │   └── Ollama (local inference)
│   ├── Codevv (shell/IDE)
│   │   ├── Yjs (CRDT sync)
│   │   └── LiveKit (voice/video)
│   ├── Kiln / BrickLayerHub (monitor)
│   └── [Integration targets]
│       ├── nvidia-nat (scheduler)
│       ├── OpenShell (sandboxing)
│       ├── Privacy Router (policy)
│       ├── NIM (model containers)
│       └── NeMo Framework (fine-tuning)
├── Family Hub / Sadie (voice AI)
│   └── [planned] ACE + Parakeet + Recall
└── Relay AI Receptionist (on hold)
```

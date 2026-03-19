# Kiln OS — Roadmap

Last updated: 2026-03-19
Status: IDEATION → PHASE 1 ACTIVE

---

## Phasing Principles

Each phase must deliver standalone value — not just "groundwork." Every phase should leave the system meaningfully better than it found it. Phases do not require the next phase to be useful.

Phase sequencing follows dependency order: you cannot have a shared fleet without sandboxed agents; you cannot distribute what you haven't stabilized; you cannot fine-tune what you haven't accumulated.

---

## Phase 1 — Agent Sandboxing via OpenShell

**Goal:** Replace the `DISABLE_OMC=1` workaround with real per-agent isolation. BL2.0 research agents run in defined sandboxes. Masonry hooks don't bleed into subprocess agents.

**The problem today:** When BrickLayer 2.0 launches a `claude` subprocess to run a research campaign, the parent session's Masonry hooks intercept the subprocess's tool calls. This causes BL2.0's domain-specific agents (quantitative-analyst, regulatory-researcher) to be replaced by Masonry's generic agents. Workaround: set `DISABLE_OMC=1` before launching. This is a hack.

**The fix:** OpenShell YAML profiles define exactly what filesystem paths and network endpoints each agent type can access. The BL2.0 research loop runs inside a `bricklayer-research` profile. Masonry hooks never see it.

### Deliverables

- [ ] Define OpenShell profile YAML schema for BL2.0 agent types
- [ ] Create profiles: `bricklayer-research`, `masonry-build`, `codevv-session`, `kiln-monitor`
- [ ] Wire profiles to BL2.0 campaign launch (`bl/campaign.py`)
- [ ] Retire `DISABLE_OMC=1` from all documentation and launch scripts
- [ ] Update CLAUDE.md to reflect new launch command
- [ ] Test: nested agent session does not trigger Masonry hooks

**Success criteria:** `claude` subprocess for BL2.0 campaign launch requires no environment variable hacks. Masonry hooks fire only in human-interactive sessions.

**Dependencies:** nvidia-nat / OpenShell availability in accessible form (may require early access program)

**Estimated effort:** 1-2 weeks once OpenShell access obtained

---

## Phase 2 — Shared Fleet via nvidia-nat A2A

**Goal:** Replace `subprocess.Popen` in `bl/campaign.py` with nvidia-nat A2A dispatch. Agents become addressable network services, not forked processes. Multiple BL2.0 campaigns can run in parallel without port conflicts or resource collisions.

**The problem today:** BL2.0 campaigns launch `claude` as a subprocess. Multiple parallel campaigns means multiple `claude` processes competing for memory and potentially stomping on shared files. There is no agent registry — no way to know what's running without checking process tables.

**The fix:** nvidia-nat provides an A2A-compliant dispatch layer. Each agent type (quantitative-analyst, regulatory-researcher, synthesizer) is registered as an addressable agent. Campaign orchestrators dispatch to named agents over A2A instead of forking subprocesses. Per-user isolation means Tim's campaign and a future team member's campaign don't interfere.

### Deliverables

- [ ] Deploy nvidia-nat locally or on homelab VM
- [ ] Register BL2.0 agent types with nvidia-nat (YAML agent manifests)
- [ ] Modify `bl/campaign.py` to dispatch via A2A instead of subprocess
- [ ] Add agent health checks to Kiln desktop monitor (show live A2A agent pool)
- [ ] Per-user agent isolation config
- [ ] `mcp_gateway.py` at port 8350 as the MCP client target for nvidia-nat
- [ ] Test: two simultaneous BL2.0 campaigns with no file conflicts

**Success criteria:** Two research campaigns run in parallel. Kiln shows both in active state. No subprocess.Popen calls remain in bl/ package.

**Dependencies:** Phase 1 complete (profiles defined); nvidia-nat access

**Estimated effort:** 3-4 weeks

---

## Phase 3 — Masonry Distribution

**Goal:** Masonry is installable by external teams via a single command. Enterprise pack includes OpenShell profiles, Recall integration, BL2.0 project templates, and the Kiln monitor.

**The problem today:** Masonry is installed by copying files manually. There is no `npm install masonry` that gives you a working agent platform. `masonry-mcp` v0.1.0 exists but is not yet feature-complete for external use.

### Deliverables

- [ ] `masonry-mcp` npm package: publish stable v1.0.0
- [ ] `npx masonry-init` scaffolding command:
  - `--template=research` — BL2.0 research project
  - `--template=build` — Autopilot software build project
  - `--template=enterprise` — Full Kiln OS stack (BL2.0 + Recall + Kiln + nvidia-nat)
- [ ] Masonry Pack format: shareable `.masonry-pack.yml` for agent/skill/profile bundles
- [ ] Masonry Registry: lightweight index of published packs (GitHub Releases initially)
- [ ] Documentation site (or README-first): install → first campaign in 10 minutes
- [ ] Kiln desktop: pack browser and install UI

**Success criteria:** A new 22 Collective developer installs Masonry, runs `npx masonry-init --template=research`, and has a working BL2.0 project in under 10 minutes. No manual file copying.

**Dependencies:** Phase 2 complete (stable agent dispatch); Recall 2.0 design finalized

**Estimated effort:** 6-8 weeks

---

## Phase 4 — Recall 2.0 as OS Memory

**Goal:** Recall becomes the authoritative OS memory layer with retention policy, SourceTrust scoring, and a Privacy Router that enforces local-vs-cloud inference policy. Cross-project semantic search unlocks the compounding knowledge flywheel.

**The problem today:** Recall is a self-hosted memory system that stores and retrieves memories per session. It works. But it lacks:
- SourceTrust: not all memories are equally reliable (agent hallucination vs human correction)
- Retention policy: no TTL or archival policy — memories accumulate without pruning strategy
- Privacy Router: no enforcement layer preventing sensitive memories from going to cloud inference
- Cross-project search: a finding from an ADBP campaign is not surfaced during a Codevv session

### Deliverables

- [ ] **SourceTrust scoring system**
  - Schema: `source_type` (agent/human/observation), `trust_score` (0.0–1.0), `verified_at`
  - Human corrections always score 1.0 and override agent memories on conflict
  - Agent memories start at 0.7, decay without reinforcement
- [ ] **Retention policy engine**
  - TTL tiers: ephemeral (24h), session (7d), project (90d), permanent (no TTL)
  - Promotion rules: memory accessed 3+ times → promote one tier
  - Archival: expired memories move to cold store (PostgreSQL), not deleted
- [ ] **Privacy Router**
  - YAML policy file: `recall-privacy-policy.yml` (human-controlled)
  - Rule engine: tag-based routing (e.g., `tag: medical → local-only`)
  - Enforcement: intercepts Recall query → inference routing before external model call
  - Audit log: all routing decisions logged
- [ ] **Cross-project semantic search**
  - BL2.0 findings automatically tagged with project namespace
  - Recall search crosses namespace boundaries (opt-in per query)
  - Codevv sessions can query BL2.0 findings in context

**Success criteria:** A new BL2.0 campaign on a topic surfaces relevant findings from prior campaigns automatically. Privacy Router blocks a simulated sensitive memory from reaching cloud inference. Human correction to a memory propagates and overrides agent memories.

**Dependencies:** Phase 3 (stable Masonry distribution to propagate Recall 2.0); Recall codebase refactor

**Estimated effort:** 8-10 weeks

---

## Phase 5 — Codevv Integration

**Goal:** Codevv's Pipeline page wires to nvidia-nat for live agent dispatch. The Knowledge Graph page feeds live from BL2.0 findings. Codevv becomes the collaborative command surface for Kiln OS.

**The problem today:** Codevv exists as a collaborative dev platform (Yjs + LiveKit + Claude + React 19) but its agent-related pages are stubs or disconnected. The Pipeline page concept exists but doesn't dispatch real agents. The Knowledge Graph exists but isn't live-fed.

### Deliverables

- [ ] **Pipeline page → nvidia-nat**
  - UI: visual pipeline builder (nodes = agent types, edges = data flow)
  - Backend: translate pipeline definition to nvidia-nat A2A dispatch calls
  - Real-time: Yjs-synced state so multiple users see live agent progress
  - Output: AgentRun and AgentFinding records written to Recall
- [ ] **Knowledge Graph → BL2.0 live feed**
  - Graph nodes: concepts, findings, entities from Recall
  - Edges: causal relationships (from `agentdb_causal-edge`)
  - Real-time updates as new BL2.0 findings arrive
  - Filterable by project, date range, confidence score
- [ ] **Recall sidebar in all Codevv pages**
  - Persistent memory panel: surfaces relevant Recall entries for current file/topic
  - Quick-store: select text → store to Recall with one click
- [ ] **Kiln OS health panel in Codevv**
  - Live status: BL2.0 campaign queue, nvidia-nat agent pool, Recall memory stats

**Success criteria:** A Codevv user opens Pipeline page, defines a BL2.0-style research workflow, runs it, and sees live findings appear in the Knowledge Graph — without touching the terminal.

**Dependencies:** Phase 2 (nvidia-nat), Phase 4 (Recall 2.0 live feed)

**Estimated effort:** 10-12 weeks

---

## Phase 6 — Fine-Tuning Loop

**Goal:** Accumulated BL2.0 findings feed a NeMo Framework fine-tuning pipeline. The result is a narrow domain model (served via NIM) that runs BL2.0 campaigns with higher accuracy and lower token cost than the base model.

**The compounding loop, implemented:**

```
BL2.0 campaigns → Recall findings
Recall findings → NeMo fine-tuning dataset
NeMo training → domain checkpoint
Domain checkpoint → NIM microservice
NIM microservice → BL2.0 campaign model backend
Better model → better campaigns → richer findings → repeat
```

### Deliverables

- [ ] **Findings export pipeline**
  - Script: `bl/export_training_data.py` — exports Recall findings to JSONL format
  - Filter: only high-SourceTrust findings (score >= 0.8), human-verified preferred
  - Format: instruction-following pairs (question + findings + verdict)
- [ ] **NeMo training workflow**
  - Docker Compose stack: NeMo Framework + training scripts
  - Training config: LoRA fine-tuning on `qwen3:14b` base (Ollama-compatible)
  - Output: `kiln-research-v1` checkpoint
- [ ] **NIM deployment**
  - Package checkpoint as NIM microservice
  - Deploy on homelab Ollama VM (RTX 3090)
  - Register with nvidia-nat as `model: kiln-research-v1`
- [ ] **BL2.0 model config**
  - Add `model` field to `questions.md` question bank
  - Campaign launcher selects model per question type (domain-tuned vs. base)
  - Telemetry: compare findings quality between base and fine-tuned runs

**Success criteria:** A BL2.0 campaign using `kiln-research-v1` produces higher-quality findings (as assessed by synthesizer) than the same campaign on `qwen3:14b` base. Measurable metric: findings marked CONFIRMED vs INCONCLUSIVE ratio.

**Dependencies:** Phase 4 (SourceTrust for training data quality); Phase 2 (NIM as dispatch target); sufficient accumulated findings (~500+ high-quality entries in Recall)

**Estimated effort:** 12-16 weeks (training infrastructure setup is the long pole)

---

## Phase 7 — Full AI OS

**Goal:** Fill the identified gaps. Credential vault, service mesh, health monitoring, and resource accounting complete the OS primitive set. Kiln OS is a coherent, monitorable, securable system.

### Deliverables

- [ ] **Credential vault**
  - Self-hosted (Infisical or HashiCorp Vault on homelab)
  - Agent access: nvidia-nat OpenShell profile grants token to secret path, not the secret
  - No secrets in environment variables, code, or config files
  - Kiln monitor: secret rotation alerts
- [ ] **Resource accounting**
  - Per-agent token usage tracking (input + output tokens per campaign + per question)
  - Cost estimation: token count × model rate → USD equivalent
  - Agent efficiency score: findings per 1K tokens
  - Dashboard: Kiln shows token budget, burn rate, projected campaign cost
- [ ] **Service mesh**
  - Inter-service discovery: each Kiln OS component registers with a lightweight service registry
  - Health endpoints: `/health` on every service
  - Automatic retry + circuit breaker for Recall, BL2.0, nvidia-nat connections
- [ ] **Health monitoring agent**
  - Scheduled agent (runs hourly): pings all Kiln OS services
  - Writes health status to Recall (machine-readable)
  - Kiln monitor: live health dashboard
  - Alert: Masonry hook or Recall integration if service is down for > 5 min

**Success criteria:** Kiln OS has a live health dashboard showing all component status. A credential is rotated without touching any code file. A research campaign reports its token cost and efficiency score. A service going offline is detected and surfaced within 5 minutes.

**Dependencies:** All prior phases; homelab Vault deployment

**Estimated effort:** 8-10 weeks

---

## Timeline Overview (Rough)

```
2026 Q1  → Phase 1: Agent sandboxing (starting now)
2026 Q2  → Phase 2: Shared fleet + A2A dispatch
2026 Q2  → Phase 3: Masonry distribution (overlaps Phase 2)
2026 Q3  → Phase 4: Recall 2.0 OS memory
2026 Q4  → Phase 5: Codevv integration
2027 Q1  → Phase 6: Fine-tuning loop
2027 Q2  → Phase 7: Full AI OS
```

Phases 2 and 3 overlap intentionally — distribution work can proceed while A2A is being wired.

---

## What Not To Build

- Do not build a custom A2A implementation. Use nvidia-nat.
- Do not build a custom model serving layer. Use NIM + Ollama.
- Do not build a custom secrets vault. Use Infisical or HashiCorp Vault.
- Do not build a web dashboard for campaign monitoring. Use Kiln.
- Do not attempt fine-tuning before 500+ high-quality Recall entries exist. The dataset is the bottleneck.

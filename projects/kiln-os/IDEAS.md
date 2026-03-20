# Kiln OS — Ideas & Ideation Capture

Last updated: 2026-03-19
Format: live capture — conversational, not formal. Rough edges are features.

---

## The Original Insight

> "You didn't set out to build an OS — you built tools that needed to exist and they converged."

This is the founding observation of Kiln OS. Tim did not decide to build an AI operating system. He decided to build a research engine (BL2.0). Then a memory system (Recall) because agents needed to remember things. Then a platform layer (Masonry) because hooks and skills needed somewhere to live. Then a desktop monitor (Kiln) because campaign visibility mattered. Then a collaborative IDE (Codevv) because pair programming with agents needed a real surface.

Each tool was justified on its own. But laid side by side, they are a kernel, a memory manager, a package manager, a system monitor, and a shell. The OS emerged from necessity, not from design. This is exactly how UNIX happened. Ken Thompson and Dennis Ritchie were not trying to build an OS — they were trying to run Space Travel on underutilized hardware. The OS was the scaffolding that emerged.

The difference: UNIX took years and Bell Labs. This took one obsessive developer and a compounding AI stack.

---

## The NemoClaw Angle

GTC 2026 dropped NemoClaw. At first read it looked like competition — NVIDIA's enterprise agent runtime vs. Tim's stack. Wrong framing.

NemoClaw is the enterprise substrate that Tim's stack is designed to run on top of.

**OpenShell profiles** solve the `DISABLE_OMC=1` problem natively. Right now, launching a BL2.0 claude subprocess from inside a Masonry-enabled session causes hook bleed — Masonry's hooks intercept the subprocess's tool calls and replace BL2.0's domain agents with generic ones. Fix: `DISABLE_OMC=1` environment variable. This is a hack. OpenShell defines exactly what filesystem paths and network endpoints a given agent profile can access. BL2.0 subprocess runs inside `bricklayer-research` profile — Masonry hooks never see it.

**nvidia-nat A2A dispatch** replaces subprocess.Popen entirely. Instead of forking a `claude` process, `bl/campaign.py` dispatches to a named agent over the A2A protocol. Agents are addressable network services, not forked processes. Two BL2.0 campaigns can run simultaneously without stomping on each other. Kiln can show a live agent pool. This is the right abstraction.

**Privacy Router** is exactly the policy enforcement layer Recall 2.0 needs. Policy file: `recall-privacy-policy.yml`. Rule: `tag: medical → local-only`. Rule: `project: ADBP → local-only`. Rule: `confidence: INCONCLUSIVE → cloud allowed`. The router intercepts Recall queries before they touch external model inference and enforces the policy. Human-readable, human-controlled, no silent cloud egress.

**NIM microservices** make the fine-tuning loop executable. Right now, all inference uses base models. The BL2.0 findings dataset is not fed back to improve inference. NIM packages model checkpoints as microservices — swappable, versioned, independently deployed. Fine-tune `qwen3:14b` on accumulated findings, package as `kiln-research-v1`, deploy on the RTX 3090, register with nvidia-nat as an available model backend. The research loop gets faster and cheaper over time.

**The pitch:** 22 Collective's self-hosted agentic research stack is a working prototype of what NemoClaw was designed to enable at enterprise scale. This is a conversation to have with NVIDIA's developer ecosystem team. Not as a customer — as an early integrator.

---

## The Codevv as Command Surface

Codevv was designed as a collaborative dev platform. But look at what the pages map to:

- **Pipeline page** → BL2.0 AgentRun dispatch. The visual pipeline builder is literally a campaign orchestrator. Wire it to nvidia-nat A2A and it IS the campaign launch UI.
- **Knowledge Graph page** → BL2.0 findings, live. Every synthesizer output is a graph node. Every causal edge the agent_db tracks is a graph edge. The Knowledge Graph page is already designed for this.
- **Editor** → Codevv pair programming + BL2.0 code analysis. Agent recommendations inline in the editor.
- **Chat** → Recall-backed conversation. Every exchange adds to the knowledge base.

Codevv is the front-end of Kiln OS. It's not a separate product — it IS the shell. Claude Code is the developer shell. Codevv is the team shell. Same OS, different surfaces.

---

## The Compounding Developer Insight

New developer joins 22 Collective. Traditional onboarding: weeks of docs, pair sessions, tribal knowledge transfer. Most of what they need lives in people's heads, not in any system.

With Kiln OS: new developer installs Masonry, connects to Recall. Their first BL2.0 campaign already knows everything the prior campaigns found. Their first Codevv session surfaces relevant findings from prior research. The Knowledge Graph shows them the current understanding of every domain the company has researched.

They don't start at zero. They start at the ceiling of what the system knows today.

This compounds. Every campaign they run adds to the ceiling. Every correction they make to an agent's wrong answer scores higher in SourceTrust and propagates forward. The system gets smarter with every developer-hour invested.

The institutional knowledge doesn't live in any one person. It lives in Recall. People are interfaces to the OS, not the OS itself.

This is what "AI OS" actually means in practice. Not replacing the developer — compounding the developer.

---

## Sadie on ACE

Sadie is the family hub voice AI. Currently: ElevenLabs voice + speaker ID + basic conversation + some mem0 memory.

The ACE (Avatar Cloud Engine) integration idea: Sadie runs as an ACE agent. Parakeet handles ASR (NVIDIA speech recognition, runs on homelab GPU). Recall handles memory (not mem0 — the full Recall stack with SourceTrust and retention policy). The family's interaction history compounds in Recall. Sadie gets smarter over time, not just within a session.

The difference from the current setup: Sadie knows that Tim usually asks about server health in the morning, family logistics in the evening, creative projects on weekends. She remembers that one of the kids hates their homework topic. She knows the household's schedule patterns.

This is the same compounding loop as the developer scenario — but for a family unit, not a software team.

The privacy angle is strong: everything stays local. Parakeet runs on the GPU VM. Recall runs on the homelab. The Privacy Router blocks any family conversation from reaching cloud inference. Sadie is a fully local AI family member.

---

## The Fine-Tuning Loop Realization

This one took a minute to land properly.

BL2.0 accumulates findings. Every research campaign generates structured outputs: question → methodology → result → verdict (CONFIRMED/REFUTED/INCONCLUSIVE). Over time, this is a dataset of domain-specific reasoning examples.

What if that dataset trained the model that runs the next campaign?

The loop:
1. BL2.0 campaigns generate findings → Recall
2. Export high-SourceTrust findings as JSONL instruction pairs
3. LoRA fine-tune `qwen3:14b` on the dataset (NeMo Framework)
4. Package checkpoint as NIM microservice (`kiln-research-v1`)
5. BL2.0 campaign launcher uses `kiln-research-v1` for research questions
6. Better model → higher CONFIRMED rate, lower INCONCLUSIVE rate → richer findings → better training data → repeat

The model gets better at doing exactly what BL2.0 needs — following the research loop, writing rigorous findings, identifying failure boundaries — because it has been trained on thousands of examples of exactly that.

This is not theoretical. The dataset exists (or will exist at scale). NeMo Framework handles the fine-tuning. NIM handles the serving. The loop is executable.

Timeline blocker: need ~500 high-quality Recall entries before the training dataset is meaningful. That's a few months of consistent BL2.0 campaigns. The accumulation is already happening — just not yet with this in mind.

---

## Missing OS Pieces — The Gaps

During architecture mapping, four OS primitives were missing from the stack:

**1. Credential vault (Keychain equivalent)**

Right now: secrets live in `.env` files, spread across Tim's dev machine, the Recall VM, CasaOS, and potentially Codevv's deployment. No rotation. No audit trail. One compromised machine = all secrets exposed.

Fix: Infisical (self-hosted, beautiful UI) or HashiCorp Vault. OpenShell profile grants an agent access to a Vault path, not the secret itself — the agent gets a temporary token that fetches only what it needs, at the moment it needs it. No secrets in environment variables, period.

**2. Per-agent resource accounting (top/ps equivalent)**

Right now: no idea how many tokens each BL2.0 agent burns per question, per campaign, per project. Cannot optimize. Cannot set budgets. Cannot measure efficiency.

Fix: token tracking in bl/campaign.py → agent_db.json. Add `tokens_in`, `tokens_out`, `cost_usd` fields to every AgentRun record. Kiln monitor shows burn rate. Efficiency metric: CONFIRMED findings per 1K tokens. This metric can guide model selection — use the fine-tuned domain model when it's more efficient than the base model.

**3. Service mesh (IPC routing table)**

Right now: when Recall is down, the Masonry observe hook silently fails. Session memories are lost. There is no retry, no circuit breaker, no fallback, no alert.

Fix: lightweight service registry. Each component registers on startup. Health endpoints (`/health`) on every service. Automatic retry with backoff on transient failures. Circuit breaker: if Recall fails 3× in 30s, stop trying and queue writes locally until it recovers. Not heavy — just enough to make failures visible and recoverable.

**4. Health monitoring daemon (systemd watchdog equivalent)**

Right now: service failures are discovered when Tim notices something is wrong. No proactive monitoring.

Fix: a scheduled Masonry agent that runs hourly, pings all Kiln OS services, writes health status to Recall, and surfaces alerts via Kiln monitor. Simple. Durable. The health data itself goes into Recall — so historical health trends are queryable.

---

## Fragments and Half-Formed Ideas

These don't have homes yet. Capturing anyway.

- **BL2.0 findings as a competitive intelligence product.** The research loop is general-purpose. If 22 Collective can run ADBP stress-tests, it can run stress-tests on any business model. Is there a professional services angle here? "We stress-test your business model with AI — the kind of adversarial scenario analysis your board should be asking for."

- **Masonry Pack marketplace.** Not just an npm registry — a curated index of agent/skill/profile bundles for specific domains. "DeFi research pack" = Solana specialist + regulatory researcher + competitive analyst + questions.md templates for DeFi stress-testing. 22 Collective builds and sells packs. Packs are installed with `npx masonry-install defi-research`.

- **The Kiln name as brand.** Kiln is a strong name for the desktop app. But "Kiln OS" may be the product brand for the full stack when it goes external. The tagline writes itself: "Where agent work becomes durable knowledge."

- **OpenShell profile versioning.** If profiles are YAML files committed to a repo, they can be versioned, reviewed, audited. "The agent's security policy is a PR" is a powerful affordance for enterprise customers.

- **Recall as a product, not just a component.** This is already in motion — Recall is being commercialized. But the Kiln OS framing gives Recall a stronger story: it's not just a memory API — it's the memory manager for an AI OS. Enterprise customers building on nvidia-nat need a memory layer. Recall is that layer, self-hosted, with SourceTrust and retention policy.

- **The "22 Collective developer ceiling" as a recruitment story.** "When you join 22 Collective, you don't start from zero. Every campaign we've ever run is searchable. Every failure boundary we've mapped is in Recall. The system knows more than any individual. Your job is to push the ceiling higher."

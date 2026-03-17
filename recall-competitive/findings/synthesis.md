# Recall Competitive Analysis — Synthesis

**Session date**: 2026-03-15
**Questions completed**: 25 (all waves complete)
**Final competitive score**: 0.509
**Overall verdict**: FAILURE

---

## Executive Summary

Recall is technically the most sophisticated self-hosted AI memory system in production, but it is commercially invisible. The lifecycle pipeline — decay, consolidation, hygiene, GC, and dream consolidation — is unique across all surveyed competitors (mem0, Zep/Graphiti, Letta, Cognee, Hindsight). The causal edge graph schema (CAUSED_BY, SUPPORTS, CONTRADICTS, SUPERSEDES) is validated by the MAGMA paper (arXiv:2601.03236, Jan 2026) as an unimplemented capability across all production systems. Hook-based passive capture is a genuine differentiator. Despite these strengths, Recall scores 0.509 overall — a FAILURE verdict — because three dimensions score at or near critical threshold: no published SDK, no hosted documentation site, and Ollama-only LLM extraction. These three gaps create a wall between Recall's technical capabilities and any developer who discovers it. The path to market leadership is not architectural — it is packaging, documentation, and distribution.

---

## Recall's Confirmed Competitive Moats

1. **Full automated lifecycle pipeline** (`memory_decay`=0.88, `auto_consolidation`=0.85, `memory_hygiene`=0.75)
   - Evidence (Q2.2): Zero competitors implement automatic access-frequency decay. mem0 offers only developer-set TTL expiration (platform-only). Zep/Graphiti uses temporal invalidation (not decay). Letta has zero automatic lifecycle. The December 2025 academic survey confirms "self-optimizing memory management" is an emerging frontier, not table stakes. Recall runs 4+ automated background processes; best competitor runs 1 (TTL expiry).
   - Risk: mem0 is building OpenClaw passive capture plugins (Q4.4). Automatic decay is still unmatched as of March 2026 — but the window is 6-12 months.

2. **Typed causal graph schema** (`graph_relationship_depth`=0.88)
   - Evidence (Q2.4, Q1.4): CAUSED_BY, SUPPORTS, CONTRADICTS, SUPERSEDES typed edges enable structured causal traversal queries that no competitor supports. mem0 uses freeform LLM-extracted strings (no queryable typed traversal). Zep/Graphiti uses generic RELATES_TO default with optional user-defined Pydantic types — causal/epistemic types require explicit user implementation. Letta has no graph. MAGMA paper validates this as an orthogonal unimplemented dimension across all production systems.
   - Risk: Low — no competitor roadmap signals are moving here.

3. **Hook-based passive auto-capture** (`hook_integration_depth`=0.88)
   - Evidence (Q3.2, Q4.4): observe-edit.js captures semantic facts from file diffs with zero user action. session-summary stores session snapshots at Stop. UserPromptSubmit injects memories before every prompt. No competitor has passive capture at the IDE lifecycle level — mem0/Zep/Letta all require explicit `.add()` calls from application code.
   - Risk: MEDIUM-HIGH. mem0 is building OpenClaw auto-capture plugins (Q4.4, v1.0.2-1.0.5). The pattern is moving to ecosystem expectation within 6-12 months. Recall's implementation quality and depth remain an advantage even if exclusivity erodes.

4. **Fully local LLM stack** (architectural)
   - Evidence (Q4.2): Ollama for both extraction (qwen3:14b) and embedding (qwen3-embedding:0.6b). Zero network calls leave the machine during memory operations. No competitor achieves this fully: mem0 self-hosted requires cloud LLM for extraction by default; Zep/Graphiti requires cloud LLM API; Hindsight (MIT) is the closest alternative with Ollama support.
   - Addressable market: 44% of enterprises cite data privacy as top AI adoption barrier (Kong 2025 Enterprise AI Report, Q4.2).

5. **Embedding model quality** (`semantic_retrieval_quality`=0.73)
   - Evidence (Q2.5): qwen3-embedding:0.6b scores 64.33 MTEB Multilingual / 61.83 MTEB English v2 Retrieval — beating BGE-M3 and OpenAI text-embedding-3-large. #1 most-pulled dedicated embedding model on Ollama (1.2M pulls).

---

## Critical Gaps (Blocking Adoption)

1. **No published SDK** — `sdk_ecosystem`=0.05 — Q3.1 — Effort: S (4-6 days)
   - mem0 has 2,034,758 PyPI downloads/month, full CRUD+history+reset, embedded mode (zero infrastructure). Letta and Zep have published SDKs. Recall has zero: developers who find Recall via web search hit the GitHub README and leave because there is no `pip install recall-sdk` to try. This is the single highest-ROI action for competitive position.

2. **No hosted documentation site** — `documentation_quality`=0.10 — Q3.5 — Effort: S (0.5 day setup + 2-3 days content)
   - mem0: Mintlify with API reference, AI search, LLMs.txt, 5-minute quickstart. Zep: Fern with 3-language SDK reference and mem0 migration guide. Letta: Starlight/Astro with "Open in Claude" buttons and per-page AI assistant. Recall: GitHub README only. No hosted site, no API reference, no quickstart, no search.

3. **Ollama-only LLM extraction** — `multi_llm_support`=0.22 — Q3.2 — Effort: M (1-2 weeks for LiteLLM)
   - mem0 supports 15 named providers + 100+ via LiteLLM. Letta supports 10+ BYOK providers. Recall is hardcoded to Ollama. Users who want cloud LLM extraction (faster, no GPU required) cannot use Recall. The MCP layer is already IDE-agnostic — the extraction pipeline gap is the remaining constraint.

4. **No hybrid retrieval** — `hybrid_retrieval`=0.10 — Q1.5 — Effort: M (2-3 days BM42)
   - mem0 shipped hybrid search (Jan 2026, changelog). Graphiti RFC for vector overlay in progress. Recall remains pure vector. While BM42 benefit for short-text memories is moderate (5-15% recall improvement per Q1.5), having no hybrid retrieval becomes a visible differentiator against mem0's "hybrid memory search" marketing.

5. **No import/export** — `import_export`=0.25 — (baseline finding) — Effort: M (3-5 days)
   - No bulk export/import tools. No standardized format. Users cannot migrate from mem0, Zep, or Letta to Recall, and cannot leave Recall for alternatives. This creates lock-in risk (negative) without any positive lock-in value.

---

## Competitive Gaps (Causing Switching)

1. **Self-hosting complexity** — `self_hosting_simplicity`=0.30 — Q3.3
   - 5-6 services + GPU hardware vs mem0's 0 (embedded) or 3 (full stack) vs Letta's 1 container. The community is explicit: "too many memory implementations, none just works" (r/LocalLLaMA, Q4.2). Recall's complexity is real and penalizes first-time discovery.

2. **No temporal search** — (Q4.4)
   - mem0 shipped temporal search filtering (Feb 28, 2026). Graphiti has always had dual-timestamp retrieval. Recall has no time-range query capability. Users expect "what happened last week?" to work.

3. **Multi-user isolation gap** — `multi_user_support`=0.35 — Q3.4
   - user_id field exists but no RTBF endpoint, no user management UI, no agent_id isolation field. mem0 has 4-dimension isolation (user+agent+app+run). The gap matters for multi-agent Claude Code setups and household deployments.

4. **Dedup threshold undocumented** — `memory_dedup_effectiveness`=0.65 — Q2.3
   - Recall's cosine similarity threshold is not published or configurable. mem0 documents threshold guidelines by use case (0.7 for general NL, 0.85-0.9 for structured data). Recall's approach is structurally sound but invisible to users.

5. **Write reliability audit needed** — (Q4.3)
   - mem0's #1 abandonment cause: 80% silent write failure rate in some configurations. Recall's write pipeline must be explicitly audited for silent failures (Qdrant unreachable, Ollama embedding timeout, hook failures). This is a risk, not a confirmed gap.

---

## Strategic Roadmap

### Tier 0 — Quick Wins (< 1 week each)

- [ ] **Deploy Mintlify docs site** from existing markdown — half a day, free tier — closes Q3.5 — `documentation_quality` 0.10 → 0.50
- [ ] **Upgrade qwen3-embedding to 4b model** — 0.5 day config change — closes Q2.5 gap — +6.6 MTEB points, `semantic_retrieval_quality` 0.73 → 0.82
- [ ] **Write cross-tool MCP documentation** (Cursor `.cursor/mcp.json`, Windsurf `mcp_config.json`) — 1-2 days, zero code — closes Q3.2 partial gap — captures multi-IDE users immediately
- [ ] **Add API quickstart page** (10-line store/search example) — 1 day — closes Q3.5 partial — `documentation_quality` → 0.60
- [ ] **Publish LLMs.txt** — 0.5 day — AI coding tool discovery signal, signals project maturity

### Tier 1 — High Impact (1-4 weeks each)

- [ ] **Publish `recall-sdk` to PyPI** — 4-6 days — closes Q3.1 — `sdk_ecosystem` 0.05 → 0.45 — thin httpx wrapper around existing REST API, sync + async, Pydantic models
- [ ] **Single docker-compose.yml for full stack** — 2-3 days — closes Q3.3 partial — `self_hosting_simplicity` 0.30 → 0.50 — target: repo clone to first memory stored in < 10 minutes
- [ ] **Architecture decision hook** (extend observe-edit.js to detect decision language) — 2-3 days — unique Claude Code feature, no competitor has it — `hook_integration_depth` 0.88 → 0.92
- [ ] **Write confirmation UX** (session-end "N memories stored this session" summary) — 1 day — addresses #1 abandonment cause across all competitors (Q4.3)
- [ ] **Temporal search parameters** (since/before date-range on recall_search) — 1-2 weeks — closes Q4.4 gap — timestamps already stored, metadata filter only
- [ ] **Write reliability audit** — 1 week — verify silent failure scenarios, add error surfacing — must precede SDK launch

### Tier 2 — Architectural Improvements (1-3 months)

- [ ] **Cross-encoder reranker** (BGE MiniLM-L6-v2 CPU, < 150MB) — 2-3 days engineering — `reranking_quality` 0.42 → 0.70 — highest retrieval ROI per Q5.1
- [ ] **LiteLLM extraction provider** — 1-2 weeks — `multi_llm_support` 0.20 → 0.60 — users with cloud API keys can use Recall without Ollama GPU
- [ ] **BM42 hybrid retrieval** via Qdrant sparse index — 2-3 days — `hybrid_retrieval` 0.10 → 0.50 — closes marketing gap vs mem0 hybrid search
- [ ] **Import/export JSON + MemGPT/mem0 migration** — 3-5 days — `import_export` 0.25 → 0.65 — closes Zep's mem0 migration guide advantage
- [ ] **Graph-augmented query expansion** via Neo4j 1-hop BFS — 1 week — `query_understanding` 0.45 → 0.65 — leverages existing graph moat for retrieval quality
- [ ] **agent_id isolation field** — 2-3 days — closes multi-agent bleed (documented openclaw issue #3998) — `multi_user_support` 0.35 → 0.55
- [ ] **Temporal validity windows** (valid_from/valid_until on Memory schema) — 2-4 days — closes Graphiti's one genuine architectural advantage over Recall

### Tier 3 — Strategic Bets (3+ months)

- [ ] **VS Code extension adapter** for Cursor/Windsurf passive capture — 2-3 weeks — extends hook moat beyond Claude Code users; ~4M Cursor users
- [ ] **Embedded mode** (SQLite + local Qdrant, zero server infrastructure) — 2-4 weeks — closes mem0's biggest adoption advantage; single-file install
- [ ] **"auto-CLAUDE.md" generator** — export high-importance arch decisions to CLAUDE.md/AGENTS.md — Claude Code-specific killer feature, no competitor can replicate
- [ ] **Entity-centric dedup** in consolidation pipeline — 1 week — major quality improvement at 1000+ memories
- [ ] **Explicit contradiction resolution** via Ollama adjudication — 3-5 days — makes CONTRADICTS edge actionable; first production system to do this
- [ ] **Privacy certification and marketing** — "zero data leaves your machine" verification + documentation — strategic positioning for enterprise privacy segment

---

## Final Competitive Score by Category

| Category | Recall Score | Leader Score | Gap | Status |
|----------|-------------|--------------|-----|--------|
| Retrieval | 0.47 | 0.71 (mem0 Platform) | -0.24 | WARNING — embedding strong, no hybrid/reranker |
| Lifecycle | 0.82 | 0.57 (none — Recall leads) | **+0.25** | HEALTHY — Recall is best-in-class |
| Developer Experience | 0.37 | 0.76 (mem0) | -0.39 | FAILURE — SDK/docs/multi-LLM critical gaps |
| Operations | 0.47 | 0.74 (Letta) | -0.27 | WARNING — self-hosting complexity |
| Product | 0.42 | 0.66 (mem0) | -0.24 | WARNING — import/export missing |
| **Overall** | **0.509** | **~0.68 (mem0)** | **-0.17** | **FAILURE** |

---

## Projected Scores After Roadmap Phases

| Phase | Scope | Projected Score | Verdict |
|-------|-------|----------------|---------|
| Current | Baseline research complete | 0.509 | FAILURE |
| After Tier 0 | Docs site + embedding upgrade + MCP docs | ~0.555 | FAILURE (gaps closing) |
| After Tier 1 | SDK + docker-compose + temporal search | ~0.610 | WARNING |
| After Tier 2 | Hybrid retrieval + cross-encoder + LiteLLM + import/export | ~0.685 | HEALTHY |
| After Tier 3 | VS Code hooks + embedded mode + entity dedup | ~0.760 | HEALTHY (market leadership) |

---

## Residual Risks After Tier 0-1 Roadmap

1. **Passive capture moat erosion** — mem0 is actively building auto-capture for OpenClaw agent framework. Within 6-12 months, passive capture will be an ecosystem expectation. Recall's moat becomes implementation quality (depth, reliability) not exclusivity.

2. **Letta sleep-time compute** — Recall has no equivalent to background agents that rewrite memory state during idle time. This is an architectural capability class Recall does not implement. Low urgency (Letta Code is early-stage) but a 12-month risk.

3. **Temporal search gap** — Both mem0 (Jan-Feb 2026) and Graphiti have time-aware retrieval. Until Recall ships temporal search, it will lose users who ask "what happened last week?" and get no results.

4. **Write reliability** — mem0's #1 abandonment cause is silent write failures (80% loss rate in some configs). Recall's write pipeline has not been publicly audited. This must be verified before any user-facing launch.

5. **Competitive compression of dev experience gap** — Recall's dev experience score (0.37) is in FAILURE territory. Even after Phase 1 improvements, it will reach ~0.55 — still below the 0.65 WARNING threshold. Closing the full gap requires the Tier 2 work (LiteLLM, hybrid retrieval, import/export).

---

## Key Decision for Tim

**The core question**: Is Recall a personal homelab tool or a publicly useful open-source project?

If personal tool: the current architecture is excellent. Continue deepening the lifecycle pipeline and causal graph schema. No urgency on SDK/docs.

If public project: the Tier 0 actions (Mintlify docs + API quickstart + LLMs.txt) take 2-3 days and are the minimum to signal that the project is alive and usable. The Tier 1 SDK is a week of work and would make Recall discoverable and installable. These two actions together transform the project's external perception without changing any core architecture.

The research strongly suggests the latter path: the niche (privacy-first, self-hosted, Claude Code-integrated, full lifecycle) is underserved, validated by community demand, and Recall is architecturally the best-positioned system to own it. The gap is packaging.

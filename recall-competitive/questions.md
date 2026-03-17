# Recall Competitive Analysis — Question Bank

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

Score impact guide: After each finding, update the relevant SCENARIO_PARAMETERS in simulate.py.

---

## Wave 1: Feature Gap Analysis — Primary Competitors

---

## Q1.1 [COMPETITOR] mem0 architecture and feature parity
**Domain**: D3 — Competitive
**Status**: DONE
**Question**: What is mem0's current architecture, feature set, and integration surface? How does its dual-layer memory approach (vector + graph optional) compare to Recall's Qdrant + Neo4j dual-store? Does mem0's Python/JS SDK make it meaningfully easier to adopt than Recall's hook-only integration?
**Research targets**: mem0ai/mem0 GitHub, mem0.ai docs, PyPI package, recent changelog
**Score dimensions affected**: `sdk_ecosystem`, `api_surface_completeness`, `multi_llm_support`, `semantic_retrieval_quality`
**Verdict threshold**:
- FAILURE: mem0 has SDK + multi-LLM support + graph memory AND is simpler to deploy
- WARNING: mem0 SDK covers most use cases Recall doesn't; gap is significant
- HEALTHY: Recall's lifecycle pipeline and hook depth offset mem0's SDK advantage

---

## Q1.2 [COMPETITOR] Zep temporal memory and session management
**Domain**: D3 — Competitive
**Status**: DONE
**Question**: What is Zep's current feature set for temporal memory, session management, and fact extraction? How does Zep's "knowledge graph" implementation compare to Recall's Neo4j graph? Does Zep have memory decay/lifecycle management comparable to Recall's pipeline?
**Research targets**: getzep.com, github.com/getzep, Zep Cloud vs Zep CE comparison
**Score dimensions affected**: `graph_relationship_depth`, `memory_decay`, `auto_consolidation`, `multi_user_support`
**Verdict threshold**:
- FAILURE: Zep has graph memory + decay + multi-tenant AND a cleaner developer story
- WARNING: Zep's graph or lifecycle is comparable and its developer story is better
- HEALTHY: Recall's lifecycle pipeline is demonstrably more sophisticated

---

## Q1.3 [COMPETITOR] Letta/MemGPT hierarchical memory tiers
**Domain**: D3 — Competitive
**Status**: DONE
**Question**: What does Letta (formerly MemGPT) offer in its current form? How does its OS-inspired hierarchical memory (in-context, archival, recall) map to Recall's architecture? Does Letta have automatic memory lifecycle management or is it agent-controlled?
**Research targets**: letta.ai, github.com/letta-ai/letta, recent release notes
**Score dimensions affected**: `graph_relationship_depth`, `auto_consolidation`, `sdk_ecosystem`
**Verdict threshold**:
- FAILURE: Letta has richer memory hierarchy AND better SDK/docs AND is easier to self-host
- WARNING: Letta's explicit memory tiers give agents more control; Recall has no equivalent
- HEALTHY: Recall's automatic pipeline is more practical for non-agent use cases

---

## Q1.4 [COMPETITOR] Does any competitor combine vector + graph the way Recall does?
**Domain**: D3 — Competitive
**Status**: DONE
**Question**: Survey the competitive landscape for systems that use both a vector store and a knowledge graph for memory. Who does this? How do their graph schemas compare to Recall's Neo4j model (RELATED_TO, causal edges, domain partitioning)? Is the dual-store approach a genuine differentiator or table stakes?
**Research targets**: mem0 graph mode docs, Zep graph docs, any academic or industry implementations
**Score dimensions affected**: `graph_relationship_depth`, `semantic_retrieval_quality`
**Verdict threshold**:
- FAILURE: Multiple well-resourced competitors do dual-store with comparable sophistication
- WARNING: One or two competitors have it but Recall's schema is more developed
- HEALTHY: Dual-store + causal edges is genuinely rare; Recall is the most sophisticated

---

## Q1.5 [ARCHITECTURE] Hybrid retrieval — does Recall need BM25?
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: What retrieval architectures do leading memory systems use in 2025? Who uses hybrid BM25+vector? What measurable quality improvements does hybrid retrieval provide for memory systems specifically (vs general RAG)? Is the absence of BM25 a meaningful regression for Recall's use case (short fact strings, not long documents)?
**Research targets**: Recent RAG/memory retrieval papers, mem0 retrieval docs, Qdrant sparse+dense hybrid docs
**Score dimensions affected**: `hybrid_retrieval`, `semantic_retrieval_quality`
**Verdict threshold**:
- FAILURE: Hybrid retrieval is standard in all serious competitors AND provides >20% recall improvement for short-text memory
- WARNING: Hybrid is common but benefit for short factual memories is unclear
- HEALTHY: For sub-200-char facts, pure vector is competitive; hybrid is over-engineering

---

## Wave 2: Architecture & Design Patterns

---

## Q2.1 [ARCHITECTURE] Retrieval quality techniques in leading memory systems
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: What retrieval quality techniques (reranking, query expansion, MMR, contextual compression, HyDE) do leading memory systems use in 2025? How does Recall's sklearn reranker compare to LLM-based reranking used by competitors? What is the quality delta and is it worth the latency cost?
**Research targets**: mem0 retrieval architecture, Zep retrieval docs, recent memory/RAG benchmarks
**Score dimensions affected**: `reranking_quality`, `query_understanding`
**Verdict threshold**:
- FAILURE: LLM reranking is standard in competitors and provides >30% quality improvement
- WARNING: LLM reranking is common but latency tradeoff is real; Recall's sklearn approach may be acceptable
- HEALTHY: Recall's reranker is competitive; LLM reranking overhead not justified for homelab

---

## Q2.2 [ARCHITECTURE] Memory lifecycle — how do competitors handle aging and pruning?
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: What lifecycle management do mem0, Zep, Letta, and other serious memory systems implement? Do any have automatic decay, consolidation, or hygiene pipelines comparable to Recall's? Is Recall's multi-stage lifecycle (decay → consolidation → hygiene → GC) genuinely differentiated or are competitors catching up?
**Research targets**: mem0 memory management docs, Zep temporal memory, Letta archival memory
**Score dimensions affected**: `memory_decay`, `auto_consolidation`, `memory_hygiene`
**Verdict threshold**:
- FAILURE: Multiple competitors have equivalent lifecycle management
- WARNING: One competitor has partial lifecycle; Recall still more complete but gap narrowing
- HEALTHY: Recall's full pipeline (decay+consolidation+hygiene+GC+dream) is uniquely sophisticated

---

## Q2.3 [ARCHITECTURE] Semantic deduplication — best practices and benchmarks
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: What deduplication strategies do memory systems use? Is Recall's dual approach (content hash + cosine similarity threshold) standard? Are there better approaches — entity-centric dedup, clustering-based merge, LLM-judged duplicates? What threshold values do production systems use?
**Research targets**: mem0 dedup docs, academic memory dedup papers, production RAG dedup patterns
**Score dimensions affected**: `memory_dedup_effectiveness`
**Verdict threshold**:
- FAILURE: Recall's dedup approach is demonstrably inferior (misses near-duplicates that matter)
- WARNING: Better approaches exist but are not widely deployed; Recall's approach is acceptable
- HEALTHY: Content hash + cosine is the standard; Recall's implementation is on par

---

## Q2.4 [ARCHITECTURE] Knowledge graph schemas in memory systems
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: How do competitors structure their knowledge graph schemas? What relationship types do mem0's graph mode, Zep's entity graph, and Letta's archival memory use? How does Recall's schema (RELATED_TO, CAUSED_BY, SUPPORTS, CONTRADICTS, SUPERSEDES, domain partitioning) compare in expressiveness and query utility?
**Research targets**: mem0 graph docs, Zep entity extraction docs, Neo4j memory pattern examples
**Score dimensions affected**: `graph_relationship_depth`
**Verdict threshold**:
- FAILURE: Competitor graph schemas are more expressive and better queryable than Recall's
- WARNING: Comparable schemas but competitors have better graph query tooling or visualization
- HEALTHY: Recall's causal edge types are more expressive than any competitor surveyed

---

## Q2.5 [ARCHITECTURE] Embedding models — what are leaders using in 2025?
**Domain**: D1 — Architecture
**Status**: DONE
**Question**: What embedding models do leading memory systems use or recommend in 2025? How does qwen3-embedding:0.6b compare to models like text-embedding-3-small, nomic-embed-text, mxbai-embed-large? Is there a meaningful quality gap for factual memory retrieval? What does self-hosted embedding look like at the competitive frontier?
**Research targets**: MTEB leaderboard, Ollama model library, mem0 embedding model docs, recent embedding benchmarks
**Score dimensions affected**: `semantic_retrieval_quality`
**Verdict threshold**:
- FAILURE: qwen3-embedding:0.6b is significantly below best available self-hosted models
- WARNING: Better models exist but the delta is modest; swap is low-effort improvement
- HEALTHY: qwen3-embedding is competitive for factual short-text retrieval

---

## Wave 3: Developer Experience

---

## Q3.1 [DEVEX] SDK landscape — what do mem0, Zep, and Letta expose?
**Domain**: D4 — Integration
**Status**: DONE
**Question**: What SDKs, client libraries, and integration patterns do the top memory systems provide? What does a typical mem0 integration look like in 10 lines of Python? How does Recall's integration story (hook config + HTTP) compare in friction? What would a minimal Recall Python SDK need to expose to be competitive?
**Research targets**: mem0 PyPI, Zep Python client, Letta SDK, integration examples in each README
**Score dimensions affected**: `sdk_ecosystem`, `documentation_quality`
**Verdict threshold**:
- FAILURE: SDK gap makes Recall unusable for developers who want to integrate programmatically
- WARNING: SDK absence is a significant friction point but hook integration partially compensates
- HEALTHY: Recall's hook-first integration is differentiated; SDK would be additive not essential

---

## Q3.2 [DEVEX] Multi-LLM support — how locked in are competitors?
**Domain**: D4 — Integration
**Status**: DONE
**Question**: How do mem0, Zep, and Letta handle multi-LLM support? Is LLM-agnosticism a genuine feature or marketing? Does Recall's deep Claude Code hook integration represent a trade-off (depth vs breadth) or a genuine moat? What would it take for Recall to support Cursor, Windsurf, or other AI coding tools?
**Research targets**: mem0 LLM provider docs, Zep LLM config, any Cursor/Windsurf memory integrations
**Score dimensions affected**: `multi_llm_support`, `hook_integration_depth`
**Verdict threshold**:
- FAILURE: Claude-only lock-in is actively limiting adoption; competitors support 10+ LLMs trivially
- WARNING: Multi-LLM support is achievable for Recall with moderate effort; gap is real but bridgeable
- HEALTHY: Recall's Claude Code depth is a genuine moat; breadth can be added incrementally

---

## Q3.3 [DEVEX] Self-hosting complexity — how does Recall compare?
**Domain**: D4 — Integration
**Status**: DONE
**Question**: What is the minimum infrastructure required to self-host mem0, Zep CE, and Letta? Compare against Recall's 4-service + Ollama requirement. What does a docker-compose.yml for each look like? Is Recall's complexity a meaningful barrier or acceptable given its capability level?
**Research targets**: mem0 self-host docs, Zep CE docker-compose, Letta self-host guide
**Score dimensions affected**: `self_hosting_simplicity`
**Verdict threshold**:
- FAILURE: Competitors achieve comparable capability with 1-2 services; Recall's 5-service stack is a hard barrier
- WARNING: Recall requires more services but complexity is documented and manageable
- HEALTHY: Recall's complexity is justified by its capability level; competitors are simpler but less capable

---

## Q3.4 [DEVEX] Multi-user and multi-tenant isolation
**Domain**: D4 — Integration
**Status**: DONE
**Question**: How do competitors handle multi-user memory isolation? What does mem0's user management look like? Does Zep have workspace/project separation? How does Recall's user_id field compare in practice? Is multi-user isolation a feature that Recall's target users (homelab, single-user) actually need?
**Research targets**: mem0 user management docs, Zep organization features, Letta multi-user support
**Score dimensions affected**: `multi_user_support`
**Verdict threshold**:
- FAILURE: Multi-tenant isolation in competitors is enterprise-grade; Recall is single-user only in practice
- WARNING: Recall's user_id field exists but lacks UI/API surface for real multi-user use
- HEALTHY: Single-user homelab use case is Recall's target; multi-user is out of scope currently

---

## Q3.5 [DEVEX] Documentation quality — what does best-in-class look like?
**Domain**: D4 — Integration
**Status**: DONE
**Question**: What does the documentation for mem0, Zep, and Letta look like? Do they have docs sites, API references, quickstart guides, integration examples? What is the minimum documentation that would make Recall's REST API usable without reading source code?
**Research targets**: docs.mem0.ai, docs.getzep.com, docs.letta.ai, their GitHub wikis
**Score dimensions affected**: `documentation_quality`
**Verdict threshold**:
- FAILURE: Competitor docs are so much better that developers won't even try Recall
- WARNING: Gap is significant but fixable; Recall's docs need a proper site and API reference
- HEALTHY: README-driven docs are acceptable for Recall's target audience (technical self-hosters)

---

## Wave 4: Market Positioning

---

## Q4.1 [MARKET] Current AI memory system landscape in 2025
**Domain**: D3 — Market
**Status**: COMPLETE
**Question**: Who are the current key players in AI memory / persistent context systems as of early 2025? What categories have emerged (agent memory, coding assistant memory, personal knowledge, enterprise RAG)? Where does Recall sit in this taxonomy? Are there any recent entrants that weren't on the radar at mid-2024?
**Research targets**: recent ProductHunt launches, GitHub trending, HN discussions on AI memory, a16z/YC portfolio
**Score dimensions affected**: context only, no direct score change
**Verdict threshold**:
- FAILURE: The market has converged on a standard that Recall is structurally unable to compete with
- WARNING: New entrants have closed gaps Recall held; competitive window is narrowing
- HEALTHY: Recall's niche (deep hook integration + full lifecycle + self-hosted) remains defensible

---

## Q4.2 [MARKET] Underserved use cases — what does nobody do well?
**Domain**: D3 — Market
**Status**: COMPLETE
**Question**: What use cases are consistently underserved across all existing memory systems? Where do developers complain that nothing works well? What niches exist that Recall could own — especially in the self-hosted, privacy-first, coding-tool-integrated segment?
**Research targets**: HN "Ask HN" threads on memory, Reddit r/LocalLLaMA, GitHub issues on mem0/Zep/Letta
**Score dimensions affected**: context for strategic positioning
**Verdict threshold**:
- FAILURE: No underserved niches exist; the market is commoditized and Recall has no moat
- WARNING: Niches exist but are small or require Recall to change direction significantly
- HEALTHY: Clear underserved niches exist that Recall's current architecture is well-positioned to own

---

## Q4.3 [MARKET] What do users complain about with existing memory systems?
**Domain**: D3 — Market
**Status**: DONE
**Question**: What are the top user complaints about mem0, Zep, Letta, and similar systems? What does "memory not surfacing at the right time" look like in practice? What failures cause users to abandon these systems? Are any of Recall's current weaknesses (complexity, no SDK) actually blocking factors for its target users?
**Research targets**: mem0 GitHub issues, Zep Discord/GitHub issues, r/LocalLLaMA, HN threads
**Score dimensions affected**: `memory_discoverability`, `retrieval quality scores`
**Verdict threshold**:
- FAILURE: Recall has the same failure modes that cause users to abandon competitors
- WARNING: Recall shares some pain points but its pipeline addresses the most common ones
- HEALTHY: Recall's lifecycle pipeline directly solves the most common complaints

---

## Q4.4 [MARKET] What features are being heavily invested in by leading memory systems?
**Domain**: D3 — Market
**Status**: DONE
**Question**: What features are mem0, Zep, and Letta actively building or recently shipped in 2024-2025? What does the roadmap signal about where memory systems are heading? Are there feature areas where Recall is about to be lapped even on its current strengths?
**Research targets**: mem0 changelog, Zep release notes, Letta blog, their GitHub commit history
**Score dimensions affected**: context for roadmap prioritization
**Verdict threshold**:
- FAILURE: Competitors are shipping Recall's core differentiators (lifecycle, graph) faster than Recall can maintain them
- WARNING: Competitors are closing the gap on lifecycle/graph but Recall still leads
- HEALTHY: Competitors are investing in different areas; Recall's core differentiators remain safe

---

## Wave 5: Strategic Improvements

---

## Q5.1 [STRATEGY] What architectural changes would most improve retrieval quality?
**Domain**: D5 — Strategic
**Status**: DONE
**Question**: Given the research findings from Waves 1-4, what specific architectural changes would most improve Recall's retrieval quality? Rank by impact vs effort. Consider: better embedding model, hybrid retrieval, LLM reranking, query expansion, HyDE, contextual compression. What is the ROI for Recall's homelab context?
**Research targets**: synthesis of prior findings + Qdrant hybrid search docs
**Score dimensions affected**: `semantic_retrieval_quality`, `hybrid_retrieval`, `reranking_quality`, `query_understanding`
**Verdict threshold**:
- FAILURE: Multiple high-impact low-effort improvements exist that Recall has ignored
- WARNING: Some improvements are worth making; prioritization is the main challenge
- HEALTHY: Recall's retrieval quality is already near the ceiling for its use case

---

## Q5.2 [STRATEGY] Minimum SDK to be developer-competitive
**Domain**: D5 — Strategic
**Status**: DONE
**Question**: What is the minimum viable Python package that would make Recall competitive for developers who want programmatic access? What methods must exist (store, search, retrieve, delete)? What authentication pattern? What would a 10-line integration example look like? Is this a weekend project or a significant effort?
**Research targets**: synthesis of Q3.1 findings + mem0 SDK as reference design
**Score dimensions affected**: `sdk_ecosystem`, `documentation_quality`
**Verdict threshold**:
- FAILURE: Minimum viable SDK is too complex to build without rearchitecting the API
- WARNING: SDK is buildable but requires significant documentation and API cleanup first
- HEALTHY: A thin wrapper around the existing REST API is all that is needed

---

## Q5.3 [STRATEGY] What would make Recall best-in-class for Claude Code users specifically?
**Domain**: D5 — Strategic
**Status**: DONE
**Question**: For users whose primary use case is Claude Code session memory — not general LLM memory — what would make Recall the unambiguous best choice? What do Claude Code users specifically need that competitors ignore? What is Recall uniquely positioned to build that mem0/Zep cannot easily replicate?
**Research targets**: Claude Code community discussions, MCP ecosystem, Claude hooks documentation
**Score dimensions affected**: `hook_integration_depth`, `memory_discoverability`
**Verdict threshold**:
- FAILURE: Claude Code users can get equivalent results from simpler competitors
- WARNING: Recall's Claude Code integration is better but not enough to drive strong preference
- HEALTHY: Recall is so much better for Claude Code users that it's the obvious choice in this niche

---

## Q5.4 [STRATEGY] How could Recall's lifecycle pipeline be improved based on competitor patterns?
**Domain**: D5 — Strategic
**Status**: DONE
**Question**: Given what we now know about competitor lifecycle management, what specific improvements would have the highest impact on Recall's memory quality over time? Consider: better importance scoring signals, smarter consolidation triggers, entity-level dedup, memory versioning, contradiction resolution improvements.
**Research targets**: synthesis of Q2.2, Q2.3 findings
**Score dimensions affected**: `importance_scoring`, `auto_consolidation`, `memory_hygiene`
**Verdict threshold**:
- FAILURE: Recall's lifecycle is sophisticated but has fundamental design flaws competitors have solved
- WARNING: Specific improvements would have high impact; Recall's pipeline is good but not optimal
- HEALTHY: Recall's lifecycle pipeline is best-in-class with only minor tuning opportunities

---

## Q5.5 [STRATEGY] Recall strategic roadmap — what is the path to market leadership?
**Domain**: D5 — Strategic
**Status**: DONE
**Question**: Synthesizing all findings from this session: what is the prioritized roadmap that would make Recall the unambiguously best self-hosted AI memory system? Rank improvements by: (1) impact on competitive position, (2) effort required, (3) alignment with Recall's homelab/privacy-first identity. Produce a tiered action plan.
**Research targets**: synthesis of all prior findings
**Score dimensions affected**: all dimensions (final synthesis run)
**Verdict threshold**:
- FAILURE: The gap to market leaders is too large to close without a full rewrite
- WARNING: Significant work needed but a clear path exists
- HEALTHY: Recall can reach market leadership with focused incremental improvements

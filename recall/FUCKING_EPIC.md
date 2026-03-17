This is the more interesting question. Let me go deep on three layers: what no one is doing architecturally, what research exists that hasn't been applied, and how you     
  actually make the research system stop anchoring to existing ideas.
                                                                                                                                                                                ---
  Layer 1: What No One Is Doing Architecturally                                                                                                                               
   
  The fundamental problem with every AI memory system

  Every production memory system — Recall included — is built from general-purpose components that were designed for completely different workloads:

  - Qdrant was built for document retrieval (immutable, static corpus)
  - Neo4j was built for business relationship graphs (stable schema, low mutation rate)
  - Redis was built for session caching (TTL-based, no semantic content)
  - PostgreSQL was built for transactional records (ACID, not probabilistic)

  None of these were designed for a workload that is:
  - High-mutation (importance scores change constantly)
  - Temporally decaying (old data should structurally move toward irrelevance)
  - Access-pattern-aware (hot memories should physically live in faster storage)
  - Semantically self-organizing (related memories should co-locate)
  - Stateful across queries (what you retrieved last affects what you need next)

  This is the architectural moat: a storage primitive built from scratch for memory semantics rather than assembled from general-purpose tools.

  ---
  What a purpose-built memory store would look like

  Tiered memory storage — like CPU cache, not like a database

  L1 — Working set (in-process, ~microsecond access)
       Hot memories: accessed in last N sessions
       Size: ~500 memories, fits in VRAM alongside the LLM

  L2 — Warm store (local mmap, ~millisecond access)
       Recent memories: accessed in last 30 days
       Size: ~50k memories

  L3 — Cold store (compressed on disk, ~10ms access)
       Aging memories: decay score below threshold
       Eviction policy: importance × recency curve

  GC  — Tombstone pool
       Soft-deleted, awaiting hard delete

  The decay curve IS the eviction policy. You don't need a separate lifecycle pipeline if memory importance directly drives physical storage tier. Today Recall runs decay as 
  a scheduled job separate from the store. In a purpose-built system, decay is storage architecture.

  No one has built this. LSM trees (used in RocksDB, LevelDB, Cassandra) use tiered compaction for write-heavy workloads. The principle is identical but nobody applied it to 
  semantic memory with importance-weighted eviction.

  ---
  Fused vector + graph in a single storage unit

  Your own Recall notes surface this: "Qdrant is source of truth, Neo4j is synchronized to match." That sync overhead is a symptom of a deeper architectural mistake — the    
  vector and the graph are separate systems that happen to reference the same memories.

  In a memory-native store, every memory node is:

  MemoryNode {
    id: uuid
    vector: [float32; 1024]        // embedding, always co-located
    content: string
    importance: float              // first-class dimension, not payload
    access_count: int
    edges: [(type, target_id)]     // typed causal edges, co-located
    tier: L1|L2|L3                 // current storage tier
    decay_curve: ExponentialDecay  // personalized per memory type
  }

  No sync. No separate database. One write, one read. The graph traversal and vector search operate on the same physical storage unit.

  This is what databases call "clustered indexes" — storing related data physically together to avoid joins. No memory system does this for vector + graph.

  ---
  A learned index for personal memory corpora

  Kraska et al. (2018) — "The Case for Learned Index Structures" — showed that ML models can replace B-trees as index structures when the access pattern is predictable. The  
  model learns the distribution of keys and predicts where data lives.

  Personal memory has highly predictable access patterns. Tim's sessions have rhythms. Monday morning is probably infrastructure/homelab. Evenings might be Recall
  development. A learned index trained on your actual session history would:
  - Predict which memory clusters are relevant before you even type the query
  - Pre-load those clusters into L1 during session startup
  - Reduce retrieval latency from the query path to near-zero for predictable sessions

  Nobody has applied learned indexes to semantic memory. The Kraska paper has 3,000+ citations in databases. Zero in AI memory systems.

  ---
  Online embedding adaptation

  Right now every memory system uses a frozen embedding model forever. You embed with qwen3-embedding:0.6b on day 1 and day 1000 with the same weights.

  But your memory corpus is a closed, known domain. You have ground truth: when you retrieve memory X for query Q and then use it (vs. ignore it), that's a training signal.  
  Contrastive fine-tuning on these pairs — "query Q found memory X useful, didn't find memory Y useful" — would produce an embedding model that's personally calibrated to    
  your retrieval patterns.

  Nobody does this. The closest analog is the recommendation systems literature (Netflix, Spotify) where they continuously fine-tune embeddings on user interaction data.     
  Applied to personal memory, the embedding model would literally learn what "relevant" means for you specifically, not for the MTEB benchmark.

  ---
  Zero-copy write path

  Recall's current write path:
  observe-edit.js → HTTP → FastAPI → qwen3:14b (extract) → qwen3-embedding (embed) → Qdrant (store) → Neo4j (sync)

  Every arrow is a process boundary, a serialization, a copy. The extraction and embedding are synchronous — the Claude Code hook waits.

  What database engineers figured out in the 1980s: Write-Ahead Log (WAL). You write to a fast sequential log immediately (microseconds), acknowledge the write, then process 
  asynchronously. SQLite does this. PostgreSQL does this. Every production database does this.

  Memory systems don't. The write path is synchronous and blocking. A WAL-based write path would:
  - Acknowledge the write immediately (hook doesn't block)
  - Process extraction + embedding in background
  - Replay the WAL if anything fails (durability)
  - Serve reads from the WAL during the processing window (read-your-writes consistency)

  This is not novel technology — it's 40-year-old database engineering that no one has applied to AI memory systems.

  ---
  The Unix socket / shared memory transport

  Every memory system uses HTTP REST. HTTP is designed for cross-network, cross-datacenter, adversarial environments. For a local homelab where the memory server and the     
  client are on the same machine or same LAN:

  - HTTP adds 10-50ms per request (TCP handshake, header parsing, body serialization)
  - Unix domain sockets add ~0.1ms (kernel buffer copy only)
  - Shared memory adds ~0.01ms (pointer pass)

  The Claude Code hooks fire on every prompt. At 10 prompts per session, 10 sessions per day, HTTP overhead accumulates to real seconds. Nobody has built a memory MCP server 
  that uses Unix sockets for local deployments. The transport is assumed to be HTTP because MCP assumes network.

  ---
  Layer 2: What Research Exists But Has Never Been Applied

  These are studies that exist in database systems, cognitive science, or systems papers but have zero citations in any AI memory system paper:

  ┌────────────────────────────────────────────────────────┬───────────────────┬───────────────────────────────────────────────────────────────────────────────────────┐      
  │                        Research                        │       Field       │                          Never Applied To Memory Because...                           │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Learned Index Structures (Kraska 2018)                 │ Databases         │ Memory systems don't think of themselves as databases                                 │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Retrieval-Induced Forgetting (Anderson 1994)           │ Cognitive science │ No one reads cognitive psych papers when building AI infra                            │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Working Memory Capacity Limits (Baddeley 2000)         │ Neuroscience      │ Treated as human limitation, not design principle                                     │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ DiskANN (Microsoft 2019)                               │ Systems           │ Designed for billion-scale, not personal corpora — but the principle applies          │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Flash Attention (Dao 2022)                             │ ML systems        │ Attention optimization, not applied to retrieval heads specifically                   │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Spaced Repetition scheduling (Leitner 1970, SM-2 1987) │ Education         │ Used in Anki, never in AI memory — but the curve math is directly applicable to decay │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Speculative execution (hardware)                       │ CPU architecture  │ Never applied to memory prefetch in software                                          │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Write coalescing (storage systems)                     │ Databases         │ Never applied to memory write batching                                                │      
  ├────────────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤      
  │ Tiered storage (NVMe/SSD/HDD hierarchies)              │ Storage systems   │ Memory systems treat all memories as equally fast-or-slow                             │      
  └────────────────────────────────────────────────────────┴───────────────────┴───────────────────────────────────────────────────────────────────────────────────────┘      

  The SM-2 algorithm specifically — it's the math behind Anki's spaced repetition. It computes the optimal review interval for a memory based on historical recall success.   
  It's been validated on millions of learners. Recall uses a custom decay function that was written from intuition. Replacing it with SM-2 or its successors (FSRS algorithm, 
  2022) would give you decades of cognitive science validation for the exact problem you're solving.

  ---
  Layer 3: How to Train BrickLayer to Be Free-Thinking

  This is the hardest problem. The issue isn't the agents — it's the attractors. Every research agent naturally gravitates toward what it can find, and what it can find is   
  what already exists. To break this:

  The Taboo Constraint

  New agent: taboo-architect.md

  The system prompt contains an explicit forbidden word list:
  You may not use or reference any of the following in your analysis:
  Qdrant, Pinecone, Chroma, Weaviate, pgvector, FAISS
  Neo4j, ArangoDB, graph database
  Redis, Memcached
  PostgreSQL, SQLite, any relational database
  mem0, Zep, Letta, any AI memory system
  vector embedding, cosine similarity, ANN search

  You must solve the problem: "how do you store and retrieve
  personal memories efficiently?" using only:
  - Physics and information theory
  - Biology and neuroscience
  - General computer science (algorithms, data structures)
  - Any non-memory-system engineering field

  When you remove the attractors, the agent has to reason from requirements. What comes out will be strange and sometimes wrong, but occasionally it's genuinely novel.       

  The Adversarial Pair

  Every architectural question gets two agents with opposing priors:

  Agent A prompt: "Build the case that Recall's current
  architecture is optimal. Find evidence. Be rigorous."

  Agent B prompt: "Build the case that Recall's current
  architecture is fundamentally wrong for the use case.
  Find evidence. Be rigorous."

  The synthesis is where the insight lives. Neither agent alone is useful. Both anchored to the same question but with opposite priors will find complementary evidence that a
   single neutral agent misses.

  This is how adversarial ML works. Apply it to architectural research.

  The 2032 Agent

  Agent prompt: "It is 2032. Recall became the standard
  architecture for personal AI memory. Write a retrospective
  blog post explaining: what architectural decisions made in
  2026 turned out to be correct? What turned out to be the
  biggest mistakes? What did the 2026 team not understand
  that seems obvious now?"

  This forces reasoning about trajectory. The agent has to extrapolate current trends (hardware curves, research directions, usage patterns) and work backward to "what should
   we build now to be right in 2032?"

  The outputs will be speculative and often wrong, but they surface assumptions about where the field is going that synchronous competitive research cannot see.

  The Physics Ceiling Agent

  Agent prompt: "Calculate the theoretical minimum latency,
  minimum storage, and minimum compute for a system that:
  - Stores N memories of average size S
  - Retrieves the top-k most relevant memories for query Q
  - Updates importance scores continuously
  - Runs on hardware profile H

  What is the gap between theoretical minimum and
  Recall's current implementation? What is the
  primary source of that gap?"

  This grounds speculation in physics. The gap between theoretical minimum and actual implementation IS the design space for optimization. Most systems never compute this    
  gap. The answer tells you where to spend engineering effort.

  ---
  The recall-arch-frontier/ Project

  Concrete structure:

  autosearch/recall-arch-frontier/
    project-brief.md        "Find architectural approaches to AI memory
                             storage that have no current implementation,
                             validated by evidence from adjacent fields"

    simulate.py             Score: novelty × evidence × feasibility × gap_from_physics

    questions.md
      Wave 1: Database systems research (LSM trees, learned indexes, WAL,
              tiered storage) applied to memory semantics
      Wave 2: Cognitive science applied to system design (forgetting curves,
              working memory limits, retrieval-induced forgetting)
      Wave 3: Physics ceiling analysis (what is the minimum possible latency?)
      Wave 4: Taboo architecture (design without naming any existing tool)
      Wave 5: Adversarial pairs (prove current arch is optimal / prove it's wrong)
      Wave 6: Convergence (what is implementable in Recall's stack right now?)

    .claude/agents/
      taboo-architect.md
      adversarial-pair.md     (runs two sub-agents with opposing priors)
      physics-ceiling.md      (calculates theoretical minimums)
      time-shifted.md         (2032 retrospective reasoning)
      db-systems-researcher.md (specifically hunts database systems papers)

  The output of this wouldn't be a competitive report. It would be a set of architectural prototypes with evidence for why they'd work — each one either something nobody has 
  built, or something from a completely different field applied to this domain for the first time.

  ---
  The moat you're describing is real. Every competitor is assembling the same general-purpose components in slightly different configurations. A purpose-built storage        
  primitive — one that bakes decay curves, importance weighting, and access-pattern-awareness into the storage layer itself rather than running them as scheduled jobs on top 
  of a database — would be architecturally unreplicable in the short term, because you'd have 2-3 years of production data about real memory access patterns that no one else 
  has.

  The question is: do you build the research first (BrickLayer finds what that system should look like), then build it? Or do you start building and let the research inform  
  iterations? Given your stack, I'd say: run the research loop for 2-3 weeks in parallel with shipping the Tier 0/1 roadmap items. The research takes no engineering time. By 
  the time you're done with SDK and docs, you'd have a grounded architectural target.

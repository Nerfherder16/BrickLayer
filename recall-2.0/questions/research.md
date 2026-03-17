# Research Questions — Recall 2.0

Questions that require external research (papers, benchmarks, competitive analysis, existing implementations) before they can be answered. Not Frontier-level ideal architecture questions — these are empirical or literature questions.

**Last updated**: 2026-03-16

---

## Literature Research

### R-LIT-01 [PENDING]
**Modern Hopfield Networks — core paper**
Read: "Hopfield Networks is All You Need" (Ramsauer et al., 2020). Extract: storage capacity formula, retrieval dynamics, update rule, temperature parameter guidance.

**Goal**: Precise understanding of capacity limits and hyperparameter sensitivity before committing to this substrate.

---

### R-LIT-02 [PENDING]
**Continual Learning and Catastrophic Forgetting**
Survey: EWC (Elastic Weight Consolidation), PackNet, Progressive Neural Networks, GEM (Gradient Episodic Memory). These address catastrophic forgetting in neural networks — the same problem as online Hebbian update interference in Hopfield.

**Goal**: Are any of these directly applicable to online Hopfield updates? Do they suggest a different online learning strategy?

---

### R-LIT-03 [PENDING]
**Complementary Learning Systems (CLS) Theory**
Read: McClelland, McNaughton & O'Reilly 1995. The hippocampus learns quickly (episodic), neocortex slowly integrates (semantic). This is the biological basis for the Hopfield + consolidation architecture.

**Goal**: Does CLS theory suggest anything about the right ratio of hot-layer to cold-store, or the ideal consolidation timing?

---

### R-LIT-04 [PENDING]
**HyDE (Hypothetical Document Embeddings)**
Read: "Precise Zero-Shot Dense Retrieval without Relevance Labels" (Gao et al., 2022). Generate a hypothetical answer to the query, embed the answer, search for similar documents.

**Goal**: Would HyDE improve cold-path retrieval quality in Recall 2.0? Does the improvement justify the additional LLM call on each retrieval?

---

### R-LIT-05 [PENDING]
**Sparse Distributed Memory (Kanerva, 1988)**
Read: Kanerva's original SDM paper. SDM stores patterns in high-dimensional binary space with distributed reading/writing — different from Hopfield's energy-minimization approach.

**Goal**: Is SDM a viable alternative to Modern Hopfield for the hot-layer substrate? How does storage capacity compare at 1024 dimensions?

---

### R-LIT-06 [PENDING]
**"Lost in the Middle" Effect in LLMs**
Read: "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., 2023). LLMs attend more to content at the beginning and end of context than to middle content.

**Goal**: Does this predict where memory injection should go relative to the user message? Is this effect present in Claude specifically?

---

## Benchmark Research

### R-BM-01 [PENDING]
**Embedding Model Comparison at <1B Parameters**
Compare on MTEB (Massive Text Embedding Benchmark), specifically the retrieval task: qwen3-embedding:0.6b, nomic-embed-text:latest, snowflake-arctic-embed:m, mxbai-embed-large:latest, all-minilm:l6-v2.

**Metrics**: NDCG@10 on retrieval tasks, inference latency on RTX 3090 via Ollama, model size, dimensions.

**Goal**: Is qwen3-embedding:0.6b actually the best choice, or is there a better model at similar cost?

---

### R-BM-02 [PENDING]
**LMDB vs SQLite vs PostgreSQL for Recall Metadata Workload**
Benchmark on operations representative of Recall 2.0 workload: single-key reads, small batch writes, range scans by timestamp.

**Goal**: Confirm LMDB is faster than SQLite for this workload. Quantify the speedup.

---

### R-BM-03 [PENDING]
**Hopfield Retrieval Latency on RTX 3090**
Implement minimal Modern Hopfield retrieval in PyTorch. Benchmark: one retrieval step latency as a function of N stored patterns (1K, 5K, 10K, 22K, 50K) at 1024 dimensions in fp16 on RTX 3090.

**Goal**: Confirm retrieval latency stays below 20ms target at 22K+ patterns.

---

### R-BM-04 [PENDING]
**HNSW vs Qdrant for Cold ANN at 22K Vectors**
Compare: a custom HNSW implementation in LMDB (using `hora` or `instant-distance` crate) vs. Qdrant for:
- Query latency at P99
- Index build time
- Memory overhead
- Persistence model

**Goal**: Is a custom HNSW embedded in LMDB competitive with Qdrant for this corpus size? Decision input for OD-01.

---

## Competitive Research

### R-CP-01 [PENDING]
**A-MEM (Agentic Memory)**
Read: A-MEM paper/implementation. Claims to evolve memory links as new memories arrive — Zettelkasten-style network that grows more connected over time.

**Goal**: What mechanism does A-MEM use for link evolution? Does it produce better retrieval quality than static graphs? What does it get wrong?

---

### R-CP-02 [PENDING]
**GraphRAG (Microsoft)**
Survey: GraphRAG builds community summaries from entity-relationship graphs. Read: approach, quality results, limitations.

**Goal**: Does GraphRAG's community summarization approach outperform flat retrieval on any Recall 2.0 use cases? Would the graph construction approach work for Recall's corpus?

---

### R-CP-03 [PENDING]
**Stanford Generative Agents (Park et al., 2023)**
Read: "Generative Agents: Interactive Simulacra of Human Behavior." Uses three-factor retrieval (recency × importance × relevance) and reflection to generate higher-level observations.

**Goal**: The reflection mechanism is similar to Recall 2.0's consolidation. What did they learn about reflection quality, timing, and frequency?

---

### R-CP-04 [PENDING]
**Neuroscience-Grounded AI Memory Systems**
Survey: any academic implementations of hippocampal-neocortical memory systems in AI. What is the state of the art in neuroscience-inspired AI memory?

**Goal**: Has anyone built a working AI system using CLS theory? What does it look like? What problems did they hit?

---

### R-CP-05 [PENDING]
**Vector Database Native Memory (Pinecone Memory Layer, Weaviate Memory Module)**
Investigate: What do Pinecone and Weaviate offer as "memory" products? How do they handle reinforcement, decay, consolidation?

**Goal**: Are there ideas worth stealing? Are there failure modes worth avoiding?

---

## Implementation Research

### R-IM-01 [PENDING]
**Rust CRDT Crate Evaluation**
Evaluate `crdts` crate (Rust): does it provide OR-Set, G-Counter, LWW-Register? Is it production-quality? What are the known limitations?

Alternative: `yrs` (Y.js for Rust) — CRDT library with different data model.

**Goal**: Choose the right Rust CRDT library before committing to it.

---

### R-IM-02 [PENDING]
**LMDB Rust Binding Evaluation**
Evaluate `heed` crate: performance, correctness, maintenance status. Compare to `lmdb-zero` and `lmdb-rkv`.

**Goal**: Choose the right LMDB Rust binding.

---

### R-IM-03 [PENDING]
**Hybrid Logical Clock Implementation**
Read: Kulkarni & Demirbas (2014) "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases." Find or evaluate existing Rust HLC implementations.

**Goal**: Understand HLC correctness requirements and confirm a good Rust implementation exists before committing to HLC for CRDT timestamps.

---

### R-IM-04 [PENDING]
**PyTorch Hopfield Implementation Survey**
Search: existing open-source Modern Hopfield Network implementations in PyTorch. Candidates: `hopfield-layers` (PyTorch implementation by Ramsauer group), any GPU-optimized variants.

**Goal**: Is there a production-quality Hopfield implementation to build on, or is this a from-scratch implementation?

---

### R-IM-05 [PENDING]
**Ollama Embedding API Latency**
Benchmark: qwen3-embedding:0.6b via Ollama API on RTX 3090. Measure: single embedding latency P50/P95/P99, batch embedding throughput, max batch size.

**Goal**: Confirm embedding is within the 150ms latency budget for the write path.

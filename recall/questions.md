# Recall Autoresearch Questions

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Performance Questions (Q1.x) — Load and Latency

---

## Q1.1 [PERFORMANCE] Search latency under concurrent load
**Mode**: performance
**Target**: POST /search
**Hypothesis**: p99 latency stays under 2000ms up to ~15 concurrent users, degrades above that
**Test**: Sweep concurrent users 5→10→20→40 (30s per stage). Each user POSTs /search with a realistic query payload. Measure p50/p95/p99 per stage. Stop sweep early on first FAILURE threshold breach.
**Verdict threshold**:
- FAILURE: p99 > 2000ms at any stage OR error rate > 5%
- WARNING: p99 > 1000ms at any stage OR error rate > 1%
- HEALTHY: p99 ≤ 1000ms and error rate ≤ 1% across all stages

---

## Q1.2 [PERFORMANCE] Store throughput and embedding queue back-pressure
**Mode**: performance
**Target**: POST /store
**Hypothesis**: At ~10 stores/sec the Ollama embedding queue backs up, causing response time to climb sharply
**Test**: Ramp store rate 1/s→5/s→10/s→20/s (20s per stage). Use sequential per-stage bursts. Measure mean response time and error rate per stage. Treat response time > 5s as queue-backed-up proxy.
**Verdict threshold**:
- FAILURE: mean response time > 5000ms OR error rate > 10% at any stage
- WARNING: mean response time > 2000ms OR error rate > 5% at any stage
- HEALTHY: mean response time ≤ 2000ms and error rate ≤ 5% across all stages

---

## Q1.3 [PERFORMANCE] /health lead or lag indicator
**Mode**: performance
**Target**: GET /health vs POST /search
**Hypothesis**: /health degrades before user-visible search errors, providing early warning
**Test**: Run 30 concurrent search users for 60s. Poll /health every 5s concurrently. Record first timestamp when /health returns non-200 or non-healthy status, and first timestamp when search error rate exceeds 1%. Compare timing.
**Verdict threshold**:
- FAILURE: /health stays green while search errors exceed 5% (false negative — health lies)
- WARNING: /health lags search errors by more than 30s
- HEALTHY: /health degrades at same time or before search errors appear

---

## Q1.4 [PERFORMANCE] Vector search latency as memory count grows
**Mode**: performance
**Target**: POST /search (Qdrant vector search leg)
**Hypothesis**: At the current ~19K memory count, search is fast; the question is whether repeated searches at high concurrency reveal indexing bottlenecks
**Test**: Run 40 concurrent users for 60s hitting /search only. Measure p50/p95/p99. Compare to baseline at 5 users. The "growth proxy" is the concurrency forcing worst-case index scans.
**Verdict threshold**:
- FAILURE: p99 > 3000ms at 40 concurrent users
- WARNING: p99 > 1500ms at 40 concurrent users
- HEALTHY: p99 ≤ 1500ms at 40 concurrent users

---

## Q1.5 [PERFORMANCE] Consolidation concurrency failure point
**Mode**: performance
**Target**: POST /ops/consolidate
**Hypothesis**: Consolidation is not designed for concurrent invocation; N simultaneous calls will either error or produce duplicate work
**Test**: Fire N concurrent POST /ops/consolidate calls (N = 1, 2, 5, 10). Measure: HTTP status codes, response times, error rate. A 409 Conflict or 500 error is expected at high N.
**Verdict threshold**:
- FAILURE: 500 errors at N ≥ 2 OR timeout at N ≥ 5
- WARNING: non-idempotent responses (different results for same N) OR 429/409 only at N ≥ 5
- HEALTHY: endpoint handles concurrent calls gracefully (idempotent, 200 or 409 with clear message)

---

## Correctness Questions (Q2.x) — Behavioral Guarantees

---

## Q2.1 [CORRECTNESS] Domain isolation under concurrent cross-domain writes
**Mode**: correctness
**Target**: tests/integration/test_concurrent.py + tests/core/test_multitenancy.py
**Hypothesis**: Domain isolation holds even when multiple domains are written concurrently
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/integration/test_concurrent.py C:/Users/trg16/Dev/Recall/tests/core/test_multitenancy.py -v --tb=short -q`
**Verdict threshold**:
- FAILURE: any test failure
- WARNING: any test skipped due to infrastructure issue
- HEALTHY: all tests pass

---

## Q2.2 [CORRECTNESS] Write guard deduplication under concurrency
**Mode**: correctness
**Target**: src/core/write_guard.py, tests/integration/test_concurrent.py
**Hypothesis**: Storing the same content 5x concurrently results in exactly 1 stored memory, not 5
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/integration/test_concurrent.py -v --tb=short -q -k "dedup or duplicate or write_guard"`
If no dedup-specific test exists, run the full concurrent suite and check for dedup assertions.
**Verdict threshold**:
- FAILURE: test explicitly shows duplicates stored OR test fails
- WARNING: no dedup test exists (gap in coverage)
- HEALTHY: dedup tests pass

---

## Q2.3 [CORRECTNESS] Decay correctness
**Mode**: correctness
**Target**: tests/integration/test_decay.py
**Hypothesis**: Decay reduces importance scores without dropping memories below the retrieval floor
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/integration/test_decay.py -v --tb=short -q`
**Verdict threshold**:
- FAILURE: any test failure
- WARNING: any test skipped
- HEALTHY: all tests pass

---

## Q2.4 [CORRECTNESS] Reranker score stability
**Mode**: correctness
**Target**: tests/core/test_reranker.py
**Hypothesis**: The ML reranker produces stable (deterministic or low-variance) scores for identical inputs
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/core/test_reranker.py -v --tb=short -q`
**Verdict threshold**:
- FAILURE: any test failure, especially score variance / non-determinism assertions
- WARNING: tests pass but stdout shows high score variance warnings
- HEALTHY: all tests pass cleanly

---

## Q2.5 [CORRECTNESS] Signal classifier accuracy
**Mode**: correctness
**Target**: tests/core/test_signal_classifier.py + tests/ml/ (if present)
**Hypothesis**: The signal classifier correctly distinguishes high-importance from low-importance signals
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/core/test_signal_classifier.py -v --tb=short -q`
Also run `pytest C:/Users/trg16/Dev/Recall/tests/ml/ -v --tb=short -q` if the directory exists.
**Verdict threshold**:
- FAILURE: any test failure
- WARNING: any test skipped or no ml/ tests found
- HEALTHY: all tests pass

---

## Quality Questions (Q3.x) — Source Code Analysis

---

## Q3.1 [QUALITY] N+1 query patterns in retrieval pipeline
**Mode**: quality
**Target**: src/core/retrieval.py
**Hypothesis**: The retrieval pipeline may issue per-result Neo4j or Qdrant calls inside a result loop instead of batching
**Test**: Read src/core/retrieval.py. Look for: loops containing DB calls (neo4j session queries, qdrant client calls, redis gets) that could be batched. Report any found.
**Verdict threshold**:
- FAILURE: confirmed N+1 pattern (DB call inside result iteration loop with no batching)
- WARNING: possible N+1 (conditional or unclear batching)
- HEALTHY: all DB calls are batched or single-shot

---

## Q3.2 [QUALITY] Embedding cache invalidation correctness
**Mode**: quality
**Target**: src/core/embeddings.py
**Hypothesis**: The embedding cache may return stale embeddings if content is updated, or may not evict on error
**Test**: Read src/core/embeddings.py and tests/core/test_embeddings_cache.py. Look for: cache key construction (does it include content hash?), error path cache behavior (does a failed embed leave a bad cache entry?), TTL correctness.
**Verdict threshold**:
- FAILURE: cache key does not include content hash (stale embedding possible) OR error path caches bad result
- WARNING: TTL is missing or set to infinite
- HEALTHY: cache key is content-addressed and error paths do not cache

---

## Q3.3 [QUALITY] Race conditions in concurrent write paths
**Mode**: quality
**Target**: src/core/write_guard.py + tests/integration/test_concurrent.py
**Hypothesis**: The write guard uses Redis SETNX but may have a TOCTOU race between check and write
**Test**: Read src/core/write_guard.py. Look for: Redis lock acquisition pattern (SETNX vs SET NX EX vs Lua script), lock release on exception path, lock TTL (no TTL = deadlock risk), gap between lock check and Qdrant write.
**Verdict threshold**:
- FAILURE: lock released before write completes OR no TTL on lock OR bare except that skips lock release
- WARNING: lock TTL exists but is very short (<1s) relative to embedding latency
- HEALTHY: atomic lock with TTL, released in finally block

---

## Q3.4 [QUALITY] Circular reference handling in consolidation
**Mode**: quality
**Target**: src/core/consolidation.py + src/core/auto_linker.py
**Hypothesis**: The consolidation graph traversal may not guard against cycles in Neo4j relationship graphs
**Test**: Read src/core/consolidation.py and src/core/auto_linker.py. Look for: graph traversal algorithms (BFS/DFS with visited set?), cycle detection, max depth limits, APOC procedure usage (which handles cycles natively).
**Verdict threshold**:
- FAILURE: graph traversal with no visited set and no depth limit (infinite loop possible)
- WARNING: visited set present but not reset between calls (state leakage)
- HEALTHY: cycle-safe traversal (visited set, depth limit, or APOC with cycle-safe procedures)

---

## Q3.5 [QUALITY] Consistent error handling across API routes
**Mode**: quality
**Target**: src/api/routes/ (all .py files)
**Hypothesis**: Some routes use bare except, return 200 on error, or expose internal stack traces
**Test**: Read all .py files in src/api/routes/. Look for: bare `except:` or `except Exception as e: pass`, missing HTTPException status codes (using 200 where 4xx/5xx is correct), f-string error messages that include internal paths or stack traces in the response body.
**Verdict threshold**:
- FAILURE: bare except that swallows errors OR 200 returned on known error condition
- WARNING: inconsistent status codes across routes (some use 422, others use 400 for same error type)
- HEALTHY: all routes use explicit HTTPException with correct status codes and no internal detail leaked

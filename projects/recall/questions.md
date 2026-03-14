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

---

## Agent Dispatch Questions (Q4.x) — Specialist Agent Fix Loops

These questions invoke specialist agents against findings from Q1–Q3.
The agent reads the finding, applies its fix loop, and reports back.

---

## Q4.1 [AGENT] security-hardener → API route error handling
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q3.5
**Source**: src/api/routes/
**Hypothesis**: security-hardener will tighten bare excepts and inconsistent error handling across API routes, committing fixes with security tests
**Verdict threshold**:
- HEALTHY: agent committed ≥1 fix with a corresponding security test
- WARNING: agent found issues but reported them as architectural debt (unfixable without redesign)
- INCONCLUSIVE: agent produced no structured output or claude CLI unavailable

---

## Q4.2 [AGENT] test-writer → write_guard and decay coverage gap
**Mode**: agent
**Agent**: test-writer
**Finding**: Q2.2
**Source**: src/core/write_guard.py
**Hypothesis**: test-writer will add fast-mode tests for write_guard deduplication that don't require @pytest.mark.slow, lifting coverage above 70%
**Verdict threshold**:
- HEALTHY: coverage increased and new tests pass without slow mark
- WARNING: tests written but coverage delta < 5%
- INCONCLUSIVE: agent produced no structured output

---

## Q4.3 [AGENT] type-strictener → reranker and retrieval type coverage
**Mode**: agent
**Agent**: type-strictener
**Finding**: Q3.4
**Source**: src/core/retrieval.py
**Hypothesis**: type-strictener will reduce mypy errors in retrieval.py by narrowing Any types and adding missing return annotations
**Verdict threshold**:
- HEALTHY: mypy error count decreases and all existing tests still pass
- WARNING: agent ran but errors reduced by < 3
- INCONCLUSIVE: agent produced no structured output or mypy not installed

---

## Q4.4 [AGENT] security-hardener → consolidation concurrency 500 errors
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q1.5
**Source**: src/core/consolidation.py
**Hypothesis**: security-hardener will add a concurrency guard (Redis lock or in-process lock) to prevent concurrent /ops/consolidate invocations from producing 500 errors, returning 409 Conflict instead
**Verdict threshold**:
- HEALTHY: agent committed a fix with a corresponding test; concurrent calls return 409 not 500
- WARNING: agent found the issue but reported it as architectural debt requiring redesign
- INCONCLUSIVE: agent produced no structured output

---

## Q4.5 [AGENT] security-hardener → write guard lock TTL too short
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q3.3
**Source**: src/core/write_guard.py
**Hypothesis**: security-hardener will extend the Redis lock TTL in write_guard.py to safely cover worst-case embedding latency, eliminating the TOCTOU window identified in Q3.3
**Verdict threshold**:
- HEALTHY: agent committed a TTL fix with a test proving the lock outlives embedding latency
- WARNING: agent found the issue but TTL delta < 5s improvement
- INCONCLUSIVE: agent produced no structured output

---

## Q4.6 [AGENT] test-writer → reranker score stability characterization
**Mode**: agent
**Agent**: test-writer
**Finding**: Q2.4
**Source**: src/core/reranker.py
**Hypothesis**: test-writer will add determinism/stability tests that characterize the reranker's score variance, either proving it is within acceptable bounds or exposing the non-determinism source
**Verdict threshold**:
- HEALTHY: stability tests pass with variance within defined threshold OR tests expose and document the non-determinism source
- WARNING: tests written but variance threshold was not defined (tests always pass)
- INCONCLUSIVE: agent produced no structured output

---

## Wave 2 Questions (Q5.x) — Targeted Follow-up

These questions address open failures from Wave 1 and cover blindspot areas.

---

## Q5.1 [CORRECTNESS] Reranker feature count sync after expansion
**Mode**: correctness
**Target**: tests/core/test_reranker.py
**Hypothesis**: Q2.4 showed 4 tests failing with "assert 13 == 11" — the reranker model was expanded to 13 features but tests still assert 11. This re-run confirms the failures are still present before dispatching the fix agent.
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/core/test_reranker.py -v --tb=short -q`
**Verdict threshold**:
- FAILURE: test_length or score tests still fail (feature mismatch unresolved)
- HEALTHY: all reranker tests pass (someone fixed them between sessions)

---

## Q5.2 [CORRECTNESS] Consolidation concurrency lock verification
**Mode**: correctness
**Target**: tests/api/test_security_hardening.py
**Hypothesis**: Q4.4 added an asyncio.Lock to /admin/consolidate. The lock tests written by the agent should prove the guard is in place. This verifies the fix is committed and tests pass.
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/api/test_security_hardening.py -v --tb=short -q -k "consolidat"`
**Verdict threshold**:
- FAILURE: lock tests fail (fix was reverted or not committed)
- WARNING: no consolidation lock tests found (tests weren't written)
- HEALTHY: all consolidation lock tests pass

---

## Q5.3 [QUALITY] Background worker silent failure patterns
**Mode**: quality
**Target**: src/workers/decay.py + src/workers/dream_consolidation.py + src/workers/hygiene.py + src/workers/invalidation.py
**Hypothesis**: Background workers run in async loops with no user-facing error path — silent failures (bare excepts, swallowed exceptions) could cause data loss or stale memory state with no observable signal
**Test**: Read src/workers/decay.py, src/workers/dream_consolidation.py, src/workers/hygiene.py, src/workers/invalidation.py. Look for: bare `except: pass`, `except Exception: pass` without logging, missing finally blocks on DB write paths, asyncio task exceptions swallowed by gather().
**Verdict threshold**:
- FAILURE: bare except on a write path with no logging (data loss possible)
- WARNING: broad except with logging but no re-raise on critical path
- HEALTHY: all exception paths log structured errors

---

## Q5.4 [QUALITY] embed_batch silent failure and zero-vector propagation
**Mode**: quality
**Target**: src/core/embeddings.py + tests/core/test_embeddings_cache.py
**Hypothesis**: embed_batch() catches all exceptions and returns zero-vectors silently. Callers receive [] or zero vectors with no signal that embedding failed — these bad vectors get stored in Qdrant and poison future retrieval results.
**Test**: Read src/core/embeddings.py. Look for: the embed_batch exception path (line ~224), what is returned on failure (zero vector vs empty list vs exception), whether the caller is notified, whether bad results are stored in cache.
**Verdict threshold**:
- FAILURE: exception path returns zero-vectors that are stored in Qdrant cache (poisoned index)
- WARNING: exception is swallowed but zero-vectors are not stored (silent degradation only)
- HEALTHY: exception is logged with structured context and callers can detect failure

---

## Q5.5 [AGENT] test-writer → fix reranker feature count test failures
**Mode**: agent
**Agent**: test-writer
**Finding**: Q2.4
**Source**: src/core/reranker.py
**Hypothesis**: test-writer will update test_reranker.py to match the current 13-feature model (not 11), fixing the 4 failing tests without changing the reranker source
**Verdict threshold**:
- HEALTHY: all 26 reranker tests pass after fix; coverage maintained
- WARNING: some tests fixed but others still fail
- INCONCLUSIVE: agent produced no structured output

---

## Q5.6 [AGENT] security-hardener → embed_batch silent failure
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q5.4
**Source**: src/core/embeddings.py
**Hypothesis**: security-hardener will add structured logging to the embed_batch failure path so callers can detect embedding failures, replacing silent zero-vector returns with observable errors
**Verdict threshold**:
- HEALTHY: agent committed logging fix + security test proving failure is observable
- WARNING: agent reported issue as architectural debt requiring caller changes
- INCONCLUSIVE: agent produced no structured output

---

## Q5.7 [AGENT] test-writer → background worker coverage
**Mode**: agent
**Agent**: test-writer
**Finding**: Q5.3
**Source**: src/workers/decay.py
**Hypothesis**: test-writer will add unit tests for the decay worker's error handling paths (the paths identified as silent-swallow risks in Q5.3), lifting coverage above 70%
**Verdict threshold**:
- HEALTHY: coverage increased and new tests exercise error paths
- WARNING: tests written but coverage delta < 5%
- INCONCLUSIVE: agent produced no structured output

---

## Wave 3 — Post-Fix Audit (Q6.x)

---

## Q6.1 [AGENT] security-hardener → embed_batch empty-list caller guard
**Status**: DONE
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q5.4
**Source**: src/workers/signals.py
**Hypothesis**: _store_signal_as_memory uses `if embedding is None:` but embed_batch per-item failure returns []. Empty list is not None, so [] reaches qdrant.search(query_vector=[]) and is caught by a broad except as generic signal_store_error — signal silently dropped without indicating the root cause. Fix: caller should skip empty embeddings in embeddings_map OR callee should use `if not embedding:`.
**Verdict threshold**:
- HEALTHY: agent committed fix + test proving empty-list embeddings trigger re-embed not silent drop
- WARNING: agent identified issue but flagged as architectural debt
- INCONCLUSIVE: agent produced no structured output

---

## Q6.2 [QUALITY] stdlib/structlog logger mismatch audit
**Status**: DONE
**Mode**: quality
**Target**: src/storage/graphiti_store.py
**Hypothesis**: graphiti_store.py imports stdlib logging but uses structlog.get_logger() for all logging calls. The stdlib import may be dead code, or there may be hidden paths using stdlib logger with structlog-style kwargs that would silently raise TypeError in except blocks.
**Verdict threshold**:
- FAILURE: files found with stdlib logger receiving kwargs (silent TypeError in except blocks)
- WARNING: mixed logger imports but no kwarg-passing found
- HEALTHY: all files consistently use structlog; stdlib import is confirmed dead code

---

## Q6.3 [CORRECTNESS] write guard Redis dedup under concurrent async load
**Status**: DONE
**Mode**: correctness
**Target**: tests/core/test_write_guard.py
**Test**: pytest C:/Users/trg16/Dev/Recall/tests/core/test_write_guard.py -v --tb=short -q
**Hypothesis**: The write guard's Redis-backed deduplication prevents double-store under 5 concurrent identical async writes. The Q4.2 agent added synchronous concurrent tests; true async concurrent behavior is unverified.
**Verdict threshold**:
- FAILURE: concurrent async writes produce duplicate entries in Qdrant
- WARNING: dedup works but race window exists (non-atomic check-then-set)
- HEALTHY: exactly-once storage confirmed under concurrent async load

---

## Q6.4 [QUALITY] module-level mutable state missing async locks
**Status**: DONE
**Mode**: quality
**Target**: src/core/retrieval.py + src/core/embeddings.py + src/core/tuning_config.py
**Hypothesis**: _speculative_seeds (dict, retrieval.py:1613), _embed_cache (OrderedDict, embeddings.py:21), and tuning_config._cache (dict, tuning_config.py) are written from async paths without asyncio.Lock guards. _cognitive_bias_cache has a lock; _speculative_seeds does not.
**Verdict threshold**:
- FAILURE: unguarded mutable module-level state on a write path (data corruption possible)
- WARNING: mutable state present but only written at initialization (low-risk)
- HEALTHY: all async-written module-level state has corresponding asyncio.Lock

---

## Q6.5 [AGENT] type-strictener → Pydantic v2 migration
**Status**: INCONCLUSIVE
**Mode**: agent
**Agent**: type-strictener
**Finding**: Q2.1
**Source**: src/core/models.py
**Hypothesis**: src/core/models.py uses Pydantic v1-style class Config and json_encoders, generating PydanticDeprecatedSince20 warnings on every test run. type-strictener will migrate to ConfigDict and replace json_encoders with custom serializers.
**Verdict threshold**:
- HEALTHY: zero PydanticDeprecatedSince20 warnings from models.py in test output; all tests pass
- WARNING: warnings reduced but not eliminated
- INCONCLUSIVE: agent produced no structured output

---

## Q6.6 [CORRECTNESS] decay integration test with live Qdrant/Neo4j
**Status**: DONE
**Mode**: correctness
**Target**: tests/workers/test_decay.py
**Test**: pytest C:/Users/trg16/Dev/Recall/tests/workers/test_decay.py -v --tb=short -q
**Hypothesis**: Importance scores for memories stored in a live Qdrant collection decrease measurably after running DecayWorker with hours_offset=24. The Q5.7 unit tests verify logic via mocks; no integration test confirms the real storage write path.
**Verdict threshold**:
- FAILURE: importance scores unchanged after decay run (write path broken)
- WARNING: scores decrease but by less than expected (decay formula mismatch)
- HEALTHY: importance scores decrease as predicted by the decay formula

---

## Q6.7 [AGENT] type-strictener → datetime.utcnow() deprecation sweep
**Status**: DONE
**Mode**: agent
**Agent**: type-strictener
**Finding**: Q5.1
**Source**: src/workers/decay.py + src/core/reranker.py + src/core/retrieval.py + src/api/routes/search.py + src/api/main.py
**Hypothesis**: 28+ usages of datetime.utcnow() across src/ and tests/ are deprecated in Python 3.12 and will become errors in a future version. type-strictener will replace all with datetime.now(datetime.UTC) and confirm all tests pass.
**Verdict threshold**:
- HEALTHY: zero datetime.utcnow() calls remain in src/ and tests/; all tests pass
- WARNING: some instances replaced but not all (≥50% reduction)
- INCONCLUSIVE: agent produced no structured output

---

## Wave 4 Questions (Q7.x) — Lock Audit, Migration, and Residual Coverage

These questions close the three open risks from the Wave 3 residual inventory, re-run
the timed-out Q6.7 agent with bounded scope, and address two patterns observed in the
findings that have not yet been asked.

---

## Q7.1 [AGENT] security-hardener → add asyncio.Lock to _embed_cache, _speculative_seeds, _tuning_cache
**Status**: DONE
**Mode**: agent
**Agent**: security-hardener
**Finding**: Q6.4
**Source**: src/core/embeddings.py + src/core/retrieval.py + src/core/tuning_config.py
**Hypothesis**: Q6.4 identified three unguarded module-level dicts written from async paths: `_speculative_seeds` (retrieval.py), `_embed_cache` (embeddings.py OrderedDict), and `_tuning_cache` (tuning_config.py). `_cognitive_bias_cache` in retrieval.py is the correct template — asyncio.Lock created at module level, double-checked inside the lock body before writing. The `_embed_cache` case is additionally risky because `OrderedDict.move_to_end()` (called on every cache hit) mutates the dict and is not safe under concurrent async access. security-hardener will apply the `_cognitive_bias_cache` pattern to all three caches and add one lock-contention test per cache.
**Verdict threshold**:
- HEALTHY: agent committed locks for all three caches + ≥3 lock-contention tests pass; all existing tests still pass
- WARNING: agent added locks to some but not all three caches, or tests were not written
- INCONCLUSIVE: agent produced no structured output

**Derived from**: Q6.4 (INCONCLUSIVE — lock audit; three unguarded caches identified)
**Simulation path**: security-hardener reads Q6.4 finding, reads the three source files, applies double-checked lock pattern from _cognitive_bias_cache, writes tests, commits

---

## Q7.2 [AGENT] executor → Pydantic v2 migration: Memory.Config → ConfigDict + @field_serializer
**Status**: DONE
**Mode**: agent
**Agent**: executor
**Finding**: Q6.5
**Source**: src/core/models.py
**Hypothesis**: Q6.5 (WARNING) confirmed that `Memory.Config` (line 137 of models.py) uses the Pydantic v1-style inner class and `json_encoders` dict. Both are deprecated in Pydantic v2.0 and will be removed in Pydantic v3. The migration path is bounded and low-risk: replace the inner `Config` class with `model_config = ConfigDict(...)` and replace `json_encoders` entries with `@field_serializer` decorators on the datetime fields. This requires no behavioral change — only the API surface changes. The fix is outside the type-strictener mandate (no mypy impact) and needs a dedicated executor pass.
**Verdict threshold**:
- HEALTHY: zero PydanticDeprecatedSince20 warnings appear in any test run after the change; all tests pass; no behavioral change to datetime serialization
- WARNING: warnings reduced but one or more remain (partial migration)
- INCONCLUSIVE: agent produced no structured output

**Derived from**: Q6.5 (WARNING — Pydantic v2 API deprecation confirmed; type-strictener declined to act)
**Simulation path**: executor reads models.py, applies ConfigDict migration and @field_serializer, runs full test suite, verifies zero PydanticDeprecatedSince20 warnings, commits

---

## Q7.3 [CORRECTNESS] decay live-Qdrant integration test — importance score write path
**Status**: PENDING
**Mode**: correctness
**Target**: tests/workers/test_decay.py (new @pytest.mark.integration test)
**Hypothesis**: All 17 decay tests in tests/workers/test_decay.py use mocks — no test confirms that the DecayWorker's importance score updates actually reach a live Qdrant collection. The write path (qdrant_client.set_payload() or equivalent) could be silently broken by a Qdrant schema change or client version bump with no failing test. A single slow-marked integration test that stores a memory, runs DecayWorker with hours_offset=24, and re-fetches the memory from Qdrant to confirm the importance field decreased would close the live-write-path gap identified in Wave 2 (Pattern 4) and confirmed open in Q6.6.
**Test**: Write and run `pytest C:/Users/trg16/Dev/Recall/tests/workers/test_decay.py -v --tb=short -q -m integration`
**Verdict threshold**:
- FAILURE: importance score unchanged after decay run against live Qdrant (write path broken)
- WARNING: test written but skipped (live Qdrant not available in CI environment)
- HEALTHY: @pytest.mark.integration test passes against live Qdrant; importance score decreases by expected delta

**Derived from**: Q6.6 (HEALTHY but mock-only), Q2.3 (skipped integration tests, Pattern 4 in Wave 1+2 synthesis)
**Simulation path**: test-writer agent adds one integration-marked test to test_decay.py; correctness loop runs it against live infra at 192.168.50.19

---

## Q7.4 [QUALITY] full codebase stdlib/structlog mismatch audit — all src/ files beyond graphiti_store.py
**Status**: DONE
**Mode**: quality
**Target**: src/ (all .py files)
**Hypothesis**: Q6.2 confirmed graphiti_store.py's stdlib import is dead code. However, Q6.2 only audited one file. The Wave 2 synthesis (Pattern 3) characterized the stdlib/structlog mismatch as a codebase-wide bug class: any file that imports `logging` and then calls `logger.warning(key=value)` with keyword arguments will raise a silent TypeError in its except blocks. The audit must cover all src/ files. Grep for `import logging` (stdlib) and cross-reference against structlog-style calls to find any remaining instances where the wrong logger type receives kwargs.
**Test**: Run `grep -rn "import logging" C:/Users/trg16/Dev/Recall/src/` and for each matching file verify the logger calls do not use structlog-style kwargs on a stdlib logger instance.
**Verdict threshold**:
- FAILURE: any src/ file found with stdlib `logging.getLogger()` result receiving structlog-style kwargs (e.g., `logger.error("msg", key=val)`) — silent TypeError possible in except paths
- WARNING: stdlib `import logging` found in files but only used for constants or isinstance checks, not for logger calls (dead import, lower risk)
- HEALTHY: no src/ file has stdlib logger receiving kwargs; all logger calls use structlog consistently

**Derived from**: Q6.2 (HEALTHY for graphiti_store.py only), Q4.2/Q4.5 (two prior instances of this bug class fixed), Wave 2 synthesis Pattern 3
**Simulation path**: grep + file read; no simulation parameters needed; pure source audit

---

## Q7.5 [QUALITY] datetime.utcnow() sweep re-run — verify Q6.7 commit actually landed
**Status**: DONE
**Mode**: quality
**Target**: src/ + tests/ (full codebase grep)
**Hypothesis**: Q6.7's finding file records INCONCLUSIVE (agent timed out after 600s, no structured output). The synthesis claims commit 9cec9f4 replaced 44 calls across 23 files, but this conflicts with the finding file evidence. Additionally, Q6.6's test evidence (run after Q6.7 allegedly committed) still shows `DeprecationWarning: datetime.datetime.utcnow()` in `src/workers/decay.py:80` and `tests/workers/test_decay.py:61` — strongly suggesting the Q6.7 commit either did not land, was reverted, or was incomplete. A direct grep of the codebase will resolve the contradiction and determine whether a re-run of the sweep agent is needed.
**Test**: Run `grep -rn "utcnow" C:/Users/trg16/Dev/Recall/src/ C:/Users/trg16/Dev/Recall/tests/`
**Verdict threshold**:
- FAILURE: ≥10 utcnow() calls remain (Q6.7 agent did not commit; full sweep still needed)
- WARNING: 1–9 utcnow() calls remain (partial fix; sweep was incomplete)
- HEALTHY: zero utcnow() calls in src/ and tests/ (commit 9cec9f4 landed correctly)

**Derived from**: Q6.7 (INCONCLUSIVE — agent timed out), Q6.6 (evidence shows utcnow DeprecationWarning still present in decay.py after Q6.7 allegedly ran)
**Simulation path**: grep only — no agent needed for the audit step; if FAILURE verdict, dispatch type-strictener with bounded scope (one file at a time, not full sweep)

---

## Q7.6 [QUALITY] hygiene and dream_consolidation worker test coverage gap
**Status**: IN_PROGRESS
**Mode**: quality
**Target**: src/workers/hygiene.py + src/workers/dream_consolidation.py
**Hypothesis**: Q5.3 confirmed all four background workers have structured exception logging. Q5.7 wrote a 17-test suite for the decay worker. However, hygiene.py and dream_consolidation.py received no dedicated test suite — only the confirmation that their exception paths log correctly (a source-read verdict, not a test-run verdict). If either worker's error path logging is later broken by a refactor, no test will catch it. The same test-writer pattern applied to decay.py in Q5.7 should be applied to both remaining workers.
**Test**: Run `pytest C:/Users/trg16/Dev/Recall/tests/workers/ -v --tb=short -q` after agent adds tests; check for test files covering hygiene.py and dream_consolidation.py
**Verdict threshold**:
- FAILURE: no test files exist for hygiene or dream_consolidation after agent pass
- WARNING: tests written but coverage < 60% of each worker file
- HEALTHY: test files exist for both workers; coverage ≥ 70% per file; all error-path branches covered

**Derived from**: Q5.3 (HEALTHY — structured logging confirmed by source read, not test run), Q5.7 (HEALTHY — decay worker test suite written; same pattern not applied to hygiene/dream_consolidation)
**Simulation path**: test-writer agent reads hygiene.py and dream_consolidation.py, writes tests/workers/test_hygiene.py and tests/workers/test_dream_consolidation.py following the test_decay.py pattern, commits

---

## ML Spec Validation Questions (Q-C24.x) — BrickLayer C-24

*Added by BrickLayer ML spec audit (2026-03-13). These re-validate the initial model choices and threshold decisions made when Recall was first configured.*

---

## Q-C24.1 [AGENT] Embedding model adequacy at scale — qwen3-embedding:0.6b vs retrieval quality
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: Recall /search/query endpoint + Ollama at 192.168.50.62:11434
**Hypothesis**: qwen3-embedding:0.6b was chosen for speed. At 19K+ memories, retrieval quality may be suffering — small embedding models lose semantic nuance that causes relevant memories to rank below the top-10 cutoff.
**Test**: Store 5 test memories with known content across distinct topics. Query for each using paraphrased phrasing (not exact match). Record whether correct memory appears in top-3 results. Repeat for 10 query pairs. Compute hit-rate.
**Verdict threshold**:
- FAILURE: hit-rate < 60% (embedding model is losing too much semantic signal)
- WARNING: hit-rate 60–79% (acceptable but upgrade to qwen3-embedding:4b worth benchmarking)
- HEALTHY: hit-rate >= 80% (model adequate for current scale)

**Context**: Ollama inference runs on 192.168.50.62 (RTX 3090). BrickLayer runs on the 3060 machine — this is a network call to the 3090, not local inference. Upgrading to 4b is server-side only.

---

## Q-C24.2 [AGENT] Consolidation threshold regression — is 0.78 causing memory loss?
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: POST /admin/consolidate + GET /search/query
**Hypothesis**: Consolidation threshold was lowered from 0.85 to 0.78 (v3.0 change). At 0.78, memories that are similar-but-distinct may be merged, permanently losing the more specific one.
**Test**: Store two memories that are related but meaningfully different (e.g., "qwen3:14b performs well on signal detection" and "qwen3:14b is slow under concurrent load"). Run consolidation. Query for both. Check if both are still retrievable as separate memories.
**Verdict threshold**:
- FAILURE: one or both memories gone or merged after consolidation (threshold too aggressive)
- WARNING: memories retrievable but one scores significantly lower (partial merge degraded importance)
- HEALTHY: both memories independently retrievable with correct content after consolidation

**Context**: `consolidation_threshold` default is 0.78 in config.py (was 0.85). Tunable via Redis key `recall:tuning:consolidation_threshold`, range 0.70–0.90.

---

## Q-C24.3 [PERFORMANCE] Signal detection hook latency — is 180s timeout causing stalls?
**Status**: PENDING
**Mode**: performance
**Target**: POST /memory/store (signal detection path via qwen3:14b)
**Hypothesis**: `signal_detection_timeout=180s` means the recall-retrieve hook could block Claude Code for up to 3 minutes if qwen3:14b is under load on the 3090. The stop hook was already cut to 4s/8s — signal detection needs the same scrutiny.
**Test**: Fire 10 sequential store requests with content that triggers signal detection (conversational text, not pure data). Measure wall-clock time per request. Record p50/p95/p99 latency.
**Verdict threshold**:
- FAILURE: p95 > 10000ms (hook would cause noticeable Claude Code stall)
- WARNING: p95 > 3000ms (acceptable but worth reducing timeout to 30s)
- HEALTHY: p95 <= 3000ms and no timeouts (180s limit is safe headroom, not a risk)

**Context**: `signal_detection_timeout` is 180.0s in config.py. The recall-retrieve hook fires on every user prompt submit — latency here directly impacts Claude Code responsiveness.

---

## Q-C24.4 [AGENT] Semantic dedup threshold — is 0.90 dropping valid distinct memories?
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: POST /memory/store (dedup path)
**Hypothesis**: `semantic_dedup_threshold` dropped from 0.95 to 0.90. At 0.90, two memories sharing the same topic but expressing different facts may be deduplicated on store — the second never persists.
**Test**: Store two semantically related but factually distinct memories back-to-back (similarity ~0.91–0.93 range). Verify both are retrievable. Then store a near-duplicate (similarity ~0.97) and confirm dedup fires correctly.
**Verdict threshold**:
- FAILURE: distinct memories (similarity < 0.93) are being dropped on store
- WARNING: threshold is working but edge cases within 0.90–0.93 band are unpredictable
- HEALTHY: dedup fires only on near-duplicates (>= 0.95 effective behavior); distinct memories persist

**Context**: `semantic_dedup_threshold=0.90` in config.py (was 0.95). Dedup happens at store time — unlike consolidation, it is not reversible.


---

## Wave 8 — Hypothesis Generator (qwen2.5:7b)

*Generated by BrickLayer local inference from campaign findings patterns.*

---

## Q8.1 [Concurrency] Concurrency Guard Verification
**Mode**: agent
**Status**: PENDING
**Hypothesis**: The concurrency guard implementation will handle high concurrency scenarios without service-unreachable errors.
**Test**: pytest --concurrent-users=50 -m "concurrency_guard"
**Verdict threshold**:
- FAILURE: Service unreachable or unexpected error rate > 1%
- WARNING: More than 3 warnings logged during test
- HEALTHY: Test passes with no errors

**Derived from**: Q1.5, Q2.4 (Q3.3)

---

## Q8.2 [Cache] Cache Consistency Under Load
**Mode**: agent
**Status**: PENDING
**Hypothesis**: The cache will remain consistent under high load without silent failures.
**Test**: pytest --concurrent-users=100 -m "cache_consistency"
**Verdict threshold**:
- FAILURE: More than 5% of requests fail due to cache inconsistencies
- WARNING: More than 2 warnings logged during test
- HEALTHY: Test passes with no errors

**Derived from**: Q3.2, Q6.4 (Q3.3)

---

## Q8.3 [Embedding] Embedding Batch Failure Handling
**Mode**: agent
**Status**: PENDING
**Hypothesis**: The embedding batch failure handling will produce zero-vectors without affecting performance.
**Test**: pytest --test-embed-batch-failure -m "embedding_batch"
**Verdict threshold**:
- FAILURE: More than 10% of batches fail and produce non-zero vectors
- WARNING: More than 3 warnings logged during test
- HEALTHY: Test passes with no errors

**Derived from**: Q3.5, Q6.4 (Q7.1)

---

## Q8.4 [Logging] Exception Path Logging Compliance
**Mode**: agent
**Status**: PENDING
**Hypothesis**: All exception paths will be logged as required.
**Test**: pytest --test-logging -m "exception_paths"
**Verdict threshold**:
- FAILURE: More than 5 unlogged exceptions found during test
- WARNING: More than 2 warnings logged during test
- HEALTHY: Test passes with no errors

**Derived from**: Q5.3, Q7.6 (Q5.5)

---

## Wave 9 — Scale, Concurrency, Quality Decay, and Failure Recovery

*Added 2026-03-14. Covers five untested risk areas: scale boundaries at 20K+ memories,
concurrent hook latency, importance decay burial, storage failure recovery, and regression hardening.*

---

## Q9.1 [PERFORMANCE] Qdrant store latency curve — does it spike as memory count grows?
**Status**: PENDING
**Mode**: performance
**Target**: POST /memory/store (bulk insertion path)
**Hypothesis**: At 20K+ memories, Qdrant's HNSW index segment merges cause periodic latency spikes during bulk stores. Individual stores at low volume are fast (Q-C24.3: p95=371ms) but a burst of 100+ stores may trigger a segment merge that blocks new writes for several seconds.
**Test**: Fire 100 sequential store requests with varied content (domain: autoresearch-scale-test). Measure latency per request. Look for: sustained latency increase after ~50 stores (indicating index growth pressure), any single request exceeding 5000ms (segment merge stall), overall p95 vs. the Q-C24.3 baseline of 371ms.
**Verdict threshold**:
- FAILURE: any single store > 5000ms OR p95 > 2000ms across the 100-store burst
- WARNING: p95 > 1000ms (2.7x above Q-C24.3 baseline) OR any store > 2000ms
- HEALTHY: p95 ≤ 1000ms and no outlier spikes — HNSW handles 20K+ gracefully

---

## Q9.2 [PERFORMANCE] Consolidation time at 20K+ memories — linear or exponential?
**Status**: PENDING
**Mode**: performance
**Target**: POST /admin/consolidate
**Hypothesis**: Consolidation clusters similar memories using embedding similarity. At 20K memories, the pairwise comparison space is large enough that each consolidation run takes >60s, which could cause HTTP timeouts from the Claude Code hook or dashboard.
**Test**: Time 3 successive POST /admin/consolidate calls (wall clock, not just HTTP response — if it's async, poll for completion). Record wall-clock duration per run. Check if duration is growing (each run has fewer candidates so should be faster, not slower).
**Verdict threshold**:
- FAILURE: any consolidation run > 120s wall clock (hook timeout risk)
- WARNING: any run > 60s OR duration growing across successive runs (runaway complexity)
- HEALTHY: all runs < 60s and duration stable or decreasing

---

## Q9.3 [PERFORMANCE] Concurrent recall-retrieve hook latency — 5 simultaneous Claude sessions
**Status**: PENDING
**Mode**: performance
**Target**: POST /search/query (the endpoint the recall-retrieve hook calls)
**Hypothesis**: The recall-retrieve hook fires on every Claude Code prompt. With multiple Claude Code instances running (casaclaude + proxyclaude + others), 5+ concurrent search queries could cause p99 to spike above 2000ms — blocking every Claude session waiting on Recall.
**Test**: Fire 5 concurrent POST /search/query requests simultaneously (asyncio.gather). Repeat 10 rounds. Measure p50/p95/p99 across all 50 requests. Compare to Q1.1 baseline (5 concurrent users: p99=24.4ms).
**Verdict threshold**:
- FAILURE: p99 > 2000ms (Claude Code sessions would visibly stall)
- WARNING: p99 > 500ms (noticeable delay, acceptable but worth reducing)
- HEALTHY: p99 ≤ 500ms under 5 concurrent sessions

---

## Q9.4 [AGENT] Importance decay burial — are old memories still surfacing at 20K+?
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: POST /search/query + Recall memory store
**Hypothesis**: After multiple decay cycles at 20K+ memories, memories older than 30 days have had their importance scores reduced enough that they no longer appear in top-10 results even when directly relevant. Recent memories crowd out older ones regardless of relevance.
**Test**: Store 3 memories with unique, highly specific content that would never appear naturally in the corpus (use rare/distinctive phrases). Wait — or check timestamps of existing old memories if the API exposes them. Query for each using the exact key phrase. Check: (1) does the memory appear in results at all, (2) what rank/score does it have. Also query for a topic you know has many recent memories to see if old relevant ones still surface.
**Verdict threshold**:
- FAILURE: specific memories stored >14 days ago are not retrievable by exact-phrase query (decay has buried them below retrieval floor)
- WARNING: memories retrievable but ranked below position 5 despite exact-phrase match (decay affecting relevance ranking)
- HEALTHY: memories retrievable at top-3 regardless of age when query is specific

---

## Q9.5 [AGENT] Qdrant-down mid-store — orphaned Neo4j nodes on partial failure
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: C:/Users/trg16/Dev/Recall/src/api/routes/memory.py, C:/Users/trg16/Dev/Recall/src/storage/qdrant.py, C:/Users/trg16/Dev/Recall/src/storage/neo4j_store.py
**Hypothesis**: The store path writes to both Qdrant (vector) and Neo4j (graph). If Qdrant is unavailable mid-store, the Neo4j node may still be created, leaving a graph node with no corresponding vector — an orphan that consumes graph resources but can never be retrieved by semantic search.
**Test**: Read the store orchestration code. Look for: transaction boundaries across Qdrant + Neo4j writes, rollback behavior if Qdrant write fails after Neo4j write succeeds, any cleanup/orphan detection mechanism, whether the write order (Neo4j first vs. Qdrant first) determines which orphan type is created.
**Verdict threshold**:
- FAILURE: Neo4j write happens before Qdrant write with no rollback on Qdrant failure (orphaned graph nodes guaranteed on any Qdrant outage)
- WARNING: write order is safe (Qdrant first) but no orphan detection exists for pre-existing orphans
- HEALTHY: either atomic transaction across both stores, OR Qdrant-first with Neo4j rollback on failure, OR orphan detection/cleanup job exists

---

## Q9.6 [AGENT] Redis-down startup — does write_guard fail open or closed?
**Status**: PENDING
**Mode**: agent
**Agent**: quantitative-analyst
**Target**: C:/Users/trg16/Dev/Recall/src/core/write_guard.py, C:/Users/trg16/Dev/Recall/src/api/main.py
**Hypothesis**: The write guard uses Redis for deduplication. If Redis is unavailable at startup or mid-session, the write guard may silently disable deduplication (fail open), allowing duplicate memories to flood Qdrant. This is the opposite of a safe default — a storage system should fail closed (reject writes) or at minimum warn loudly.
**Test**: Read src/core/write_guard.py. Look for: the Redis connection initialization path, what happens on `redis.exceptions.ConnectionError` during SETNX, whether there's a fallback mode, what the startup health check does with Redis unavailability, and whether the API rejects store requests or allows them when Redis is down.
**Verdict threshold**:
- FAILURE: Redis failure causes write_guard to skip dedup silently — stores proceed without dedup check (fail open, no warning)
- WARNING: Redis failure raises an exception that aborts the store (fail closed) but no structured log is emitted and /health still returns green
- HEALTHY: Redis failure is detected, logged with structured context, /health reflects degraded state, and store either fails closed or falls back to in-process dedup

---

## Q9.7 [AGENT] test-writer → hygiene and dream_consolidation worker test suites
**Status**: PENDING
**Mode**: agent
**Agent**: test-writer
**Finding**: Q7.6
**Source**: src/workers/hygiene.py
**Hypothesis**: Q7.6 confirmed hygiene.py and dream_consolidation.py have structured exception logging (source-read verdict) but no dedicated test suite. The same test-writer pattern that produced 17 tests for decay.py in Q5.7 should be applied to both remaining workers — covering their error paths, loop logic, and exception handling.
**Verdict threshold**:
- HEALTHY: test files exist for both workers; coverage ≥ 70% per file; all error-path branches covered; all tests pass
- WARNING: tests written but coverage < 70% on either file
- INCONCLUSIVE: agent produced no structured output

**Derived from**: Q7.6 (INCONCLUSIVE — source read only, no tests), Q5.7 (HEALTHY — decay worker pattern to follow)

---

## Q9.8 [CORRECTNESS] Regression sweep — re-run all previously FAILURE/WARNING questions
**Status**: PENDING
**Mode**: correctness
**Target**: results.tsv (all WARNING verdicts)
**Hypothesis**: Several questions were resolved as WARNING (Q1.5, Q3.3, Q3.5, Q6.4, Q6.5) with fixes applied in subsequent agent waves. No question has re-run the original WARNING tests to confirm the fixes held. A regression could have been introduced by any of the ~15 commits made since those findings.
**Test**: Re-run the original tests for each WARNING question:
- Q1.5: `pytest C:/Users/trg16/Dev/Recall/tests/api/test_security_hardening.py -k "consolidat" -v --tb=short -q`
- Q3.3: Read src/core/write_guard.py — confirm asyncio.Lock present on Redis lock path
- Q3.5: Read src/core/embeddings.py — confirm embed_batch failure path logs structured error
- Q6.4: Read src/core/retrieval.py + embeddings.py + tuning_config.py — confirm locks present on all three caches
**Verdict threshold**:
- FAILURE: any original WARNING condition is still present (fix was not committed or was reverted)
- WARNING: fixes present but no test covers the fixed path (regression risk without test coverage)
- HEALTHY: all original WARNING conditions resolved; tests cover the fix paths


---

*Follow-up drill-down for Q9.4 — WARNING verdict*

## Q9.4.1 [Memory Decay] Why are old memories still ranking in top positions?
**Mode**: agent
**Status**: PENDING
**Hypothesis**: The decay algorithm is not effectively reducing the importance scores of older memories, leading to their continued high rankings.
**Test**: Increase the age of the stored memories by 5-7 days and re-run the queries. Observe if the rank/score of old memories improves or remains unchanged.
**Verdict threshold**:
- FAILURE: Old memories continue to rank in top positions (positions 1-3) after increased age.
- WARNING: Old memories still rank between positions 2-6 but show slight improvement in ranking.
- HEALTHY: Old memories consistently rank below position 5, indicating effective decay application.
**Derived from**: Q9.4 (WARNING)

---

## Q9.4.2 [Importance Score] What is the impact of base importance on memory retrieval?
**Mode**: agent
**Status**: PENDING
**Hypothesis**: The low base importance score (0.32) is causing older memories to be displaced by more recent, higher-importance ones.
**Test**: Store new memories with a base importance score significantly higher than 0.32 and compare their retrieval rank against the old memories.
**Verdict threshold**:
- FAILURE: Old memories still outperform newer, high-importance memories in top rankings.
- WARNING: Newer, high-importance memories start to appear in top positions but older memories remain in lower ranks (positions 4-6).
- HEALTHY: Older memories consistently rank below position 5 regardless of the base importance score.
**Derived from**: Q9.4 (WARNING)

---

## Q9.4.3 [Decay Application] Is decay being applied uniformly across all memories?
**Mode**: agent
**Status**: PENDING
**Hypothesis**: Decay is not being applied consistently to older memories, leading to their continued high rankings.
**Test**: Check the decay ratios of multiple old and recent memories to ensure they are consistent with expected values.
**Verdict threshold**:
- FAILURE: Decay ratios for old memories remain at 1.000 or close to it, indicating no decay application.
- WARNING: Some decay ratios for old memories show slight improvement but still not enough to affect their ranking.
- HEALTHY: Decay ratios for all memories consistently reflect the expected reduction over time.
**Derived from**: Q9.4 (WARNING)

---



---

*Follow-up drill-down for Q9.1 — FAILURE verdict*

## Q9.1.1 [AGENT] Qdrant HNSW configuration — is segment merge stall tunable?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The 5973ms max store latency from Q9.1 is a Qdrant HNSW segment merge stall — a known behavior when the index grows large. The collection may be using default HNSW parameters (m=16, ef_construction=100) that are suboptimal at 20K+ vectors. Tuning m lower (e.g., 8) or enabling on_disk_payload reduces merge pressure.
**Test**: Call GET /collections/{collection_name} on the Qdrant API (http://192.168.50.19:6333) to retrieve the current HNSW config (m, ef_construction, on_disk_payload, indexing_threshold). Compare against recommended values for a 20K+ vector collection. Check the collection's segment count — high segment count confirms merge pressure.
**Verdict threshold**:
- FAILURE: m >= 16 AND indexing_threshold at default AND segment count > 5 (all factors pointing to merge pressure with no mitigation)
- WARNING: suboptimal config detected but partial mitigation in place
- HEALTHY: m <= 8 OR on_disk_payload=true OR indexing_threshold tuned for low-merge operation
**Derived from**: Q9.1 (FAILURE)

---

## Q9.1.2 [AGENT] Qdrant collection segment count at 20K+ vectors
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: At 20K+ memories, the Qdrant collection has accumulated many small segments that trigger frequent merges. Each merge briefly blocks new vector writes, causing the 5-6s latency spike. The segment count is directly observable via the Qdrant API and confirms/rules out this cause.
**Test**: Call GET /collections/{collection_name}/cluster and GET /collections/{collection_name} on the Qdrant API (http://192.168.50.19:6333). Check: (1) segments_count in the collection info, (2) optimizer_status, (3) vectors_count. A high segment count (>10) with optimizer running confirms the hypothesis.
**Verdict threshold**:
- FAILURE: segments_count > 10 AND optimizer_status != "ok" (active merge contention)
- WARNING: segments_count > 5 (merge pressure building)
- HEALTHY: segments_count <= 5 and optimizer_status = "ok"
**Derived from**: Q9.1 (FAILURE)

---

## Q9.1.3 [AGENT] Qdrant optimizer config — is indexing_threshold set for write throughput?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: Qdrant's indexing_threshold controls when segments get merged into the HNSW index. The default (20000 vectors) means the index triggers a full rebuild at 20K vectors — exactly the corpus size in Q9.1. Lowering indexing_threshold or tuning max_segment_size would reduce stall frequency.
**Test**: Call GET /collections/{collection_name} on the Qdrant API (http://192.168.50.19:6333). Check: (1) config.optimizer_config.indexing_threshold, (2) config.optimizer_config.max_segment_size, (3) config.optimizer_config.memmap_threshold. Compare against the Qdrant documentation recommendation for write-heavy workloads.
**Verdict threshold**:
- FAILURE: indexing_threshold at default (20000) with corpus already at 20K+ (exact trigger point for full reindex)
- WARNING: threshold within 20% of corpus size
- HEALTHY: threshold significantly above corpus size or max_segment_size tuned to limit merge scope
**Derived from**: Q9.1 (FAILURE)

---



---

*Wave 10 — Post-fix validation + corpus health*

## Q10.1 [AGENT] Decay effectiveness post-fix — are importance scores actually decreasing now?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The Q9.4 UTC timezone bug (ac0454b) silently skipped all memories stored before the Q6.7 utcnow() migration. Now that the fix is deployed, the decay worker should be processing those memories and reducing their importance. This question verifies the fix worked end-to-end on the live system.
**Test**: Hit the Recall API (http://192.168.50.19:8200, Bearer token auth). (1) Query for 5 memories older than 14 days using GET /memories with a broad search. (2) Record their current `importance` and `initial_importance` fields. (3) Calculate decay ratio = importance / initial_importance for each. (4) Check the audit_log table via GET /admin/audit-log or similar for recent `decay` entries to confirm the worker is running. Compare decay ratios against the Q9.4 baseline (all ratios = 1.000 for 25-28d memories).
**Verdict threshold**:
- FAILURE: decay ratios still all 1.000 for memories >14 days old (fix not taking effect)
- WARNING: some decay observed but ratios > 0.95 for memories >21 days old (decay rate too slow)
- HEALTHY: decay ratios < 0.95 for memories >14 days old AND audit_log shows recent decay runs
**Derived from**: Q9.4 (WARNING) + fix commit ac0454b

---

## Q10.2 [AGENT] Live orphan count — how many Qdrant-only ghost vectors exist today?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: Q9.4 confirmed a Qdrant-Postgres desync — memories that appear in vector search results but return 404 on direct GET. These are Qdrant vectors with no corresponding Postgres/Neo4j record. The reconcile worker runs Sunday 5:30am, so the current orphan backlog is unmeasured. High orphan counts degrade search precision and waste index space.
**Test**: Call POST /reconcile?repair=false on the Recall API (http://192.168.50.19:8200, Bearer token auth). Record: (1) `qdrant_orphans` count — vectors in Qdrant with no Neo4j node, (2) `neo4j_orphans` count — nodes in Neo4j with no Qdrant vector, (3) total corpus size. Calculate orphan rate = (qdrant_orphans + neo4j_orphans) / total. Also check `importance_mismatches` and `superseded_mismatches` counts.
**Verdict threshold**:
- FAILURE: orphan rate > 5% OR qdrant_orphans > 1000 (significant index pollution)
- WARNING: orphan rate 1-5% OR any mismatches > 100 (manageable but needs first reconcile run)
- HEALTHY: orphan rate < 1% AND mismatches < 100

---

## Q10.3 [AGENT] Initial importance calibration — are high-signal memories getting appropriate scores?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: Q9.4 found old memories with `importance=0.32` being outranked by new memories at `0.44–1.0`. If the signal extraction pipeline systematically assigns low initial importance to certain memory types (e.g., semantic vs episodic, short content vs long), relevant old memories get buried by rank displacement even before decay runs. This is a calibration problem independent of the decay bug.
**Test**: Query the Recall API (http://192.168.50.19:8200) for a sample of 50+ memories across different `memory_type` values (semantic, episodic, procedural). Record the `importance` distribution per type. Compute: mean, p25, p75 per type. Also check if there's a correlation between content length and importance score by sampling 10 short (<50 chars) and 10 long (>200 chars) memories and comparing importance.
**Verdict threshold**:
- FAILURE: mean importance < 0.35 for any memory type (systematic undervaluing causes burial before decay)
- WARNING: p25 importance < 0.30 for any type OR >30% of memories at exactly 0.32 (default value, signal extraction not running)
- HEALTHY: mean importance >= 0.40 across all types AND p25 >= 0.30 (distribution reflects signal quality)

---

## Q10.4 [AGENT] Consolidation dedup rate at 20K+ — is the corpus bloated with near-duplicates?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The consolidation worker runs every hour and merges memories with cosine similarity above a threshold. At 20K+ memories, if the threshold is too conservative or the worker is skipping memories, near-duplicates accumulate and dilute search results — multiple near-identical vectors crowd the top-k results for any query.
**Test**: (1) Call POST /admin/consolidate (or GET /admin/consolidate/status) to get consolidation stats — how many merges have happened total, last run time, pending candidates. (2) Run 3 test searches for very specific phrases and count how many of the top-10 results are semantically near-identical (same content, different timestamps). (3) Check the consolidation worker logs via GET /admin/audit-log filtering on action='consolidate'. Report: total_merges_lifetime, merges_last_24h, near_duplicate_rate in top-10 results.
**Verdict threshold**:
- FAILURE: >3 near-identical results in top-10 for a specific-phrase query (dedup not working)
- WARNING: consolidation last_run > 4 hours ago OR merges_last_24h = 0 with corpus > 10K
- HEALTHY: near_duplicate_rate < 1 in top-10 AND consolidation ran within last 2 hours

---

*Follow-up drill-down for Q9.5 — WARNING verdict*

## Q9.5.1 [AGENT] Transaction boundary verification
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The transaction boundaries between Qdrant and Neo4j writes are not properly managed, leading to potential race conditions.
**Test**: Read C:/Users/trg16/Dev/Recall/src/api/routes/memory.py and C:/Users/trg16/Dev/Recall/src/storage/qdrant.py and C:/Users/trg16/Dev/Recall/src/storage/neo4j_store.py. Review the code for explicit transaction management or isolation levels that ensure both writes are committed atomically.
**Verdict threshold**:
- FAILURE: Lack of transactional guarantees
- WARNING: Inconsistent transaction handling logic
- HEALTHY: Explicit transaction boundaries with proper rollback behavior
**Derived from**: Q9.5 (WARNING)

---

## Q9.5.2 [AGENT] Rollback mechanism validation
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The rollback mechanism for Neo4j writes in case of Qdrant failure is insufficient, potentially leaving orphaned nodes.
**Test**: Read C:/Users/trg16/Dev/Recall/src/api/routes/memory.py. Inspect the code to ensure that a failed Qdrant write triggers a proper rollback in Neo4j, deleting any created nodes.
**Verdict threshold**:
- FAILURE: Missing or ineffective rollback mechanism
- WARNING: Incomplete or conditional rollback logic
- HEALTHY: Robust rollback behavior for both stores
**Derived from**: Q9.5 (WARNING)

---

## Q9.5.3 [AGENT] Orphan detection and cleanup
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: There is no mechanism in place to detect or clean up orphaned Neo4j nodes, leading to potential resource leaks.
**Test**: Read C:/Users/trg16/Dev/Recall/src/workers/hygiene.py. Check for any existing mechanisms that periodically scan the graph for orphaned nodes and delete them.
**Verdict threshold**:
- FAILURE: No orphan detection or cleanup mechanism
- WARNING: Inadequate or infrequent orphan detection
- HEALTHY: Regular and effective orphan detection and cleanup process
**Derived from**: Q9.5 (WARNING)

---


---

*Wave 12 — ML observability, classifier health, corpus recovery*

## Q12.1 [AGENT] ML health dashboard: add `ml` key to /admin/health/dashboard
**Mode**: agent
**Agent**: benchmark-engineer
**Status**: PENDING
**Hypothesis**: The main health dashboard has no ML section (Q11.3). Operators monitoring /admin/health/dashboard are blind to reranker and signal classifier degradation. The 6-day silent reranker failure (Q10.5) is the proof case. Adding an `ml` aggregation block with staleness + cv_score thresholds gives ops visibility with minimal implementation cost.
**Test**: (1) Verify current dashboard response has no `ml` key (baseline). (2) Inspect src/api/routes/admin.py — find the health/dashboard endpoint and the ML status endpoints. (3) Add `ml` aggregation block: reranker (cv_score, trained_at, staleness_hours, health=HEALTHY/WARNING/FAILURE) + signal_classifier (binary_cv_score, type_cv_score, trained_at, staleness_hours, health). Thresholds: HEALTHY cv>=0.85 staleness<168h; WARNING cv 0.70-0.84 or staleness 168-336h; FAILURE cv<0.70 or staleness>336h. (4) Verify dashboard response now includes `ml` key with correct data. (5) Write 2 tests asserting ml section present and thresholds applied.
**Verdict threshold**:
- FAILURE: Dashboard still missing ML section after implementation attempt OR cv_score thresholds not applied
- WARNING: ML section present but staleness or threshold logic incorrect
- HEALTHY: Dashboard includes ml.reranker + ml.signal_classifier with live data and correct health classification
**Derived from**: Q11.3 (WARNING — ML health not in dashboard)

---

## Q12.2 [AGENT] Signal classifier retraining: does a scheduled cron exist?
**Mode**: agent
**Agent**: benchmark-engineer
**Status**: PENDING
**Hypothesis**: The reranker has a cron trigger in WorkerSettings. The signal classifier's `trained_at=2026-03-08` (6 days at Q11.3 measurement) suggests it has no scheduled retraining. If so, type classification accuracy (currently 0.6488) will degrade further as new signal patterns accumulate that the 2026-03-08 model has never seen.
**Test**: (1) Read src/workers/main.py — find WorkerSettings.cron_jobs. List all scheduled jobs and whether signal classifier retraining appears. (2) Grep src/ for train_signal_classifier or equivalent — find where classifier retraining is triggered and whether it has a cron schedule. (3) If no cron: add one with weekly cadence (same pattern as reranker). (4) If cron exists: verify it's actually firing by checking GET /admin/audit-log for classifier training events. (5) After any fix, confirm signal classifier trained_at is < 7 days old.
**Verdict threshold**:
- FAILURE: No retraining trigger exists anywhere (manual only) AND trained_at > 14 days
- WARNING: Retraining trigger exists but not scheduled OR last retrain > 7 days ago
- HEALTHY: Scheduled cron confirmed AND trained_at < 7 days old
**Derived from**: Q11.3 (WARNING — signal classifier stale; no retraining cron found)

---

## Q12.3 [AGENT] Corpus mean importance recovery — has Q10.3.2 rubric moved the needle?
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: Q11.2 projected 2-3 weeks for corpus mean to cross 0.40 via natural decay + new well-scored signals. With the rubric fix deployed (2026-03-14) and amnesty applied (floor=0.3 on 3,858 memories), the distribution should now be accumulating new 0.5+ technical domain signals. This question measures actual trajectory.
**Test**: (1) Call GET /admin/health/memory-quality. Record mean_quality and histogram. (2) Compare to Q11.2 baseline (mean=0.393, 57% below 0.40). (3) Query /memories for 10 most recently stored memories (sort by created_at desc) — check their importance values. If rubric is working, recent technical domain memories should score 0.5+. (4) Compute how many new memories have been stored since 2026-03-14 via the admin stats or audit log. (5) Project time-to-HEALTHY based on current trajectory.
**Verdict threshold**:
- FAILURE: Mean still < 0.393 (trajectory flat or declining — rubric fix not taking effect)
- WARNING: Mean 0.393-0.399 (recovering but not yet HEALTHY — expected if < 2 weeks post-fix)
- HEALTHY: Mean >= 0.40 AND recent memories show importance >= 0.5 for technical domains
**Derived from**: Q11.2 (WARNING — amnesty insufficient; natural recovery expected)

---

## Q12.4 [AGENT] Signal classifier type accuracy post-retraining
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: The signal classifier's type_cv_score=0.6488 (Q11.3) is marginal for production use. With 9,000+ signals now available (vs 1,209 training samples at 2026-03-08), retraining on the full corpus should materially improve type accuracy. Target: type_cv >= 0.75.
**Test**: (1) Check current signal classifier status via GET /admin/ml/signal-classifier-status. Record trained_at, n_samples, type_cv_score. (2) If retrain cron added by Q12.2 and a retrain has run: compare new type_cv_score to Q11.3 baseline (0.6488). (3) If no retrain yet: manually trigger retraining (POST /admin/ml/retrain-signal-classifier or equivalent). (4) Measure delta in type_cv_score. (5) Check type_distribution for class imbalance — if any type has <20 samples, flag it.
**Verdict threshold**:
- FAILURE: type_cv_score still < 0.65 after retrain on expanded dataset (model architecture limitation)
- WARNING: type_cv_score 0.65-0.74 (improvement but below target)
- HEALTHY: type_cv_score >= 0.75 AND all type classes have >= 20 samples
**Derived from**: Q11.3 (WARNING — type_cv=0.6488 marginal)

---

## Q12.5 [AGENT] Decay correctness at recalibrated importance baseline
**Mode**: agent
**Agent**: quantitative-analyst
**Status**: PENDING
**Hypothesis**: Q10.1 confirmed decay working at corpus scale. With technical domain memories now scoring 0.5-0.8 (vs 0.1-0.3 before the rubric fix), the decay worker should apply proportional decay. The risk is that the decay formula's half-life tuning was calibrated against the old 0.3-0.4 distribution — at 0.6-0.8 starting points, memories might over-decay to noise faster than expected, or conversely be protected by importance guards.
**Test**: (1) Find 5 memories stored after 2026-03-14 with importance >= 0.5 (technical domain, newly scored by rubric). Record their importance and initial_importance. (2) Check these same memories 7 days later — or if that's not possible, find technical domain memories from a prior session with known initial_importance and check their current decay ratio. (3) Compare decay ratio to pre-rubric memories at similar age to determine if decay rate is consistent. (4) Check decay worker config for any importance-dependent decay rate or floor protection.
**Verdict threshold**:
- FAILURE: High-importance memories (>0.6) decaying faster than expected (ratio < 0.80 within 7 days, no access)
- WARNING: Decay rate inconsistent between pre-rubric (0.3-0.4 initial) and post-rubric (0.5-0.8 initial) memories
- HEALTHY: Decay ratio consistent across importance tiers AND no unexpected floor hits within 14 days
**Derived from**: Q10.1 (HEALTHY) + Q10.3.2 (rubric fix changing baseline importance distribution)

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

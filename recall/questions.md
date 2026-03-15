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
**Status**: DONE
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
**Status**: DONE
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

## Wave 13 — Retrieval Health and Coverage (Q13.x)

*Derived from Wave 12 live system observability audit (2026-03-14). These questions probe the gap between what Recall stores and what it actually surfaces.*

---

## Q13.1 [DOMAIN-5] Retrieval coverage rate — why are 86–93% of memories never surfaced?
**Status**: DONE
**Mode**: benchmark
**Target**: GET /admin/health/distributions + recall_retrieve.js hook
**Hypothesis**: With 20,536 stored memories but only ~447 injection events, the retrieval coverage rate is 7–14%. Most memories are permanently invisible because: (a) vector search returns top-K from a large pool so low-ranked memories are never selected, (b) the hook's `adaptiveFilter` raises the similarity floor over time, and (c) the hook skips short prompts entirely. The practical effect is that Recall accumulates memories faster than it can serve them, and the oldest/lowest-importance content never re-enters the context window.
**Test**: Query `/admin/health/distributions` for injection rate. Cross-check `/memories/stats` for total count. Compute coverage = injections_30d / total_memories. Sample 20 memories that have never been retrieved (access_count=0 AND created_at < 30d ago) to assess whether they are genuinely valuable or safely ignorable.
**Verdict threshold**:
- FAILURE: coverage rate < 10% AND sampled never-retrieved memories contain ≥5 that are genuinely useful (high-value knowledge being buried)
- WARNING: coverage rate < 20% but never-retrieved memories are mostly low-value artifacts
- HEALTHY: coverage rate ≥ 20% OR never-retrieved memories are demonstrably low-value (working as designed)

**Derived from**: Wave 12 live audit — 20,536 memories stored, ~447 injections observed, estimated 7–14% coverage rate
**Simulation path**: benchmark-engineer fetches stats + samples never-retrieved memories via /search/browse filtered by access_count=0; apply by-design content audit protocol before finalizing verdict

---

## Q13.1a [DOMAIN-5] MIN_SIMILARITY threshold sweep — what floor maximizes useful injections without noise?
**Status**: DONE
**Mode**: benchmark
**Target**: recall-retrieve.js MIN_SIMILARITY + injection_log feedback quality
**Hypothesis**: Lowering MIN_SIMILARITY from 0.45 to 0.40 would expose the 2,456 memories in the 0.40–0.45 similarity band. If the implicit feedback loop rates ≥50% of these additional injections as useful (topic overlap on next prompt), the lower floor is warranted. If <30% useful, the floor is correctly calibrated.
**Test**: Sample 30 injection events where max_raw_similarity falls in 0.40–0.45. Cross-reference against subsequent prompt terms using the implicit feedback heuristic (>20% term overlap = useful). Report: useful rate, noise rate, ambiguous rate.
**Verdict threshold**:
- FAILURE: >70% of 0.40–0.45 range injections would be noise (floor is correct, problem is structural)
- WARNING: 30–70% useful (borderline — lower floor helps but doesn't solve the coverage problem)
- HEALTHY: ≥70% useful (lower floor recommended — would expand coverage without hurting precision)
**Derived from**: Q13.1 FAILURE finding — MIN_SIMILARITY=0.45 excludes 2,456 memories in the 0.40–0.44 band

---

## Q13.1b [DOMAIN-5] High-importance never-retrieved memories — content audit
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant recall_memories, importance ≥ 0.6, access_count = 0
**Hypothesis**: Of the estimated 4,996 high-importance (≥0.6) memories with access_count=0, a meaningful fraction are genuinely high-value knowledge being buried. If ≥30% are high-value, the coverage problem is urgent and affects Tim's most important stored knowledge.
**Test**: Sample 50 memories from Qdrant where importance ≥ 0.6 AND access_count = 0. Classify each as: high-value (specific, actionable, relevant to active projects), medium-value (generally useful but not urgent), low-value (synthetic/test content, outdated, redundant with existing memories).
**Verdict threshold**:
- FAILURE: ≥30% of high-importance never-retrieved memories are high-value (urgent: important knowledge is permanently buried)
- WARNING: 15–30% are high-value (notable: some important knowledge is buried but not catastrophic)
- HEALTHY: <15% are high-value (high-importance memories are mostly redundant/synthetic noise)
**Derived from**: Q13.1 FAILURE finding — 3,945 memories with importance 0.6–0.8 and 1,351 with 0.8–1.0; estimated 94.6% never injected

---

## Q13.2 [DOMAIN-1] fact_extraction empty rate — 30.2% of LLM extraction calls return nothing
**Status**: DONE
**Mode**: simulation
**Target**: observe-edit.js hook → /extract endpoint
**Hypothesis**: 30.2% of fact_extraction pipeline calls return empty results (no facts extracted). This is wasted Ollama inference (qwen3:14b at ~15s/call). Root causes may be: (a) edits to config/JSON/YAML files where there are no facts to extract, (b) very small diffs below a meaningful content threshold, (c) LLM refusing to extract from non-prose content, or (d) structural prompt mismatch. If category (a)/(b) dominates, a pre-filter on file type or diff size could eliminate the waste without losing coverage.
**Test**: Pull the last 100 audit_log entries where action='extract' AND result IS NULL or empty. Classify by: file type edited, diff size (chars), content type (code/prose/config). Identify the dominant category. Simulate the impact of adding a pre-filter (e.g., skip if diff_chars < 200 OR file_ext in ['.json','.yaml','.toml','.lock']).
**Verdict threshold**:
- FAILURE: > 50% of empty extractions come from edits where facts genuinely exist but were missed (model failure, not pre-filterable)
- WARNING: 30–50% are pre-filterable but no filter is implemented
- HEALTHY: ≥ 80% of empty extractions are from pre-filterable content types (config/small diffs); pre-filter recommendation documented

**Derived from**: Wave 12 audit — fact_extraction empty rate 30.2% observed in /admin/health/distributions pipeline stats
**Simulation path**: quantitative-analyst queries audit_log, classifies empty extractions, tests threshold scenarios in simulate.py

---

## Q13.2a [DOMAIN-1] fact_extraction file-type breakdown — what fraction of empty extractions come from config/JSON/YAML files?
**Status**: DONE
**Mode**: benchmark
**Target**: observe-edit.js → /extract endpoint + prompt_metrics.metadata
**Hypothesis**: The 42.2% empty rate is dominated by config file edits (.json, .yaml, .toml, .md) which contain no extractable facts. If ≥60% of empty extractions come from these file types, adding them to a LOW_YIELD_EXTENSIONS filter in observe-edit.js would eliminate the majority of wasted Ollama calls without any loss of coverage.
**Test**: After instrumenting the /extract endpoint to persist file_ext in prompt_metrics.metadata (see Q13.2 mitigation #2), sample 100 recent empty extractions and classify by file extension. Report: empty rate per file type, fraction of total empty calls attributable to config types vs code files.
**Verdict threshold**:
- FAILURE: ≥50% of empty extractions come from code files (.py, .js, .ts) — model is failing to extract from valid content (structural problem, not filterable)
- WARNING: 30–60% from config types — filter helps but doesn't eliminate the problem
- HEALTHY: ≥60% from config/small-diff types — filter eliminates majority of waste without coverage loss
**Derived from**: Q13.2 WARNING finding — metadata.file_ext NULL prevented file-type analysis; gap must be closed before this question is answerable
**Prerequisite**: metadata.file_ext observability gap must be closed first (instrument /extract endpoint, collect 48h of data)

---

## Q13.3 [DOMAIN-5] p95 extraction latency — 15–16 second outliers in the extraction pipeline
**Status**: DONE
**Mode**: benchmark
**Target**: observe-edit.js → POST /extract (Ollama qwen3:14b)
**Hypothesis**: The p95 extraction latency of 15–16 seconds is 3–5× the expected inference time for qwen3:14b on an RTX 3090. The outliers are likely caused by: (a) Ollama model cold-start (first inference after idle period loads model to VRAM), (b) context window overflow forcing multi-pass chunking, or (c) RTX 3090 thermal throttling under sustained load. The p50 latency may be acceptable while the p95 creates perceived hook "freezes" for the user.
**Test**: Analyze the last 200 extract audit_log entries: compute p50/p75/p95/p99 latency. Identify whether outliers cluster at session start (cold-start signature) or are uniformly distributed (thermal/overflow signature). Check if outlier events correlate with large diff sizes (content length > X chars).
**Verdict threshold**:
- FAILURE: p95 > 20s OR outliers uniformly distributed (not cold-start, indicating sustained degradation)
- WARNING: p95 15–20s but outliers cluster at session start (acceptable cold-start behavior)
- HEALTHY: p95 ≤ 10s OR cold-start confirmed and mitigatable (e.g., Ollama keep_alive setting)

**Derived from**: Wave 12 audit — p95 latency 15–16s observed in /admin/health/distributions pipeline performance
**Simulation path**: benchmark-engineer queries audit_log for timing data, computes distribution, correlates with content size and time-of-day patterns

---

## Q13.3a [DOMAIN-5] Ollama concurrency limiter A/B — does max-1 in-flight extraction call reduce p95 below 10s?
**Status**: DONE
**Mode**: benchmark
**Target**: /extract endpoint → Ollama queue depth
**Hypothesis**: Adding a concurrency limiter (max 1 in-flight Ollama extraction call from the /extract endpoint) will eliminate compound queuing and reduce p95 from 14s to ≤10s. With 1 in-flight call, queue depth is bounded at 1 waiting request, so max wait = 1× inference time ≈ 4s + actual inference = ≤8s total, within the 10s HEALTHY threshold.
**Test**: Add a server-side semaphore (asyncio.Semaphore(1)) to the /extract endpoint. Measure p95 over 48h before/after. Compare: (a) p95 latency, (b) queue rejection rate (requests dropped due to full queue), (c) throughput (extractions/hour). A/B requires 48h of production traffic on both configurations.
**Verdict threshold**:
- FAILURE: p95 still >10s after limiter (queuing was not the cause — other mechanism responsible)
- WARNING: p95 drops to 10–14s (improvement confirmed but target not met; Ollama parallelization may also be needed)
- HEALTHY: p95 ≤10s (queuing was the dominant cause; limiter resolves the latency failure)
**Derived from**: Q13.3 FAILURE finding — uniform 22% slow rate attributed to Ollama request queuing; M/D/1 queue model predicts concurrency=1 fixes p95
**Prerequisite**: Implement asyncio.Semaphore(1) in /extract handler; deploy; collect 48h pre/post data

---

## Q13.4 [DOMAIN-1] observer supersedure rate — 46.7% of session summaries are over-deduped
**Status**: DONE
**Mode**: correctness
**Target**: recall-session-summary.js hook → /store deduplication logic
**Hypothesis**: The observer (session summary) pipeline shows a 46.7% supersedure rate — nearly half of all session summaries are being absorbed/merged into existing memories rather than stored as new entries. Session summaries are high-value durable memories that represent entire work sessions. If they are being collapsed into older memories with different content, recent session context is lost. The question is whether the dedup threshold is too aggressive for session-length content, or whether the summaries genuinely repeat the same topics.
**Test**: Fetch the last 20 session-summary memories that were superseded (action='store', result='superseded'). Compare the summary content against the memory they were merged into. Assess: (a) is the superseding memory actually semantically equivalent, or just topically similar? (b) What is the similarity score at which supersedure fires for these entries?
**Verdict threshold**:
- FAILURE: ≥ 5 of 20 superseded summaries contain unique session-specific facts that were lost (genuine data loss)
- WARNING: supersedure fires correctly but threshold is borderline (0.85–0.90 cosine) — recent summaries absorb into old ones without updating them
- HEALTHY: superseded summaries are genuinely redundant with the surviving memory; no unique facts lost

**Derived from**: Wave 12 audit — observer supersedure rate 46.7% observed; concern that high-value session summaries are being aggressively deduplicated
**Simulation path**: benchmark-engineer fetches superseded session summaries from audit_log, compares content pairs, applies by-design content audit protocol

---

## Q13.4a [DOMAIN-1] supersedure similarity threshold — what cosine score triggers deduplication?
**Status**: DONE
**Mode**: benchmark
**Target**: /store endpoint deduplication logic (server-side code)
**Hypothesis**: The supersedure threshold is below 0.90, which causes false-positive session merges where topically similar but session-distinct summaries are collapsed. If the threshold were raised to 0.92–0.95, the 14996103→de31f553 false-positive merge would not have fired.
**Test**: Inspect the /store endpoint source code to find the cosine similarity threshold for supersedure. Then query the audit_log supersede entries and cross-reference with Qdrant similarity scores (if stored in details) to compute the actual distribution of similarity scores at which supersedure fires. Report: threshold value, distribution of similarity scores for fired supersedures, recommended threshold.
**Verdict threshold**:
- FAILURE: threshold < 0.85 (too aggressive — semantically similar but content-distinct memories are being merged)
- WARNING: threshold 0.85–0.92 (borderline — some false positives likely, especially for repeated-topic sessions)
- HEALTHY: threshold ≥ 0.92 (calibrated correctly; rare false positives only)
**Derived from**: Q13.4 WARNING finding — audit_log details lacks similarity scores; threshold value unknown; one confirmed false-positive merge observed

---

## Q13.5 [DOMAIN-1] corpus/retrieval capacity imbalance — does storing more memories hurt retrieval quality?
**Status**: DONE
**Mode**: simulation
**Target**: simulate.py — vector search recall degradation model
**Hypothesis**: Recall stores memories indefinitely (with decay, but the floor prevents deletion). As the corpus grows from 20K → 50K → 100K memories, the top-K vector search returns the same K results but from a larger haystack — the signal-to-noise ratio degrades. A memory that would rank #3 in a 10K corpus might rank #12 in a 100K corpus and fall below the injection threshold. The system has no mechanism to retire truly dead memories (importance = floor, access_count = 0, age > 90d), so the haystack grows monotonically.
**Test**: Model retrieval precision as a function of corpus size. Assume: fixed top-K=10, target memories have importance~0.6, noise memories have importance~0.2. Sweep corpus sizes 10K / 20K / 50K / 100K / 200K. Compute probability that a target memory ranks in top-5 at each corpus size.
**Verdict threshold**:
- FAILURE: model predicts top-5 hit rate drops below 60% before corpus reaches 100K (urgent capacity problem)
- WARNING: degradation is gradual but meaningful retirement/pruning policy needed before 200K
- HEALTHY: top-5 hit rate stays above 80% through 200K corpus size (current growth rate not a near-term risk)

**Derived from**: Wave 12 audit — 20,536 stored memories growing monotonically; no memory retirement policy; 7–14% coverage rate already observed
**Simulation path**: quantitative-analyst models top-K precision degradation in simulate.py; sweep corpus_size parameter from 10K to 200K

---

## Q13.5a [DOMAIN-1] synthetic testbed memory retirement — how many testbed memories are eligible for bulk deletion?
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant recall_memories — testbed:* tagged entries
**Hypothesis**: ~15,000 of the 20,560 total memories are synthetic testbed entries (tagged testbed:a94448f4c891, testbed:1efb824d749c, etc. from autoresearch load testing). If ≥80% of these have access_count=0, a bulk delete would reduce corpus to ~6,000 real memories and restore top-5 hit rate to ~50%+ (from 5.4% current).
**Test**: Query Qdrant for memories with tags matching testbed:* pattern. Count: total testbed memories, those with access_count=0, importance distribution. Compute: expected coverage rate after bulk delete of access_count=0 testbed memories.
**Verdict threshold**:
- FAILURE: <50% of testbed memories are access_count=0 (they ARE being retrieved for real queries — deletion would hurt coverage)
- WARNING: 50–80% are access_count=0 (partial retirement viable)
- HEALTHY: ≥80% are access_count=0 (bulk retirement safe; would restore effective coverage to ~50%)
**Derived from**: Q13.5 FAILURE finding — ~15,000 synthetic testbed memories identified as primary corpus bloat; retirement could restore coverage from 5.4% to ~50%

---

## Q13.6 [DOMAIN-3] vocabulary mismatch — do domain-specific queries fail to surface relevant memories?
**Status**: DONE
**Mode**: benchmark
**Target**: POST /search with domain-specific query terms
**Hypothesis**: Recall's hook extracts "key terms" from conversational prompts and uses them as the search query. When a user asks about "the CasaOS Docker stack" or "the Relay AI project", the stored memories may use different vocabulary ("homelab containers", "AI phone receptionist"). The qwen3-embedding:0.6b model has a compressed similarity range (0.3–0.65), so vocabulary mismatch pushes relevant memories below the injection threshold even when they are semantically related. This would manifest as the retrieval hook returning zero results for specific project queries even though relevant memories exist.
**Test**: Run 10 targeted queries covering each active project (Recall, FamilyHub, Relay, Bricklayer, media stack). For each: (a) query the API directly and record top-5 results + similarity scores; (b) manually verify whether the returned memories are relevant; (c) test an alternative phrasing and compare results. Measure: hit rate (relevant memory in top-5) and mean similarity of top-1 result per query.
**Verdict threshold**:
- FAILURE: < 60% of targeted queries return a relevant memory in top-5 (vocabulary mismatch causing systematic misses)
- WARNING: 60–80% hit rate but mean top-1 similarity < 0.50 (borderline matches, vulnerable to threshold changes)
- HEALTHY: ≥ 80% hit rate with mean top-1 similarity ≥ 0.55 (retrieval robust to query phrasing variation)

**Derived from**: Wave 12 audit — qwen3-embedding:0.6b compressed range noted; hook vocabulary extraction identified as potential mismatch source; domain-specific recall gaps suspected
**Simulation path**: benchmark-engineer runs 10 structured queries against live API (192.168.50.19:8200), records similarity scores, evaluates relevance manually

---

## Q13.6a [DOMAIN-3] recall-retrieve.js query construction — does it include file/tool context or only user message terms?
**Status**: DONE
**Mode**: benchmark
**Target**: recall-retrieve.js hook query construction logic
**Hypothesis**: The hook extracts key terms only from the user's message text, not from tool context (current file, tool_name, event_type). This means queries about abstract API concepts ("UserPromptSubmit") fail to surface concrete implementation memories ("observe-edit hook"). Including current_file and tool_name in the query construction would close this vocabulary gap.
**Test**: Read recall-retrieve.js to find the query term extraction logic. Identify exactly what inputs are used to construct the Qdrant search query. Report: which fields are included, whether tool context is used, whether project name inference is applied.
**Verdict threshold**:
- FAILURE: only user message text is used; no file/tool/project context (vocabulary mismatch is structural and systematic)
- WARNING: some context is included but project names or tool names are excluded
- HEALTHY: full context included (user message + current_file + tool_name + project name inference)
**Derived from**: Q13.6 WARNING finding — abstract API term "UserPromptSubmit" failed to surface concrete hook memories; alt phrasings with concrete names succeeded

---

## Q13.7 [DOMAIN-1] signal classifier retraining readiness — is type_cv above 0.75 yet?
**Status**: DONE
**Mode**: benchmark
**Target**: GET /admin/health (signal_classifier section) + /admin/ml/metrics
**Hypothesis**: Wave 12 found signal_classifier type_cv=0.6488, below the 0.75 target. The root cause was the audit_log content bug (fixed in commits a70246d + 93711a0). Two weeks of content accumulation were required before retraining would be meaningful. It is now approximately 2+ weeks since the fix. The classifier may be ready for retraining, or the content accumulation may still be insufficient.
**Test**: Fetch current type_cv from /admin/health or /admin/ml/metrics. Count audit_log entries where action='extract' AND content IS NOT NULL since commit 93711a0 (2026-03-14). If entry count > 500 AND type_cv still < 0.75, trigger retraining and re-measure. Report whether retraining moves type_cv above threshold.
**Verdict threshold**:
- FAILURE: type_cv still < 0.65 after retraining attempt (content insufficient or model degraded)
- WARNING: type_cv 0.65–0.75 after retraining (improvement confirmed but target not yet reached)
- HEALTHY: type_cv ≥ 0.75 after retraining (target reached; signal classification reliable)

**Derived from**: Wave 12 Q12.4 fix (audit_log content bug) — retrain deferred 2 weeks; Wave 12 closing risk: "Re-train signal classifier after ~2 weeks of content accumulation; verify type_cv > 0.75"
**Simulation path**: benchmark-engineer checks current metrics, counts accumulated content, triggers retrain if ready, re-measures type_cv

## Q13.7a [DOMAIN-1] type classifier per-class precision/recall — should contradiction be merged into warning?
**Status**: DONE
**Mode**: benchmark
**Target**: GET /admin/ml/signal-classifier-status or retrain endpoint returning per-class metrics
**Hypothesis**: The type classifier (type_cv=0.6539) has only 44 contradiction samples vs 150 fact samples. If contradiction precision < 0.5, it is misclassifying more than half the time and should be merged with warning (which has 54 samples, semantically similar). Merging contradiction+warning (98 combined) and decision+preference (121 combined) may push type_cv from 0.6539 to above 0.75 without adding new data.
**Test**: Retrieve per-class precision, recall, and F1 from the signal classifier's cross-validation results. Identify which classes have precision < 0.5 and recall < 0.5. Model the expected type_cv if: (a) contradiction merged with warning, (b) decision merged with preference, (c) both merged. Compare against 0.75 target.
**Verdict threshold**:
- FAILURE: Per-class data unavailable (endpoint doesn't expose it); or contradiction precision > 0.7 (merge not justified)
- WARNING: Contradiction precision < 0.5 but merged-class model doesn't reach type_cv ≥ 0.75
- HEALTHY: Merged-class model projects type_cv ≥ 0.75; merge is the right next action

**Derived from**: Q13.7 WARNING finding — type_cv=0.6539, minority classes (contradiction=44, decision=54) identified as bottleneck; Q13.7 recommends: "reduce to 5–6 types: merge contradiction into warning, decision into preference"

---

## Q13.8 [DOMAIN-5] Session Markov Chain — why are prefetch cache hits and predictions at zero?
**Status**: DONE
**Mode**: benchmark
**Target**: Session Markov Chain feature (/admin/features/stats)
**Hypothesis**: The Markov Chain feature reports 3,988 file visits tracked and 2,256 transition pairs learned, but 0 prefetch cache hits and 0 predictions generated. The feature is accumulating state but never firing. Likely causes: (a) the prefetch trigger threshold is set too high, (b) the prefetch write path is broken and silently fails, (c) the hook consuming prefetched results was never wired to the retrieval path, or (d) prediction TTL expires before any prompt arrives to consume them.
**Test**: Check the Markov Chain implementation for the prefetch trigger condition and hook integration. Verify whether prefetch entries are ever written to Redis/cache. Attempt a manual trigger by simulating a known file transition sequence. Check logs for any prefetch-related errors.
**Verdict threshold**:
- FAILURE: prefetch write path is broken or hook is not wired — feature accumulating state but delivering zero value
- WARNING: feature fires but TTL too short or threshold too high — predictions generated but never consumed
- HEALTHY: zero hits explained by low session repetition rate (new file pairs each session)

**Derived from**: Live dashboard eval (2026-03-15) — 3,988 file visits, 2,256 transition pairs, prefetch_cache_hits=0 and predictions_generated=0 despite feature status "active"
**Simulation path**: benchmark-engineer reads Markov Chain source, checks prefetch write path and hook wiring, tests manual trigger against live system

## Q13.8a [DOMAIN-5] Markov Chain transition confidence — after fixing the tag bug, how many file pairs have ≥5 transitions?
**Status**: DONE
**Mode**: benchmark
**Target**: Redis keys recall:markov:trans:* (HGETALL on a sample of trans keys)
**Hypothesis**: After the tag vocabulary fix is applied, prefetch will only deliver value for file pairs with enough transition history to produce confident predictions. If most file pairs have only 1–2 observed transitions (driven by one-off session patterns), the Markov model will generate noisy predictions. The fix is necessary but may not be sufficient for meaningful value.
**Test**: Sample all recall:markov:trans:* keys. For each, get the top transition count. Distribution: what fraction of source files have a highest-count transition ≥5? ≥10? Report the top-20 most confident file transition pairs (source → predicted, count).
**Verdict threshold**:
- FAILURE: <10% of source files have any transition with count ≥5 (insufficient history for reliable prediction)
- WARNING: 10–30% of source files have transitions ≥5 (marginal — some predictions reliable, most noisy)
- HEALTHY: ≥30% of source files have transitions ≥5 (enough stable patterns for the prefetch to deliver value)

**Derived from**: Q13.8 FAILURE finding — tag vocabulary mismatch root cause identified; question is whether the learning side has accumulated enough data to justify fixing the prediction side

## Q13.8b [DOMAIN-5] Markov prefetch O(N) scan — does build_prefetch_cache need scroll_all() or can it use a targeted tag filter?
**Status**: DONE
**Mode**: correctness
**Target**: C:/Users/trg16/Dev/Recall/src/core/markov_chain.py — build_prefetch_cache implementation
**Hypothesis**: build_prefetch_cache currently calls qdrant_store.scroll_all() (O(N) — 20,560 memories) then filters Python-side for file: tags. After the tag fix, this should be replaced with a targeted Qdrant tag filter: {must: [{key: "tags", match: {any: ["file:foo", "file:bar"]}}]} which is O(matching memories) instead of O(total corpus). At current corpus size the difference is ~20,560 reads vs ~1–5 reads. As corpus grows, the current approach becomes increasingly expensive.
**Test**: Check whether qdrant_store exposes a filtered scroll method. Review the scroll_all() caller signature. Confirm that the Qdrant collection has a payload index on the "tags" field (required for efficient tag filter). If no payload index exists, a filter scan is still O(N) at the Qdrant layer.
**Verdict threshold**:
- FAILURE: No payload index on tags field AND no targeted search method available; scroll_all() is the only option
- WARNING: Targeted filter available but tags field has no payload index (filter scan still O(N) at Qdrant level)
- HEALTHY: Targeted filter available AND tags field has a payload index (O(matching) retrieval)

**Derived from**: Q13.8 FAILURE finding — O(N) scroll_all() identified as secondary performance concern; fix should address both the tag vocabulary mismatch AND the search efficiency

---

## Wave 14 — Verification, Cleanup, and Prerequisite Fixes (Q14.x)

*Derived from Wave 13 findings (2026-03-15). Wave 14 focuses on actionable verification of the three FAILURE-level issues, closing the two INCONCLUSIVE prerequisites, and quantifying newly discovered contamination and dedup problems.*

---

## Q14.1 [DOMAIN-5] Sim-persona residue quantification — how many fake memories remain after the 2026-02-25 bulk delete?
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant recall_memories — content-based scan of importance ≥ 0.6, access_count = 0
**Hypothesis**: Q13.1b found 25% of a 20-sample audit were sim-persona residue that escaped the 2026-02-25 bulk deletion (which targeted sim_ username prefixes only). These memories were stored under real usernames with high importance scores (0.61–0.74) because the signal classifier cannot distinguish fictional first-person statements from real user preferences. Extrapolating 25% across the 5,168 high-importance never-retrieved population suggests ~1,292 sim-persona memories remain. A content-based filter using first-person fictional signals ("As [Name]", "In my experience as", "From my work at", persona vocabulary) can identify and count them precisely.
**Test**: Scroll Qdrant for memories with importance ≥ 0.6 AND access_count = 0. Apply a content-based regex filter for sim-persona markers: first-person fictional introductions, named persona references (Aria Chen, Priya Sharma, etc.), consulting/startup vocabulary patterns. Sample 200 flagged memories to verify the filter's precision (true positive rate). Report: total flagged count, precision of filter, estimated true residue count.
**Verdict threshold**:
- FAILURE: ≥1,000 sim-persona memories remain (bulk cleanup required before any retrieval improvement work)
- WARNING: 200–1,000 remain (cleanup recommended but not blocking)
- HEALTHY: <200 remain (residue is negligible; 2026-02-25 delete was nearly complete)

**Derived from**: Q13.1b FAILURE finding — 5/20 (25%) of high-importance never-retrieved sample were sim-persona residue; bulk delete missed memories stored without sim_ prefix

---

## Q14.2 [DOMAIN-5] Exploration-based retrieval prototype — does random-walk injection of buried memories improve coverage without degrading session quality?
**Status**: DONE
**Mode**: benchmark
**Target**: recall-retrieve.js hook + POST /search
**Hypothesis**: Q13.1b's Priority 1 recommendation is exploration-based retrieval: on every Nth retrieval call, include 2–3 memories sampled from importance ≥ 0.7, access_count = 0 regardless of similarity score. This should surface buried high-value memories but risks injecting irrelevant content that degrades the context window. The key metric is whether the injected memories are topically relevant to the session (>30% term overlap with subsequent prompts) or pure noise.
**Test**: Simulate exploration injection by: (1) sample 30 memories from importance ≥ 0.7, access_count = 0; (2) for each, retrieve the 5 most recent session prompts from injection_log; (3) compute term overlap between the sampled memory content and those prompts; (4) classify each as relevant (>20% overlap), marginal (10–20%), or noise (<10%). Report: relevance rate, noise rate, and projected coverage improvement if exploration fires every 10th call with 2 memories.
**Verdict threshold**:
- FAILURE: >60% of exploration-injected memories would be noise (<10% term overlap) — exploration degrades session quality
- WARNING: 30–60% noise — exploration helps some sessions but needs filtering (e.g., only inject if importance ≥ 0.8)
- HEALTHY: <30% noise — exploration is safe to deploy; projected coverage improvement documented

**Derived from**: Q13.1b FAILURE finding — 35% of high-importance never-retrieved memories are genuinely high-value; Priority 1 mitigation is exploration-based retrieval

---

## Q14.3 [DOMAIN-1] Store-time dedup behavior — does supersedure update the surviving memory or silently drop the incoming write?
**Status**: DONE
**Mode**: correctness
**Target**: POST /store deduplication path — src/core/memory.py + src/core/qdrant.py
**Hypothesis**: Q13.4a found semantic_dedup_threshold=0.90 and confirmed a false-positive merge (session 14996103 absorbed into de31f553). But the deeper question is: when supersedure fires, does the surviving memory get updated with content from the incoming write (merge/append), or is the incoming write silently dropped? If dropped, the system loses the unique facts from the newer memory. Q13.1b audit item #4 noted that "store-time path drops incoming write, does not create Neo4j edges" — this suggests a drop-not-merge pattern that loses data.
**Test**: Read the /store dedup code path. Trace what happens when cosine similarity > 0.90: (a) is the incoming memory's content appended/merged into the surviving memory? (b) is the incoming memory's importance compared and the higher value kept? (c) are Neo4j edges created for the relationship? (d) is the audit_log entry created with the incoming content preserved? Sample 10 recent supersede audit_log entries and verify: does the surviving memory contain facts from both the original and the incoming write?
**Verdict threshold**:
- FAILURE: incoming write is silently dropped with no content merge — unique facts from newer memory are permanently lost
- WARNING: incoming write is dropped but audit_log preserves the content (recoverable, not merged)
- HEALTHY: incoming write is merged into surviving memory (content union, higher importance kept, Neo4j edges created)

**Derived from**: Q13.4a WARNING finding — supersedure threshold=0.90 causes false positives; Q13.1b audit item #4 — "store-time path drops incoming write, does not create Neo4j edges"

---

## Q14.4 [DOMAIN-5] Global OllamaLLM semaphore — does adding asyncio.Semaphore(1) to OllamaLLM.generate() reduce system-wide p95 below 10s?
**Status**: DONE
**Mode**: benchmark
**Target**: src/core/llm.py — OllamaLLM.generate() method
**Hypothesis**: Q13.3a concluded that the endpoint-level extraction semaphore (already deployed) is insufficient because all LLM callers (fact_extraction, consolidation, observer, signal detection) share the same Ollama GPU queue without coordination. A global asyncio.Semaphore(1) on OllamaLLM.generate() would serialize all inference requests, bounding p95 at approximately queue_depth x median_inference_time. Q13.3a predicted this would achieve HEALTHY (p95 ≤ 10s). This question verifies that prediction empirically.
**Test**: After deploying the global semaphore: collect 48h of prompt_metrics data across all prompt types. Compute p50/p75/p95/p99 for each prompt type. Compare pre-deploy vs post-deploy distributions. Check whether interactive /search signal detection latency is acceptably bounded (p95 < 3s — signal detection is on the critical user-facing path).
**Verdict threshold**:
- FAILURE: p95 still >10s after global semaphore (root cause is inference time, not queuing)
- WARNING: p95 drops to 5–10s but signal_detection p95 > 3s (background tasks starve interactive path — needs priority queue)
- HEALTHY: p95 ≤ 10s across all prompt types AND signal_detection p95 ≤ 3s

**Derived from**: Q13.3a INCONCLUSIVE finding — structural analysis predicts global semaphore achieves HEALTHY; empirical verification required
**Prerequisite**: Deploy asyncio.Semaphore(1) to OllamaLLM.generate() in src/core/llm.py (~10 lines)

---

## Q14.5 [DOMAIN-1] file_ext proxy analysis — can input_chars distribution in prompt_metrics approximate the config/code split without instrumentation?
**Status**: DONE
**Mode**: benchmark
**Target**: PostgreSQL prompt_metrics table — action='fact_extraction', empty=true
**Hypothesis**: Q13.2a was INCONCLUSIVE because file_ext is not captured in prompt_metrics. However, the input_chars field IS captured. Config files (.json, .yaml, .toml) tend to produce shorter extraction prompts (<300 chars) than code files (.py, .js, .ts) which produce 500–2000 char prompts. If the input_chars distribution for empty extractions clusters below 300 chars, this is indirect evidence that config files dominate the empty rate — supporting the pre-filter recommendation without requiring code instrumentation.
**Test**: Query prompt_metrics: SELECT input_chars distribution for action='fact_extraction' WHERE empty=true, bucketed into <300, 300–1000, >1000 chars. Compare against the same distribution for empty=false (successful extractions). If empty extractions are disproportionately short (<300 chars), the config-file hypothesis is supported. Additionally: sample 30 memories from Qdrant where metadata.observer=True and metadata.source_file is populated, extract file extensions, compute the file-type distribution of observer-originated memories.
**Verdict threshold**:
- FAILURE: empty extractions have the same input_chars distribution as successful ones (file type is NOT the differentiator — model quality is the issue)
- WARNING: empty extractions skew shorter but overlap significantly with successful extractions (partial signal, not conclusive)
- HEALTHY: ≥60% of empty extractions have input_chars < 300 AND ≥60% of successful extractions have input_chars > 500 (clear separation — config pre-filter justified)

**Derived from**: Q13.2a INCONCLUSIVE finding — proxy analysis via input_chars suggested but not executed; avoids the ~20-line instrumentation prerequisite

---

## Q14.6 [DOMAIN-1] Per-class classifier confusion matrix — what does scikit-learn's cross_val_predict reveal about type misclassification patterns?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: Signal classifier retrain path — src/core/signal_classifier.py or /admin/ml/retrain endpoint
**Hypothesis**: Q13.7a confirmed the endpoint exposes no per-class metrics, but the training code uses scikit-learn which computes them internally during cross_val_predict. By adding classification_report(output_dict=True) to the retrain output and storing it, we can directly answer: which classes have precision < 0.5? Does contradiction systematically misclassify as warning (supporting the merge)? Does the confusion matrix reveal other unexpected misclassification pairs?
**Test**: Read the signal classifier training code (signal_classifier.py). Identify where cross-validation runs. Add classification_report output to the retrain response (or extract it from the training logs if already computed but not exposed). Trigger a retrain. Report: full 8-class confusion matrix, per-class precision/recall/F1, and the top-3 misclassification pairs by count.
**Verdict threshold**:
- FAILURE: contradiction precision ≥ 0.7 AND no class has precision < 0.5 (merge is not justified; low type_cv has a different root cause)
- WARNING: contradiction precision < 0.5 but unexpected misclassification pairs exist (merge helps contradiction but other classes also problematic)
- HEALTHY: contradiction precision < 0.5 AND contradiction→warning is the dominant misclassification pair (merge directly addresses the primary confusion source)

**Derived from**: Q13.7a FAILURE finding — per-class data unavailable; merge hypothesis (contradiction→warning, decision→preference) cannot be validated without confusion matrix

---

## Q14.7 [DOMAIN-5] Retrieval coverage after sim-persona cleanup — what is the effective coverage rate on a clean corpus?
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant recall_memories — post-cleanup corpus statistics
**Hypothesis**: Q13.1 measured 8.9% coverage rate (1,827 unique memories retrieved / 20,602 total). Q13.1b found ~25% of high-importance never-retrieved memories are sim-persona residue. Q13.5a confirmed all 20,602 memories are real user data (no testbed bulk delete possible). After removing sim-persona residue (~1,000–1,300 estimated from Q14.1), the denominator shrinks and the coverage rate should increase modestly. More importantly, the remaining never-retrieved population would be genuinely useful content, making the exploration-based retrieval recommendation (Q14.2) more impactful.
**Test**: After Q14.1 cleanup is executed: recompute coverage rate = unique_retrieved / total_memories. Recompute the high-importance never-retrieved population (importance ≥ 0.6, access_count = 0). Sample 20 from the cleaned population to verify sim-persona contamination is eliminated. Report: new coverage rate, new high-importance buried count, sample audit results.
**Verdict threshold**:
- FAILURE: coverage rate still < 12% after cleanup (sim-persona removal was insufficient; structural retrieval changes needed)
- WARNING: coverage rate 12–20% (cleanup helped but exploration-based retrieval still needed)
- HEALTHY: coverage rate ≥ 20% (cleanup alone restores acceptable coverage)

**Derived from**: Q13.1b FAILURE finding + Q14.1 (sim-persona quantification) — measures the impact of cleanup on the core coverage metric
**Prerequisite**: Q14.1 must complete first (quantify residue); cleanup must be executed before this measurement

---

## Q14.8 [DOMAIN-1] Session summary dedup exemption — do session summaries warrant a higher similarity threshold or full exemption from store-time dedup?
**Status**: DONE
**Mode**: correctness
**Target**: POST /store dedup logic + recall-session-summary.js hook
**Hypothesis**: Q13.4 found 46.7% supersedure rate for session summaries, and Q13.4a found the threshold at 0.90 (reduced from 0.95 in v2.x). Session summaries are structurally repetitive: they describe "what Tim worked on" using overlapping vocabulary (project names, tool names, action verbs). Two sessions working on the same project will produce summaries with >0.90 cosine similarity even though they describe different work. The dedup logic should either: (a) exempt session summaries entirely (tag-based bypass), or (b) apply a higher threshold (0.95+) for memories with a session_summary tag. The risk of the current 0.90 threshold is that consecutive sessions on the same project collapse into a single memory, losing session-specific context.
**Test**: Fetch the 20 most recent session summaries from Qdrant (filter by tags containing "session_summary" or metadata.observer containing "session"). Compute pairwise cosine similarity for consecutive sessions. Report: (a) how many consecutive pairs exceed 0.90 similarity, (b) content diff between pairs that would be superseded, (c) unique facts in the newer summary that would be lost. Model the impact of raising threshold to 0.95 vs full exemption.
**Verdict threshold**:
- FAILURE: ≥50% of consecutive session pairs exceed 0.90 similarity AND ≥3 contain unique facts that would be lost (aggressive dedup destroying session history)
- WARNING: 25–50% exceed 0.90 but most share genuinely redundant content (threshold is borderline)
- HEALTHY: <25% exceed 0.90 (session summaries are sufficiently distinct; current threshold is acceptable)

**Derived from**: Q13.4 WARNING finding — 46.7% supersedure rate for session summaries; Q13.4a WARNING — threshold=0.90; recommendation to "exempt session summaries from auto-dedup"

---

## Q14.9 [DOMAIN-5] Markov prefetch targeted filter implementation — after replacing scroll_all() with tag filter, does prefetch latency drop from ~200–500ms to <10ms?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: src/core/markov_chain.py — build_prefetch_cache
**Hypothesis**: Q13.8b confirmed scroll_all() is structural and the O(N) scan runs on every file visit with transition history. After replacing scroll_all() with a targeted Qdrant tag filter (FieldCondition key="tags" match=MatchAny), prefetch latency should drop from ~200–500ms (scrolling 20,602 memories) to <10ms (matching 1–5 memories). This is a prerequisite for the Q13.8 tag vocabulary fix — the filter replacement must happen first to avoid making a broken-but-cheap operation into a working-but-expensive one.
**Test**: After implementing the targeted filter: (1) measure build_prefetch_cache latency with timing instrumentation around the Qdrant call; (2) verify the filter returns correct results by comparing against scroll_all() output for 10 known file:tag patterns; (3) confirm Qdrant tags payload index exists via collection info API.
**Verdict threshold**:
- FAILURE: targeted filter latency still >50ms (Qdrant tags index missing or filter not working correctly)
- WARNING: latency <50ms but correctness check shows missed results vs scroll_all() baseline
- HEALTHY: latency <10ms AND results match scroll_all() baseline for all 10 test patterns

**Derived from**: Q13.8b FAILURE finding — scroll_all() O(N) scan confirmed structural; fix order: targeted filter FIRST, then tag storage fix
**Prerequisite**: Implement scroll_by_tags() or equivalent in Qdrant store class; replace scroll_all() call in build_prefetch_cache

---

## Q14.4a [DOMAIN-5] Priority queue LLM dispatch — does routing signal_detection to front of queue reduce signal_detection p95 below 3s?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: src/core/llm.py — OllamaLLM dispatch mechanism
**Hypothesis**: Q14.4 confirmed Semaphore(1) is insufficient because consolidation/observer_high_value tasks hold the semaphore for 10–25s, blocking interactive signal_detection. A priority queue that places signal_detection ahead of background tasks would bound signal_detection wait time to ~0ms (background tasks yielded). p95 for signal_detection should drop from ~8s to <3s since inference time for signal_detection prompts is ~1–2s.
**Test**: Implement a priority asyncio.PriorityQueue with prompt_type as priority key (signal_detection=0, fact_extraction=1, observer=2, consolidation=3). Measure signal_detection p95 over 24h post-deploy. Compare against Q14.4 baseline (p95=8,356ms, n=5).
**Verdict threshold**:
- FAILURE: signal_detection p95 still >5s (queue priority not respected or insufficient signal_detection volume to measure)
- WARNING: signal_detection p95 3–5s (priority helps but inference time still dominates)
- HEALTHY: signal_detection p95 ≤ 3s AND other prompt types p95 acceptable (≤ 60s for background)

**Derived from**: Q14.4 FAILURE finding — semaphore serializes correctly but fat-tail inference blocks interactive path; priority dispatch is the next mitigation step

---

## Q14.4b [DOMAIN-5] Input length vs latency correlation — is there a chars threshold above which qwen3:14b inference jumps to >10s?
**Status**: DONE
**Mode**: benchmark
**Target**: PostgreSQL prompt_metrics — input_chars vs latency_ms correlation
**Hypothesis**: Q14.4 found p50=1,007ms but p95=16,843ms for fact_extraction — a 16× spread. The likely driver is prompt length: config files produce <300-char prompts (fast) while large code files produce >4,000-char prompts (slow). A scatter of input_chars vs latency_ms should reveal a threshold (e.g., ~3,000–5,000 chars) where inference time shifts from the 1–2s regime to the 10–25s regime, justifying a prompt truncation strategy.
**Test**: Query prompt_metrics: SELECT input_chars, latency_ms for all rows where input_chars IS NOT NULL AND latency_ms IS NOT NULL. Bucket into <500, 500–1000, 1000–2000, 2000–4000, 4000–8000, >8000 chars. Compute p50/p95 per bucket. Report: the bucket where p95 first exceeds 10,000ms and the sample count at that bucket.
**Verdict threshold**:
- FAILURE: no clear correlation (p95 > 10s even for short inputs — model startup or other factor dominates)
- WARNING: threshold exists but is at <1,000 chars (truncation would lose too much content to be practical)
- HEALTHY: threshold at 3,000–6,000 chars (truncation at that boundary preserves most content and achieves p95 < 10s)

**Derived from**: Q14.4 FAILURE finding — inference time variance is root cause; characterizing the input_chars→latency relationship is prerequisite to prompt truncation strategy

---

## Wave 15 — Dedup Blast Radius, Timeout Misconfiguration, and Empty Extraction Pathologies (Q15.x)

*Derived from Wave 14 findings (2026-03-15). Wave 15 targets the three highest-priority open threads: (1) the blast radius and recoverability of the Q14.3 store-time dedup silent-drop defect, (2) the signal_detection_timeout=180s misconfiguration discovered in Q14.4a that applies to all LLM calls, and (3) two unresolved fact_extraction empty-extraction pathologies from Q14.5 — the very-short-prompt cluster and the high-input_chars outlier regime.*

---

## Q15.1 [DOMAIN-1] Store-time dedup hit rate — how often does the silent-drop path fire, and what is the cumulative data loss?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: PostgreSQL audit_log table + Qdrant recall_memories — `POST /store` dedup path, `src/api/routes/memory.py` lines 230–255
**Hypothesis**: Q14.3 confirmed that every store-time dedup hit (cosine similarity > 0.90) silently drops the incoming write with no audit entry, no content merge, and no Neo4j edge. The audit log confirms zero `dedup_drop` entries and zero store-path supersede entries (all 100 sampled supersede entries have `actor="consolidation"`). The unknown variable is how often the 0.90 threshold fires at store time. If the hit rate is < 1% of stores, the blast radius is bounded. If it is > 5%, accumulated data loss over the system's 368,038 audit entries is significant. The total store count can be inferred from audit_log `action="store"` entries; the dedup hit count requires either code instrumentation or proxy estimation from semantic similarity distributions in Qdrant.
**Test**: (1) Query `SELECT COUNT(*) FROM audit_log WHERE action='store'` to establish total store volume. (2) Estimate dedup hits using Qdrant: for a random sample of 200 memories, query each against the corpus at threshold 0.90 and count how many would have been deduplicated if stored today (simulates the rate prospectively). (3) Cross-check by querying structlog output for `semantic_dedup_hit` events in signals.py and observer.py if a log sink is accessible. Report: estimated dedup hit rate (%), estimated total silent-drop count over system lifetime, and whether any log sink captures the worker-path drops.
**Verdict threshold**:
- FAILURE: estimated dedup hit rate > 5% of total stores (>18,000 silent drops over system lifetime — material data loss requiring immediate Tier 1 audit-preservation fix)
- WARNING: hit rate 1–5% (3,600–18,000 drops — concerning but bounded; fix is urgent but not emergency)
- HEALTHY: hit rate < 1% (<3,600 drops — blast radius is limited; dedup is rarely triggering at 0.90 threshold on genuine writes)

**Derived from**: Q14.3 FAILURE finding — store-time dedup path silently drops incoming writes; blast radius (frequency) is unknown and required to prioritize the fix; Q14.3a follow-up question

---

## Q15.2 [DOMAIN-1] Observer and signals dedup structlog persistence — are worker-path silent drops captured to a durable log sink or are they ephemeral container stdout?
**Status**: WARNING
**Mode**: correctness
**Target**: `src/workers/signals.py` line 285–301 (`signal_semantic_dedup_hit` debug log), `src/workers/observer.py` line 175 (`continue` silent skip), Docker logging configuration
**Hypothesis**: Q14.3 confirmed that the observer.py and signals.py dedup paths produce zero audit_log entries — the only trace of a worker-path dedup hit is a `structlog.debug("signal_semantic_dedup_hit", ...)` call in signals.py and a bare `continue` in observer.py (no log at all). The recoverability of these drops depends entirely on whether structlog output is captured to a persistent sink (file rotation, centralized log aggregator, or Docker volume mount) or whether it is ephemeral container stdout that is lost on container restart. If logs are ephemeral, every observer/signals dedup hit over the system's lifetime is unrecoverable — the content is gone with no record anywhere.
**Test**: (1) Read the Docker Compose configuration for the recall-api service and identify the logging driver (`logging.driver`) and any volume mounts for log output. (2) Check whether structlog is configured to write to a file sink (look for `structlog.WriteLoggerFactory` or file handlers in `src/core/logging.py` or equivalent). (3) Inspect the observer.py dedup path at line 175 — confirm whether any log call exists before the `continue`. (4) Attempt to retrieve historical `signal_semantic_dedup_hit` events from any available log surface (Docker `docker logs`, log files, or admin API). Report: log sink type, retention window (if file-based), and whether any historical worker dedup events are recoverable.
**Verdict threshold**:
- FAILURE: structlog output is ephemeral container stdout with no persistent sink — all historical observer/signals dedup drops are unrecoverable; observer.py has zero log call before `continue` (completely invisible drops)
- WARNING: structlog writes to a persistent file but observer.py still has no log call (signals drops are recoverable from file; observer drops remain invisible)
- HEALTHY: structlog writes to a persistent sink AND observer.py logs a dedup event before `continue` — all worker-path drops are at minimum recoverable from logs even without audit_log entries

**Derived from**: Q14.3 FAILURE finding — observer and signals dedup paths produce no audit entries; Q14.3c follow-up question — recoverability depends on log sink persistence; severity escalates to critical if logs are ephemeral

---

## Q15.3 [DOMAIN-5] Global LLM timeout misconfiguration — does signal_detection_timeout=180s apply to all OllamaLLM callers, and what is the worst-case semaphore hold duration per caller type?
**Status**: FAILURE
**Mode**: correctness
**Target**: `src/core/config.py` line 71 (`signal_detection_timeout`), `src/core/llm.py` OllamaLLM `__init__` — `httpx.AsyncClient(timeout=self.settings.signal_detection_timeout)`
**Hypothesis**: Q14.4a's peer review discovered that `signal_detection_timeout` in config.py (value: 180.0s) is used as the global httpx client timeout for ALL LLM callers, not only signal_detection. The timeout name implies it was intended for signal_detection specifically, but a single `httpx.AsyncClient` instance is reused across all `generate()` calls. This means: (a) consolidation and observer_high_value tasks — which already produce p95 inference times of 14–20s — can hold the asyncio.Semaphore(1) for up to 180s on a stalled call, blocking all other LLM work for 3 minutes; (b) signal_detection, which should be the fastest path, gets no preferential timeout. The correct fix is per-caller timeout configuration: signal_detection at ~15s, background tasks at 60–90s, with the global cap at 180s only as a hard circuit-breaker.
**Test**: (1) Read `src/core/config.py` — confirm `signal_detection_timeout` is the sole LLM timeout setting and its value. (2) Read `src/core/llm.py` — confirm the httpx client is initialized once with `timeout=self.settings.signal_detection_timeout` and reused for all callers. (3) Check whether any caller passes a per-call timeout override (e.g., via `httpx` request-level timeout). (4) Query prompt_metrics for `latency_ms > 30000` (30s) by prompt_type — count how many calls have exceeded 30s inference time historically, as these are the cases where a 15s per-caller cap would have already timed them out. Report: whether the timeout is global or per-caller, the number of >30s inference events by type, and the maximum observed latency_ms per prompt_type (worst-case semaphore hold).
**Verdict threshold**:
- FAILURE: timeout is global (single value), no per-caller override mechanism exists, AND >10 consolidation/observer events show latency_ms > 60s (confirmed worst-case 3-minute semaphore locks are occurring in production)
- WARNING: timeout is global but >60s events are rare (<10 total) — risk is theoretical but unmitigated
- HEALTHY: per-caller timeout override mechanism exists OR signal_detection_timeout has already been reduced to ≤ 30s (misconfiguration is resolved or bounded)

**Derived from**: Q14.4a INCONCLUSIVE finding — peer review identified signal_detection_timeout=180s applies to all LLM calls; Q14.4 FAILURE finding — semaphore can be held for up to timeout duration on stalled inference; worst-case 3-minute blocks unquantified

---

## Q15.4 [DOMAIN-1] Very-short-prompt empty rate — does the input_chars < 50 sub-cluster justify a narrow pre-filter for fact_extraction?
**Status**: DONE
**Mode**: benchmark
**Target**: PostgreSQL `prompt_metrics` table — `prompt_type='fact_extraction'`, `input_chars < 50`
**Hypothesis**: Q14.5 found that the 100–300 char range has the *lowest* empty rate (23.7%), but the <100 char range has a 51.0% empty rate — nearly double. This non-monotonic pattern suggests the <100 char regime contains a distinct pathology sub-population: single-line config values, lock file hashes, auto-generated enum entries, and other content that is genuinely not worth extracting. If this sub-population concentrates below ~50 chars and achieves an empty rate of ≥ 70%, a narrow pre-filter (skip fact_extraction if input_chars < 50) would be both precise (high empty-rate reduction) and low-risk (the discarded content is genuinely empty). Q14.5 recommended investigating this sub-population but did not execute the query.
**Test**: Query prompt_metrics with fine-grained buckets in the 0–100 char range: SELECT input_chars bucket (0–10, 10–25, 25–50, 50–75, 75–100), COUNT(*), SUM(CASE WHEN empty THEN 1 ELSE 0 END) / COUNT(*)::float AS empty_rate FROM prompt_metrics WHERE prompt_type='fact_extraction' AND input_chars IS NOT NULL GROUP BY bucket ORDER BY bucket. Report: empty rate per sub-bucket, total volume per bucket, and the chars threshold (if any) where empty rate first falls below 60%. Additionally: sample 20 prompts from the < 50 chars bucket to characterize the content type (lock file hash, JSON scalar, comment-only line, etc.).
**Verdict threshold**:
- FAILURE: no sub-bucket achieves empty rate ≥ 70% — very-short prompts are not systematically empty; pre-filter is not justified at any threshold below 100 chars
- WARNING: input_chars < 25 achieves ≥ 70% empty rate but volume is < 5% of total (pre-filter viable but impact is limited)
- HEALTHY: input_chars < 50 achieves ≥ 70% empty rate AND represents ≥ 15% of total fact_extraction calls (pre-filter is both precise and high-impact — justifies a 2-line guard in fact_extractor.py)

**Derived from**: Q14.5 FAILURE finding — input_chars cannot proxy file-type split; non-monotonic empty rate (51% for <100 chars) implies a distinct pathology sub-population below 50 chars; Q14.5a follow-up question

---

## Q15.5 [DOMAIN-1] High-input_chars outlier regime — what content type produces 1,000–3,000 char fact_extraction prompts with a 60.6% empty rate?
**Status**: DONE
**Mode**: benchmark
**Target**: PostgreSQL `prompt_metrics` table + Qdrant recall_memories — `prompt_type='fact_extraction'`, `input_chars BETWEEN 1000 AND 3000`
**Hypothesis**: Q14.5 found that the 1,000–3,000 char bucket has the *highest* empty rate of any bucket (60.6%, exceeding even the <100 char pathology at 51%). This is counterintuitive — longer prompts should contain more extractable content. The likely explanation is that this bucket contains large generated or binary-adjacent files: minified JavaScript, lock files (package-lock.json, poetry.lock), generated type definitions, or large data files pasted whole. These files have high character counts but zero meaningful semantic content for fact extraction. If this hypothesis holds, a content-based pre-filter (detect minified/generated files by line-length entropy or file extension) would eliminate 60%+ of wasted inference calls in this bucket — and those calls also hold the Semaphore(1) for disproportionately long durations given their high input_chars (Q14.4b showed 1,000–3,000 char prompts have p50=1,672ms but p95=15,536ms).
**Test**: (1) Query prompt_metrics for the 1,000–3,000 char bucket: retrieve 30 sample rows with their full prompt content (or truncated prompt if stored). Classify each by likely source type: minified code, lock file, generated types, config, or genuine source code. (2) Compute the proportion of each class and its empty rate. (3) Check whether any metadata distinguishes this bucket from lower-char buckets (e.g., presence of a single very long line, low newline density as a minification proxy). Report: content type distribution, empty rate per type, and whether a structural signal (line-length, entropy, file extension if available) reliably identifies the high-empty-rate content.
**Verdict threshold**:
- FAILURE: high-input_chars empty extractions are structurally indistinguishable from successful ones — no content type clustering; no pre-filter signal available
- WARNING: a dominant content type (e.g., lock files) is identifiable but requires file extension data not currently captured — instrumentation prerequisite before filter can be deployed
- HEALTHY: ≥ 70% of the high-input_chars empty extractions share a structural signature detectable without file extension (e.g., single-line minified content, low newline density) — a ~5-line guard in fact_extractor.py can filter them without instrumentation

**Derived from**: Q14.5 FAILURE finding — 1,000–3,000 char bucket has 60.6% empty rate (highest of any bucket), counterintuitive given longer prompts; Q14.5c follow-up question; also relevant to Q14.4b finding — this bucket's p95=15,536ms contributes disproportionately to semaphore hold time


---

## Wave 16 -- Dedup Observability, Timeout Remediation, and Content-Type Instrumentation (Q16.x)

## Q16.1 [DOMAIN-4] Dedup counter instrumentation -- after adding recall_dedup_hits_total, what is the baseline store-time hit rate in the first 24h?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: `src/api/routes/memory.py` lines 247-271, `src/workers/signals.py` lines 294-301, `src/workers/observer.py` lines 175-176, Prometheus metrics endpoint `http://192.168.50.19:8200/metrics`
**Hypothesis**: Q15.1 found that all three dedup drop sites are uninstrumented -- there is no `recall_dedup_hits_total` Prometheus counter and no `action='dedup_drop'` audit entry anywhere. The threshold history (0.95 -> 0.90 -> 0.92) confirms real-world dedup fires were noticed subjectively but never measured. Once a counter is added at all three sites, the baseline hit rate should become quantifiable within 24h of normal operation. If the hit rate exceeds 1% of total store attempts, the 0.92 threshold is dropping a material volume of memories and threshold recalibration is warranted. If the hit rate is below 0.1%, the threshold is effectively inert and the observability gap is low-urgency.
**Test**: (1) Verify that `recall_dedup_hits_total{source="api"}`, `recall_dedup_hits_total{source="signal"}`, and `recall_dedup_hits_total{source="observer"}` counters now exist at `GET /metrics`. (2) If they do not exist, this question is BLOCKED -- prerequisite instrumentation is not yet deployed. (3) If they exist, query the counter values and divide by `recall_memories_total` (also at /metrics) to compute the hit rate. (4) Also query `SELECT count(*) FROM audit_log WHERE action='dedup_drop'` to cross-validate. (5) Break down by source label. Report: hit rate per source, total across all three, and whether the total exceeds 1% of store volume.
**Verdict threshold**:
- FAILURE: dedup counters exist but total hit rate > 5% of store attempts -- threshold is actively dropping a high volume of memories; recalibration is urgent
- WARNING: counters exist and hit rate is 1-5% -- material drop volume requiring threshold review; OR counters still do not exist (instrumentation not yet deployed, question remains BLOCKED)
- HEALTHY: counters exist and hit rate < 1% of store attempts -- dedup threshold is operating conservatively; observability gap is resolved

**Derived from**: Q15.1 INCONCLUSIVE -- store-time dedup hit rate is completely unquantifiable due to zero instrumentation at all three drop sites; Q14.3 FAILURE -- no audit_log entry for dedup drops

---

## Q16.2 [DOMAIN-4] Observer dedup silent-drop fix -- does adding a logger.debug call before the observer.py continue produce any events in the Docker logs within 1h?
**Status**: INCONCLUSIVE
**Mode**: correctness
**Target**: `src/workers/observer.py` lines 170-176 (semantic dedup `continue` block), Docker logs `docker logs recall-worker`
**Hypothesis**: Q15.2 WARNING established that observer.py semantic dedup `continue` has zero log instrumentation -- it is the only drop path with no trace at any layer (no audit entry per Q14.3, no log event per Q15.2). The recommended one-line fix is `logger.debug("observer_semantic_dedup_hit", similarity=round(similar[0][1], 4))` before the `continue`. Once this line is deployed, any subsequent observer dedup hit will appear in `docker logs recall-worker`. If no events appear within 1h of normal operation, either the observer dedup path is not firing in practice or the log level is suppressing DEBUG events. If events appear within 1h, the fix is confirmed working and the first real-time evidence of observer dedup activity is available.
**Test**: (1) Confirm the fix is deployed: read `src/workers/observer.py` lines 170-176 and verify a `logger.debug("observer_semantic_dedup_hit", ...)` call exists before the `continue`. (2) If the fix is not deployed, this question is BLOCKED. (3) Run `docker logs recall-worker --since 1h | grep observer_semantic_dedup_hit` and report the count of matching events. (4) If count > 0, report the similarity values and frequency distribution. (5) Compare the observer event rate to the `signal_semantic_dedup_hit` rate from `docker logs recall-api --since 1h | grep signal_semantic_dedup_hit`.
**Verdict threshold**:
- FAILURE: fix is deployed but zero `observer_semantic_dedup_hit` events appear in 1h AND `signal_semantic_dedup_hit` also has zero events -- the log level is suppressing DEBUG output; all dedup events across both workers remain invisible despite the fix
- WARNING: fix is deployed and events appear in logs, but event rate differs from signals.py by more than 10x without structural explanation (suggests one worker dedup threshold is miscalibrated relative to the other)
- HEALTHY: fix is deployed and at least one `observer_semantic_dedup_hit` event appears in logs within 1h OR both worker paths show zero events (threshold not firing in this period), confirming the fix is functional and the path is instrumented

**Derived from**: Q15.2 WARNING -- observer.py bare `continue` with zero log call; the one-line fix is the lowest-cost remediation in the entire Wave 15 set; Q14.3 FAILURE -- observer dedup has no audit coverage

---

## Q16.3 [DOMAIN-5] Per-caller LLM timeout implementation -- does adding a timeout parameter to generate() bound the worst-case semaphore hold to <=60s for fact_extraction and <=90s for consolidation?
**Status**: FAILURE
**Mode**: correctness
**Target**: `src/core/llm.py` `generate()` method signature and `httpx.AsyncClient` initialization, `src/core/config.py` timeout settings
**Hypothesis**: Q15.3 FAILURE confirmed that `signal_detection_timeout=180s` is the sole LLM timeout, applies globally, and has already produced 43 production events with `latency_ms > 60,000ms` (consolidation=16, fact_extraction=27), each of which held `Semaphore(1)` for over a minute. The fix direction from Q15.3 is: add a `timeout: float | None = None` parameter to `generate()` and add per-type config values (`fact_extraction_timeout`, `consolidation_timeout`). Once implemented, the worst-case semaphore hold for fact_extraction should be bounded to <=60s and for consolidation to <=90s. This question verifies the implementation is structurally correct -- not just that config values exist -- by checking that all callsites in `src/workers/` pass the appropriate timeout argument.
**Test**: (1) Read `src/core/llm.py` -- confirm `generate()` now accepts a `timeout` parameter and uses it as a per-request override (not baked into `AsyncClient` construction). (2) Read `src/core/config.py` -- confirm `fact_extraction_timeout` and `consolidation_timeout` (or equivalent named fields) exist with values <=60s and <=90s respectively. (3) Grep for all `llm.generate(` callsites in `src/workers/` and `src/api/` -- confirm each caller passes the appropriate timeout argument. (4) Query `prompt_metrics` for events after the deployment date with `latency_ms > fact_extraction_timeout * 1000` -- if any exist, the per-request timeout is not being enforced. Report: whether all callers pass a timeout, the configured values, and whether any post-deployment events exceed the configured timeout.
**Verdict threshold**:
- FAILURE: `generate()` still has no timeout parameter OR per-type config values do not exist -- the global 180s misconfiguration is unresolved; semaphore holds remain unbounded
- WARNING: `generate()` accepts a timeout parameter but not all callers in `src/workers/` pass one -- partial fix leaves some callers still governed by the global 180s ceiling
- HEALTHY: `generate()` has a timeout parameter, per-type config values exist with values <=60s (fact_extraction) and <=90s (consolidation), and all callsites in `src/workers/` pass the appropriate value

**Derived from**: Q15.3 FAILURE -- 43 production events with >60s semaphore holds; global timeout named for signal_detection governs all callers; fix direction explicitly stated as per-caller timeout config

---

## Q16.4 [DOMAIN-4] Dedup observability completeness -- do all three drop sites now satisfy audit_log, Prometheus counter, and structlog simultaneously?
**Status**: FAILURE
**Mode**: correctness
**Target**: `src/api/routes/memory.py` lines 247-271, `src/workers/signals.py` lines 292-301, `src/workers/observer.py` lines 170-176
**Hypothesis**: Q15.1 (INCONCLUSIVE), Q15.2 (WARNING), and Q14.3 (FAILURE) together describe a complete three-layer observability gap: no audit_log entries, no Prometheus counters, and no INFO-level log events across any of the three drop sites. This is a compound failure -- each individual gap could be excused, but the combination means dedup activity is completely invisible across all observable surfaces. Q16.1 and Q16.2 test counter and log instrumentation in isolation. This question tests whether all three sites now satisfy ALL THREE observability requirements simultaneously: (a) an audit_log entry (`action='dedup_drop'` with similarity and existing_id), (b) a Prometheus counter increment (`recall_dedup_hits_total{source=...}`), and (c) a `logger.info` or `logger.debug` event. Any site missing any layer is an incomplete fix. The 9-cell matrix (3 sites x 3 layers) must be fully green for HEALTHY.
**Test**: (1) For each of the three files, read the dedup drop code path and check for: an audit_log call, a `recall_dedup_hits_total` counter increment, and a logger call at any level. (2) POST a near-duplicate memory to `/api/v1/memories` with content very similar to an existing memory (cosine similarity expected > 0.92). (3) Verify the response shows `created=False`. (4) Check `SELECT * FROM audit_log WHERE action='dedup_drop' ORDER BY created_at DESC LIMIT 5` -- confirm an entry was written. (5) Check `GET /metrics | grep dedup` -- confirm the counter incremented. Report a 3x3 pass/fail matrix.
**Verdict threshold**:
- FAILURE: any of the three sites is missing all three observability layers -- the compound gap from Q14.3+Q15.1+Q15.2 persists at that site; a dedup drop at that site remains completely invisible
- WARNING: all sites have at least one observability layer but at least one site is still missing audit_log coverage -- audit is the most durable surface and its absence was the original Q14.3 FAILURE finding
- HEALTHY: all three sites have all three observability layers; the 9-cell matrix is fully green; the compound dedup observability gap from Q14.3+Q15.1+Q15.2 is closed

**Derived from**: Q14.3 FAILURE (no audit_log for any dedup path), Q15.1 INCONCLUSIVE (no Prometheus counter), Q15.2 WARNING (observer.py bare continue, signals.py DEBUG-only) -- all three findings identify the same compound gap across three independent observable surfaces

---

## Q16.5 [DOMAIN-1] Content-type instrumentation -- does adding a file_extension field to prompt_metrics unlock a >=70% empty-rate filter for fact_extraction?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: `src/workers/observer.py` `extract_facts_for_memory` callsite, PostgreSQL `prompt_metrics` table schema, `src/workers/fact_extractor.py`
**Hypothesis**: Q15.4 FAILURE established that input_chars alone cannot identify high-empty-rate content (no sub-bucket below 50 chars reaches 70%), and Q15.5 HEALTHY showed that the newline-density signal works only for the 1,000-3,000 char regime and eliminates just 14 fast-fail calls. The root limitation identified by both findings is that metadata is null for all rows in prompt_metrics -- there is no `file_extension`, `content_class`, or `source_tag` field. Q15.4 recommendation 3 explicitly states that instrumenting prompt_metrics with a file_extension field would enable a high-precision filter (likely 70-90% empty rate for known bad types like .lock, .min.js). If observer.py passes the file extension from the edit event context through to fact_extractor.py, and fact_extractor.py logs it to prompt_metrics, then a retrospective query can identify which extensions drive empty rates and justify a pre-filter. This question tests whether that instrumentation is deployed and, if so, what the data shows.
**Test**: (1) Read the observer.py callsite for `extract_facts_for_memory` -- check whether the call now passes a `file_ext` or `source_tag` parameter. (2) Read `src/workers/fact_extractor.py` -- check whether `prompt_metrics` inserts now include a `file_extension` or `content_class` column. (3) If instrumentation exists and has been running for >=24h, query: `SELECT file_extension, COUNT(*), ROUND(AVG(CASE WHEN empty THEN 1.0 ELSE 0.0 END)*100,1) AS empty_pct FROM prompt_metrics WHERE prompt_type='fact_extraction' AND file_extension IS NOT NULL GROUP BY file_extension ORDER BY empty_pct DESC LIMIT 20`. (4) Report the top 5 extensions by empty rate and whether any achieves >=70% with volume >=100 rows.
**Verdict threshold**:
- FAILURE: file_extension instrumentation still not deployed -- prerequisite for a precision pre-filter remains missing; both Q15.4 and Q15.5 remediation paths remain blocked
- WARNING: instrumentation deployed but < 24h of data collected, OR no extension achieves >=70% empty rate with sufficient volume -- results not yet statistically meaningful; re-run after 48h
- HEALTHY: instrumentation deployed, >=24h of data, and >=1 file extension achieves >=70% empty rate with volume >=100 rows -- a precision content-type pre-filter is now data-justified

**Derived from**: Q15.4 FAILURE -- metadata null prevents content-type analysis; length-based filter unjustified; recommendation 3 explicitly calls for file_extension instrumentation; Q15.5 HEALTHY -- newline-density is a partial proxy but file_ext is the high-precision path

---

## Wave 17 — Timeout Remediation Verification, Dedup Observability Closure, and Importance-Inheritance Audit (Q17.x)

## Q16.3a [DOMAIN-5] Per-caller timeout post-deployment — after adding timeout parameter to generate(), do fact_extraction p99 semaphore holds drop below 60s?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: `src/core/llm.py` generate() signature (post-fix), PostgreSQL `prompt_metrics` fact_extraction rows post-deployment
**Hypothesis**: Q16.3 FAILURE confirmed generate() has no timeout parameter and 43 production events >60s already exist. The Q16.3 fix adds `timeout: float | None = None` to generate() and per-type config values (fact_extraction_timeout=60s, consolidation_timeout=90s). After deployment, any fact_extraction call that would have exceeded 60s should now be cut off at 60s (LLMError thrown, semaphore released). The p99 semaphore hold for fact_extraction should drop from current (17,000ms+ with tail at 60,000ms+) to approximately 60,000ms (the new hard ceiling). If the timeout parameter is not being passed by callers, p99 will be unchanged.
**Test**: (1) Read generate() in llm.py -- confirm timeout parameter exists and is used per-request. (2) Grep all llm.generate() callsites -- confirm each passes timeout=settings.{type}_timeout. (3) Query: SELECT MAX(latency_ms), percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) FROM prompt_metrics WHERE prompt_type='fact_extraction' AND timestamp > '{deploy_date}'. (4) Compare to pre-fix p99 from Q15.3.
**Verdict threshold**:
- FAILURE: generate() has timeout param but callers don't pass it; OR post-deploy p99 is unchanged from Q15.3 baseline (>60,000ms); semaphore holds remain unbounded
- WARNING: timeout param deployed and some callers pass it; post-deploy p99 reduced but still >30,000ms; partial improvement
- HEALTHY: timeout param deployed; all callers pass appropriate timeout; post-deploy p99 ≤60,000ms for fact_extraction
**Derived from**: Q16.3 FAILURE -- generate() has no timeout parameter; 43 production events >60s semaphore holds persist

---

## Q16.3b [DOMAIN-5] httpx per-request timeout override — does client.post(..., timeout=N) correctly override the client-level timeout set at AsyncClient construction?
**Status**: DONE

**Mode**: quality
**Target**: `src/core/llm.py` httpx.AsyncClient construction (line 49) and generate() post() call (line 95)
**Hypothesis**: Q16.3 identified that httpx.AsyncClient is constructed with timeout=180s and the per-request fix requires passing timeout= to client.post(). httpx documentation states that a per-request timeout passed to client.post() overrides the client-level timeout. However, the exact behavior depends on whether httpx uses the timeout as a scalar or a Timeout object. If the client-level timeout is a scalar (180.0) and per-request is also a scalar, the per-request value overrides it. If the client was constructed with httpx.Timeout(180.0) and per-request passes a float, behavior may differ. This question verifies the override works as expected by reading httpx source behavior and the Recall code path.
**Test**: (1) Read llm.py lines 49 and 95 -- check whether the client is constructed with scalar or Timeout object, and whether per-request timeout is scalar or Timeout. (2) Fetch httpx documentation (context7 or web) confirming the per-request override behavior. (3) If the per-request fix is deployed, write a targeted test: call generate() with timeout=1.0 against a slow mock and confirm httpx.TimeoutException fires within 1-2s.
**Verdict threshold**:
- FAILURE: httpx per-request timeout does NOT override client-level timeout; the fix approach is architecturally incorrect; alternative (reconstruct client per-request or use Timeout objects) is required
- HEALTHY: httpx per-request timeout correctly overrides client-level timeout; the scalar override is confirmed by documentation and/or test
**Derived from**: Q16.3 FAILURE -- per-caller timeout fix assumes httpx per-request override works; this must be verified before declaring the fix correct

---

## Q16.4a [DOMAIN-4] Dedup drop volume post-instrumentation — after adding recall_dedup_hits_total, what fraction of daily stores are dedup-dropped, and does the API store path fire more often than observer?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: Prometheus /metrics recall_dedup_hits_total{source="api|signal|observer"}, recall_memories_total, PostgreSQL prompt_metrics store volume
**Hypothesis**: Q16.4 found that the 9-cell observability matrix is 2/12 covered and no site has complete instrumentation. The fix adds Prometheus counters at all sites. Once deployed, the hit rate per source will reveal which path is most active. The API store path (memory.py) handles all MCP-initiated stores and likely has the highest dedup hit rate because session hook data is frequently redundant. The observer path handles file-edit extractions and may have lower dedup rate since each file edit produces different content. If the total hit rate exceeds 5% of daily stores (~1,036 stores/day from Q15.4 context), threshold recalibration at 0.92 is warranted.
**Test**: After instrumentation is deployed: (1) Read /metrics -- confirm recall_dedup_hits_total{source=*} counters exist. (2) Compute hit rate = sum(dedup_hits) / (recall_memories_total + sum(dedup_hits)). (3) Break down by source label. (4) Report whether API store rate > observer rate and what the combined rate implies for threshold calibration.
**Verdict threshold**:
- FAILURE: counters deployed but total hit rate > 10% -- threshold 0.92 is aggressively collapsing distinct memories; significant data loss
- WARNING: counters deployed and hit rate 1-10% -- material volume, worth monitoring; threshold review warranted
- HEALTHY: counters deployed and hit rate < 1% -- threshold operating conservatively; compound observability gap closure confirmed
**Derived from**: Q16.4 FAILURE -- 7/12 observability cells empty; compound gap persists; Q15.1 INCONCLUSIVE -- hit rate completely unquantifiable

---

## Q16.4b [DOMAIN-4] Importance inheritance correctness — does the memory.py importance-inheritance path (lines 251-259) correctly promote existing memory when a dedup-dropped store has higher importance?
**Status**: FAILURE
**Mode**: quality
**Target**: `src/api/routes/memory.py` lines 251-259 (importance inheritance block inside dedup path)
**Hypothesis**: Q16.4 identified a secondary concern: the importance-inheritance logic at memory.py:251-259 executes inside the dedup drop path but has zero observability. The logic: if a new store request has higher importance than the existing memory, the existing memory's importance is promoted. This is a correctness-critical path — if it silently fails (exception caught at line 258, pass), the existing memory retains a stale low importance score and the new high-importance signal is lost with no trace. Since Q16.4 confirms no structlog, no audit_log, and no Prometheus counter at this path, any failure mode here is invisible. This question audits the correctness and exception handling of this path.
**Test**: (1) Read memory.py lines 247-270. (2) Check: does the try/except at line 258 log the exception? It currently has `except Exception: pass` -- completely silent. (3) Check: does qdrant.update_importance() have its own logging? Read the qdrant store's update_importance() method. (4) Write a test scenario: store a memory with importance=0.3, then attempt to store a near-duplicate with importance=0.9. Verify the existing memory's importance is updated to 0.9.
**Verdict threshold**:
- FAILURE: `except Exception: pass` silently swallows importance update failures with no log; OR qdrant.update_importance() has no error handling; importance inheritance is a silent black box
- WARNING: exception is caught and logged but at DEBUG level; importance update failures are not visible in production
- HEALTHY: importance update path has adequate error logging; a test confirms the promotion works correctly
**Derived from**: Q16.4 FAILURE -- memory.py dedup path has zero observability; importance inheritance logic has bare except:pass at line 258

---

## Wave 18 — Silent Write Failures, Timeout Deployment Blockers, and Dedup Correctness Consequences (Q18.x)

## Q18.1 [DOMAIN-5] Decay batch write failure mode — does asyncio.gather() over update_importance calls abort the entire batch on first Qdrant error, leaving remaining memories un-decayed?
**Status**: WARNING
**Mode**: correctness
**Target**: `src/workers/decay.py` lines 183–188 (`asyncio.gather` over `qdrant.update_importance` and `neo4j.update_importance`), `src/storage/qdrant.py` `update_importance()` (line 476)
**Hypothesis**: Q16.4b established that `qdrant.update_importance()` has no internal error handling — it calls `client.set_payload()` naked and propagates exceptions to callers. In decay.py, the batch write at lines 184–187 fans out all per-memory importance updates via `asyncio.gather()` without `return_exceptions=True`. If any single `set_payload` call raises (Qdrant transient error, unknown point ID, network blip), `asyncio.gather` will propagate the first exception, abort the entire gather, and skip all remaining importance updates in the batch. The `stats["decayed"] += len(decay_updates)` at line 188 would then be an overcount — crediting all planned updates even though only some completed. Since this is a background worker with no per-call logging on success, there is no way to detect partial batch failures from the audit log or metrics.
**Test**: (1) Read `decay.py` lines 183–192 — confirm `asyncio.gather` has no `return_exceptions=True`. (2) Read the enclosing `try/except` block — determine what catches the gather if it raises (is the gather inside a try block? what is the outer exception handler?). (3) Grep for `return_exceptions` in the decay worker. (4) Simulate a partial failure scenario: what happens to `stats["decayed"]` if `gather` raises after completing 3 of 10 updates? (5) Check whether the decay audit log (`_log_decay_audit`) is written before or after the gather — if after, a gather failure means no audit entry either.
**Verdict threshold**:
- FAILURE: `asyncio.gather` has no `return_exceptions=True` AND the gather is not inside a try block with per-batch error logging; a single Qdrant failure silently aborts the entire decay batch with incorrect `stats["decayed"]` accounting
- WARNING: `asyncio.gather` has no `return_exceptions=True` but the outer exception handler logs the failure; partial batch aborts are visible but not recoverable
- HEALTHY: `return_exceptions=True` is used and per-failure logging handles partial writes; OR each update is individually awaited with per-memory error handling

**Derived from**: Q16.4b FAILURE — `qdrant.update_importance()` has no error handling; pattern confirmed at `update_pinned()` too; decay.py is the highest-volume consumer of batch importance writes (runs on scroll_all results daily)

---

## Q18.2 [DOMAIN-5] Retrieval access-stat write failures — do update_importance(), update_confidence(), and update_access() calls in retrieval.py fire outside any error boundary, making per-retrieval stat updates silently lossy?
**Status**: WARNING
**Mode**: correctness
**Target**: `src/core/retrieval.py` lines 1540–1555 (`_update_access_stats` method, post-retrieval importance/confidence/access writes)
**Hypothesis**: Q16.4b identified `update_importance()` and `update_pinned()` as having no error handling at the storage layer. `retrieval.py:_update_access_stats` (lines 1540–1555) calls `qdrant.update_importance()`, `qdrant.update_confidence()`, and `qdrant.update_access()` in sequence with no surrounding try/except. If any of these three calls raises, the exception propagates up through `_update_access_stats` to the background task caller. Since this is a background task (likely spawned via `asyncio.create_task`), an unhandled exception may be silently swallowed by the event loop with only an `asyncio` error log. This means per-retrieval access reinforcement — the mechanism by which frequently-retrieved memories gain importance — is silently lossy on any Qdrant transient error.
**Test**: (1) Read `retrieval.py` lines 1495–1560 — identify whether `_update_access_stats` is called directly, via `asyncio.create_task`, or via `background_tasks.add_task`. (2) Check whether the call site wraps the task in a try/except. (3) Confirm whether `update_importance`, `update_confidence`, and `update_access` calls at lines 1542–1555 have any error handling. (4) Identify what happens to the access reinforcement feedback loop if the first call (`update_importance`) raises: are `update_confidence` and `update_access` still attempted? (5) Check whether any test covers partial failure in `_update_access_stats`.
**Verdict threshold**:
- FAILURE: all three write calls are outside any try/except AND the method is called as a background task where unhandled exceptions are silently discarded; access reinforcement can silently fail with no observable signal
- WARNING: write calls are outside try/except but the caller catches exceptions with logging; failures are visible but the partial-write state (some stats updated, some not) is not corrected
- HEALTHY: write calls are individually wrapped in try/except with logging; OR the calling pattern guarantees exception visibility (e.g., `await` in a monitored context)

**Derived from**: Q16.4b FAILURE — storage write methods uniformly lack error handling; `retrieval.py` is the most frequent consumer of `update_importance()` (called on every cache-miss retrieval hit for memories not accessed in the last hour)

---

## Q18.3 [DOMAIN-5] LLM timeout deployment gap — with httpx override confirmed sound (Q16.3b HEALTHY), what is the minimum changeset blocking immediate deployment of the per-caller timeout fix, and does any callsite have a structural impediment?
**Status**: DONE
**Mode**: correctness
**Target**: `src/core/llm.py` `generate()` signature (line 51), all 14+ `llm.generate()` callsites across `src/workers/` and `src/api/` and `src/core/`
**Hypothesis**: Q16.3 confirmed the fix is undeployed. Q16.3b confirmed httpx override semantics are correct. The minimum deployment changeset is: (1) add `timeout: float | None = None` to `generate()`, (2) add `fact_extraction_timeout` and `consolidation_timeout` to config, (3) update each callsite to pass its type-appropriate timeout. The risk is that some callers may not have a clearly mappable timeout type — e.g., `admin.py` ad-hoc LLM calls, `search.py` narrative generation, `causal_extractor.py`, `dream_consolidation.py` — and leaving them without a timeout argument means they still fall through to the 180s global. This question audits the full callsite inventory: which callers map cleanly to a known timeout category, which are ambiguous, and whether any caller has a structural reason (e.g., intentionally long-running) that would justify the full 180s rather than a shorter per-type value.
**Test**: (1) Read `generate()` in `llm.py` — confirm current signature. (2) Enumerate all 14+ callsites from: `workers/fact_extractor.py`, `workers/observer.py`, `workers/signals.py` (via `signal_detector.py`), `core/consolidation.py`, `core/contradiction_detector.py`, `core/causal_extractor.py`, `workers/cognitive_distiller.py`, `workers/dream_consolidation.py`, `workers/patterns.py`, `workers/profile_drift.py`, `workers/state_fact_extractor.py`, `api/routes/admin.py`, `api/routes/search.py`, `core/document_ingest.py`. (3) For each callsite, classify: (a) maps to `fact_extraction_timeout` (60s), (b) maps to `consolidation_timeout` (90s), (c) ambiguous / needs new timeout category, (d) intentionally unbounded. (4) Report: how many callsites can be updated without a new config value, how many require a new named timeout, and whether any callsite is a structural blocker.
**Verdict threshold**:
- FAILURE: >3 callsites are structurally ambiguous or require new timeout categories that are not yet defined in config; deployment is blocked pending further classification work
- WARNING: 1-3 callsites are ambiguous but the highest-volume paths (fact_extraction, consolidation) can be updated immediately; partial deployment is possible but incomplete
- HEALTHY: all callsites map cleanly to ≤3 named timeout categories; no structural blocker; the fix is a mechanical 1-line change per callsite with no design decisions outstanding

**Derived from**: Q16.3 FAILURE — 14+ callsites all use global 180s; Q16.3b HEALTHY — httpx override confirmed sound; the deployment is architecturally unblocked; this question asks whether it is operationally unblocked

---

## Q18.4 [DOMAIN-4] Dedup correctness consequence — are near-duplicate signals actually being stored in Qdrant despite the dedup path being intended to prevent them, due to the signals.py dedup operating at DEBUG level only?
**Status**: DONE
**Mode**: correctness
**Target**: `src/workers/signals.py` lines 239–248 (content hash dedup), lines 285–301 (semantic dedup), `src/workers/observer.py` lines 169–176 (observer semantic dedup), Qdrant collection via `scroll_all`
**Hypothesis**: Q16.4 confirmed that signals.py dedup fires at DEBUG level (structlog only, no counter, no audit) and observer.py dedup has zero instrumentation. However, the observability gap raises a deeper correctness question: given that these dedup paths return `None, None` or `continue` silently, is it possible that near-duplicates are entering Qdrant anyway through a different code path? Specifically: if signals.py dedup fires and returns `None, None`, does the caller (`signals.py` main flow) still proceed to store the signal? The answer depends on whether the caller correctly handles `None, None`. If the caller stores the signal unconditionally regardless of the dedup return value, the dedup logic is present but bypassed. This question verifies the functional correctness of the dedup mechanism — not just its observability.
**Test**: (1) Read `signals.py` lines 239–320 — identify what the caller does with the `None, None` return from the content-hash dedup path. (2) Read `signals.py` lines 285–315 — identify what the caller does with `None, None` from semantic dedup. (3) Trace the full call chain: from dedup hit to `return None, None` to the calling function — does the caller short-circuit and skip the Qdrant store? (4) For observer.py: read lines 160–200 — after `continue`, is there any additional code path in the loop that could still store the memory? (5) As a ground truth check: query Qdrant for memories with cosine similarity > 0.95 to any other memory — count the pairs. If near-duplicates are present in meaningful volume, dedup is either not firing or is being bypassed.
**Verdict threshold**:
- FAILURE: the caller of the dedup return path stores the signal anyway (dedup is functionally bypassed); OR Qdrant contains >10 pairs of memories with similarity >0.95 (statistically implausible if dedup was working correctly at the 0.92 threshold)
- WARNING: dedup return is handled correctly but the `None, None` sentinel is not a well-typed signal (relies on caller convention rather than a typed guard); future refactors could introduce bypass risk
- HEALTHY: caller correctly handles `None, None` by not storing; observer `continue` correctly skips the rest of the loop body; Qdrant near-duplicate pair count is ≤5 (consistent with a working dedup at 0.92)

**Derived from**: Q16.4 FAILURE — dedup observability gap prevents confirmation that dedup is working; Q16.4b FAILURE — importance inheritance may silently fail; this question tests whether the dedup mechanism itself is functionally correct, independent of its observability

---

## Q18.5 [DOMAIN-1] Dedup threshold asymmetry — do episodic and session_summary type exemptions from dedup cause measurable corpus bloat, or is the exemption correctly scoped to prevent collapsing distinct temporal records?
**Status**: INCONCLUSIVE
**Mode**: benchmark
**Target**: `src/api/routes/memory.py` lines 234–235 (dedup skip types: `{"episodic", "session_summary"}`), PostgreSQL `memories` table, Qdrant collection
**Hypothesis**: The dedup path at memory.py:234 explicitly exempts `episodic` and `session_summary` memory types from semantic dedup, reasoning that each is a distinct temporal record. This is a correctness-first decision but has a potential corpus bloat consequence: if the same session produces structurally similar session summaries (e.g., two sessions where Claude did similar work), they will both be stored regardless of similarity. Over time, the session_summary type could accumulate near-duplicate content that the 0.92 threshold would have caught for other types. This question quantifies whether the exemption is causing measurable redundancy: what is the p99 pairwise similarity between session_summary entries, and between episodic entries? If either distribution has a significant mass above 0.85, the exemption is generating corpus bloat that the dedup threshold was designed to prevent.
**Test**: (1) Query: `SELECT COUNT(*) FROM memories WHERE memory_type = 'session_summary'` and `WHERE memory_type = 'episodic'` — establish baseline counts. (2) Via Qdrant scroll_all filtered to session_summary type, compute pairwise cosine similarity for a sample of 100 entries. Report the distribution: what fraction have similarity > 0.85 with at least one other entry? > 0.92? (3) Repeat for episodic type. (4) Compare to the non-exempt types (e.g., `factual`, `procedural`) — does the exempt types have a higher near-duplicate density than the non-exempt corpus? (5) Report: what fraction of the total memory corpus is composed of exempt types?
**Verdict threshold**:
- FAILURE: >5% of session_summary entries have a near-duplicate (similarity > 0.92) in the corpus — the exemption is generating corpus bloat at the same scale that dedup was designed to prevent
- WARNING: 1–5% of exempt-type entries are near-duplicates; low but non-zero redundancy; no immediate action needed but worth tracking as corpus grows
- HEALTHY: <1% of exempt-type entries are near-duplicates; the exemption is correctly scoped; temporal distinctiveness is sufficient to prevent meaningful redundancy

**Derived from**: Q16.4 FAILURE — dedup observability gap means no one has verified whether the exemption is correctly scoped; Q14.8 WARNING — session_summary dedup exemption was added without quantifying how many session summaries are semantically similar; this question provides the first data-backed answer


---

## Wave 19 -- Silent Write Failures (Scope Expansion), Dedup Observability Operational Cost, LLM Semaphore Cascade, Importance Corpus Audit, and Unguarded Fire-and-Forget Tasks (Q19.x)

## Q19.1 [DOMAIN-5] Unguarded asyncio.gather() scope audit -- beyond decay.py, are there other batch-write workers that use asyncio.gather() without return_exceptions=True, creating the same partial-batch-abort failure mode?
**Status**: DONE
**Mode**: correctness
**Target**: `src/workers/` and `src/core/` -- all files that call `asyncio.gather()`, excluding decay.py (already confirmed in Q18.1)
**Hypothesis**: Q18.1 WARNING confirmed that decay.py:184-187 uses `asyncio.gather()` without `return_exceptions=True` across a batch of importance updates. The Q18.1 finding explicitly posed the follow-up: "Does the same unguarded gather pattern exist in other batch-write workers?" Given that decay.py, consolidation.py, and the graph-link workers all perform parallel bulk writes, and given that Q16.4b established that `qdrant.update_importance()` propagates all exceptions to callers, the same abort pattern is likely present wherever `asyncio.gather()` fans out over storage calls. If consolidation.py uses gather for its Neo4j SUPERSEDES edge writes, a single Neo4j transient error would abort the entire consolidation batch with no audit entry -- a higher-severity version of the decay problem, because consolidation is the only mechanism that writes content-merge audit records.
**Test**: (1) Grep `asyncio.gather` across all `src/workers/*.py` and `src/core/*.py` files -- list every callsite. (2) For each callsite, check whether `return_exceptions=True` is present. (3) For each unguarded gather, identify: (a) what the gathered coroutines do (storage writes, external calls, etc.), (b) what the surrounding try/except covers, (c) whether missing audit writes or stat updates result from a raise. (4) Specifically check `core/consolidation.py` -- if it uses gather for Neo4j SUPERSEDES edge writes, a failure here would leave ghost memories (Qdrant updated, Neo4j edge missing). (5) Report a complete inventory: N total gather calls, M without return_exceptions, and the severity of each unguarded call.
**Verdict threshold**:
- FAILURE: consolidation.py or any other high-severity writer uses unguarded gather -- a single transient error can abort content-merge operations, leaving the corpus in an inconsistent Qdrant/Neo4j state with no audit trail
- WARNING: unguarded gather exists in lower-severity workers (profile_drift, patterns) but not in consolidation; partial-write risk is present but does not affect the core integrity path
- HEALTHY: all gather calls in non-decay workers use `return_exceptions=True` or are individually awaited; only decay.py carries the Q18.1 WARNING pattern

**Derived from**: Q18.1 WARNING -- decay.py asyncio.gather() no return_exceptions=True; open follow-up explicitly asks whether this pattern exists elsewhere; Q16.4b FAILURE -- qdrant.update_importance() propagates all exceptions to callers

---

## Q19.2 [DOMAIN-5] _store_retrieval_context fire-and-forget audit -- does the asyncio.create_task(_store_retrieval_context) at retrieval.py:572 have the same unguarded write pattern as _track_access, and does it write to Qdrant/Neo4j outside any error boundary?
**Status**: DONE
**Mode**: correctness
**Target**: `src/core/retrieval.py` line 572 (`asyncio.create_task(self._store_retrieval_context(...))`) and the `_store_retrieval_context` method body
**Hypothesis**: Q18.2 WARNING confirmed that `_track_access()` at retrieval.py:568 is a fire-and-forget task with five bare await calls to storage writers. The Q18.2 finding explicitly noted: "Does the `_store_retrieval_context` task at line 572 have the same unguarded pattern? It runs concurrently with `_track_access` and also has no return value check." These two tasks are spawned back-to-back at lines 568 and 572. If `_store_retrieval_context` also writes to Qdrant or Neo4j without per-call error handling, then every retrieval event spawns two concurrent fire-and-forget tasks, either of which can fail silently and leave an inconsistent access state. The compound failure mode -- both tasks failing simultaneously on the same retrieval event -- is worse than the Q18.2 finding because it means zero access state is recorded for that retrieval event.
**Test**: (1) Read retrieval.py lines 565-580 -- confirm the spawn sites for both tasks. (2) Read the full `_store_retrieval_context` method body -- identify all storage writes (Qdrant, Neo4j, Redis, PostgreSQL). (3) Check whether those writes are inside a try/except. (4) Identify the difference in scope between `_track_access` (per-memory importance/access update) and `_store_retrieval_context` (what does this one store?). (5) Check whether either task has a callback or error handler registered via `task.add_done_callback()`. (6) Compare the two tasks: if both raise on the same retrieval event, what is the net state change in Qdrant and Neo4j?
**Verdict threshold**:
- FAILURE: `_store_retrieval_context` writes to Qdrant or Neo4j outside any try/except AND no done_callback is registered; two concurrent fire-and-forget tasks can both fail silently, leaving retrieval events with zero state updates
- WARNING: `_store_retrieval_context` has bare writes but they are lower-severity (e.g., Redis working set only, no Qdrant/Neo4j writes); or the method has a top-level try/except that catches all storage exceptions
- HEALTHY: `_store_retrieval_context` either has per-write error handling or does not write to persistent storage (Qdrant/Neo4j); the fire-and-forget pattern is acceptable for its use case

**Derived from**: Q18.2 WARNING -- _track_access fire-and-forget bare awaits; open follow-up explicitly names _store_retrieval_context at line 572 as the next unverified task; Q16.4b FAILURE -- storage write methods uniformly lack error handling

---

## Q19.3 [DOMAIN-5] LLM semaphore cascade under Semaphore(1) -- when a per-caller timeout fires while others are queued, does Semaphore(1) guarantee FIFO ordering and does the timeout fix actually bound interactive caller latency to the signal_detection ceiling?
**Status**: DONE
**Mode**: benchmark
**Target**: `src/core/llm.py` asyncio.Semaphore(1), Python asyncio.Semaphore ordering guarantees, `prompt_metrics` latency data for signal_detection calls that queued behind consolidation calls
**Hypothesis**: Q18.3 HEALTHY confirmed 17 LLM callsites across 4 timeout tiers (15s interactive, 60s background, 90s long-running, 120s admin). Under Semaphore(1) with the fix deployed, a new failure mode emerges: Python asyncio.Semaphore does not document FIFO ordering. When the semaphore is released (either by normal completion or by timeout exception), any waiting coroutine may acquire it. If consolidation.py (90s timeout) acquires ahead of signal_detector.py (15s timeout), the interactive call still waits up to 90s. The per-caller timeout fix bounds the hold time of an active caller but does not guarantee that a fast-timeout caller is served before a slow-timeout caller. Under Semaphore(1), the worst-case signal_detection wait is bounded by one full consolidation timeout (90s) regardless of per-caller values -- only a priority-aware queue (Q14.4a) would actually deliver the 15s interactive ceiling.
**Test**: (1) Read `llm.py` -- confirm Semaphore(1) is the concurrency mechanism. (2) Check Python asyncio.Semaphore documentation: does acquire() use a FIFO queue or unordered set? (3) Query prompt_metrics for signal_detection calls where a consolidation call was running in the prior 120s: SELECT a.prompt_type, a.latency_ms, b.prompt_type AS preceding_type FROM prompt_metrics a JOIN prompt_metrics b ON b.prompt_type IN ('consolidation','dream_consolidation') AND b.timestamp BETWEEN a.timestamp - interval '120s' AND a.timestamp WHERE a.prompt_type = 'signal_detection' ORDER BY a.latency_ms DESC LIMIT 20. (4) Compare signal_detection latency when consolidation was running vs. not. (5) Report: does empirical data show signal_detection is penalized when consolidation is co-running, and by how much?
**Verdict threshold**:
- FAILURE: asyncio.Semaphore is NOT FIFO; empirical data shows signal_detection p95 >60s when consolidation is co-running; per-caller timeout fix does not deliver interactive latency improvement; priority queue (Q14.4a) is required
- WARNING: asyncio.Semaphore is FIFO by implementation but empirical data shows signal_detection still queues behind consolidation in practice; improvement is real but not the advertised 15s ceiling
- HEALTHY: asyncio.Semaphore is FIFO AND empirical signal_detection latency is below 30s even when consolidation is co-running; the per-caller timeout fix is sufficient without priority routing

**Derived from**: Q18.3 HEALTHY -- all 17 callsites deployable; Q14.4a INCONCLUSIVE -- priority queue proposed but not built; Q15.3 FAILURE -- Semaphore(1) does not prevent interactive callers from waiting behind slow background calls; this question tests whether the per-caller timeout fix alone achieves the interactive latency goal

---

## Q19.4 [DOMAIN-4] Importance corpus contamination -- what fraction of active memories have importance=0.5 (the store-time default), and is the default-cluster anomalously large given the expected number of importance-inheritance promotions?
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant collection (importance field distribution across all living memories), PostgreSQL `audit_log` (store event volume as proxy for dedup event frequency), `src/api/routes/memory.py` importance-inheritance block (lines 251-259)
**Hypothesis**: Q16.4b FAILURE confirmed that the importance-inheritance block in memory.py:251-259 uses `except Exception: pass`, silently swallowing all Qdrant errors during importance updates. If `qdrant.update_importance()` has been failing on transient errors since the feature was deployed, every dedup event where the incoming memory had higher importance has left the existing memory at its original importance score. The visible symptom would be: a high fraction of memories sitting at importance=0.5 (the store-time default). A healthy corpus with active importance-inheritance would show a continuous distribution from 0.5 upward. A bimodal distribution with a spike at 0.5 and another at 0.9 (pinned memories) with nothing in between is the fingerprint of a broken middle-tier promotion path.
**Test**: (1) Via the Recall API or Qdrant HTTP, scroll all living memories and extract the importance field. (2) Bucket the distribution at 0.1 intervals and specifically count memories at exactly 0.5. (3) Report: what percentage of memories are at exactly 0.5? What percentage are above 0.7? (4) From audit_log: count total creates vs. current memory count -- the gap gives a lower-bound on dedup+supersedure events, and thus the expected number of importance-inheritance triggers. (5) Cross-check: query for memories with access_count > 5 -- these should have importance > 0.5 from _track_access reinforcement. If they do not, both importance update paths are broken.
**Verdict threshold**:
- FAILURE: >60% of active memories have importance = 0.5 AND memories with access_count > 5 also show importance near 0.5 -- both the importance-inheritance AND the _track_access reinforcement paths are silently failing; importance values are frozen at store-time defaults
- WARNING: 40-60% of memories at 0.5 OR memories with high access_count show importance = 0.5; partial failure in one of the two promotion paths
- HEALTHY: <40% of memories at 0.5 AND memories with access_count > 5 show importance > 0.5 -- both importance update paths are functioning; Q16.4b except:pass is either not triggering or the update is succeeding despite missing error handling

**Derived from**: Q16.4b FAILURE -- except:pass silently swallows importance update failures in dedup path; Q18.2 WARNING -- _track_access also has bare update_importance calls that can fail silently; this question tests the combined impact of both failure modes on the actual importance distribution in the corpus

---

## Q19.5 [DOMAIN-4] Dedup hit rate lower-bound via audit proxy -- can audit_log create-event volume minus current corpus size estimate an implied dedup rate, and does the git history reveal the empirical basis for the 0.92 threshold?
**Status**: DONE
**Mode**: benchmark
**Target**: PostgreSQL `audit_log` (create event count), `memories` table (total rows including superseded), git log for `src/core/config.py` (threshold change history), Prometheus /metrics (`recall_memories_total`)
**Hypothesis**: Q18.4 HEALTHY confirmed dedup is functionally correct but direct hit rate measurement is impossible without instrumentation (Q15.1 INCONCLUSIVE). Q18.5 INCONCLUSIVE established that a Qdrant batch similarity scan is infeasible. However, an indirect proxy exists: audit_log records every successful create event. Total store attempts minus successful creates equals the combined volume of dedup drops plus validation rejections -- a lower-bound on dedup activity. Additionally, the threshold was changed from 0.90 to 0.92 at some point (Q13.4a synthesis). If the git commit message for this change contains the rationale, it provides the only human-authored calibration evidence for the threshold. Without this context there is no way to know whether 0.92 was chosen for a reason or arbitrarily.
**Test**: (1) Query: SELECT COUNT(*) FROM audit_log WHERE action = 'create'. (2) Query: SELECT COUNT(*) FROM memories (all rows including superseded). (3) Compute: implied_drops = audit_creates - total_memories. Note this is a ceiling (includes supersedure), not just dedup. (4) Run git log against config.py and look for commits referencing threshold, dedup, or similarity -- read the full commit message. (5) From /metrics, confirm recall_memories_total counter and compare to audit_log create count. (6) Report: the implied drop volume and whether the threshold change has a documented rationale.
**Verdict threshold**:
- FAILURE: implied drop volume >10% of total creates AND git history shows threshold was set without empirical basis -- significant data loss at an unjustified threshold
- WARNING: implied drop volume 1-10% OR git history shows threshold was changed reactively without quantification; material drop activity at a weakly-justified threshold
- HEALTHY: implied drop volume <1% (consistent with conservative threshold) OR git commit shows threshold was based on empirical observation of false positive rate -- the 0.92 threshold is justified even without real-time counters

**Derived from**: Q15.1 INCONCLUSIVE -- hit rate completely unquantifiable via direct observation; Q18.4 HEALTHY -- dedup functionally correct but ground-truth scan not feasible; Q13.4a WARNING -- threshold change from 0.90 to 0.92 noted but rationale undocumented in any finding; this question attempts the indirect measurement path and documentation audit simultaneously

---

## Q19.6 [DOMAIN-5] Neo4j write error handling scope -- can a Neo4j transient error during consolidation produce a split-brain state where a memory is superseded in Qdrant but still active in the graph, and do neo4j.py write methods propagate exceptions as nakedly as the Qdrant methods confirmed in Q16.4b?
**Status**: DONE
**Mode**: correctness
**Target**: `src/storage/neo4j.py` core write methods (`create_memory_node`, `create_relationship`, `update_importance`, `create_supersedes`), and their callsites in `src/core/consolidation.py`
**Hypothesis**: Q16.4b FAILURE established that `qdrant.update_importance()` has no internal error handling. Q18.2 WARNING showed that retrieval.py calls `neo4j.update_importance()` as a bare await alongside Qdrant calls. However, the most critical Neo4j write path has not been audited: the SUPERSEDES edge creation during consolidation. Consolidation writes a supersede record to Qdrant (marking the old memory as superseded), creates a SUPERSEDES edge in Neo4j, and writes an audit_log entry. If consolidation writes Qdrant first and then the Neo4j write fails with an unhandled exception, the memory is marked superseded in the vector store but still appears active in the graph. Graph-based retrieval paths would continue to surface the superseded memory; vector-based retrieval would not. This Qdrant/Neo4j split-brain is the worst consistency failure mode in the codebase because it is invisible and potentially permanent.
**Test**: (1) Read `src/storage/neo4j.py` -- examine `create_memory_node()`, `create_relationship()`, `update_importance()`, and `create_supersedes()` for internal try/except coverage. (2) Read `src/core/consolidation.py` -- identify the sequence of writes: when does it write to Qdrant vs Neo4j, and are they inside a shared try/except or separate? (3) Determine write order: if Qdrant is written before Neo4j, a Neo4j failure leaves Qdrant in a terminal superseded state with no compensating rollback. (4) Check whether any integration test covers partial consolidation failure (Qdrant succeeds, Neo4j raises). (5) Report: is a Qdrant/Neo4j split-brain state possible on a Neo4j transient error, and is there any detection or repair mechanism?
**Verdict threshold**:
- FAILURE: consolidation.py writes Qdrant SUPERSEDES before Neo4j SUPERSEDES edge with no compensating rollback; a Neo4j transient error produces a split-brain corpus state (vector store: superseded, graph: active) with no audit trail and no repair path
- WARNING: Neo4j write methods propagate exceptions but consolidation wraps both writes in a shared try/except that logs the failure and skips or rolls back the Qdrant write; split-brain is prevented but the rollback correctness is untested
- HEALTHY: Neo4j write methods have internal error handling OR consolidation uses an atomic write pattern (e.g., write Neo4j first, then Qdrant); split-brain state is not possible on transient failures

**Derived from**: Q16.4b FAILURE -- qdrant storage writes uniformly lack error handling; Q18.1 WARNING -- asyncio.gather() in decay can leave partial Qdrant writes with no Neo4j counterpart; Q18.2 WARNING -- _track_access calls both Neo4j and Qdrant bare; this question targets the consolidation path where Qdrant/Neo4j consistency determines whether the corpus can be trusted for graph-based retrieval

---

## Wave 20 — Split-Brain Quantification, Reconcile Coverage, and Corpus Quality Measurement (Q20.x)

*Derived from Wave 19 findings (2026-03-15). Wave 20 addresses three open threads: (1) the Q19.6 split-brain claim of "permanent divergence" was incomplete — reconcile.py exists and repairs it weekly, but the current backlog is unknown; (2) the Q19.4 0.5-importance cluster age distribution and memory_type breakdown needed to isolate Q16.4b contribution; (3) the Q19.5 dedup threshold has never been empirically calibrated on the live corpus. Wave 20 also probes the reconcile worker's own correctness and scalability.*

---

## Q20.1 [DOMAIN-5] Current split-brain backlog — how many memories are Qdrant-superseded but Neo4j-active right now, and when did the last reconcile run?
**Status**: DONE
**Mode**: observability
**Target**: `POST /admin/reconcile?repair=false` (report-only mode) + audit_log for last reconcile timestamp
**Hypothesis**: Q19.6 concluded that split-brain divergence from consolidation failures is "permanent." This is incorrect: `src/workers/reconcile.py` runs weekly (Sundays 5:30am) and explicitly detects and repairs `superseded_mismatches` by syncing Qdrant → Neo4j. However, the repair window is up to 7 days. The current `superseded_mismatches` count from a live reconcile report will reveal: (a) whether any split-brain memories currently exist, (b) the scale of divergence since the last Sunday run, and (c) whether the reconcile cadence is adequate for the consolidation rate (1 consolidation/hour × potential Neo4j transient errors).
**Test**: (1) Call `POST /admin/reconcile?repair=false` against the live system (192.168.50.19:8200) and record `superseded_mismatches`, `importance_mismatches`, `qdrant_orphans`, `neo4j_orphans`. (2) Query audit_log: `SELECT MAX(timestamp) FROM audit_log WHERE action = 'reconcile'` to find the last repair run. (3) Query audit_log: `SELECT COUNT(*) FROM audit_log WHERE action = 'consolidate' AND timestamp > (last reconcile timestamp)` to count consolidation runs since last repair. Compute: implied split-brain rate = superseded_mismatches / consolidations_since_last_reconcile.
**Verdict threshold**:
- FAILURE: `superseded_mismatches` > 50 (more than 50 memories currently in split-brain state) OR last reconcile run > 14 days ago (repair cadence broken)
- WARNING: `superseded_mismatches` 1–50 (split-brain exists but manageable scale) OR implied split-brain rate > 1% of consolidation runs
- HEALTHY: `superseded_mismatches` = 0 AND last reconcile run < 7 days ago AND implied split-brain rate < 1%

**Derived from**: Q19.6 FAILURE -- split-brain path confirmed at consolidation.py:282-283; reconcile.py discovered during source audit as the repair mechanism not mentioned in Q19.6; Q19.6 open follow-up: "Are there any known production consolidation failures visible in the audit log?"

---

## Q20.2 [DOMAIN-5] Reconcile worker scalability -- does scroll_all(include_superseded=True) over 20,836 memories complete within the 30-minute ARQ job timeout, and what happens as the corpus grows?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/workers/reconcile.py:23` (`qdrant.scroll_all(include_superseded=True)`) + `src/api/routes/ops.py:262` (same pattern in the admin endpoint)
**Hypothesis**: Both the worker and admin reconcile paths call `qdrant.scroll_all(include_superseded=True)` followed by `neo4j.get_all_memory_ids()` and `neo4j.get_bulk_memory_data(list(common_ids))`. At 20,836 memories this is an O(N) Qdrant scroll + O(N) Neo4j bulk fetch. The ARQ job timeout is 30 minutes. As the corpus grows to 100K+ memories, the reconcile run time grows linearly. The admin endpoint has no timeout protection — a 100K-memory reconcile via `POST /admin/reconcile` would hold the HTTP connection open for potentially minutes. The question is: what is the current measured run time, and at what corpus size does it breach the 30-minute ARQ limit?
**Test**: (1) Read `src/workers/reconcile.py` -- confirm there is no pagination, batching, or cursor resumption in the scroll_all call. (2) Read `src/storage/qdrant.py` `scroll_all()` implementation -- confirm page size and total pages for 20,836 memories. (3) Calculate: at current Qdrant scroll page size, how many round trips does scroll_all require for 20,836 memories? At ~50ms/round trip, what is the estimated full-corpus scan time? (4) Read `neo4j.get_bulk_memory_data()` -- what is the Cypher query structure, and does it use `UNWIND` batching or per-ID queries? (5) Model: at what corpus size (50K / 100K / 200K) does the reconcile run exceed 30 minutes?
**Verdict threshold**:
- FAILURE: scroll_all has no pagination cursor (entire corpus fetched in one blocking call) OR neo4j.get_bulk_memory_data() issues per-ID queries (O(N) Cypher calls) OR modeled breach of 30-minute timeout before 100K corpus size
- WARNING: pagination exists but admin HTTP endpoint has no timeout guard (long-running request possible) OR modeled breach between 100K–200K
- HEALTHY: scroll_all is paginated with cursor, neo4j fetch is single batched UNWIND query, modeled 30-minute breach > 500K corpus size

**Derived from**: Q19.6 source audit revealing reconcile.py existence; reconcile uses scroll_all(include_superseded=True) which was flagged as O(N) in Q13.8b (Markov Chain context); Q20.1 establishes the repair is real -- this question establishes whether the repair mechanism itself has a scalability ceiling

---

## Q20.3 [DOMAIN-1] Importance=0.5 cluster age and memory_type breakdown -- are the 889 stuck memories fresh creates or Q16.4b casualties?
**Status**: DONE
**Mode**: observability
**Target**: Qdrant `recall_memories` collection -- scroll with filter `importance ∈ [0.499, 0.501]`
**Hypothesis**: Q19.4 found 889 memories at exactly importance=0.5 (21x spike, 99% never-accessed) but could not determine whether they are: (a) fresh creates not yet processed by decay (expected transient), or (b) memories whose importance-inheritance promotion silently failed via Q16.4b's `except Exception: pass` (pathological persistent). The discriminator is `created_at` age: if >80% of the 889 memories are >7 days old, they have been through multiple decay cycles and are stuck -- decay would have moved them to 0.3–0.4 otherwise. Additionally, a `memory_type` breakdown (semantic vs episodic vs procedural) would reveal whether the 0.5 cluster is disproportionately `semantic` -- the memory type where importance-inheritance fires during dedup -- which would implicate Q16.4b as the dominant cause.
**Test**: (1) Scroll Qdrant for all memories with `importance ∈ [0.499, 0.501]`. For each, extract `created_at`, `memory_type`, `access_count`, `domain`. (2) Compute age distribution: bucket by <1 day, 1–7 days, 7–30 days, >30 days. (3) Compute memory_type distribution: what fraction are `semantic` vs `episodic` vs other? (4) Compare: if the corpus-wide semantic fraction is X%, and the 0.5-cluster semantic fraction is >2X%, Q16.4b importance-inheritance failure is the primary cause. (5) Report: age distribution, memory_type breakdown, and estimated Q16.4b contribution vs fresh-create explanation.
**Verdict threshold**:
- FAILURE: >50% of 0.5-cluster memories are >30 days old AND disproportionately semantic (>2x corpus-wide semantic rate) -- Q16.4b is the dominant cause, cluster will not self-resolve
- WARNING: 20–50% are >30 days old OR mild semantic over-representation (1.5–2x) -- mixed cause, partial Q16.4b contribution
- HEALTHY: >80% are <7 days old AND memory_type distribution matches corpus-wide rate -- fresh-create explanation confirmed, cluster will self-resolve via decay

**Derived from**: Q19.4 WARNING -- 889 memories at 0.5 default, Q16.4b contribution "cannot be excluded"; Q19.4 open follow-up: "Are the 889 memories at 0.5 disproportionately concentrated in any memory_type or domain? What is the age distribution?"

---

## Q20.4 [DOMAIN-1] Dedup threshold empirical calibration -- how many near-duplicates does the live corpus contain at 0.90 vs 0.92, and what does the difference reveal about false-positive rate?
**Status**: DONE
**Mode**: observability
**Target**: `POST /admin/dedup` batch scan endpoint against live corpus (20,836 memories)
**Hypothesis**: Q19.5 found the 0.92 dedup threshold was set qualitatively ("reduce false-positive dedup on qwen3-embedding range") with no empirical calibration. The only prior empirical measurement was a 2026-02-19 batch scan that found 129 near-duplicates at 0.90 in a 4,602-memory corpus (2.8%). The current corpus is 4.5x larger (20,836 memories). Running the admin batch scan at both 0.90 and 0.92 will yield: (a) current near-duplicate count at 0.92 (the active threshold), (b) the delta count at 0.90 (memories that were caught at 0.90 but escaped at 0.92), and (c) by sampling the delta entries, an estimate of the false-positive rate for the 0.90–0.92 similarity band. If the delta is large (>200 entries) and a manual sample of the delta shows mostly true duplicates, the 0.92 raise was overcorrected. If the delta is small (<20 entries) or samples as false positives, the 0.92 threshold is correctly calibrated.
**Test**: (1) Call the admin batch dedup endpoint (or equivalent Qdrant scan) at threshold=0.92 and record total near-duplicate pairs found. (2) Repeat at threshold=0.90 and record total. (3) Delta = count(0.90) - count(0.92). (4) Sample 20 memory pairs from the delta band (0.90–0.92 similarity). For each pair, manually assess: are they true duplicates (same fact, different phrasing) or false positives (same topic, distinct content)? (5) Compute: estimated false-positive rate in the 0.90–0.92 band, implied correction direction for the threshold.
**Verdict threshold**:
- FAILURE: delta > 200 pairs AND manual sample shows >70% true duplicates in the 0.90–0.92 band (threshold overcorrected -- significant true duplicates are escaping dedup)
- WARNING: delta 20–200 pairs OR manual sample shows mixed (30–70% true duplicates) -- threshold may need fine-tuning but not urgent
- HEALTHY: delta < 20 pairs OR manual sample shows <30% true duplicates in 0.90–0.92 band (raise was correct -- band was false-positive-dominated)

**Derived from**: Q19.5 WARNING -- 0.92 threshold set without empirical calibration; Q19.5 open follow-up: "Run admin /dedup endpoint on current 20,836-memory corpus at both 0.90 and 0.92 to see how many near-duplicates each threshold finds"

---

## Q20.5 [DOMAIN-5] Compound failure: can a single consolidation run produce a memory that is simultaneously split-brain (Qdrant-superseded, Neo4j-active) AND importance-mismatched AND missing from the decay audit?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/core/consolidation.py:262–305`, `src/workers/decay.py:182–191`, `src/storage/postgres_store.py` audit_log schema
**Hypothesis**: Three independent failure modes have been confirmed: Q19.6 (consolidation split-brain at line 282-283), Q18.1 (decay gather partial writes with no audit entry), Q16.4b (importance-inheritance silent failure). The compound scenario is: (1) consolidation succeeds in Qdrant (marks source superseded) but fails in Neo4j at line 283 -- split-brain created; (2) the split-brain source memory, still active in Neo4j, continues to receive importance updates from the next decay run; (3) the decay gather for that user partially fails, writing some Qdrant importance updates but no audit entry; (4) the merged memory's importance was never set via the inheritance path (Q16.4b silently fails). Result: a cluster of 3 memories in permanently inconsistent state across all four tracking dimensions (Qdrant supersedure, Neo4j supersedure, importance values, audit trail). The question is whether the code paths interact in a way that makes this compound scenario reachable in a single consolidation cycle, or whether the timing constraints prevent it.
**Test**: (1) Trace the exact call sequence in a consolidation run that merges cluster [A, B] → C. List every storage write in order and the exception handling at each step. (2) Identify the earliest failure point that produces all three conditions simultaneously (split-brain + importance-mismatch + missing audit). (3) Determine whether the reconcile worker would detect and repair all three conditions or only the supersedure mismatch. (4) Determine whether the compound state is recoverable: if reconcile repairs the split-brain, does the repaired state leave the importance values consistent? (5) Report: is the compound state reachable, detectable, and fully repairable, or does partial repair leave residual inconsistency?
**Verdict threshold**:
- FAILURE: compound state is reachable in a single consolidation cycle AND reconcile partial repair leaves residual importance inconsistency (decay runs on a memory reconcile just re-activated, with wrong importance values)
- WARNING: compound state is reachable but fully repairable by running reconcile followed by decay (two-step manual repair sufficient)
- HEALTHY: compound state is not reachable (timing constraints, write ordering, or exception propagation prevent all three conditions from occurring simultaneously)

**Derived from**: Q19.6 FAILURE (consolidation split-brain), Q18.1 WARNING (decay partial writes), Q16.4b FAILURE (importance-inheritance silent failure); compound scenario is the intersection of all three unresolved failure modes

---

## Q20.6 [DOMAIN-1] Decay run audit gap -- how many decay_run audit entries exist vs expected runs, and does the 694-entry count imply missed decay executions?
**Status**: DONE
**Mode**: observability
**Target**: `audit_log` table -- `action = 'decay_run'` entries vs expected ARQ cron count
**Hypothesis**: Q19.5 audit revealed 694 `decay_run` entries in the audit_log. The ARQ cron schedule runs decay every 6 hours (4x/day). If the system has been running for N days, the expected count is 4N. The 694 entries implies approximately 694/4 = 173 days of operation, or a shorter period with some missed runs. Q18.1 WARNING established that a gather() failure in decay.py skips `_log_decay_audit()`, meaning any decay run that encounters a Qdrant error produces no audit_run entry. The gap between expected and actual decay_run entries is a direct measure of how often decay failures have silently occurred -- each missing entry represents a run where some memories received partial or no decay without any audit trail.
**Test**: (1) Query audit_log: `SELECT DATE(timestamp) as day, COUNT(*) as runs FROM audit_log WHERE action = 'decay_run' GROUP BY day ORDER BY day`. (2) Identify the earliest decay_run entry to establish system start date. (3) Compute expected runs = days_since_start × 4. (4) Compute gap = expected - actual. (5) Identify specific days with <4 runs (partial-day gaps) vs days with 0 runs (complete decay outage). (6) Correlate gap days with any Docker logs evidence of `decay_user_error` events if accessible. Report: total gap count, gap rate, worst-gap day, and whether gaps cluster (suggesting sustained failure periods) or are scattered (suggesting transient errors).
**Verdict threshold**:
- FAILURE: gap > 20% of expected runs (>1 in 5 decay runs silently failed with no audit entry) OR any 7-day window with >50% missing entries (sustained decay outage)
- WARNING: gap 5–20% of expected runs OR scattered missing entries suggesting periodic Qdrant transient errors
- HEALTHY: gap < 5% of expected runs AND no multi-day outage windows (decay is running reliably; small gap explained by maintenance windows or initial deployment period)

**Derived from**: Q18.1 WARNING -- `_log_decay_audit()` skipped when asyncio.gather() raises, so each missing audit_run entry represents a silent partial-write decay run; Q19.5 audit revealed 694 decay_run entries as a data point; quantifying the gap answers whether Q18.1's failure mode is theoretical or actively occurring in production

---

## Wave 21 — Reconcile Convergence Fix, Superseded Garbage Collection, and Residual Split-Brain Mechanics (Q21.x)

*Derived from Wave 20 findings (2026-03-15). Wave 20 established: (1) Q20.5 FAILURE — reconcile introduces new importance mismatches during compound repair because neo4j.mark_superseded zeros importance=0.0, overwriting the prior importance fix; (2) Q20.4 — 72% of Qdrant points are superseded with no garbage collection; (3) Q20.1 — 1,315 importance mismatches with 9 sub-pattern-A entries now explained by Q20.5's compound failure; (4) Q20.6 — processed=0 decay_run entries suggest ghost users. Wave 21 targets the reconcile convergence defect, superseded storage bloat, repair=true risk assessment, and the Qdrant payload structure needed for any future unmark_superseded operation.*

---

## Q21.1 [DOMAIN-5] Does neo4j.mark_superseded's importance=0.0 serve any graph traversal or query purpose, or is it vestigial?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/storage/neo4j_store.py` — `mark_superseded()` method; all Neo4j Cypher queries in `src/storage/neo4j_store.py` and `src/core/retrieval.py` that reference `m.importance`
**Hypothesis**: Q20.5 identified that `neo4j.mark_superseded()` sets `importance=0.0` alongside `superseded_by=<successor_id>`. This zeroing is the root cause of reconcile's two-pass convergence requirement — Step B overwrites Step A's importance repair. If no Neo4j Cypher query uses `m.importance` as a filter or sort condition for superseded memories, then the `importance=0.0` assignment is vestigial (carried over from an earlier design where Neo4j importance was a retrieval signal) and can be safely removed. Removing it would allow reconcile to converge compound failures in a single pass without the minimum fix proposed in Q20.5. If Neo4j queries DO filter on importance (e.g., `WHERE m.importance > 0` as a proxy for "active"), removing the zeroing could surface superseded memories in graph traversals.
**Test**: (1) Read `neo4j_store.py:mark_superseded()` — confirm it sets importance=0.0 and identify the exact Cypher statement. (2) Grep all Cypher queries across `neo4j_store.py` and `retrieval.py` for references to `m.importance` or `importance` in WHERE clauses, ORDER BY, or RETURN. (3) For each query that references importance, determine: does it also filter on `superseded_by IS NULL`? If yes, the importance=0.0 is redundant (the superseded_by filter already excludes the memory). If no, importance=0.0 serves as a secondary exclusion mechanism. (4) Check whether any graph traversal (MATCH path patterns, relationship hops) uses importance as a weight or filter. (5) Report: is importance=0.0 in mark_superseded functionally necessary for any query path, or is it safe to remove?
**Verdict threshold**:
- FAILURE: ≥1 Neo4j query filters on `importance > 0` WITHOUT also filtering on `superseded_by IS NULL` — removing importance=0.0 from mark_superseded would surface superseded memories in active retrieval results
- WARNING: all queries double-filter (importance + superseded_by) but importance=0.0 is documented as intentional in comments or commit history — removal is safe but requires explicit design decision
- HEALTHY: no Neo4j query uses importance as a filter for superseded memories; importance=0.0 is vestigial; removal is safe and fixes reconcile single-pass convergence

**Derived from**: Q20.5 FAILURE — neo4j.mark_superseded zeroing importance=0.0 is the root cause of reconcile two-pass convergence; Q20.5 open follow-up: "Does neo4j.mark_superseded zeroing importance=0.0 serve any purpose for Neo4j graph traversal?"

---

## Q21.2 [DOMAIN-5] Reconcile repair=true risk assessment — what happens to the 1,315 importance mismatches and 9 sub-pattern-A entries when repair runs?
**Status**: DONE
**Mode**: observability
**Target**: `POST /admin/reconcile?repair=true` against live system (192.168.50.19:8200) — dry-run analysis first, then controlled repair
**Hypothesis**: Q20.1 found 1,315 importance mismatches (6.3% of corpus) including 9 sub-pattern-A entries (neo4j=0.0, qdrant=0.3–0.8). Q20.5 explained sub-pattern-A as compound-failure memories awaiting a second reconcile pass. Running repair=true will: (a) fix the 1,306 sub-pattern-B entries by syncing Neo4j importance to Qdrant importance (small drift correction, low risk), (b) fix the 9 sub-pattern-A entries by setting Neo4j importance to the Qdrant value — but Q20.5 showed that if any of these 9 also have a pending superseded_by mismatch, the sequential repair will re-introduce the importance=0.0 overwrite. The risk is: does running repair=true on the current corpus converge fully, or does it create new sub-pattern-A entries from the superseded repair step? A pre-repair reconcile report (repair=false) followed by a post-repair report will measure convergence.
**Test**: (1) Run `POST /admin/reconcile?repair=false` and record baseline: importance_mismatches, superseded_mismatches, neo4j_orphans. (2) Run `POST /admin/reconcile?repair=true` and record: repairs_applied, response time. (3) Immediately run `POST /admin/reconcile?repair=false` again and record: importance_mismatches (should be 0 if single-pass convergence), superseded_mismatches (should be 0). (4) If importance_mismatches > 0 after repair, these are the residual sub-pattern-A entries created by the sequential repair — count them and compare to the 9 pre-repair sub-pattern-A. (5) Run a second repair=true and verify full convergence.
**Verdict threshold**:
- FAILURE: post-repair importance_mismatches > 50 (repair created more mismatches than it fixed — reconcile is divergent)
- WARNING: post-repair importance_mismatches 1–50 (partial convergence — the Q20.5 sequential repair defect is active; second pass needed)
- HEALTHY: post-repair importance_mismatches = 0 AND superseded_mismatches = 0 (single-pass convergence — either no compound failures exist or the repair order happened to converge)

**Derived from**: Q20.1 WARNING — 1,315 importance mismatches including 9 sub-pattern-A; Q20.5 FAILURE — reconcile sequential repair introduces residual mismatches; Q20.1 open follow-up: "Running repair=true would fix the 1,315 mismatches — is there risk?"

---

## Q21.3 [DOMAIN-4] Superseded memory garbage collection — at what age and under what conditions can superseded Qdrant points be safely deleted?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/storage/qdrant.py` (superseded_by payload field usage), `src/core/consolidation.py` (successor chain traversal), `src/workers/reconcile.py` (reconcile references to superseded memories), `src/core/retrieval.py` (any superseded memory access)
**Hypothesis**: Q20.4 found 15,007 superseded memories (72% of 20,889 total Qdrant points) with no garbage collection mechanism. These accumulate indefinitely, increasing reconcile scan time (Q20.2: 209 round trips for full corpus vs ~62 for active-only), storage footprint (~45MB vectors for superseded alone), and admin operation latency. However, superseded memories may still be referenced: (a) the successor chain (memory A superseded_by B superseded_by C) may be traversed for provenance; (b) reconcile needs superseded memories to verify Neo4j consistency; (c) retrieval may use superseded memories for graph context. The question is: which code paths access superseded memories, and is there a safe age threshold (e.g., >30 days since supersedure AND successor is still active) after which a superseded point can be deleted from Qdrant without breaking any code path?
**Test**: (1) Grep all callsites of `scroll_all(include_superseded=True)` — these are the only paths that see superseded memories. (2) For each callsite, determine: does it need the superseded memory's vector, payload, or just its ID? (3) Check whether any retrieval or consolidation path traverses the successor chain (A→B→C) — if yes, deleting A while B references it via superseded_by breaks the chain. (4) Check whether Neo4j stores its own superseded_by edges independently — if yes, Qdrant superseded points are redundant for provenance. (5) Identify the minimum safe deletion criteria: superseded_by is set, successor memory exists and is active, age since supersedure > N days.
**Verdict threshold**:
- FAILURE: superseded memories are accessed by retrieval or consolidation paths beyond reconcile — deletion would break active functionality
- WARNING: superseded memories are only accessed by reconcile and admin endpoints, but successor chain traversal exists in Neo4j that cross-references Qdrant IDs — deletion requires Neo4j cleanup too
- HEALTHY: superseded memories are only accessed by reconcile (which can skip deleted points) and admin dedup (which already filters them out) — safe to delete after successor validation with no functional impact

**Derived from**: Q20.4 HEALTHY (primary) with Medium secondary finding — 72% superseded ratio with no garbage collection; Q20.2 HEALTHY — reconcile fetches 3.5x more points than needed due to include_superseded=True over a 72% superseded corpus

---

## Q21.4 [DOMAIN-5] Qdrant payload structure for superseded_by — can superseded_by be unset via direct payload update, and what is the correct API call?
**Status**: DONE
**Mode**: benchmark
**Target**: Qdrant HTTP API (`PUT /collections/{name}/points/payload`), `src/storage/qdrant.py` — mark_superseded() payload structure, Qdrant documentation for payload field deletion
**Hypothesis**: Q19.6 noted that `qdrant.unmark_superseded()` does not exist in the codebase. The reconcile worker syncs Qdrant→Neo4j (one direction only). If a memory is incorrectly superseded in Qdrant (false positive from consolidation), there is no programmatic way to un-supersede it — the memory is permanently removed from search results. The Qdrant REST API supports `DELETE /collections/{name}/points/payload` to remove specific payload keys, and `PUT /collections/{name}/points/payload` to overwrite them. The question is: (a) what is the exact payload structure for superseded_by in Recall's Qdrant collection (string UUID? dict? nested?), (b) can it be set to null/removed via the Qdrant API to restore a memory to active status, and (c) does removing superseded_by from Qdrant also require removing `invalid_at` (set by mark_superseded) to fully restore the memory?
**Test**: (1) Read `qdrant.py:mark_superseded()` — extract the exact payload update call and field names. (2) Query Qdrant HTTP API for one known superseded memory: `GET /collections/recall_memories/points/{id}` — inspect the full payload structure for superseded_by and invalid_at fields. (3) Test un-superseding via `DELETE /collections/recall_memories/points/payload` with `{"keys": ["superseded_by", "invalid_at"]}` on a single test memory. (4) Verify the memory reappears in `scroll_all(include_superseded=False)` results. (5) Report: the exact API call needed for un-supersedure, and whether this is safe (no side effects on Neo4j or audit_log).
**Verdict threshold**:
- FAILURE: superseded_by is stored as a nested structure or index that cannot be removed via payload delete API — un-supersedure requires Qdrant point re-insertion (destructive)
- WARNING: superseded_by can be removed via payload delete, but invalid_at or other fields also need cleanup — multi-step un-supersedure with risk of partial state
- HEALTHY: superseded_by and invalid_at can be atomically removed via a single payload delete call, and the memory immediately reappears in active scroll results — un-supersedure is a safe, reversible operation

**Derived from**: Q19.6 FAILURE — "qdrant.unmark_superseded() does not exist"; Q20.5 FAILURE — compound failures leave memories incorrectly superseded; Q20.1 WARNING — reconcile is one-directional (Qdrant→Neo4j), cannot reverse an incorrect Qdrant supersedure

---

## Q21.5 [DOMAIN-1] Ghost users in decay — what user_ids produce processed=0 decay_run entries, and do they have any memories in Qdrant?
**Status**: DONE
**Mode**: observability
**Target**: PostgreSQL `audit_log` (decay_run entries with processed=0), Qdrant `recall_memories` collection (per-user memory counts)
**Hypothesis**: Q20.6 noted that some `decay_run` entries have `processed=0`, suggesting the decay worker iterated over user_ids returned by `qdrant.get_distinct_user_ids()` that have no active memories. These could be: (a) users whose memories were all superseded (active count=0, but superseded memories still have the user_id in their payload), (b) users deleted from the auth system but still present in Qdrant metadata, or (c) a race condition where memories were deleted between get_distinct_user_ids() and scroll_memories_for_decay(). If case (a), the ghost user count will grow as more memories are superseded — each consolidation cycle can reduce a user's active count to 0. The decay worker wastes one audit_log row and one Qdrant scroll per ghost user per run (4x/day × N ghost users). At 9 users this is negligible; at 100+ users it becomes measurable overhead.
**Test**: (1) Query audit_log: `SELECT metadata->>'user_id' as uid, COUNT(*) as zero_runs FROM audit_log WHERE action = 'decay_run' AND (metadata->>'processed')::int = 0 GROUP BY uid ORDER BY zero_runs DESC`. (2) For each ghost user_id, query Qdrant: scroll with filter `user_id = <uid>` and `superseded_by IS NULL` — count active memories. (3) Also scroll with `user_id = <uid>` without the superseded filter — count total (active + superseded). (4) Report: how many ghost users exist, whether they have superseded-only memories, and the per-run overhead (scroll calls + audit writes per ghost user).
**Verdict threshold**:
- FAILURE: >20% of user_ids are ghost users with 0 active memories AND the per-ghost overhead is measurable (>100ms per ghost per decay run)
- WARNING: ghost users exist (1–20% of user_ids) but overhead is negligible; or ghost users are a known artifact of the test/development user lifecycle
- HEALTHY: zero ghost users (all user_ids returned by get_distinct_user_ids have ≥1 active memory) OR processed=0 entries are explained by timing (memories created between get_distinct and scroll)

**Derived from**: Q20.6 HEALTHY — secondary finding: "processed=0 entries suggest some users have zero active memories at decay time. Are these ghost users or recently created users with no memories yet?"

---

## Q21.6 [DOMAIN-5] Reconcile audit trail — does adding an audit_log entry for each reconcile run enable the last-run-date query that Q20.1 could not answer?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/workers/reconcile.py` (run_reconcile function), `src/api/routes/ops.py` (reconcile_stores endpoint), `src/storage/postgres_store.py` (audit_log_entry method signature)
**Hypothesis**: Q20.1 found that reconcile has zero audit trail — `SELECT COUNT(*) FROM audit_log WHERE action = 'reconcile'` returns 0. The reconcile worker logs only via structlog, making the last run date unverifiable from the database. The system already has a well-established audit_log pattern (used by decay_run, consolidate, dedup, etc.) with `action`, `memory_id`, `metadata` columns. Adding a single `audit_log_entry(action='reconcile', memory_id='system', metadata={...})` call at the end of both `run_reconcile()` and `reconcile_stores()` would close this observability gap. The question is: (a) what is the exact audit_log_entry function signature and does it support arbitrary metadata dicts, (b) is the postgres_store dependency already available in the reconcile worker context (or would it need to be plumbed in), and (c) what metadata fields should the reconcile audit entry carry to be useful (importance_mismatches, superseded_mismatches, repairs_applied, duration_ms)?
**Test**: (1) Read `postgres_store.py` — find the `audit_log_entry` or equivalent method. Extract its signature: what parameters does it accept? Does it support a `metadata` dict? (2) Read `reconcile.py:run_reconcile()` — is `postgres_store` available in scope, or only `qdrant` and `neo4j`? (3) Read `ops.py:reconcile_stores()` — same question for the admin endpoint. (4) Identify the minimum change: how many lines are needed to add a reconcile audit entry in both paths? (5) Report: feasibility, LOC estimate, and recommended metadata schema for the audit entry.
**Verdict threshold**:
- FAILURE: postgres_store is not available in the reconcile worker context AND plumbing it in requires changes to the ARQ worker setup, dependency injection, and >20 LOC — audit trail requires architectural change
- WARNING: postgres_store is available but audit_log_entry does not support metadata dicts (only fixed fields) — audit entry possible but without the repair details that make it useful
- HEALTHY: postgres_store is available in both reconcile paths, audit_log_entry accepts metadata dict, and the change is ≤10 LOC per path — reconcile audit trail is a trivial addition

**Derived from**: Q20.1 WARNING — "Reconcile has zero audit observability: neither run_reconcile() nor reconcile_stores() writes to audit_log"; Q20.1 secondary finding B: "a critical repair operation is invisible — same gap as Q16.1 for dedup"

---

## Wave 22 — Ghost User Confirmation, Primary User Double-Decay, GC Readiness, and Reconcile Observability Improvements (Q22.x)

*Derived from Wave 21 findings (2026-03-15). Wave 21 established: (1) Q21.1 HEALTHY — importance=0.0 in mark_superseded is vestigial; removal fixes reconcile single-pass convergence; (2) Q21.2 HEALTHY — repair=true converges in one pass on current corpus (1,315→0 mismatches); weekly cron resolved 99.8% before manual repair; (3) Q21.3 WARNING — causal_extractor accesses superseded memories during live store; GC safe at 30-day threshold with simultaneous Neo4j cleanup; (4) Q21.4 HEALTHY — qdrant.unmark_superseded is a 4-line addition; neo4j side needs new helper; (5) Q21.5 WARNING — 70% ghost users in decay; primary user double-processed; audit lacks user_id; (6) Q21.6 HEALTHY — reconcile audit trail is 9 LOC across 2 files. Wave 22 follows up on the open threads: ghost user identity, primary user double-decay root cause, GC age threshold readiness, and reconcile response format.*

---

## Q22.1 [DOMAIN-1] Primary user double-decay root cause — is the primary user's corpus split across user_id=None AND user_id=N?
**Status**: DONE
**Mode**: observability
**Target**: Qdrant `recall_memories` collection — `get_distinct_user_ids()` output + per-user active memory counts
**Hypothesis**: Q21.5 showed the primary user is processed TWICE per decay slot (e.g., 5693 + 5693 in the 18:15 slot). The leading explanation is a user_id split: memories stored before user tracking was added have `user_id=None` (processed in the system/null run), while memories stored after have `user_id=N` (processed in the named-user run). If both runs produce ~5,700 processed counts, either: (a) both batches contain ~5,700 active memories (total ~11,400 — but only ~5,900 active memories exist corpus-wide, so both runs process overlapping or identical sets), or (b) the null-user run processes ALL active memories (no user_id filter) and the named-user run processes the same memories again (user_id=N matches most of them). Case (b) means the decay factor is applied twice per slot = `importance * 0.96^2 ≈ 0.9216` instead of `0.96` — a 4% overdecay per run compounding over time.
**Test**: (1) Call `get_distinct_user_ids()` or equivalent Qdrant query to list all unique user_ids in the collection (including NULL). (2) For each user_id (including NULL), count active memories: `scroll with filter user_id=X AND superseded_by IS NULL`. (3) Confirm whether NULL-user and named-user counts sum to more than total active corpus (indicating overlap/double-counting). (4) Read `decay.py:run_decay_all_users()` — how does it handle the NULL user case? Does `scroll_memories_for_decay(user_id=None)` apply a user_id filter or skip it? (5) Report: is the primary user's corpus split, and does the decay worker process the same memories twice?
**Verdict threshold**:
- FAILURE: NULL-user decay run processes ALL active memories (no user_id filter) AND named-user run re-processes the same memories — confirmed double-decay on every run (importance error compounds at 0.96^2 per slot)
- WARNING: user_id split exists but overlap is partial (<50% of memories appear in both runs) — overdecay affects a subset
- HEALTHY: no overlap — NULL-user and named-user counts sum to exactly the total active corpus, or decay correctly skips NULL users

**Derived from**: Q21.5 WARNING — "Primary user processed twice per slot (5693, 5693)"; Q21.5 open follow-up: "is their corpus split across user_id=None AND user_id=N?"

---

## Q22.2 [DOMAIN-1] Ghost user identity — do the 7 ghost user_ids have any memories (active or superseded) in Qdrant?
**Status**: DONE
**Mode**: observability
**Target**: Qdrant `recall_memories` collection — per-ghost-user memory counts (active + superseded)
**Hypothesis**: Q21.5 identified 7 ghost user_ids producing processed=0 decay_run entries every slot. These users are returned by `get_distinct_user_ids()` because their user_id exists in at least one Qdrant point's payload. The question is whether these are: (a) "exhausted" users whose ALL memories have been superseded (they had real memories that were consolidated away — their user_id persists only in superseded payloads), (b) test/development accounts that stored a few memories and then went inactive, or (c) user_ids that somehow exist in metadata without any associated memories (data artifact). Category (a) confirms that ghost user count will grow proportionally with supersedure rate. Category (b) suggests a one-time cleanup. Category (c) would be a data integrity issue.
**Test**: (1) Determine the 7 ghost user_ids — either by calling `get_distinct_user_ids()` and then querying active memory count per user, or by querying Qdrant directly for all distinct user_id values. (2) For each ghost user_id: scroll with filter `user_id = X AND superseded_by IS NULL` (active count). (3) Scroll with filter `user_id = X` without superseded filter (total count = active + superseded). (4) Report per ghost user: active count, superseded count, total. (5) Classify: exhausted (active=0, superseded>0), test account (active=0, superseded=0 but user_id in some payload), or data artifact.
**Verdict threshold**:
- FAILURE: ≥1 ghost user_id has 0 total memories (no active, no superseded) — data integrity issue; user_id exists in metadata with no corresponding point
- WARNING: all ghost users are "exhausted" (active=0, superseded>0) — confirms ghost count grows with supersedure rate; get_distinct_user_ids fix from Q21.5 is the correct mitigation
- HEALTHY: all ghost users are test accounts with small total counts (<10 memories each) — one-time artifact, not a growing problem

**Derived from**: Q21.5 WARNING — "Do the 7 ghost user_ids have any memories at all (active or superseded) in Qdrant?"

---

## Q22.3 [DOMAIN-4] GC age threshold readiness — have any superseded memories crossed the 30-day invalid_at threshold yet?
**Status**: DONE
**Mode**: observability
**Target**: Qdrant `recall_memories` collection — superseded points with `invalid_at` payload field
**Hypothesis**: Q21.3 established a 30-day GC threshold for superseded memory deletion. The deployment started 2026-02-21 (23 days before 2026-03-15). If consolidation started within the first 3 days, the earliest superseded memories have `invalid_at` dates around 2026-02-24 — which is now 19 days ago (below the 30-day threshold). The 30-day threshold becomes actionable around 2026-03-24. However, if any superseded memories have `invalid_at` dates earlier than 2026-02-13 (perhaps from pre-deployment test data or data migration), GC could begin immediately. This question measures the actual `invalid_at` distribution to determine when GC first becomes actionable and how large the initial deletable batch will be.
**Test**: (1) Scroll Qdrant for superseded memories (filter: `superseded_by IS NOT NULL`), extracting `invalid_at` from each payload. (2) Parse `invalid_at` timestamps and compute age = now - invalid_at. (3) Bucket the age distribution: <7 days, 7-14 days, 14-21 days, 21-30 days, >30 days. (4) Report: how many superseded memories are currently ≥30 days old (immediately deletable), how many will cross the threshold in the next 7 days, and what is the earliest `invalid_at` in the corpus. (5) If any are ≥30 days old, verify their successor memory still exists and is active (GC criterion #3 from Q21.3).
**Verdict threshold**:
- FAILURE: >1,000 superseded memories are ≥30 days old but successor verification fails for >10% (dangling successor chains — GC would orphan references)
- WARNING: 0 superseded memories are ≥30 days old yet (GC not yet actionable; first batch expected in ~7 days based on deployment date math)
- HEALTHY: ≥1 superseded memories are ≥30 days old AND successor verification passes for >90% — GC is immediately actionable for a measurable batch

**Derived from**: Q21.3 WARNING — "Deployment started 2026-02-21 = 22 days ago [...] A 14-day threshold would make ~8,000–10,000 points immediately deletable"; this question resolves the actual invalid_at distribution

---

## Q22.4 [DOMAIN-5] Reconcile response format — does ops.py reconcile_stores() have access to all variable names needed for the audit entry?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/api/routes/ops.py` — `reconcile_stores()` function body; variable scoping for `qdrant_total`, `neo4j_total`, `importance_mismatches`, `superseded_mismatches`, `repairs_applied`
**Hypothesis**: Q21.6 confirmed that `log_audit()` is callable from ops.py with a details dict. The recommended audit entry schema uses variable names like `qdrant_total`, `neo4j_total`, `importance_mismatches`, `superseded_mismatches`, `repairs_applied`. However, Q21.6 did not verify that these exact variable names exist in the local scope of `reconcile_stores()` at the point where the audit call would be inserted. The admin endpoint may compute these values differently from the ARQ cron (e.g., storing counts as ints vs lists, using different variable names, or computing them inline in the response dict). If the variable names don't match, the audit insertion requires additional extraction/renaming logic beyond the 4-line estimate.
**Test**: (1) Read `ops.py:reconcile_stores()` — identify every local variable or dict key that corresponds to the audit schema fields. (2) Determine the exact point in the function where the audit call should be inserted (after repairs but before response return). (3) List which audit schema fields are directly available as local variables at that point and which need extraction from intermediate data structures. (4) Report: is the 4-line audit insertion accurate, or does variable scoping require additional logic?
**Verdict threshold**:
- FAILURE: ≥3 audit schema fields require multi-line extraction from nested data structures — the "4 lines" estimate is off by >2x
- WARNING: 1-2 fields need extraction but the total change is still ≤8 LOC — minor underestimate
- HEALTHY: all audit schema fields are directly available as local variables at the insertion point — the 4-line estimate is accurate

**Derived from**: Q21.6 HEALTHY — "Does the admin HTTP endpoint (ops.py reconcile_stores) actually have access to all the variable names needed?"

---

## Q22.5 [DOMAIN-5] Neo4j unmark_superseded — does any existing neo4j_store method already support REMOVE property operations?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/storage/neo4j_store.py` — all methods that modify Memory node properties; Cypher patterns for `REMOVE` or property deletion
**Hypothesis**: Q21.4 proposed a `neo4j.unmark_superseded(memory_id, importance)` method requiring `REMOVE m.superseded_by, m.invalid_at` Cypher. The Neo4j Cypher `REMOVE` keyword deletes a property from a node (distinct from `SET m.prop = null` which sets it to null). The question is: (a) does any existing method in `neo4j_store.py` use `REMOVE` in a Cypher query (establishing the pattern is already in use), (b) does `mark_superseded`'s test suite cover the reverse case (if so, the new method can be tested symmetrically), and (c) would `SET m.superseded_by = null, m.invalid_at = null` work equivalently to `REMOVE` for Recall's reconcile logic (which uses `superseded_by IS NULL` checks)?
**Test**: (1) Grep `neo4j_store.py` for `REMOVE` in any Cypher query string. (2) Grep for `= null` or `= NULL` in any SET clause. (3) Read the `mark_superseded` test (if one exists in `tests/storage/test_neo4j.py` or similar) — does it verify the properties are set and could the test be mirrored for unmark? (4) Read `reconcile.py` — does the superseded_by mismatch check use `IS NULL` or `is None` or `== ""` — which determines whether `REMOVE` vs `SET null` is the correct approach. (5) Report: is the REMOVE pattern already established, and what is the exact Cypher needed for unmark_superseded?
**Verdict threshold**:
- FAILURE: neo4j_store.py uses a custom property deletion wrapper or ORM that makes raw REMOVE Cypher incompatible — architectural mismatch requiring >20 LOC
- WARNING: no REMOVE pattern exists in neo4j_store.py but SET null would work equivalently — 8-line method addition with new Cypher pattern
- HEALTHY: REMOVE or SET null pattern already exists in neo4j_store.py — unmark_superseded mirrors an established pattern; 8-line addition with symmetric test

**Derived from**: Q21.4 HEALTHY — "Neo4j side requires a corresponding neo4j.unmark_superseded() helper"; Q21.4 open follow-up: "Is there any existing neo4j_store method close to the needed REMOVE m.superseded_by?"

---

## Q22.6 [DOMAIN-5] Reconcile repair response — post-repair state visibility for operators
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/api/routes/ops.py` — `reconcile_stores()` response construction after repair=true
**Hypothesis**: Q21.2 found that the repair=true response shows pre-repair scan state (`importance_mismatches: 2` in the response even though repairs were applied and post-repair state is 0 mismatches). An operator reading this response would think repair failed. The fix is to either: (a) run a second scan after repairs and return the post-repair counts alongside the pre-repair counts, or (b) add explicit `pre_repair_mismatches` and `post_repair_mismatches` fields to the response dict. The question is: what is the current response construction pattern in `reconcile_stores()`, and how many lines are needed to add post-repair visibility?
**Test**: (1) Read `ops.py:reconcile_stores()` — identify where the response dict is constructed. (2) Determine whether the response is built incrementally during scanning (pre-repair values baked in) or built at the end from accumulated results (easier to augment). (3) Estimate LOC needed for option (a) — re-run the scan loop after repair and include both counts. (4) Estimate LOC needed for option (b) — rename existing fields and add post-repair fields without re-scanning. (5) Report: which option is simpler, LOC estimate, and whether re-scanning has performance concerns (double reconcile scan time).
**Verdict threshold**:
- FAILURE: response is constructed inline during the scan loop with no clear separation between scan and repair — adding post-repair visibility requires refactoring the scan/repair separation (>30 LOC)
- WARNING: response is built at the end but re-scanning doubles the reconcile time (2x Qdrant+Neo4j scans) — option (b) is preferred but requires careful field renaming
- HEALTHY: response is built from variables that can be captured pre-repair and post-repair with ≤10 LOC — either option is a trivial addition

**Derived from**: Q21.2 HEALTHY — "repair=true response shows pre-repair scan state even for repair=true — misleading but functionally benign"; Q21.2 open follow-up: "Should the reconcile endpoint run a second scan after applying repairs and return the post-repair counts?"

---

## Q22.7 [DOMAIN-1] Decay user_id audit gap — after adding user_id to the decay audit INSERT, can existing processed=0 entries be backfilled?
**Status**: DONE
**Mode**: static-analysis
**Target**: `src/workers/decay.py` — `_log_decay_audit()` function; PostgreSQL `audit_log` table schema
**Hypothesis**: Q21.5 identified that `_log_decay_audit()` does not populate the `user_id` column, making ghost user identification impossible from the audit log. The fix is to pass `user_id` to the INSERT. However, there are ~28 processed=0 entries per day already in the audit_log (7 ghost users x 4 runs/day). These historical entries have `user_id=NULL`. The question is: (a) does `_log_decay_audit()` receive the user_id as a parameter or only the aggregate stats dict, (b) does the `audit_log` table have a `user_id` column (or is it embedded in the `details` JSON), and (c) can historical processed=0 entries be retroactively identified by correlating timestamps with `get_distinct_user_ids()` output ordering (if the decay loop processes users in a deterministic order)?
**Test**: (1) Read `decay.py:_log_decay_audit()` — what parameters does it accept? Does it have access to the current user_id? (2) Read the `audit_log` schema (via postgres_store.py or migration files) — does a `user_id` column exist? (3) Read `decay.py:run_decay_all_users()` — is _log_decay_audit called inside the per-user loop (user_id available) or after the loop (user_id lost)? (4) If _log_decay_audit is called after the loop, the fix requires moving the audit call inside the loop OR passing user_id as a parameter. Estimate LOC. (5) Report: feasibility, LOC, and whether historical backfill is possible.
**Verdict threshold**:
- FAILURE: _log_decay_audit is called once per cron invocation (after all users processed) with aggregate stats only — per-user audit requires restructuring the decay loop (>20 LOC change)
- WARNING: _log_decay_audit is called per-user but user_id is not passed — adding the parameter is straightforward but historical entries cannot be backfilled
- HEALTHY: _log_decay_audit is called per-user AND already receives user_id (or can trivially accept it) — fix is ≤5 LOC; historical entries identifiable by deterministic processing order

**Derived from**: Q21.5 WARNING — "audit log lacks user_id field making ghost identity unresolvable without Qdrant direct query"; Q21.5 fix recommendation: "add user_id to the audit entry INSERT"

---

## Q22.8 [DOMAIN-4] Causal extractor superseded access — what fraction of causal edges are created from superseded vs active candidates?
**Status**: DONE
**Mode**: observability
**Target**: `src/core/causal_extractor.py:128` — the `include_superseded=True` search call; Neo4j CAUSAL_PRECEDES edges
**Hypothesis**: Q21.3 identified `causal_extractor.py:128` as the only live production path accessing superseded memories. The GC safety argument rests on the claim that "memories superseded ≥30 days ago are unlikely to be semantically relevant to current store operations." This claim is untested. If a significant fraction (>20%) of CAUSAL_PRECEDES edges in Neo4j link to superseded source memories, then GC at 30 days would retroactively orphan those edges (the source node would be deleted from Qdrant but the Neo4j edge would remain pointing to a non-existent vector). If the fraction is low (<5%), the 30-day threshold is empirically validated as safe. A direct Neo4j query counting CAUSAL_PRECEDES edges where the source memory is superseded would answer this.
**Test**: (1) Query Neo4j: `MATCH (a:Memory)-[:CAUSAL_PRECEDES]->(b:Memory) WHERE a.superseded_by IS NOT NULL RETURN count(*) AS superseded_source_edges`. (2) Query Neo4j: `MATCH (a:Memory)-[:CAUSAL_PRECEDES]->(b:Memory) RETURN count(*) AS total_causal_edges`. (3) Compute fraction = superseded_source_edges / total_causal_edges. (4) For superseded source edges, check: is the superseded source's successor (a.superseded_by) ALSO linked via CAUSAL_PRECEDES to the same target? If yes, the causal relationship is already captured via the successor — edge orphaning has no information loss. (5) Report: fraction, successor coverage rate, and whether 30-day GC would cause causal edge orphaning with information loss.
**Verdict threshold**:
- FAILURE: >20% of CAUSAL_PRECEDES edges have superseded sources AND <50% of those have successor-equivalent edges — GC would cause significant causal knowledge loss
- WARNING: 5-20% of edges have superseded sources OR successor coverage is 50-90% — GC safe but some causal edges would be orphaned; Neo4j DETACH DELETE handles this but information is lost
- HEALTHY: <5% of edges have superseded sources OR >90% successor coverage — 30-day GC threshold empirically validated as safe for causal knowledge preservation

**Derived from**: Q21.3 WARNING — "causal_extractor queries superseded memories with include_superseded=True during every new memory store"; Q21.3 GC safety argument is time-bounded but not empirically measured

## Q22.9 [DOMAIN-5] Corpus state anomaly — what event occurred between 2026-03-14T18:15 and 2026-03-15T00:16 UTC causing 521 importance mismatches and primary user (user_id=2) to disappear from the decay loop?
**Status**: DONE
**Mode**: observability
**Target**: audit_log (all action types), reconcile results, decay slot data for 2026-03-15
**Hypothesis**: Between the 18:15 slot (10 decay entries with primary user ~5693) and the 00:16 slot (8 entries, no primary user), a significant corpus event occurred: (a) importance mismatches rose from 0 (post-Q21.2 repair) to 521, (b) primary user's decay loop entries dropped from [5693, 5693] to [absent], (c) an isolated single-entry decay slot at 00:01 fired 14 minutes early with processed=5749. The most likely trigger is a large consolidation wave that superseded most or all of the primary user's ~5,749 active memories, creating 507 new superseded entries (confirmed in Q22.3 audit data for 0–2 day bucket) and causing the importance mismatch count to spike (newly-consolidated memories have Qdrant importance unchanged but Neo4j importance set to 0.0 by mark_superseded — this is the exact neo4j.mark_superseded() vestigial importance=0.0 bug from Q21.1). The question is: what triggered the consolidation wave, what is the current active corpus size for user_id=2, and how many of the 521 mismatches are attributable to this event?
**Test**: (1) Query audit log for consolidate events between 2026-03-14T18:00 and 2026-03-15T01:00 UTC — count them and note timestamps. (2) Run reconcile dry-run to get current totals and mismatch count. (3) Check audit log for any `session_end`, `store`, or other bulk operations in the anomaly window. (4) Read Neo4j or Qdrant stats for user_id=2 current active memory count (if accessible via admin API). (5) Hypothesis validation: if the 521 mismatches are neo4j=0.0/qdrant>0 pairs from newly-superseded memories, this is the Q21.1 vestigial importance=0.0 bug manifesting at scale.
**Verdict threshold**:
- FAILURE: the corpus anomaly caused data loss — active memories were deleted (not superseded), reducing the total corpus size below the expected baseline
- WARNING: large consolidation wave occurred, 521 mismatches are all attributable to neo4j.mark_superseded() vestigial importance=0.0 bug (Q21.1) — confirms Q21.1 is a recurring production issue, not a theoretical concern
- HEALTHY: the 521 mismatches have a different root cause unrelated to mark_superseded(); primary user data is intact as a new consolidated form

**Derived from**: Q22.2 WARNING — "521 importance mismatches re-appeared, primary user user_id=2 absent from decay loop"; Q21.1 HEALTHY — "importance=0.0 in neo4j.mark_superseded is vestigial but creates mismatch pattern on every supersedure event"

---

## Wave 23 Questions

---

## Q23.1 [DOMAIN-1] Double-decay damage quantification — what is the cumulative importance loss from the double-decay bug, and which memories have dropped below the functional threshold?
**Status**: DONE
**Mode**: observability
**Target**: Qdrant active memories — importance distribution snapshot, comparison to expected decay trajectory
**Hypothesis**: The Q22.1 double-decay bug applies 0.9216/slot instead of 0.96/slot. At 96 slots/day, the actual daily factor is 0.9216^96 vs intended 0.96^96. A memory stored 7 days ago with initial importance 0.8 should be meaningfully above 0.05 (active threshold) under single-decay; under double-decay it could be near zero. The question is: (a) what is the current importance distribution, (b) how many memories are below 0.05 that would be above it under single-decay, (c) how long has the double-decay been running?
**Test**: (1) Query active memory importance distribution via admin API or stats endpoint. (2) Identify earliest active memory created_at to bound how long double-decay has been running. (3) Compare observed importance for memories of known age to expected value under single-decay formula. (4) Count memories with importance < 0.05 that have created_at < 7 days ago. (5) If decay_rate config accessible, compute expected vs actual importance at multiple age points.
**Verdict threshold**:
- FAILURE: >20% of memories stored >3 days ago are at importance < 0.05; measured importance is <50% of expected single-decay value at any age point >= 3 days
- WARNING: 10-20% of memories aged 3-7 days are below 0.05; measured importance 50-80% of expected
- HEALTHY: <10% of 3-7 day memories below 0.05; measured importance within 80% of expected single-decay value

**Derived from**: Q22.1 FAILURE — double-decay confirmed at 0.9216/slot vs 0.96/slot; exponential divergence over days not yet quantified

---

## Q23.2 [DOMAIN-1] ARQ restart slot structure — why did the decay slot structure change from 10 to 8 to 2 entries across the Q22.9 anomaly window, and is the current 2-entry structure still double-decaying?
**Status**: DONE
**Mode**: observability
**Target**: audit_log decay_run entries (most recent 48 hours), decay.py ARQ cron registration
**Hypothesis**: Q22.9 documented three distinct slot structures: (1) pre-outage: 10 entries [system, 7xghost, user_id=2, system], (2) post-restart 00:16 and 06:15: 8 entries [7xghost, user_id=2] no system run, (3) post-06:30: ~2 entries [system, system] system-only. If the current slot is 2-entry double-system, the Q22.1 bug is still active. If it is 1-entry, the restart may have self-corrected. Understanding the current structure is critical to knowing whether Q22.1 is still active.
**Test**: (1) Query /admin/audit?action=decay_run&limit=50 for most recent 48h. (2) Count entries per 15-minute slot (group by floor(timestamp, 15min)). (3) Identify which user_ids appear as processed values. (4) Check decay.py for run_decay_all_users() vs run_decay_for_user() entrypoints and their ARQ cron registrations. (5) Determine if current slot structure shows double-decay (two entries with proc=full_corpus) or single-decay.
**Verdict threshold**:
- FAILURE: Current slots still show double-decay (proc=active_corpus in both entries per slot); Q22.1 bug still active
- WARNING: Slot structure changed but new pattern has missing runs (some users not being decayed)
- HEALTHY: Current slot structure shows single-decay per memory per slot; restart changed the behavior; Q22.1 bug is latent

**Derived from**: Q22.9 WARNING — "slot structure changed 10 to 8 to 2 entries across 12-hour window"; Q22.1 FAILURE — double-decay mechanism confirmed

---

## Q23.3 [DOMAIN-1] User_id type consistency — are any Qdrant payloads storing user_id as float instead of int, causing count_user_memories() to return 0 for users who have memories?
**Status**: DONE
**Mode**: static code analysis + observability
**Target**: memory.py, qdrant.py store paths — user_id type handling; Qdrant payload inspection for user_id field type
**Hypothesis**: Q22.9 identified an unresolved anomaly: count_user_memories(2) returned 0 while get_distinct_user_ids() was returning user_id=2 in the decay loop. Two explanations: (a) memories have user_id=2.0 (float) stored in Qdrant — get_distinct_user_ids() converts via int(uid) so 2 appears, but MatchValue(value=2) (int exact match) returns 0 results; (b) memories were already superseded at time of API check. If float storage is the cause, this is a systematic type inconsistency affecting all user-scoped queries for any user whose memories were written via a float-producing path.
**Test**: (1) Query /admin/users/2/export (includes_superseded=True) — if 0 results, user_id=2 memories are either gone or type-mismatched. (2) Check memory.py and observer.py store paths — is user_id typed as int, float, or untyped when passed to qdrant.store()? (3) Read qdrant.py _user_conditions() — MatchValue(value=user_id) where user_id is int; check if any write path can produce float. (4) Check if Pydantic Memory model has user_id as int or Optional[int] — does JSON serialization/deserialization coerce to float? (5) If admin API allows raw payload inspection, check a known user memory for user_id field type.
**Verdict threshold**:
- FAILURE: user_id stored as float in Qdrant for some write path; MatchValue(value=int) systematically misses float-stored memories; all user-scoped queries undercount
- WARNING: Inconsistency exists for specific write path (observer vs API store); partial scoping failures
- HEALTHY: user_id consistently stored as int; count_user_memories(2)=0 explained by consolidation supersedure, not type mismatch

**Derived from**: Q22.9 WARNING — "count_user_memories(2)=0 while proc=2 in decay loop — unresolved: float vs int user_id OR genuine supersedure"

---

## Q23.4 [DOMAIN-5] Reconcile mismatch growth rate — at what rate are new importance mismatches accumulating per day after the Q22.9 baseline of 521?
**Status**: DONE
**Mode**: observability
**Target**: POST /admin/reconcile?dry_run=True current count, audit_log consolidate entries last 7 days
**Hypothesis**: Every supersedure event creates exactly 1 importance mismatch (Q22.9 confirmed). Q21.3 estimated ~600 new superseded/day from continuous consolidation. If that rate holds, the mismatch count should be growing by ~600/day from the 521 baseline. A current dry-run reconcile should show a substantially higher count, and the delta divided by days since 2026-03-15 should match the daily consolidation supersedure rate. This validates Q21.3 estimate and provides a concrete urgency metric for the Q21.1 one-line fix.
**Test**: (1) Call POST /admin/reconcile?dry_run=True, record importance_mismatches count. (2) Compute delta from 521 (Q22.9 baseline, 2026-03-15T07:09). (3) Count audit consolidate entries in last 7 days via /admin/audit?action=consolidate&limit=1000, group by day. (4) Compare mismatches/day to consolidations/day x avg_sources_per_consolidation. (5) If Q21.1 fix deployed, confirm count has stopped growing (expected: delta = 0).
**Verdict threshold**:
- FAILURE: Mismatch count has grown by >1000 from baseline (>600/day confirmed); growth rate is accelerating or above Q21.3 estimate
- WARNING: Count growing at 100-600/day; steady accumulation; consistent with Q21.3 estimate
- HEALTHY: Count <= 521 (Q21.1 fix deployed, growth stopped) OR growth rate <50/day (consolidation rate much lower than Q21.3 estimated)

**Derived from**: Q22.9 WARNING — "521 mismatches = entire historical Q21.1 accumulation; every supersedure = 1 permanent mismatch"; Q21.3 WARNING — "~600 new superseded/day"

---

## Q23.5 [DOMAIN-4] Consolidation worker rate and backoff — does the continuously-running consolidation worker have any rate limit or natural termination condition?
**Status**: DONE
**Mode**: static code analysis + observability
**Target**: consolidation.py (worker loop and exit conditions), ARQ cron registration, audit_log consolidate entries per hour
**Hypothesis**: Q22.9 states consolidation "runs continuously." If no rate limit exists, the worker consumes similar memory pairs indefinitely. Combined with double-decay (Q22.1), consolidation output memories (user_id=None) are processed by the system run but user originals were also being double-decayed — the effective decay rate for user content compounds further. The question is whether consolidation has a per-run limit, similarity floor, or naturally terminates when no similar pairs remain above threshold.
**Test**: (1) Read consolidation.py for sleep calls, loop bounds, per-batch limits, or termination conditions. (2) Check ARQ cron registration — scheduled (fixed interval) or self-rescheduling (continuous)? (3) Count consolidate audit entries per hour in last 24h — is the rate constant or does it slow as the corpus becomes more consolidated? (4) Check the similarity threshold used in consolidation — same as dedup 0.92 or different? (5) Measure: does consolidation rate drop toward zero or remain constant?
**Verdict threshold**:
- FAILURE: No rate limit or loop bound; worker cycles indefinitely even when no new pairs exist; no audit entry for batch-complete state; rate is unbounded
- WARNING: Worker has per-run limit but re-schedules immediately with no backoff; effective rate is bounded but aggressively continuous
- HEALTHY: Worker runs on fixed schedule, has per-run limit, or naturally terminates when similarity search returns no results; rate is controlled and predictable

**Derived from**: Q22.9 WARNING — "consolidation ran continuously at 06:00–06:01"; Q21.3 WARNING — "~600 new superseded/day; unbounded accumulation"

---

## Q23.6 [DOMAIN-5] Mark_superseded audit coverage — does consolidation emit per-supersedure audit entries, or is each consolidation event invisible except for the aggregate consolidate action?
**Status**: DONE
**Mode**: static code analysis + observability
**Target**: consolidation.py (log_audit call sites), postgres_store.py log_audit(), audit_log supersede action query
**Hypothesis**: Q22.9 event reconstruction had to infer individual supersedure events from the mismatch count rather than reading them directly from the audit trail. If consolidation.py does not call log_audit() for each mark_superseded() call, then the only evidence of a supersedure is (a) the memory superseded_by field, (b) the aggregate consolidate action, and (c) the reconcile mismatch count increment. This makes post-hoc debugging of consolidation waves rely on reconcile dry-run as the only counting mechanism. Compare to decay: Q22.7 showed decay emits per-memory audit entries via executemany — does consolidation have an equivalent?
**Test**: (1) Grep consolidation.py for log_audit calls — how many, which actions, which fields. (2) Check if neo4j.mark_superseded() or qdrant.mark_superseded() call log_audit() internally. (3) Query GET /admin/audit?action=supersede&limit=50 — do any entries exist? (4) Count: should be ~521 entries if per-supersedure logging exists. (5) Characterize the complete audit trail for one consolidation cycle.
**Verdict threshold**:
- FAILURE: No supersede action in audit_log; individual supersedure events completely invisible; post-hoc debugging requires reconcile dry-run to count victims
- WARNING: Some supersedure events logged (inconsistent coverage across code paths)
- HEALTHY: Each mark_superseded() call emits audit entry with source_id, merged_id, user_id; full supersedure chain reconstructable from audit trail

**Derived from**: Q22.9 WARNING — "event reconstruction required inference from mismatch count, not direct audit trail"; Q22.7 HEALTHY — decay emits per-memory audit entries via executemany

---

## Q23.7 [DOMAIN-1] Importance floor — is there a minimum importance floor below which decay stops, and does double-decay push active memories below it?
**Status**: DONE
**Mode**: static code analysis + observability
**Target**: decay.py (decay formula and floor check), constants.py, active memory importance histogram
**Hypothesis**: With double-decay, memories aged >7 days may be at importance < 0.001 — functionally zero but still appearing in active scroll and retrieval results. If no floor exists, near-zero memories may: (a) pollute retrieval results (returned with near-zero relevance score), (b) block new stores via dedup (MatchValue still finds them as candidates), (c) occupy Qdrant storage and reconcile scan bandwidth indefinitely. A floor check (e.g., skip update if new_importance < 0.001) would bound the damage but also hide evidence of the double-decay bug.
**Test**: (1) Read decay.py for min_importance, floor check, or if new_importance < threshold: skip before applying update. (2) Check constants.py for MIN_IMPORTANCE or decay floor constant. (3) Query current active memories importance histogram — what is the minimum importance? How many memories below 0.01? Below 0.001? (4) Check retrieval.py — does search filter by importance > threshold or return all active regardless of importance? (5) Check dedup: does similarity check filter by candidate importance?
**Verdict threshold**:
- FAILURE: No importance floor; double-decay has pushed large numbers of active memories to near-zero importance (<0.001); these memories remain in active scroll, pollute dedup checks, and occupy retrieval bandwidth
- WARNING: No floor but near-zero memories are deprioritized in scoring; retrievability degraded but no active pollution
- HEALTHY: Importance floor exists (e.g., min_importance=0.01); decay stops at floor; double-decay damage is bounded; OR minimum active memory importance is above 0.01 even under double-decay

---

## Wave 24 Questions

---

## Q24.1 [DOMAIN-1] Double-decay fix verification — after deploying the Q22.1 fix to _user_conditions(), does each cron slot now apply decay exactly once per memory?
**Status**: DONE
**Wave**: 24
**Mode**: observability
**Target**: decay audit_log (GET /admin/audit?action=decay_run), Qdrant active memory importance histogram
**Hypothesis**: The Q22.1 fix (add IsNullCondition or MatchAny to the system-run Qdrant filter in _user_conditions(None), or remove the Phase 2 system run) should reduce the per-slot audit entries from 10 to ~2: one entry for the primary named user (proc≈active corpus) and one for the system/null run (proc≈0 if no unowned memories exist). The two 5936-count entries per slot (Q23.2 Phase 4 [system+system]) should collapse to a single named-user entry. Additionally, importance values for recently-created memories should start climbing toward single-decay baseline: a 1-day-old memory that was decaying at 0.9228/slot should now decay at 0.9606/slot, and the 3-7d cohort median importance/expected ratio should recover above 0.80 within a week of fix deployment.
**What to measure**: (1) Read the last 3 cron slots from GET /admin/audit?action=decay_run — count entries per slot and record proc values. (2) Verify no two entries in the same slot have proc≈active_corpus (both should be distinct: named user count + near-zero system count). (3) Compute current 3-7d cohort median importance/expected ratio — should trend above 0.793 (Q23.1 baseline). (4) Count memories at floor (importance=0.05) — should start declining as new memories no longer arrive at floor prematurely. (5) Confirm _user_conditions code change is present in the deployed version (read qdrant.py lines 106-114 or equivalent post-fix).
**Verdict threshold**:
- FAILURE: Slot structure still shows two full-corpus proc entries (proc≈active_corpus in both); fix not deployed or not effective; double-decay still active
- WARNING: Slot structure improved but not fully correct (e.g., system run now proc=0 but named-user run fires twice, or proc counts inconsistent across slots)
- HEALTHY: Each slot shows exactly one proc≈active_corpus entry (named user) and zero or one low-count system entry (proc=0 or near-zero); no slot has two entries with identical proc≈active_corpus; 3-7d median importance ratio trending above Q23.1 baseline of 0.793
**Priority**: Tier 0 — must be the first verification question answered after any fix deployment
**Derived from**: Q22.1 FAILURE — double-decay root cause; Q23.2 FAILURE — fix not deployed reconfirmed; Q23.1 WARNING — damage quantified; synthesis §14 post-deployment re-measurement Q23.2

---

## Q24.2 [DOMAIN-5] mark_superseded importance=0.0 fix verification — after removing importance=0.0 from neo4j.mark_superseded(), does the reconcile mismatch count stop growing?
**Status**: DONE
**Wave**: 24
**Mode**: observability
**Target**: neo4j_store.py mark_superseded() (code inspection), POST /admin/reconcile?dry_run=true (count trend), GET /admin/audit?action=supersede (rate measurement)
**Hypothesis**: The Q21.1 one-line fix (remove `m.importance = 0.0` from neo4j_store.py mark_superseded()) stops every new supersedure from creating a new importance mismatch. Before the fix, each of the ~700/day consolidation supersedures sets Neo4j importance to 0.0 while Qdrant retains the original importance — creating 1 new mismatch per supersedure. After the fix, Neo4j importance is preserved at whatever value the memory had, so reconcile dry_run importance_mismatches for active memories should stop growing. The existing ~15,000+ superseded mismatches (invisible to the current active-only scan) will not be repaired by this fix alone — those require a repair=true run or a reconcile scope restoration. But the growth rate should drop to near zero.
**What to measure**: (1) Read neo4j_store.py mark_superseded() — confirm `m.importance = 0.0` line is absent. (2) Call POST /admin/reconcile?dry_run=true, record importance_mismatches. (3) Wait for 1 cron cycle (~1 hour for consolidation), call reconcile dry_run again. (4) Compare counts: delta should be ≤5 (statistical noise) not ~700. (5) Verify active-memory mismatch count (the 50 from Q23.4) is being tracked separately — Q24.2 targets the supersede-path mismatches, not the creation-path mismatches.
**Verdict threshold**:
- FAILURE: importance_mismatches count still growing at >100/day after fix deployment; mark_superseded still setting importance=0.0 (code not changed or change not deployed)
- WARNING: Growth rate reduced but not eliminated (>10/day); possible secondary code path setting importance=0.0 not covered by the one-line fix
- HEALTHY: importance_mismatches count stable between consecutive reconcile dry_runs (delta ≤5 over 1h observation window); neo4j_store.py mark_superseded() confirmed to not set importance=0.0; new supersedure events add 0 mismatches
**Priority**: Tier 1b — verify after Q21.1 fix deployed
**Derived from**: Q21.1 HEALTHY — one-line fix confirmed safe; Q22.9 WARNING — 521 mismatches = historical accumulation; Q23.4 WARNING — ~700/day accumulation rate confirmed; synthesis §14 post-deployment re-measurement Q23.4

---

## Q24.3 [DOMAIN-5] Active-memory Neo4j sync gap root cause — what code path produces active memories with neo4j_importance=0.0 and how many exist now?
**Status**: DONE
**Wave**: 24
**Mode**: static code analysis + observability
**Target**: memory.py POST /store path (Neo4j write sequence), neo4j_store.py add_memory() or create_memory(), reconcile active mismatch sample (the 50 from Q23.4)
**Hypothesis**: Q23.4 found 50 active memories (e.g., id=41569d71, created 2026-03-15T05:33) where Qdrant importance=0.7+ but Neo4j importance=0.0. This is a different bug from Q21.1 (which only affects superseded memories via mark_superseded). The root cause is likely one of: (a) Neo4j node creation in the memory store path fails to write the importance field — created with importance=0 default; (b) the Neo4j write succeeds but importance is passed as None/0.0 by a code path that doesn't carry the importance value; (c) a Neo4j write error at creation time is silently swallowed (Q16.4b pattern), leaving the node with a default 0.0 importance. The accumulation rate is unknown — Q23.4 observed 50 at one snapshot but creation-path failures could be systematic (every store) or intermittent.
**What to measure**: (1) Read memory.py POST /store path — where does Neo4j importance get written? Is it passed explicitly or left to a default? (2) Read neo4j_store.py add_memory()/create_memory() — is importance a required field or optional with default=0.0? (3) Check if the Neo4j write for importance is in a try/except that swallows errors (Q16.4b pattern). (4) Call POST /admin/reconcile?dry_run=true — record current active importance_mismatches count; compare to Q23.4 baseline of 50 (created 2026-03-15T05:33). If count has grown, estimate daily creation rate. (5) Inspect the 50 known mismatch IDs — are they all from the same date/time window (suggesting an outage-related batch) or spread across multiple days (suggesting ongoing systematic failure)?
**Verdict threshold**:
- FAILURE: Active mismatch count has grown significantly above 50 (e.g., >200) since Q23.4 measurement; creation-path Neo4j sync failure is systematic and ongoing; every store may be producing Neo4j importance=0.0
- WARNING: Count is stable at ~50 (isolated to a specific window, not ongoing); root cause identified as a code path that can recur; fix specified but not yet deployed
- HEALTHY: Count stable at ~50; root cause confirmed as one-time event (e.g., Q22.9 outage period); fix is same as or simpler than Q21.1; not a regression risk for future stores
**Priority**: Tier 1 — characterize before deploying mark_superseded fix to confirm non-overlapping root causes
**Derived from**: Q23.4 WARNING — "50 NEW active-memory mismatches (neo4j=0.0, qdrant=0.7+); different bug from Q21.1"; synthesis §15 — "Active-memory Neo4j sync gap: new High severity open risk"

---

## Q24.4 [DOMAIN-5] Reconcile scope regression — is the active-only scope of the current reconcile API intentional or a regression that should be reverted to full-corpus scanning?
**Status**: DONE
**Wave**: 24
**Mode**: static code analysis + observability
**Target**: reconcile.py and ops.py reconcile logic (scroll_all call site, filter parameters), git log or code comments indicating scope change intent
**Hypothesis**: Q23.4 found that the reconcile API now scans only active memories, making 15,000+ superseded mismatches invisible in its output. The prior behavior (Q22.9 baseline) scanned all memories including superseded. This scope change could be: (a) an intentional narrowing — superseded memories are no longer being reconciled because find_related() filters superseded_by IS NULL anyway (so Neo4j importance for superseded memories doesn't affect retrieval); (b) an unintentional regression introduced alongside another change; (c) a performance optimization to avoid scanning 15,000+ superseded points. If intentional, the 15,000+ accumulated mismatches are "accepted waste" and the Q21.1 fix just stops new waste from accumulating. If a regression, the scope should be restored and a repair=true run should clear the backlog.
**What to measure**: (1) Read reconcile.py and ops.py — does the reconcile scroll use include_superseded=False or a filter that excludes superseded? Was this the case in Q22.9 when 521 were visible? (2) Check for any recent git commits or code comments explaining the scope change. (3) Determine whether superseded-memory importance mismatches affect any live system behavior: does find_related() use Neo4j importance for superseded memories? Does any query path include superseded memories by intention? (4) If the scope change is a regression: what is the effort to restore full-corpus scanning and what is the performance cost at current corpus size (~21,011 total)?
**Verdict threshold**:
- FAILURE: Scope change is a regression (no intentional code comment, no performance rationale); superseded mismatches are not benign (some query path does use Neo4j importance on superseded memories); full-corpus scan should be restored
- WARNING: Scope change is intentional but undocumented; superseded mismatches confirmed benign for retrieval (find_related filters them); but the change silently hides ~15,000 known-bad records from monitoring visibility
- HEALTHY: Scope change is intentional and documented; superseded mismatches confirmed to have zero retrieval or functional impact; active-only scan is the correct design; Q21.1 fix is sufficient to stop new mismatches from accumulating
**Priority**: Tier 1b — answer before deciding whether to run repair=true on the superseded mismatch backlog
**Derived from**: Q23.4 WARNING — "reconcile API changed scope from all-memories to active-only; 521+ superseded mismatches invisible"; Q21.1 HEALTHY — "Neo4j queries already filter superseded_by IS NULL so importance=0.0 on superseded has limited retrieval impact"

---

## Q24.5 [DOMAIN-4] Consolidation user_id attribution fix verification — after fixing consolidation.py:235 to pass user_id to merged Memory(), do consolidated memories retain user attribution?
**Status**: DONE
**Wave**: 24
**Mode**: observability + static code analysis
**Target**: consolidation.py Memory() constructor call at line ~235, GET /admin/users/{id}/export, get_distinct_user_ids() output
**Hypothesis**: Q22.9 confirmed that consolidation.py:235 creates the merged Memory() without a user_id argument, permanently attributing consolidated memories to user_id=None. The fix is ~3 lines (pass user_id=source_memories[0].user_id or infer from sources). After deployment, new consolidation events should produce merged memories that appear in the originating user's count_user_memories() and export, and users who had ALL their originals consolidated should reappear in get_distinct_user_ids(). The primary test is: find a user who recently had memories consolidated and verify the merged output has their user_id, not None.
**What to measure**: (1) Read consolidation.py around line 235 — confirm `Memory(... user_id=<source_user_id> ...)` pattern is present in the deployed version. (2) Trigger a manual consolidation (POST /ops/consolidate) and inspect the created merged memory via the export API for user_id. (3) Call GET /admin/users/{primary_user_id}/export and confirm the count includes recently-merged memories (not just originals). (4) Call get_distinct_user_ids() equivalent — confirm no users have disappeared due to consolidation. (5) Verify edge case: if sources have different user_ids (cross-user consolidation), what user_id does the merged memory get?
**Verdict threshold**:
- FAILURE: consolidated memories still have user_id=None after fix deployment; Memory() constructor not updated; user attribution still lost
- WARNING: Consolidated memories now have user_id set BUT edge cases exist (multi-user source memories, system memories) — partial fix
- HEALTHY: Consolidated memories have user_id matching their primary source; users do not disappear from get_distinct_user_ids() after consolidation; count_user_memories() includes merged memories; code inspection confirms the fix is present
**Priority**: Tier 2 — verify after consolidation.py:235 fix deployed
**Derived from**: Q22.9 WARNING — "consolidation.py:235 creates Memory() without user_id; user_id=2 data not deleted — consolidated into user_id=None merged form"; synthesis §13 Tier 2 item #18

---

## Q24.6 [DOMAIN-4] Superseded GC first batch — the 30-day eligibility window has opened; how many memories are now GC-eligible and what is the correct deletion procedure?
**Status**: DONE
**Wave**: 24
**Mode**: observability + static code analysis
**Target**: Qdrant superseded points (superseded_by IS NOT NULL AND invalid_at < now−30d), causal_extractor.py access patterns, neo4j_store.py delete_memory_node()
**Hypothesis**: Q21.3 identified the first GC-eligible batch would be ~2026-03-21 (30 days after earliest supersedure audit entry on 2026-03-02). Q22.3 confirmed 507 overnight consolidation entries from the Q22.9 anomaly window become 14-day eligible by 2026-03-27. We are now past both dates (current date: 2026-03-15 was Q23's date; the first batch is now due or imminent). The GC cron (Tier 3 item #26) is not deployed, so no deletions have occurred. This question characterizes the current GC backlog size, validates the safe GC criteria (age ≥30d + successor active + simultaneous Neo4j DELETE), and provides the spec for what the GC cron should do when deployed.
**What to measure**: (1) Query Qdrant for superseded memories where invalid_at < (now − 30 days) — count the GC-eligible batch. (2) For a sample of eligible memories, verify the successor memory is still active (superseded_by ID exists and is not itself superseded). (3) Check causal_extractor.py — does it access superseded memories by ID directly (which would make deletion unsafe) or only via active-memory queries? Q21.3 noted include_superseded=True but characterize whether old (>30d) superseded memories are realistically accessed. (4) Read neo4j_store.py for a delete_memory_node() or equivalent method — does it perform DETACH DELETE, and does it cascade to relationship cleanup? (5) Estimate: if GC cron ran today, how many points would be deleted? What percentage of the total Qdrant corpus would remain?
**Verdict threshold**:
- FAILURE: GC-eligible batch is >5,000 memories and growing; no deletion mechanism exists; causal_extractor accesses old superseded memories by direct ID lookup making safe deletion impossible without code changes
- WARNING: GC-eligible batch confirmed; safe deletion criteria satisfied for most but causal_extractor edge case requires a one-query fix before GC can run safely; or neo4j_store.py lacks delete_memory_node()
- HEALTHY: GC-eligible batch quantified; safe deletion criteria satisfied (successor active, no live causal_extractor access to old superseded); neo4j_store.py has delete_memory_node(); GC cron spec confirmed ready to implement
**Priority**: Tier 3 — characterize before implementing GC cron; GC window is open
**Derived from**: Q21.3 WARNING — "~600 new superseded/day; safe GC: age ≥30d + successor active + simultaneous Neo4j DELETE; 30-day batch eligible ~2026-03-21"; Q22.3 HEALTHY — "507-entry overnight wave eligible 2026-03-27"; synthesis §13 Tier 3 item #26

---

## Q24.7 [DOMAIN-1] Ghost-user decay fix verification — after fixing get_distinct_user_ids() to scan active-only, do ghost users disappear from the decay loop?
**Status**: DONE
**Wave**: 24
**Mode**: observability + static code analysis
**Target**: qdrant.py get_distinct_user_ids() (IS NULL filter on superseded_by), decay audit_log per-slot entry count
**Hypothesis**: Q21.5 found that get_distinct_user_ids() scans all 20,923 Qdrant points including superseded, returning user_ids whose only surviving memories are superseded — these ghost users produce 7/10 decay_run entries per slot with processed=0. The fix is a one-line IS NULL filter on superseded_by, which would reduce the returned user_id list from ~10 to ~2-3 (active named users only). After the fix, the per-slot audit entry count should drop from ~10 to ~2-3, eliminating the 7 wasted scroll operations per slot. Additionally, the primary user double-processing (~4% overdecay per run from Q21.5) should also be investigated — does the fix prevent the primary user from appearing twice?
**What to measure**: (1) Read qdrant.py get_distinct_user_ids() — confirm IS NULL filter on superseded_by is present. (2) Call GET /admin/audit?action=decay_run&limit=30 and count entries per cron slot — should now be ~2-3 not ~10. (3) Confirm no entries with processed=0 remain in the per-slot list (ghost users eliminated). (4) Verify the primary user appears exactly once per slot (not twice from the old Q21.5 double-processing). (5) Measure the improvement: old scan processed 20,923 points; new scan should process ~active_corpus (~6,000); verify via timing or log messages if available.
**Verdict threshold**:
- FAILURE: get_distinct_user_ids() still scans superseded points; per-slot decay entry count still ~10; ghost users still appearing with processed=0
- WARNING: Ghost users eliminated but per-slot count reduction smaller than expected (e.g., 7 not 3); or primary user still double-processed via a different mechanism
- HEALTHY: Per-slot decay entries reduced from ~10 to ≤3; no processed=0 entries per slot; get_distinct_user_ids() confirmed to filter active-only; qdrant scan size reduced from ~21,000 to ~6,000 points per decay cycle
**Priority**: Tier 2 — verify after Q21.5 IS NULL filter fix deployed
**Derived from**: Q21.5 WARNING — "7/10 decay_run entries/slot are processed=0; root cause: get_distinct_user_ids() scans superseded; 28 wasted scrolls/day"; Q22.2 WARNING — ghost user identity confirmed; synthesis §13 Tier 2 item #16

---

## Q24.8 [DOMAIN-5] Reconcile audit trail fix verification — after deploying the 9-LOC reconcile audit changes (Q21.6), are reconcile runs now visible in the audit log?
**Status**: DONE
**Wave**: 24
**Mode**: observability + static code analysis
**Target**: GET /admin/audit?action=reconcile, reconcile.py and ops.py (log_audit call sites)
**Hypothesis**: Q21.6 confirmed the reconcile audit fix is a ~9-LOC change across reconcile.py and ops.py, adding log_audit() calls for each reconcile run with fields including: mismatch count, repair count, run timestamp, and dry_run flag. After deployment, GET /admin/audit?action=reconcile should return entries for each reconcile execution, enabling: (a) last-run-date verification, (b) mismatch trend detection across runs, (c) repair convergence monitoring (was repair=true invoked and did the count drop?). Currently, 0 entries exist for action=reconcile — any non-zero count after deployment confirms the fix is working.
**What to measure**: (1) Read reconcile.py and ops.py — confirm log_audit() calls are present for reconcile runs. (2) Trigger a reconcile dry_run: POST /admin/reconcile?dry_run=true. (3) Query GET /admin/audit?action=reconcile&limit=10 — confirm at least 1 entry exists with correct fields (mismatch_count, dry_run=True, timestamp). (4) Trigger a reconcile with repair=true: POST /admin/reconcile?repair=true. (5) Query audit again — confirm a second entry exists with dry_run=False and repair_count > 0; verify the response now shows post-repair importance_mismatches (Q22.6 post-repair visibility fix, if also deployed).
**Verdict threshold**:
- FAILURE: GET /admin/audit?action=reconcile returns 0 entries after triggering reconcile; fix not deployed; reconcile execution still invisible
- WARNING: Reconcile audit entries exist but missing key fields (e.g., no mismatch_count, or dry_run flag absent); partial implementation
- HEALTHY: At least 1 audit entry per reconcile invocation with fields: action=reconcile, mismatch_count (int), dry_run (bool), timestamp; repair runs show repair_count > 0; last-run-date query returns correct timestamp
**Priority**: Tier 1b — verify after Q21.6 fix deployed; enables monitoring of all other fix verifications
**Derived from**: Q21.6 HEALTHY — "~9 LOC across reconcile.py + ops.py closes Q20.1 reconcile observability gap"; Q20.1 WARNING — "reconcile has zero audit_log entries — execution history unverifiable"; synthesis §13 Tier 1b item #7

---

## Wave 25 Questions

---

## Q25.1 [DOMAIN-1] Double-decay deployment check — has the _user_conditions(None) fix been deployed since Wave 24?
**Status**: DONE
**Wave**: 25
**Mode**: static code analysis + observability
**Target**: `src/workers/decay.py` or `src/storage/qdrant.py` `_user_conditions()` method; GET /admin/audit?action=decay_run
**Hypothesis**: Wave 24 (Q24.1) confirmed double-decay is still active after 12 consecutive waves. The fix requires adding `IsNullCondition(key="user_id")` to the system-run filter in `_user_conditions(None)` (or equivalent separation of the system-run entrypoint). No code change has been deployed in 13 characterization waves. This question checks whether the Tier 0 emergency hotfix has been applied in the interval since Wave 24 by inspecting the code and the live audit pattern. If deployed, each 6-hour audit slot should show exactly ONE full-corpus proc entry (system run) rather than two, and 3-7d cohort importance ratios should begin recovering above the Q24.1 baseline of 0.793.
**What to measure**: (1) Read `_user_conditions()` in qdrant.py or decay.py — does `_user_conditions(None)` now return a filter with `IsNullCondition(key="user_id")` instead of `[]`? (2) GET /admin/audit?action=decay_run&limit=40 — count entries per 6-hour slot. If the fix is deployed, each slot should have exactly 1 full-corpus proc entry (proc≈active_corpus) plus per-user entries, not 2 full-corpus entries. (3) Sample the most recent 3 slots. Report slot structure: number of entries, proc values per entry, whether any entry shows proc≈full_corpus twice. (4) If fix is deployed: check the 3-7d cohort — query `GET /admin/memories?age_min_days=3&age_max_days=7&limit=100` and compute median importance. Recovery would show ratio >0.793 (Q24.1 baseline).
**Verdict threshold**:
- FAILURE: `_user_conditions(None)` still returns `[]`; per-slot audit still shows two proc≈active_corpus entries; fix not deployed; 14th consecutive wave with zero Tier 0 action
- WARNING: Code change deployed but slot audit still shows two full-corpus entries (possible regression in different code path); or code change partially applied
- HEALTHY: `_user_conditions(None)` confirmed to return IS NULL filter; per-slot audit shows exactly 1 full-corpus proc entry; no per-user entry duplicates the full-corpus run; fix confirmed deployed
**Priority**: Tier 0 — highest priority; 12+ consecutive failure confirmations; fix is ~3 lines
**Derived from**: Q24.1 FAILURE — "double-decay fix not deployed (12th consecutive wave)"; Q22.1 FAILURE — "_user_conditions(None) returns [] → every memory decayed twice per slot"; synthesis §14 Tier 0 item #0; synthesis §15 Q24.1-post re-measurement spec

---

## Q25.2 [DOMAIN-5] mark_superseded importance=0.0 deployment check — has neo4j_store.py:391 been fixed since Wave 24?
**Status**: DONE
**Wave**: 25
**Mode**: static code analysis + observability
**Target**: `src/storage/neo4j_store.py` `mark_superseded()` method around line 391; GET /admin/reconcile?dry_run=true
**Hypothesis**: Wave 24 (Q24.2) confirmed `neo4j_store.py:391` still sets `m.importance = 0.0` in `mark_superseded()`. At ~796 consolidation events/day, approximately 796 new importance mismatches have accumulated since the Q24.2 measurement. If the fix was deployed (removing the one-line `m.importance = 0.0` assignment), the mismatch count growth rate should have dropped to near zero — the Sunday reconcile will have repaired the accumulated backlog and new consolidations will no longer create mismatches. This question verifies deployment and measures whether the mismatch accumulation rate has stopped.
**What to measure**: (1) Read `mark_superseded()` in neo4j_store.py — confirm whether `m.importance = 0.0` (or equivalent) is present or absent. (2) POST /admin/reconcile?dry_run=true — record `importance_mismatches` count. Compare to Q24.2 baseline of 92. If the fix is deployed and the Sunday reconcile has run, count should be near 0 (or a small accumulation since the last Sunday repair). If fix is NOT deployed, count should reflect ~796/day accumulation since Q24.2 (likely 1,500–3,000+ if days have passed). (3) Calculate implied accumulation rate: (current_count - Q24.2_baseline_of_92) / days_since_Q24.2. Rate >500/day confirms fix not deployed; rate ~0/day after a Sunday repair confirms fix deployed.
**Verdict threshold**:
- FAILURE: `neo4j_store.py:391` still contains `m.importance = 0.0`; importance_mismatches growing at >100/day; fix not deployed
- WARNING: Code fix present but mismatch count still growing (secondary code path creating 0.0 importance); or fix deployed but Sunday reconcile has not yet run to clear backlog
- HEALTHY: `mark_superseded()` confirmed to not set importance=0.0; reconcile dry_run shows importance_mismatches ≤10 (post-Sunday baseline or near-zero daily accumulation); fix confirmed deployed
**Priority**: Tier 1b — 1-line fix; resolves Q20.5 compound failure + stops weekly mismatch accumulation cycle
**Derived from**: Q24.2 FAILURE — "mark_superseded importance=0.0 fix not deployed; neo4j_store.py:391 confirmed unchanged; 92 mismatches; ~796/day accumulation"; Q21.1 HEALTHY — "one-line removal confirmed vestigial, zero regressions"; synthesis §15 Q24.2-post re-measurement spec

---

## Q25.3 [DOMAIN-4] Consolidation user_id attribution deployment check — has consolidation.py:235 been fixed since Wave 24?
**Status**: DONE
**Wave**: 25
**Mode**: static code analysis + observability
**Target**: `src/core/consolidation.py` Memory() constructor call around line 235; GET /admin/audit?action=supersede&limit=20
**Hypothesis**: Wave 24 (Q24.5) confirmed `consolidation.py:235` Memory() constructor has no `user_id=` argument. At ~796 merged memories/day, approximately that many attribution-less merged memories have accumulated since Q24.5. If the fix has been deployed, new consolidated memories should have `user_id` populated from the source cluster. The supersede audit entries (action=supersede) include `actor=consolidation` — cross-referencing a recently-created merged memory's user_id field against its source cluster members' user_ids will confirm whether attribution is being preserved.
**What to measure**: (1) Read `consolidation.py` around line 235 — confirm whether `Memory(... user_id=cluster[0].user_id ...)` or equivalent is present. (2) GET /admin/audit?action=supersede&limit=20 — identify the most recent consolidation-supersedure event (actor=consolidation). Extract the merged memory ID from the `details.superseded_by` field. (3) Query the merged memory: GET /admin/memories/{merged_id} — check its `user_id` field. Is it None (fix not deployed) or a valid user_id (fix deployed)? (4) If fix deployed: verify edge case — if the source cluster contained memories from multiple user_ids, what user_id was assigned to the merged output? (5) Count how many active memories in Qdrant have user_id=None — compare to Q24.5's pre-fix baseline.
**Verdict threshold**:
- FAILURE: `consolidation.py:235` Memory() constructor still lacks `user_id=` argument; most recent merged memory has user_id=None; ~796/day attribution loss continues
- WARNING: Fix deployed but edge case present — multi-user source clusters produce user_id=None merged memories; single-user case works correctly
- HEALTHY: `consolidation.py:235` confirmed to pass user_id from source cluster; most recent merged memory has user_id matching source memories; active memory user_id=None count not growing relative to Q24.5 baseline
**Priority**: Tier 2 — 3-line fix; prevents silent user attribution loss; users with consolidated memories disappear from decay loop
**Derived from**: Q24.5 FAILURE — "consolidation.py:235 Memory() constructor missing user_id argument confirmed; ~796 merged memories/day accumulate with user_id=None"; Q22.9 WARNING — "user_id=None merged form; disappears from get_distinct_user_ids()"; synthesis §15 Q24.5-post re-measurement spec

---

## Q25.4 [DOMAIN-3] Manual GC first batch — use the admin purge endpoint to delete a sample of 30+ day old superseded memories and verify the operation is safe
**Status**: DONE
**Wave**: 25
**Mode**: observability + live admin operation
**Target**: `/admin/memory/purge` or `/admin/memory/purge-domain` endpoint; Qdrant superseded points with `invalid_at < (now - 30d)`; Neo4j node count
**Hypothesis**: Wave 24 (Q24.6) confirmed ~11,000+ consolidation-superseded memories are 30+ days old and eligible for DETACH DELETE. No GC cron exists. The admin purge endpoint exists and can perform manual cleanup. Synthesis §15 identified this as a "no prerequisite" low-priority analytical question that can run without a cron implementation. The key question is: does the manual purge endpoint correctly delete both Qdrant points AND corresponding Neo4j nodes, does it affect active-memory queries (it should not), and does it reduce the ghost-user count in `get_distinct_user_ids()`? This is both a verification of the purge endpoint's correctness and a partial remediation of the Q24.6 WARNING.
**What to measure**: (1) Before purge: record Qdrant total count (should be ~21,043), active count (~5,945), superseded count (~15,099), and `get_distinct_user_ids()` output (should include 7+ ghost users). (2) Identify a small sample (50-100) of GC-eligible memories: Qdrant points with `superseded_by IS NOT NULL AND invalid_at < (today - 30 days)`. Verify each sample memory's successor (superseded_by ID) is still active. (3) Call the admin purge endpoint for the eligible sample batch. (4) After purge: record Qdrant total count, active count (should be unchanged), and superseded count (should decrease by batch size). (5) Verify Neo4j: check that the deleted memories' Neo4j nodes are gone (GET /admin/memories/{deleted_id} should return 404 or empty). (6) Re-call `get_distinct_user_ids()` — does the ghost user count decrease proportionally to the number of deleted superseded memories? (7) Verify active-memory queries return same results (spot-check 3 searches before and after purge).
**Verdict threshold**:
- FAILURE: Purge endpoint deletes Qdrant points but leaves Neo4j nodes (half-delete); or purge removes active memories erroneously; or active-memory search results change after purge
- WARNING: Purge is correct for both Qdrant and Neo4j, but ghost user count in `get_distinct_user_ids()` does not decrease as expected; or purge endpoint does not support batch deletion of superseded-by-criteria and requires individual memory IDs
- HEALTHY: Purge correctly removes both Qdrant points and Neo4j nodes for the sample batch; active memory count unchanged; active-memory searches unaffected; ghost user count in get_distinct_user_ids() decreases proportionally; operation is confirmed safe for larger batch execution
**Priority**: Tier 3 — no prerequisite; partial remediation of Q24.6 WARNING; confirms admin purge endpoint is production-ready for manual GC batches
**Derived from**: Q24.6 WARNING — "~11,000 eligible; admin purge endpoint available for manual GC; no DETACH DELETE cron"; Q21.3 WARNING — "safe GC: age ≥30d + successor active + simultaneous Neo4j DELETE"; synthesis §15 "Manual GC first batch — no prerequisite, can run without cron implementation"

---

## Q25.5 [DOMAIN-1] Hygiene cron first-archival threshold — with 632 floor-clamped memories and ongoing double-decay, are any active memories now meeting all hygiene archival criteria?
**Status**: DONE
**Wave**: 25
**Mode**: observability + static code analysis
**Target**: GET /admin/audit?action=auto_archive; `workers/hygiene.py` archival criteria; `scroll_hygiene_candidates` in qdrant.py
**Hypothesis**: Wave 24 (Q24.6) found the hygiene cron has archived 0 memories to date. The archival criteria require: `importance < 0.3 AND access_count = 0 AND age > 30 days AND not pinned AND not permanent AND superseded_by IS NULL`. Wave 23 (Q23.1) quantified 632 memories at the 0.05 importance floor — well below the 0.3 threshold. However, the 30-day age AND access_count=0 requirements may not yet be met for most floor-clamped memories. The double-decay bug accelerates the rate at which memories reach the floor — a memory that would normally reach importance=0.3 after ~30 days is instead reaching it in ~10-15 days under double-decay. This means the double-decay bug is also accelerating hygiene eligibility. As the corpus ages, the first hygiene archival batch may be imminent. This question characterizes how many active memories currently meet ALL hygiene criteria simultaneously.
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=10 — confirm whether any archival events have occurred since Q24.6 (still 0, or first batch happened). (2) Query active memories meeting the full hygiene criteria: `importance < 0.3 AND access_count = 0 AND created_at < (now - 30d) AND superseded_by IS NULL`. Count the eligible batch. (3) Of those eligible, what is the importance distribution? How many are at the 0.05 floor vs 0.05–0.30? (4) Estimate when the first archival will trigger: oldest eligible memory created_at date + 30d threshold — has that date passed? (5) Static check: does `scroll_hygiene_candidates` in qdrant.py correctly use `access_count <= 0` (matching memories with zero accesses) — or does it use `== 0` which might miss edge cases? (6) Cross-reference: do any of the 632 floor-clamped memories also have age > 30d AND access_count = 0? These are the highest-risk candidates for hygiene archival in the next run.
**Verdict threshold**:
- FAILURE: Hygiene cron criteria are misconfigured (e.g., `access_count = 0` never matches any memory due to schema mismatch); eligible batch exists but hygiene fails to archive; memories meeting all criteria are silently skipped
- WARNING: Eligible batch confirmed (>100 memories meeting all criteria); hygiene should have archived them but has not (possible cron failure or edge case in criteria matching); or first archival is imminent (<24h) and the auto-archive soft-delete mechanism is about to trigger
- HEALTHY: 0 or very few (<20) memories currently meet all hygiene criteria simultaneously (age threshold is the binding constraint for most floor-clamped memories); first archival batch projected >7 days away; hygiene cron is operating correctly on its intended timeline
**Priority**: Tier 3 — no prerequisite; cross-cutting (interacts with double-decay, floor, GC); characterizes the next phase of the memory lifecycle under current failure conditions
**Derived from**: Q24.6 WARNING — "hygiene cron running but 0 archived; hygiene is active-only soft-delete"; Q23.1 WARNING — "632 active memories at 0.05 floor (10.6%); 12 premature casualties in 3-7d age band"; Q24.1 FAILURE — "double-decay ongoing; 3-7d cohort ratio = 0.793"; synthesis §14 Tier 3 item #26 (GC cron cross-reference)

---

## Q25.6 [DOMAIN-1] ARQ worker restart anomaly characterization — what caused the Mar 15 timing anomaly and is it a recurring pattern?
**Status**: DONE
**Wave**: 25
**Mode**: observability
**Target**: GET /admin/audit?action=decay_run; GET /health; Docker container logs; ARQ worker uptime
**Hypothesis**: Wave 24 (Q24.1) noted a Mar 15 timing anomaly in the decay cron schedule: a single run at 00:01 (instead of the expected 06:xx pattern), then two runs 4 minutes apart at 06:45 and 06:49. Q24.1 noted this could indicate a system restart between Mar 14 18:15 and Mar 15 00:01 — consistent with the Q22.9 ARQ 6-hour outage pattern from Mar 14T18:15–00:01. The anomaly did not affect the double-decay finding (still confirmed), but it raises a secondary question: is the ARQ worker experiencing recurrent restart-on-recovery behavior where a backlog of missed cron slots fires in rapid succession after restart? If so, a single ARQ restart can produce a burst of decay runs in a short window, potentially over-decaying the corpus more than the already-confirmed 2× factor. This question characterizes the anomaly pattern and determines whether it is a one-off or recurring.
**What to measure**: (1) GET /admin/audit?action=decay_run&limit=200 — retrieve the full observable decay audit history. Identify all slots where the gap between consecutive entries is < 30 minutes (indicating burst behavior) vs the expected ~360-minute (6-hour) cadence. Count burst events. (2) Identify the Mar 15 anomaly slot specifically: confirm the 00:01 entry (single run), then 06:45 + 06:49 (two full-corpus runs 4 minutes apart). Is the 00:01 run a catch-up from the Q22.9 outage window (Mar 14 18:15–00:01 = 1 missed slot)? (3) Look for any other burst windows in the full audit history — how many times has a gap < 60 minutes appeared between full-corpus entries? (4) Check current ARQ health: GET /health — does it show the ARQ worker as healthy and connected? What is the reported uptime? (5) If burst behavior is recurring: characterize the maximum burst size (number of decay runs fired in < 1 hour). This matters because each burst run applies the double-decay factor — a 3-run burst = 0.9216³ = 0.782× factor on that window.
**Verdict threshold**:
- FAILURE: Burst behavior (< 30-min gap) appears more than 3 times in the audit history; ARQ worker is restarting recurrently; compound decay damage from bursts is materially worse than the 2× factor already characterized; effective daily decay rate is worse than the Q22.1 model
- WARNING: Mar 15 anomaly is isolated (appears once); or ARQ restarts occasionally but < 3 times in observable history; burst decay adds marginal damage above the Q22.1 baseline but does not change the severity characterization
- HEALTHY: Mar 15 anomaly is explained as a catch-up from the Q22.9 outage (exactly 1 missed slot → 1 catch-up run at 00:01); no other burst patterns in history; ARQ worker uptime is stable; the Q22.1 double-decay characterization (2× factor per slot) remains the complete model of decay behavior
**Priority**: Tier 3 — observability; cross-references Q22.9 outage pattern; determines whether the Q22.1 decay model understates actual corpus damage
**Derived from**: Q24.1 FAILURE — "Mar 15 timing anomaly (00:01 single run, 06:45+06:49 4 min apart) suggests possible system restart; double-decay still manifest"; Q22.9 WARNING — "ARQ 6-hour outage 2026-03-14T18:15–00:01; dec=4544 catch-up at 00:01"; synthesis §3 Wave 24 cross-domain observation #1

---

## Q25.7 [DOMAIN-1] Ghost-user decay and consolidation user_id deployment check — have Q21.5 (IS NULL filter) and Q24.5 (consolidation user_id) fixes been co-deployed?
**Status**: DONE
**Wave**: 25
**Mode**: static code analysis + observability
**Target**: `src/storage/qdrant.py` `get_distinct_user_ids()` (IS NULL filter); `src/core/consolidation.py:235` (user_id argument); GET /admin/audit?action=decay_run&limit=40
**Hypothesis**: Q24.7 confirmed the ghost-user decay fix (IS NULL filter in `get_distinct_user_ids()`) is not deployed — 7/10 decay_run entries per slot still show proc=0 ghost users. Q24.5 confirmed the consolidation user_id attribution fix is also not deployed — merged memories still get user_id=None, which is the root cause of ghost users being created. These two fixes interact: deploying the IS NULL filter (Q21.5 fix) will immediately eliminate ghost users from the decay loop, but new ghost users will continue accumulating unless the consolidation user_id fix (Q24.5 fix) is also deployed. This question checks deployment status of both fixes and measures whether their co-deployment has reduced the per-slot ghost user count.
**What to measure**: (1) Read `get_distinct_user_ids()` in qdrant.py — confirm whether `IsNullCondition(is_null=PayloadField(key="superseded_by"))` filter is present. (2) Read `consolidation.py:235` Memory() constructor — confirm whether `user_id=` argument is present (overlaps with Q25.3 but scoped to ghost-user impact). (3) GET /admin/audit?action=decay_run&limit=40 — count entries per cron slot. If IS NULL filter is deployed: slots should show ≤3 entries (1 full-corpus system run + 1-2 real users) instead of ~10; no proc=0 entries. (4) If IS NULL filter deployed but consolidation user_id fix NOT deployed: count whether new merged memories with user_id=None are accumulating in Qdrant — these will eventually become new ghost users as their originals get superseded and GC'd. (5) Report the compound deployment status: both fixes deployed / only IS NULL deployed / only consolidation user_id deployed / neither deployed.
**Verdict threshold**:
- FAILURE: Neither fix deployed; per-slot decay audit still shows ~10 entries with 7 proc=0 ghost users; both code paths confirmed unchanged from Q24.7 and Q24.5
- WARNING: IS NULL filter deployed (ghost users eliminated from current loop) but consolidation user_id fix NOT deployed — ghost users will re-accumulate as new merged memories with user_id=None age through the superseded pool; partial fix only
- HEALTHY: Both fixes deployed; per-slot decay audit shows ≤3 entries; 0 proc=0 ghost entries; Qdrant scan size reduced from 21,043 to ~5,945 per decay cycle; new consolidated memories have user_id set; ghost user re-accumulation path closed
**Priority**: Tier 2 — compound deployment check; the two fixes must both be deployed to permanently eliminate ghost users
**Derived from**: Q24.7 FAILURE — "ghost-user decay fix not deployed; 7 proc=0 entries per slot confirmed"; Q24.5 FAILURE — "consolidation user_id attribution fix not deployed; ~796 merged memories/day with user_id=None"; Q21.5 WARNING — "get_distinct_user_ids() scans superseded; ghost users grow with superseded pool"; synthesis §13 Tier 2 items #16 and #18

---

## Wave 26 Questions

**Wave theme**: Hygiene first-archival verification, deployment status re-check (4 open FAILUREs), and compound-damage quantification from 14 waves of unresolved double-decay.

---

## Q26.1 [DOMAIN-1] Hygiene first-archival verification — did the 2026-03-17 or 2026-03-18 04:00 cron archive the Feb 14 cohort?
**Status**: DONE
**Wave**: 26
**Mode**: observability
**Target**: GET /admin/audit?action=hygiene_archive&limit=100; GET /admin/audit?action=auto_archive&limit=100; active memory age/importance distribution query
**Hypothesis**: Q25.5 established that 0 memories met all hygiene criteria as of the Wave 25 measurement, with the oldest active memory (2026-02-14T18:00:51) crossing the 30-day threshold on 2026-03-16 at 18:00 UTC. The daily 4am hygiene cron would first encounter eligible memories on 2026-03-17 (if any created before 04:00 on Feb 15 have crossed) or 2026-03-18 at 04:00 (when the full Feb 14 cohort is unambiguously > 30 days old). Under double-decay, the Feb 14 cohort will have reached importance near the 0.05 floor — meaning the fraction eligible for archival is determined almost entirely by the age gate and access_count=0, not importance. The first batch size is uncharacterized.
**What to measure**: (1) GET /admin/audit?action=hygiene_archive&limit=100 (or auto_archive if that is the correct action name) — did any hygiene archive events fire? If yes: how many memories were archived? Report archive count and importance distribution of archived memories. (2) If 0 archival events: check whether the action name is correct — try action=archive or action=hygiene, or check worker logs for hygiene worker output around 04:00 on Mar 17-18. (3) Compare to single-decay expectation: under single-decay from importance=0.5 over 30 days, expected importance = 0.5 x 0.96^(96x30) near-zero; under double-decay (0.9216/slot) even faster. Confirm: are all archived memories at or near the 0.05 floor? (4) Post-archive: re-query active memory count — confirm count decreased by archived batch size. (5) Verify that hygiene archival is a soft-delete (archive flag or archive table) NOT a DETACH DELETE — consolidation-superseded memories must NOT have been touched; confirm superseded memory count unchanged.
**Verdict threshold**:
- FAILURE: Hygiene cron fired but 0 memories archived despite eligible batch confirmed (criteria misconfigured, cron failing silently, or hygiene soft-delete broken); or hygiene archive deleted consolidation-superseded memories (scope bleed)
- WARNING: Hygiene criteria are correct but the 04:00 run on Mar 17 caught 0 memories because the age threshold was not crossed until 18:00 — first batch deferred to Mar 18; or batch size is unexpectedly large (> 2x the single-decay estimate), confirming double-decay over-acceleration
- HEALTHY: Hygiene archive fires on Mar 17 or Mar 18; batch size consistent with double-decay-accelerated importance profile; active memory count decreases by archived batch; no superseded memories touched; soft-delete mechanism verified correct
**Priority**: TIME-SENSITIVE — Wave 26 day 1; Q25.5 explicitly flagged this as required Wave 26 verification; first real-world hygiene system activation
**Derived from**: Q25.5 HEALTHY — "first batch expected 2026-03-17 at 04:00; double-decay accelerates eligibility; follow-up required Wave 26"; synthesis §16 "Hygiene first archival verification (RUN ON 2026-03-17)"; synthesis §10 Pattern 10

---

## Q26.2 [DOMAIN-1] Double-decay deployment check — has the _user_conditions(None) fix been deployed since Wave 25?
**Status**: DONE
**Wave**: 26
**Mode**: static code analysis + observability
**Target**: `src/storage/qdrant.py` `_user_conditions()` method; GET /admin/audit?action=decay_run&limit=20
**Hypothesis**: Q25.1 confirmed the double-decay fix (adding IsNullCondition or MatchAny to the system-run filter in _user_conditions(None)) is not deployed — the 14th consecutive wave. If deployed between Wave 25 and Wave 26, per-slot decay audit should now show exactly 1 full-corpus proc entry per 6-hour slot (system-only run) plus per-user entries, rather than 2 full-corpus entries. Critically, if the fix was NOT deployed before the hygiene cron ran on 2026-03-17/18, the first hygiene batch was processed under double-decay conditions — more memories archived than expected under correct single-decay behavior.
**What to measure**: (1) Read _user_conditions() in qdrant.py — confirm whether IsNullCondition or MatchAny with user_id IS NULL is now present. (2) GET /admin/audit?action=decay_run&limit=20 — examine the 3 most recent 6-hour slots. Count full-corpus proc entries per slot. If fix deployed: each slot shows 1 full-corpus system run + per-user entries. If not deployed: each slot shows 2 full-corpus runs (15th consecutive FAILURE). (3) If fix is deployed: calculate the slot timestamp when fix became effective — was it BEFORE or AFTER the hygiene cron run on 2026-03-17 04:00? If deployed AFTER the hygiene run, the hygiene batch was inflated by double-decay. (4) Record the current 3-7d cohort importance ratio (compare to Q23.1 baseline of 0.793) — if fix deployed and time has elapsed, ratio should be recovering toward 1.0. (5) Report floor-clamped count (was 632 in Q23.1) — should be stable or decreasing if fix deployed.
**Verdict threshold**:
- FAILURE: _user_conditions(None) still returns []; per-slot audit still shows 2 full-corpus proc entries; fix not deployed (15th consecutive wave)
- WARNING: Code change deployed but slot audit still shows two full-corpus entries (regression in different code path or fix partially applied)
- HEALTHY: _user_conditions(None) confirmed to return IS NULL filter; per-slot audit shows exactly 1 full-corpus proc entry per slot; fix confirmed deployed; document whether fix was deployed before or after the hygiene first-archival event
**Priority**: Tier 0 — highest priority; 14 consecutive failure confirmations; ~3-line fix
**Derived from**: Q25.1 FAILURE — "double-decay fix not deployed (14th consecutive wave); 21 of 22 slots confirm 2 full-corpus runs per slot"; synthesis §16 "Q25.1-post — Double-decay post-fix verification"; synthesis §15 Tier 0 item #0

---

## Q26.3 [DOMAIN-1] Double-decay compound damage accumulation — how much total corpus damage has 14 waves of unresolved double-decay deposited?
**Status**: DONE
**Wave**: 26
**Mode**: observability + quantitative analysis
**Target**: Active memory corpus; importance distribution; floor-clamped cohort size; age-stratified importance analysis
**Hypothesis**: Q23.1 quantified double-decay damage at Wave 23: 632 memories (10.6%) floor-clamped, 12 premature casualties in the 3-7d band, median 3-7d importance = 79.3% of single-decay baseline. Wave 26 is several days later with still no fix deployed. The floor-clamped cohort may have grown, and the corpus has rotated — new memories have entered and some old ones may now have been hygiene-archived (Q26.1). This question provides a full damage snapshot at the Wave 26 measurement point, including the interaction with the hygiene first-archival event.
**What to measure**: (1) Query current floor-clamped memory count: active memories with importance = 0.05 (or importance <= 0.051). Compare to Q23.1 baseline of 632 (10.6%). If growing: estimate how many new memories have been prematurely driven to the floor since Wave 23. (2) Age-stratified importance ratio: for memories in the 3-7d band, compute median importance and divide by single-decay expectation (0.5 x 0.96^(96x5) for a 5-day memory starting at 0.5). Compare to Q23.1 ratio of 0.793. (3) Estimate total importance-units stolen from corpus by double-decay: for each active memory with age T slots, stolen importance = initial_importance x (single_decay_factor^T - double_decay_factor^T). Sum across all active memories. (4) Post-hygiene-archival check (cross-ref Q26.1): were the archived memories predominantly from the floor-clamped cohort? Report whether hygiene archival removed memories that would have survived under single-decay (i.e., memories where single-decay importance would still be > 0.3 but double-decay drove them below 0.3 and into the archive — double-decay-induced false hygiene positives).
**Verdict threshold**:
- FAILURE: Floor-clamped cohort has grown significantly (> 800, up from 632); or Q26.1 hygiene archive removed memories with estimated single-decay importance > 0.3 (double-decay-induced false positives); total importance-unit damage continues at projected rate with no recovery
- WARNING: Floor-clamped cohort stable or slightly grown (632 +/- 50); 3-7d ratio declined further below 0.793; hygiene batch size explainable by double-decay but within expected range
- HEALTHY: Floor-clamped cohort stable at ~632; ratio near Q23.1 baseline (fix may have been deployed during measurement period); hygiene batch consistent with single-decay expectation
**Priority**: Tier 3 — compound damage characterization; no prerequisite; documents scope of remediation required post-fix
**Derived from**: Q23.1 WARNING — "632 active memories at floor; 12 premature casualties; median 3-7d importance 79.3% of baseline"; Q25.1 FAILURE — "active corpus 5,936 as of Mar 15T06"; synthesis §15 Pattern 9; synthesis §10 Pattern 10

---

## Q26.4 [DOMAIN-5] mark_superseded fix deployment + weekly mismatch cycle third data point — has neo4j_store.py:391 been fixed?
**Status**: DONE
**Wave**: 26
**Mode**: static code analysis + observability
**Target**: `src/storage/neo4j_store.py` `mark_superseded()` line ~391; POST /admin/reconcile?dry_run=true
**Hypothesis**: Q25.2 confirmed the fix is not deployed and established the weekly mismatch cycle empirically: ~92 mismatches/day, ~5,572 at peak (pre-Sunday), repaired by Sunday 05:30am reconcile. Q24.2 and Q25.2 both measured exactly 92 mismatches ~1 day post-Sunday repair, providing the first two data points for the cycle curve. Wave 26 provides a third data point. The expected count depends on day of week: ~1 day post-Sunday = ~92; mid-week = ~460; pre-Sunday = ~5,572. This question tests both deployment status and, if undeployed, provides the third data point for empirical cycle confirmation.
**What to measure**: (1) Read mark_superseded() in neo4j_store.py — confirm presence or absence of m.importance = 0.0 or equivalent. (2) POST /admin/reconcile?dry_run=true — record importance_mismatches count. Note the day of week and time (relative to Sunday 05:30am). (3) If fix NOT deployed: calculate implied daily accumulation rate = mismatch_count / days_since_last_Sunday_repair. Compare to Q24.2 and Q25.2 rates (~92/day). Third empirical data point for the cycle: does the rate hold at ~92/day and peak at ~5,572? (4) If fix IS deployed: expected count is 0 or near-0 (if Sunday reconcile has run since deployment) or only backlog accumulated before deployment date. (5) Check reconcile audit: GET /admin/audit?action=reconcile&limit=10 — still expect 0 entries unless Q24.8 fix also deployed.
**Verdict threshold**:
- FAILURE: neo4j_store.py:391 still contains m.importance = 0.0; importance_mismatches growing at ~92/day rate; fix not deployed (3rd consecutive wave reconfirmation)
- WARNING: Fix deployed but mismatch count still shows accumulation (secondary path creating mismatches); or fix deployed but Sunday reconcile has not yet run to clear backlog
- HEALTHY: mark_superseded() confirmed to not set importance=0.0; reconcile dry_run shows importance_mismatches near 0 or declining post-Sunday repair; fix confirmed deployed
**Priority**: Tier 1b — 1-line fix; 2nd consecutive reconfirmation; stops weekly ~5,572-mismatch accumulation cycle
**Derived from**: Q25.2 FAILURE — "mark_superseded importance=0.0 fix not deployed; neo4j_store.py:391 unchanged; 92 mismatches = 1 day post-Sunday repair; mismatch cycle confirmed ~92/day"; synthesis §16 "Q25.2-post — mark_superseded mismatch rate post-fix"

---

## Q26.5 [DOMAIN-4] Ghost-user re-accumulation trajectory — how quickly will the ghost-user pool rebuild after IS NULL-only deployment?
**Status**: DONE
**Wave**: 26
**Mode**: quantitative analysis + static code analysis
**Target**: `src/storage/qdrant.py` `get_distinct_user_ids()` (IS NULL filter status); `src/core/consolidation.py:235` (user_id= status); Qdrant user_id=None active memory count; audit supersede log
**Hypothesis**: Q25.7 identified a ghost re-accumulation trap: even if the IS NULL filter (Q21.5) is deployed, new merged memories with user_id=None (from the undeployed Q24.5 fix) continue accumulating at ~796/day. These will become ghost user candidates when their original source memories are eventually superseded or GC-ed. The question is: how long after deploying only the IS NULL filter would it take for ghost users to return to their current level (7 per cron slot)? This characterizes whether IS NULL-only deployment buys meaningful time or whether the ghost user pool rebuilds within days, making co-deployment of both fixes the only effective strategy.
**What to measure**: (1) Confirm deployment status of both fixes (IS NULL filter in get_distinct_user_ids(); user_id= in consolidation.py:235). (2) Count the current user_id=None active memory pool: query Qdrant for active memories (superseded_by IS NULL) with user_id=None. Compare to Q25.3 cumulative estimate of ~22,288 attribution-less merged memories. (3) Characterize dormant ghost users: user_id=None active memories whose parent_ids are ALL already superseded — these will appear in get_distinct_user_ids() immediately as their source memories are superseded. Count this dormant pool. (4) Estimate re-accumulation timeline: at ~796 new user_id=None merged memories/day and given hourly consolidation, how many days after deploying only the IS NULL filter would it take for 7 ghost users to re-emerge? (5) If both fixes still undeployed: report current per-slot ghost user count from audit (should still be 7 per slot matching Q25.7).
**Verdict threshold**:
- FAILURE: Neither fix deployed; per-slot count still 7 proc=0; re-accumulation trajectory shows ghost users rebuild within 30 days of IS NULL-only deployment; dormant pool already exists
- WARNING: IS NULL deployed but consolidation user_id not; current ghost user count is 0 but user_id=None pool growing; re-accumulation in progress; estimated days to first new ghost user < 30
- HEALTHY: Both fixes deployed; per-slot count <= 3; no proc=0 entries; user_id=None pool not growing; ghost re-accumulation path permanently closed
**Priority**: Tier 2 — deployment sequencing decision support; no prerequisite; informs whether IS NULL-only deployment is worth doing without the consolidation user_id fix
**Derived from**: Q25.7 FAILURE — "ghost re-accumulation path open: ~796 new user_id=None merged memories/day seed next ghost generation"; Q25.3 FAILURE — "cumulative ~22,288 attribution-less merged memories over 28 days"; synthesis §17 residual risk "Ghost users in decay: both Q21.5 IS NULL fix and Q24.5 consolidation user_id fix must be co-deployed"

---

## Q26.6 [DOMAIN-3] Superseded GC backlog growth — how large has the eligible pool grown since Q24.6, and is reconcile scan time degrading?
**Status**: DONE
**Wave**: 26
**Mode**: observability + quantitative analysis
**Target**: Qdrant total/superseded point counts; POST /admin/reconcile?dry_run=true (scan duration); GET /admin/audit?action=reconcile
**Hypothesis**: Q24.6 found ~15,099 total superseded memories with ~11,000+ crossing the 30-day eligible threshold. Q25.4 confirmed no GC endpoint or cron can touch this pool. The pool grows at approximately ~796 new superseded memories/day from consolidation. By Wave 26 (~3-7 days after Wave 25), the pool should have grown by ~2,400-5,600 additional superseded points. Q20.2 established reconcile scan time baseline (209 cursor round trips at 20K total points). As the superseded pool grows, reconcile scan time grows proportionally. Additionally, Q26.1 may have reduced the active pool (hygiene archive) — checking whether active count change interacts with reconcile scope.
**What to measure**: (1) Query current Qdrant total count and active count. Compute superseded count = total - active. Compare to Q25.4 baseline (total ~21,043, active ~5,936, superseded ~15,107). Calculate daily growth rate over the interval since Q25.4. (2) POST /admin/reconcile?dry_run=true — time the operation. Compare to Q20.2 baseline. Has duration increased proportionally to corpus growth? (3) Estimate the 30-day-eligible GC pool: memories with superseded_by IS NOT NULL AND invalid_at < (now - 30d). Compare to Q24.6 estimate of ~11,000+. (4) Project: at current growth rates with no GC, how many superseded points in 30 days? 60 days? At what corpus size does reconcile scan time exceed 60 minutes (ARQ task timeout)? (5) If Q26.1 confirmed hygiene archival occurred: was the archived count reflected in the active total? Reconcile should include archived memories if they retain their Qdrant point; confirm whether hygiene-archived memories are soft-deleted (flag only) or hard-deleted (point removed).
**Verdict threshold**:
- FAILURE: Superseded pool has grown by > 5,000 since Q25.4; reconcile scan time has measurably increased (> 20% over Q20.2 baseline); trajectory projects ARQ timeout breach within 90 days
- WARNING: Superseded pool growing as expected (~796/day); reconcile scan time stable; GC-eligible pool at 12,000-15,000 and growing; trajectory projects operational issues within 1 year
- HEALTHY: Superseded pool growth matches consolidation rate; reconcile scan time stable; no measurable operational degradation; GC-eligible pool characterized and scoped for new endpoint implementation
**Priority**: Tier 3 — characterizes backlog growth trajectory; motivates Tier 3 item #26 GC cron; no prerequisite
**Derived from**: Q25.4 WARNING — "no available endpoint or cron for bulk superseded GC; consolidation-superseded GC gap persists"; Q24.6 WARNING — "~11,000 eligible; 15,099 total superseded; no DETACH DELETE cron"; Q21.3 WARNING — "~600 new superseded/day; unbounded accumulation growing reconcile scan time"; synthesis §15 Pattern 8

---

## Q26.7 [DOMAIN-5] Reconcile and hygiene audit observability — have the Q21.6 reconcile audit entries been deployed, and did the Wave 26 hygiene archival event write audit records?
**Status**: DONE
**Wave**: 26
**Mode**: static code analysis + observability
**Target**: `src/workers/reconcile.py` and `src/api/routes/ops.py` (log_audit calls); GET /admin/audit?action=reconcile&limit=10; GET /admin/audit?action=hygiene_archive&limit=20
**Hypothesis**: Q24.8 confirmed the reconcile audit trail fix (Q21.6, ~9 LOC) is not deployed — zero reconcile entries in audit_log after multiple invocations. The Wave 26 hygiene first-archival event (Q26.1) creates a new audit observability test: if the hygiene worker writes audit entries for each archived memory, the audit log should contain hygiene_archive or auto_archive entries. If the hygiene worker also lacks audit instrumentation, it follows the same observability anti-pattern as reconcile — a critical maintenance operation runs with zero visibility. This question checks both the reconcile audit gap (2nd consecutive reconfirmation) and whether hygiene archival produces observable audit evidence.
**What to measure**: (1) Read reconcile.py and ops.py — confirm whether log_audit() calls are present near reconcile execution points. (2) POST /admin/reconcile?dry_run=true — then GET /admin/audit?action=reconcile&limit=10. Expect 0 entries if fix not deployed; expect >= 1 entry if fix deployed. (3) GET /admin/audit?action=hygiene_archive&limit=20 (or auto_archive or archive) — confirm whether hygiene archival events are written to the audit log. If Q26.1 confirmed archival occurred, there should be audit entries with memory_id, importance, and created_at fields. (4) Read workers/hygiene.py — does the hygiene worker call log_audit() after archiving? Or does it run silently like reconcile? (5) If reconcile audit IS deployed: confirm format includes mismatch_count, repair_count, scan_duration, and timestamp as metadata fields (per Q21.6 specification).
**Verdict threshold**:
- FAILURE: Both reconcile audit fix and hygiene archive audit are undeployed; zero entries in both action namespaces; two critical maintenance operations have zero observability
- WARNING: Reconcile audit fix not deployed but hygiene archive events ARE visible in audit log; partial observability gap (reconcile invisible, hygiene visible); or reconcile fix deployed but audit entry format is incomplete (missing mismatch_count or repair_count)
- HEALTHY: Reconcile audit fix deployed; GET /admin/audit?action=reconcile returns >= 1 entry with required fields; hygiene archive entries also visible for Q26.1 events
**Priority**: Tier 1b — 9-LOC fix; 2nd consecutive reconfirmation; Wave 26 hygiene event makes this time-relevant (reveals whether hygiene archival is also invisible)
**Derived from**: Q24.8 FAILURE — "reconcile audit trail fix not deployed; zero reconcile entries in audit_log"; Q21.6 HEALTHY — "9 LOC across reconcile.py + ops.py; fire-and-forget log_audit()"; Q26.1 creates opportunity to test whether hygiene worker also lacks audit instrumentation

## Wave 27 Questions

**Wave theme**: Hygiene first-archival verification (time-sensitive 2026-03-17/18), first GC-eligible cohort emergence (2026-03-16), double-decay 7-20d band impact, information recovery debt quantification, and deployment re-checks for the three open FAILURE items.

---

## Q27.1 [DOMAIN-1] Hygiene first-archival verification (TIME-SENSITIVE) -- did the 2026-03-17 or 2026-03-18 04:00 cron archive the Feb 14 cohort?
**Status**: INCONCLUSIVE
**Wave**: 27
**Mode**: observability
**Target**: GET /admin/audit?action=auto_archive&limit=100; active memory count; Qdrant total point count post-archival
**Hypothesis**: Q26.1 was INCONCLUSIVE because it was measured 2 days before the expected first-archival. Q26.7 confirmed that hygiene.py:49 has log_audit(action="auto_archive") instrumentation with per-memory metadata. The daily 4am hygiene cron should fire on 2026-03-17 or 2026-03-18. Q26.3 revised expectations: for 30d+ memories, both decay models drive importance near 0.05 floor, so batch size is driven by access_count=0 criterion. Archival should be soft-delete (superseded_by="auto-archive") NOT DETACH DELETE.
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=100 -- how many auto_archive entries exist? Extract importance, access_count, age_days from details field. (2) If 0 entries: verify timing (must be after 04:00 on 2026-03-17 or 2026-03-18). Try action=archive or action=hygiene as fallbacks. (3) Verify soft-delete: archived memories should have superseded_by="auto-archive" in Qdrant; should NOT appear in active scroll (IS NULL filter). (4) Confirm consolidation-superseded pool is UNCHANGED -- hygiene must not have touched the 15,130+ superseded memories. (5) Active count before vs after: confirm decreased by archived batch size. (6) Total Qdrant points should be UNCHANGED (soft-delete, not hard-delete).
**Verdict threshold**:
- FAILURE: Cron fired but 0 memories archived despite age > 30d criterion met; or hygiene archived consolidation-superseded memories (scope bleed)
- WARNING: Mar 17 04:00 caught 0 (bulk cohort not yet past threshold); first real batch deferred to Mar 18; or batch size unexpectedly large or small
- HEALTHY: auto_archive audit entries confirmed; batch size consistent with access_count=0 criterion; soft-delete verified; active count decreased; superseded pool unchanged
**Priority**: TIME-SENSITIVE -- Wave 27 day 1; Q26.1 explicitly deferred this verification to Wave 27
**Derived from**: Q26.1 INCONCLUSIVE; Q26.7 FAILURE/NOTE (hygiene.py:49 confirmed); Q26.3 WARNING (batch not inflated for 30d+ cohort)

---

## Q27.2 [DOMAIN-3] First GC-eligible cohort emergence -- are any superseded memories now 30+ days old and eligible for DETACH DELETE?
**Status**: DONE
**Wave**: 27
**Mode**: observability + quantitative analysis
**Target**: Qdrant superseded pool (superseded_by IS NOT NULL AND invalid_at < now-30d); POST /admin/reconcile?dry_run=true
**Hypothesis**: Q26.6 corrected Q24.6: first GC-eligible cohort (superseded memories from Feb 14 originals) crosses 30-day threshold on 2026-03-16. As of Wave 27, the first GC-eligible batch should exist. No automated mechanism exists (Q21.3 GC cron unimplemented). This is the first time real GC-eligible candidates are available for measurement.
**What to measure**: (1) Query Qdrant for superseded memories with invalid_at < (now - 30 days): count and report. (2) Verify these are consolidation-superseded (superseded_by IS NOT NULL, not superseded_by="auto-archive"). (3) Check if any automated GC ran: has superseded pool total changed beyond expected consolidation growth rate? (4) Reconcile scan time: POST /admin/reconcile?dry_run=true -- compare to Q26.6 baseline of 5.94s for 21,105 points. (5) Cross-ref with Q27.1: do hygiene-archived memories also appear in GC-eligible query?
**Verdict threshold**:
- FAILURE: 0 GC-eligible memories despite 2026-03-16 threshold (calculation wrong); or automated GC ran silently without audit entries
- WARNING: First GC-eligible cohort confirmed (hundreds of memories from Feb 14 cohort); no automated GC; Q21.3 cron remains unimplemented
- HEALTHY: GC-eligible cohort confirmed and sized; automated GC cron deployed and running; Qdrant total decreasing
**Priority**: Tier 2 -- first real GC opportunity; motivated by Q26.6 timeline correction
**Derived from**: Q26.6 WARNING (0 GC-eligible as of 2026-03-15; first cohort emerges 2026-03-16); Q21.3 WARNING (GC cron unimplemented)

---

## Q27.3 [DOMAIN-1] Double-decay 7-20d band -- are memories approaching the hygiene importance threshold faster than under single-decay?
**Status**: DONE
**Wave**: 27
**Mode**: quantitative analysis
**Target**: Active memory corpus; importance distribution stratified by age band (7-10d, 10-15d, 15-20d); hygiene threshold importance < 0.3
**Hypothesis**: Q26.3 noted the 7-20d band is disproportionately affected by double-decay. Under single-decay (0.9228/slot), a memory at importance=0.5 reaches importance=0.3 in approximately 7-8 days. Under double-decay (0.8516/slot), the same memory reaches 0.3 in approximately 3-4 days -- the hygiene threshold is reached roughly 2x faster. This creates a "double-decay inflation queue": memories in the 15-30d range with importance < 0.3 and access_count=0 that will be hygiene-archived at 30 days due to double-decay even though they would survive under single-decay.
**What to measure**: (1) Sample 7-20d active memory cohort. Compute importance / expected_single_decay_importance ratio. Compare to Q23.1 3-7d ratio of 0.793 (expect lower). (2) Measure fraction of 7-20d cohort with importance < 0.3. Compare to expected fraction under single-decay. (3) Count "double-decay inflation queue": active memories with age 15-30d, importance < 0.3, AND access_count = 0. These will be archived at 30 days via double-decay that would survive under single-decay. (4) Report what fraction of Q26.3 179.5 importance-units stolen comes from the 7-20d band vs floor-clamped cohort.
**Verdict threshold**:
- FAILURE: 7-20d importance/expected ratio < 0.5; or inflation queue > 500 memories
- WARNING: 7-20d ratio in 0.5-0.8 range; inflation queue 100-500 memories; measurable excess pre-hygiene eligibility
- HEALTHY: 7-20d ratio near 1.0 (Q22.1 fix deployed); inflation queue near 0
**Priority**: Tier 3 -- compound damage characterization; quantifies downstream hygiene inflation
**Derived from**: Q26.3 WARNING (7-20d band disproportionately affected; 179.5 importance-units stolen)

---

## Q27.4 [DOMAIN-1] Information recovery debt -- how many floor-clamped memories are permanently stuck vs recoverable if Q22.1 deployed today?
**Status**: DONE
**Wave**: 27
**Mode**: quantitative analysis
**Target**: Floor-clamped active memory cohort (importance <= 0.051); access_count, age, source distributions
**Hypothesis**: Q26.3 found 673 memories at the 0.05 floor (up from 632 at Q23.1). Decay can only reduce importance -- it cannot spontaneously restore it. Floor-clamped memories with access_count=0 and no active consolidation siblings have no natural recovery path. If Q22.1 were deployed today, these memories would stop losing importance (already at floor) but would not recover. Quantifying this "permanent loss" pool characterizes the remediation debt from 15 waves of unresolved double-decay.
**What to measure**: (1) Sample floor-clamped cohort (importance = 0.05, active). For each: access_count, age, source, estimate initial_importance. (2) Segment: (a) can recover via retrieval _track_access; (b) may recover via consolidation boost (has active siblings); (c) permanently stuck (access_count=0, no active siblings, age approaching 30d). (3) Report fraction in category (c) -- permanent information loss. (4) For category (c): how many will be hygiene-archived within 30 days?
**Verdict threshold**:
- FAILURE: > 500 floor-clamped memories permanently stuck; unrecoverable information loss
- WARNING: 200-500 permanently stuck; remainder have some recovery pathway
- HEALTHY: < 100 permanently stuck; Q22.1 fix deployment would prevent further damage with minimal sunk loss
**Priority**: Tier 3 -- remediation debt quantification
**Derived from**: Q26.3 WARNING (673 floor-clamped; 179.5 importance-units stolen); Q22.1 FAILURE (15 consecutive waves)

---

## Q27.5 [DOMAIN-4] Consolidation user_id deployment re-check (3rd attempt) -- has consolidation.py:235 been fixed?
**Status**: DONE
**Wave**: 27
**Mode**: static code analysis + observability
**Target**: src/core/consolidation.py:235 Memory() constructor; active null-uid consolidated memory count vs Q26.5 baseline of 1,833
**Hypothesis**: Q25.3 (FAILURE) and Q24.5 (FAILURE) confirmed consolidation.py:235 Memory() constructor missing user_id= argument. Q26.5 quantified the seed pool: 1,833 active consolidation-source memories with user_id=None. If deployed, new merged memories should have user_id propagated. The existing seed pool still creates re-accumulation risk until those memories are superseded.
**What to measure**: (1) Read consolidation.py:235 -- confirm whether user_id= argument is present. (2) If deployed: query recent merged memories (source=consolidation, created after fix date) -- do they have user_id set? (3) Update seed pool: active memories with source=consolidation AND user_id=None. Compare to Q26.5 baseline of 1,833. If fix deployed: count stable. If not: count grown by ~796/day * consolidation fraction * days_since_Q26.5. (4) Decay audit: GET /admin/audit?action=decay_run&limit=20 -- is proc=0 ghost count still 7 per slot?
**Verdict threshold**:
- FAILURE: consolidation.py:235 still lacks user_id=; seed pool growing beyond 1,833; fix not deployed (3rd consecutive wave)
- WARNING: Fix deployed; seed pool stable at ~1,833 (old seeds remain); co-deployment of Q21.5 required to eliminate current ghost users
- HEALTHY: consolidation.py:235 passes user_id= to Memory(); new merged memories have user_id; seed pool not growing
**Priority**: Tier 2 -- 3rd consecutive wave; co-deployment with Q21.5 required for permanent ghost user fix
**Derived from**: Q26.5 WARNING (1,833 seed pool; co-deployment required); Q25.3 FAILURE (2nd consecutive)

---

## Q27.6 [DOMAIN-5] Reconcile audit fix deployment re-check (3rd attempt) -- has log_audit() been added to reconcile.py and ops.py?
**Status**: DONE
**Wave**: 27
**Mode**: static code analysis + observability
**Target**: src/workers/reconcile.py; src/api/routes/ops.py (log_audit calls); GET /admin/audit?action=reconcile&limit=10
**Hypothesis**: Q26.7 (FAILURE) and Q24.8 (FAILURE) confirmed zero log_audit() calls in reconcile.py or ops.py. Q26.7 established reconcile is the ONLY scheduled maintenance worker with zero audit visibility. If Q21.6 fix (~9 LOC) was deployed, the next reconcile run should produce audit entries with action="reconcile" and fields for mismatch_count, repair_count, scan_duration.
**What to measure**: (1) Read reconcile.py and ops.py -- confirm whether log_audit() calls are present. (2) POST /admin/reconcile?dry_run=true then GET /admin/audit?action=reconcile&limit=10. Expect 0 if not deployed; >= 1 if deployed. (3) If entry exists: verify fields include mismatch_count, repair_count, scan_duration, qdrant_total (Q21.6 spec). (4) If not deployed: confirm 0 entries (3rd consecutive FAILURE). (5) Cross-check: GET /admin/audit?action=auto_archive&limit=10 -- hygiene entries from Q27.1 should exist, confirming audit infrastructure works.
**Verdict threshold**:
- FAILURE: reconcile.py and ops.py still lack log_audit() calls; GET /admin/audit?action=reconcile returns 0; fix not deployed (3rd consecutive wave)
- WARNING: log_audit() present in one file but not both; or entry exists but missing required fields
- HEALTHY: log_audit() confirmed in both files; at least 1 reconcile audit entry with all required fields; reconcile no longer sole audit-blind worker
**Priority**: Tier 1b -- 9-LOC fix; 3rd consecutive wave; asymmetric observability gap fully characterized
**Derived from**: Q26.7 FAILURE/NOTE (reconcile ONLY worker with zero audit visibility; 2nd consecutive); Q21.6 HEALTHY (9 LOC across 2 files)

---

## Q27.7 [DOMAIN-1] Hygiene archival rate projection -- will hygiene stabilize, reduce, or over-archive the active corpus under double-decay?
**Status**: DONE
**Wave**: 27
**Mode**: quantitative analysis (depends on Q27.1 for first batch data)
**Target**: Q27.1 archival count; active corpus age distribution; daily new memory rate; double-decay importance profiles for 15-30d cohort
**Hypothesis**: Q27.1 provides the first empirical hygiene batch size. At ~5,975 active memories and ~213 new memories/day (store + consolidation estimate), the corpus is currently growing. If hygiene archives more than new memories enter per day, the active corpus shrinks. The double-decay bug affects the 15-30d pipeline: memories with importance < 0.3 and access_count=0 in the 15-30d range will hit the hygiene gate at 30 days. Under single-decay, fewer would be below 0.3 at 30 days, so the double-decay bug inflates the ongoing daily archival pipeline.
**What to measure**: (1) From Q27.1: first batch size as reference for one cohort. (2) Pipeline query: active memories with age 15-30d, importance < 0.3, access_count = 0. This is the daily hygiene pipeline. Report count and estimate daily rate (count / 15 days average). (3) Compare daily new memories vs daily archival rate. Active corpus in growth, equilibrium, or decline? (4) Under double-decay vs single-decay: for 15-30d memories, what fraction have importance < 0.3? Excess quantifies ongoing inflation from bug. (5) 30-day projection under: (a) no fixes deployed; (b) Q22.1 deployed today.
**Verdict threshold**:
- FAILURE: Projected daily archival rate > 200/day (hygiene shrinking corpus > 1,000/week); or double-decay inflates ongoing archival by > 2x vs single-decay
- WARNING: Daily archival rate 50-200/day; active corpus in slow decline; double-decay adds 20-50% to ongoing archival rate
- HEALTHY: Daily archival rate < 50/day; active corpus stable or growing; double-decay has < 10% ongoing effect on daily archival
**Priority**: Tier 3 -- forward corpus health projection; depends on Q27.1 first batch data
**Derived from**: Q27.1 (first archival batch); Q26.3 WARNING (7-20d band disproportionately affected); Q22.1 FAILURE (15 waves)

---

## Q28.1 [DOMAIN-1] Hygiene first archival re-verification -- did the 2026-03-16T04:00 cron fire and archive the expected ~2 memories?
**Status**: INCONCLUSIVE
**Wave**: 28
**Mode**: observability
**Target**: GET /admin/audit?action=auto_archive&limit=20; active corpus count; superseded pool count
**Hypothesis**: Q27.1 was INCONCLUSIVE (measured ~17h before first cron run). Q27.7 corrected the re-verify target to 2026-03-16T04:00 UTC and projected the first batch at ~2 memories (25-27d cohort, importance<0.3, access=0). Wave 28 should catch the first audit entries if the cron has now fired.
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=20 -- are there now N>0 entries? (2) If entries exist: report count, timestamps, and importance distribution of archived memories. (3) Verify batch count matches Q27.7 projection (~2 for first batch; ~18 for Week 12 total). (4) Check active corpus count via GET /admin/stats -- has it decreased by batch size since Q27.7 baseline (6,005)? (5) Verify superseded pool unchanged (hygiene archives to superseded, not DETACH DELETE).
**Verdict threshold**:
- FAILURE: Still 0 entries after 2026-03-16T04:00 (hygiene cron not firing; instrumentation broken; or age>30d binding constraint still holds)
- INCONCLUSIVE: Measured before 2026-03-16T04:00 UTC (re-verify again)
- WARNING: Entries exist but count much larger than ~2 (>20 for first day) suggesting Q27.7 age distribution was wrong; or entries present but metadata missing
- HEALTHY: 1-5 entries consistent with Q27.7 ~2 projection; timing matches 04:00 UTC; soft-delete confirmed
**Priority**: TIME-SENSITIVE -- first run on/after 2026-03-16T04:00 UTC
**Derived from**: Q27.1 INCONCLUSIVE; Q27.7 WARNING (projection: ~2 first batch, 18 total Week 12)

---

## Q28.2 [DOMAIN-1] Double-decay fix deployment check (Wave 28) -- is Q22.1 finally deployed?
**Status**: DONE
**Wave**: 28
**Mode**: static code analysis + observability
**Target**: src/storage/qdrant.py:114 _user_conditions(); GET /admin/audit?action=decay_run&limit=20
**Hypothesis**: Q22.1 has been confirmed undeployed for 16 consecutive waves (Waves 12-27). The 3-line fix in _user_conditions() would eliminate double-decay: add MatchAny or IsNullCondition filter so system run only processes memories without user_id. Wave 28 begins with a mandatory deployment check.
**What to measure**: (1) Read qdrant.py:114 -- is _user_conditions(None) still returning []? Or does it now return a filter for user_id IS NULL? (2) GET /admin/audit?action=decay_run&limit=20 -- most recent 6h slot: 1 full-corpus proc entry (fixed) or still 2 full-corpus proc entries (double-decay)? (3) If deployed: is floor-clamped cohort (673 baseline) stabilizing? (4) If not deployed: 17th consecutive FAILURE confirmation.
**Verdict threshold**:
- FAILURE: _user_conditions(None) still returns []; most recent slot still shows 2 full-corpus proc entries; 17th consecutive FAILURE
- WARNING: Fix deployed in code but not yet observable in audit log; or partial fix
- HEALTHY: _user_conditions(None) returns non-empty filter; most recent slot shows 1 full-corpus proc + per-user entries; decay rate normalized
**Priority**: MANDATORY -- run before any other Wave 28 analysis
**Derived from**: Q22.1 FAILURE (16 consecutive waves); Q27.3 FAILURE (inflation queue 1,332)

---

## Q28.3 [DOMAIN-1] Double-decay archival count parity -- does the first hygiene batch size confirm Q27.7 correction?
**Status**: INCONCLUSIVE
**Wave**: 28
**Mode**: quantitative verification
**Target**: GET /admin/audit?action=auto_archive&limit=100; Q27.7 age-band projections
**Hypothesis**: Q27.7 asserted that double-decay does NOT inflate the 30-day archival COUNT because both single and double decay bring zero-access memories to the 0.05 floor within 10 days -- well before the 30-day gate. The first batch (~2 memories) should match this projection regardless of decay regime. If actual batch is much larger, Q27.7 correction needs re-examination.
**What to measure**: (1) From Q28.1: actual first batch count. (2) Compare to Q27.7 projection: Week 12 (Mar 17-21) = 18 total. If actual >50 for Week 12, Q27.7 correction needs re-examination. (3) Age distribution: are any memories <20d old in the archived cohort? (would indicate earlier archival under double-decay). (4) Importance distribution: are all archived memories near 0.05 floor (confirming both decay regimes converge before 30d gate)?
**Verdict threshold**:
- FAILURE: First week archival count >100 (Q27.7 projection was 18); or memories <20d old appear in archived cohort
- WARNING: First week count 19-100 (projection exceeded but not catastrophically); importance spread above floor
- HEALTHY: Week 12 count within 25% of Q27.7 projection (13-23 memories); all archived at importance near floor; Q27.7 parity correction CONFIRMED
**Priority**: Tier 2 -- depends on Q28.1 data; validates Q27.7 correction
**Derived from**: Q27.7 WARNING (double-decay does NOT inflate archival count); Q27.3 FAILURE (inflation queue 1,332)

---

## Q28.4 [DOMAIN-3] GC-eligible cohort at 2026-03-21 -- are superseded memories now crossing the 30-day threshold?
**Status**: INCONCLUSIVE
**Wave**: 28
**Mode**: observability + quantitative analysis
**Target**: Qdrant superseded pool (superseded_by IS NOT NULL AND invalid_at < now-30d); POST /admin/reconcile?dry_run=true
**Hypothesis**: Q27.2 corrected Q26.6: first GC-eligible date is 2026-03-21T19:12 UTC (oldest consolidation-source active memory = 2026-02-19T19:12). After 2026-03-21, a growing cohort crosses the 30-day invalid_at threshold and becomes eligible for DETACH DELETE. No automated GC cron exists (Q21.3 unimplemented). Wave 28 is the first wave where this cohort should be observable.
**What to measure**: (1) Query superseded pool for invalid_at < (now-30d) AND superseded_by IS NOT NULL: count. (2) Is count >0 (Q27.2 prediction: yes if after 2026-03-21T19:12)? (3) Has overall superseded pool (15,130 Wave 27 baseline) grown? (4) Reconcile scan time vs Q26.6 baseline of 5.94s for 21,105 points. (5) Confirm no automated GC ran (pool should only grow absent cron).
**Verdict threshold**:
- FAILURE: 0 GC-eligible after 2026-03-21T19:12 (Q27.2 correction was wrong -- 4th estimate failure)
- INCONCLUSIVE: Wave 28 measured before 2026-03-21T19:12 UTC (re-verify Wave 29)
- WARNING: GC-eligible cohort confirmed (10-500 memories); no automated GC; Q21.3 still unimplemented
- HEALTHY: GC cron deployed and running; superseded pool stabilizing
**Priority**: Tier 2 -- run on/after 2026-03-21T19:12 UTC; 3rd consecutive GC estimate verification
**Derived from**: Q27.2 WARNING (first GC-eligible date = 2026-03-21T19:12; 3rd consecutive estimate correction)

---

## Q28.5 [DOMAIN-4] Consolidation user_id fix deployment re-check (4th attempt) -- has consolidation.py:235 been fixed?
**Status**: DONE
**Wave**: 28
**Mode**: static code analysis + observability
**Target**: src/core/consolidation.py:235 Memory() constructor; src/storage/qdrant.py:1143 get_distinct_user_ids(); active null-uid consolidated memory count
**Hypothesis**: Q27.5 (3rd consecutive FAILURE) confirmed consolidation.py:235 Memory() constructor still lacks user_id= and qdrant.py:1143 still lacks IS NULL filter. Both fixes required for permanent ghost user elimination. Wave 28 is the 4th verification attempt.
**What to measure**: (1) Read consolidation.py:235-249 -- is user_id= now present in Memory() constructor? (2) Read qdrant.py:1143-1162 -- does get_distinct_user_ids() now have IS NULL filter? (3) If either fix deployed: query active memories with source=consolidation AND user_id=None -- count stable vs 1,833 baseline? (4) Decay audit: GET /admin/audit?action=decay_run&limit=20 -- proc=0 ghost count still 7 per slot?
**Verdict threshold**:
- FAILURE: consolidation.py:235 still missing user_id=; qdrant.py:1143 still lacks IS NULL filter; 4th consecutive FAILURE
- WARNING: One fix deployed but not both; ghost count reduced but re-accumulation path open
- HEALTHY: Both fixes deployed; new merged memories have user_id; ghost count near 0; seed pool stable
**Priority**: Tier 1 -- 4th consecutive wave; two linked fixes required together
**Derived from**: Q27.5 FAILURE (3rd consecutive); Q26.5 WARNING (1,833 seed pool; co-deployment required)

---

## Q28.6 [DOMAIN-5] Reconcile audit fix deployment re-check (4th attempt) -- has log_audit() been added to reconcile.py and ops.py?
**Status**: DONE
**Wave**: 28
**Mode**: static code analysis + observability
**Target**: src/workers/reconcile.py; src/api/routes/ops.py; GET /admin/audit?action=reconcile&limit=10
**Hypothesis**: Q27.6 (3rd consecutive FAILURE) confirmed 0 log_audit() calls in reconcile.py or ops.py. Reconcile remains the only scheduled maintenance worker with zero audit visibility. The Q21.6 9-LOC fix has been confirmed absent for 3 consecutive waves. Wave 28 is the 4th verification attempt.
**What to measure**: (1) Read reconcile.py -- is log_audit() present after reconcile completion? (2) Read ops.py -- is log_audit() present in the manual reconcile trigger? (3) POST /admin/reconcile?dry_run=false then GET /admin/audit?action=reconcile&limit=10 -- count >0? (4) If deployed: verify fields include mismatch_count, repair_count, scan_duration, qdrant_total. (5) Cross-check: GET /admin/audit?action=auto_archive -- entries from Q28.1 should exist (confirms audit infrastructure functioning).
**Verdict threshold**:
- FAILURE: 0 log_audit() in reconcile.py/ops.py; 0 reconcile audit entries; 4th consecutive FAILURE
- WARNING: log_audit() in one file but not both; or entry present but missing required fields
- HEALTHY: Both files have log_audit(); at least 1 reconcile audit entry with all required fields
**Priority**: Tier 1b -- 9-LOC fix; 4th consecutive wave
**Derived from**: Q27.6 FAILURE (3rd consecutive); Q26.7 FAILURE (reconcile sole audit blind spot)

---

## Q28.7 [DOMAIN-1] Hygiene Week 13 batch verification -- does the March 22-28 archival rate match Q27.7 projection (~128/day)?
**Status**: INCONCLUSIVE
**Wave**: 28
**Mode**: observability + quantitative analysis
**Target**: GET /admin/audit?action=auto_archive&limit=200; active corpus count; Q27.7 weekly projection
**Hypothesis**: Q27.7 projected weekly hygiene archival: Week 12 (Mar 17-21) = 18 total (~3/day); Week 13 (Mar 22-28) = 898 total (~128/day); Week 14 (Mar 29-Apr 4) = 1,550 total (~221/day, peak). By Wave 28, Week 12 should be complete and Week 13 may be in progress. The Week 13 rate is the first meaningful validation of the Q27.7 projection model.
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=200 -- cumulative count and daily rate trend. (2) Compare to Q27.7 projection by measurement date. (3) Active corpus count: has it decreased by archived count from 6,005 baseline? (4) Report actual-vs-projected ratio -- if >2x, Q27.7 double-decay non-inflation assertion needs revisiting. (5) Confirm archival rate accelerating toward ~128/day by end of Week 13.
**Verdict threshold**:
- FAILURE: Actual archival count >2x Q27.7 projection at same date (double-decay IS inflating count); or hygiene cron stopped firing
- WARNING: Actual count 1.25-2x projection; or corpus decline steeper than expected
- HEALTHY: Actual within 25% of Q27.7 projection; daily rate trend consistent with Week 13 estimate
**Priority**: Tier 3 -- depends on Q28.1 data; longitudinal validation of Q27.7 projection
**Derived from**: Q27.7 WARNING (3,289 pipeline; Wk12=18, Wk13=898, Wk14=1550; corpus shrinks Week 14)

---

## Wave 29 Questions

---

## Q29.1 [DOMAIN-1] Hygiene first archival confirmed? -- did the 2026-03-16T04:00 cron fire and archive the expected ~2 memories? (4th attempt)
**Status**: INCONCLUSIVE
**Wave**: 29
**Mode**: observability
**Target**: GET /admin/audit?action=auto_archive&limit=20; GET /admin/stats (active count vs 6,005 baseline)
**Hypothesis**: Q28.1 was INCONCLUSIVE -- 0 auto_archive entries at 2026-03-15T10:15 UTC, ~18h before target. Q26.1 and Q27.1 were also INCONCLUSIVE for the same reason. This is the 4th attempt. If the 2026-03-16T04:00 UTC cron fired, auto_archive entries should now be present. Expected: ~2 entries from the 25-27d cohort (importance<0.3, access=0, age>30d).
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=20 -- count >0? (2) If yes: report count, timestamps (match 04:00 UTC slot), details.archived, importance distribution. (3) Active corpus count -- decreased from 6,005 baseline by batch size? (4) If still 0: verify whether target time has passed; if yes, escalate to FAILURE (hygiene cron broken or age filter wrong). (5) Check: were any memories <20d old archived (would indicate importance filter archiving too aggressively under double-decay)?
**Verdict threshold**:
- FAILURE: Still 0 entries AND current time is after 2026-03-16T04:00 UTC (hygiene cron not firing; instrumentation broken; age filter wrong)
- INCONCLUSIVE: Current time still before 2026-03-16T04:00 UTC (re-verify again -- 4th consecutive)
- WARNING: Entries present but count much larger than ~2 (>20 for first batch) -- Q27.7 age projection was wrong
- HEALTHY: 1-5 entries consistent with Q27.7 ~2 projection; timing matches 04:00 UTC; active corpus decreased by batch size
**Priority**: TIME-SENSITIVE -- must run on/after 2026-03-16T04:00 UTC; 4th consecutive attempt
**Derived from**: Q28.1 INCONCLUSIVE (3rd consecutive); Q26.1/Q27.1 INCONCLUSIVE; Q27.7 WARNING (pipeline: 2 first batch, 18 Week 12)

---

## Q29.2 [DOMAIN-1] Double-decay fix deployment check (Wave 29) -- is Q22.1 finally deployed? (18th attempt)
**Status**: DONE
**Wave**: 29
**Mode**: static code analysis + observability
**Target**: src/storage/qdrant.py:114 _user_conditions(); GET /admin/audit?action=decay_run&limit=20 (check details.processed field)
**Hypothesis**: Q28.2 confirmed: _user_conditions(None) at qdrant.py:112-114 is unchanged (17th consecutive FAILURE); two full-corpus runs per slot (details.processed=6,002 each). Wave 29 is the 18th consecutive mandatory deployment check.
**What to measure**: (1) Read qdrant.py:112-114 -- is _user_conditions(None) still returning []? Or does it now return IsNullCondition? (2) GET /admin/audit?action=decay_run&limit=10 -- check details.processed for most recent slot: 1 entry (fixed) or 2 entries (still double-decay)? (3) If deployed: has floor-clamped count begun decreasing from 673 baseline (Q27.4)?
**Verdict threshold**:
- FAILURE: _user_conditions(None) returns []; most recent slot still shows 2 full-corpus entries; 18th consecutive FAILURE
- WARNING: Fix deployed in code but only 1 observable slot; or partial fix (e.g. returns filter but wrong key)
- HEALTHY: _user_conditions(None) returns non-empty filter; most recent slot shows 1 full-corpus entry; double-decay resolved
**Priority**: MANDATORY -- run before any other Wave 29 analysis
**Derived from**: Q28.2 FAILURE (17th consecutive); Q22.1 root cause (Waves 12-28 unresolved)

---

## Q29.3 [DOMAIN-1] Hygiene Week 12 cumulative archival -- did the 18 projected Week 12 archives (Mar 17-21) occur? (depends on Q29.1)
**Status**: INCONCLUSIVE
**Wave**: 29
**Mode**: observability + quantitative verification
**Target**: GET /admin/audit?action=auto_archive&limit=100; Q27.7 Week 12 projection (Mar 17-21, ~18 total, ~3/day)
**Hypothesis**: Q27.7 projected Week 12 (Mar 17-21) archival at ~18 total (~3/day). If Q29.1 confirms the first batch fired, Wave 29 can now verify the full Week 12 cumulative count. This also serves as the Q28.3 empirical parity check: if actual matches projection (~18), Q27.7's assertion that double-decay does NOT inflate 30d archival count is empirically confirmed.
**What to measure**: (1) From Q29.1: was the first batch (2026-03-16T04:00) confirmed? (2) Total auto_archive audit entries to date -- does cumulative count match Week 12 projection (~18 for 5-day window)? (3) Daily rate trend: growing from ~2/day (Week 12 start) toward Week 13 peak of ~128/day? (4) Compare actual vs Q27.7 projection ratio -- within 25% = HEALTHY; >2x = Q27.7 correction needed.
**Verdict threshold**:
- FAILURE: Week 12 actual count >36 (>2x projection of 18) -- double-decay IS inflating count; Q27.7 correction was wrong
- WARNING: Week 12 actual count 19-36 (1.05-2x projection); or hygiene cron missed some days
- HEALTHY: Week 12 actual count 13-23 (within 25% of 18 projection); Q27.7 archival count parity CONFIRMED empirically
- INCONCLUSIVE: Q29.1 prerequisite not met (hygiene not yet confirmed operational)
**Priority**: Tier 2 -- depends on Q29.1; empirically validates Q27.7 parity correction (Q28.3 follow-up)
**Derived from**: Q28.3 INCONCLUSIVE; Q27.7 WARNING (Wk12=18, Wk13=898, Wk14=1550)

---

## Q29.4 [DOMAIN-4] Consolidation user_id fix deployment re-check (5th attempt) -- has consolidation.py:235 been fixed?
**Status**: DONE
**Wave**: 29
**Mode**: static code analysis
**Target**: src/core/consolidation.py:235 Memory() constructor; src/storage/qdrant.py:1143 get_distinct_user_ids()
**Hypothesis**: Q28.5 (4th consecutive FAILURE) confirmed both fixes still absent. Wave 29 is the 5th verification attempt. The 1-line fix (user_id=user_id, in Memory() constructor at line 235) and the IS NULL filter in get_distinct_user_ids() remain the simplest undeployed fixes in the system.
**What to measure**: (1) Read consolidation.py:235-249 -- is user_id= now present in Memory() constructor? (2) Read qdrant.py:1143-1162 -- does get_distinct_user_ids() now have IS NULL filter in the scroll? (3) If either fix deployed: query active memories with source=consolidation AND user_id=None -- count stable vs 1,833 baseline?
**Verdict threshold**:
- FAILURE: consolidation.py:235 still missing user_id=; qdrant.py:1143 still lacks IS NULL filter; 5th consecutive FAILURE
- WARNING: One fix deployed but not both; ghost count reduced but re-accumulation path still open
- HEALTHY: Both fixes deployed; new merged memories have user_id; ghost count stable or decreasing
**Priority**: Tier 1 -- 5th consecutive wave; two linked fixes required together
**Derived from**: Q28.5 FAILURE (4th consecutive); Q26.5 WARNING (co-deployment required)

---

## Q29.5 [DOMAIN-5] Reconcile audit fix deployment re-check (5th attempt) -- has log_audit() been added to reconcile.py and ops.py?
**Status**: DONE
**Wave**: 29
**Mode**: static code analysis + observability
**Target**: src/workers/reconcile.py; src/api/routes/ops.py; GET /admin/audit?action=reconcile&limit=10
**Hypothesis**: Q28.6 (4th consecutive FAILURE) confirmed 0 log_audit() calls in reconcile.py or ops.py. Wave 29 is the 5th verification attempt. Reconcile remains the only scheduled maintenance worker with zero audit visibility.
**What to measure**: (1) Read reconcile.py -- is log_audit() present after reconcile completion? (2) Read ops.py -- is log_audit() present in the manual reconcile trigger? (3) POST /admin/reconcile?dry_run=false then GET /admin/audit?action=reconcile&limit=10 -- count >0? (4) Cross-check: GET /admin/audit?action=auto_archive -- entries should now exist if Q29.1 confirmed hygiene fired.
**Verdict threshold**:
- FAILURE: 0 log_audit() in reconcile.py/ops.py; 0 reconcile audit entries; 5th consecutive FAILURE
- WARNING: log_audit() in one file but not both; or entry present but missing required fields
- HEALTHY: Both files have log_audit(); at least 1 reconcile audit entry with all required fields
**Priority**: Tier 1b -- 9-LOC fix; 5th consecutive wave
**Derived from**: Q28.6 FAILURE (4th consecutive); Q21.6 9-LOC fix undeployed

---

## Q29.6 [DOMAIN-1] Double-decay floor accumulation -- has the floor-clamped count grown above Q27.4 baseline of 673?
**Status**: DONE
**Wave**: 29
**Mode**: quantitative analysis
**Target**: Active memories with importance <= 0.051 (floor) and access_count=0 across all source categories
**Hypothesis**: Q27.4 measured 673 total floor-clamped memories (Cat-C=432 permanently stuck, Cat-B=234, Cat-A=7). At ~10 new floor-clamped/day under double-decay, the count should have grown by ~40-50 since Q27.4 measurement (~4-5 days elapsed). Q28.2 confirmed double-decay is still active. This question tracks the accumulation trajectory.
**What to measure**: (1) Count active memories with importance <= 0.051 AND access_count=0 -- total and by source category. (2) Compare to Q27.4 baseline: Cat-C=432 permanently stuck, Cat-B=234, Cat-A=7, total=673. (3) Daily growth rate: (current_total - 673) / days_since_Q27.4. (4) Are any Cat-C memories being archived (would reduce count)? First Cat-C archival due ~April 7 (23 days from Q27.4 measurement). (5) If Q29.2 confirms double-decay still active: project when floor count will begin decreasing (only after hygiene archives Cat-C members AND double-decay fix deployed).
**Verdict threshold**:
- FAILURE: Floor-clamped count > 800 (>19% growth from 673 baseline; suggests accelerating accumulation)
- WARNING: Count 674-800 (growing at expected ~10/day; consistent with ongoing double-decay; Cat-C not yet archived)
- HEALTHY: Count decreasing from 673 (would require double-decay fix deployed AND hygiene archiving Cat-C)
**Priority**: Tier 2 -- tracks double-decay compound damage; depends on Q29.2 deployment status
**Derived from**: Q27.4 WARNING (673 floor-clamped, 432 Cat-C permanently stuck); Q28.2 FAILURE (17th consecutive)

---

## Q29.7 [DOMAIN-3] Superseded pool growth rate -- has the 15,130 baseline grown as expected? (verify Q28.4 pre-condition)
**Status**: DONE
**Wave**: 29
**Mode**: observability
**Target**: GET /admin/stats (superseded count); total Qdrant points
**Hypothesis**: Q27.2 measured superseded pool at 15,130 (~4 days ago). At ~796 new superseded/day (from consolidation rate), the pool should now be at ~18,314 (15,130 + 4 * 796). Q28.4 (GC-eligible at 2026-03-21T19:12) requires this pool to be growing. This question verifies growth is occurring as expected and provides the pre-condition state for Q28.4 re-verification on 2026-03-21.
**What to measure**: (1) GET /admin/stats -- current superseded count. (2) Growth since Q27.2 baseline (15,130): actual vs expected (796/day * days_elapsed). (3) Total Qdrant points: active + superseded should match. (4) Confirm 0 GC-eligible today (before 2026-03-21T19:12 UTC). (5) Note: GC eligibility threshold crosses at 2026-03-21T19:12 -- verify current time and confirm Wave 30 should be the first wave to observe GC-eligible memories.
**Verdict threshold**:
- FAILURE: Superseded count unchanged or decreasing (GC running without authorization; or consolidation stopped)
- WARNING: Growth rate significantly different from 796/day baseline (consolidation rate changed)
- HEALTHY: Pool growing at ~796/day; total consistent with active + superseded accounting; 0 GC-eligible (before 2026-03-21T19:12)
**Priority**: Tier 2 -- pre-condition verification for Q28.4 re-verify on 2026-03-21
**Derived from**: Q28.4 INCONCLUSIVE; Q27.2 WARNING (superseded 15,130; GC-eligible date 2026-03-21T19:12 UTC)

---

## Wave 30 Questions

---

## Q30.1 [DOMAIN-1] Hygiene first archival CONFIRMED or FAILED? -- did the 2026-03-16T04:00 UTC cron fire? (5th attempt; escalation trigger)
**Status**: INCONCLUSIVE
**Wave**: 30
**Mode**: observability
**Target**: GET /admin/audit?action=auto_archive&limit=20; active corpus count vs 6,017 baseline
**Hypothesis**: Q29.1 was INCONCLUSIVE (4th consecutive) -- 0 auto_archive entries at 2026-03-15T10:35 UTC, ~17.4h before the target. This is the 5th attempt. Per Q29.1 verdict threshold: if current time is AFTER 2026-03-16T04:00 UTC and auto_archive count is still 0, escalate to FAILURE. Wave 30 is the first wave that CAN achieve a non-INCONCLUSIVE verdict on hygiene first archival.
**What to measure**: (1) GET /admin/audit?action=auto_archive&limit=100 -- count >0? (2) If yes: report timestamps (match 04:00 UTC slot), details.archived, importance distribution; active corpus count vs 6,017. (3) If still 0 AND current time > 2026-03-16T04:00 UTC: FAILURE -- hygiene cron not firing or age filter wrong. (4) If still 0 AND current time < 2026-03-16T04:00 UTC: INCONCLUSIVE (5th) -- still timing-blocked.
**Verdict threshold**:
- FAILURE: 0 entries AND current time > 2026-03-16T04:00 UTC (hygiene cron broken; age filter misconfigured; audit instrumentation missing)
- INCONCLUSIVE: Current time still before 2026-03-16T04:00 UTC (5th consecutive -- should not happen in Wave 30)
- WARNING: Entries present but count much larger than ~2 (>20 for first batch -- Q27.7 age projection wrong)
- HEALTHY: 1-5 entries consistent with Q27.7 ~2 projection; timing matches 04:00 UTC slot; active corpus decreased
**Priority**: TIME-SENSITIVE -- CRITICAL ESCALATION POINT; first wave that can confirm FAILURE if cron is broken
**Derived from**: Q29.1 INCONCLUSIVE (4th consecutive); Q27.7 WARNING (first batch 2 memories)

---

## Q30.2 [DOMAIN-1] Double-decay fix deployment check (Wave 30) -- is Q22.1 finally deployed? (19th attempt)
**Status**: DONE
**Wave**: 30
**Mode**: static code analysis + observability
**Target**: src/storage/qdrant.py:114 _user_conditions(); GET /admin/audit?action=decay_run&limit=10
**Hypothesis**: Q29.2 confirmed _user_conditions(None) returns [] (18th consecutive FAILURE). Wave 30 is the 19th consecutive mandatory deployment check. The 941 floor-clamped count (Q29.6 FAILURE) provides new urgency -- every wave the fix is undeployed, floor-clamped accumulation continues.
**What to measure**: (1) Read qdrant.py:106-114 -- is _user_conditions(None) still returning []? (2) GET /admin/audit?action=decay_run&limit=10 -- check details.processed: still 6,002 per slot (FAILURE) or reduced? (3) If deployed: re-run Q29.6 floor-clamped count -- has 941 stabilized or begun declining?
**Verdict threshold**:
- FAILURE: _user_conditions(None) returns []; 19th consecutive FAILURE
- WARNING: Fix deployed in code but only 1 observable slot; or partial fix
- HEALTHY: _user_conditions(None) returns non-empty filter; single-pass per slot confirmed
**Priority**: MANDATORY -- run before any other Wave 30 analysis
**Derived from**: Q29.2 FAILURE (18th consecutive); Q29.6 FAILURE (floor-clamped 941 directly linked)

---

## Q30.3 [DOMAIN-5] Importance mismatch trend -- are the 179 Qdrant vs Neo4j mismatches growing, stable, or shrinking?
**Status**: DONE
**Wave**: 30
**Mode**: observability
**Target**: POST /admin/reconcile; importance_mismatches field; compare to Q29.7 baseline of 179
**Hypothesis**: Q29.5 and Q29.7 both surfaced a new anomaly: 179 memories have importance stored in Qdrant but Neo4j reports 0.0. The reconcile endpoint detects these but repairs_applied=0 (does not auto-repair). Without audit logging (Q29.5 FAILURE), historical trend is unknowable. Wave 30 can establish whether this count is growing, stable, or shrinking.
**What to measure**: (1) POST /admin/reconcile -- record importance_mismatches count. (2) Compare to Q29.7 baseline of 179: growing/stable/shrinking? (3) Are any of the 179 mismatch IDs the same as prior waves (stable set) or all new? (4) Cross-check: do these 179 memories appear in active export with non-zero importance? (5) Is there a repair mechanism that should be fixing these automatically?
**Verdict threshold**:
- FAILURE: importance_mismatches > 200 (growing; active defect creating new mismatches faster than repair)
- WARNING: 150-200 mismatches (stable or slow growth; historical artifact)
- HEALTHY: < 50 mismatches (shrinking; self-healing mechanism exists or manual repair ran)
**Priority**: Tier 2 -- new anomaly from Q29.5/Q29.7; baseline needed for trend analysis
**Derived from**: Q29.5 FAILURE (new: 179 mismatches detected, repairs_applied=0); Q29.7 WARNING (same anomaly)

---

## Q30.4 [DOMAIN-4] Consolidation user_id fix deployment re-check (6th attempt) -- has consolidation.py:235 been fixed?
**Status**: DONE
**Wave**: 30
**Mode**: static code analysis
**Target**: src/core/consolidation.py:235 Memory() constructor; src/storage/qdrant.py:1143 get_distinct_user_ids()
**Hypothesis**: Q29.4 (5th consecutive FAILURE) confirmed both fixes still absent. Wave 30 is the 6th verification attempt. Q29.6 FAILURE (941 floor-clamped, consolidation source 7->375) provides direct measurement of the bug impact.
**What to measure**: (1) Read consolidation.py:235-249 -- is user_id= now present in Memory() constructor? (2) Read qdrant.py:1143-1162 -- does get_distinct_user_ids() now have IS NULL filter? (3) If either fix deployed: run floor-clamped count analysis (Q29.6 methodology) -- is consolidation-source count stabilizing?
**Verdict threshold**:
- FAILURE: consolidation.py:235 still missing user_id=; qdrant.py:1143 still lacks IS NULL filter; 6th consecutive FAILURE
- WARNING: One fix deployed but not both
- HEALTHY: Both fixes deployed; new merged memories have user_id
**Priority**: Tier 1 -- 6th consecutive wave; direct link to Q30.6 floor-clamped count
**Derived from**: Q29.4 FAILURE (5th consecutive); Q29.6 FAILURE (941 floor-clamped, consolidation spike 7->375)

---

## Q30.5 [DOMAIN-5] Reconcile audit fix deployment re-check (6th attempt) -- has log_audit() been added to reconcile.py and ops.py?
**Status**: DONE
**Wave**: 30
**Mode**: static code analysis + observability
**Target**: src/workers/reconcile.py; src/api/routes/ops.py; GET /admin/audit?action=reconcile&limit=10
**Hypothesis**: Q29.5 (5th consecutive FAILURE) confirmed 0 log_audit() calls. Wave 30 is the 6th verification attempt. New urgency: without audit logging, the 179 importance mismatch trend (Q30.3) cannot be tracked over time.
**What to measure**: (1) Read reconcile.py -- is log_audit() present? (2) Read ops.py -- is log_audit() present? (3) POST /admin/reconcile then GET /admin/audit?action=reconcile&limit=10 -- count >0? (4) If deployed: check if reconcile entries include importance_mismatches count -- enabling Q30.3 trend analysis automatically.
**Verdict threshold**:
- FAILURE: 0 log_audit() in reconcile.py/ops.py; 0 reconcile audit entries; 6th consecutive FAILURE
- WARNING: log_audit() in one file but not both
- HEALTHY: Both files have log_audit(); at least 1 reconcile audit entry with mismatch counts
**Priority**: Tier 1b -- 9-LOC fix; 6th consecutive wave; blocks Q30.3 trend analysis
**Derived from**: Q29.5 FAILURE (5th consecutive); 179 importance_mismatches need audit trail for trend analysis

---

## Q30.6 [DOMAIN-1] Floor-clamped count trajectory -- has 941 (Q29.6 FAILURE) grown further or stabilized?
**Status**: DONE
**Wave**: 30
**Mode**: quantitative analysis
**Target**: Active memories with importance <= 0.051 and access_count=0; compare to Q29.6 baseline of 941
**Hypothesis**: Q29.6 measured 941 floor-clamped (FAILURE threshold 800). If Q30.2 confirms double-decay still active and Q30.4 confirms consolidation user_id fix still absent, the count should be growing. If hygiene first archival fired (Q30.1), some of the oldest floor-clamped members may have been archived, potentially reducing the count.
**What to measure**: (1) Download admin/export and count importance<=0.051 by source (same Q29.6 methodology). (2) Compare to Q29.6: system=547, consolidation=375, pattern=16, user=3, total=941. (3) Cross-check: if Q30.1 confirms hygiene fired, how many floor-clamped memories were archived? (4) Identify if consolidation-source count (375) is still growing.
**Verdict threshold**:
- FAILURE: Floor-clamped count > 941 (still growing; no fixes deployed, no hygiene archival reducing it)
- WARNING: Count 800-941 (hygiene beginning to offset new accumulation; or growth slowing)
- HEALTHY: Count < 800 (fixes deployed and/or hygiene archival significantly reducing accumulation)
**Priority**: Tier 2 -- direct compound damage measurement; depends on Q30.1/Q30.2/Q30.4 status
**Derived from**: Q29.6 FAILURE (941 vs 673 Q27.4 baseline); Q30.1 hygiene archival timing

---

## Q30.7 [DOMAIN-3] GC-eligible cohort size at 2026-03-21T19:12 UTC -- has the first GC run fired? (Q28.4 re-verify)
**Status**: INCONCLUSIVE
**Wave**: 30
**Mode**: observability
**Target**: POST /admin/reconcile (superseded count); GET /admin/audit?action=gc_run&limit=10; Qdrant total points
**Hypothesis**: Q28.4 was INCONCLUSIVE -- GC eligibility date 2026-03-21T19:12 UTC was 6 days away. Q29.7 confirmed superseded pool at 15,185. If Wave 30 runs on or after 2026-03-21T19:12, the first GC-eligible cohort has arrived. Q21.3 noted no automated GC cron exists; the eligible pool may accumulate without removal.
**What to measure**: (1) Current time: is it after 2026-03-21T19:12 UTC? If not, INCONCLUSIVE. (2) If after: GET /admin/audit?action=gc_run&limit=10 -- has any GC run? (3) POST /admin/reconcile -- superseded count vs 15,185 Q29.7 baseline; has it decreased (GC fired) or increased (no GC)? (4) Estimate GC-eligible pool: superseded memories with updated_at < (now - 30d). (5) If 0 gc_run audit entries: confirm no automated GC cron exists; quantify the eligible-but-undeleted backlog.
**Verdict threshold**:
- FAILURE: 0 gc_run entries AND GC-eligible pool > 0 after 2026-03-21T19:12 UTC (no GC scheduled; backlog growing)
- WARNING: GC eligible pool present but small (<100); gc_run entries present (manual GC ran)
- HEALTHY: gc_run entries present; superseded count decreased; eligibility window working as expected
- INCONCLUSIVE: Current time before 2026-03-21T19:12 UTC
**Priority**: Tier 2 -- time-gated; run on/after 2026-03-21T19:12 UTC
**Derived from**: Q28.4 INCONCLUSIVE; Q29.7 WARNING (superseded 15,185); Q21.3 WARNING (no GC cron)

---

## Wave 31 Questions — Post-Fix Verification

---

## Q31.1 [DOMAIN-2] Hygiene first archival -- has the mandatory FAILURE escalation finally fired?
**Status**: DONE
**Wave**: 31
**Mode**: observability
**Target**: GET /admin/audit?action=hygiene_run&limit=5; GET /admin/audit?action=archive&limit=20
**Hypothesis**: Q30.1 was FAILURE (6th consecutive miss; last confirmed run 2026-03-09). The hygiene cron targets 4:00am UTC daily. As of Wave 31 (2026-03-15+), at least 6 more windows have passed. Either the cron is broken (no runs at all) or archival is running but producing 0 results (archive entries absent). This is the highest-priority open issue.
**What to measure**: (1) GET /admin/audit?action=hygiene_run&limit=5 -- any entries after 2026-03-09? Record timestamps. (2) GET /admin/audit?action=archive&limit=20 -- any entries? (3) If hygiene_run entries present but no archive entries: hygiene is running but not archiving (threshold config issue). (4) If no hygiene_run entries at all: cron not firing; check ARQ worker logs. (5) Compare floor-clamped count (Q31.3) to Q30.6 baseline as indirect signal.
**Verdict threshold**:
- FAILURE: No hygiene_run audit entries after 2026-03-09 (cron still broken; 7th+ consecutive miss)
- WARNING: hygiene_run entries present but 0 archive entries (running but not archiving)
- HEALTHY: hygiene_run entries present AND archive entries present (archival confirmed working)
**Priority**: Tier 0 -- 6 consecutive FAILUREs; highest priority in Wave 31
**Derived from**: Q30.1 FAILURE (6th miss); Q29.1 FAILURE; Q28.1 FAILURE; Q27.1 FAILURE

---

## Q31.2 [DOMAIN-1] Double-decay fix VERIFIED -- has processed count per decay slot halved?
**Status**: DONE
**Wave**: 31
**Mode**: quantitative analysis
**Target**: GET /admin/audit?action=decay_run&limit=10; decay log output from ARQ worker
**Hypothesis**: Q22.1 identified the double-decay bug: _user_conditions(None) returned [] causing system decay to process ALL memories, then per-user passes processed them again. The fix (user_id=0 sentinel) was deployed in this session. If working correctly, total memories processed per decay slot should be roughly half the Q30.3 baseline (which measured the doubled count). The decay_run audit entries should show a per_user breakdown with no system=all overlap.
**What to measure**: (1) GET /admin/audit?action=decay_run&limit=10 -- compare processed counts to Q30.3 baseline. (2) If decay has run since deployment: calculate ratio (new count / Q30.3 count); expect ~0.5. (3) Check for any decay_error entries indicating the sentinel fix broke something. (4) If decay has not run since deployment (cron fires at 0:15/6:15/12:15/18:15 UTC): note time elapsed and mark INCONCLUSIVE.
**Verdict threshold**:
- FAILURE: Processed count unchanged from Q30.3 baseline (fix did not deploy or is not working)
- WARNING: Processed count reduced but not by ~50% (partial fix or other decay source)
- HEALTHY: Processed count reduced by ~40-60% from Q30.3 baseline (double-decay eliminated)
- INCONCLUSIVE: No decay_run entries since deployment timestamp
**Priority**: Tier 1 -- direct verification of the highest-impact fix deployed this session
**Derived from**: Q22.1 FAILURE (double-decay); Q30.3 (decay baseline measurement)

---

## Q31.3 [DOMAIN-1] Floor-clamped count post-fix -- is the 941 FAILURE count declining?
**Status**: DONE
**Wave**: 31
**Mode**: quantitative analysis
**Target**: GET /admin/export (all memories); filter importance <= 0.051 AND access_count = 0
**Hypothesis**: Q30.6 measured 941 floor-clamped memories (FAILURE threshold 800). Three fixes were deployed this session that should reduce new accumulation: (1) double-decay fix stops over-decaying system memories, (2) consolidation user_id fix stops stranding merged memories at floor, (3) hygiene archival (if finally working) removes oldest floor-clamped members. The count should be declining or at minimum stable.
**What to measure**: (1) Download admin/export; count importance<=0.051 by source (same Q30.6 methodology). (2) Compare to Q30.6: system=547, consolidation=375, pattern=16, user=3, total=941. (3) Breakdown by source: which category changed most? (4) Cross-reference with Q31.1 (hygiene archival) and Q31.2 (double-decay) results for causal attribution.
**Verdict threshold**:
- FAILURE: Floor-clamped count > 941 (fixes not working; accumulation continuing)
- WARNING: Count 800-941 (stabilized but not yet declining; fixes deployed but not enough time elapsed)
- HEALTHY: Count < 800 (declining; at least one fix is reducing accumulation)
**Priority**: Tier 1 -- compound damage measurement; lagging indicator for Q31.1 + Q31.2
**Derived from**: Q30.6 FAILURE (941); Q22.1 double-decay fix; Q24.5 consolidation user_id fix

---

## Q31.4 [DOMAIN-3] Reconcile audit trail WORKING -- are entries now appearing in audit_log?
**Status**: DONE
**Wave**: 31
**Mode**: observability
**Target**: GET /admin/audit?action=reconcile_run&limit=5; POST /admin/reconcile (trigger manual run)
**Hypothesis**: Q21.6 and Q24.8 both found FAILURE: no audit entries for reconcile runs. The fix (log_audit() added to both reconcile.py and ops.py) was deployed this session. The weekly reconcile cron fires Sunday 5:30am UTC; a manual POST /admin/reconcile can verify immediately without waiting.
**What to measure**: (1) POST /admin/reconcile to trigger a run. (2) GET /admin/audit?action=reconcile_run&limit=5 -- any entries? (3) Verify entry contains expected fields: action=reconcile_run, actor=reconcile, details with qdrant_only/neo4j_only counts. (4) Check GET /admin/audit?action=reconcile_op&limit=20 for per-orphan entries if any orphans were repaired. (5) Confirm no exception in the reconcile response body.
**Verdict threshold**:
- FAILURE: No reconcile_run audit entries after manual trigger (fix did not deploy or log_audit call is erroring silently)
- WARNING: reconcile_run entry present but missing expected detail fields (partial audit)
- HEALTHY: reconcile_run entry present with full details (qdrant_only, neo4j_only counts)
**Priority**: Tier 1 -- verifies the ops.py audit fix; can be tested immediately without waiting for cron
**Derived from**: Q24.8 FAILURE (no reconcile audit); Q21.6 FAILURE (same); fix deployed this session

---

## Q31.5 [DOMAIN-3] Importance mismatch drain -- did the Sunday reconcile repair the 179 mismatches?
**Status**: DONE
**Wave**: 31
**Mode**: quantitative analysis
**Target**: POST /admin/reconcile (trigger); check response body for importance_mismatch count; compare to Q29.5 baseline of 179
**Hypothesis**: Q29.5 measured 179 importance mismatches (Qdrant importance != Neo4j importance). The root cause was mark_superseded() setting importance=0.0 in Neo4j while Qdrant retained the original value. The fix (removing m.importance=0.0 from the Cypher query) was deployed this session. Reconcile repairs existing mismatches when it runs; if the weekly Sunday cron fired since deployment, mismatches should be lower. If not yet, triggering manual reconcile now will repair them.
**What to measure**: (1) POST /admin/reconcile -- note importance_mismatch count in response. (2) Compare to Q29.5 baseline (179). (3) If mismatches are still 179: reconcile has not run since fix deployment; trigger it manually and recheck. (4) If mismatches are 0 or near 0: fix + reconcile has repaired the backlog. (5) Monitor whether new mismatches accumulate in the next wave (should be 0 new ones with the mark_superseded fix).
**Verdict threshold**:
- FAILURE: importance_mismatch count still near 179 AND reconcile has been run (fix not working)
- WARNING: importance_mismatch count reduced but not 0 (partial repair; some edge case remaining)
- HEALTHY: importance_mismatch count at 0 or near 0 after reconcile run (fix + repair working)
**Priority**: Tier 1 -- direct verification of neo4j_store.py mark_superseded fix
**Derived from**: Q29.5 FAILURE (179 mismatches); mark_superseded importance=0.0 fix deployed this session

---

## Q31.6 [DOMAIN-3] GC cron registered and first eligible cohort -- did GC run after 2026-03-21T19:12 UTC?
**Status**: INCONCLUSIVE
**Wave**: 31
**Mode**: observability
**Target**: GET /admin/audit?action=gc_run&limit=5; GET /admin/audit?action=gc_delete&limit=10; POST /admin/reconcile (superseded count)
**Hypothesis**: Q30.7 was INCONCLUSIVE because 2026-03-21T19:12 UTC was in the future. The GC cron (run_gc, daily 5:00am UTC) was deployed this session and registered in WorkerSettings. Wave 31 runs on 2026-03-15; the first eligible cohort arrives 2026-03-21. If Wave 31 runs before that date, this is INCONCLUSIVE again. If after, check whether gc_run audit entries exist.
**What to measure**: (1) Check current date against 2026-03-21T19:12 UTC. If before: INCONCLUSIVE. (2) If after: GET /admin/audit?action=gc_run&limit=5 -- any entries? (3) GET /admin/audit?action=gc_delete&limit=10 -- any individual deletions? (4) POST /admin/reconcile -- has superseded count decreased from Q30.7 baseline (15,185+)? (5) If no gc_run entries: confirm GC worker is deployed and ARQ worker restarted after deployment.
**Verdict threshold**:
- FAILURE: After 2026-03-21 -- no gc_run entries AND superseded count still growing (GC not deployed or not running)
- WARNING: gc_run entries present but gc_delete count = 0 (GC ran but found no eligible candidates; possible cutoff logic issue)
- HEALTHY: gc_run entries present AND gc_delete count > 0 (GC running and deleting eligible memories)
- INCONCLUSIVE: Current date before 2026-03-21T19:12 UTC
**Priority**: Tier 2 -- time-gated; only actionable after 2026-03-21
**Derived from**: Q30.7 INCONCLUSIVE; Q21.3 WARNING (no GC cron); GC worker deployed this session

---

## Q31.7 [DOMAIN-4] LLM per-call timeout tiers DEPLOYED -- are all 17 callsites updated?
**Status**: DONE
**Wave**: 31
**Mode**: observability
**Target**: Source code audit of all LLM generate() callsites; grep for timeout= parameter
**Hypothesis**: Q15.3 and Q16.3 identified that generate() had no per-call timeout, allowing a single slow Ollama call to hold a semaphore slot for up to 180s. Timeout tiers were deployed this session: 15s (signal_detector, search), 30s (observer, state_fact_extractor, admin), 60s (causal_extractor, contradiction_detector, document_ingest, fact_extractor), 90s (consolidation, patterns, cognitive_distiller, dream_consolidation, profile_drift). All 17 callsites should now have explicit timeout= parameters.
**What to measure**: (1) Grep all Python files for llm.generate( or await llm.generate( calls. (2) For each call: does it include timeout=N? (3) Count callsites with timeout vs without. (4) Verify the llm.py generate() signature accepts timeout= and passes it to client.post(). (5) Check for any generate() calls added after this session that may be missing the timeout.
**Verdict threshold**:
- FAILURE: Any generate() callsite missing timeout= parameter (partial deployment; worst-case 180s still possible)
- WARNING: All callsites have timeout= but values are inconsistent with the tier spec (wrong tier assigned)
- HEALTHY: All 17 callsites have timeout= matching their assigned tier; llm.py signature confirmed
**Priority**: Tier 1 -- verifies LLM timeout deployment; can be checked via static grep without running the system
**Derived from**: Q15.3 FAILURE (no timeout); Q16.3 FAILURE (semaphore starvation); timeout tiers deployed this session

---

## Wave 32 Questions — Cron Verification, Rate Measurement, and Damage Characterization

---

## Q32.1 [DOMAIN-2] Hygiene cron — did the 2026-03-16T04:00 UTC window finally fire?
**Status**: PENDING
**Wave**: 32
**Mode**: observability
**Target**: GET /admin/audit?action=hygiene_run&limit=5; GET /admin/audit?action=archive&limit=20
**Hypothesis**: Q31.1 confirmed FAILURE (7th+ miss): the 2026-03-15T04:00 UTC window passed with zero hygiene_run entries; last confirmed run was 2026-03-09. The next window is 2026-03-16T04:00 UTC. Wave 32 runs after that window. Either (a) the cron finally fired and archived the first cohort (expected ~2 memories, then rapidly scaling as the Feb 14+ cohort crosses 30d), or (b) the cron remains broken (8th+ consecutive miss, indicating the ARQ task registration is structurally broken, not a transient failure).
**What to measure**: (1) GET /admin/audit?action=hygiene_run&limit=5 — any entries with timestamps after 2026-03-16T04:00 UTC? (2) GET /admin/audit?action=archive&limit=20 — any archive entries? Count them and note timestamps. (3) If hygiene_run present but archive=0: cron fires but archival threshold not being met (threshold config issue or date math bug in the candidate query). (4) If no hygiene_run entries: cron is still broken; investigate ARQ worker task list (check WorkerSettings.functions includes hygiene_task). (5) Cross-reference with Q32.4 floor-clamped count — archival should be visible as a reduction in floor-clamped members.
**Verdict threshold**:
- FAILURE: No hygiene_run audit entries after 2026-03-16T04:00 UTC (8th+ consecutive miss; cron structurally broken)
- WARNING: hygiene_run entries present but 0 archive entries (cron firing but not archiving; threshold/query bug)
- HEALTHY: hygiene_run entries present AND archive entries > 0 (cron repaired; archival confirmed)
**Priority**: Tier 0 — 7 consecutive FAILUREs; escalation point: if this is the 8th miss, cron registration must be manually verified in ARQ WorkerSettings
**Derived from**: Q31.1 FAILURE (7th+); Q27.1 INCONCLUSIVE; Q27.7 WARNING (first batch target 2026-03-17)

---

## Q32.2 [DOMAIN-1] Double-decay — 21st consecutive reconfirmation
**Status**: PENDING
**Wave**: 32
**Mode**: quantitative analysis
**Target**: GET /admin/audit?action=decay_run&limit=10
**Hypothesis**: Q31.2 confirmed FAILURE (20th consecutive): `_user_conditions(None)` returns `[]`; system pass processed 5,994/6,048 (99.1%) active memories per slot; fix not deployed. Wave 32 runs without deployment; expect the same 2× processing pattern. This reconfirmation tracks the unbroken streak and validates the Wave 31 measurement against any spontaneous drift.
**What to measure**: (1) GET /admin/audit?action=decay_run&limit=10 — note processed counts for system run and per-user runs. (2) Confirm system run processed count is still ~5,994 (or consistent with current active corpus count). (3) Note current active corpus total (qdrant_total from GET /admin/stats). (4) Verify no partial fix has been applied: _user_conditions(None) still returns [] (static code check). (5) Calculate effective decay multiplier: 2× if system run processes full corpus.
**Verdict threshold**:
- FAILURE: System decay_run processed count ≈ total active corpus (fix not deployed; 21st consecutive)
- WARNING: System processed count reduced by 20-49% (partial mitigation without full fix; anomalous)
- HEALTHY: System processed count ≈ 0 or IS NULL condition applied (fix deployed between waves)
**Priority**: Tier 1 — streak tracking; also validates whether any spontaneous fix occurred
**Derived from**: Q31.2 FAILURE (20th); Q22.1 root cause analysis; double-decay unbroken streak Waves 12–31

---

## Q32.3 [DOMAIN-1] Floor-clamped 24h rate — does the +108 in 3h extrapolation hold over a full day?
**Status**: PENDING
**Wave**: 32
**Mode**: quantitative analysis
**Target**: GET /admin/export (all memories); filter importance <= 0.051 AND access_count = 0
**Hypothesis**: Q31.3 measured floor-clamped at 1,049 (+108 from Q30.6 baseline of 941 in ~3 hours), extrapolating ~864/day. However Q30.6 observed δ=0 over a 79-minute window (same-day artifact). Wave 32 runs ~24h after Q31.3, providing a true daily accumulation measurement. If the +864/day rate holds, expect ~1,913 floor-clamped memories. If the 3h window was a consolidation burst, expect a lower rate (~100-200/day). The source breakdown (system vs consolidation vs pattern) will identify whether Q22.1 double-decay or Q24.5 consolidation user_id is the dominant driver.
**What to measure**: (1) Download admin/export; count importance<=0.051 by source field. (2) Compare total to Q31.3 baseline: system=572, consolidation=449, pattern=25, user=3, total=1,049. (3) Calculate Δ and hours elapsed since Q31.3 measurement (Q31.3 was ~13:46 UTC 2026-03-15). (4) Compute daily rate = Δ / hours × 24. (5) Identify dominant source: is consolidation still growing at +74/3h rate or was that a burst?
**Verdict threshold**:
- FAILURE: Floor-clamped total > 1,049 (continued accumulation; no fix effective)
- WARNING: Floor-clamped total 800-1,049 (stable in FAILURE zone but not accelerating)
- HEALTHY: Floor-clamped total < 800 (declining; archival or double-decay fix taking effect)
**Priority**: Tier 1 — rate measurement resolves Q31.3 ambiguity; directly informs hygiene urgency
**Derived from**: Q31.3 FAILURE (1,049, +108 in 3h); Q30.6 WARNING (δ=0 over 79 min); Q22.1 + Q24.5 interaction

---

## Q32.4 [DOMAIN-3] Sunday reconcile cron — did it fire on 2026-03-16T05:30 UTC?
**Status**: PENDING
**Wave**: 32
**Mode**: observability
**Target**: GET /admin/audit?action=reconcile_run&limit=5; POST /admin/reconcile (trigger manual run)
**Hypothesis**: Q31.4 confirmed FAILURE (7th): reconcile_run=0 after manual POST /admin/reconcile trigger; log_audit() fix not deployed. The weekly reconcile cron fires Sunday at 5:30am UTC. 2026-03-16 is Sunday. If Wave 32 runs after 2026-03-16T05:30 UTC, the cron should have fired — but without the audit fix, the run itself may complete while leaving no audit trail. However, the manual trigger confirmed the cron logic itself is broken (reconcile_run=0 even after explicit trigger), suggesting the issue is deeper than just the audit trail. This question tests whether the reconcile mechanism itself is now producing any response when triggered manually.
**What to measure**: (1) POST /admin/reconcile — capture full response body. Is the response non-empty? Does it include qdrant_total, importance_mismatch count? (2) GET /admin/audit?action=reconcile_run&limit=5 — any entries after 2026-03-16T05:30 UTC? (3) If cron fired but reconcile_run=0: audit fix not deployed but reconcile ran (partial). (4) If reconcile_run entries present: audit fix was deployed between waves. (5) Compare importance_mismatch count in response to Q31.5 baseline (264).
**Verdict threshold**:
- FAILURE: POST /admin/reconcile returns response with reconcile_run=0 AND no reconcile_run audit entries (7th+ consecutive; mechanism broken)
- WARNING: POST /admin/reconcile returns reconcile_run=1 but no audit entry (reconcile works but log_audit fix not deployed)
- HEALTHY: POST /admin/reconcile returns reconcile_run=1 AND reconcile_run audit entry present (both reconcile + audit fix working)
**Priority**: Tier 1 — tests whether Sunday cron fired AND whether reconcile mechanism is functional
**Derived from**: Q31.4 FAILURE (7th); Q24.8 FAILURE; Sunday reconcile window 2026-03-16T05:30 UTC

---

## Q32.5 [DOMAIN-3] Importance mismatch 24h trajectory — is the +28/hour rate sustained or a consolidation burst?
**Status**: PENDING
**Wave**: 32
**Mode**: quantitative analysis
**Target**: POST /admin/reconcile (trigger); note importance_mismatch count in response
**Hypothesis**: Q31.5 measured importance mismatches at 264 (+85 from Q29.7 baseline of 179 in ~3 hours), implying +28/hour. But Q24.2 characterization suggested ~32 new mismatches/day from consolidation. The 10x discrepancy between Q31.5's rate and Q24.2's estimate must be resolved: either (a) Q31.5's 3-hour window captured an unusually active consolidation burst, (b) the +28/hour rate is real and the total by Wave 32 should be ~264 + (hours_elapsed × 28), or (c) some other mismatch source is active. Wave 32 provides a 24h measurement to distinguish these.
**What to measure**: (1) POST /admin/reconcile — note importance_mismatch count in response. (2) Calculate Δ from Q31.5 baseline (264) and hours elapsed. (3) Compute hourly rate: Δ / hours. Compare to Q31.5 rate (+28/hour) and Q24.2 estimate (~1.3/hour). (4) If rate is ~28/hour sustained: the Q24.2 estimate was wrong; a new mismatch source is active beyond mark_superseded. (5) If rate is ~1-3/hour: Q31.5 was a burst (probably caused by a large consolidation run shortly before measurement). Note: repairs_applied=0 from Q31.4 means reconcile is not draining mismatches, so count should only grow.
**Verdict threshold**:
- FAILURE: importance_mismatch > 264 (mismatches still accumulating; mark_superseded fix + reconcile both undeployed)
- WARNING: importance_mismatch 180-264 (partial drainage; reconcile repaired some but accumulation continuing)
- HEALTHY: importance_mismatch < 50 (mark_superseded fix deployed AND reconcile repaired the backlog)
**Priority**: Tier 1 — rate measurement resolves Q31.5 vs Q24.2 discrepancy; informs fix urgency
**Derived from**: Q31.5 FAILURE (264, +47% in 3h); Q24.2 FAILURE (mark_superseded fix undeployed); Q21.1 root cause

---

## Q32.6 [DOMAIN-4] LLM semaphore hold events — are >60s Ollama events accumulating in prod logs?
**Status**: PENDING
**Wave**: 32
**Mode**: observability
**Target**: ARQ worker logs; GET /admin/metrics or equivalent; LLM callsite audit cross-check
**Hypothesis**: Q31.7 confirmed FAILURE: 15/18 generate() callsites missing timeout=. Q15.3 identified 43 confirmed >60s events before the Wave 15 measurement. With 180s client-level timeout still active for 83.3% of callsites, every slow Ollama inference (qwen3:14b can take 1–24s per request per Q14.4) risks an extended semaphore hold. The Semaphore(1) means one held semaphore blocks ALL other LLM callers. This question measures whether the risk has materialized: how many >60s events have occurred since Q15.3, and what is the current rate?
**What to measure**: (1) Check ARQ worker / uvicorn logs for "ollama timeout" or HTTPTimeoutError entries since 2026-03-15. Count events. (2) Check if any HTTP 504 or 500 errors appear in the admin or store endpoints with LLM involvement. (3) Check signal_detection_timeout config value (currently 180s): has it been changed? (4) If logs are unavailable: verify whether GET /admin/metrics exposes any LLM timeout or semaphore wait counters. (5) Cross-reference with the 3 callsites that DO have timeout=: what are their timeout values? Are they firing?
**Verdict threshold**:
- FAILURE: >60s events accumulating at a rate higher than Q15.3 baseline (43 total), OR any 180s timeout event in logs (full semaphore starvation confirmed in production)
- WARNING: >60s events present but below Q15.3 baseline rate; no 180s events (risk present but not yet critical)
- HEALTHY: Zero >60s events in logs since Q15.3 measurement (Ollama performing consistently <60s; timeout fix lower priority than assumed)
- INCONCLUSIVE: Logs unavailable or do not capture LLM timing
**Priority**: Tier 2 — risk characterization; does not block other fixes but informs urgency of Q31.7 deployment
**Derived from**: Q31.7 FAILURE (15/18 callsites unprotected); Q15.3 FAILURE (43 events, 180s semaphore hold risk); Q14.4 (1–24s inference variance)

---

## Q32.7 [DOMAIN-3] GC-eligible pool tracking — what is the superseded pool growth rate with 6 days to eligibility?
**Status**: PENDING
**Wave**: 32
**Mode**: quantitative analysis
**Target**: POST /admin/reconcile (response includes superseded counts); or GET /admin/stats
**Hypothesis**: Q31.6 was INCONCLUSIVE: GC eligibility is 2026-03-21T19:12 UTC (~6d away). The superseded pool was 15,275 at Q31.6 (+91 from Q30.7 in ~3 hours). At ~728/day growth (91 in 3h × 8), the pool at 2026-03-21 would be ~19,543. But Q21.3's estimate was ~600 new superseded/day. The pool size at GC eligibility determines the first GC batch size and whether GC will meaningfully reduce Qdrant storage and reconcile scan time. This question establishes the 24h growth rate baseline.
**What to measure**: (1) GET /admin/stats or POST /admin/reconcile — note qdrant_total (includes superseded) and active count. Superseded = qdrant_total − active. (2) Compare superseded count to Q31.6 baseline (~15,275) and note hours elapsed. (3) Compute 24h growth rate. (4) Project superseded pool size at 2026-03-21T19:12 UTC (GC eligibility): baseline + (rate × 6d). (5) Note whether the pool is growing faster or slower than Q21.3's ~600/day estimate.
**Verdict threshold**:
- FAILURE: Superseded pool growth rate > 1,000/day (accelerating beyond Q21.3 estimate; GC batch at eligibility will be very large)
- WARNING: Superseded pool growth rate 400-1,000/day (within expected range; GC will have meaningful first batch)
- HEALTHY: Superseded pool growth rate < 400/day or pool is shrinking (consolidation rate dropped or external cleanup occurred)
- INCONCLUSIVE: Insufficient time elapsed since Q31.6 to compute reliable rate (same-day measurement artifact as Q30.7)
**Priority**: Tier 2 — time-gated observation; re-verify on/after 2026-03-21T19:12 UTC for Q32.7 HEALTHY/FAILURE verdict
**Derived from**: Q31.6 INCONCLUSIVE; Q30.7 INCONCLUSIVE; Q21.3 WARNING (~600/day superseded accumulation)

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

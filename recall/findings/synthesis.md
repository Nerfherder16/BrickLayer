# Synthesis: Recall Autoresearch — Waves 1–22

**Generated**: 2026-03-15 (updated with Wave 22 findings)
**Questions answered**: 119 (Q1.1–Q1.5, Q2.1–Q2.5, Q3.1–Q3.5, Q4.1–Q4.6, Q5.1–Q5.4, Q5.6–Q5.7, Q6.1–Q6.7, Q7.1–Q7.6, Q13.1–Q13.8, Q13.1a–Q13.8b, Q14.1–Q14.9, Q14.4a, Q14.4b, Q15.1–Q15.5, Q16.1–Q16.5, Q16.3b, Q16.4b, Q18.1–Q18.5, Q19.1–Q19.6, Q20.1–Q20.6, Q21.1–Q21.6, Q22.1–Q22.9)
**Wave 17 questions (Q16.3a, Q16.4a)**: PENDING — deferred until Tier 1 fixes deployed
**Source codebase**: C:/Users/trg16/Dev/Recall/
**Stack**: FastAPI + Qdrant + Neo4j + Redis + PostgreSQL + Ollama (qwen3:14b + qwen3-embedding:0.6b)

---

## 1. Executive Summary

Twenty-one waves of autoresearch have been run against the Recall self-hosted memory system. Waves 1–12 established a well-tested, type-safe codebase. Wave 13 revealed structural failures at the retrieval architecture level. Waves 14–20 added five FAILURE-severity findings across five clusters: LLM timeout misconfiguration, dedup observability, silent write failures, consolidation split-brain, and reconcile convergence failure. Wave 20 was an operational measurement wave that confirmed compound failures are occurring in production.

Wave 21 was a **deep-dive investigation wave** focused on the reconcile/superseded subsystem: characterizing the safety of the neo4j.mark_superseded importance=0.0 assignment, measuring repair=true convergence in practice, auditing superseded memory GC safety, confirming the Qdrant payload structure for un-supersedure, investigating ghost users in the decay loop, and verifying reconcile audit trail feasibility.

Wave 22 was a **fix-specification and corpus-integrity wave**: characterizing whether the double-decay bug extends to the primary user's corpus split, confirming ghost user identity, measuring GC threshold readiness, verifying reconcile response field availability, probing Neo4j REMOVE pattern support, auditing post-repair response visibility, confirming the decay user_id audit gap fix scope, measuring causal extractor GC safety, and reconstructing a 6-hour corpus state anomaly event.

**Overall health signal: CRITICAL ACCUMULATION — FIVE OPEN FAILURE CLUSTERS, SEVERAL WITH CONFIRMED LOW-EFFORT FIXES. ONE NEW FAILURE (Q22.1 double-decay). CONSOLIDATION USER_ID ATTRIBUTION LOSS CONFIRMED IN PRODUCTION (Q22.9).**

Wave 21 produced 4 HEALTHY (Q21.1, Q21.2, Q21.4, Q21.6) and 2 WARNING (Q21.3, Q21.5). No new FAILURE findings. Three of the open issues from Wave 20 were directly addressed: Q21.1 confirms that removing importance=0.0 from neo4j.mark_superseded is safe (zero-risk one-line change that directly fixes Q20.5's two-pass convergence defect); Q21.2 confirms repair=true converged the corpus in a single pass (1,315→2→0 mismatches); Q21.6 confirms reconcile audit trail is a 9-LOC change.

Wave 22 produced 1 FAILURE (Q22.1 double-decay), 2 WARNING (Q22.2 ghost user identity, Q22.9 corpus anomaly), and 6 HEALTHY (Q22.3–Q22.8). The double-decay bug (Q22.1) is a new FAILURE: every 15-minute cron slot applies `importance × (1-decay)²` to ALL active memories instead of `importance × (1-decay)`. The corpus is decaying at 0.9216× per slot instead of 0.96×, meaning every memory loses importance ~2× faster than configured. Q22.9 confirms the Q21.1 importance=0.0 bug is actively accumulating in production (521 mismatches = 521 historical supersedure events, each creating 1 permanent mismatch), and reveals a consolidation user_id attribution loss pattern where user memories consolidated into system-merged form become permanently orphaned from their original user.

**Wave 22 key findings**:
- Q22.1: Double-decay FAILURE — `_user_conditions(None)` returns `[]`, causing system run to process ALL active memories with no user_id filter; every cron slot applies decay twice (once system run + once per-user run); effective decay 0.9216× per slot instead of 0.96×; corpus decaying 2× faster than configured; fix: `MatchAny` or `IsNullCondition` in system-run filter
- Q22.2: Ghost users identified as exhausted legacy user_ids (stored float 2.0 in Qdrant, returned by `int(uid)` conversion); all have 0 active memories; stale user_ids not in PostgreSQL users table; PRIMARY ANOMALY: 521 importance mismatches re-appeared, user_id=2 absent from decay post-consolidation
- Q22.3: 0 superseded memories ≥30 days old (earliest audit 2026-03-02, 13d ago); first GC batch eligible ~2026-04-01; 507-entry overnight wave reaches 14d threshold 2026-03-27
- Q22.4–Q22.7: Fix-specification HEALTHY findings — reconcile audit fields available (9-11 LOC), Neo4j REMOVE pattern established inline, post-repair response achievable in 6 LOC, decay user_id audit gap fixable in 4 LOC
- Q22.8: Causal extractor GC safe — `CAUSAL_PRECEDES` schema error corrected (actual types DECIDED/ATTEMPTED/REVERTED); `find_related()` already filters `superseded_by IS NULL` making GC info-equivalent
- Q22.9: Corpus anomaly reconstructed — ARQ 6-hour outage (18:15–00:01); 521 mismatches = Q21.1 bug accumulated across ALL historical consolidation events (not just anomaly window); user_id=2 attribution lost via consolidation (merged into user_id=None), not deletion; active corpus grew 5693→5936 confirming no data loss

**Wave 21 key findings**:
- Q21.1: importance=0.0 in neo4j.mark_superseded is vestigial — every Neo4j query that filters on importance already has superseded_by IS NULL upstream; the or 0.5 fallback overrides 0.0 in activation scaling; removal is a one-line change that directly fixes the Q20.5 two-pass defect
- Q21.2: repair=true confirmed converging in a single pass — 1,315 importance mismatches (Q20.1) dropped to 2 via the Sunday 05:30am reconcile cron, then to 0 after manual repair=true; the Q20.5 compound defect is latent not active; repair response shows pre-repair state (Medium observability gap)
- Q21.3: causal_extractor.py uses include_superseded=True in the live POST /store path; deletion of superseded memories requires a 30-day age threshold + simultaneous Neo4j cleanup; ~600 new superseded/day with no GC = unbounded accumulation
- Q21.4: superseded_by/invalid_at are flat string fields removable atomically via client.delete_payload; IsNullCondition treats absent keys as NULL; qdrant.unmark_superseded() is 4 lines; Neo4j side needs a separate 8-line helper
- Q21.5: 7/10 decay_run entries per cron slot are processed=0 (ghost users); root cause: get_distinct_user_ids() scans all 20,923 Qdrant points including superseded; audit INSERT lacks user_id; primary user double-processed (overdecay ~4%/run)
- Q21.6: postgres_store importable in reconcile context via 1-line import extension; log_audit() accepts metadata dicts; ~9 LOC closes the Q20.1 reconcile observability gap

The eight-wave remediation stall (Waves 13–21) continues. No Tier 1 fix has been deployed. Wave 21 has further reduced the implementation uncertainty on several open fixes, bringing total characterized-but-undeployed fixes to 24.

---

## 2. Cumulative Findings by Verdict Tier (Waves 1–22)

### FAILURE — Open (requires fix before scaling)

| ID | Finding | Severity | Wave |
|----|---------|---------|------|
| Q13.1 | Coverage 8.9%: greedy top-K at K=3 cannot cover growing corpus; structural architecture failure | Critical | 13 |
| Q13.5 | Top-5 hit rate 5.4% at 20K memories; 60% threshold breached at N~1,850; capacity ceiling is fixed K | Critical | 13 |
| Q13.3 / Q13.3a | p95 extraction latency 14,055ms; system-wide Ollama queue saturation across all callers | High | 13 |
| Q13.1b | 35% of high-importance never-retrieved memories are genuinely high-value; knowledge burial confirmed | High | 13 |
| Q14.3 | Store-time semantic dedup silently drops incoming write with no content merge, no audit entry, no Neo4j edge — unique facts permanently lost | High | 14 |
| Q14.4 | Global asyncio.Semaphore(1) deployed but p95 still 11,313–16,843ms; root cause is qwen3:14b inference time variance (1s–24s per request), not concurrency | High | 14 |
| Q14.7 | Retrieval coverage 9.50% (unchanged from Q13.1's 8.9%); structural problem confirmed | High | 14 |
| Q15.3 | signal_detection_timeout=180s applies to ALL OllamaLLM callers via httpx.AsyncClient at init time; no per-call override in generate() signature; 43 confirmed >60s events; worst-case semaphore hold = 180s | High | 15 |
| Q15.4 | Very-short-prompt pre-filter at <50 chars not justified: best sub-bucket is 61.2% (threshold 70%); 30–44 char range has lower empty rate (34–42%) than overall average | Medium | 15 |
| Q16.3 | generate() has no timeout parameter; httpx.AsyncClient constructed once with 180s; per-call override path does not exist; 43 >60s events confirmed; fix not deployed | High | 16 |
| Q16.4 | 9-cell (4-site x 3-layer) dedup observability matrix: 2/12 cells covered; memory.py and observer.py have 0/3 layers; compound gap from Q14.3+Q15.1+Q15.2 not remediated | High | 16 |
| Q16.4b | except:pass in memory.py importance-inheritance block silently swallows all Qdrant errors; importance promotions never confirmed in production | Medium | 16 |
| Q13.8 | Session Markov Chain: 0 predictions in 4,008 visits; tag vocabulary mismatch; feature completely inert | Medium | 13 |
| Q13.8a | 0% of source files have >=5 transitions; max observed = 4; insufficient training data even after tag fix | Medium | 13 |
| Q13.5a | Sim-persona retirement inapplicable — all 20,602 memories are real user data; only 18 low-importance candidates | High | 13 |
| Q14.5 | input_chars cannot proxy file-type split for fact_extraction pre-filter; non-monotonic empty rate (51%->24%->36%->61%); distributions too overlapping | Medium | 14 |
| Q19.6 | Split-brain confirmed in consolidation: qdrant.mark_superseded() at line 282 committed before neo4j.mark_superseded() at line 283 bare await; Neo4j failure = divergence; all 4 Neo4j write methods unguarded; **Q20.1 bounds impact**: weekly reconcile repairs superseded_by mismatches (0 currently); divergence window up to 7 days, not permanent | High | 19 |
| **Q20.5** | **Compound failure reachable: Q18.1 partial gather + Q19.6 split-brain co-occur on single memory; reconcile Step A fix overwritten by Step B mark_superseded (importance=0.0); two passes required for convergence; 9 sub-pattern-A entries in Q20.1 are production evidence; Q21.1 provides one-line fix (remove importance=0.0 from mark_superseded); Q21.2 confirms compound state is currently latent (0 active)** | **High** | **20** |
| **Q22.1** | **Double-decay FAILURE: `_user_conditions(None)` returns `[]` → system run processes ALL active memories (no user_id filter); every 15-min cron slot applies decay twice (system run + per-user run); effective decay 0.9216× per slot instead of 0.96×; corpus decaying 2× faster than configured; fix: add MatchAny or IsNullCondition to system-run filter in `_user_conditions`** | **High** | **22** |

### WARNING — Open

| ID | Finding | Severity | Wave |
|----|---------|---------|------|
| Q13.2 | fact_extraction empty rate 42.2%; 89% of calls <200 chars input; 2,006 empty calls >10s each | Medium | 13 |
| Q13.4 | 65% of session summaries are raw noise; importance inversion in 3/20 superseded pairs | Medium | 13 |
| Q13.4a | semantic_dedup_threshold=0.90 (WARNING zone); store-time path drops incoming without importance check | Low | 13 |
| Q13.6 | 70% vocabulary hit rate; 1 genuine mismatch (abstract vs concrete terms); 2 coverage gaps | Medium | 13 |
| Q13.6a | Hook query uses user text + session topics + domain_hint only; tool_name/file path absent | Low | 13 |
| Q13.7 | type_cv=0.6539 after retrain (target 0.75); binary_cv=0.943 healthy; class imbalance limits improvement | Low | 13 |
| Q14.8 | Session summaries: 3 false-positive dedup pairs confirmed (genuinely distinct sessions merged); 5 near-misses at 0.85–0.90; zero tag-aware exemption in dedup path | Medium | 14 |
| Q15.2 | observer.py dedup `continue` has zero log call — drops are permanently unrecoverable; signals.py dedup is DEBUG-only (recoverable within 30MB docker log rotation window) | Medium | 15 |
| Q18.1 | asyncio.gather() in decay.py:184-187 has no return_exceptions=True — first Qdrant error aborts entire batch; remaining memories un-decayed; audit log skipped for failed run; partial writes untracked | Medium | 18 |
| Q18.2 | retrieval.py _track_access() fire-and-forget task has bare awaits; loop terminates early on first error; N+1 memories in retrieval batch receive zero access reinforcement; exception visible via asyncio but per-memory partial write state untracked | Medium | 18 |
| Q19.3 | Semaphore(1) FIFO queue wait unbounded; per-caller timeout bounds inference phase only; interactive 15s caller can wait 89s in queue behind consolidation — total 104s worst-case; priority routing required for interactive SLA compliance | Medium | 19 |
| Q19.4 | 889 memories at exactly importance=0.5 (21x spike, 4.3% of corpus); 99% never-accessed; decay working (peak at 0.3–0.4); Q16.4b + Q18.2 together prevent the cluster from draining normally; **Q20.3 resolves**: cluster is daily throughput artifact (97% drain in 26h); not persistent accumulation | Medium | 19 |
| Q19.5 | 2.8% batch near-duplicate rate from single admin scan (2026-02-19); dedup threshold changed 3 times qualitatively; no precision/recall measurement ever performed; **Q20.4 resolves**: 0.90-0.95 band empty; threshold raise confirmed correct | Medium | 19 |
| **Q20.1** | **1,315 importance mismatches (6.3% corpus drift); sub-pattern-A (neo4j=0.0, qdrant positive) on 9 memories explained by Q20.5 compound failure; sub-pattern-B (small drift 0.03-0.06) consistent with Q18.2 _track_access; reconcile has zero audit trail (no audit_log entries for any reconcile run); Q21.2 update: Sunday cron resolved 1,313 of 1,315; Q21.6 confirms 9-LOC fix for audit trail** | **Medium** | **20** |
| **Q21.3** | **causal_extractor.py uses include_superseded=True in live POST /store path; safe GC requires: superseded_by IS NOT NULL AND invalid_at <now−30d AND successor active AND simultaneous Neo4j cleanup; ~600 new superseded/day with no GC; 30-day eligible pool first available ~2026-03-21; unbounded accumulation growing reconcile scan time** | **Medium** | **21** |
| **Q21.5** | **7/10 decay_run entries per cron slot are processed=0 (ghost users); root cause: get_distinct_user_ids() scans all 20,923 Qdrant points including superseded; users with only superseded memories trigger full Qdrant scroll returning 0 results; audit INSERT lacks user_id; primary user decayed twice per slot (overdecay ~4%/run); 28 wasted scrolls/day** | **Medium** | **21** |
| **Q22.2** | **Ghost users confirmed as exhausted legacy user_ids (stored float in Qdrant; int() conversion surfaces them in get_distinct_user_ids()); all have 0 active memories; not in PostgreSQL users table; secondary anomaly: user_id=2 absent from decay loop post-consolidation, 521 mismatches re-appeared** | **Medium** | **22** |
| **Q22.9** | **ARQ decay worker 6-hour outage (2026-03-14T18:15–00:01 UTC); 521 importance mismatches = Q21.1 bug accumulated over ALL historical consolidation (~521 supersedure events each creating 1 permanent Neo4j=0.0 vs Qdrant!=0 mismatch); user_id=2 data not deleted — consolidated into user_id=None merged form (consolidation.py:235 creates Memory() without user_id); disappears from get_distinct_user_ids() when ALL originals superseded; active corpus grew 5693→5936; dec=4544 catch-up at 00:01 is time-based formula, not bulk deletion** | **High** | **22** |

### INCONCLUSIVE — Open (observation gap, not resolved)

| ID | Finding | Severity | Wave |
|----|---------|---------|------|
| Q15.1 | Store-time dedup hit rate: 3 silent-drop sites, 0 audit entries, 0 Prometheus counter — hit rate completely unquantifiable; prior threshold change (0.90->0.92) confirms real-world fires with no measurement | High | 15 |
| Q16.1 | recall_dedup_hits_total counter absent from /metrics; instrumentation from Q15.1 not deployed; 6 metric families present, none dedup-related; baseline unmeasurable | Medium | 16 |
| Q16.2 | logger.debug fix from Q15.2 not deployed; observer.py:176 is still bare `continue`; observer dedup remains most invisible path in the system | Medium | 16 |
| Q16.5 | file_extension absent from prompt_metrics schema; metadata column null for all 34,902 rows; >=70% empty-rate extension filter blocked; instrumentation chain not deployed | Medium | 16 |
| Q18.5 | session_summary dedup exemption is dead code (session summaries stored via Graphiti, not Qdrant path); episodic exemption live at 3,154 creates but pairwise similarity scan not feasible without batch Qdrant API | Low | 18 |
| Q13.2a | file_ext not captured in prompt_metrics; prevents file-type breakdown of empty extraction calls | Low | 13 |
| Q13.3a | Fact_extractor semaphore already exists; global LLM semaphore needed but not A/B tested | Medium | 13 |
| Q14.6 | Per-class confusion matrix structurally absent from signal classifier training; cross_val_predict never called; 15-line fix required | Medium | 14 |
| Q14.9 | Markov O(N) scan: scroll_all() is structural; targeted Qdrant tag filter predicted to achieve <10ms but not deployed; note: 0 cache hits expected until Q13.8 tag fix co-deployed | Medium | 14 |
| Q14.4a | Priority queue LLM dispatch: structurally feasible in ~25 lines; signal_detection volume too low (n=5 all-time, 0.23/day) for empirical p95 measurement | Medium | 14 |

### HEALTHY — Closed (all confirmed)

Waves 1–12 produced 35 HEALTHY findings across performance under load (Q1.1–Q1.4), domain isolation (Q2.1), graph traversal safety (Q3.4), error observability (Q5.3), concurrency guards (Q5.2, Q7.1), type safety (Q4.3, Q7.2), test coverage (Q4.1–Q4.6, Q5.6, Q5.7, Q7.6), and datetime/logger hygiene (Q6.7, Q7.4, Q7.5). All remain confirmed holding.

Wave 14–15 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q14.1 | Sim-persona residue: zero named-persona entities in current 5,831-memory non-superseded corpus | 14 |
| Q14.2 | Exploration-based retrieval prototype: 90% of buried high-importance memories topically relevant (0% noise); safe to deploy | 14 |
| Q14.4b | Input length threshold confirmed at ~4,000 chars: p75 doubles (7s->14s), p95 doubles (15s->37s) above 4,000 chars; 99.4% of prompts are below this threshold; truncation at 4,000 chars is practical and eliminates catastrophic semaphore holds | 14 |
| Q15.5 | 1,000–3,000 char empty extraction bucket: 14/21 (67%) empty rows are single-line (newline density <0.1%); filterable via newline-density guard without file_ext instrumentation | 15 |

Wave 16 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q16.3b | httpx per-request timeout correctly overrides client-level default; `client.post(..., timeout=N)` wins over `AsyncClient(timeout=180)`; Q16.3 fix approach confirmed architecturally sound | 16 |

Wave 18 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q18.3 | 17 LLM callsites audited across 13 files; all categorizable into 4 timeout tiers (15s/30s/60s/90s); no structural blockers; Q16.3 fix deployable immediately with 2 PRs | 18 |
| Q18.4 | Dedup code paths functionally correct: all 3 callers correctly handle (None, None) short-circuit; no path to double-store; observability gap is monitoring problem not correctness problem | 18 |

Wave 19 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q19.1 | Full-codebase gather audit: 14 gather call sites; only decay.py:184 is an unguarded write-gather (already Q18.1 WARNING); consolidation.py has zero gather calls; contradiction_backfill.py correctly uses return_exceptions=True; all other 11 gathers are read-only | 19 |
| Q19.2 | _store_retrieval_context has full try/except; writes to Redis only (ephemeral, 2h TTL); _emit_retrieval_activity also correctly guarded; _track_access is the sole fire-and-forget task with bare Qdrant/Neo4j writes | 19 |

Wave 20 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q20.2 | Reconcile scalability confirmed: scroll_all uses cursor pagination (209 round trips at 20K); Neo4j uses single UNWIND query; ARQ 30-minute timeout breach modeled at 36M memories (~99 years at current growth); minor note: full corpus accumulated in-memory (~30MB at 20K) | 20 |
| Q20.3 | Importance=0.5 cluster is daily throughput artifact: 97% drain in 26 hours (889 -> 25 active); all same-day creates; 92% semantic type; Q16.4b casualties do not persistently cluster at 0.5; resolves Q19.4 ambiguity | 20 |
| Q20.4 | Dedup threshold calibration confirmed correct: 0 duplicate pairs at 0.90 threshold on 5,882 active memories; 1 pair at 0.95; 0.90-0.95 band empty; threshold raise from 0.90 to 0.92 was empirically correct; **secondary: active corpus is 5,882 of 20,889 (72% superseded)** | 20 |
| Q20.6 | Decay audit coverage confirmed: 694 entries = per-user multiplier (9 users x 4 runs/day); single zero-day (2026-02-23) is 4.7% of expected cron slots; last 7 days show perfect 4/day coverage; no systematic Q18.1 audit gaps detected | 20 |

Wave 21 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q21.1 | importance=0.0 in neo4j.mark_superseded is vestigial: all Neo4j Cypher queries that filter on importance already have superseded_by IS NULL upstream; activation scaling uses `or 0.5` fallback that overrides 0.0; no query uses importance as a proxy for active/superseded status; one-line removal directly fixes Q20.5 reconcile two-pass convergence defect | 21 |
| Q21.2 | repair=true converges in single pass: 1,315→2 mismatches resolved by Sunday 05:30am reconcile cron; 2→0 resolved by manual repair=true in one pass; Q20.5 compound defect is latent not active (0 simultaneous superseded+importance mismatches); repair response format shows pre-repair state (Medium observability gap — operators may retry unnecessarily) | 21 |
| Q21.4 | superseded_by and invalid_at are flat scalar strings; client.delete_payload removes both atomically; IsNullCondition treats absent keys as NULL — memory immediately reappears in active scroll after deletion; qdrant.unmark_superseded() is 4 lines; Neo4j side needs 8-line helper + importance restore | 21 |
| Q21.6 | postgres_store importable in reconcile via 1-line import; log_audit() fire-and-forget accepts metadata dicts; ~9 LOC across 2 files closes Q20.1 reconcile observability gap; enables last-run-date query, mismatch trend detection, repair convergence monitoring | 21 |

---

## 3. Wave 22 Results (Q22.1–Q22.9)

### Overview

Wave 22 was a **fix-specification and corpus-integrity wave** — following Wave 21's identification of ghost-user decay waste (Q21.5), reconcile response opacity (Q21.2), and the Q21.1 importance=0.0 vestigial bug, Wave 22 mapped the double-decay bug, confirmed ghost user identity, verified fix scope for 6 pending changes, measured GC threshold readiness, probed causal GC safety, and reconstructed a 6-hour corpus state anomaly that surfaced 521 importance mismatches and the disappearance of the primary user from the decay loop.

Of 9 questions: 1 FAILURE (Q22.1), 2 WARNING (Q22.2, Q22.9), 6 HEALTHY (Q22.3–Q22.8).

**The defining finding of Wave 22**: Q22.1 is a new FAILURE — the system's decay mechanism has been running at double-speed since the per-user cron was introduced. `_user_conditions(None)` returns `[]` (no filter), so the system run processes all active memories without restriction. In a 15-minute cron slot, a memory is decayed once in the system run and again in its per-user run: the combined factor is `0.96 × 0.96 = 0.9216` per slot instead of the intended `0.96`. At 96 slots/day, the effective daily decay factor is `0.9216^96 ≈ 0.00028` instead of `0.96^96 ≈ 0.0199`. The corpus is decaying ~71× faster per day than the decay configuration intends, and every memory that should decay to importance 0.10 after 30 days is already at <0.001.

**Q22.9's compound revelation**: The 6-hour ARQ outage (18:15–00:01) is a secondary finding — the primary revelation is that the 521 importance mismatches are a direct, counting accumulation of the Q21.1 bug: every single consolidation event since the system was deployed has created 1 permanent reconcile mismatch. With ~521 supersedure events in the visible audit history and a continuously running consolidation worker, this count will grow indefinitely until the one-line mark_superseded fix is deployed. The user_id=2 attribution loss pattern confirms a production consolidation design gap: consolidated memories get `user_id=None` permanently, breaking user-level decay, export, and memory ownership tracking.

**Q22.3's GC timing snapshot**: The 30-day GC threshold has not yet been crossed (earliest audit 2026-03-02, 13 days ago). The first large eligible batch is ~2026-04-01. The 507-entry overnight consolidation wave from the Q22.9 anomaly window becomes 14-day eligible on 2026-03-27. No urgent GC window is open, but the clock is running.

---

### Wave 22 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q22.1 | FAILURE | High | `_user_conditions(None)` returns `[]` → system run processes ALL active memories; every cron slot decays all memories twice (system + per-user); effective decay 0.9216/slot vs 0.96 intended; corpus decaying 2× faster than configured; fix: filter system run to `user_id IS NULL` only via `IsNullCondition` or `MatchAny` |
| Q22.2 | WARNING | Medium | Ghost users = exhausted legacy user_ids with 0 active memories (stored as float in Qdrant; `int(uid)` conversion surfaces them); not in PostgreSQL users table; stale user_ids persist as long as superseded memories exist; primary anomaly: user_id=2 absent from decay post-consolidation, 521 mismatches re-appeared |
| Q22.3 | HEALTHY | Info | 0 superseded memories ≥30 days old (system 13d old); first GC batch ~2026-04-01; 507-entry overnight wave (Q22.9 anomaly) eligible at 14d threshold 2026-03-27; no urgent GC window open |
| Q22.4 | HEALTHY | Info | All 8 reconcile audit schema fields available as local variables at insertion point; ops.py needs 9-11 LOC (individual variable extraction instead of stats dict); reconcile.py ~5 LOC; total ~14-16 LOC vs Q21.6's 9 LOC estimate |
| Q22.5 | HEALTHY | Info | Cypher `REMOVE` pattern for clearing `superseded_by` already established inline in ops.py:348 and reconcile.py:65 (identical pattern); neo4j_store.py has no REMOVE yet; `unmark_superseded()` is 8-line promotion; existing inline code omits `invalid_at` removal (minor incompleteness) |
| Q22.6 | HEALTHY | Info | Reconcile response built from pre-repair lists at function end (scan→repair→response phases); 6 LOC adds per-type counters + `post_repair_importance_mismatches` / `post_repair_superseded_mismatches` response fields; no re-scan needed |
| Q22.7 | HEALTHY | Info | `_log_decay_audit()` called per-user from inside `worker.run()` which has `user_id` in scope; `audit_log.user_id` column exists (migration at postgres_store.py:172); fix is 4 LOC: signature + INSERT + call site; historical backfill not practical (identical timestamps, ghost identity better resolved by Q21.5 fix) |
| Q22.8 | HEALTHY | Info | `CAUSAL_PRECEDES` schema error corrected (does not exist; actual types: DECIDED_BECAUSE / ATTEMPTED_BEFORE / REVERTED_DUE_TO); `find_related()` at neo4j_store.py:280 filters `related.superseded_by IS NULL` → causal edges to superseded targets already invisible in production; GC via DETACH DELETE produces no new information loss; ~3% of 83,830 total relationships are causal; ~0.3% have superseded targets |
| Q22.9 | WARNING | High | ARQ 6-hour outage (18:15–00:01); 521 importance mismatches = entire historical accumulation of Q21.1 bug (every supersedure → Neo4j importance=0.0, Qdrant unchanged); user_id=2 not deleted — consolidated into `user_id=None` merged form (consolidation.py:235 creates `Memory()` without user_id); disappears from `get_distinct_user_ids()` when all originals superseded; active corpus grew 5693→5936 confirming no data loss; dec=4544 catch-up is time-based formula, not bulk deletion |

---

### Wave 22 Cross-Domain Observations

#### Observation 1: Q22.1 adds a sixth failure cluster — decay double-application

Wave 22 opens a new independent FAILURE cluster: the per-user decay cron creates a double-decay bug where every named user's memories are processed in both the system run (user_id=None filter returns `[]` → all memories) and the per-user run. The fix is a single-line change to `_user_conditions(None)` or the cron entrypoint to separate system-only and per-user execution paths. Until fixed, all user memories decay at `0.9216/slot` instead of `0.96/slot` — the corpus is functionally ~71× more aggressive than the decay_rate parameter suggests.

#### Observation 2: Q22.9 confirms Q21.1 is not theoretical — it is actively accumulating

Wave 21 confirmed that removing `importance=0.0` from `mark_superseded` was safe. Wave 22 confirms that NOT removing it is costly: every consolidation event since deployment has created a permanent reconcile mismatch. The 521 count will grow with every future consolidation. With a continuously-running consolidation worker, the rate of new mismatches is approximately the supersedure rate (estimated ~600/day from Q21.3). Reconcile repair can clear these (as Q21.2 demonstrated), but only by calling `repair=true` and only by re-syncing the importance field from Qdrant. The one-line removal from `mark_superseded` would stop new mismatches from being created.

#### Observation 3: Consolidation user_id attribution is a silent data governance bug

Q22.9 documents that `consolidation.py:235` creates merged memories without user_id. This is a previously uncharacterized production gap: when system consolidation runs on user memories, the merged output has `user_id=None`. The original memories are then marked superseded. Once all of a user's original memories are superseded, the user disappears from `get_distinct_user_ids()` — not because of deletion but because every surviving copy is attributed to `user_id=None`. The user's memories are preserved in content but their ownership is permanently lost. This affects user-level decay, export, and count APIs.

#### Observation 4: Six Wave 22 HEALTHY findings confirm fix specifications — implementation cost is fully characterized

Q22.4–Q22.8 provide complete implementation specifications for six pending changes:
- Reconcile audit trail: 14-16 LOC (Q22.4, refining Q21.6's 9 LOC estimate)
- Neo4j unmark_superseded(): 8 LOC with REMOVE pattern proven inline (Q22.5)
- Post-repair response visibility: 6 LOC counter approach (Q22.6)
- Decay user_id in audit: 4 LOC (Q22.7)
- GC causal safety: confirmed safe via find_related() filter (Q22.8)

The total implementation cost for all five Wave 22 fix specifications is ≤38 LOC. Combined with the Wave 21 fix specifications (1-line mark_superseded removal, 4-line unmark_superseded, 1-line get_distinct_user_ids filter), the Tier 1b fix set is now fully specified with exact line counts.

---

## 5. Wave 21 Results (Q21.1–Q21.6)

### Overview

Wave 21 was a **reconcile/superseded subsystem deep-dive**. Following Wave 20's identification of the Q20.5 compound-failure/two-pass-convergence defect, Wave 21 investigated: Is the importance=0.0 assignment in mark_superseded safe to remove? Does repair=true actually converge? How should superseded memories be GC'd? What is the Qdrant payload structure for reversal? Why are there ghost users in decay? Is the reconcile audit trail feasible?

Of 6 questions: 4 HEALTHY (Q21.1, Q21.2, Q21.4, Q21.6), 2 WARNING (Q21.3, Q21.5). No new FAILURE findings. The wave materially de-risked the Q20.5 fix (Q21.1 confirms it is a one-line deletion), confirmed the corpus is currently clean (Q21.2), and revealed two new medium-severity issues in adjacent subsystems (GC bloat Q21.3, ghost-user decay waste Q21.5).

**The defining finding of Wave 21**: Q21.1 provides the clearest finding of any wave — the importance=0.0 in neo4j.mark_superseded is vestigial by complete audit. Zero Cypher queries use importance as an active/superseded proxy. The defensive intent of the assignment failed from inception: the queries it was meant to protect already had superseded_by IS NULL guards, and the activation scaling code uses `or 0.5` which overrides 0.0 anyway. Removing the one line directly fixes Q20.5 without any retrieval, scoring, or graph-traversal regression.

**Q21.2's operational confirmation**: The concern that repair=true might create new mismatches (the Q20.5 scenario) was not observed. The Sunday reconcile cron cleared 1,313 of 1,315 mismatches automatically. The 2 remaining sub-pattern-A entries were repaired in a single pass because their superseded_by fields were already reconciled — only the importance residual remained, which Step A fixed without Step B firing. Q20.5's two-pass scenario requires simultaneous superseded and importance mismatches, which are not currently present. The defect is latent, not active.

**Q21.3's unbounded accumulation warning**: The superseded GC question reveals two issues: (a) causal_extractor.py accesses superseded memories in the live POST /store path, making deletion non-trivially safe, and (b) ~600 new superseded points per day with no deletion mechanism means the 72% superseded ratio will continue growing indefinitely. At the 30-day threshold, the first large GC batch becomes eligible ~2026-03-21. Without GC, reconcile scan time, storage, and decay user-list scan overhead all grow proportionally.

**Q21.5's ghost-user decay finding**: The decay loop processes 10 user_ids per cron slot but 7 of them have zero active memories. The root cause (get_distinct_user_ids scans all 20,923 points including superseded) connects directly to Q21.3 — as the superseded population grows, the number of ghost users will grow. The primary user being processed twice per slot (overdecay ~4% per run) is the most actionable finding: if their corpus is split across user_id=None and user_id=N, both will be processed each slot indefinitely.

---

### Wave 21 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q21.1 | HEALTHY | Info (fix severity: High) | importance=0.0 in neo4j.mark_superseded is vestigial; all importance-querying Cypher has superseded_by IS NULL pre-filter; activation scaling uses or 0.5 fallback; one-line removal fixes Q20.5 reconcile two-pass defect; zero functional regressions |
| Q21.2 | HEALTHY | Info (observability gap: Medium) | repair=true converges in single pass; 1,315→2 mismatches resolved by Sunday cron; 2→0 by manual repair=true; Q20.5 latent not active; repair response shows pre-repair state (misleading for operators); 27 new stores in ~7h; zero orphans |
| Q21.3 | WARNING | Medium | causal_extractor uses include_superseded=True in live store path; safe GC: age ≥30d + successor active + simultaneous Neo4j DELETE; no GC mechanism exists; ~600 new superseded/day; 30-day batch first eligible ~2026-03-21; needs new ARQ cron + neo4j.delete_memory_node helper |
| Q21.4 | HEALTHY | Info (impl gap: Low) | superseded_by/invalid_at are flat scalar strings; delete_payload removes atomically; IsNullCondition treats absent as NULL; qdrant.unmark_superseded() is 4 lines; Neo4j side needs REMOVE helper + importance restore; or: run repair=true after Qdrant unmark |
| Q21.5 | WARNING | Medium | 7/10 decay_run entries/slot are processed=0 (ghost users); get_distinct_user_ids() scans all 20,923 points; users with only superseded memories trigger empty runs; audit INSERT lacks user_id; primary user double-processed (overdecay ~4%/run); fix: add IS NULL filter to get_distinct_user_ids() + user_id column to audit INSERT |
| Q21.6 | HEALTHY | Info | postgres_store importable in reconcile via trivial 1-line import; log_audit() fire-and-forget supports metadata dicts; ~9 LOC across reconcile.py + ops.py; enables last-run-date query, trend detection, convergence monitoring for Q20.1 gap |

---

### Wave 21 Cross-Domain Observations

#### Observation 1: Q21.1 collapses Q20.5 from a design defect to a one-line vestigial removal

Wave 20 framed Q20.5 as a reconcile design defect (Step A importance fix overwritten by Step B mark_superseded) requiring either step-ordering logic or a two-pass execution. Q21.1 reframes the problem entirely: the root cause is that mark_superseded sets importance=0.0 at all, which has been vestigial since it was written. The defensive intent (suppress nodes from importance-ranked results if superseded_by filter somehow fails) was redundant from inception — the superseded_by IS NULL filter was always present. Removing the one line eliminates the defect naturally, without any change to reconcile's step ordering, without any impact on retrieval, and without any compensating rollback logic.

This is the most favorably resolved Wave-20 finding. Q20.5 added a FAILURE and specified a ~10-line reconcile.py fix. Q21.1 reduces the same fix to 1 line in neo4j_store.py with higher confidence.

#### Observation 2: Q21.2 provides the first live verification of reconcile repair effectiveness

Wave 20 measured the corpus state but did not run repair=true. Wave 21 executed the full repair cycle: baseline → repair run → post-repair verification. The result (0 mismatches after single pass) is the most direct evidence yet that the reconcile mechanism is working. The 99.8% reduction from 1,315 to 2 by the Sunday cron confirms the weekly schedule is sufficient at current compound failure rates (~2 sub-pattern-A entries generated per week cycle). The observability gap in the response format (showing pre-repair state) is a low-effort fix that prevents operator confusion.

#### Observation 3: Q21.3 and Q21.5 reveal that the superseded memory accumulation is a cross-cutting concern

The 72% superseded ratio noted as a secondary finding in Q20.4 now has three downstream effects confirmed across Wave 21:
1. **GC unavailability** (Q21.3): causal_extractor access makes simple deletion unsafe; requires age threshold + simultaneous Neo4j cleanup
2. **Decay ghost users** (Q21.5): get_distinct_user_ids() scans superseded points, returning user_ids with 0 active memories; each produces a wasted cron slot
3. **Reconcile scan overhead** (Q20.2): scroll_all with include_superseded fetches 3.5x more data than needed

All three trace to the same root: superseded memories are never deleted. The GC implementation (Q21.3 specification) would fix all three simultaneously: fewer superseded points → fewer ghost user_ids → fewer reconcile round trips.

#### Observation 4: Q21.4 enables the Q19.6 compensating rollback

Q21.4 confirms that qdrant.unmark_superseded() is a 4-line atomic operation. This directly enables the Tier 1b fix #5 (consolidation compensating rollback): when Neo4j.mark_superseded fails after Qdrant.mark_superseded succeeds, calling qdrant.unmark_superseded(id) restores the Qdrant side without re-insertion. The Q21.4 finding eliminates the last open question about Q19.6's fix specification — all components are now confirmed.

#### Observation 5: The nine-wave remediation stall deepens — yet Q21 findings lower implementation risk for all major fixes

Waves 13–21 have produced characterizations without deployed remediation. However, Wave 21 has reduced implementation uncertainty on the most critical open items:
- Q20.5 fix: was ~10 lines reconcile.py → now **1 line neo4j_store.py** (Q21.1)
- Q20.1 audit trail: was unspecified → now **9 LOC fully specified** (Q21.6)
- Q19.6 compensating rollback: qdrant side was uncertain → now **4 lines confirmed** (Q21.4)
- Decay ghost users: root cause was unclear → now **one-line IS NULL filter** (Q21.5)

The remaining implementation cost of the Tier 1 and Tier 1b fixes is lower after Wave 21 than it was after Wave 20.

---

## 6. Wave 20 Results (Q20.1–Q20.6)

### Overview

Wave 20 was an **operational measurement and compound-failure investigation wave**. Following seven waves of characterization without deployment, Wave 20 turned to live production queries to measure whether the characterized failures were materializing, at what rate, and whether self-repair mechanisms (reconcile, decay) were bounding the damage. The wave also investigated whether the four open failure clusters could interact to produce compound states worse than any single cluster.

Of 6 questions: 4 HEALTHY (Q20.2, Q20.3, Q20.4, Q20.6), 1 WARNING (Q20.1), 1 FAILURE (Q20.5).

**The defining finding of Wave 20**: The compound failure (Q20.5) demonstrates that clusters 3 and 4 interact — Q18.1 (partial gather) and Q19.6 (split-brain) can co-occur on a single memory in one consolidation cycle, producing a state that reconcile cannot fully repair in a single pass. More critically, reconcile itself introduces a NEW importance mismatch while repairing the superseded_by mismatch (mark_superseded zeros Neo4j importance, overwriting the Step A importance fix). This is a **reconcile design defect**, not just a compound failure reachability finding. The 9 sub-pattern-A entries in Q20.1 are direct production evidence that this has already occurred. **Wave 21 update**: Q21.1 collapses this to a 1-line vestigial removal; Q21.2 confirms 0 active compound failures after repair.

**The operational measurement findings**: Q20.1 through Q20.4 and Q20.6 provide the first live production state measurements:
- The split-brain repair mechanism (weekly reconcile) is working — 0 superseded_mismatches despite 6,441 consolidation events over 28 days (Q20.1)
- However, 1,315 importance mismatches (6.3% corpus) reveal structural Qdrant/Neo4j drift from the Q18.2 _track_access pattern (Q20.1)
- Reconcile has zero audit trail — its execution history is invisible from the audit_log (Q20.1); Q21.6 confirms 9-LOC fix
- Reconcile scalability is not a concern at current or projected corpus sizes (Q20.2)
- The importance=0.5 cluster is self-clearing daily throughput, resolving Q19.4 ambiguity (Q20.3)
- The dedup threshold is empirically correct; the 0.90–0.95 cosine band is empty (Q20.4)
- Decay audit coverage is complete; 694 entries explained by per-user multiplier (Q20.6)
- Active corpus is only 5,882 of 20,889 Qdrant points — 72% are superseded (Q20.4 secondary)

---

### Wave 20 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q20.1 | WARNING | Medium | 0 superseded_mismatches (split-brain repaired by reconcile); 1,315 importance_mismatches (6.3% corpus drift); sub-pattern-A (neo4j=0.0, qdrant positive, 9 entries) explained by Q20.5 compound failure; sub-pattern-B (small drift) from Q18.2 _track_access; reconcile has zero audit_log entries — last run date unverifiable; **Q21.2**: 1,313 resolved by Sunday cron; **Q21.6**: 9-LOC fix confirmed |
| Q20.2 | HEALTHY | Info | scroll_all cursor-paginated (209 round trips at 20K); neo4j.get_bulk_memory_data uses single UNWIND; ARQ timeout breach at 36M memories (~99 years at current growth); in-memory accumulation minor concern at 500K+ |
| Q20.3 | HEALTHY | Info | Importance=0.5 cluster: 97% drain in 26h (889 -> 25); all same-day creates; Q16.4b casualties do not persistently cluster at 0.5; Q19.4 ambiguity resolved |
| Q20.4 | HEALTHY | Info | 0 duplicate pairs at 0.90 on 5,882 active; 1 pair at 0.95; 0.90-0.95 band empty; threshold raise confirmed correct; secondary: 72% of Qdrant points are superseded (5,882 active of 20,889 total) |
| Q20.5 | FAILURE | High | Compound failure reachable: Q18.1 partial gather -> importance drift + audit gap; then Q19.6 split-brain; reconcile repairs superseded_by but introduces NEW importance mismatch (neo4j=0.0 vs qdrant!=0); two passes required; 9 sub-pattern-A entries are production evidence; **Q21.1**: one-line removal of importance=0.0 from mark_superseded directly fixes this; **Q21.2**: compound state currently latent (0 active) |
| Q20.6 | HEALTHY | Info | 694 decay_run entries = per-user multiplier (9 users x 4/day x ~85 slots); single zero-day 2026-02-23 = 4.7%; last 7 days perfect; no systematic Q18.1 audit gaps |

---

## 7. Wave 19 Results (Q19.1–Q19.6)

### Overview

Wave 19 was a **boundary-measurement and scope-confirmation wave**. Following Wave 18's discovery of two silent-write-failure patterns, Wave 19 asked: are these isolated or do they extend to adjacent code paths? The wave also probed two cross-cutting concerns — the semaphore latency implications of the pending timeout fix, and the state of the importance distribution in the live corpus.

Of 6 questions: 2 HEALTHY (Q19.1, Q19.2), 3 WARNING (Q19.3, Q19.4, Q19.5), 1 FAILURE (Q19.6).

**The defining finding of Wave 19**: The split-brain failure (Q19.6) is a new, independent FAILURE that was not anticipated by Waves 14–18. It is structurally analogous to Q16.4b (Qdrant writes unguarded in importance-inheritance) but with higher consequence: the divergence between Qdrant's superseded state and Neo4j's active state can persist for up to 7 days until the weekly reconcile cycle repairs it. Q19.6 opens a fourth cluster. **Wave 20 update**: Q20.1 confirms 0 superseded_mismatches currently; Q20.5 identifies a reconcile convergence defect when repairing compound failures. **Wave 21 update**: Q21.4 confirms qdrant.unmark_superseded() is 4 lines — the compensating rollback for Q19.6 is now fully specified.

---

### Wave 19 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q19.1 | HEALTHY | Info | Full-codebase asyncio.gather() audit: 14 sites, 1 unguarded write-gather (decay.py:184 = Q18.1 WARNING), consolidation.py has zero gather calls, contradiction_backfill.py uses return_exceptions=True; cluster 3 blast radius is bounded |
| Q19.2 | HEALTHY | Info | _store_retrieval_context: full try/except, Redis-only writes (ephemeral 2h TTL); _emit_retrieval_activity also guarded; _track_access is the sole unguarded fire-and-forget storage task; Q18.2 blast radius is bounded |
| Q19.3 | WARNING | Medium | Semaphore(1) is FIFO-confirmed; per-caller timeouts bound inference phase only; interactive 15s timeout does not bound queue wait; consolidation queue hold -> interactive waits up to 89s before own 15s window opens; total worst-case 104s; priority routing required |
| Q19.4 | WARNING | Medium | 889 memories at importance=0.5 (21x spike, 4.3% of corpus); 99% never-accessed dark memories; decay working (corpus peak at 0.3–0.4); Q16.4b importance-inheritance bug + Q18.2 _track_access loop exit combine to sustain contamination; **Q20.3**: resolved as daily throughput artifact |
| Q19.5 | WARNING | Medium | 2.8% batch near-duplicate rate (129/4,602 corpus, 2026-02-19 admin scan); threshold history 0.95->0.90->0.92 all qualitative; no precision/recall measurement ever performed; real-time dedup rate remains unquantifiable; **Q20.4**: 0.90-0.95 band empty, raise confirmed correct |
| Q19.6 | FAILURE | High | Split-brain confirmed in consolidation: qdrant.mark_superseded (line 282) bare await committed before neo4j.mark_superseded (line 283) bare await; Neo4j failure after Qdrant success = divergence (up to 7 days until reconcile); all 4 Neo4j write methods unguarded; partial-iteration failure leaves multi-memory compound inconsistency; **Q20.1**: 0 superseded_mismatches currently; **Q20.5**: reconcile convergence defect on compound failures; **Q21.4**: qdrant.unmark_superseded() confirmed as 4-line compensating rollback |

---

## 8. Wave 18 Results (Q18.1–Q18.5)

### Overview

Wave 18 was a silent-write-failure audit — motivated by Q16.4b's discovery of the `except:pass` pattern in the importance-inheritance block, and by the broader pattern of partial-write states seen across three waves of dedup investigation. Wave 18 extended that investigation to two additional critical write paths (decay batch and retrieval access tracking) and also clarified whether the timeout fix has any remaining deployment blockers and whether dedup is functionally correct beneath the observability gap.

Of 5 questions: 2 HEALTHY (Q18.3, Q18.4), 2 WARNING (Q18.1, Q18.2), 1 INCONCLUSIVE (Q18.5).

**The defining finding of Wave 18**: The silent-write-failure pattern is not limited to the dedup path. Both `decay.py` and `retrieval.py` have the same class of defect: batch/loop write operations that can produce partial writes with no audit record of which memories were affected. The dedup `except:pass` (Q16.4b) plus the decay gather abort (Q18.1) plus the retrieval loop early-exit (Q18.2) form a third systemic cluster alongside the timeout and observability clusters.

---

### Wave 18 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q18.1 | WARNING | Medium | decay.py:184-187 asyncio.gather() has no return_exceptions=True; first Qdrant error aborts entire batch; remaining memories un-decayed; audit log (_log_decay_audit) skipped; partial writes from completed coroutines untracked; exception IS logged at ERROR level by outer caller |
| Q18.2 | WARNING | Medium | retrieval.py _track_access() fire-and-forget task has bare awaits in per-memory for-loop; exception from memory N terminates loop — N+1 memories receive zero access reinforcement; error visible via asyncio "task exception never retrieved" at GC time but lacks per-memory context |
| Q18.3 | HEALTHY | Info | 17 llm.generate() callsites across 13 files audited; all classifiable into 4 tiers (interactive 15–30s, background 60s, long-running 90s, admin 120s); no structural blockers; Q16.3 fix deployable as 2 PRs (1 file core change + 13 file callsite update) |
| Q18.4 | HEALTHY | Low | All 3 dedup callers correctly short-circuit on (None, None); API store path returns before qdrant.store(); observer `continue` skips store+graph calls; signals.py `if memory_id:` guard is correct; no double-store path exists in code |
| Q18.5 | INCONCLUSIVE | Low | session_summary exemption in memory.py:234 is dead code — session summaries stored via Graphiti not Qdrant; episodic exemption live (3,154 creates) but pairwise similarity scan requires O(N^2) Qdrant queries not feasible via current API |

---

## 9. Wave 17 Status (Q16.3a, Q16.4a — PENDING)

Wave 17 was planned as a post-deployment verification wave with two questions:

**Q16.3a** — Per-caller timeout post-deployment: after adding `timeout` parameter to `generate()`, does fact_extraction p99 semaphore hold drop below 60s?
*Status: PENDING — prerequisite (Q16.3 fix) not deployed. Cannot be answered until timeout parameter is deployed. Note: Q19.3 adds a qualifier — even after deployment, interactive callers can wait 89s in queue; Q16.3a should measure total latency (queue + inference), not inference alone.*

**Q16.4a** — Dedup drop volume post-instrumentation: after adding `recall_dedup_hits_total`, what fraction of daily stores are dedup-dropped, and does the API store path fire more often than observer?
*Status: PENDING — prerequisite (Q15.1/Q16.1 instrumentation) not deployed. Cannot be answered until dedup counters are deployed.*

These two questions remain the highest-priority measurement questions in the queue.

---

## 10. Wave 16 Results (Q16.1–Q16.5, Q16.3b, Q16.4b)

### Overview

Wave 16 was a deployment-verification wave — its explicit goal was to check whether any of the Wave 14–15 remediation recommendations had been merged and deployed. In every case except the httpx sub-verification, the prerequisite fix was not deployed, making the measurement question INCONCLUSIVE.

Of 7 questions: 1 HEALTHY (Q16.3b), 2 FAILURE (Q16.3, Q16.4), 1 FAILURE/Medium (Q16.4b), 3 INCONCLUSIVE (Q16.1, Q16.2, Q16.5). Zero improvements observed.

---

### Wave 16 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q16.1 | INCONCLUSIVE | Medium | recall_dedup_hits_total not in /metrics; 6 metric families present, none dedup-related; 4 drop sites confirmed unmetered; prerequisite from Q15.1 undeployed |
| Q16.2 | INCONCLUSIVE | Medium | observer.py:176 still a bare `continue`; no logger.debug before it; 1-line fix from Q15.2 not deployed; observer dedup remains permanently invisible |
| Q16.3 | FAILURE | High | generate() signature confirmed: no `timeout` parameter; client constructed with 180s global timeout at init; `client.post()` passes no timeout kwarg; 43 confirmed >60s events remain unbounded |
| Q16.3b | HEALTHY | Low | httpx per-request timeout correctly overrides client-level default; Q16.3 fix approach verified architecturally sound; per-call `timeout=N` will work as expected |
| Q16.4 | FAILURE | High | Full 9-cell (4-site x 3-layer) matrix: 2/12 cells covered (signals.py structlog at DEBUG only); memory.py and observer.py have 0/3 layers each; compound gap from Q14.3+Q15.1+Q15.2 persists unchanged |
| Q16.4b | FAILURE | Medium | except:pass in memory.py lines 251-259 silently swallows all Qdrant errors during importance-inheritance; update_importance() has no internal error handling; no confirmation importance promotions ever succeed |
| Q16.5 | INCONCLUSIVE | Medium | prompt_metrics.metadata null for all 34,902 rows; file_extension not instrumented; >=70% empty-rate extension filter cannot be built; 3-file instrumentation chain not deployed |

---

## 11. Waves 15 and 14 Results (archived from prior synthesis — condensed)

**Wave 15** (Q15.1–Q15.5): Dedup observability crisis confirmed — three independent code paths produce zero audit entries, zero log entries, no Prometheus counter. Global LLM timeout 180s applies to all callers; 43 confirmed >60s events; per-call override does not exist. Q15.4 ruled out length-based pre-filtering. Q15.5 identified newline-density guard as a practical fast-fail alternative for dense single-line content.

**Wave 14** (Q14.1–Q14.9, Q14.4a, Q14.4b): Store-time dedup confirmed as silent pure drop (no merge, no audit, no Neo4j edge). Global Semaphore(1) deployed but p95 unchanged — root cause is inference variance not contention. 4,000-char truncation confirmed practical. Cross-type session summary dedup confirmed as source of 3 false-positive merges.

---

## 12. Cross-Wave Patterns (Waves 1–22)

### Pattern 1: Dedup observability gap — three waves, four sites, zero remediation (Q14.3, Q15.1, Q15.2, Q16.1, Q16.2, Q16.4) — SYSTEMIC / STALLED — Q20.4 confirms threshold correct

The semantic dedup subsystem has been investigated for three consecutive waves with zero remediation applied. Wave 18 (Q18.4) adds a critical clarification: the dedup mechanism is functionally correct — no double-stores occur. Wave 19 (Q19.5) adds the first empirical dedup rate: 2.8% batch near-duplicate rate from a single admin scan. **Wave 20 (Q20.4) resolves the threshold calibration question**: the 0.90–0.95 cosine band is empty on the live corpus. The threshold (0.92) is empirically correct — the raise from 0.90 eliminated false positives without sacrificing true duplicate detection.

**Consequence**: The system makes data retention decisions at an unknown real-time rate with zero audit trail. Batch scans confirm the threshold is correct but cannot reconstruct which real-time stores were dropped.

### Pattern 2: LLM timeout — five waves of investigation, zero remediation (Q15.3, Q16.3, Q16.3b, Q18.3, Q19.3) — FULLY CHARACTERIZED / STALLED

| Wave | Finding | Evidence |
|------|---------|----------|
| 15 | Q15.3 FAILURE | signal_detection_timeout=180s is global; no per-call override; 43 >60s events confirmed |
| 16 | Q16.3 FAILURE | generate() signature confirmed: no `timeout` param; client.post() passes no `timeout` kwarg |
| 16 | Q16.3b HEALTHY | httpx per-request override works: `client.post(url, timeout=N)` overrides client default |
| 18 | Q18.3 HEALTHY | 17 callsites audited; 4 tiers identified; no structural blockers; 2 PRs sufficient |
| 19 | Q19.3 WARNING | Per-caller timeouts bound inference phase only; queue wait unbounded; 104s worst-case total; priority routing required for interactive SLA |

The fix is now fully specified with one additional qualifier from Wave 19: per-caller timeouts are necessary but not sufficient for interactive SLA compliance. The compound fix requires both per-caller timeouts AND acquisition-timeout or priority routing for interactive callers.

### Pattern 3: Silent write failure paths — systemic anti-pattern, bounded scope (Q16.4b, Q18.1, Q18.2) — Q20.3 resolves observable signal ambiguity

Three independent code locations exhibit the same failure pattern: batch/loop write operations that can produce partial-write states with no audit trail identifying which items were affected. Wave 19 (Q19.1, Q19.2) confirmed the scope is bounded — no additional sites extend this cluster beyond the three known locations.

| Location | Pattern | Consequence |
|----------|---------|-------------|
| memory.py importance-inheritance (Q16.4b) | `except Exception: pass` | Qdrant errors swallowed; importance promotions silently fail |
| decay.py gather (Q18.1) | `asyncio.gather()` without `return_exceptions=True` | First error aborts batch; remaining memories un-decayed; audit log skipped |
| retrieval.py _track_access (Q18.2) | Bare awaits in fire-and-forget loop | First error terminates loop; N+1 memories get no access reinforcement |

**Wave 20 update**: Q20.3 resolves Q19.4's contamination signal — the 889-at-0.5 cluster was daily throughput (97% drain in 26h), not a persistent accumulation from these bugs. The bugs are real but their observable effect is the diffuse importance drift (1,315 mismatches from Q20.1), not the 0.5 cluster. Q20.5 shows these bugs interact with cluster 4 to produce compound failures.

### Pattern 4: Cross-store state divergence in consolidation — bounded by reconcile (Q19.6, Q20.1, Q20.5) — FAILURE / OPERATIONALLY BOUNDED / FIX FULLY SPECIFIED

Q19.6 opens a fourth cluster: the consolidation write loop at consolidation.py:272–283 processes Qdrant and Neo4j writes sequentially without a compensating rollback pattern. **Wave 20 provides critical operational context**: Q20.1 shows 0 superseded_mismatches on a corpus with 6,441 consolidation events — the weekly reconcile is successfully repairing split-brain. Q19.6's original assessment ("permanent divergence, no auto-repair path") is corrected: divergence is bounded by the weekly reconcile cycle (up to 7 days).

Q20.5 identified a reconcile design defect: compound failures (Q18.1 + Q19.6 co-occurring) cannot converge in a single reconcile pass because mark_superseded zeros Neo4j importance, overwriting the prior importance fix. **Wave 21 (Q21.1) collapses this**: the importance=0.0 is vestigial — removing it (one line in neo4j_store.py) eliminates the two-pass requirement entirely. **Wave 21 (Q21.4)** confirms qdrant.unmark_superseded() is 4 lines, completing the compensating rollback specification for Q19.6. All components of the fix are now fully specified.

### Pattern 5: Retrieval architecture — structural, not configurational (Q13.1, Q13.5, Q14.2, Q14.7)

The retrieval coverage crisis identified in Wave 13 (8.9% coverage, fixed K=3 vs. growing corpus) was re-measured in Wave 14 at 9.50% — essentially unchanged. Q14.2 confirmed that exploration-based injection is safe to deploy (90% relevance, 0% noise), providing the structural fix. **Q20.4 secondary finding**: active corpus is only 5,882 of 20,889 — K=3 achieves meaningfully better per-query hit rate against the active subset than against the total. The structural repair is less urgent than originally assessed, but the exploration injection from Q14.2 should still be deployed to surface buried high-value memories.

### Pattern 6: Remediation stall — nine consecutive waves find no improvements deployed (Waves 13–21)

In Waves 1–12, findings frequently referenced commits. Starting with Wave 13, the number of referenced commits drops to zero. Waves 14–21 have produced characterizations of failure clusters with no deployed remediation. The highest-value next action remains deployment, not continued investigation.

### Pattern 7: Reconcile observability gap — confirmed fixable (Q20.1, Q21.6)

The reconcile worker and admin API endpoint have zero audit_log entries. **Wave 21 (Q21.6)** confirms this is a 9-LOC fix. It is the same observability anti-pattern as the dedup subsystem (Q15.1, Q16.1): a critical repair operation runs regularly but its execution, results, and repair counts are invisible. Combined with Q20.5's (now one-line fixable) convergence issue, the 9-LOC audit trail fix is the fastest path to verifying compound failure resolution.

### Pattern 8: Superseded memory accumulation — cross-cutting concern confirmed (Q20.4 secondary, Q21.3, Q21.5) — NEW

The 72% superseded ratio (Q20.4 secondary) has downstream effects across three subsystems confirmed by Wave 21: GC unavailability (Q21.3), decay ghost users (Q21.5), and reconcile scan overhead (Q20.2). All three trace to the same root — no deletion mechanism exists for old superseded points. A single GC cron (Q21.3 specification: age ≥30d + successor active + simultaneous Neo4j DELETE) would address all three simultaneously. At current accumulation rate (~600/day), without GC the superseded-to-active ratio will continue to widen and all three downstream effects will worsen proportionally.

---

## 13. Prioritized Remediation Roadmap (Current State, post Wave 22)

Based on severity, feasibility, and number of waves confirming the gap. Items marked with `[N waves]` have been confirmed across multiple investigation cycles without remediation. **Wave 22 updates are bolded.**

### Tier 0 — Emergency hotfix (< 1 day, 3 lines)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 0 | **Fix double-decay in `_user_conditions(None)`**: filter system run to `user_id IS NULL` only — add `IsNullCondition(key="user_id")` to system-run Qdrant filter OR separate system-run and per-user run into non-overlapping entrypoints — **Q22.1 FAILURE: corpus has been decaying at 0.9216/slot instead of 0.96/slot; all memories losing importance ~2× faster than configured** | **~3 lines qdrant.py or decay.py** | **Q22.1** | **Stops double-decay immediately; every future slot decays at the correct single rate; importance values begin recovering toward intended baseline over next few weeks** |

### Tier 1 — Stop the bleeding (1-3 days, high confidence, 3-10 lines each)

| # | Action | Effort | Resolves | Expected Impact | Waves confirming |
|---|--------|--------|----------|-----------------|-----------------|
| 1 | **Add `timeout` parameter to `generate()`** and pass per-caller values (fact_extraction<=45s, consolidation<=90s, signal_detection<=15s) via `client.post(..., timeout=N)` — Q18.3 confirms 17 callsites in 4 tiers, 2 PRs sufficient | ~5 lines llm.py + 13 callsite files | Q15.3, Q16.3 | Bounds worst-case semaphore hold from 180s to per-type ceiling; eliminates 43+ >60s events; httpx override confirmed sound by Q16.3b; no structural blockers per Q18.3 | 5 waves |
| 2 | **Truncate inputs at 4,000 chars** in fact_extractor.py | ~5 lines | Q14.4b | Eliminates 37–93s p99 semaphore holds from long inputs; estimated p95 drop from ~15s to ~9s | 1 wave (uncontested) |
| 3 | **Add dedup counters at all four drop sites**: `metrics.increment("recall_dedup_hits_total", {"source": site})` | ~4 lines across 3 files | Q15.1, Q16.1 | Closes measurement gap; hit rate visible within first minute of deployment; enables Q16.4a measurement | 2 waves |
| 4 | **Add logger.info call** to observer.py before `continue` at line 176 | 1 line | Q15.2, Q16.2 | Makes observer dedup drops visible in Docker logs | 2 waves |

### Tier 1b — Critical additions from Waves 19–21 (1-2 days)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 5 | **Wrap consolidation source-supersedure loop** (consolidation.py:272–283) in per-source try/except with logger.error on failure; implement `qdrant.unmark_superseded()` as compensating rollback when Neo4j fails after Qdrant succeeds — **Q21.4 confirms: 4 lines qdrant.py** | ~30 lines consolidation.py + **4 lines qdrant_store.py** (confirmed by Q21.4) | Q19.6 | Prevents Qdrant/Neo4j split-brain; compensating rollback confirmed atomic and zero-regression |
| 6 | **Remove `m.importance = 0.0` from neo4j.mark_superseded** (neo4j_store.py:390–391) — **Q21.1 confirms: 1 line deletion, zero functional regressions; all Neo4j queries already have superseded_by IS NULL guards** | **1 line** | Q20.5 | Compound failures converge in one reconcile pass instead of two; eliminates sub-pattern-A production artifacts permanently; safer and simpler than the ~10-line reconcile.py fix previously specified |
| 7 | **Add reconcile audit_log entries** in reconcile.py and ops.py — **Q21.6 confirms: ~9 LOC, trivial import, fire-and-forget** | **~9 LOC across 2 files** (confirmed by Q21.6) | Q20.1 | Makes reconcile execution visible in audit trail; enables last-run-date query, mismatch trend, convergence monitoring |

### Tier 2 — Fix structural defects (3-7 days)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 8 | **Store-time dedup: write audit entry** preserving dropped content before returning `created=False` | ~10 lines memory.py | Q14.3, Q16.4 | Satisfies WARNING threshold (recoverable); prerequisite for content merge |
| 9 | **Fix except:pass in importance-inheritance block**: replace with `except Exception as e: logger.warning(...)` | ~3 lines memory.py | Q16.4b | Makes importance promotion failures visible; closes one of three cluster 3 sources |
| 10 | **Fix decay.py gather**: add `return_exceptions=True` with per-failure logging and accurate stats accounting | ~10 lines decay.py | Q18.1 | Prevents batch abort; enables per-failure logging; closes one of three cluster 3 sources; prevents Q20.5 compound failure entry path |
| 11 | **Fix _track_access() in retrieval.py**: wrap per-memory update block in try/except with continue + logger.warning | ~10 lines retrieval.py | Q18.2 | Converts loop-terminating exception to per-memory warning; closes one of three cluster 3 sources |
| 12 | **Add semaphore acquisition timeout for interactive callers** (`asyncio.wait_for` on semaphore acquire with budget=timeout/2 for callers with timeout<30s) | ~25 lines llm.py | Q19.3, Q14.4a | Ensures interactive signal_detection callers fail fast rather than waiting 89s in queue; required for interactive SLA compliance alongside Tier 1 fix #1 |
| 13 | **Tag-aware dedup exemption** for session-summary and session-checkpoint tags | ~5 lines memory.py | Q14.8, Q13.4a | Eliminates confirmed false-positive merges; prevents architectural knowledge loss in session summaries |
| 14 | **Exploration slot injection** in recall-retrieve.js (every 5th query, inject 2 buried high-importance memories) | ~40 lines in hook | Q13.1, Q14.7, Q14.2 | Surfaces buried high-importance memories; Q14.2 confirmed 90% relevant, 0% noise; note: active corpus only 5,882 (Q20.4) makes per-query coverage better than modeled at 20K |
| 15 | **Importance inheritance on dedup**: surviving memory gets `max(old.importance, new.importance)` | ~5 lines memory.py | Q13.4, Q13.4a | Prevents importance inversion; reduces importance drift accumulation |
| 16 | **Fix get_distinct_user_ids() to scan active-only**: add `IS NULL` filter on superseded_by — **Q21.5 confirms root cause; one-line filter change** | **~3 lines qdrant.py** | Q21.5 | Eliminates 7/10 ghost user decay runs per cron slot; reduces Qdrant scan from 20,923 to ~5,882 points per decay cycle (3.5× faster); eliminates 28 wasted scrolls/day |
| 17 | **Add user_id column to decay audit INSERT** — **Q22.7 confirms: 4 LOC (signature + INSERT + call site)** | **4 LOC decay.py** | Q21.5, Q22.7 | Makes ghost user identification possible from audit log without Qdrant direct queries |
| 18 | **Fix consolidation user_id attribution**: pass `user_id` to merged `Memory()` constructor in `consolidation.py:235` — **Q22.9 confirms: Memory() created without user_id; merged memories permanently get user_id=None** | **~3 lines consolidation.py** | Q22.9 | Prevents user memories consolidated by system run from losing user attribution; user appears in get_distinct_user_ids() after consolidation; preserves user-level decay, export, count |
| 19 | **Add post-repair visibility to reconcile response**: 6 LOC (2 counters + 2 loop increments + 2 response fields) — **Q22.6 confirms: no re-scan needed** | **6 LOC ops.py + reconcile.py** | Q22.6, Q21.2 | Operators can confirm `post_repair_importance_mismatches: 0` without running a second dry-run; prevents unnecessary re-invocation |

### Tier 3 — Observability and refinement (1-2 weeks)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 18 | **Thread file_ext through extraction pipeline**: pass `file_ext = Path(file_path).suffix.lower()` from observer.py to `log_prompt_metric()` via metadata jsonb | ~20 lines | Q13.2a, Q14.5, Q16.5 | Unlocks file-type breakdown of empty extractions; enables >=70% empty-rate extension pre-filter |
| 19 | **Promote signals.py dedup logs from DEBUG to INFO** | ~2 lines | Q16.4 | Makes signal dedup events visible in production without LOG_LEVEL=DEBUG |
| 20 | **Remove `session_summary` from `_dedup_skip_types`** — dead code; session summaries route via Graphiti not Qdrant | ~1 line memory.py | Q18.5 | Removes misleading code |
| 21 | **Add cross_val_predict + classification_report** to signal_classifier_trainer.py | ~15 lines | Q14.6 | Per-class precision/recall in retrain response; enables contradiction/warning merge decision |
| 22 | **Add newline-density pre-filter** in fact_extractor.py (skip if >500 chars and <0.001 newlines/char) | ~3 lines | Q15.5 | Eliminates membench synthetic log inference calls |
| 23 | **Coverage rate operational metric**: track `distinct_injected_30d / total_living_memories` in /admin/health | ~20 lines | Q13.1, Q13.5 | Ongoing monitoring; alert when coverage drops below threshold |
| 24 | **Increase Docker log retention**: `max-file=10, max-size=10m` (100MB cap) | 1 line docker-compose.yml | Q15.2 | Extends signal_semantic_dedup_hit log recovery window |
| 25 | **Sync admin dedup endpoint default threshold** with config `semantic_dedup_threshold` (currently endpoint defaults to 0.95 while config is 0.92) | ~3 lines ops.py | Q20.4 | Prevents silent parameter-name errors and mismatched threshold behavior |
| 26 | **Add superseded memory GC cron** — weekly ARQ job: delete Qdrant points where superseded_by IS NOT NULL AND invalid_at <now−30d AND successor active; delete corresponding Neo4j node simultaneously — **Q21.3 specifies: new ARQ cron + neo4j.delete_memory_node() helper** | **~30 lines + new Neo4j helper** | Q21.3, Q20.4 secondary | Caps superseded accumulation; reduces Qdrant storage (currently 72% superseded); reduces reconcile scan time; reduces ghost-user decay runs; first 30-day batch eligible ~2026-03-21 |
| 27 | **Add repair response post-repair state**: after applying repairs in reconcile, run a second scan and return post-repair counts in response — **Q21.2 identifies operator confusion risk** | ~15 lines reconcile.py | Q21.2 | Prevents operators from believing repair failed when it succeeded; response currently shows pre-repair state even after applying repairs |
| 28 | **Add qdrant.unmark_superseded() and neo4j.unmark_superseded() helpers** + admin endpoint `POST /admin/memories/{id}/unmark-superseded` — **Q21.4 specifies: 4 lines qdrant.py + 8 lines neo4j_store.py + ~8 lines admin route** | **~20 LOC** | Q21.4 | Enables manual reversal of erroneous supersedure; needed for admin correction workflows |

### Tier 4 — Markov rehabilitation (deferred, after Tier 1-3 complete)

| # | Action | Effort | Resolves |
|---|--------|--------|----------|
| 29 | Replace scroll_all() with targeted Qdrant MatchAny filter | ~30 lines markov_chain.py | Q14.9, Q13.8b |
| 30 | Add file:{normalized_path} tags during memory storage | ~5 lines observer.py | Q13.8 |
| 31 | Project-scoped Markov learning + lower confidence threshold to 2 | ~50 lines | Q13.8a |

Note: Markov feature should remain disabled (build_prefetch_cache short-circuited) until at least Tier 1 and Tier 2 are complete.

---

## 14. Open Threads for Wave 23

**Strong recommendation**: Wave 23 should be DEPLOYMENT ONLY. The research loop has now produced ten waves of characterization (13–22) with zero deployed remediation. All open clusters are fully characterized, operational impact is measured, compound interactions are mapped, and Wave 22 has fully specified all pending small fixes (Q22.4–Q22.8 provide implementation specs for 5 pending changes with total ≤38 LOC). Wave 22 also adds a new FAILURE (Q22.1 double-decay) that is trivially fixable (~3 lines). A further characterization wave would produce negligible marginal value. Deploy the Tier 1 fixes in order, starting with Q22.1 double-decay (highest severity, smallest fix), then answer Q16.3a and Q16.4a to verify impact.

### Post-deployment re-measurements (activate after Tier 1/1b deploy)

**Q16.3a — Per-caller timeout impact**: After deploying timeout parameter to generate(), does fact_extraction p99 drop below 60,000ms? Does total interactive latency drop, or does queue wait dominate?
*Prerequisite: Q16.3 fix deployed. Note: Q19.3 finding — measure queue wait phase separately from inference phase.*

**Q16.4a — Dedup hit rate baseline**: After deploying recall_dedup_hits_total counters, what is the 24h baseline hit rate per source?
*Prerequisite: Q15.1/Q16.1 instrumentation deployed.*

**Q23.1 — Post-GC verification**: After deploying the Tier 3 superseded GC cron (Q21.3), measure: (a) superseded-to-active ratio drops below 50%, (b) decay ghost-user count drops toward zero, (c) reconcile round-trip count decreases proportionally, (d) causal_extractor correctly excludes GC'd memories (since DECIDED_BECAUSE/ATTEMPTED_BEFORE/REVERTED_DUE_TO — not CAUSAL_PRECEDES).
*Prerequisite: Tier 3 fix deployed.*

**Q23.2 — Double-decay post-fix verification**: After deploying Q22.1 fix (IS NULL filter in _user_conditions or system-run filter), verify: (a) 10 decay_run entries per slot → 2 (system run + named users); (b) system-run audit entry proc count no longer equals full active corpus; (c) importance values in Qdrant post-fix are higher than pre-fix (corpus not over-decayed).
*Prerequisite: Q22.1 fix deployed.*

**Q23.3 — Consolidation user_id attribution propagation**: After fixing consolidation.py:235 to pass `user_id` to the merged Memory constructor, verify: (a) new merged memories have user_id set; (b) user_id=2 reappears in get_distinct_user_ids() after consolidation; (c) no regression on system-run consolidation (user_id=None runs should still produce user_id=None output).
*Prerequisite: consolidation user_id fix deployed.*

### Low-priority analytical questions (proceed only if deployment gating is impractical)

**Q23.4 — sub-pattern-A steady-state rate post-fix**: After deploying Q21.1 1-line removal of importance=0.0 from mark_superseded, does the reconcile importance_mismatches count stop growing? Measure weekly accumulation rate pre-fix vs post-fix.
*No prerequisite. Analytical.*

**Q23.5 — Neo4j unmark_superseded helper validation**: After implementing Q21.4's neo4j.unmark_superseded() helper and the admin /unmark-superseded endpoint, validate: (a) Qdrant unmark + Neo4j unmark produce a memory that passes reconcile dry-run with 0 mismatches, (b) repair=true does not re-supersede the restored memory.
*Prerequisite: Tier 3 fix #28 deployed.*

---

## 15. Residual Risk Inventory (Current State, post Wave 22)

| Risk | Severity | Likelihood | Trigger | Status |
|------|---------|-----------|---------|--------|
| **Double-decay: corpus decaying 2× faster than configured; every memory decays at 0.9216/slot instead of 0.96/slot** | **CRITICAL** | **Certain (every cron slot)** | **Every 15-minute decay run** | **OPEN — Q22.1 FAILURE; fix is ~3 lines in _user_conditions() or decay cron entrypoint; deployed fix needed immediately** |
| Dedup hit rate completely unquantifiable — unknown volume of unique facts permanently dropped | High | Active (31,289+ creates processed without measurement) | Every store event that triggers dedup path | OPEN — 4 waves unresolved (Q15.1, Q16.1); real-time rate unmeasurable; Q20.4 confirms threshold is correct but real-time rate still unknown |
| Global LLM timeout 180s — single slow call blocks entire pipeline for up to 180s | High | Active (43 confirmed >60s events) | Any consolidation or fact_extraction call with long input | OPEN — 5 waves unresolved (Q15.3, Q16.3); Q18.3 confirms fix deployable; Q19.3 adds queue-wait qualifier |
| Store-time dedup silent drop — unique facts in incoming write permanently lost with no audit trail | High | Active (every dedup event) | Any store that scores >0.92 against existing memory | OPEN — Q14.3 FAILURE; audit entry not deployed |
| Dedup observability matrix: 10/12 cells empty; memory.py and observer.py have zero coverage | High | Active (every dedup event) | Any dedup drop at API or observer path | OPEN — Q16.4 FAILURE |
| LLM p95 > 10s — Semaphore(1) + inference variance dominates; interactive callers can wait 89s in queue | High | Active (p95=11–17s post-semaphore; queue wait unbounded) | Any mix of long-inference (consolidation) + short (signal_detection) calls | OPEN — Q14.4 FAILURE; Q19.3 WARNING adds queue-wait gap; per-caller timeouts insufficient alone |
| Retrieval coverage structural failure — K=3 fixed vs. growing corpus; 9.5% lifetime coverage | High | Certain (coverage degrades with corpus growth) | Each new memory stored | OPEN — Q13.1, Q14.7; exploration injection from Q14.2 not deployed; note: active corpus only 5,882 (Q20.4) |
| Consolidation split-brain: Neo4j failure after Qdrant mark_superseded = divergence up to 7 days | High | Unknown (consolidation runs regularly; Neo4j transient errors possible) | Any Neo4j transient error during consolidation source-supersedure loop | OPEN — Q19.6 FAILURE; Q20.1 bounds impact (0 superseded_mismatches currently; weekly reconcile repairing); **Q21.4 confirms compensating rollback is 4 lines qdrant.py** |
| **Reconcile convergence defect: compound failures require two passes; mark_superseded overwrites Step A importance fix** | **High** | **Latent (9 entries produced historically; 0 active after Q21.2 repair)** | **Q18.1 partial gather + Q19.6 split-brain co-occurring on same memory** | **OPEN — Q20.5 FAILURE; Q21.1 collapses fix to 1-line removal of importance=0.0 from neo4j_store.py; not deployed** |
| **Reconcile audit invisibility: zero audit_log entries for any reconcile run — execution history unverifiable** | **Medium** | **Certain (reconcile runs weekly but never writes to audit_log)** | **Every reconcile run** | **OPEN — Q20.1 secondary; Q21.6 confirms 9-LOC fix; not deployed** |
| 1,315 importance mismatches (6.3% corpus): Qdrant/Neo4j drift from _track_access and compound failures | Medium | Active (Q21.2 resolved to 0 after repair; will re-accumulate) | Every _track_access exception (Q18.2) and every compound failure (Q20.5) | OPERATIONALLY BOUNDED — Q21.2 confirms repair=true converges in single pass; weekly reconcile resolves 1,313 mismatches automatically; residual 2 sub-pattern-A resolved by manual repair=true |
| except:pass in importance-inheritance block — Qdrant errors silently swallowed; promotions unconfirmed | Medium | Unknown (never logged) | Any Qdrant error during dedup drop at API path | OPEN — Q16.4b FAILURE; Q19.4 provides indirect evidence this is materializing |
| decay.py gather partial write — batch abort leaves partial Qdrant writes untracked; audit log skipped | Medium | Unknown (depends on decay_user_error frequency) | Any Qdrant error during decay batch execution | OPEN — Q18.1 WARNING; Q19.1 confirms scope is bounded to decay.py only |
| retrieval.py _track_access loop early exit — N+1 memories in retrieval batch miss access reinforcement | Medium | Unknown (depends on _track_access exception frequency) | Any storage error during retrieval stat update | OPEN — Q18.2 WARNING; Q19.2 confirms scope is bounded to _track_access only |
| Importance corpus contamination: Q16.4b + Q18.2 prevent importance promotion; 1,315 importance mismatches accumulating | Medium | Active (6.3% of corpus, measurable drift; resolves weekly) | Any dedup event (Q16.4b) or retrieval event (Q18.2) where write fails silently | OPEN — Q20.1 WARNING; re-accumulates between weekly reconcile runs |
| **Superseded memory storage bloat: ~15,007 superseded Qdrant points (72% of corpus); ~600 new/day; no GC** | **Medium** | **Certain (grows with every consolidation)** | **Every consolidation event creates superseded points that are never deleted** | **OPEN — Q21.3 WARNING; safe GC criteria confirmed (age ≥30d + successor active + Neo4j simultaneous); 30-day batch eligible ~2026-03-21; implementation: new ARQ cron + neo4j.delete_memory_node helper** |
| **Ghost users in decay: 7/10 decay_run entries/slot processed=0; overdecay ~4%/run for primary user** | **Medium** | **Certain (70% of user_id list are phantoms; grows with superseded accumulation)** | **Every cron slot; every decay run for primary user** | **OPEN — Q21.5 WARNING; Q22.2 confirms ghost identity; root cause confirmed (get_distinct_user_ids scans superseded); fix: IS NULL filter (1 line) + user_id in audit INSERT (4 LOC Q22.7)** |
| **Consolidation user_id attribution loss: merged memories get user_id=None permanently; user vanishes from get_distinct_user_ids() when all originals superseded** | **Medium** | **Certain (runs continuously; every system consolidation event)** | **Every consolidation of named-user memories by system run** | **OPEN — Q22.9 WARNING; root cause: consolidation.py:235 creates Memory() without user_id; fix: ~3 lines to pass user_id to merged Memory constructor** |
| Dedup threshold (0.92) empirically confirmed correct (Q20.4) — 0 pairs at 0.90 | Low | Resolved | — | **RESOLVED by Q20.4** — threshold is empirically correct; 0.90-0.95 band empty |
| observer.py semantic dedup: zero log call before continue — drops permanently unrecoverable | Medium | Active (every observer dedup event) | Dedup threshold fires on any observer-sourced memory | OPEN — 2 waves unresolved (Q15.2, Q16.2) |
| Session summaries: 3 confirmed false-positive merges; 5 near-misses; no tag-aware exemption | Medium | Active (low rate: 3.7% of consecutive pairs) | Any two sessions with similar boilerplate phrasing | OPEN — Q14.8 WARNING |
| fact_extraction empty rate 42.2%; 560 GPU-min/month wasted | Medium | Active (ongoing) | observe-edit.js fires on all edits including config/JSON | OPEN — Q13.2; pre-filter not implemented |
| file_extension absent from prompt_metrics — >=70% empty-rate extension filter blocked | Medium | Active (ongoing) | Every observer-triggered fact_extraction call | OPEN — Q16.5 INCONCLUSIVE |
| Signal classifier type_cv=0.6539 below 0.75 target; no per-class metrics | Low | Active | Tag-based filtering by type; per-class data unavailable | OPEN — Q13.7, Q14.6 |
| Session Markov Chain: tag vocabulary mismatch + O(N) scan + insufficient training data | Medium | Active (wasted CPU per file visit) | Every file edit triggers O(5,831) scan with 0 results | OPEN — Q13.8, Q14.9; feature not disabled |
| session_summary exemption in _dedup_skip_types is dead code — creates false impression of special handling | Low | Certain (always present) | Code review / future maintenance | OPEN — Q18.5; 1-line removal in Tier 3 |
| Admin dedup endpoint default threshold (0.95) differs from config semantic_dedup_threshold (0.92) | Low | Active (every admin dedup scan) | Admin invokes /admin/dedup without explicit threshold | OPEN — Q20.4; parameter name mismatch also observed |
| **Reconcile repair response format shows pre-repair state — operators may double-invoke repair=true unnecessarily** | **Low** | **Active (every repair=true invocation)** | **Admin calls POST /admin/reconcile?repair=true** | **OPEN — Q21.2 observability gap; ~15-line fix; no functional impact, only operator confusion** |
| _speculative_seeds concurrent writes (no hard lock) | Low | Very Low | Multiple simultaneous speculation triggers | OPEN — subsumed by Q7.1; single-instance deployment bounds risk |
| Decay correctness without live-infra CI | Info | Low | Qdrant/Neo4j schema changes | OPEN — Q7.3 skip-guarded test present; passes from homelab only |
| datetime.utcnow() in models.py field defaults | Info | Certain | Python version upgrade | OPEN — narrow residual from Q7.2 scope |

---

## 16. Waves 1–12 Baseline (summary, not modified)

Waves 1–12 produced 35 HEALTHY findings and 5 committed fixes covering: p99 search latency well under threshold at 40 concurrent users (Q1.1–Q1.4); domain isolation correct under concurrent writes (Q2.1); graph traversal guarded against cycles (Q3.4); all 4 background workers with structured exception logging (Q5.3); asyncio.Lock added to all async-mutated module-level state (Q7.1, e73858f); Pydantic v2 migration complete (Q7.2, 033ede9); datetime.utcnow() sweep complete across 23 files (Q6.7, 9cec9f4); all 4 worker test suites written and passing (Q5.7, Q7.6); embed_batch per-item fallback confirmed observable (Q6.1, 26da1aa); stdlib/structlog mismatch eliminated across all 77 src/ files (Q7.4). These findings remain confirmed holding.

**Key pre-condition**: The Waves 1–12 work addressed code quality and unit-test coverage. Wave 13 established that this well-built code is failing at its primary job — surfacing the right memories at the right time. Waves 14–21 have added twelve FAILURE/WARNING findings to the runtime behavior and documented a remediation stall pattern that has now run for nine consecutive waves.

**Wave 22 post-synthesis recommendation**: The research loop has produced maximum marginal value. The open clusters are fully characterized, all key fixes are specified with LOC estimates confirmed by code audit, and operational state is measured. **Immediate priority**: Deploy Tier 0 fix #0 (Q22.1 double-decay, ~3 lines) — the corpus is currently decaying 2× faster than configured and every passing 15-minute slot compounds the damage. Then deploy the 7 Tier 1/1b fixes in order (timeout parameter, input truncation, dedup counters, observer logging, consolidation try/except + qdrant.unmark_superseded, neo4j.mark_superseded 1-line removal, reconcile 9-LOC audit trail). Then answer Q16.3a and Q16.4a to verify impact. No further characterization waves are justified until at least Tier 0 + Tier 1 remediation is deployed.

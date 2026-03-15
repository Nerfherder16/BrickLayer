# Synthesis: Recall Autoresearch — Waves 1–24

**Generated**: 2026-03-15 (updated with Wave 24 findings)
**Questions answered**: 134 (Q1.1–Q1.5, Q2.1–Q2.5, Q3.1–Q3.5, Q4.1–Q4.6, Q5.1–Q5.4, Q5.6–Q5.7, Q6.1–Q6.7, Q7.1–Q7.6, Q13.1–Q13.8, Q13.1a–Q13.8b, Q14.1–Q14.9, Q14.4a, Q14.4b, Q15.1–Q15.5, Q16.1–Q16.5, Q16.3b, Q16.4b, Q18.1–Q18.5, Q19.1–Q19.6, Q20.1–Q20.6, Q21.1–Q21.6, Q22.1–Q22.9, Q23.1–Q23.7, Q24.1–Q24.8)
**Wave 17 questions (Q16.3a, Q16.4a)**: PENDING — deferred until Tier 1 fixes deployed
**Source codebase**: C:/Users/trg16/Dev/Recall/
**Stack**: FastAPI + Qdrant + Neo4j + Redis + PostgreSQL + Ollama (qwen3:14b + qwen3-embedding:0.6b)

---

## 1. Executive Summary

Twenty-four waves of autoresearch have been run against the Recall self-hosted memory system. Waves 1–12 established a well-tested, type-safe codebase. Wave 13 revealed structural failures at the retrieval architecture level. Waves 14–20 added five FAILURE-severity findings across five clusters: LLM timeout misconfiguration, dedup observability, silent write failures, consolidation split-brain, and reconcile convergence failure. Wave 20 was an operational measurement wave that confirmed compound failures are occurring in production.

Wave 24 was a **fix-verification wave** — the second consecutive attempt to confirm deployment of the Tier 0/1/1b fixes characterized across Waves 21–23. All five FAILURE questions confirmed fixes still not deployed. One WARNING confirmed (GC). Two HEALTHY findings corrected Wave 23 residual risk items.

**Wave 24 signal: 13 consecutive characterization waves (Waves 12–24), ZERO fixes deployed.** The system is operating with confirmed double-decay, attribution loss, ghost-user overhead, invisible reconcile runs, and accumulating stale storage. Every characterized fix remains undeployed. Wave 23's "new High severity" active-memory Neo4j sync gap risk (Q23.4) is CLOSED by Wave 24 investigation (Q24.3/Q24.4) — it was a temporal measurement artifact, not a standalone bug.

**Wave 24 key findings**:
- Q24.1: FAILURE — Double-decay fix not deployed (12th consecutive wave); `_user_conditions(None)` still returns `[]`; 15 observable 6-hour slots all show two full-corpus runs; 3-7d cohort ratio = 0.793 (identical to Q23.1 — zero recovery in 24h); 632 memories floor-clamped; Mar 15 timing anomaly (possible system restart) does not change the finding
- Q24.2: FAILURE — mark_superseded importance=0.0 fix not deployed; `neo4j_store.py:391` still sets `m.importance = 0.0`; 92 importance mismatches confirmed (all superseded); weekly reconcile auto-repairs on Sunday but accumulation resumes immediately at ~796/day; ~5,572 mismatches per week cycle
- Q24.3: HEALTHY with correction — Q23.4 "active-memory creation-path bug" hypothesis RULED OUT; zero active memories have neo4j=0.0; all 92 mismatches are superseded memories from the mark_superseded path; `create_memory_node()` explicitly sets importance from the memory object; Q23.4's "50 active mismatches" were temporal artifacts — newly-created memories that became superseded within hours; **Wave 23 synthesis "Active-memory Neo4j sync gap (new High severity)" risk item is CLOSED**
- Q24.4: HEALTHY — Q23.4 scope-change assertion was incorrect; both reconcile code paths use `include_superseded=True`; full-corpus scan (21,043 points) confirmed; Q23.4's "521+ superseded mismatches invisible" never existed as a static backlog — the weekly repair cycle has been running all along; no decision needed on backlog repair
- Q24.5: FAILURE — Consolidation user_id attribution fix not deployed; `consolidation.py:235` Memory() constructor confirmed missing `user_id=` argument; ~796 merged memories/day accumulate with user_id=None
- Q24.6: WARNING — GC window open; hygiene cron running daily at 4am but 0 memories archived to date; hygiene worker is active-only soft-delete (superseded memories explicitly excluded); no DETACH DELETE cron exists for old consolidation-superseded memories; ~11,000 memories are 30+ days past consolidation date and eligible; ~15,099 superseded memories accumulating with no automatic cleanup
- Q24.7: FAILURE — Ghost-user decay fix not deployed; `qdrant.py:1143-1162` `get_distinct_user_ids()` still scans all 21,043 Qdrant points with no IS NULL filter; 7 ghost user proc=0 entries per slot confirmed; 28+ wasted scroll operations per day continue
- Q24.8: FAILURE — Reconcile audit trail fix not deployed; zero reconcile entries in audit_log after multiple reconcile invocations; neither `reconcile.py` nor `ops.py` contains `log_audit()` calls; Q20.1 observability gap persists

Wave 23 produced 1 FAILURE (Q23.2), 2 WARNINGs (Q23.1, Q23.4), and 4 HEALTHYs (Q23.3, Q23.5, Q23.6, Q23.7). Q23.4's WARNING about "50 active-memory mismatches — different bug from Q21.1" is now corrected: Q24.3 confirms those were temporal artifacts. The correct picture: all importance mismatches come from the single mark_superseded path (Q21.1), which the weekly reconcile auto-repairs, and no separate creation-path bug exists.

**Overall health signal: CRITICAL — 13 CONSECUTIVE CHARACTERIZATION WAVES WITH ZERO FIXES DEPLOYED. FIVE OPEN FAILURE CLUSTERS. SYSTEM OPERATING WITH CONFIRMED DOUBLE-DECAY, USER ATTRIBUTION LOSS, GHOST-USER OVERHEAD, AND ACCUMULATING STALE STORAGE. THE Q23.4 "ACTIVE-MEMORY NEO4J SYNC GAP (HIGH SEVERITY)" RISK IS CLOSED — THERE IS NO CREATION-PATH BUG. THE ONLY NEO4J IMPORTANCE BUG IS Q21.1 (mark_superseded, ONE-LINE FIX). DEPLOYMENT IS THE ONLY REMAINING ACTION.**

---

## 2. Cumulative Findings by Verdict Tier (Waves 1–24)

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
| **Q23.2 / Q24.1** | **Double-decay FAILURE RECONFIRMED (12th consecutive wave): Q22.1 fix not deployed; `_user_conditions(None)` confirmed unchanged; 15 observable 6-hour slots all show two full-corpus proc entries; 3-7d cohort median ratio = 0.793 (Q23.1 parity — zero recovery in 24h); 632 memories (10.6%) floor-clamped; Mar 15 timing anomaly (possible system restart) does not resolve double-decay** | **High** | **23/24** |
| **Q24.2** | **mark_superseded importance=0.0 fix NOT deployed: `neo4j_store.py:391` still sets `m.importance = 0.0`; 92 importance mismatches confirmed, all from superseded memories; weekly reconcile auto-repairs Sunday 5:30am but accumulation resumes at ~796/day; ~5,572 mismatches per week cycle; retrieval unaffected (find_related filters superseded) but monitoring unreliable** | **Medium** | **24** |
| **Q24.5** | **Consolidation user_id attribution fix NOT deployed: `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; ~796 merged memories/day accumulate with user_id=None; users fully consolidated lose attribution permanently** | **Medium** | **24** |
| **Q24.7** | **Ghost-user decay fix NOT deployed: `qdrant.py:1143-1162` `get_distinct_user_ids()` scans all 21,043 points with no IS NULL filter; 7 ghost user proc=0 entries per slot confirmed; 28+ wasted scroll operations per day continue** | **Medium** | **24** |
| **Q24.8** | **Reconcile audit trail fix NOT deployed: zero reconcile entries in audit_log after multiple invocations; neither `reconcile.py` nor `ops.py` contains `log_audit()` calls; Q20.1 reconcile observability gap persists; monitoring of other fix verifications impaired** | **Medium** | **24** |

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
| **Q22.9** | **ARQ decay worker 6-hour outage (2026-03-14T18:15–00:01 UTC); 521 importance mismatches = Q21.1 bug accumulated over ALL historical consolidation (~521 supersedure events each creating 1 permanent Neo4j=0.0 vs Qdrant!=0 mismatch); user_id=2 data not deleted — consolidated into user_id=None merged form (consolidation.py:235 creates Memory() without user_id); disappears from get_distinct_user_ids() when ALL originals superseded; active corpus grew 5693→5936 confirming no data loss; dec=4544 catch-up at 00:01 is time-based formula, not bulk deletion** | **High** | **22** |
| **Q23.1** | **Double-decay damage quantified: 632 active memories (10.6%) clamped at 0.05 floor; 12 premature casualties in 3-7d age band (avg init_imp=0.583); median 3-7d importance 79.3% of expected single-decay baseline; ~217 importance-units stolen from 3-7d cohort; damage bounded by floor (0 below 0.05)** | **Medium** | **23** |
| **Q24.6** | **GC window open: hygiene cron running daily at 4am but 0 memories archived; hygiene is active-only soft-delete (IS NULL on superseded_by); no DETACH DELETE cron for consolidation-superseded memories; ~11,000 memories 30+ days past consolidation date eligible; 15,099 total superseded accumulating; Q21.3 GC cron recommendation still unimplemented** | **Medium** | **24** |

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
| Q20.3 | Importance=0.5 cluster is daily throughput artifact: 97% drain in 26 hours (889 -> 25); all same-day creates; 92% semantic type; Q16.4b casualties do not persistently cluster at 0.5; resolves Q19.4 ambiguity | 20 |
| Q20.4 | 0 duplicate pairs at 0.90 on 5,882 active; 1 pair at 0.95; 0.90-0.95 band empty; threshold raise confirmed correct; secondary: 72% of Qdrant points are superseded (5,882 active of 20,889 total) | 20 |
| Q20.6 | Decay audit coverage confirmed: 694 entries = per-user multiplier (9 users x 4 runs/day); single zero-day (2026-02-23) is 4.7% of expected cron slots; last 7 days show perfect 4/day coverage; no systematic Q18.1 audit gaps detected | 20 |

Wave 21 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q21.1 | importance=0.0 in neo4j.mark_superseded is vestigial: all Neo4j Cypher queries that filter on importance already have superseded_by IS NULL upstream; activation scaling uses or 0.5 fallback that overrides 0.0; one-line removal directly fixes Q20.5 reconcile two-pass convergence defect | 21 |
| Q21.2 | repair=true converges in single pass: 1,315→2 mismatches resolved by Sunday 05:30am reconcile cron; 2→0 resolved by manual repair=true; Q20.5 latent not active; repair response format shows pre-repair state (misleading for operators); 27 new stores in ~7h; zero orphans | 21 |
| Q21.4 | superseded_by and invalid_at are flat scalar strings; client.delete_payload removes both atomically; IsNullCondition treats absent keys as NULL — memory immediately reappears in active scroll after deletion; qdrant.unmark_superseded() is 4 lines; Neo4j side needs 8-line helper + importance restore | 21 |
| Q21.6 | postgres_store importable in reconcile via 1-line import; log_audit() fire-and-forget accepts metadata dicts; ~9 LOC across 2 files closes Q20.1 reconcile observability gap; enables last-run-date query, mismatch trend detection, repair convergence monitoring | 21 |

Wave 24 HEALTHY additions (corrections):

| ID | Finding | Wave |
|----|---------|------|
| Q24.3 | Active-memory Neo4j sync gap (Q23.4 hypothesis) RULED OUT: zero active memories have neo4j=0.0; all importance mismatches are from superseded memories via mark_superseded path; `create_memory_node()` explicitly sets `m.importance = $importance`; Q23.4's 50 "active" mismatches were temporal artifacts from newly-created memories superseded within hours; **Wave 23 "Active-memory Neo4j sync gap (High severity)" residual risk CLOSED** | 24 |
| Q24.4 | Reconcile scope is full-corpus (include_superseded=True) in both code paths: `reconcile.py:23` and `ops.py:262` both confirmed; Q23.4 assertion that "reconcile changed to active-only" was factually incorrect; `qdrant_total: 21,043` in reconcile output confirms full-corpus scan; no scope regression; Q23.4's "521+ superseded mismatches invisible" finding was based on incorrect scope assumption | 24 |

---

## 3. Wave 24 Results (Q24.1–Q24.8)

### Overview

Wave 24 was a **fix-verification wave** — checking whether the Tier 0/1/1b fixes characterized across Waves 21–23 had been deployed. Of 8 questions: 5 FAILURE, 1 WARNING, 2 HEALTHY (with corrections).

The defining result of Wave 24: **zero fixes deployed, thirteen consecutive waves of characterization with no remediation.** The five FAILURE findings are all reconfirmations of previously characterized bugs with known one-to-three-line fixes. The two HEALTHY findings close a false alarm — Q23.4's "new High severity active-memory creation-path bug" was a temporal measurement artifact, not a standalone defect.

**The Q23.4 correction**: Wave 23 raised a "new High severity" risk item — 50 active memories with neo4j=0.0 from a creation-path bug. Q24.3 rules this out completely. All current importance mismatches (92 total) are from superseded memories via the mark_superseded path. `create_memory_node()` sets importance correctly. Q23.4's "50 active mismatches" were newly-created memories that happened to be in an active state during Q23.4's measurement window but were superseded within hours by the running consolidation process. Q24.4 further corrects Q23.4's scope-change assertion — the reconcile has always scanned the full corpus (include_superseded=True). The weekly repair cycle explains why mismatch counts stay bounded.

**The GC window (Q24.6)**: The 30-day eligibility threshold has been crossed. The hygiene cron runs daily but has archived zero memories and is explicitly designed to exclude superseded memories. An estimated 11,000+ consolidation-superseded memories are now eligible for true GC (DETACH DELETE) but no such cron exists. The admin purge endpoint can perform manual cleanup.

**Double-decay persistence (Q24.1)**: The Q22.1 fix has now been undeployed through 12 characterization waves. The 3-7d cohort median importance ratio (0.793) is statistically identical to the Q23.1 baseline measured 24 hours earlier — confirming there is no self-correction mechanism and every passing day deposits more memories at the 0.05 floor. A possible system restart between Mar 14 18:15 and Mar 15 00:01 (timing anomaly in cron schedule) had no effect on the double-decay behavior.

---

### Wave 24 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q24.1 | FAILURE | High | Double-decay fix not deployed (12th consecutive wave); `_user_conditions(None)` returns `[]` confirmed; 15 observable 6-hour slots all show two full-corpus proc entries (proc≈active_corpus in both); 3-7d cohort ratio = 0.793 (Q23.1 parity — zero recovery); 632 memories floor-clamped; Mar 15 timing anomaly (00:01 single run, 06:45+06:49 4 min apart) suggests possible system restart but double-decay still manifest |
| Q24.2 | FAILURE | Medium | mark_superseded importance=0.0 fix not deployed; `neo4j_store.py:391` confirmed unchanged; 92 importance mismatches (all superseded); weekly Sunday 5:30am reconcile auto-repairs ~5,572 mismatches/week then accumulation resumes at ~796/day; active-memory retrieval unaffected (find_related filters superseded) but reconcile monitoring unreliable |
| Q24.3 | HEALTHY | Info | Q23.4 "active-memory creation-path bug" RULED OUT; zero active memories have neo4j=0.0; all 92 importance mismatches are superseded memories from mark_superseded path; `create_memory_node()` explicitly sets `m.importance = $importance` (line 100); Q23.4's 50 "active" mismatches were temporal: newly-created memories that became superseded within hours; Wave 23 "High severity" risk item closed |
| Q24.4 | HEALTHY | Info | Reconcile scope is full-corpus (include_superseded=True) in both `reconcile.py:23` and `ops.py:262`; Q23.4 scope-change assertion was incorrect; `qdrant_total: 21,043` confirms all 21,043 points scanned; no "15,000+ superseded mismatch backlog" — weekly repair cycle handles accumulation; no action required |
| Q24.5 | FAILURE | Medium | Consolidation user_id attribution fix not deployed; `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; ~796 merged memories/day accumulate with user_id=None; users fully consolidated lose attribution permanently |
| Q24.6 | WARNING | Medium | GC window open; hygiene cron (daily 4am) running but 0 archived; hygiene is active-only soft-delete (`IS NULL on superseded_by`); no DETACH DELETE cron for consolidation-superseded memories; ~11,144 memories estimated 30+ days past consolidation date (eligible); 15,099 total superseded with no scheduled cleanup; admin purge endpoint available for manual GC |
| Q24.7 | FAILURE | Medium | Ghost-user decay fix not deployed; `qdrant.py:1143-1162` confirmed scanning all 21,043 points with no filter; per-slot audit shows 7 ghost user proc=0 entries; 28+ wasted scroll operations per day |
| Q24.8 | FAILURE | Medium | Reconcile audit trail fix not deployed; GET /admin/audit?action=reconcile returns 0 entries despite multiple invocations; neither `reconcile.py` nor `ops.py` contains `log_audit()` call; Q20.1 reconcile observability gap persists |

---

### Wave 24 Cross-Domain Observations

#### Observation 1: The Q23.4 "new High severity" risk is closed — only one Neo4j importance bug exists

Wave 23's Q23.4 raised the prospect of two independent Neo4j importance sync bugs: the known mark_superseded path (Q21.1) and a new creation-path bug affecting active memories. Q24.3 rules out the creation-path bug completely. The current picture is simpler and more actionable: **there is exactly one Neo4j importance bug**, which is the one-line fix in `neo4j_store.py:391`. The weekly reconcile auto-repairs all accumulated mismatches every Sunday. The Q21.1 fix prevents new mismatches from being created. No secondary investigation is needed.

#### Observation 2: 13 consecutive characterization waves — the characterization work is complete

Wave 24 is the 13th consecutive wave (Waves 12–24) that found zero improvements deployed. All five FAILURE clusters are fully characterized, each with a known fix of 1–9 lines. The Tier 0 fix (Q22.1 double-decay) is ~3 lines. The Tier 1b fixes (Q21.1 mark_superseded, Q21.6 reconcile audit) are 1 line and 9 lines respectively. The consolidation attribution fix (Q24.5) is ~3 lines. The ghost-user fix (Q24.7) is ~3 lines. Total LOC for all five Wave 24 FAILURE fixes: approximately 20 lines across five files. **No further characterization is needed. The next action is deployment only.**

#### Observation 3: Weekly reconcile provides a damage-bounding safety net for the importance mismatch bug

Q24.2/Q24.4 together reveal that the mark_superseded importance=0.0 bug (Q21.1) has a built-in weekly repair cycle: the scheduled `run_reconcile()` every Sunday 5:30am repairs all mismatches (neo4j.importance = qdrant.importance for all mismatched memories). This means the observable mismatch count is bounded at ~5,572 (one week's accumulation at ~796/day) rather than growing unboundedly. The weekly repair does not fix the root cause, but it prevents the mismatch from permanently degrading graph queries that use Neo4j importance values.

#### Observation 4: GC eligibility is now active — manual intervention available

The 30-day GC window is open (Q24.6). An estimated 11,000 consolidation-superseded memories with `invalid_at < 2026-02-14` are eligible for DETACH DELETE. The admin purge endpoint exists and can perform manual cleanup. Until a scheduled GC cron is implemented (Tier 3 item #26), the stale memory accumulation and its downstream effects (ghost users, reconcile scan overhead, storage bloat) will continue growing.

---

## 4. Wave 23 Results (Q23.1–Q23.7)

### Overview

Wave 23 was a **damage-quantification and Q22.9-correction wave**. Having confirmed the Q22.1 double-decay FAILURE and the Q21.1 importance mismatch accumulation across ten waves without remediation, Wave 23 turned to measuring actual damage, correcting multiple Q22.9 mischaracterizations, and establishing the importance floor as a damage-bounding mechanism.

Of 7 questions: 1 FAILURE (Q23.2 — Q22.1 reconfirmation), 2 WARNING (Q23.1, Q23.4), 4 HEALTHY (Q23.3, Q23.5, Q23.6, Q23.7).

**The defining finding of Wave 23**: Double-decay is still active (Q23.2 FAILURE reconfirmation). The Q22.1 fix has not been deployed. Two system-level full-corpus runs fire 4 minutes apart (06:45 proc=5936 and 06:49 proc=5936), confirming the Phase 4 [system+system] slot structure. Separately, Q23.7 establishes that the importance floor mechanism (decay_default_floor=0.05 in tuning_config.py) successfully bounds the damage — no active memory has fallen below 0.05 despite the double-decay bug. This means the double-decay bug is causing accelerated floor-clamping (632 memories at 0.05 instead of ~200 expected under single-decay) rather than near-zero pollution.

**Q23.3's Q22.9 correction**: The Q22.9 finding contained a critical misinterpretation. `details.processed=2` in the decay audit record means "2 memories were processed", not "user_id=2 was the target". user_id=2 does not exist anywhere in the Qdrant corpus (neither active nor superseded). The user with 2 active memories is user_id=71. Q22.9's "user_id=2 data was consolidated then disappeared" narrative is structurally correct about the mechanism but factually wrong about which user was affected.

**Q23.4's WARNING** (subsequently corrected by Q24.3/Q24.4): The reconcile API was reported to have changed scope from all-memories to active-only, with 50 NEW active-memory mismatches from a creation-path bug. Q24.3 and Q24.4 confirm these findings were incorrect: the reconcile has always scanned the full corpus, and the 50 "active" mismatches were temporal artifacts from newly-superseded memories. The Wave 23 "Active-memory Neo4j sync gap (new High severity)" risk item is CLOSED.

**Q23.5's Q22.9 correction**: Consolidation does NOT run continuously. Wave 22's description of "continuously running consolidation worker" was based on observing a single hourly batch and misinterpreting its 64-second duration. The inter-batch gap is 3528-3540 seconds (~59 minutes), confirming a 1-hour fixed cron schedule.

**Q23.6's Q22.9 correction**: Per-supersedure audit entries (action=supersede) have always existed. Q22.9's use of the reconcile mismatch count as an indirect proxy was unnecessary.

---

### Wave 23 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q23.1 | WARNING | Medium | Double-decay damage quantified: 632 active memories at 0.05 floor (10.6%); 12 premature casualties in 3-7d age band (avg init_imp=0.583); median 3-7d importance = 79.3% of expected single-decay baseline; ~217 importance-units stolen from 3-7d cohort; floor bounds damage (0 memories below 0.05); 28-day corpus confirms no catastrophic collapse despite double-decay |
| Q23.2 | FAILURE | High | Q22.1 double-decay CONFIRMED still active: Phase 4 [system+system] slot structure; 06:45 and 06:49 audit entries both show proc=5936 (full-corpus); 4 minutes apart; no per-user runs visible in current observation window; Q22.1 Tier 0 fix not deployed; damage accumulating every cron slot |
| Q23.3 | HEALTHY | Info | All user_ids stored as int (float=0, str=0); user_id=2 non-existent in corpus; Q22.9 proc=2 misinterpretation corrected: `details.processed=2` means "2 memories were processed" not "user_id=2 was target"; actual user with 2 active memories is user_id=71 (ids 34d8d118 and 39836cee, created 2026-03-13T23:23-26) |
| Q23.4 | WARNING (corrected by Q24.3/Q24.4) | High → Closed | Reconcile scope reported as active-only and 50 NEW active-memory mismatches (neo4j=0.0) reported as creation-path bug — BOTH FINDINGS CORRECTED BY Q24: reconcile scope is full-corpus; the 50 "active" mismatches were temporal artifacts; no creation-path bug exists; Wave 23 "High severity" residual risk item CLOSED |
| Q23.5 | HEALTHY | Info | Consolidation worker runs on 1-hour fixed cron schedule (NOT continuously); 3528-3540s inter-batch gaps confirmed; each batch runs ~64 seconds and processes 1-28 consolidations; Q22.9 "continuously running" characterization incorrect; batch count tracks corpus freshness (27 at peak, 1 when exhausted) |
| Q23.6 | HEALTHY with caveat | Info | Per-supersedure audit entries confirmed (action=supersede, memory_id=source, details.superseded_by=merged, actor=consolidation); 1000 visible entries (3 days at 700/day rate); Q22.9 indirect proxy via reconcile mismatch count was unnecessary — direct evidence existed; CAVEAT: user_id=null in all entries requires memory table join for user attribution |
| Q23.7 | HEALTHY | Info | Importance floor is configured constant decay_default_floor=0.05 in tuning_config.py with 3-tier graph-aware floors (hub=0.3, moderate=0.15, default=0.05); floor applied explicitly via max(floor, new_importance) in decay.py:167; live corpus confirms min=0.05, 0 below floor; floor value equals min_importance_for_retrieval=0.05; GC threshold 0.3 above floor but requires age>30d+access_count=0 — intended lifecycle path; near-zero pollution hypothesis ruled out |

---

### Wave 23 Cross-Domain Observations

#### Observation 1: Double-decay damage is bounded but accumulating — floor is the only protection

Wave 23 quantifies the double-decay damage precisely: 632 memories (10.6%) are clamped at the 0.05 floor, arriving there 3× faster than they should under single-decay. The importance floor (Q23.7) is the only mechanism preventing near-zero pollution — without it, the damage would be catastrophic. The floor holds, but each passing day deposits more memories at the floor boundary. The Q22.1 Tier 0 fix remains the highest-priority undeployed change.

#### Observation 2: Q23.4's "two independent Neo4j sync bugs" finding was incorrect — corrected by Q24

Wave 23 (Q23.4) suggested two independent Neo4j importance bugs: the mark_superseded path (Q21.1) and a new creation-path bug. Q24.3 rules out the creation-path bug. There is exactly one Neo4j importance bug: the mark_superseded path. The simplification has no effect on remediation priority but does close the Wave 23 "High severity" open risk item.

#### Observation 3: Q22.9 contained three factual errors — corrected by Wave 23

Wave 22's Q22.9 was the most information-rich finding but contained three mischaracterizations, all corrected in Wave 23:
1. **proc=2 = user_id=2** (Q22.9) → **proc=2 = 2 memories processed** (Q23.3). user_id=2 does not exist.
2. **Consolidation runs continuously** (Q22.9) → **1-hour fixed cron, 64s batches** (Q23.5)
3. **Supersede events required indirect inference via reconcile mismatch count** (Q22.9) → **Direct audit evidence existed (action=supersede)** (Q23.6)

None of these corrections change the severity of Q22.1, Q21.1, or Q22.9's structural findings.

---

## 5. Wave 22 Results (Q22.1–Q22.9)

### Overview

Wave 22 was a **fix-specification and corpus-integrity wave** — following Wave 21's identification of ghost-user decay waste (Q21.5), reconcile response opacity (Q21.2), and the Q21.1 importance=0.0 vestigial bug, Wave 22 mapped the double-decay bug, confirmed ghost user identity, verified fix scope for 6 pending changes, measured GC threshold readiness, probed causal GC safety, and reconstructed a 6-hour corpus state anomaly that surfaced 521 importance mismatches and the disappearance of the primary user from the decay loop.

Of 9 questions: 1 FAILURE (Q22.1), 2 WARNING (Q22.2, Q22.9), 6 HEALTHY (Q22.3–Q22.8).

**The defining finding of Wave 22**: Q22.1 is a new FAILURE — the system's decay mechanism has been running at double-speed since the per-user cron was introduced. `_user_conditions(None)` returns `[]` (no filter), so the system run processes all active memories without restriction. In a 15-minute cron slot, a memory is decayed once in the system run and again in its per-user run: the combined factor is `0.96 × 0.96 = 0.9216` per slot instead of the intended `0.96`. At 96 slots/day, the effective daily decay factor is `0.9216^96 ≈ 0.00028` instead of `0.96^96 ≈ 0.0199`. The corpus is decaying ~71× faster per day than the decay configuration intends, and every memory that should decay to importance 0.10 after 30 days is already at <0.001.

**Q22.9's compound revelation**: The 6-hour ARQ outage (18:15–00:01) is a secondary finding — the primary revelation is that the 521 importance mismatches are a direct, counting accumulation of the Q21.1 bug: every single consolidation event since the system was deployed has created 1 permanent reconcile mismatch. With ~521 supersedure events in the visible audit history and a continuously running consolidation worker, this count will grow indefinitely until the one-line mark_superseded fix is deployed. The user_id attribution loss pattern confirms a production consolidation design gap: consolidated memories get `user_id=None` permanently, breaking user-level decay, export, and memory ownership tracking.

**Q22.3's GC timing snapshot**: The 30-day GC threshold has not yet been crossed (earliest audit 2026-03-02, 13 days ago). The first large eligible batch is ~2026-04-01. The 507-entry overnight consolidation wave from the Q22.9 anomaly window becomes 14-day eligible on 2026-03-27. No urgent GC window is open, but the clock is running. **(Wave 24 update: the GC window is now open — Q24.6 confirms 11,000+ eligible memories.)**

---

### Wave 22 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q22.1 | FAILURE | High | `_user_conditions(None)` returns `[]` → system run processes ALL active memories; every cron slot decays all memories twice (system + per-user); effective decay 0.9216/slot vs 0.96 intended; corpus decaying 2× faster than configured; fix: filter system run to `user_id IS NULL` only via `IsNullCondition` or `MatchAny` |
| Q22.2 | WARNING | Medium | Ghost users = exhausted legacy user_ids with 0 active memories (stored as float in Qdrant; `int(uid)` conversion surfaces them); not in PostgreSQL users table; stale user_ids persist as long as superseded memories exist; primary anomaly: user_id=2 absent from decay post-consolidation, 521 mismatches re-appeared |
| Q22.3 | HEALTHY | Info | 0 superseded memories ≥30 days old (system 13d old); first GC batch ~2026-04-01; 507-entry overnight wave (Q22.9 anomaly) eligible at 14d threshold 2026-03-27; no urgent GC window open (Wave 24 update: window now open per Q24.6) |
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

Wave 21 confirmed that removing `importance=0.0` from `mark_superseded` was safe. Wave 22 confirms that NOT removing it is costly: every consolidation event since deployment has created a permanent reconcile mismatch. The 521 count will grow with every future consolidation. With a consolidation worker running hourly, the rate of new mismatches is approximately the supersedure rate (estimated ~600/day from Q21.3). Reconcile repair can clear these (as Q21.2 demonstrated), but only by calling `repair=true` and only by re-syncing the importance field from Qdrant. The one-line removal from `mark_superseded` would stop new mismatches from being created.

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

## 6. Wave 21 Results (Q21.1–Q21.6)

### Overview

Wave 21 was a **reconcile/superseded subsystem deep-dive**. Following Wave 20's identification of the Q20.5 compound-failure/two-pass-convergence defect, Wave 21 investigated: Is the importance=0.0 assignment in mark_superseded safe to remove? Does repair=true actually converge? How should superseded memories be GC'd? What is the Qdrant payload structure for reversal? Why are there ghost users in decay? Is the reconcile audit trail feasible?

Of 6 questions: 4 HEALTHY (Q21.1, Q21.2, Q21.4, Q21.6), 2 WARNING (Q21.3, Q21.5). No new FAILURE findings. The wave materially de-risked the Q20.5 fix (Q21.1 confirms it is a one-line deletion), confirmed the corpus is currently clean (Q21.2), and revealed two new medium-severity issues in adjacent subsystems (GC bloat Q21.3, ghost-user decay waste Q21.5).

**The defining finding of Wave 21**: Q21.1 provides the clearest finding of any wave — the importance=0.0 in neo4j.mark_superseded is vestigial by complete audit. Zero Cypher queries use importance as an active/superseded proxy. The defensive intent of the assignment failed from inception: the queries it was meant to protect already had superseded_by IS NULL guards, and the activation scaling code uses `or 0.5` which overrides 0.0 anyway. Removing the one line directly fixes Q20.5 without any retrieval, scoring, or graph-traversal regression.

**Q21.2's operational confirmation**: The concern that repair=true might create new mismatches (the Q20.5 scenario) was not observed. The Sunday reconcile cron cleared 1,313 of 1,315 mismatches automatically. The 2 remaining sub-pattern-A entries were repaired in a single pass because their superseded_by fields were already reconciled — only the importance residual remained, which Step A fixed without Step B firing. Q20.5's two-pass scenario requires simultaneous superseded and importance mismatches, which are not currently present. The defect is latent, not active.

**Q21.3's unbounded accumulation warning**: The superseded GC question reveals two issues: (a) causal_extractor.py accesses superseded memories in the live POST /store path, making deletion non-trivially safe, and (b) ~600 new superseded points per day with no deletion mechanism means the 72% superseded ratio will continue growing indefinitely. At the 30-day threshold, the first large GC batch becomes eligible ~2026-03-21. Without GC, reconcile scan time, storage, and decay user-list scan overhead all grow proportionally. **(Wave 24 update: GC threshold has been crossed — Q24.6 confirms ~11,000 eligible memories.)**

**Q21.5's ghost-user decay finding**: The decay loop processes 10 user_ids per cron slot but 7 of them have zero active memories. The root cause (get_distinct_user_ids scans all 20,923 points including superseded) connects directly to Q21.3 — as the superseded population grows, the number of ghost users will grow. The primary user being processed twice per slot (overdecay ~4% per run) is the most actionable finding.

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

Wave 20 framed Q20.5 as a reconcile design defect requiring either step-ordering logic or a two-pass execution. Q21.1 reframes the problem entirely: the root cause is that mark_superseded sets importance=0.0 at all, which has been vestigial since it was written. Removing the one line eliminates the defect naturally, without any change to reconcile's step ordering, without any impact on retrieval, and without any compensating rollback logic.

#### Observation 2: Q21.2 provides the first live verification of reconcile repair effectiveness

Wave 20 measured the corpus state but did not run repair=true. Wave 21 executed the full repair cycle: baseline → repair run → post-repair verification. The result (0 mismatches after single pass) is the most direct evidence yet that the reconcile mechanism is working. The 99.8% reduction from 1,315 to 2 by the Sunday cron confirms the weekly schedule is sufficient at current compound failure rates.

#### Observation 3: Q21.3 and Q21.5 reveal that the superseded memory accumulation is a cross-cutting concern

The 72% superseded ratio noted as a secondary finding in Q20.4 now has three downstream effects confirmed across Wave 21:
1. **GC unavailability** (Q21.3): causal_extractor access makes simple deletion unsafe; requires age threshold + simultaneous Neo4j cleanup
2. **Decay ghost users** (Q21.5): get_distinct_user_ids() scans superseded points, returning user_ids with 0 active memories; each produces a wasted cron slot
3. **Reconcile scan overhead** (Q20.2): scroll_all with include_superseded fetches 3.5x more data than needed

All three trace to the same root: superseded memories are never deleted. The GC implementation (Q21.3 specification) would fix all three simultaneously.

#### Observation 4: Q21.4 enables the Q19.6 compensating rollback

Q21.4 confirms that qdrant.unmark_superseded() is a 4-line atomic operation. This directly enables the Tier 1b fix #5 (consolidation compensating rollback): when Neo4j.mark_superseded fails after Qdrant.mark_superseded succeeds, calling qdrant.unmark_superseded(id) restores the Qdrant side without re-insertion.

#### Observation 5: The remediation stall deepens — yet Q21 findings lower implementation risk for all major fixes

Waves 13–21 have produced characterizations without deployed remediation. However, Wave 21 has reduced implementation uncertainty on the most critical open items:
- Q20.5 fix: was ~10 lines reconcile.py → now **1 line neo4j_store.py** (Q21.1)
- Q20.1 audit trail: was unspecified → now **9 LOC fully specified** (Q21.6)
- Q19.6 compensating rollback: qdrant side was uncertain → now **4 lines confirmed** (Q21.4)
- Decay ghost users: root cause was unclear → now **one-line IS NULL filter** (Q21.5)

---

## 7. Wave 20 Results (Q20.1–Q20.6)

### Overview

Wave 20 was an **operational measurement and compound-failure investigation wave**. Following seven waves of characterization without deployment, Wave 20 turned to live production queries to measure whether the characterized failures were materializing, at what rate, and whether self-repair mechanisms (reconcile, decay) were bounding the damage. The wave also investigated whether the four open failure clusters could interact to produce compound states worse than any single cluster.

Of 6 questions: 4 HEALTHY (Q20.2, Q20.3, Q20.4, Q20.6), 1 WARNING (Q20.1), 1 FAILURE (Q20.5).

**The defining finding of Wave 20**: The compound failure (Q20.5) demonstrates that clusters 3 and 4 interact — Q18.1 (partial gather) and Q19.6 (split-brain) can co-occur on a single memory in one consolidation cycle, producing a state that reconcile cannot fully repair in a single pass. More critically, reconcile itself introduces a NEW importance mismatch while repairing the superseded_by mismatch (mark_superseded zeros Neo4j importance, overwriting the Step A importance fix). This is a **reconcile design defect**, not just a compound failure reachability finding. The 9 sub-pattern-A entries in Q20.1 are direct production evidence that this has already occurred. **Wave 21 update**: Q21.1 collapses this to a 1-line vestigial removal; Q21.2 confirms 0 active compound failures after repair.

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

## 8. Wave 19 Results (Q19.1–Q19.6)

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

## 9. Wave 18 Results (Q18.1–Q18.5)

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

## 10. Wave 17 Status (Q16.3a, Q16.4a — PENDING)

Wave 17 was planned as a post-deployment verification wave with two questions:

**Q16.3a** — Per-caller timeout post-deployment: after adding `timeout` parameter to `generate()`, does fact_extraction p99 semaphore hold drop below 60s?
*Status: PENDING — prerequisite (Q16.3 fix) not deployed. Cannot be answered until timeout parameter is deployed. Note: Q19.3 adds a qualifier — even after deployment, interactive callers can wait 89s in queue; Q16.3a should measure total latency (queue + inference), not inference alone.*

**Q16.4a** — Dedup drop volume post-instrumentation: after adding `recall_dedup_hits_total`, what fraction of daily stores are dedup-dropped, and does the API store path fire more often than observer?
*Status: PENDING — prerequisite (Q15.1/Q16.1 instrumentation) not deployed. Cannot be answered until dedup counters are deployed.*

These two questions remain the highest-priority measurement questions in the queue.

---

## 11. Wave 16 Results (Q16.1–Q16.5, Q16.3b, Q16.4b)

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

## 12. Waves 15 and 14 Results (archived from prior synthesis — condensed)

**Wave 15** (Q15.1–Q15.5): Dedup observability crisis confirmed — three independent code paths produce zero audit entries, zero log entries, no Prometheus counter. Global LLM timeout 180s applies to all callers; 43 confirmed >60s events; per-call override does not exist. Q15.4 ruled out length-based pre-filtering. Q15.5 identified newline-density guard as a practical fast-fail alternative for dense single-line content.

**Wave 14** (Q14.1–Q14.9, Q14.4a, Q14.4b): Store-time dedup confirmed as silent pure drop (no merge, no audit, no Neo4j edge). Global Semaphore(1) deployed but p95 unchanged — root cause is inference variance not contention. 4,000-char truncation confirmed practical. Cross-type session summary dedup confirmed as source of 3 false-positive merges.

---

## 13. Cross-Wave Patterns (Waves 1–24)

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

### Pattern 6: Remediation stall — thirteen consecutive waves find no improvements deployed (Waves 12–24)

In Waves 1–12, findings frequently referenced commits. Starting with Wave 13, the number of referenced commits drops to zero. Waves 13–24 have produced characterizations of failure clusters with no deployed remediation. The highest-value next action remains deployment, not continued investigation.

### Pattern 7: Reconcile observability gap — confirmed fixable (Q20.1, Q21.6) — Q24.8 reconfirms unfixed

The reconcile worker and admin API endpoint have zero audit_log entries. **Wave 21 (Q21.6)** confirms this is a 9-LOC fix. **Wave 24 (Q24.8)** reconfirms the fix is still not deployed. It is the same observability anti-pattern as the dedup subsystem (Q15.1, Q16.1): a critical repair operation runs regularly but its execution, results, and repair counts are invisible.

### Pattern 8: Superseded memory accumulation — cross-cutting concern, GC window now open (Q20.4 secondary, Q21.3, Q21.5, Q24.6)

The 72% superseded ratio (Q20.4 secondary) has downstream effects across three subsystems confirmed by Wave 21: GC unavailability (Q21.3), decay ghost users (Q21.5), and reconcile scan overhead (Q20.2). All three trace to the same root — no deletion mechanism exists for old superseded points. A single GC cron (Q21.3 specification: age ≥30d + successor active + simultaneous Neo4j DELETE) would address all three simultaneously. **Wave 24 (Q24.6) confirms the 30-day eligibility window is open**: ~11,000 memories are eligible for true GC but no scheduled cron exists. Admin purge endpoint available for manual cleanup.

### Pattern 9: Double-decay — twelve consecutive failure confirmations, zero remediation (Q22.1, Q23.2, Q24.1)

The double-decay bug was first confirmed as a FAILURE in Wave 22. It has been reconfirmed in every subsequent wave (Waves 23 and 24). The 3-7d cohort importance ratio (0.793) measured in Q24.1 is statistically identical to Q23.1's baseline from 24 hours earlier — there is no self-correction mechanism. The fix is ~3 lines. The damage compounds with every 6-hour cron slot.

---

## 14. Prioritized Remediation Roadmap (Current State, post Wave 24)

Based on severity, feasibility, and number of waves confirming the gap. Items marked with `[N waves]` have been confirmed across multiple investigation cycles without remediation. **Wave 24 updates are bolded.**

### Tier 0 — Emergency hotfix (< 1 day, 3 lines)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 0 | **Fix double-decay in `_user_conditions(None)`**: filter system run to `user_id IS NULL` only — add `IsNullCondition(key="user_id")` to system-run Qdrant filter OR separate system-run and per-user run into non-overlapping entrypoints — **Q22.1 FAILURE: corpus has been decaying at 0.9216/slot instead of 0.96/slot; Q24.1 confirms fix still not deployed after 12 consecutive waves** | **~3 lines qdrant.py or decay.py** | **Q22.1, Q23.2, Q24.1** | **Stops double-decay immediately; every future slot decays at the correct single rate; importance values begin recovering toward intended baseline over next few weeks** |

### Tier 1 — Stop the bleeding (1-3 days, high confidence, 3-10 lines each)

| # | Action | Effort | Resolves | Expected Impact | Waves confirming |
|---|--------|--------|----------|-----------------|-----------------|
| 1 | **Add `timeout` parameter to `generate()`** and pass per-caller values (fact_extraction<=45s, consolidation<=90s, signal_detection<=15s) via `client.post(..., timeout=N)` — Q18.3 confirms 17 callsites in 4 tiers, 2 PRs sufficient | ~5 lines llm.py + 13 callsite files | Q15.3, Q16.3 | Bounds worst-case semaphore hold from 180s to per-type ceiling; eliminates 43+ >60s events; httpx override confirmed sound by Q16.3b; no structural blockers per Q18.3 | 5 waves |
| 2 | **Truncate inputs at 4,000 chars** in fact_extractor.py | ~5 lines | Q14.4b | Eliminates 37–93s p99 semaphore holds from long inputs; estimated p95 drop from ~15s to ~9s | 1 wave (uncontested) |
| 3 | **Add dedup counters at all four drop sites**: `metrics.increment("recall_dedup_hits_total", {"source": site})` | ~4 lines across 3 files | Q15.1, Q16.1 | Closes measurement gap; hit rate visible within first minute of deployment; enables Q16.4a measurement | 2 waves |
| 4 | **Add logger.info call** to observer.py before `continue` at line 176 | 1 line | Q15.2, Q16.2 | Makes observer dedup drops visible in Docker logs | 2 waves |

### Tier 1b — Critical additions from Waves 19–22 (1-2 days)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 5 | **Wrap consolidation source-supersedure loop** (consolidation.py:272–283) in per-source try/except with logger.error on failure; implement `qdrant.unmark_superseded()` as compensating rollback when Neo4j fails after Qdrant succeeds — **Q21.4 confirms: 4 lines qdrant.py** | ~30 lines consolidation.py + **4 lines qdrant_store.py** (confirmed by Q21.4) | Q19.6 | Prevents Qdrant/Neo4j split-brain; compensating rollback confirmed atomic and zero-regression |
| 6 | **Remove `m.importance = 0.0` from neo4j.mark_superseded** (neo4j_store.py:391) — **Q21.1 confirms: 1 line deletion, zero functional regressions; Q24.2 reconfirms fix not deployed** | **1 line** | Q20.5, Q24.2 | Stops new importance mismatches from being created; compound failures converge in one reconcile pass; eliminates weekly ~5,572-mismatch accumulation cycle |
| 7 | **Add reconcile audit_log entries** in reconcile.py and ops.py — **Q21.6 confirms: ~9 LOC, trivial import, fire-and-forget; Q24.8 reconfirms fix not deployed** | **~9 LOC across 2 files** (confirmed by Q21.6) | Q20.1, Q24.8 | Makes reconcile execution visible in audit trail; enables last-run-date query, mismatch trend, convergence monitoring |

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
| 16 | **Fix get_distinct_user_ids() to scan active-only**: add `IS NULL` filter on superseded_by — **Q21.5 confirms root cause; one-line filter change; Q24.7 reconfirms fix not deployed** | **~3 lines qdrant.py** | Q21.5, Q24.7 | Eliminates 7/10 ghost user decay runs per cron slot; reduces Qdrant scan from 21,043 to ~5,945 points per decay cycle; eliminates 28 wasted scrolls/day |
| 17 | **Add user_id column to decay audit INSERT** — **Q22.7 confirms: 4 LOC (signature + INSERT + call site)** | **4 LOC decay.py** | Q21.5, Q22.7 | Makes ghost user identification possible from audit log without Qdrant direct queries |
| 18 | **Fix consolidation user_id attribution**: pass `user_id` to merged `Memory()` constructor in `consolidation.py:235` — **Q24.5 reconfirms fix not deployed; ~796 merged memories/day accumulating with user_id=None** | **~3 lines consolidation.py** | Q22.9, Q24.5 | Prevents user memories consolidated by system run from losing user attribution; user appears in get_distinct_user_ids() after consolidation; preserves user-level decay, export, count |
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
| 26 | **Add superseded memory GC cron** — weekly ARQ job: delete Qdrant points where superseded_by IS NOT NULL AND invalid_at <now−30d AND successor active; delete corresponding Neo4j node simultaneously — **Q21.3 specifies: new ARQ cron + neo4j.delete_memory_node() helper; Q24.6 confirms ~11,000 eligible memories NOW** | **~30 lines + new Neo4j helper** | Q21.3, Q20.4 secondary, Q24.6 | Caps superseded accumulation; reduces Qdrant storage; reduces reconcile scan time; reduces ghost-user decay runs; manual cleanup available via admin purge endpoint until cron implemented |
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

## 15. Open Threads for Wave 25

**Strong recommendation**: Wave 25 should be DEPLOYMENT ONLY. Thirteen consecutive waves (12–24) have produced characterizations with zero deployed remediation. Wave 24 confirms all five Tier 0/1b FAILUREs are still not deployed. The Tier 0 fix (Q22.1 double-decay) is ~3 lines. All five Wave 24 FAILURE fixes combined are approximately 20 lines across five files. Wave 24 closed the last open investigation question (Q23.4's creation-path bug hypothesis). **There are no remaining analytical questions that justify further delay. Deploy the Tier 0 fix immediately, then Tier 1/1b in order.**

If deployment remains blocked for reasons external to this research loop, the Wave 25 queue should be treated as follows:

### Post-deployment re-measurements (activate only after Tier 1/1b deploy)

**Q16.3a — Per-caller timeout impact**: After deploying timeout parameter to generate(), does fact_extraction p99 drop below 60,000ms? Does total interactive latency drop, or does queue wait dominate?
*Prerequisite: Q16.3 fix deployed. Note: Q19.3 finding — measure queue wait phase separately from inference phase.*

**Q16.4a — Dedup hit rate baseline**: After deploying recall_dedup_hits_total counters, what is the 24h baseline hit rate per source?
*Prerequisite: Q15.1/Q16.1 instrumentation deployed.*

**Q24.1-post — Double-decay post-fix verification**: After deploying Q22.1 fix (IS NULL filter in _user_conditions or system-run filter), verify: (a) each 6-hour slot shows exactly ONE full-corpus proc entry (system run) plus per-user entries; (b) 3-7d cohort ratio begins recovering above 0.793 baseline; (c) floor-clamped memory count begins decreasing.
*Prerequisite: Q22.1 fix deployed.*

**Q24.2-post — mark_superseded mismatch rate post-fix**: After removing `m.importance = 0.0` from `neo4j_store.py:391`, verify: (a) reconcile dry_run shows 0 new mismatches accumulating after the weekly repair; (b) importance_mismatches count stabilizes and does not grow between Sunday repairs.
*Prerequisite: Q21.1 fix deployed.*

**Q24.5-post — Consolidation user_id attribution propagation**: After fixing `consolidation.py:235` to pass `user_id` to merged Memory constructor, verify: (a) new merged memories have user_id set; (b) users with recently consolidated originals reappear in get_distinct_user_ids().
*Prerequisite: consolidation user_id fix deployed.*

### Low-priority analytical questions (proceed only if deployment gating is impractical)

**Q24.6-followup — Manual GC first batch**: Use admin purge endpoint to delete a sample of 30+ day old superseded memories; verify (a) Qdrant point count decreases; (b) corresponding Neo4j nodes removed; (c) no effect on active memory queries; (d) ghost user count in get_distinct_user_ids() decreases proportionally.
*No prerequisite. Can run without cron implementation.*

---

## 16. Residual Risk Inventory (Current State, post Wave 24)

| Risk | Severity | Likelihood | Trigger | Status |
|------|---------|-----------|---------|--------|
| **Double-decay: corpus decaying 2× faster than configured; every memory decays at 0.9216/slot instead of 0.96/slot; 632 memories floor-clamped (10.6%)** | **CRITICAL** | **Certain (every cron slot)** | **Every 6-hour decay run** | **OPEN — Q22.1 FAILURE; Q23.2 + Q24.1 RECONFIRMED (12th wave); fix is ~3 lines in _user_conditions() or decay cron entrypoint; Mar 15 timing anomaly does not resolve; 3-7d cohort ratio = 0.793, zero recovery in 24h** |
| Dedup hit rate completely unquantifiable — unknown volume of unique facts permanently dropped | High | Active (31,289+ creates processed without measurement) | Every store event that triggers dedup path | OPEN — 4 waves unresolved (Q15.1, Q16.1); real-time rate unmeasurable; Q20.4 confirms threshold is correct but real-time rate still unknown |
| Global LLM timeout 180s — single slow call blocks entire pipeline for up to 180s | High | Active (43 confirmed >60s events) | Any consolidation or fact_extraction call with long input | OPEN — 5 waves unresolved (Q15.3, Q16.3); Q18.3 confirms fix deployable; Q19.3 adds queue-wait qualifier |
| Store-time dedup silent drop — unique facts in incoming write permanently lost with no audit trail | High | Active (every dedup event) | Any store that scores >0.92 against existing memory | OPEN — Q14.3 FAILURE; audit entry not deployed |
| Dedup observability matrix: 10/12 cells empty; memory.py and observer.py have zero coverage | High | Active (every dedup event) | Any dedup drop at API or observer path | OPEN — Q16.4 FAILURE |
| LLM p95 > 10s — Semaphore(1) + inference variance dominates; interactive callers can wait 89s in queue | High | Active (p95=11–17s post-semaphore; queue wait unbounded) | Any mix of long-inference (consolidation) + short (signal_detection) calls | OPEN — Q14.4 FAILURE; Q19.3 WARNING adds queue-wait gap; per-caller timeouts insufficient alone |
| Retrieval coverage structural failure — K=3 fixed vs. growing corpus; 9.5% lifetime coverage | High | Certain (coverage degrades with corpus growth) | Each new memory stored | OPEN — Q13.1, Q14.7; exploration injection from Q14.2 not deployed; note: active corpus only 5,945 (Q24.3) |
| Consolidation split-brain: Neo4j failure after Qdrant mark_superseded = divergence up to 7 days | High | Unknown (consolidation runs regularly; Neo4j transient errors possible) | Any Neo4j transient error during consolidation source-supersedure loop | OPEN — Q19.6 FAILURE; Q20.1 bounds impact (0 superseded_mismatches currently; weekly reconcile repairing); **Q21.4 confirms compensating rollback is 4 lines qdrant.py** |
| **Reconcile convergence defect: compound failures require two passes; mark_superseded overwrites Step A importance fix** | **High** | **Latent (9 entries produced historically; 0 active after Q21.2 repair)** | **Q18.1 partial gather + Q19.6 split-brain co-occurring on same memory** | **OPEN — Q20.5 FAILURE; Q21.1 collapses fix to 1-line removal of importance=0.0 from neo4j_store.py; Q24.2 confirms fix not deployed** |
| **mark_superseded importance=0.0: ~796 new Neo4j importance mismatches/day; ~5,572 accumulate weekly before Sunday repair** | **Medium** | **Certain (every consolidation event creates 1 mismatch)** | **Every consolidation supersedure** | **OPEN — Q21.1 root cause confirmed; Q24.2 confirms fix not deployed; weekly reconcile auto-repairs but root cause persists; retrieval unaffected (find_related filters superseded)** |
| **Reconcile audit invisibility: zero audit_log entries for any reconcile run — execution history unverifiable** | **Medium** | **Certain (reconcile runs weekly but never writes to audit_log)** | **Every reconcile run** | **OPEN — Q20.1 secondary; Q21.6 confirms 9-LOC fix; Q24.8 confirms fix not deployed** |
| 1,315 importance mismatches (6.3% corpus): Qdrant/Neo4j drift from _track_access and compound failures | Medium | Active (Q21.2 resolved to 0 after repair; will re-accumulate) | Every _track_access exception (Q18.2) and every compound failure (Q20.5) | OPERATIONALLY BOUNDED — Q21.2 confirms repair=true converges in single pass; weekly reconcile resolves 1,313 mismatches automatically; residual 2 sub-pattern-A resolved by manual repair=true |
| except:pass in importance-inheritance block — Qdrant errors silently swallowed; promotions unconfirmed | Medium | Unknown (never logged) | Any Qdrant error during dedup drop at API path | OPEN — Q16.4b FAILURE; Q19.4 provides indirect evidence this is materializing |
| decay.py gather partial write — batch abort leaves partial Qdrant writes untracked; audit log skipped | Medium | Unknown (depends on decay_user_error frequency) | Any Qdrant error during decay batch execution | OPEN — Q18.1 WARNING; Q19.1 confirms scope is bounded to decay.py only |
| retrieval.py _track_access loop early exit — N+1 memories in retrieval batch miss access reinforcement | Medium | Unknown (depends on _track_access exception frequency) | Any storage error during retrieval stat update | OPEN — Q18.2 WARNING; Q19.2 confirms scope is bounded to _track_access only |
| Importance corpus contamination: Q16.4b + Q18.2 prevent importance promotion; 1,315 importance mismatches accumulating | Medium | Active (6.3% of corpus, measurable drift; resolves weekly) | Any dedup event (Q16.4b) or retrieval event (Q18.2) where write fails silently | OPEN — Q20.1 WARNING; re-accumulates between weekly reconcile runs |
| **Superseded memory storage bloat: ~15,099 superseded Qdrant points; ~796 new/day; no scheduled GC; ~11,000 eligible for DETACH DELETE** | **Medium** | **Certain (grows with every consolidation)** | **Every consolidation event creates superseded points that are never scheduled for deletion** | **OPEN — Q21.3 WARNING; Q24.6 WARNING (GC window now open); safe GC criteria confirmed; admin purge endpoint available for manual cleanup; no scheduled GC cron** |
| **Ghost users in decay: 7/10 decay_run entries/slot processed=0; overdecay ~4%/run for primary user** | **Medium** | **Certain (70% of user_id list are phantoms; grows with superseded accumulation)** | **Every cron slot; every decay run for primary user** | **OPEN — Q21.5 WARNING; Q22.2 confirms ghost identity; Q24.7 confirms fix not deployed; fix: IS NULL filter (1 line) + user_id in audit INSERT (4 LOC Q22.7)** |
| **Consolidation user_id attribution loss: merged memories get user_id=None permanently; user vanishes from get_distinct_user_ids() when all originals superseded** | **Medium** | **Certain (runs hourly; every system consolidation event)** | **Every consolidation of named-user memories by system run** | **OPEN — Q22.9 WARNING; Q24.5 FAILURE (fix not deployed); ~796 merged memories/day with user_id=None** |
| Dedup threshold (0.92) empirically confirmed correct (Q20.4) — 0 pairs at 0.90 | Low | Resolved | — | **RESOLVED by Q20.4** — threshold is empirically correct; 0.90-0.95 band empty |
| ~~Active-memory Neo4j sync gap: active memories with neo4j=0.0~~ | ~~High~~ | ~~Active~~ | ~~Memory creation path~~ | **CLOSED by Q24.3** — hypothesis ruled out; Q23.4's 50 "active" mismatches were temporal artifacts; zero active memories have neo4j=0.0; only creation-path bug is the mark_superseded path (Q21.1) |
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

## 17. Waves 1–12 Baseline (summary, not modified)

Waves 1–12 produced 35 HEALTHY findings and 5 committed fixes covering: p99 search latency well under threshold at 40 concurrent users (Q1.1–Q1.4); domain isolation correct under concurrent writes (Q2.1); graph traversal guarded against cycles (Q3.4); all 4 background workers with structured exception logging (Q5.3); asyncio.Lock added to all async-mutated module-level state (Q7.1, e73858f); Pydantic v2 migration complete (Q7.2, 033ede9); datetime.utcnow() sweep complete across 23 files (Q6.7, 9cec9f4); all 4 worker test suites written and passing (Q5.7, Q7.6); embed_batch per-item fallback confirmed observable (Q6.1, 26da1aa); stdlib/structlog mismatch eliminated across all 77 src/ files (Q7.4). These findings remain confirmed holding.

**Key pre-condition**: The Waves 1–12 work addressed code quality and unit-test coverage. Wave 13 established that this well-built code is failing at its primary job — surfacing the right memories at the right time. Waves 14–24 have added numerous FAILURE/WARNING findings to the runtime behavior and documented a remediation stall pattern that has now run for thirteen consecutive waves.

**Wave 24 post-synthesis recommendation**: Thirteen waves of characterization (12–24) with zero deployed remediation. Wave 24 confirms: (1) Q22.1 double-decay is still active — 12th consecutive wave; the 3-7d cohort ratio is unchanged from 24 hours earlier at 0.793, confirming no self-correction; (2) all five Tier 0/1b FAILUREs remain undeployed; (3) the Q23.4 "High severity" active-memory Neo4j sync gap risk is CLOSED — there is no creation-path bug, only the known one-line mark_superseded fix; (4) the GC window is now open with ~11,000 eligible memories. **Immediate priority**: Deploy Tier 0 fix #0 (Q22.1 double-decay, ~3 lines). Then Tier 1b fixes #6 and #7 (~10 LOC total). Then Tier 2 fixes #16, #17, #18 (~10 LOC). No further characterization waves are justified until at least Tier 0 + Tier 1 remediation is deployed.

# Synthesis: Recall Autoresearch — Waves 1–36

**Generated**: 2026-03-15 (updated with Wave 35–36 findings and 2026-03-16 post-hoc re-runs)
**Questions answered**: 228 (Q1.1–Q1.5, Q2.1–Q2.5, Q3.1–Q3.5, Q4.1–Q4.6, Q5.1–Q5.4, Q5.6–Q5.7, Q6.1–Q6.7, Q7.1–Q7.6, Q13.1–Q13.8, Q13.1a–Q13.8b, Q14.1–Q14.9, Q14.4a, Q14.4b, Q15.1–Q15.5, Q16.1–Q16.5, Q16.3b, Q16.4b, Q18.1–Q18.5, Q19.1–Q19.6, Q20.1–Q20.6, Q21.1–Q21.6, Q22.1–Q22.9, Q23.1–Q23.7, Q24.1–Q24.8, Q25.1–Q25.7, Q26.1–Q26.7, Q27.1–Q27.7, Q28.1–Q28.7, Q29.1–Q29.7, Q30.1–Q30.7, Q31.1–Q31.7, Q31.2a, Q32.1–Q32.7, Q33.1–Q33.7, Q33.2a–Q33.2c, Q34.1–Q34.7, Q35.1–Q35.6, Q36.1–Q36.6)
**Wave 17 questions (Q16.3a, Q16.4a)**: PENDING — deferred until Tier 1 fixes deployed
**Source codebase**: C:/Users/trg16/Dev/Recall/
**Stack**: FastAPI + Qdrant + Neo4j + Redis + PostgreSQL + Ollama (qwen3:14b + qwen3-embedding:0.6b)

---

## 1. Executive Summary

Twenty-nine waves of autoresearch have been run against the Recall self-hosted memory system. Waves 1–12 established a well-tested, type-safe codebase. Wave 13 revealed structural failures at the retrieval architecture level. Waves 14–20 added five FAILURE-severity findings across five clusters: LLM timeout misconfiguration, dedup observability, silent write failures, consolidation split-brain, and reconcile convergence failure. Wave 20 was an operational measurement wave that confirmed compound failures are occurring in production.

Waves 24–29 are consecutive **fix-verification waves** — the second through seventh attempts to confirm deployment of the Tier 0/1/1b fixes. Wave 29 produces 4 FAILURE, 2 INCONCLUSIVE (timing-blocked), 1 WARNING.

**Wave 30 signal: 19 consecutive characterization waves (Waves 12–30), ZERO fixes deployed.** Wave 29 reveals a new FAILURE: floor-clamped count has accelerated to 941 (Q29.6, FAILURE, threshold 800 exceeded) driven by the Q24.5 consolidation user_id bug — consolidation-source floor-clamped memories jumped from 7 to 375 (+368, +5,257%) since Q27.4 baseline. Three existing FAILURE threads continue: (1) **Double-decay 18th consecutive FAILURE** (Q29.2). (2) **Consolidation user_id fix 5th consecutive FAILURE** (Q29.4). (3) **Reconcile audit fix 5th consecutive FAILURE** (Q29.5, with new anomaly: 179 importance mismatches detected by reconcile but repairs_applied=0). Q29.7 (superseded pool) is WARNING: pool growing to 15,185 (+55 from Q27.2 baseline), 179 Neo4j importance mismatches detected.

**Wave 29 key findings**:
- Q29.1: INCONCLUSIVE (4th consecutive) — auto_archive still 0 at 2026-03-15T10:35 UTC; target cron 2026-03-16T04:00 UTC ~17.4h away
- Q29.2: FAILURE (18th) — `_user_conditions(None)` returns [] unchanged; two full-corpus runs per slot
- Q29.3: INCONCLUSIVE — Q29.1 prerequisite not met; Week 12 dates (Mar 17-21) not yet reached
- Q29.4: FAILURE (5th consecutive) — consolidation.py:235 Memory() still missing user_id=; consolidation-source floor-clamped 7→375 (+368)
- Q29.5: FAILURE (5th consecutive) — 0 log_audit() in reconcile.py/ops.py; new: 179 importance_mismatches, repairs_applied=0
- Q29.6: FAILURE — floor-clamped 941 vs 673 Q27.4 baseline (+268, +39.8%); exceeds 800 FAILURE threshold
- Q29.7: WARNING — superseded pool 15,185 vs 15,130 baseline (+55); 179 importance mismatches Qdrant vs Neo4j

Wave 28 produced 3 FAILURE, 4 INCONCLUSIVE. Wave 29 produces 4 FAILURE, 2 INCONCLUSIVE, 1 WARNING.

**Wave 30 key findings**:
- Q30.1: INCONCLUSIVE (5th consecutive) — auto_archive still 0 at 2026-03-15T10:50 UTC; 17.1h before 2026-03-16T04:00 UTC target; Wave 31 mandatory FAILURE escalation
- Q30.2: FAILURE (19th) — `_user_conditions(None)` returns [] unchanged; processed=6,002 per slot
- Q30.3: WARNING — importance_mismatches stable at 179 (Q29.7 baseline; δ=0); same IDs confirmed; historical artifact
- Q30.4: FAILURE (6th consecutive) — consolidation.py:235 Memory() still missing user_id=; consolidation-source floor-clamped stable at 375
- Q30.5: FAILURE (6th consecutive) — 0 log_audit() in reconcile.py/ops.py; mismatch trend limited to manual per-wave sampling
- Q30.6: WARNING — floor-clamped stable at 941/6,044 (15.6%); growth arrested in 79-minute same-day window; within 800-941 WARNING range
- Q30.7: INCONCLUSIVE — GC eligibility 6d 8h away (2026-03-21T19:12 UTC); superseded 15,184 (−1 from Q29.7; flat)

Wave 30 produces 3 FAILURE, 2 WARNING, 2 INCONCLUSIVE.

**Wave 31 first-run key findings** (superseded by re-run below):
- Q31.1: FAILURE (7th+ consecutive) — hygiene_run=0; archive=0; 2026-03-15T04:00 UTC window passed with no entries; cron broken since 2026-03-09
- Q31.2: FAILURE (20th consecutive) — double-decay fix not deployed; system pass processed=5,994/6,048 (99.1%)
- Q31.3: FAILURE — floor-clamped 1,049/6,048 (17.3%); +108 from Q30.6 baseline 941 in ~3 hours
- Q31.4: FAILURE (7th consecutive) — reconcile_run=0 after manual trigger; **SUPERSEDED: FALSE NEGATIVE** — wrong action name queried
- Q31.5: FAILURE — importance_mismatches grew 179→264 (+85, +47%); mark_superseded fix undeployed; ~28/hour new mismatch rate
- Q31.6: INCONCLUSIVE — GC eligibility 6d 5h away (2026-03-21T19:12 UTC); superseded pool ~15,275 (+91 from Q30.7)
- Q31.7: FAILURE — LLM timeout tiers not deployed; 15/18 generate() callsites missing timeout= — **SUPERSEDED: FULLY DEPLOYED**

**Wave 31 re-run key findings** (Q31.1–Q31.7 second pass + Q31.2a):
- Q31.1: FAILURE (7th+ consecutive) — hygiene_run=0; archive=0; cron not fired since 2026-03-09; ARQ worker alive (decay running), confirming hygiene-task-specific failure
- Q31.2: FAILURE (21st consecutive) — IS NULL fix deployed (`user_id=0` sentinel) but second full-corpus run (~5,994/slot) persists; behavioral doubling confirmed
- Q31.2a: FAILURE — Second run source confirmed NOT admin API (actor="decay" on both runs), NOT duplicate cron (only one cron entry); ARQ enqueuing `run_decay` twice per cycle from unknown enqueue path; admin endpoint structural risk (`worker.run()` without user_id) identified
- Q31.3: FAILURE — floor-clamped 1,038–1,049/6,021 (17.3%); stable vs prior Q31.3 (−11 noise); +97 above Q30.6 FAILURE threshold of 941; partial IS NULL fix may have halted new accumulation; no drain active
- Q31.4: WARNING (CORRECTION — 7 prior FAILUREs were FALSE NEGATIVES) — audit IS deployed and working; action name is `"reconcile"` not `"reconcile_run"`; entries confirmed in audit log; 262 mismatches, repairs_applied=0 (scan-only scheduler)
- Q31.5: WARNING — repair=true clears all mismatches (261/261 cleared in one run); scheduled runs are scan-only (repairs_applied=0 always); mark_superseded root cause unpatched; mismatches re-accumulate continuously
- Q31.6: INCONCLUSIVE — GC gate 6d 4h away; superseded pool 15,335 (+151 from Q30.7 in ~3.5 hours; ~1,035/day burst rate)
- Q31.7: HEALTHY — 17/17 generate() callsites have correct timeout= tiers; full reversal from prior run's 15/18 missing; 180s semaphore-hold risk eliminated

Wave 31 re-run produces 3 FAILURE, 2 WARNING, 1 HEALTHY, 1 INCONCLUSIVE (plus Q31.2a FAILURE).

**Wave 32–33 signal: ROOT CAUSE OF DOUBLE-DECAY IDENTIFIED (Q33.2b) AFTER 24 CONSECUTIVE FAILURE WAVES.** The investigation chain Q31.2→Q31.2a→Q33.2→Q33.2a→Q33.2b traced the double-decay to its exact code-level origin: `get_distinct_user_ids()` returns `[0]` (integer zero), causing the per-user loop to run `worker.run(user_id=0)` which maps to `IsNullCondition` and decays 5,043 null-user_id memories — then the explicit system pass runs `worker.run(user_id=0)` again, decaying the same 5,043 memories a second time. Meanwhile, 975 memories with integer `user_id=0` are NEVER decayed (missed by both passes). Q33.2a definitively refuted the two-replica hypothesis (one container confirmed via SSH + Redis). Q33.2c confirms the two-line fix has NOT been deployed (24th consecutive FAILURE). Q33.7 HEALTHY: the Feb 14 cohort (first to cross 30d boundary) has zero floor-clamped active members — double-decay damage is concentrated in mid-life 7–21d cohorts, not the archival boundary. Q32.1 extends the hygiene cron miss streak to 9 consecutive windows. Q32.4 HEALTHY confirms Sunday reconcile cron is registered and functional. Q32.6 HEALTHY confirms LLM timeout compliance (17/17, closing Q15.3/Q16.3 permanently). Three questions INCONCLUSIVE due to same-day timing (Q32.3, Q32.5, Q32.7).

**Wave 35 key findings** (2026-03-15, crisis-response wave):
- Q35.1: FAILURE — rehabilitate-importance endpoint uses `>= 0.05` instead of `> 0.05`; misses every floor-clamped memory at exactly 0.050; endpoint has never been run
- Q35.2: WARNING — hygiene cron registered and ran once (2026-03-15T14:47); 0 candidates (expected — system 29 days old, no memories cross 30d cutoff yet); filter logic is correct
- Q35.3: FAILURE — 846 null-user_id floor-clamped (up from Q34.7's 644; +202 growth); development domain 229 casualties (FAILURE threshold >100); 413 total in critical domains (48.8% of all floor-clamped)
- Q35.4: WARNING — 2 of 3 code fixes deployed (consolidation user_id + decay.py explicit system pass); Fix-1 (`qdrant.py uid>0 guard`) NOT deployed; double-decay continues
- Q35.5: WARNING — rehabilitate broken (off-by-one); amnesty endpoint IS viable (`POST /admin/importance/amnesty?dry_run=false` would boost 4,173 memories including floor-clamped); purge/decay endpoints are wrong tools
- Q35.6: HEALTHY — floor-clamped stable at 1,049 over 2h 14m window (consolidation not running in measurement period)

**Wave 36 key findings** (2026-03-15, intervention + verification wave):
- Q36.1: HEALTHY — amnesty live run rescued 4,173/5,211 memories (80.1% of scanned; 99.9% of eligible); post-run residual eligible: 5; floor-clamped pool reduced from ~23% to 3.9% of active memories; amnesty endpoint writes NO audit rows (observability gap)
- Q36.2: WARNING — hygiene 0-candidate confirmed correct; system only 29 days old; no memory older than 30d; filter logic verified correct; first real archival expected 2026-03-17T04:00 UTC
- Q36.3: HEALTHY — one-char fix (`>= 0.05` → `> 0.05`) enables rehabilitate to reach ~838/846 (99.1%) of null-pool floor-clamped; "no default branch" risk does NOT strand bulk because 99% are durable (branch 2 covers); ~8 ephemeral low-access memories correctly unreachable
- Q36.4: HEALTHY — post-amnesty residual eligible: 5 (HEALTHY threshold <100); importance distribution shifted: 0.0-0.2 bucket contracted from 23.3% to 3.9%; amnesty cleanup confirmed at scale
- Q36.5: WARNING — Fix-1 still NOT deployed (qdrant.py `uid is not None and uid > 0`); 74 FamilyHub memories discovered (uid 53–71); other callers (patterns, dream_consolidation, consolidation) lack explicit system-user fallback — pre-existing gap; deployment requires container restart
- Q36.6: HEALTHY — N3 (stranded, amnesty-ineligible) ≈ 8 ephemeral ac<3 memories; graph isolation does NOT create stranded segment (graph_strength modulates boost amount, not eligibility); N1 rescued ≈ 838/846 (99.1%); N2 does not exist

**2026-03-16 post-hoc re-run key findings** (Q33.1, Q33.3–Q33.6):
- Q33.1: WARNING — hygiene cron fired at 2026-03-16T04:00 UTC (2nd ever run); 0 candidates again (correct — 30d cutoff missed Feb 14 cohort by hours); 9-wave FAILURE streak resolved; first real archival expected 2026-03-17T04:00 UTC
- Q33.3: INCONCLUSIVE — Q31.3 baseline invalidated by amnesty operation; floor-clamped count reset then re-accumulating; 3,198 amnesty-eligible (up from 5 in Q36.4, +3,193 in 23.5h); amnesty-boosted memories will decay back to floor by ~2026-03-21 without Fix-1
- Q33.4: FAILURE — Sunday reconcile cron (2026-03-16T05:30 UTC) MISSED; worker likely restarted overnight; gap: 24h 12m with no reconcile entry; 1,027 mismatches accumulated without mid-period repair
- Q33.5: FAILURE — importance mismatch rate ~41/hour (1,027 mismatches in 25.1h from clean baseline); Q24.2's ~1.3/hour estimate conclusively rejected; 15.8% of active corpus now has divergent retrieval scores; weekly-window accumulation ~6,888/week = coverage of entire active pool
- Q33.6: WARNING — superseded pool growing at ~613/day (23.5h clean measurement); matches Q21.3 analytical estimate; projected pool at GC eligibility (~19,610) is manageable

**Overall health signal: PARTIAL CRISIS MITIGATION — AMNESTY RAN AND RESCUED 4,173 FLOOR-CLAMPED MEMORIES (Q36.1 HEALTHY), BUT FIX-1 (double-decay root cause) REMAINS UNDEPLOYED. WITHOUT FIX-1, CORPUS WILL RETURN TO PRE-AMNESTY DEGRADED STATE BY ~2026-03-21. HYGIENE CRON NOW STRUCTURALLY SOUND (Q33.1 — fires on schedule); FIRST REAL ARCHIVAL 2026-03-17T04:00 UTC. CONSOLIDATION FIX DEPLOYED (Q35.4). RECONCILE MISSED SUNDAY WINDOW (Q33.4 FAILURE); MISMATCH RATE 41/HOUR CONFIRMED (Q33.5 FAILURE). SUPERSEDED GC ELIGIBILITY APPROACHING (2026-03-21T19:12 UTC; ~19,610 PROJECTED POOL). CRITICAL REMAINING ACTIONS: (1) DEPLOY FIX-1 (`qdrant.py uid>0 guard`) + CONTAINER RESTART; (2) CHANGE RECONCILE SCHEDULER TO repair=true; (3) FIX REHABILITATE ENDPOINT OFF-BY-ONE (`>= 0.05` → `> 0.05`); (4) SECOND AMNESTY RUN BEFORE 2026-03-21 IF FIX-1 NOT DEPLOYED.**

---

## 2. Cumulative Findings by Verdict Tier (Waves 1–34)

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
| Q15.3 | ~~signal_detection_timeout=180s applies to ALL OllamaLLM callers via httpx.AsyncClient at init time; no per-call override in generate() signature; 43 confirmed >60s events; worst-case semaphore hold = 180s~~ **CLOSED by Q31.7 re-run: all 17 callsites now have explicit timeout= matching tier spec; 180s hold risk eliminated** | High → CLOSED | 15 / 31 |
| Q15.4 | Very-short-prompt pre-filter at <50 chars not justified: best sub-bucket is 61.2% (threshold 70%); 30–44 char range has lower empty rate (34–42%) than overall average | Medium | 15 |
| Q16.3 | ~~generate() has no timeout parameter; httpx.AsyncClient constructed once with 180s; per-call override path does not exist; 43 >60s events confirmed; fix not deployed~~ **CLOSED by Q31.7 re-run: timeout parameter exists in generate() signature; all 17 callsites supply explicit values; httpx per-request override confirmed** | High → CLOSED | 16 / 31 |
| Q16.4 | 9-cell (4-site x 3-layer) dedup observability matrix: 2/12 cells covered; memory.py and observer.py have 0/3 layers; compound gap from Q14.3+Q15.1+Q15.2 not remediated | High | 16 |
| Q16.4b | except:pass in memory.py importance-inheritance block silently swallows all Qdrant errors; importance promotions never confirmed in production | Medium | 16 |
| Q13.8 | Session Markov Chain: 0 predictions in 4,008 visits; tag vocabulary mismatch; feature completely inert | Medium | 13 |
| Q13.8a | 0% of source files have >=5 transitions; max observed = 4; insufficient training data even after tag fix | Medium | 13 |
| Q13.5a | Sim-persona retirement inapplicable — all 20,602 memories are real user data; only 18 low-importance candidates | High | 13 |
| Q14.5 | input_chars cannot proxy file-type split for fact_extraction pre-filter; non-monotonic empty rate (51%->24%->36%->61%); distributions too overlapping | Medium | 14 |
| Q19.6 | Split-brain confirmed in consolidation: qdrant.mark_superseded() at line 282 committed before neo4j.mark_superseded() at line 283 bare await; Neo4j failure = divergence; all 4 Neo4j write methods unguarded; **Q20.1 bounds impact**: weekly reconcile repairs superseded_by mismatches (0 currently); divergence window up to 7 days, not permanent | High | 19 |
| **Q20.5** | **Compound failure reachable: Q18.1 partial gather + Q19.6 split-brain co-occur on single memory; reconcile Step A fix overwritten by Step B mark_superseded (importance=0.0); two passes required for convergence; 9 sub-pattern-A entries in Q20.1 are production evidence; Q21.1 provides one-line fix (remove importance=0.0 from mark_superseded); Q21.2 confirms compound state is currently latent (0 active)** | **High** | **20** |
| **Q22.1** | **Double-decay FAILURE: `_user_conditions(None)` returns `[]` → system run processes ALL active memories (no user_id filter); every 15-min cron slot applies decay twice (system run + per-user run); effective decay 0.9216× per slot instead of 0.96×; corpus decaying 2× faster than configured; fix: add MatchAny or IsNullCondition to system-run filter in `_user_conditions`** | **High** | **22** |
| **Q23.2 / Q24.1 / Q25.1 / Q26.2 / Q27.3 / Q28.2 / Q29.2 / Q31.2 / Q31.2a / Q32.2 / Q33.2 / Q33.2a / Q33.2b / Q33.2c** | **Double-decay FAILURE (24th consecutive wave, Q33.2c). ROOT CAUSE FULLY IDENTIFIED (Q33.2b): `get_distinct_user_ids()` returns `[0]` → per-user loop runs `worker.run(user_id=0)` → `_user_conditions(0)` returns `IsNullCondition` → decays 5,043 null-user_id memories → explicit system pass runs `worker.run(user_id=0)` AGAIN → same 5,043 decayed twice. Three-way population split confirmed via direct Qdrant API: 5,043 active null (double-decayed), 975 active integer-0 (never decayed), 0 active user_id=1+. Q33.2a refuted two-replica hypothesis (1 container, 1 ARQ heartbeat). Fix is two lines: (1) `qdrant.py:1207` change `if uid is not None:` to `if uid is not None and uid > 0:`; (2) `decay.py:296` remove redundant `worker.run(user_id=0)` system pass. Fix NOT deployed (Q33.2c FAILURE).** | **High** | **23/24/25/26/27/28/29/30/31/32/33** |
| **Q24.2 / Q25.2 / Q26.4** | **mark_superseded importance=0.0 fix NOT deployed: `neo4j_store.py:391` still sets `m.importance = 0.0`; Wave 26: 124 mismatches on Sunday repair day itself (higher than 1-day post-repair baseline of 92 — confirms same-day re-accumulation); 3rd data point for weekly cycle: Sunday repair → ~32 new mismatches in hours → ~92/day accumulation → ~5,572 peak pre-Sunday; retrieval unaffected (find_related filters superseded) but monitoring unreliable** | **Medium** | **24/25/26** |
| **Q24.5 / Q25.3 / Q27.5 / Q28.5 / Q29.4 / Q30.4** | **Consolidation user_id attribution fix NOT deployed (7th consecutive): `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; consolidation-source floor-clamped 375→449 (+74) by Wave 31; total floor-clamped 1,049; co-deployment of Q21.5 + Q24.5 required for permanent fix** | **Medium** | **24/25/27/28/29/30/31** |
| **Q24.7 / Q25.7** | **Ghost-user compound FAILURE — neither Q21.5 IS NULL filter nor Q24.5 consolidation user_id fix deployed; `qdrant.py:1143-1162` confirmed unchanged; 7 ghost user proc=0 entries per slot; 28+ wasted scroll operations/day; ghost re-accumulation path open: new merged memories with user_id=None (~796/day) seed next generation of ghost users even if IS NULL filter were deployed today** | **Medium** | **24/25** |
| **Q24.8 / Q26.7 / Q27.6 / Q28.6 / Q29.5 / Q30.5** | **~~Reconcile audit trail fix NOT deployed (6 prior waves)~~ — CORRECTED by Q31.4 re-run: all 6 FAILURE verdicts were FALSE NEGATIVES caused by querying `?action=reconcile_run` (string not present in codebase). Actual action name is `"reconcile"`. `log_audit(action="reconcile")` is deployed in both `ops.py:373-377` and `workers/reconcile.py:112-116`. Entries confirmed under correct action name. Mismatch details fully visible in audit.** | **Medium → CLOSED** | **24/26/27/28/29/30 (corrected Q31.4)** |
| **Q27.3** | **Double-decay inflation queue FAILURE: 1,332 active memories (7–29d, importance<0.3, access_count=0) > 500 FAILURE threshold; 89.2% of 7–10d cohort below 0.3 (vs 59.2% expected under single-decay); double-decay halves time-to-threshold (2.1d→1.1d) and time-to-floor (9.5d→4.7d); correction: double-decay does NOT inflate 30d archival COUNT (floor reached in <10d under either regime); bug's damage is to information quality in 0–10d window only** | **High** | **27** |
| **Q29.6 / Q31.3 / Q33.7** | **Floor-clamped accumulation FAILURE: Q29.6 941/6,044 (15.6%); Q31.3 1,049/6,048 (17.3%); total floor-clamped pool 1,049; no drain active (hygiene cron broken, Q32.1 9th miss). Q33.7 HEALTHY provides key nuance: the Feb 14 cohort (first to cross 30d boundary) has ZERO floor-clamped active members — all 14 active memories maintain importance 0.30–0.40 due to sustained access (min ac=1, max ac=130). Floor-clamped backlog is concentrated in mid-life 7–21d cohorts, not the 30d+ archival boundary. Double-decay damage manifests in the mid-cohort, confirming Q27.7 analytical proof that both decay regimes archive the same count at 30d.** | **High** | **29/31/33** |
| **Q34.1** | **Total importance suppression damage FAILURE+INCONCLUSIVE: 795 null-pool memories at decay floor (≤0.05) — exceeds FAILURE threshold of 500. Null pool mean importance 0.2584 (n=5,048). Importance-units stolen INCONCLUSIVE: int-0 pool is not a valid control group (mean 0.1852 < null pool mean 0.2584 — inversion; different origin populations). Without stored `initial_importance` per memory, magnitude of suppression is uncomputable. 795 are retrieval dead zone: floor-clamped memories never surface in importance-weighted queries; double-decay fix stops further accumulation but does not restore clamped memories.** | **High** | **34** |
| **Q34.2** | **user_id attribution architecture broken across 4 dimensions: (1) auth.py writes `user_id=0` (integer) but `_user_conditions(0)` queries IS NULL — decay/scan misses all 2,996 integer-0 memories; (2) 5 worker paths (observer.py:151, observer.py:286, signals.py:259, patterns.py:241, ingest.py:221) omit user_id entirely; (3) consolidation `_get_eligible_memories()` drops user_id from deserialization — all merged memories default to user_id=None regardless of source; (4) integer-0 pool growing at 58/day (all from session-summary hook). The `_user_conditions` semantic contract (0 = "IS NULL/unowned") is violated by the storage reality (admin-key writes integer 0). Three-population system is accidental, not designed.** | **High** | **34** |
| **Q34.6** | **Consolidation floor-clamped growth self-reinforcing loop FAILURE: 199–648 new floor-clamped memories per day from consolidation output alone, far exceeding 50/day FAILURE threshold. All consolidation outputs reach floor because (a) Q24.5 bug produces null-user_id merged memories and (b) null-user_id memories are double-decayed at 2× rate. Recent session (autoresearch wave activity) drives throughput to 648/day (13× threshold). Loop is self-reinforcing: more session activity → more consolidation candidates → more null-user_id floor-clamped outputs. Floor is a one-way trap — no promotion mechanism exists. Fix required: Q24.5 (`consolidation.py:235` must pass `user_id=source_memories[0].user_id`).** | **High** | **34** |
| **Q34.7** | **~~644 premature casualties — natural recovery impossible; bulk re-score mandatory; 16.6-day hygiene window is hard deadline.~~ PARTIALLY RESOLVED by Q36.1 amnesty: ~838 of the original 844 null-pool casualties rescued by amnesty live run on 2026-03-15T15:42 UTC. Poverty trap remains active for ~8 ephemeral memories (Q36.6 N3). However, without Fix-1 (qdrant.py uid>0 guard), amnesty-rescued memories will decay back to floor by ~2026-03-21 under double-decay. The rehabilitate endpoint still has the `>= 0.05` off-by-one defect (Q35.1 FAILURE); fix: change to `> 0.05`.** | **High → Partially Mitigated** | **34/35/36** |
| **Q35.1** | **Rehabilitate-importance endpoint off-by-one FAILURE: `admin.py:1123` uses `if importance >= 0.05: continue` — skips memories at exactly 0.050 (the floor). All floor-clamped premature casualties are at exactly 0.050. Endpoint has NEVER been invoked (audit log: 0 entries). When the filter is corrected (`> 0.05`), it would reach ~838/846 (99.1%) of null-pool via branch 2 (durable, max 0.2). Incremental rescue beyond amnesty: ~0–7 memories (pinned/permanent edge cases). Fix: one char change in `src/api/routes/admin.py:1123`.** | **Medium** | **35** |
| **Q35.3** | **Floor-clamped domain clustering FAILURE: 846 null-user_id floor-clamped at time of measurement (+202 from Q34.7's 644); development domain 229 casualties (FAILURE threshold >100; 27.1% of total); 413 total in critical domains (48.8%). Distribution follows memory production rates — all operational domains proportionally degraded. RESOLVED for pre-amnesty cohort by Q36.1 amnesty, but will re-accumulate without Fix-1.** | **High → Partially Mitigated** | **35** |
| **Q33.4** | **Sunday reconcile cron MISSED: no reconcile entry at or near 2026-03-16T05:30 UTC; gap 24h 12m; worker likely restarted or temporarily down overnight. Q32.4 HEALTHY (cron registered + manual trigger works) remains accurate for infrastructure, but operational reliability now unconfirmed. Missed run allowed 1,027 mismatches to accumulate without mid-period repair.** | **Medium** | **33 (post-hoc 2026-03-16)** |
| **Q33.5** | **Importance mismatch rate FAILURE: ~41/hour confirmed (1,027 mismatches in 25.1h from Q31.5 clean baseline); Q24.2's ~1.3/hour estimate conclusively rejected (31× underestimate). 15.8% of active corpus (1,027/6,492) has divergent retrieval scores. Weekly accumulation at this rate ~6,888 = exceeds entire active pool. Dominant pattern: Qdrant < Neo4j (decay runs without Neo4j sync for superseded/stale memories). Immediate fix: change reconcile scheduler from scan-only to `repair=true` on every run.** | **High** | **33 (post-hoc 2026-03-16)** |

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
| **Q24.6 / Q26.6 / Q27.2** | **Superseded GC backlog: hygiene cron running daily at 4am but 0 memories archived; hygiene is active-only soft-delete (IS NULL on superseded_by); no DETACH DELETE cron for consolidation-superseded memories; **Q24.6's "~11,000 GC-eligible" estimate was INCORRECT (3rd estimate correction)**: Q27.2 corrects to: oldest consolidation-source active memory = 2026-02-19T19:12; first GC-eligible date = **2026-03-21T19:12 UTC** (6 days from Wave 27 measurement); 15,130 total superseded; Q21.3 GC cron still unimplemented** | **Medium** | **24/26/27** |
| **Q27.4 → Q29.6** | **Information recovery debt (escalated to FAILURE in Q29.6): Q27.4 baseline 673 floor-clamped; Q29.6 confirmed 941 — exceeds 800 FAILURE threshold; see Q29.6 FAILURE row above** | **Medium→High** | **27→29** |
| **Q27.7** | **Hygiene archival pipeline WARNING: 3,289 active memories qualify for archival (importance<0.3, access=0; 54.8% of 6,005 active corpus); daily new rate 186.7/day; peak Week 14 (Mar 29–Apr 4): 1,550 archives = 221/day → corpus temporarily SHRINKS ~34/day; recovers after April 5; key correction: double-decay does NOT inflate archival count at 30d (floor reached in <10d under either regime; damage is to 0–10d information quality only); first actual archival: 2026-03-16T04:00 UTC (2 memories)** | **Medium** | **27** |
| **Q29.7** | **Superseded pool WARNING: 15,185 vs 15,130 Q27.2 baseline (+55); pool growing (not FAILURE); growth rate below 796/day estimate (same-day measurement window, hours not days elapsed); new anomaly: 179 importance mismatches detected (Qdrant non-zero vs Neo4j=0.0, repairs_applied=0); GC eligibility still 2026-03-21T19:12 UTC (~6 days)** | **Medium** | **29** |
| **Q23.6** | **Mark_superseded audit coverage WARNING: per-supersedure log_audit() calls exist in consolidation.py:299-305; 1000+ entries in audit trail; chain reconstructable; TWO gaps: user_id null throughout (Q24.5 propagation); 2.6% duplicate memory_ids from Q22.1 double-processing** | **Medium** | **23/31** |
| **Q30.3** | **Importance mismatch trend WARNING: 179 stable (Q29.7 baseline 179; δ=0); same IDs confirmed; qdrant_total +26 (21,202→21,228) but no new mismatches; historical artifact; no repair mechanism; Neo4j importance queries return stale 0.0 for these 179 memories** | **Medium** | **30** |
| **Q30.6** | **Floor-clamped count trajectory WARNING: 941 stable vs Q29.6 FAILURE baseline (δ=0); growth arrested in 79-minute same-day window; active corpus 6,017→6,044 (+27 new all above floor); within 800-941 WARNING range; underlying bugs (Q30.2, Q30.4) still present; long-term accumulation resumes on next multi-day interval** | **High** | **30** |
| **Q33.2 / Q33.2a / Q33.2b** | **Double-decay root cause investigation chain (WARNING tier — root cause identified but fix not deployed): Q33.2 rules out stale Redis job, proposes two-replica hypothesis; Q33.2a refutes two-replica (1 container confirmed), identifies `run_decay_all_users` logic bug; Q33.2b confirms three-way population split via direct Qdrant API: 5,043 null double-decayed, 975 integer-0 never decayed. Exact fix specified (two lines). Escalated to FAILURE in Q33.2c.** | **HIGH** | **33** |
| **Q31.4 (re-run)** | **Reconcile audit trail WORKING (WARNING — naming discrepancy): audit entries confirmed under action="reconcile" in both ops.py and workers/reconcile.py; 262 mismatches detected; repairs_applied=0 (scan-only); WARNING because scheduled cron never repairs detected mismatches; action name "reconcile_run" used in all prior question hypotheses was wrong; any dashboard filters referencing "reconcile_run" must be updated** | **Low** | **31** |
| **Q31.5 (re-run)** | **Importance mismatches: repair mechanism functional (261/261 cleared by repair=true); scheduled runs scan-only (never auto-repair); mark_superseded root cause unpatched (neo4j_store.py does not call update_importance when superseding); re-accumulation guaranteed; immediate fix: update scheduler to use repair=true; root fix: patch mark_superseded** | **Medium** | **31** |
| **Q34.4** | **Admin decay endpoint unscoped — single call = full-corpus floor-clamp: `POST /admin/decay` has no `user_id` parameter; calls `worker.run(user_id=None)` which scrolls and decays ALL memories across all users with no filter. Rate limit 10/min constrains throughput but not sustained attack (600 calls/hour). Audit actor is hardcoded `"decay"` regardless of caller — admin-triggered runs are forensically indistinguishable from cron runs. `simulate_hours` parameter allows time-amplification (e.g., 8760 hours flattens entire corpus to floor in one call). No confirmed incident in observable window. Recommended fix: add `user_id` scoping to `DecayRequest`, require admin role, stamp actor in audit log, cap `simulate_hours` (max ~168).** | **Medium** | **34** |
| **Q35.2** | **Hygiene 0-candidate WARNING: cron registered (Q35.2 confirms `WorkerSettings.cron_jobs`) and ran once on 2026-03-15T14:47 UTC; candidates_scanned=0 because system only ~29 days old — no memory crosses 30-day cutoff. Filter logic confirmed correct. Updated Q33.1 (post-hoc 2026-03-16): cron fired again at 04:00 UTC on schedule; 0 candidates again (correct — Feb 14 cohort just crossing 30d boundary). First real archival expected 2026-03-17T04:00 UTC. The 9-wave FAILURE streak was a monitoring artifact; hygiene task was registered all along (Q35.2). WARNING persists only until 2026-03-17 archival is confirmed.** | **Low** | **35/33** |
| **Q35.4** | **Deployment state WARNING: Fix-1 (`qdrant.py:1207` `uid > 0` guard) NOT deployed; Fixes 2+3 (decay.py explicit system pass + consolidation.py user_id propagation) ARE deployed. Double-decay continues because uid=0 is still included in per-user loop AND the explicit system block also processes uid=0 — same double-decay condition. Side effect: other callers (patterns.py, dream_consolidation.py, consolidation.py) lack explicit system fallback — pre-existing gap not introduced by Fix-1. Deployment requires `docker compose restart recall-worker` (ARQ no hot-reload).** | **High** | **35** |
| **Q35.5** | **Mitigation assessment WARNING: rehabilitate endpoint broken (off-by-one); amnesty IS viable and did rescue 4,173 memories (Q36.1). Amnesty skips ephemeral, pinned, and permanent memories. Purge/decay are wrong tools. Recommended action completed: amnesty ran live on 2026-03-15T15:42 UTC.** | **Low → Resolved via Q36.1** | **35** |
| **Q36.2** | **Hygiene 0-candidate root cause confirmed: not a bug. The 4-condition filter (importance<0.3, access_count=0, superseded_by IS NULL, created_at < cutoff) is logically correct. System's oldest memory: 2026-02-14T18:00. At 04:00 UTC on 2026-03-16, cutoff = 2026-02-14T04:00 — oldest memories are 29h 23m beyond cutoff but import started after 04:00. First genuine candidate crosses at 2026-03-17T04:00 UTC.** | **Low** | **36** |
| **Q36.5** | **Fix-1 risk assessment WARNING: single-line change is low-risk but has side effects in 4 callers (patterns, dream_consolidation, consolidation, decay). After Fix-1, memories with `user_id=0` stored explicitly would be silently skipped by patterns/dream_consolidation/consolidation (no system-user fallback in those workers). FamilyHub users (uid 53–71, 74 memories) will now be correctly included in per-user loops. Deployment requires `docker compose restart recall-worker`.** | **Low** | **36** |
| **Q33.1 (post-hoc)** | **Hygiene cron now firing on schedule: 2026-03-16T04:00 UTC confirmed (id=394171); 0 candidates again (correct per Q36.2 date boundary analysis); FAILURE streak resolved. This is a WARNING not HEALTHY because archive_count=0 — operational confirmation of actual archival pending at 2026-03-17T04:00 UTC.** | **Low** | **33 (post-hoc 2026-03-16)** |
| **Q33.6** | **Superseded pool ~613/day (23.5h clean measurement; Q21.3 estimate confirmed). Active fraction stable at 28.8%. Projected pool at GC eligibility (2026-03-21T19:12 UTC): ~19,610 — under 20,000 concern threshold; first GC batch will be large but manageable. GC infrastructure should be confirmed operational before window opens.** | **Medium** | **33 (post-hoc 2026-03-16)** |
| **Q25.4** | **Purge endpoint scope clarified: `/admin/memory/purge` uses `scroll_all(include_superseded=False)` by default — targets ACTIVE low-quality memories only (1,081 eligible: importance≤0.15, age≥7d, access=0); consolidation-superseded memories (15,099) are explicitly excluded from its scope by IS NULL filter; Q24.6 GC gap is fully unaddressed by any available endpoint or scheduled cron; purge deletion logic is correct (Qdrant + Neo4j DETACH DELETE) but misscoped for GC purpose; new endpoint or cron required for superseded GC** | **Medium** | **25** |
| **Q26.3** | **Double-decay compound damage growing: floor-clamped count 673 (+41 from Q23.1 baseline of 632, +6.5%); ~10 new floor-clamped memories/day; 179.5 importance-units stolen across 5,975 active memories (avg 0.030 per memory, 6% of typical 0.5 initial importance); 3-7d cohort ratio 1.2988 reflects stability variation not absence of damage; floor-clamped count is most reliable direct damage metric; first hygiene batch (2026-03-17) NOT materially inflated by double-decay for 30d+ cohort (both decay models reach floor by 30d)** | **Medium** | **26** |
| **Q26.5** | **Ghost re-accumulation trap characterized: 1,833 active consolidation-source memories with user_id=None (30.7% of active corpus); IS NULL-only deployment eliminates current ghost users immediately but re-accumulation within weeks as these 1,833 memories get superseded through consolidation; co-deployment of Q21.5 (IS NULL filter) AND Q24.5 (consolidation user_id= propagation) required for permanent fix; 3,191 additional null-uid memories are system/observer by design (not re-accumulation seeds)** | **Medium** | **26** |

### INCONCLUSIVE — Open (observation gap, not resolved)

| ID | Finding | Severity | Wave |
|----|---------|---------|------|
| **Q26.1 / Q28.1 / Q29.1 / Q30.1 / Q31.1 / Q32.1 → RESOLVED Q35.2/Q33.1** | **Hygiene first-archival chain: Q32.1 was the 9th consecutive miss, 0 hygiene_run entries in 379,666 audit records. RESOLVED: Q35.2 confirmed task is registered in `WorkerSettings.cron_jobs` with daily 04:00 UTC schedule. Q33.1 (post-hoc 2026-03-16) confirmed cron fired at 04:00 UTC on schedule (id=394171); 0 candidates (correct — system only 29 days old per Q36.2). First actual archival expected 2026-03-17T04:00 UTC. The 9-wave miss was a monitoring artifact — task was registered all along.** | **Critical → Resolved** | **26/28/29/30/31/32/35/33** |
| **Q28.3 / Q29.3** | **Double-decay archival count parity + Week 12 cumulative: Q29.1 prerequisite not met (auto_archive still 0); Week 12 dates (Mar 17-21) not yet reached; Q27.7 analytical proof stands (both decay regimes archive same count at 30d); empirical verification pending** | **Info** | **28/29** |
| **Q33.3** | **Floor-clamped 24h rate INCONCLUSIVE: Q31.3 baseline (1,049 at 2026-03-15T13:46) invalidated by amnesty live run at 2026-03-15T15:42 (reset floor-clamped to ~1). Cannot compute pre-amnesty accumulation rate. Secondary finding: 3,198 amnesty-eligible in 23.5h (up from 5 in Q36.4); 0.0-0.2 bucket: 12.5% (up from 3.9%). Estimated floor-clamped (exactly 0.05): ~50-200. Amnesty-boosted memories will decay back to floor by ~2026-03-21 without Fix-1. Re-run recommended at ~2026-03-21 for clean post-amnesty floor-clamped rate.** | **High** | **33 (post-hoc 2026-03-16)** |
| **Q28.4** | **GC-eligible cohort: target date 2026-03-21T19:12 UTC; 0 GC-eligible today; superseded pool 15,185 (Q29.7); re-verify on/after 2026-03-21T19:12 UTC** | **Info** | **28** |
| **Q28.7** | **Hygiene Week 13 batch (Mar 22-28, ~128/day): depends on Q28.1/Q29.1 data; target dates now 7-13 days from Wave 29; re-verify starting 2026-03-22** | **Info** | **28** |
| **Q30.7 / Q31.6** | **GC-eligible cohort INCONCLUSIVE: Q30.7 6d 8h before 2026-03-21T19:12 UTC; Q31.6 re-run 6d 4h before; gc_run=0; superseded pool 15,335 (+151 from Q30.7 in ~3.5h; burst rate ~1,035/day); no GC endpoints exist (404); Wave 32+ verdict-capable on/after 2026-03-21T19:12 UTC** | **Info** | **30/31** |
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

Wave 25 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q25.5 | **Hygiene first archival imminent**: zero active memories currently meet all hygiene criteria (age>30d is binding constraint); oldest active memory created 2026-02-14 (28 days old as of Q25.5); first batch expected 2026-03-17 at 04:00 when Feb 14 cohort crosses 30-day threshold; hygiene `scroll_hygiene_candidates` criteria are well-formed (`access_count lte=0` confirmed correct); double-decay accelerates importance decay into sub-0.3 territory faster than expected — first batch may be larger than single-decay assumptions suggest; **time-sensitive follow-up required on 2026-03-17** | 25 |
| Q25.6 | ARQ Mar 15 timing anomaly fully explained as isolated catch-up event from Q22.9 outage slot; 200-entry audit history (22 complete 6h slots) shows no recurring ARQ restart pattern; 20 raw "burst events" all classified as normal double-decay pairs (11–13s gaps) or boundary artifacts; Mar 15T00 single run = catch-up after Q22.9 outage missed the 00:15 scheduled slot; Mar 15T06 4.3-min gap = post-restart queue settling artifact (still canonical 2× factor); Q22.1 double-decay 2× model remains complete and accurate characterization of decay behavior | 25 |

Wave 31 re-run HEALTHY addition:

| ID | Finding | Wave |
|----|---------|------|
| Q31.7 | **LLM per-call timeout tiers FULLY DEPLOYED**: 17/17 generate() callsites have explicit `timeout=` matching tier spec (15s: signal_detector/search; 30s: observer/state_fact_extractor/admin; 60s: causal_extractor/contradiction_detector/document_ingest/fact_extractor; 90s: consolidation/patterns/cognitive_distiller/dream_consolidation/profile_drift); `llm.py:generate()` signature confirmed; httpx per-request timeout override path confirmed; 180s semaphore-hold risk eliminated; full reversal from prior Q31.7 run (15/18 callsites missing); closes Q15.3/Q16.3 | 31 (re-run) |

Wave 32–33 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q32.4 | **Sunday reconcile cron confirmed registered and functional**: cron defined in `main.py` (`weekday=6, hour=5, minute=30`); manual trigger produces auditable `action=reconcile` entry; stores fully in sync (21,373 Qdrant = 21,373 Neo4j); zero orphans, zero mismatches at measurement time; reconcile infrastructure is operational | 32 |
| Q32.6 | **LLM semaphore hold events: no >60s accumulation risk; 17/17 callsites compliant** (Q31.7 re-confirmed); `httpx.TimeoutException` properly caught + logged + metriced; semaphore released via `async with` — no leak path; max theoretical hold = 90s (heavy tier, intentional); 180s unbounded hold from Q15.3 structurally eliminated; zero `llm_error` or `llm_timeout` audit entries | 32 |
| Q33.7 | **Feb 14 cohort intact — double-decay has NOT degraded oldest memories**: 14 active memories all maintain importance 0.30–0.40 (well above floor); median access_count ~30; 0 floor-clamped in the >30d archival boundary group; floor-clamped backlog (1,049) concentrated in mid-life 7–21d cohorts; archival backlog specifically >=30d old: **0 memories**; confirms Q27.7 proof that both decay regimes archive same count at 30d | 33 |

Wave 35–36 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q35.6 | **Floor-clamped stable at 1,049 over 2h 14min**: zero net change from Q31.3 baseline; consolidation not running in measurement window; confirms growth is episodic not continuous | 35 |
| Q36.1 | **Amnesty live run rescued 4,173/5,211 floor-clamped memories (80.1% of scanned, 99.9% of eligible)**: post-run residual eligible: 5; 0.0-0.2 bucket contracted from 23.3% to 3.9%; amnesty writes no audit rows (observability gap noted) | 36 |
| Q36.3 | **One-char rehabilitate fix (`>= 0.05` → `> 0.05`) would reach ~838/846 (99.1%) of null-pool**: "no default branch" risk does not strand bulk because ~99% of floor-clamped nulls are durable (branch 2 covers); ~8 ephemeral low-access correctly unreachable by design | 36 |
| Q36.4 | **Post-amnesty residual: 5 amnesty-eligible memories** (HEALTHY threshold <100); importance distribution confirms success; amnesty endpoint logic verified correct (graph_strength modulates boost, not eligibility) | 36 |
| Q36.6 | **N3 (stranded, amnesty-ineligible) ≈ 8 ephemeral ac<3 memories**: N2 (graph-isolated) does not exist — graph connectivity does not gate eligibility; N1 (rescued by amnesty) ≈ 838/846 (99.1%); ephemeral stranding is correct lifecycle behavior | 36 |

Wave 34 HEALTHY additions:

| ID | Finding | Wave |
|----|---------|------|
| Q34.3 | **Importance mismatch re-accumulation rate 0.00/hour post Q31.5 repair**: mismatch rate measured 0.00/hour over 58-minute post-repair window with 33 consolidation events. Single transient mismatch at 14:32 self-cleared by 15:10 without intervention. Q31.5 implied ~28/hour re-accumulation rate; actual observed rate is near-zero. Consolidation events in window produced almost no new mismatches — consistent with same-session create-then-supersede cycles resolving within the reconcile polling interval. Clean-slate repair from Q31.5 is holding. | 34 |
| Q34.5 | **Integer-0 active pool has zero retrieval-contaminating zombie memories**: 952 int-0 active memories; mean importance 0.185; 92% never accessed (access_count=0); 0 memories meet zombie criteria (imp>0.5 AND ac=0 AND age>14d) — single candidate at 0.950 is 13d old (1 day short of threshold). Int-0 pool mean (0.185) is *below* null pool mean (0.257) — never-decayed memories are not inflating importance because they were inherently low-importance at creation. 18 memories with imp>0.5 are all recent (within 13d) and do not qualify as zombies. No retrieval pollution from this cohort is detectable. | 34 |

---

## 3. Waves 35–36 Results and 2026-03-16 Post-Hoc Re-runs

### Overview

Wave 35 is the **crisis-response wave** — six questions probing the mortality crisis infrastructure: the rehabilitate endpoint defect, hygiene cron status, floor-clamped domain analysis, fix deployment state, immediate mitigation options, and current growth rate. Of 6 questions: 2 FAILURE (Q35.1, Q35.3), 3 WARNING (Q35.2, Q35.4, Q35.5), 1 HEALTHY (Q35.6).

Wave 36 is the **intervention + verification wave** — amnesty ran live, and five questions verified the outcome and characterized residual risk. Of 6 questions: 0 FAILURE, 2 WARNING (Q36.2, Q36.5), 4 HEALTHY (Q36.1, Q36.3, Q36.4, Q36.6).

The 2026-03-16 post-hoc re-runs (Q33.1, Q33.3–Q33.6) measured 24-hour rates and cron behavior on the day after the Wave 35–36 session. Of 5 questions: 2 FAILURE (Q33.4, Q33.5), 1 WARNING (Q33.1, Q33.6), 1 INCONCLUSIVE (Q33.3).

**The defining event across this entire cluster: amnesty live run at 2026-03-15T15:42 UTC rescued 4,173 floor-clamped memories — the first successful large-scale data-recovery action in the research program.** However, without Fix-1 (qdrant.py uid>0 guard), the corpus will return to pre-amnesty degraded state by ~2026-03-21.

---

### Wave 35 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q35.1 | FAILURE | Medium | Rehabilitate endpoint `>= 0.05` off-by-one misses all floor-clamped memories at exactly 0.050; endpoint never invoked; fix: change to `> 0.05` in `admin.py:1123` |
| Q35.2 | WARNING | Low | Hygiene cron registered and ran once (2026-03-15T14:47); 0 candidates (expected — system 29 days old); filter logic correct; first real archival 2026-03-17T04:00 UTC |
| Q35.3 | FAILURE | High | 846 null-user_id floor-clamped; development domain 229 (FAILURE threshold >100); total critical domain casualties 413 (48.8%); growth +202 from Q34.7's 644 |
| Q35.4 | WARNING | High | 2/3 fixes deployed (consolidation user_id + decay.py explicit pass); Fix-1 (qdrant.py uid>0 guard) NOT deployed; double-decay continues |
| Q35.5 | WARNING | Low | Rehabilitate broken; amnesty IS viable (4,173 eligible confirmed by dry-run); purge/decay are wrong tools; amnesty recommended |
| Q35.6 | HEALTHY | None | Floor-clamped stable at 1,049 over 2h 14min; consolidation not running in measurement window; growth episodic not continuous |

---

### Wave 36 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q36.1 | HEALTHY | None | Amnesty live run: 4,173 rescued (80.1% of 5,211 scanned; 99.9% of eligible); post-run residual: 5; 0.0-0.2 bucket: 3.9% (down from 23.3%); no audit rows written (bulk ops blind to audit trail) |
| Q36.2 | WARNING | Low | Hygiene 0-candidate root cause confirmed: not a bug; filter correct; system's oldest memory 2026-02-14T18:00; cutoff at 04:00 UTC misses by hours; first candidate crosses 2026-03-17 |
| Q36.3 | HEALTHY | None | Rehabilitate one-char fix would reach ~838/846 (99.1%) of null-pool; "no default branch" risk does not apply because ~99% durable; incremental rescue beyond amnesty: ~0–7 memories |
| Q36.4 | HEALTHY | None | Post-amnesty residual: 5 eligible; 0.0-0.2 bucket: 3.9%; active pool 6,126 memories; superseded pool ~15,429; amnesty cleanup confirmed at corpus scale |
| Q36.5 | WARNING | Low | Fix-1 NOT deployed; 74 FamilyHub memories (uid 53–71) discovered; other callers lack system-user fallback; deployment requires container restart |
| Q36.6 | HEALTHY | None | N3 (stranded) ≈ 8 ephemeral memories; N2 (graph-isolated) does not exist; amnesty eligibility gates on durability not graph_strength; N1 rescued ≈ 838/846 (99.1%) |

---

### 2026-03-16 Post-Hoc Re-run Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q33.1 | WARNING | Low | Hygiene cron fired 2026-03-16T04:00 UTC (2nd run, on schedule); 0 candidates (correct — Feb 14 cohort just crossing 30d boundary); FAILURE streak resolved; first archival 2026-03-17T04:00 UTC |
| Q33.3 | INCONCLUSIVE | High | Floor-clamped 24h rate invalidated by amnesty; secondary: 3,198 amnesty-eligible 23.5h post-amnesty (640× increase from 5); 0.0-0.2 bucket 12.5%; floor-clamped (exactly 0.05) estimated ~50-200 |
| Q33.4 | FAILURE | Medium | Sunday reconcile cron missed 2026-03-16T05:30 UTC window; 24h 12m gap; worker likely restarted overnight; Q32.4 HEALTHY conditionally confirmed (manual trigger works) but operational reliability unconfirmed |
| Q33.5 | FAILURE | High | Mismatch rate ~41/hour (1,027 in 25.1h from clean baseline); Q24.2's ~1.3/hour estimate rejected (31×); 15.8% of active corpus has divergent retrieval scores; projected 6,888/week ≈ full active pool |
| Q33.6 | WARNING | Medium | Superseded pool ~613/day (23.5h measurement; Q21.3 estimate confirmed); projected ~19,610 at GC eligibility — manageable first batch |

---

### Wave 35–36 Cross-Domain Observations

#### Observation 1: Amnesty is the first successful large-scale data recovery in the research program

Q36.1 is the most positive operational result in the entire 36-wave research program. After 24 waves of documented decay accumulation and zero data recovery actions, the amnesty live run at 2026-03-15T15:42 UTC rescued 4,173 memories — reducing the 0.0-0.2 importance bucket from 23.3% to 3.9% of total memories. This demonstrates the system's self-healing infrastructure is functional when invoked.

The critical caveat: amnesty is a one-shot repair, not a structural fix. Q33.3's secondary finding (3,198 amnesty-eligible 23.5h later) confirms that without Fix-1, the corpus decays back at the same rate — reaching the pre-amnesty degraded state by approximately 2026-03-21 under the double-decay regime.

#### Observation 2: Hygiene 9-wave FAILURE streak was a monitoring artifact

Q35.2 confirmed that `run_hygiene` is registered in `WorkerSettings.cron_jobs`. Q36.2 confirmed the 0-candidate results were correct because the system is only 29 days old — no memories have crossed the 30-day archival threshold yet. The "9 consecutive FAILURE" characterization was technically accurate (no archival had occurred) but missed the distinction between "cron not running" and "cron running but finding no candidates." First genuine archival is expected at 2026-03-17T04:00 UTC.

#### Observation 3: Two new FAILURE threads opened on 2026-03-16

Q33.4 (Sunday reconcile missed) and Q33.5 (41/hour mismatch rate) are both operational failures that were not measurable from the March 15 session. Q33.5 is particularly significant: the ~41/hour mismatch rate means 15.8% of active corpus currently has divergent retrieval scores. This makes the reconcile auto-repair change (from scan-only to repair=true on every scheduled run) the highest-urgency operational action remaining.

#### Observation 4: Fix-1 is the single blocking action preventing corpus stabilization

With Q35.4 confirming that Fixes 2+3 are deployed, the only remaining code change blocking corpus stabilization is Fix-1 (`qdrant.py:1207` `uid > 0` guard). Q36.5 assessed it as low-risk with known side effects. Q36.2 closes the hygiene concern. Q35.2 closes the hygiene-cron-registration concern. The entire corpus recovery pathway now depends on a single-line code change plus container restart.

---

### Fix Priority Table (Updated Post-Wave 36)

| Priority | Fix | Status | Impact |
|----------|-----|--------|--------|
| **P0 — IMMEDIATE** | Deploy Fix-1: `qdrant.py:1207` `if uid is not None and uid > 0:` + `docker compose restart recall-worker` | NOT DEPLOYED (Q35.4, Q36.5) | Stops double-decay; prevents amnesty benefit from decaying away by 2026-03-21 |
| **P0 — IMMEDIATE** | Change reconcile scheduler to `repair=true` on every run | NOT DONE (Q33.5) | Stops 41/hour mismatch accumulation; 15.8% of active corpus currently degraded |
| **P1 — THIS WEEK** | Fix rehabilitate endpoint: `admin.py:1123` `>= 0.05` → `> 0.05` | NOT DEPLOYED (Q35.1) | Enables standalone rescue tool for future floor-clamped events |
| **P2 — BEFORE 2026-03-21** | Second amnesty run if Fix-1 not deployed | Pending | Intercepts wave of decaying memories before they reach floor; 3,198 currently sub-amnesty-threshold |
| **P3 — BEFORE 2026-03-21** | Verify GC infrastructure for ~19,610 superseded memory first batch | Pending (Q33.6) | First GC window opens 2026-03-21T19:12 UTC |
| **P4 — MONITOR** | Watch 2026-03-17T04:00 UTC hygiene run for first actual archival | Pending (Q33.1) | Validates hygiene pipeline end-to-end |

---

## 4. Wave 34 Results (Q34.1–Q34.7)

### Overview

Wave 34 is the **root-cause consequence wave** — the first wave to measure the downstream damage from the double-decay and user_id attribution architecture bugs whose root causes were fully identified in Wave 33. Of 7 questions: 4 FAILURE (Q34.1, Q34.2, Q34.6, Q34.7), 1 WARNING (Q34.4), 2 HEALTHY (Q34.3, Q34.5).

The defining narrative: the Q33.2b root-cause identification unlocked a new question set that measured *what the bugs have actually done* to the corpus — not just confirming the bugs are present, but quantifying the casualty count, the ongoing accumulation rate, and the window before permanent data loss.

**Key findings count**: 4 FAILURE, 1 WARNING, 2 HEALTHY.

---

### The Mortality Crisis (Q34.7)

Q34.7 is the most time-sensitive finding in the entire research program.

**644 premature casualties** are floor-clamped memories that should still be above the decay floor under correct single-decay logic. They are at importance=0.05, the hard floor. They have never been retrieved (99% access_count=0). They were high-value at creation (median initial_importance=0.700). The double-decay bug pushed them to floor prematurely — median age 13.4 days old, where single-decay would place them at importance ~0.0776 (still above floor and eligible for retrieval).

**The poverty trap is permanent without intervention.** Floor memories score 1/3 of an average corpus member in retrieval. Since they never surface, they receive no access boost. The access boost formula is +0.02 additive per access — not a restore to initial_importance. Without daily access (which is near-zero probability at importance=0.05), each memory needs ~8.3 days of daily access to reach corpus median. They will not receive it.

**The hygiene deadline is ~16.6 days from 2026-03-15.** The hygiene worker deletes memories where `access_count==0 AND importance<0.3 AND age>30d`. With median age 13.4 days, the median premature casualty hits the 30-day deletion window in approximately 16.6 days. Without a bulk re-score run, 644 high-value memories — including infrastructure knowledge, tooling facts, and development context — will be permanently deleted.

The `POST /admin/rehabilitate-importance` endpoint exists but targets `importance < 0.05` (strict less-than). Floor-clamped memories sit at exactly 0.050. Verify the endpoint filter uses `<=` before executing.

---

### The Self-Reinforcing Loop (Q34.6)

Q34.6 establishes that the floor-clamped pool is not merely accumulating — it is accelerating via a self-reinforcing feedback loop:

1. Active sessions generate memories (observer, signals, patterns workers)
2. Consolidation runs hourly, merging clusters → produces null-user_id outputs (Q24.5 bug)
3. Null-user_id outputs are double-decayed (Q33.2b bug) → reach floor in ~4.7 days
4. Floor-clamped count grows: 199/day (conservative) to 648/day (active session)
5. Active sessions generate more memories → step 1 repeats

At the current autoresearch session throughput, the loop produces **648 new floor-clamped memories per day** — 13× the 50/day FAILURE threshold. Until Q24.5 (consolidation user_id= fix) is deployed, every consolidation run permanently adds to the floor-clamped backlog with no escape.

---

### user_id Attribution Architecture (Q34.2)

Q34.2 extends the Q33.2b root-cause finding to reveal that the entire user_id attribution architecture is broken across four independent dimensions simultaneously:

1. **Storage/query contract mismatch**: `auth.py` writes integer-0 for admin-key requests; `_user_conditions(0)` queries IS NULL. These match different populations.
2. **Five worker paths omit user_id**: observer, signals, patterns, ingest, session snapshot — all produce null-attributed memories regardless of session context.
3. **Consolidation deserialization drops user_id**: `_get_eligible_memories()` rebuilds Memory objects without reading `user_id` from payload. Even if source memories have user_id=0, the merged output defaults to user_id=None.
4. **Integer-0 pool actively growing at 58/day**: All from session-summary hooks using the master admin key.

This means the "three-population split" identified in Q33.2b (null-double-decayed, int-0-never-decayed, user_id=1+-correctly-decayed) is not an accident that can be fixed with one line — it reflects four distinct code-level attribution failures that each require their own fix.

---

### Positive Surprise (Q34.3)

Q34.3 is a significant positive result. Q31.5 found the mark_superseded root cause creates ~28 new importance mismatches per hour. Q34.3 measured the actual re-accumulation rate after the Q31.5 clean-slate repair: **0.00/hour over a 58-minute window with 33 consolidation events.**

The Q31.5 rate estimate was based on a pre-repair accumulation trend, not a post-repair measurement. The actual post-repair rate is near-zero, suggesting that consolidation events during the measurement window predominantly created new memories rather than supersessions that would trigger mismatches. This does not mean the mark_superseded root cause is fixed — only that the current session's consolidation pattern produced minimal mismatch-generating supersessions.

---

### Fix Priority Ordering (16.6-Day Hygiene Window)

Given the mortality crisis deadline, fix sequencing is time-constrained:

| Priority | Fix | Deadline | Status (Post-Wave 36) | Impact |
|----------|-----|----------|-----------------------|--------|
| **P0 — IMMEDIATE** | Bulk re-score 644 premature casualties: `POST /admin/rehabilitate-importance` with `importance <= 0.05` filter | Before 2026-04-01 | **DONE via amnesty (Q36.1)** — 4,173 rescued; 8 ephemeral stranded (correct) | Prevented permanent deletion; amnesty superseded rehabilitate for initial rescue |
| **P1 — SAME DAY** | Double-decay Fix-1: `qdrant.py:1207` add `and uid > 0`; Fix-2: `decay.py:296` explicit system pass present | Immediately | **Fix-2 DEPLOYED; Fix-1 NOT DEPLOYED (Q35.4)** | Double-decay continues for null-pool; amnesty benefit will decay away by ~2026-03-21 without Fix-1 |
| **P2 — SAME DAY** | Consolidation user_id= fix: `consolidation.py:235` pass `user_id=cluster[0].user_id` | Immediately | **DEPLOYED (Q35.4)** | New consolidation outputs now correctly attributed |
| **P3 — THIS WEEK** | Hygiene cron: register hygiene task in `cron_jobs` | Before 2026-03-22 | **CONFIRMED REGISTERED (Q35.2); FIRING ON SCHEDULE (Q33.1)** | First archival expected 2026-03-17T04:00 UTC |
| **P4 — THIS WEEK** | Worker user_id attribution: pass user context through observer, signals, patterns, ingest paths | This week | NOT DONE | Closes null-accumulation from background workers |
| **P5 — LOW URGENCY** | Admin decay endpoint scoping: add `user_id` param, admin-role check, caller-stamped audit | When convenient | NOT DONE | Closes single-call full-corpus floor-clamp attack surface (no confirmed incident) |

---

### Wave 34 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q34.1 | FAILURE + INCONCLUSIVE | High | 795 null-pool memories at decay floor (>500 FAILURE threshold); importance-units stolen INCONCLUSIVE (int-0 not a valid control); null pool mean 0.2584 higher than never-decayed int-0 mean 0.1852 (inversion invalidates comparison) |
| Q34.2 | FAILURE | High | user_id attribution broken in 4 dimensions: storage/query mismatch; 5 worker paths omit user_id; consolidation deserialization drops user_id; int-0 pool growing 58/day |
| Q34.3 | HEALTHY | None | Mismatch re-accumulation rate 0.00/hour post Q31.5 clean-slate repair; 33 consolidation events produced near-zero new mismatches; Q31.5 repair holding |
| Q34.4 | WARNING | Medium | Admin decay endpoint unscoped — single authenticated call can floor-clamp entire corpus; audit log indistinguishable from cron run; no confirmed incident but structural risk present |
| Q34.5 | HEALTHY | None | 0 zombie int-0 memories (strict: imp>0.5, ac=0, age>14d); int-0 mean 0.185 below null mean 0.257 — no retrieval inflation; 92% never accessed; dormant low-value entries |
| Q34.6 | FAILURE | High | Consolidation floor-clamped growth 199–648/day; self-reinforcing loop: session activity → consolidation candidates → null-user_id outputs → floor-clamped; 13× FAILURE threshold at current throughput |
| Q34.7 | FAILURE | High | 644 premature casualties; 99% access_count=0; poverty trap confirmed (floor score 1/3 corpus median); hygiene deadline ~16.6 days; bulk re-score mandatory; `rehabilitate-importance` filter must use `<= 0.05` not `< 0.05` |

---

### Wave 34 Cross-Domain Observations

#### Observation 1: Root cause investigation chain complete — damage quantification is now the priority

The Q33.2b breakthrough unlocked a second research phase: now that the *mechanism* is known, Wave 34 quantified the *consequences*. Q34.1 (795 floor casualties), Q34.6 (199-648/day new accumulation), and Q34.7 (644 premature casualties with 16.6d deadline) convert an abstract "decay is running twice" finding into a concrete triage problem with a hard deadline.

#### Observation 2: The three-population split is a symptom of a deeper architecture problem

Q33.2b identified three populations (null-double-decayed, int-0-never-decayed, user_id≥1-correctly-decayed). Q34.2 reveals why: the code was built with a single intended population ("system/unowned memories stored as null") but the actual data has two separate system populations because auth.py and workers/observer.py make different choices about what to write when there is no authenticated user. This is not a one-line fix — it requires a coordinated correction across storage, query, consolidation, and worker-ingest paths.

#### Observation 3: Q34.3 positive result clarifies the mismatch accumulation model

The Q31.5 rate of ~28/hour was an estimate based on delta-over-time from accumulated pre-repair mismatches. Q34.3's post-repair measurement of 0.00/hour over 58 minutes suggests the rate is episodic rather than continuous — mismatches accumulate during heavy consolidation activity and are near-zero during quieter periods. This makes the weekly reconcile cron (Sunday 05:30) more effective than the ~28/hour estimate implied.

#### Observation 4: Two HEALTHY verdicts in a single wave is unprecedented since Wave 20

Prior waves (29–33) produced zero or one HEALTHY finding. Wave 34 produces two (Q34.3, Q34.5). Both are targeted validation questions that tested specific concerns (retrieval pollution from int-0 pool, mismatch re-accumulation) and found the concerns are not realized at current scale. This confirms the research is now correctly focusing on confirmed failures rather than speculative risks.

---

## 5. Wave 32–33 Results (Q32.1–Q32.7, Q33.2, Q33.2a, Q33.2b, Q33.2c, Q33.7)

### Overview

Wave 32 ran on 2026-03-15T14:27–14:32 UTC, approximately 14–41 minutes after the Wave 31 re-run. Of 7 questions: 2 FAILURE (Q32.1 hygiene 9th miss, Q32.2 double-decay 22nd consecutive), 3 INCONCLUSIVE (Q32.3/Q32.5/Q32.7 timing), 2 HEALTHY (Q32.4 reconcile cron, Q32.6 LLM timeouts). The three INCONCLUSIVE verdicts are timing artifacts — all were measured within minutes of their Wave 31 baselines and require 24h windows for meaningful rate computation.

Wave 33 is the **double-decay deep-dive wave** — a focused investigation chain that traced the double-decay to its exact root cause at the code level for the first time in 24 waves.

**The Q33.2b breakthrough**: The investigation chain Q31.2 → Q31.2a → Q33.2 → Q33.2a → Q33.2b systematically eliminated hypotheses until the exact mechanism was identified with direct Qdrant API confirmation:

1. **Q31.2**: IS NULL fix deployed but second full-corpus run persists
2. **Q31.2a**: Not admin API, not duplicate cron; ARQ source unclear
3. **Q33.2**: Two-replica hypothesis proposed based on sequential execution pattern
4. **Q33.2a**: Two-replica hypothesis **refuted** — SSH confirms 1 container, Redis confirms 0 duplicate ARQ heartbeats. True source identified in `run_decay_all_users` logic.
5. **Q33.2b**: **ROOT CAUSE FOUND** — `get_distinct_user_ids()` returns `[0]` (integer zero is `not None`). Per-user loop calls `worker.run(user_id=0)` → `_user_conditions(0)` → `IsNullCondition` → decays 5,043 null-user_id memories. Then explicit system pass calls `worker.run(user_id=0)` → same IsNullCondition → **same 5,043 memories decayed again**. Three-way population split: 5,043 null (double-decayed), 975 integer-0 (never decayed), 0 user_id=1+.
6. **Q33.2c**: Fix NOT deployed — 24th consecutive FAILURE. Both code changes remain unpatched.

### Wave 32 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q32.1 | FAILURE | Critical | Hygiene cron 9th consecutive miss; 0 hygiene_run entries in 379,666 audit records; scheduler has never fired a hygiene job; all maintenance crons absent; only decay and reconcile operational |
| Q32.2 | FAILURE | High | Double-decay 22nd consecutive; 2 full-corpus runs per cycle confirmed (5,994 each, 19–21s gap); IS NULL fix has not resolved doubling; pattern identical across all cycles |
| Q32.3 | INCONCLUSIVE | Low | Floor-clamped 24h rate — only 41 minutes elapsed since Q31.3 baseline; re-run required 2026-03-16T13:46 UTC |
| Q32.4 | HEALTHY | None | Sunday reconcile cron registered in source (`weekday=6, hour=5, minute=30`); manual trigger produces audit entry; stores in sync (21,373/21,373); zero orphans |
| Q32.5 | INCONCLUSIVE | Low | Importance mismatch 24h trajectory — only 12.6 minutes elapsed since Q31.5 repair; 0 new mismatches; re-run required 2026-03-16T14:17 UTC |
| Q32.6 | HEALTHY | None | LLM semaphore hold resolved; 17/17 callsites compliant (Q31.7 confirmed); max hold 90s (intentional); zero llm_error/llm_timeout audit entries; 180s risk structurally eliminated |
| Q32.7 | INCONCLUSIVE | N/A | Superseded pool growth rate — only 14 minutes since Q31.6; +22 qdrant_total (mixed inflows, not attributable to superseded growth); re-run required 2026-03-16T14:18 UTC minimum |

### Wave 33 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q33.2 | WARNING | Medium | Stale Redis job ruled out as double-decay source; sequential execution with gap=run duration inconsistent with pre-queued job; off-schedule cycles (06:45, 09:48) suggest worker restart catch-up; two-replica hypothesis proposed |
| Q33.2a | WARNING | High | Two-replica hypothesis **refuted** — 1 container confirmed via SSH (`docker ps`, container inspection); 0 ARQ heartbeats in Redis; `container_name: recall-worker` prevents duplicates. True source identified: `run_decay_all_users` logic bug — `scroll_all(user_id=0)` and explicit system pass both process same 5,043 null memories |
| Q33.2b | WARNING | HIGH | **ROOT CAUSE FOUND** — three-way population split confirmed via direct Qdrant API: 5,043 active null (double-decayed), 975 active integer-0 (never decayed), 0 active user_id=1+. `get_distinct_user_ids()` returns `[0]` because `uid=0` passes `is not None` check. Fix: (1) `qdrant.py:1207` add `and uid > 0`; (2) `decay.py:296` remove redundant system pass |
| Q33.2c | FAILURE | Critical | 24th consecutive double-decay FAILURE — neither fix deployed; `qdrant.py:1207` still `if uid is not None:`; `decay.py:296` still has redundant `worker.run(user_id=0)`; audit log confirms 2 full-corpus runs per cycle continuing |
| Q33.7 | HEALTHY | Low | Feb 14 cohort intact; 14 active memories all importance 0.30–0.40; 0 floor-clamped at 30d+ boundary; double-decay damage concentrated in 7–21d mid-life cohorts; archival backlog >=30d = 0 |

---

### Wave 32–33 Cross-Domain Observations

#### Observation 1: Double-decay root cause is now fully characterized — fix is trivial

Q33.2b is the culmination of 24 waves of investigation. The root cause is a semantic mismatch between code intent and data reality: the code uses `user_id=0` as a sentinel meaning "system/unowned memories stored with null", but the actual data has TWO distinct populations — integer-0 (975 memories, explicitly stored by system/worker ingest paths) and JSON-null (5,043 memories, legacy consolidation records). `IsNullCondition` catches only the null population, while `get_distinct_user_ids()` includes integer-0 in the per-user loop. The result: null memories decayed twice, integer-0 memories decayed zero times.

The fix is two lines:
1. `qdrant.py` line 1207: `if uid is not None:` → `if uid is not None and uid > 0:`
2. `decay.py` line 296: remove the redundant `stats = await worker.run(user_id=0)` call

Optionally, a more thorough fix would also add a `FieldCondition(match=0)` branch in `_user_conditions` to catch the 975 integer-0 memories that are currently never decayed.

#### Observation 2: Hygiene cron has NEVER fired — not just broken recently

Q32.1 extends the miss streak to 9 consecutive windows, but more importantly reveals that `hygiene_run`, `archive`, and `decay_check` action types have ZERO entries in the ENTIRE audit log (379,666 entries). The scheduler has never executed a hygiene job since the system was stood up on Feb 14. This is not a recent regression — it is a standing defect. The hygiene cron task is either not registered, not included in `cron_jobs`, or silently failing at startup.

#### Observation 3: Feb 14 cohort health provides a calibration point for double-decay damage

Q33.7 demonstrates that double-decay's damage is bounded by access patterns. Foundational memories with sustained access (the Feb 14 cohort, median ac~30) maintain healthy importance (0.30–0.40) despite 29 days of double-decay exposure. The damage is concentrated in low-access memories that hit floor in 4.7 days under double-decay (vs 9.5 days under single-decay) — the Q27.3 "information quality in 0–10d window" finding. This confirms Q27.7's analytical proof: at the 30d archival boundary, both decay regimes archive the same count because floor is reached well before 30 days under either regime.

#### Observation 4: Three INCONCLUSIVE findings require 24h re-measurement

Q32.3 (floor-clamped rate), Q32.5 (importance mismatch trajectory), and Q32.7 (superseded pool growth) were all measured within minutes of their Wave 31 baselines. They require re-measurement on/after 2026-03-16T13:46 UTC for reliable 24h rate computation.

---

## 6. Wave 31 Results (Q31.1–Q31.7, Q31.2a) — First Run and Re-Run

### Overview — First Run

Wave 31 first run continues on 2026-03-15, ~1 hour after Wave 30. Of 9 questions: 6 FAILURE, 1 WARNING, 2 INCONCLUSIVE.

The defining escalation: **Q31.3 FAILURE — floor-clamped count surged from 941 to 1,049 (+108) in approximately 3 hours** between Wave 30 and Wave 31. Extrapolated daily rate: ~864/day, far higher than prior estimates of ~10-15/day. The consolidation-source component (+74 in 3 hours) is the primary driver, consistent with active consolidation runs at the 09:48 and 12:15 UTC slots. Q31.5 (mismatches 179→264, +47%) confirms mark_superseded bug at ~28/hour.

### Wave 31 First-Run Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q23.6 | WARNING | Medium | Per-supersedure audit logging exists (consolidation.py:299-305); 1000+ entries; user_id null (Q24.5 gap); 26/1000 duplicate memory_ids |
| Q27.1 | INCONCLUSIVE | Info | Hygiene timing-blocked; 1d 14h before 2026-03-17T04:00 UTC; superseded by Q31.1 FAILURE |
| Q31.1 | FAILURE | High | Hygiene cron broken (7th+); hygiene_run=0; archive=0; 2026-03-15T04:00 UTC passed with no entries |
| Q31.2 | FAILURE | High | Double-decay 20th consecutive; system pass processed=5,994/6,048 (99.1%); fix not deployed |
| Q31.3 | FAILURE | High | Floor-clamped 1,049/6,048 (17.3%); +108 from Q30.6 in ~3 hours; consolidation +74 |
| Q31.4 | FAILURE | Medium | Reconcile audit 7th consecutive FAILURE; reconcile_run=0 after manual trigger |
| Q31.5 | FAILURE | Medium | Importance mismatches 179→264 (+85, +47%); ~28/hour new accumulation rate |
| Q31.6 | INCONCLUSIVE | Info | GC eligibility 6d 5h away; gc_run=0; superseded pool 15,275 (+91 from Q30.7) |
| Q31.7 | FAILURE | High | LLM timeout tiers not deployed; 15/18 generate() callsites missing timeout= |

---

### Overview — Re-Run

The Wave 31 re-run was conducted on 2026-03-15T14:13–14:19 UTC, approximately 3.5 hours after the first run. It produces significant verdict reversals for Q31.4 and Q31.7, adds Q31.2a to characterize the ARQ double-enqueue root cause, and refines Q31.3 and Q31.5.

**Two major corrections:**

**Q31.4 CORRECTION — 7 prior FAILURE waves were FALSE NEGATIVES.** The reconcile audit trail has been deployed and working the entire time. All prior waves queried `?action=reconcile_run` — a string that does not exist anywhere in the codebase. The deployed action name is `"reconcile"`. Q31.4 re-run confirmed `log_audit(action="reconcile")` in both `ops.py:373-377` and `workers/reconcile.py:112-116`, with live entries in the audit log. This closes a major analytical gap: Waves 24–30 were tracking a non-existent action name.

**Q31.7 CORRECTION — LLM timeout tiers fully deployed.** The prior Q31.7 run found 15/18 callsites missing `timeout=`. The re-run finds 17/17 compliant. This is a full reversal, closing the Q15.3/Q16.3 semaphore-hold risk that has been open since Wave 15.

**New finding Q31.2a:** The second full-corpus decay run per cycle is confirmed NOT from admin API calls (actor="decay" not "admin") and NOT from duplicate cron entries (single `cron(run_decay, ...)` in `main.py`). The ARQ worker is enqueuing `run_decay` twice per scheduler cycle via an unknown path. Both full-corpus runs appear since 2026-03-14T18:15 — the same cycle where the IS NULL fix was deployed — suggesting the IS NULL fix deployment may have triggered a re-enqueue event or the fix was deployed with an ARQ job state inconsistency. Admin endpoint structural risk also identified: `POST /admin/decay` calls `worker.run()` without `user_id`, which processes the entire corpus unscoped.

### Wave 31 Re-Run Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q31.1 | FAILURE | High | Hygiene cron broken; hygiene_run=0; archive=0; cron broken since 2026-03-09; decay cron alive — failure is hygiene-task-specific; action types `hygiene_run`, `archive`, `auto_archive` have never appeared in all-time audit log |
| Q31.2 | FAILURE | High | Double-decay 21st consecutive; IS NULL fix deployed (user_id=0 sentinel works) but second full-corpus run (5,994/slot) persists; processed count has not halved; total Qdrant: 21,354 |
| Q31.2a | FAILURE | High | Second full-corpus run source: NOT admin API (actor="decay"), NOT duplicate cron (1 cron entry only); duplicate enqueue source unknown; pattern consistent from 2026-03-14T18:15 onwards; admin endpoint also has structural risk (`worker.run()` unscoped) |
| Q31.3 | FAILURE | High | Floor-clamped 1,038 (ac=0) / 1,049 (any); stable vs prior Q31.3 run (−11 noise); total importance≤0.051 unchanged at 1,049; +97 above Q30.6 FAILURE threshold; partial IS NULL fix may have halted new accumulation but no drain active |
| Q31.4 | WARNING | Low | Reconcile audit IS deployed and working; action="reconcile" (not "reconcile_run"); 262 mismatches detected; repairs_applied=0 (scan-only); WARNING: scheduler never repairs; 7 prior FAILURE verdicts were false negatives |
| Q31.5 | WARNING | Medium | Repair=true clears all 261 mismatches in one run (0 remaining); scheduled runs are scan-only; mark_superseded root cause unpatched; mismatches re-accumulate continuously (~+28/hr); scheduler must be updated to use repair=true |
| Q31.6 | INCONCLUSIVE | Info | GC gate 6d 4h away (2026-03-21T19:12 UTC); superseded pool 15,335 (+151 from Q30.7 in ~3.5h; ~1,035/day burst); no GC infrastructure (404 on gc endpoints) |
| Q31.7 | HEALTHY | None | 17/17 generate() callsites have correct timeout= tiers; 0 missing; full reversal from first run (15/18 missing); 180s semaphore-hold risk eliminated; closes Q15.3/Q16.3 |

---

### Wave 31 Cross-Domain Observations

#### Observation 1: Floor-clamped accumulation rate is far higher than estimated — but partial fix may have stabilized it

Q30.6 showed delta=0 (79-minute same-day window). The first Q31.3 run showed +108 in approximately 3 hours (~36/hr). The second Q31.3 run (re-run, 29 minutes later) shows −11 (noise) — total importance≤0.051 population unchanged at 1,049. The Q30.6 WARNING was misleading; the true rate is visible only across multi-slot windows. The tentative positive signal: the IS NULL fix (user_id=0 sentinel in `_user_conditions`) may have halted NEW floor-clamping while existing 1,049 remain. This hypothesis requires confirmation over a multi-day window.

#### Observation 2: Reconcile audit is deployed — 7 waves of false-negative data must be discarded

Q31.4 re-run overturns 7 consecutive FAILURE verdicts. The practical consequence: mismatch trend data from Waves 24–30 that was characterized as "unknowable without audit trail" was in fact being logged continuously under `action="reconcile"`. The audit trail now shows exactly 2 entries (both from the Wave 31 session itself), suggesting the reconcile cron has not run automatically recently — or the audit DB was purged. This warrants a follow-up query: how many reconcile entries exist in the full audit log, and what is the last automatic cron run date?

#### Observation 3: ARQ double-enqueue is the remaining root cause of double-decay

Q31.2a establishes that the double-decay behavioral failure has evolved. The original Q22.1 root cause (`_user_conditions(None)` returning no filter) has been partially fixed. The new root cause is an ARQ job being enqueued twice per cycle. This is a different fix than the original — the original was a Python filter function; the new issue is in ARQ job dispatch. The admin endpoint (`POST /admin/decay`) is a structural risk but is not the active source. Likely investigation paths: (1) check ARQ job queue length and pending jobs in Redis; (2) check whether the IS NULL deployment restarted ARQ with a stale job in the queue; (3) check whether any code path outside `cron_jobs` calls `arq.enqueue_job("run_decay")`.

#### Observation 4: LLM timeout fix closes a 15-wave open FAILURE — confirmed positive deployment signal

Q31.7 HEALTHY is the first confirmed fix deployment observed in 21 waves of characterization. Every prior wave found zero fixes deployed. The Q15.3/Q16.3 180s semaphore-hold risk, open since Wave 15 (10+ waves), is now fully closed. This confirms the deployment channel is functional — the other identified fixes are deployable via the same path.

---

## 7. Wave 30 Results (Q30.1–Q30.7)

### Overview

Wave 30 is the **eighth consecutive fix-verification wave**. Of 7 questions: 3 FAILURE, 2 WARNING, 2 INCONCLUSIVE.

Wave 30 and Wave 29 executed on the same calendar day (2026-03-15), approximately 15–79 minutes apart. This explains the stable floor-clamped count (Q30.6 WARNING, not FAILURE) and stable importance mismatches (Q30.3 WARNING) — insufficient time elapsed for accumulation. The three FAILURE threads (Q30.2, Q30.4, Q30.5) represent the 19th, 6th, and 6th consecutive FAILURE verdicts respectively.

---

### Wave 30 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q30.1 | INCONCLUSIVE | Info | Hygiene first-archival (5th attempt): auto_archive=0 at 2026-03-15T10:50 UTC; 17.1h before 2026-03-16T04:00 UTC; Wave 31 mandatory FAILURE escalation |
| Q30.2 | FAILURE | High | Double-decay 19th consecutive; `_user_conditions(None)` returns [] unchanged; processed=6,002 per slot |
| Q30.3 | WARNING | Medium | Importance mismatches stable at 179 (Q29.7 baseline; δ=0); same IDs; historical artifact; no new mismatches from +26 new memories |
| Q30.4 | FAILURE | Medium | Consolidation user_id fix NOT deployed (6th consecutive); Memory() at line 235 still missing user_id=; floor-clamped consolidation stable at 375 |
| Q30.5 | FAILURE | Medium | Reconcile audit fix NOT deployed (6th consecutive); 0 log_audit(); Q30.3 trend limited to manual per-wave sampling |
| Q30.6 | WARNING | High | Floor-clamped 941/6,044 (15.6%); stable vs Q29.6 (δ=0); growth arrested in 79-min same-day window; within 800-941 WARNING range |
| Q30.7 | INCONCLUSIVE | Info | GC eligibility 6d 8h away (2026-03-21T19:12 UTC); superseded 15,184 (−1; flat); no automated GC cron |

---

### Wave 30 Cross-Domain Observations

#### Observation 1: Same-day measurement explains WARNING verdicts for Q30.3 and Q30.6

Both Q30.6 (floor-clamped) and Q30.3 (importance mismatches) show exactly δ=0 from Q29 baselines. This is not evidence of fixes or self-healing — it reflects that Waves 29 and 30 executed within a 79-minute window on the same day. The underlying bugs (Q30.2 double-decay, Q30.4 consolidation user_id) remain active. Multi-day measurement intervals will show resumed accumulation.

#### Observation 2: 19th consecutive double-decay FAILURE

Q30.2 marks the 19th consecutive characterization wave confirming Q22.1 undeployed. The fix is 3 lines in `_user_conditions()`. Combined with Q30.4 (6th consecutive) and Q30.5 (6th consecutive), the total fix burden remains ~19 LOC across 4 files. No code changes have been observed in any consecutive wave from Wave 12 to Wave 30.

#### Observation 3: Wave 31 carries two mandatory verdict gates

Wave 31 must run on/after 2026-03-16T04:00 UTC for Q31.1 (hygiene first archival) and on/after 2026-03-21T19:12 UTC for Q31.x (GC eligibility). Hygiene gate is the sooner, opening ~17 hours from Wave 30 measurement. If auto_archive remains 0 after 04:00 UTC, verdict is FAILURE (hygiene cron not running or age filter broken).

---

## 8. Wave 29 Results (Q29.1–Q29.7)

### Overview

Wave 29 is the **seventh consecutive fix-verification wave**. Of 7 questions: 4 FAILURE, 2 INCONCLUSIVE (timing-blocked), 1 WARNING.

The defining new result: **Q29.6 FAILURE — floor-clamped count 941 exceeds the 800 FAILURE threshold**. This is the first time floor-clamped accumulation has crossed the FAILURE threshold. The spike is driven by the Q24.5 consolidation user_id bug: consolidation-source floor-clamped memories grew from 7 (Q27.4 baseline) to 375 (+368, +5,257%) because memories consolidated without `user_id=` are invisible to user-scoped retrieval, receive zero access_count, hit importance floor 0.05 under double-decay (also active per Q29.2), and accumulate with no removal path until hygiene archives them after 30 days.

---

### Wave 29 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q29.1 | INCONCLUSIVE | Info | Hygiene first-archival (4th attempt): auto_archive still 0 at 2026-03-15T10:35 UTC; target 2026-03-16T04:00 UTC ~17.4h away |
| Q29.2 | FAILURE | High | Double-decay 18th consecutive; `_user_conditions(None)` returns [] unchanged; processed=6,002 per slot |
| Q29.3 | INCONCLUSIVE | Info | Week 12 archival: Q29.1 prerequisite not met; Week 12 dates (Mar 17-21) not yet reached |
| Q29.4 | FAILURE | Medium | Consolidation user_id fix NOT deployed (5th consecutive); consolidation-source floor-clamped 7→375 (+368) confirmed |
| Q29.5 | FAILURE | Medium | Reconcile audit fix NOT deployed (5th consecutive); 0 log_audit(); 179 importance_mismatches detected but repairs_applied=0 |
| Q29.6 | FAILURE | High | Floor-clamped 941 vs 673 Q27.4 baseline (+268, +39.8%); FAILURE threshold 800 exceeded; compound effect of Q22.1+Q24.5 |
| Q29.7 | WARNING | Medium | Superseded pool 15,185 (+55 from Q27.2); growing; 179 Qdrant/Neo4j importance mismatches; GC eligibility ~2026-03-21 |

---

### Wave 29 Cross-Domain Observations

#### Observation 1: Q29.6 FAILURE confirms compound damage from two undeployed fixes

Q29.6 is the first floor-clamped measurement to exceed the FAILURE threshold. The 941-vs-673 jump (+39.8%) is driven by two compounding undeployed bugs:
- **Q22.1 (double-decay)**: decays all memories at 2× rate → consolidation memories reach floor in ~4.7d instead of ~9.5d
- **Q24.5 (user_id=None)**: consolidated memories are invisible to user-scoped retrieval → access_count stays 0 → no importance reinforcement → floor at 4.7d guaranteed

Without either fix, consolidated memories are processed by the system-scope decay loop twice per slot and never accessed. The 375 consolidation-source floor-clamped (20.3% of 1,845 consolidation memories) is a direct measurement of the compound damage.

#### Observation 2: Hygiene is the only removal mechanism for floor-clamped — first batch imminent

Hygiene archival (importance<0.3, access=0, age>30d) is the only scheduled mechanism that will reduce the floor-clamped count. The first batch targets 2026-03-16T04:00 UTC (imminent — ~17.4h from Wave 29 measurement). Wave 30 should confirm whether the first batch fired. If it did, the floor-clamped count should begin a slow decline for the oldest members. However, the production rate of new floor-clamped memories (~941 current, growing daily from both system and consolidation sources) will outpace archival unless Q22.1 and Q24.5 are also fixed.

#### Observation 3: 179 importance mismatches (Qdrant vs Neo4j) require investigation

Q29.5 and Q29.7 both surfaced a new anomaly: 179 active memories have importance stored in Qdrant but Neo4j reports 0.0 for them. The reconcile endpoint detected these mismatches (`repairs_applied=0` — it does not auto-repair importance mismatches). Without audit logging (Q29.5 FAILURE), the trend direction is unknown. This is a candidate for Wave 30 investigation.

#### Observation 4: Five consecutive FAILURE waves — analytical work is complete, only deployment remains

Q29.4 (5th consecutive) and Q29.5 (5th consecutive) have both reached 5 consecutive FAILURE verdicts. Q29.2 (18th consecutive). Q29.6 is a new FAILURE. Combined fix burden: ~19 LOC across 4 files:
- Q22.1: `_user_conditions(None)` returns `[IsNullCondition(key="user_id")]` (~3 lines)
- Q24.5: `user_id=user_id,` in `Memory()` at `consolidation.py:248` (1 line)
- Q21.5: IS NULL filter in `get_distinct_user_ids()` at `qdrant.py:1143` (~5 lines)
- Q21.6: `log_audit()` after reconcile completion in `reconcile.py` + `ops.py` (~9 lines)

---

## 9. Wave 28 Results (Q28.1–Q28.7)

### Overview

Wave 28 is the **sixth consecutive fix-verification wave**. Of 7 questions: 3 FAILURE, 4 INCONCLUSIVE (all timing-blocked).

The defining result: **zero fixes deployed, seventeen consecutive waves of characterization with no remediation.** Wave 28 completes three actionable deployment checks (Q28.2, Q28.5, Q28.6) and documents four timing-blocked questions that cannot be answered until their respective observation windows open (Q28.1: 2026-03-16T04:00, Q28.3: depends on Q28.1, Q28.4: 2026-03-21T19:12, Q28.7: 2026-03-22).

**Audit schema correction (Q28.2)**: Prior wave queries (Waves 22–27) used `metadata.processed_count` to read decay processed counts — this field does not exist. The actual audit entry schema stores the processed count at `details.processed`. This correction does not change any verdicts; it clarifies why prior audit queries printed `?` for this field. Live data from Q28.2: two full-corpus decay_run entries per hourly slot, both showing `details.processed=6,002`.

**Three FAILURE threads at 4th consecutive strike**: Q28.5 (consolidation user_id, 4th consecutive) and Q28.6 (reconcile audit, 4th consecutive) have both reached 4 consecutive FAILURE verdicts. Q28.2 (double-decay) reaches 17 consecutive FAILUREs. The combined fix burden for Q28.5+Q28.6 is ~11 LOC across 3 files — these are the simplest outstanding fixes in the system.

---

### Wave 28 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q28.1 | INCONCLUSIVE | Info | Hygiene first-archival: auto_archive still 0 at 2026-03-15T10:15 UTC; target cron 2026-03-16T04:00 UTC ~18h away; 3rd consecutive INCONCLUSIVE measurement (Q26.1, Q27.1, Q28.1) |
| Q28.2 | FAILURE | High | Double-decay 17th consecutive; `_user_conditions(None)` returns [] unchanged; two full-corpus runs per slot (processed=6,002 each); audit schema corrected: `details.processed` not `metadata.processed_count` |
| Q28.3 | INCONCLUSIVE | Info | Archival count parity: Q28.1 prerequisite not met; Q27.7 analytical proof stands (both regimes archive same at 30d); empirical check pending |
| Q28.4 | INCONCLUSIVE | Info | GC-eligible cohort: 2026-03-21T19:12 UTC is 6 days away; 0 GC-eligible today; superseded pool 15,130 |
| Q28.5 | FAILURE | Medium | Consolidation user_id fix NOT deployed (4th consecutive); `consolidation.py:235` Memory() still missing `user_id=`; `qdrant.py:1143` IS NULL filter still absent |
| Q28.6 | FAILURE | Medium | Reconcile audit fix NOT deployed (4th consecutive); 0 `log_audit()` calls in reconcile.py/ops.py; reconcile sole remaining maintenance worker without observability |
| Q28.7 | INCONCLUSIVE | Info | Hygiene Week 13 (Mar 22-28, ~128/day): depends on Q28.1 data; target dates 7-13 days away |

---

### Wave 28 Cross-Domain Observations

#### Observation 1: Audit schema correction resolves prior wave query confusion

Q28.2 discovered that the decay_run audit entries store the processed count at `details.processed`, not `metadata.processed_count`. Prior wave queries (Q22.1 through Q27.3) used the wrong key path and received `?` for this field. The correction means all prior-wave processed count readings from decay audit entries were blind — the data was always there. This does not change any verdicts (the double-decay evidence was independently confirmed via code inspection at every wave), but it resolves a standing confusion about why audit queries returned empty metadata.

#### Observation 2: Four consecutive timing-blocked waves for hygiene first archival

Q28.1 is the third consecutive INCONCLUSIVE measurement for hygiene first archival (Q26.1, Q27.1, Q28.1 — all measured before 2026-03-16T04:00 UTC). This represents 3 consecutive waves in which the question could not be answered due to timing. Wave 29 should be the first wave able to confirm whether the first archival batch fired. If Q29 finds auto_archive still 0 despite the 2026-03-16T04:00 target window having passed, escalate immediately (hygiene cron may not be running or the 30-day age calculation is wrong).

#### Observation 3: GC and hygiene timelines are converging

Two major lifecycle events are approaching in quick succession: (1) First hygiene archival: 2026-03-16T04:00 UTC (~18h from Wave 28 measurement). (2) First GC-eligible cohort: 2026-03-21T19:12 UTC (~6 days from Wave 28 measurement). Wave 29 should confirm the first hygiene archival and begin monitoring the superseded pool for GC eligibility growth. After 2026-03-21, a new class of query becomes available: how many superseded memories cross the 30-day threshold each day, and at what rate will the 15,130 superseded pool drain under any future GC cron.

#### Observation 4: Three independent FAILURE threads at 4+ consecutive waves — no analytical work remains

Q28.2 (17 consecutive), Q28.5 (4 consecutive), Q28.6 (4 consecutive) are all independently characterized, verified, and have known fixes:
- Q22.1: add `IsNullCondition(key="user_id")` to `_user_conditions()` when `user_id is None` (~3 lines)
- Q24.5: add `user_id=user_id,` to `Memory()` constructor in `consolidation.py:235` (1 line)
- Q21.5: add IS NULL filter to `get_distinct_user_ids()` scroll in `qdrant.py:1143` (~5 lines)
- Q21.6: add `log_audit()` call after reconcile completion in `reconcile.py` and `ops.py` (~9 lines)

Total fix burden: ~18 LOC across 4 files. Zero analytical work remaining on any of these items.

---

## 10. Wave 27 Results (Q27.1–Q27.7)

### Overview

Wave 27 is the **fifth consecutive fix-verification wave**. Of 7 questions: 3 FAILURE, 3 WARNING, 1 INCONCLUSIVE.

The defining result: **zero fixes deployed, sixteen consecutive waves of characterization with no remediation.** Wave 27 delivers three corrections to prior estimates and quantifies the long-horizon damage from 16 waves of unmitigated double-decay.

**Hygiene first-archival timing corrected (Q27.1/Q27.7)**: Q27.1 found the hygiene system still at 0 auto_archive entries, measured ~17h before the expected first cron run. Q27.7's pipeline analysis corrects the first-batch date: the oldest active memories were created 2026-02-14T18:00 → eligible 2026-03-15T18:00 UTC → first cron run **2026-03-16T04:00 UTC** (tomorrow from measurement date). Only ~2 memories qualify for this first batch (the 25–27d cohort). The first significant batch is 2026-03-23 (~122 memories). Peak archival is Week 14 (March 29–April 4): ~1,550 archives = 221/day vs 187 new/day — the active corpus will temporarily shrink ~34/day during that peak week.

**GC-eligible estimate corrected again (Q27.2)**: Q26.6 corrected Q24.6's "~11,000 GC-eligible" claim (none were actually eligible; corpus started 2026-02-14). Q27.2 now corrects Q26.6's "first eligible cohort emerges 2026-03-16" claim. The export revealed the oldest consolidation-source active memory is dated 2026-02-19T19:12 (not 2026-02-14). Consolidation-superseded memories are the GC-eligible class; the first such memory won't cross the 30-day threshold until **2026-03-21T19:12 UTC**. This is the third consecutive correction to the GC eligibility estimate.

**Double-decay archival count parity (Q27.3/Q27.7)**: Q27.3 measured an inflation queue of 1,332 memories (>500 FAILURE threshold). However, Q27.7 discovered that this framing partially overstates the impact of double-decay on 30-day archival: both single and double decay bring any zero-access memory to the importance floor (0.05) within 10 days, well before the 30-day hygiene gate. The double-decay bug's actual damage is to **information quality in the 0–10 day window** (memories are "dead" for ~25 days instead of ~20 days before archival). The archival count at day 30 is unchanged regardless of decay regime. The 1,332-count inflation queue remains a FAILURE because 89.2% of 7–10d memories are below 0.3 — the damage is confirmed, but its mechanism is information quality loss, not count inflation.

---

### Wave 27 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q27.1 | INCONCLUSIVE | Info | Hygiene first-archival: 0 auto_archive entries (measured ~17h before first cron); re-verify target corrected to 2026-03-16T04:00 UTC (not 2026-03-17); hygiene instrumentation confirmed at `hygiene.py:49`; first significant batch: 2026-03-23 |
| Q27.2 | WARNING | Medium | 0 GC-eligible superseded memories today; Q26.6 estimate corrected (3rd time): oldest consolidation-source active memory = 2026-02-19T19:12; first GC-eligible date = **2026-03-21T19:12 UTC** (6 days); Q21.3 GC cron still unimplemented; superseded pool 15,130 stable |
| Q27.3 | FAILURE | High | Inflation queue 1,332 memories (7–29d, importance<0.3, access=0) > 500 FAILURE threshold; 89.2% of 7–10d cohort below 0.3; double-decay halves time-to-threshold (2.1d→1.1d) and time-to-floor (9.5d→4.7d); note: does NOT inflate 30d archival count (see Q27.7 correction) |
| Q27.4 | WARNING | Medium | Recovery debt: 673 floor-clamped total; Cat-C=432 permanently stuck (source=system, access=0, no recovery) within WARNING range (200–500); Cat-B=234 theoretical consolidation recovery; Cat-A=7 accessible; all 432 Cat-C archived within 23 days; deploying Q22.1 stops future accumulation but does not recover existing 673 |
| Q27.5 | FAILURE | Medium | Consolidation user_id fix NOT deployed (3rd consecutive); `consolidation.py:235` Memory() still missing `user_id=`; `qdrant.py:1143` IS NULL filter still absent; 1,833 active null-uid memories confirmed (Q26.5 baseline); ghost re-accumulation continues |
| Q27.6 | FAILURE | Medium | Reconcile audit fix NOT deployed (3rd consecutive); 0 `log_audit()` calls in reconcile.py/ops.py; 0 reconcile audit entries; `GET /admin/audit?action=auto_archive → count=0` confirms hygiene not yet fired (consistent with Q27.1) |
| Q27.7 | WARNING | Medium | Hygiene pipeline: 3,289 qualifying memories (54.8% of active corpus 6,005); peak Week 14 (Mar 29–Apr 4): 1,550 archives vs 187 new/day → **corpus shrinks ~34/day**; recovers after April 5; key correction: double-decay does NOT inflate 30d archival count; first batch: 2026-03-16T04:00 UTC (~2 memories) |

---

### Wave 27 Cross-Domain Observations

#### Observation 1: Three consecutive GC estimate corrections — stable characterization required

Q27.2 is the third correction in as many waves to the GC eligibility estimate: Q24.6 ("~11,000 eligible now"), Q26.6 ("0 eligible, first cohort 2026-03-16"), Q27.2 ("0 eligible, first cohort 2026-03-21"). Each correction reveals a different assumption flaw (total superseded ≠ GC-eligible; oldest active ≠ oldest consolidation-source active). The Q27.2 estimate should be verified on 2026-03-21 against actual GC-eligible count from the admin API before further projection.

#### Observation 2: Double-decay damage mechanism is confirmed but partially misframed

Q27.3 correctly identifies that double-decay is degrading the 7–10d cohort (89.2% below 0.3). Q27.7's correction adds precision: the damage is to **information quality and retrieval rank** during the 0–10 day window, not to 30-day archival count. The practical consequence is that memories become unsearchable ~5 days earlier under double-decay (floor at 4.7d vs 9.5d), reducing their effective useful life by approximately 2× before they become hygiene-eligible. This is still severe — it just means the impact is felt in retrieval quality stats rather than hygiene archival count statistics.

#### Observation 3: Hygiene pipeline peak will temporarily shrink the active corpus

Wave 14 (March 29–April 4) will be the first week in the system's history where daily archival exceeds daily new memories. With 221 archives/day vs 187 new/day, the active corpus (~6,005 as of Wave 27) will shrink by ~34/day net for approximately 7 days, losing ~238 total memories. This is an expected consequence of 30 days of zero-access accumulation, not a pathological event. Post-peak (April 5+), the corpus resumes normal growth. Wave 28 should monitor whether the actual peak matches the projection.

#### Observation 4: Two FAILURE threads at 3rd consecutive strike — escalation threshold reached

Q27.5 (consolidation user_id) and Q27.6 (reconcile audit) have both reached 3 consecutive FAILURE verdicts without deployment. The combined fix is ~11 LOC across 3 files (`consolidation.py:235`, `qdrant.py:1143`, `reconcile.py`/`ops.py`). These are the simplest outstanding fixes in the system. The 3-strike threshold should trigger explicit escalation documentation: these are not analytical gaps — the characterization is complete and verified three times over.

---

## 11. Wave 26 Results (Q26.1–Q26.7)

### Overview

Wave 26 is the **fourth consecutive fix-verification wave**. Of 7 questions: 3 FAILURE, 3 WARNING, 1 INCONCLUSIVE.

The defining result: **zero fixes deployed, fifteen consecutive waves of characterization with no remediation.** Wave 26 brings two landmark corrections and one confirmed asymmetry.

**Q24.6 GC-eligible estimate corrected (Q26.6)**: Q24.6 stated "~11,000+ memories are 30+ days old and eligible for GC." Q26.6 analysis reveals this was incorrect. The entire corpus started on 2026-02-14 (28 days ago as of Q26.6 measurement on 2026-03-15). No memory in the corpus can be 30+ days old. The first GC-eligible cohort will emerge on 2026-03-16. The Q24.6 estimate used the wrong baseline; the Q21.3 GC cron is still the correct recommendation, but the urgency timeline was overstated.

**Asymmetric observability gap (Q26.7)**: Direct code inspection confirms that reconcile (`reconcile.py`, `ops.py`) has zero `log_audit()` calls — making it the only scheduled maintenance worker with zero audit visibility. However, hygiene.py:49 has full `log_audit(action="auto_archive")` instrumentation with per-memory metadata. When the first hygiene archival fires on 2026-03-17, it will produce observable audit entries. The observability gap is now asymmetric: reconcile is invisible, hygiene will be visible.

**Double-decay compound damage growing (Q26.3)**: The floor-clamped cohort has grown to 673 (+41 since Q23.1 four days earlier, +6.5%). Total importance-units stolen from the active corpus = 179.5 across 5,975 memories. The daily accumulation rate (~10 new floor-clamped memories/day) is consistent with the ongoing double-decay at each 6-hour slot.

**Ghost re-accumulation trap quantified (Q26.5)**: 1,833 active consolidation-source memories have user_id=None (30.7% of active corpus). Deploying only the IS NULL filter (Q21.5) would eliminate current ghost users immediately, but re-accumulation would begin within weeks as these 1,833 memories get superseded through ongoing consolidation. The permanent fix requires co-deployment of Q21.5 and Q24.5 together.

---

### Wave 26 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q26.1 | INCONCLUSIVE | Info | Hygiene first-archival timing: measured 2 days before expected event (2026-03-17 04:00); 0 auto_archive audit entries (expected at this timing); hygiene audit instrumentation CONFIRMED at `hygiene.py:49` (action="auto_archive", per-memory metadata); re-verify on/after 2026-03-17 |
| Q26.2 | FAILURE | High | Double-decay fix not deployed (15th consecutive wave); `_user_conditions(None)` returns `[]` confirmed unchanged at `qdrant.py:114`; most recent slot Mar 15T06: 2 full-corpus runs at 06:45 and 06:49; first hygiene batch on 2026-03-17 will occur under double-decay conditions |
| Q26.3 | WARNING | Medium | Floor-clamped count 673 (+41 from Q23.1 baseline of 632, +6.5%); 179.5 importance-units stolen across 5,975 active memories; ~10 new floor-clamped memories/day; first hygiene batch NOT materially inflated by double-decay for 30d+ cohort (both models reach floor by 30d); 7-20d band disproportionately affected |
| Q26.4 | FAILURE | Medium | mark_superseded importance=0.0 fix NOT deployed (3rd consecutive FAILURE); `neo4j_store.py:391` unchanged; 124 mismatches on Sunday repair day (same-day re-accumulation, higher than 1-day post-repair baseline of 92); weekly cycle confirmed: 3rd empirical data point |
| Q26.5 | WARNING | Medium | Ghost re-accumulation trap: 1,833 active consolidation-source memories with user_id=None (30.7% of active corpus); IS NULL-only deployment gives temporary relief but re-accumulation within weeks; co-deployment of Q21.5 + Q24.5 required for permanent fix; neither fix currently deployed |
| Q26.6 | WARNING | Medium | Superseded pool 15,130 (+23 vs Q25.4 baseline); **Q24.6 GC-eligible estimate corrected**: 0 memories are actually 30+ days old (corpus started 2026-02-14); first GC-eligible cohort emerges 2026-03-16; reconcile scan 5.94s for 21,105 points (no degradation); Q21.3 GC cron still unimplemented |
| Q26.7 | FAILURE/NOTE | Medium | Reconcile audit fix NOT deployed (2nd consecutive); 0 `log_audit()` calls in reconcile.py or ops.py; 0 reconcile audit entries; **hygiene IS instrumented** at `hygiene.py:49` (action="auto_archive" per-memory); asymmetric observability: reconcile invisible, hygiene visible from 2026-03-17 |

---

### Wave 26 Cross-Domain Observations

#### Observation 1: Q24.6 GC-eligible estimate was wrong — first cohort emerges 2026-03-16

Wave 24's synthesis stated "~11,000+ consolidation-superseded memories are eligible for GC." This estimate was based on an incorrect assumption about corpus age. The corpus started on 2026-02-14, making the oldest memories 28 days old as of Q26.6 measurement. No memory has crossed the 30-day GC eligibility threshold yet. The first GC-eligible cohort (memories consolidated from Feb 14 originals) crosses the threshold on 2026-03-16. Wave 27 should verify whether the first GC-eligible batch is observable. The Q21.3 GC cron recommendation stands; its urgency timeline has been corrected but its necessity has not changed.

#### Observation 2: Reconcile is the sole audit blind spot among all scheduled workers

Q26.7's code inspection confirms an asymmetric observability pattern across Recall's four scheduled maintenance workers:
- **Decay**: has `decay_run` audit entries (one per run, per-user detail)
- **Consolidation**: has `supersede` audit entries (one per supersedure event)
- **Hygiene**: has `auto_archive` audit entries at `hygiene.py:49` (one per archived memory)
- **Reconcile**: zero audit entries; no `log_audit()` calls in either `reconcile.py` or `ops.py`

Reconcile is the sole blind spot. The Q21.6 fix (~9 LOC across 2 files) closes this gap and enables last-run-date querying, mismatch trend detection, and repair convergence monitoring.

#### Observation 3: Ghost fix deployment sequencing is critical

Q26.5 quantifies the ghost re-accumulation trap: 1,833 active merged memories with user_id=None will seed new ghost users as they get superseded. Deploying only the IS NULL filter (Q21.5) is a temporary fix that will require re-deployment within weeks. The co-deployment requirement (Q21.5 + Q24.5) means these two fixes are linked — neither alone is sufficient. This has not been clearly documented until Q26.5.

#### Observation 4: First hygiene archival is tomorrow — verify with audit log

The hygiene first archival is 1 day away (2026-03-17). Q26.7 confirms the audit infrastructure is ready (`hygiene.py:49` instrumentation confirmed). Wave 27's first question should be verification of the 2026-03-17 archival event: (a) how many memories were archived; (b) does the batch size match Q26.3's expectation; (c) were any memories archived that would have survived under single-decay (double-decay inflation check); (d) did the hygiene audit entries appear at `GET /admin/audit?action=auto_archive`.

---

## 12. Wave 25 Results (Q25.1–Q25.7)

### Overview

Wave 25 was the **third consecutive fix-verification wave**. Of 7 questions: 4 FAILURE, 1 WARNING, 2 HEALTHY.

The defining result: **zero fixes deployed, fourteen consecutive waves of characterization with no remediation.** Wave 25 brings two new time-critical developments that elevate urgency beyond prior waves.

**Hygiene first archival is imminent (Q25.5)**: The oldest active memory in the corpus was created 2026-02-14 (28 days old as of Q25.5 measurement). The daily 4am hygiene cron will first encounter memories that have crossed the 30-day age threshold on **2026-03-17**. This is the first activation of the hygiene system. Given the double-decay bug (Q25.1), the Feb 14 cohort has decayed approximately twice as fast as intended — a higher fraction will be below the importance<0.3 threshold than under single-decay assumptions. The first batch size may be substantially larger than expected.

**Purge endpoint scope clarified — GC gap remains fully open (Q25.4)**: The Q24.6 finding "admin purge endpoint available for manual GC" was partially misleading. Q25.4 confirms that `/admin/memory/purge` uses `scroll_all(include_superseded=False)` by default, which means the IS NULL filter is applied and all 15,099 consolidation-superseded memories are excluded from purge scope. The endpoint is correctly designed for cleaning up active low-quality memories (1,081 eligible) — it cannot touch the consolidation-superseded backlog. The Q24.6 GC gap (no DETACH DELETE mechanism for superseded memories) remains fully unaddressed.

**Sunday reconcile cycle confirmed (Q25.2)**: The 92 importance mismatch count in Q25.2 (measured ~1 day after the 2026-03-15 Sunday reconcile) exactly matches the Q24.2 baseline (measured ~1 day after the 2026-03-08 Sunday reconcile). This is the first direct measurement confirming the weekly mismatch cycle: ~92 new mismatches accumulate per day Mon–Sat, repaired in a single Sunday 05:30am cron pass, cycle repeats.

**ARQ anomaly closed (Q25.6)**: The Mar 15 timing anomaly noted in Q24.1 is now fully characterized. The Mar 15T00 single-run is a direct catch-up from the Q22.9 ARQ outage (one missed 00:15 slot → one catch-up run at restart). The Mar 15T06 4.3-minute gap between the two double-decay runs is post-restart queue settling. Neither event creates damage beyond the already-characterized 2× factor per slot. The Q22.1 model is complete.

---

### Wave 25 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q25.1 | FAILURE | High | Double-decay fix not deployed (14th consecutive wave); `_user_conditions(None)` returns `[]` confirmed; 21 of 22 observable 6h slots (Mar 10–Mar 15) show 2 full-corpus runs per slot; Mar 15T00 single run = Q22.9 ARQ catch-up (isolated, not a fix); active corpus 5,936 as of Mar 15T06 |
| Q25.2 | FAILURE | Medium | mark_superseded importance=0.0 fix not deployed; `neo4j_store.py:391` unchanged; 92 importance mismatches = exactly 1 day post-Sunday repair; mismatch cycle confirmed: ~92/day accumulation Mon–Sat, ~5,572 peak, repaired Sunday 05:30am |
| Q25.3 | FAILURE | Medium | Consolidation user_id attribution fix not deployed; `consolidation.py:235` Memory() constructor still lacks `user_id=`; cumulative ~22,288 attribution-less merged memories over 28 days (~796/day × 28d) |
| Q25.4 | WARNING | Medium | Purge endpoint uses `scroll_all(include_superseded=False)` by default — targets ACTIVE low-quality memories (1,081 eligible); consolidation-superseded memories (15,099) explicitly excluded by IS NULL filter; Q24.6 GC gap fully unaddressed by any available endpoint or scheduled cron; purge deletion logic is correct (Qdrant + Neo4j DETACH DELETE) but scoped to active-only |
| Q25.5 | HEALTHY | Info | **Time-sensitive**: 0 memories currently meet all hygiene criteria (age>30d binding); oldest active memory 2026-02-14 (28 days); first archival batch expected 2026-03-17 at 04:00; double-decay accelerates importance decay — first batch likely larger than single-decay baseline; hygiene criteria well-formed (access_count lte=0 confirmed) |
| Q25.6 | HEALTHY | Info | Mar 15 timing anomaly is isolated Q22.9 ARQ outage catch-up; 22 slots analyzed, 20/22 show canonical 11–13s double-decay gap; Q22.1 2× model is complete and accurate; no additional decay damage beyond 2× per slot |
| Q25.7 | FAILURE | Medium | Ghost-user compound FAILURE: neither Q21.5 IS NULL filter nor Q24.5 consolidation user_id fix deployed; `qdrant.py:1143-1162` unchanged; 7 proc=0 ghost entries per slot; ghost re-accumulation path open — ~796 new user_id=None merged memories/day seed next generation of ghost users |

---

### Wave 25 Cross-Domain Observations

#### Observation 1: Hygiene first archival is a time-sensitive verification event (2026-03-17)

The hygiene cron has been running for weeks but has never fired an archival event because no memories have crossed the 30-day age gate. That changes in 2 days. Wave 26 should confirm on 2026-03-17 that: (a) the hygiene cron fired and archived memories as expected; (b) the first batch size is consistent with expectations (and document the double-decay interaction — the batch may be 2× larger than under single-decay assumptions); (c) the hygiene soft-delete (archive, not DETACH DELETE) behaves correctly and does not touch consolidation-superseded memories.

#### Observation 2: Purge endpoint is not a GC mechanism for the known backlog

The Wave 24 synthesis recommended the admin purge endpoint for "manual cleanup" of the Q24.6 superseded memory backlog. Q25.4 corrects this: the purge endpoint cannot reach those memories. The 15,099 consolidation-superseded memories require a separate endpoint or cron that passes `scroll_all(include_superseded=True)` and filters by `superseded_by IS NOT NULL AND invalid_at < (now - 30d)`. Until such a mechanism is built (Tier 3 item #26), the backlog will grow. The residual risk table (§17) has been updated accordingly.

#### Observation 3: 14 consecutive FAILURE waves for double-decay — escalation required

The Tier 0 double-decay fix has been confirmed undeployed through 14 consecutive waves (Waves 11–25). Every 6-hour slot, the active corpus (5,936 memories as of Mar 15) decays twice. The fix is ~3 lines. There is no analytical work remaining. The framing of this as a "characterization loop" item must end — this is an operational emergency that requires direct escalation to the deploying party.

#### Observation 4: The weekly reconcile cycle is confirmed but does not prevent mismatch accumulation

Q25.2's matching mismatch count (92 = 1 day post-Sunday repair in both Q24.2 and Q25.2) provides the first direct empirical confirmation of the weekly mismatch cycle. The reconcile repair works correctly. But confirming the repair works is not an argument for deferring the Q21.1 fix — the repair is a cleanup loop, not a prevention mechanism. Each weekly cycle creates and discards ~5,572 mismatches unnecessarily.

---

## 13. Wave 24 Results (Q24.1–Q24.8)

### Overview

Wave 24 was a **fix-verification wave** — checking whether the Tier 0/1/1b fixes characterized across Waves 21–23 had been deployed. Of 8 questions: 5 FAILURE, 1 WARNING, 2 HEALTHY (with corrections).

The defining result of Wave 24: **zero fixes deployed, thirteen consecutive waves of characterization with no remediation.** The five FAILURE findings are all reconfirmations of previously characterized bugs with known one-to-three-line fixes. The two HEALTHY findings close a false alarm — Q23.4's "new High severity active-memory creation-path bug" was a temporal measurement artifact, not a standalone defect.

**The Q23.4 correction**: Wave 23 raised a "new High severity" risk item — 50 active memories with neo4j=0.0 from a creation-path bug. Q24.3 rules this out completely. All current importance mismatches (92 total) are from superseded memories via the mark_superseded path. `create_memory_node()` sets importance correctly. Q23.4's "50 active mismatches" were newly-created memories that happened to be in an active state during Q24.3's measurement window but were superseded within hours by the running consolidation process. Q24.4 further corrects Q23.4's scope-change assertion — the reconcile has always scanned the full corpus (include_superseded=True). The weekly repair cycle explains why mismatch counts stay bounded.

**The GC window (Q24.6)**: The 30-day eligibility threshold has been crossed. The hygiene cron runs daily but has archived zero memories and is explicitly designed to exclude superseded memories. An estimated 11,000+ consolidation-superseded memories are now eligible for true GC (DETACH DELETE) but no such cron exists. Note: the admin purge endpoint cannot address this backlog (Q25.4 clarification — it targets active memories only).

**Double-decay persistence (Q24.1)**: The Q22.1 fix has now been undeployed through 12 characterization waves. The 3-7d cohort median importance ratio (0.793) is statistically identical to the Q23.1 baseline measured 24 hours earlier — confirming there is no self-correction mechanism and every passing day deposits more memories at the 0.05 floor. The Mar 15 timing anomaly (now fully explained as ARQ catch-up by Q25.6) had no effect on the double-decay behavior.

---

### Wave 24 Findings Summary

| ID | Verdict | Severity | Key Finding |
|----|---------|---------|-------------|
| Q24.1 | FAILURE | High | Double-decay fix not deployed (12th consecutive wave); `_user_conditions(None)` returns `[]` confirmed; 15 observable 6-hour slots all show two full-corpus proc entries (proc≈active_corpus in both); 3-7d cohort ratio = 0.793 (Q23.1 parity — zero recovery); 632 memories floor-clamped; Mar 15 timing anomaly (00:01 single run, 06:45+06:49 4 min apart) now fully explained as ARQ catch-up by Q25.6 |
| Q24.2 | FAILURE | Medium | mark_superseded importance=0.0 fix not deployed; `neo4j_store.py:391` confirmed unchanged; 92 importance mismatches (all superseded); weekly Sunday 5:30am reconcile auto-repairs ~5,572 mismatches/week then accumulation resumes at ~796/day; mismatch cycle confirmed by Q25.2 |
| Q24.3 | HEALTHY | Info | Q23.4 "active-memory creation-path bug" RULED OUT; zero active memories have neo4j=0.0; all 92 importance mismatches are superseded memories from mark_superseded path; `create_memory_node()` explicitly sets `m.importance = $importance` (line 100); Q23.4's 50 "active" mismatches were temporal: newly-created memories that became superseded within hours; Wave 23 "High severity" risk item closed |
| Q24.4 | HEALTHY | Info | Reconcile scope is full-corpus (include_superseded=True) in both `reconcile.py:23` and `ops.py:262`; Q23.4 scope-change assertion was incorrect; `qdrant_total: 21,043` confirms all 21,043 points scanned; no "15,000+ superseded mismatch backlog" — weekly repair cycle handles accumulation; no action required |
| Q24.5 | FAILURE | Medium | Consolidation user_id attribution fix not deployed; `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; ~796 merged memories/day accumulate with user_id=None; users fully consolidated lose attribution permanently |
| Q24.6 | WARNING | Medium | GC window open; hygiene cron (daily 4am) running but 0 archived; hygiene is active-only soft-delete (`IS NULL on superseded_by`); no DETACH DELETE cron for consolidation-superseded memories; ~11,144 memories estimated 30+ days past consolidation date (eligible); 15,099 total superseded with no scheduled cleanup; **note: admin purge endpoint does NOT address this backlog (Q25.4)** |
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

## 14. Wave 23 Results (Q23.1–Q23.7)

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

## 15. Wave 22 Results (Q22.1–Q22.9)

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

## 16. Wave 21 Results (Q21.1–Q21.6)

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

## 17. Wave 20 Results (Q20.1–Q20.6)

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

## 18. Wave 19 Results (Q19.1–Q19.6)

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

## 19. Wave 18 Results (Q18.1–Q18.5)

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

## 20. Wave 17 Status (Q16.3a, Q16.4a — PENDING)

Wave 17 was planned as a post-deployment verification wave with two questions:

**Q16.3a** — Per-caller timeout post-deployment: after adding `timeout` parameter to `generate()`, does fact_extraction p99 semaphore hold drop below 60s?
*Status: PENDING — prerequisite (Q16.3 fix) not deployed. Cannot be answered until timeout parameter is deployed. Note: Q19.3 adds a qualifier — even after deployment, interactive callers can wait 89s in queue; Q16.3a should measure total latency (queue + inference), not inference alone.*

**Q16.4a** — Dedup drop volume post-instrumentation: after adding `recall_dedup_hits_total`, what fraction of daily stores are dedup-dropped, and does the API store path fire more often than observer?
*Status: PENDING — prerequisite (Q15.1/Q16.1 instrumentation) not deployed. Cannot be answered until dedup counters are deployed.*

These two questions remain the highest-priority measurement questions in the queue.

---

## 21. Wave 16 Results (Q16.1–Q16.5, Q16.3b, Q16.4b)

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

## 22. Waves 15 and 14 Results (archived from prior synthesis — condensed)

**Wave 15** (Q15.1–Q15.5): Dedup observability crisis confirmed — three independent code paths produce zero audit entries, zero log entries, no Prometheus counter. Global LLM timeout 180s applies to all callers; 43 confirmed >60s events; per-call override does not exist. Q15.4 ruled out length-based pre-filtering. Q15.5 identified newline-density guard as a practical fast-fail alternative for dense single-line content.

**Wave 14** (Q14.1–Q14.9, Q14.4a, Q14.4b): Store-time dedup confirmed as silent pure drop (no merge, no audit, no Neo4j edge). Global Semaphore(1) deployed but p95 unchanged — root cause is inference variance not contention. 4,000-char truncation confirmed practical. Cross-type session summary dedup confirmed as source of 3 false-positive merges.

---

## 23. Cross-Wave Patterns (Waves 1–36)

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

### Pattern 6: Remediation stall — fourteen consecutive waves find no improvements deployed (Waves 12–25)

In Waves 1–12, findings frequently referenced commits. Starting with Wave 13, the number of referenced commits drops to zero. Waves 13–24 have produced characterizations of failure clusters with no deployed remediation. The highest-value next action remains deployment, not continued investigation.

### Pattern 7: Reconcile observability gap — confirmed fixable (Q20.1, Q21.6) — Q24.8 reconfirms unfixed

The reconcile worker and admin API endpoint have zero audit_log entries. **Wave 21 (Q21.6)** confirms this is a 9-LOC fix. **Wave 24 (Q24.8)** reconfirms the fix is still not deployed. It is the same observability anti-pattern as the dedup subsystem (Q15.1, Q16.1): a critical repair operation runs regularly but its execution, results, and repair counts are invisible.

### Pattern 8: Superseded memory accumulation — cross-cutting concern, GC window open, no available cleanup tool (Q20.4 secondary, Q21.3, Q21.5, Q24.6, Q25.4)

The 72% superseded ratio (Q20.4 secondary) has downstream effects across three subsystems confirmed by Wave 21: GC unavailability (Q21.3), decay ghost users (Q21.5), and reconcile scan overhead (Q20.2). All three trace to the same root — no deletion mechanism exists for old superseded points. A single GC cron (Q21.3 specification: age ≥30d + successor active + simultaneous Neo4j DELETE) would address all three simultaneously. **Wave 24 (Q24.6) confirms the 30-day eligibility window is open**: ~11,000 memories are eligible for true GC but no scheduled cron exists. **Wave 25 (Q25.4) further clarifies: the admin purge endpoint CANNOT address the superseded memory backlog.** The purge endpoint uses `scroll_all(include_superseded=False)` by default, which explicitly excludes all superseded memories. There is currently no endpoint, tool, or cron that can clean up consolidation-superseded memories in bulk. A new endpoint or cron that passes `scroll_all(include_superseded=True)` and filters by `superseded_by IS NOT NULL AND invalid_at < (now - 30d)` is required before any GC can be performed.

### Pattern 9: Double-decay — fourteen consecutive failure confirmations, zero remediation (Q22.1, Q23.2, Q24.1, Q25.1)

The double-decay bug was first confirmed as a FAILURE in Wave 22. It has been reconfirmed in every subsequent wave (Waves 23, 24, and 25). Q25.1 provides the most comprehensive audit to date: 21 of 22 observable 6-hour slots from 2026-03-10 through 2026-03-15 show two full-corpus runs per slot. The Q22.9 ARQ catch-up anomaly (Mar 15T00) is now fully characterized by Q25.6 as an isolated event that does not resolve the double-decay. The fix is ~3 lines. The active corpus stands at 5,936 memories as of Mar 15T06, all decaying at 2× the intended rate every 6 hours.

### Pattern 10: Hygiene system first activation — time-sensitive event (Q25.5)

The hygiene archival cron has been running daily at 4am with zero output for the lifetime of the system. On 2026-03-17, the Feb 14 cohort (the oldest active memories) will cross the 30-day age threshold and become eligible for hygiene archival. This is the system's first real-world hygiene test. The double-decay interaction is the key uncertainty: memories in the Feb 14 cohort have decayed approximately twice as fast as intended and will likely arrive at the 30-day threshold with lower importance values than expected under single-decay — meaning a higher fraction will be both old enough AND below the importance<0.3 threshold. Wave 26 must verify this activation event.

---

## 24. Prioritized Remediation Roadmap (Current State, post Wave 36)

Based on severity, feasibility, and number of waves confirming the gap. Items marked with `[N waves]` have been confirmed across multiple investigation cycles without remediation. **Wave 25 updates are bolded.**

### Tier 0 — Emergency hotfix (< 1 day, 3 lines)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 0 | **Fix double-decay — ROOT CAUSE IDENTIFIED (Q33.2b)**: `get_distinct_user_ids()` returns `[0]` (integer zero passes `is not None`), causing per-user loop to run `worker.run(user_id=0)` → IsNullCondition → decays 5,043 null memories. Then explicit system pass runs `worker.run(user_id=0)` again → same 5,043 decayed twice. **Two-line fix**: (1) `qdrant.py:1207`: `if uid is not None:` → `if uid is not None and uid > 0:` (excludes sentinel 0 from per-user loop); (2) `decay.py:296`: remove redundant `stats = await worker.run(user_id=0)` system pass. **24 consecutive FAILURE waves** (Q22.1 through Q33.2c). Three-way population split confirmed: 5,043 null double-decayed, 975 integer-0 never decayed, 0 user_id=1+. Optional third fix: add `FieldCondition(match=0)` to catch the 975 integer-0 memories currently skipped. | **2 lines (qdrant.py + decay.py)** | **Q22.1, Q23.2, Q24.1, Q25.1, Q32.2, Q33.2b, Q33.2c** | **Stops double-decay immediately; 5,043 null memories decay once per cycle instead of twice; 975 integer-0 memories remain un-decayed until optional third fix; importance values begin recovering toward intended baseline; hygiene batch size no longer inflated by double-decay** |

### Tier 1 — Stop the bleeding (1-3 days, high confidence, 3-10 lines each)

| # | Action | Effort | Resolves | Expected Impact | Waves confirming |
|---|--------|--------|----------|-----------------|-----------------|
| 1 | ~~**Add `timeout` parameter to `generate()`**~~ **CLOSED by Q31.7 + Q32.6**: 17/17 callsites have explicit `timeout=` matching tier spec. 180s semaphore-hold risk eliminated. Q32.6 confirms zero llm_error/llm_timeout audit entries; max theoretical hold = 90s (heavy tier, intentional). | ~~~5 lines~~ DEPLOYED | Q15.3, Q16.3 | **RESOLVED** — closes Q15.3/Q16.3 permanently | Q31.7 (re-run), Q32.6 |
| 2 | **Truncate inputs at 4,000 chars** in fact_extractor.py | ~5 lines | Q14.4b | Eliminates 37–93s p99 semaphore holds from long inputs; estimated p95 drop from ~15s to ~9s | 1 wave (uncontested) |
| 3 | **Add dedup counters at all four drop sites**: `metrics.increment("recall_dedup_hits_total", {"source": site})` | ~4 lines across 3 files | Q15.1, Q16.1 | Closes measurement gap; hit rate visible within first minute of deployment; enables Q16.4a measurement | 2 waves |
| 4 | **Add logger.info call** to observer.py before `continue` at line 176 | 1 line | Q15.2, Q16.2 | Makes observer dedup drops visible in Docker logs | 2 waves |

### Tier 1b — Critical additions from Waves 19–22 (1-2 days)

| # | Action | Effort | Resolves | Expected Impact |
|---|--------|--------|----------|-----------------|
| 5 | **Wrap consolidation source-supersedure loop** (consolidation.py:272–283) in per-source try/except with logger.error on failure; implement `qdrant.unmark_superseded()` as compensating rollback when Neo4j fails after Qdrant succeeds — **Q21.4 confirms: 4 lines qdrant.py** | ~30 lines consolidation.py + **4 lines qdrant_store.py** (confirmed by Q21.4) | Q19.6 | Prevents Qdrant/Neo4j split-brain; compensating rollback confirmed atomic and zero-regression |
| 6 | **Remove `m.importance = 0.0` from neo4j.mark_superseded** (neo4j_store.py:391) — **Q21.1 confirms: 1 line deletion, zero functional regressions; Q24.2 reconfirms fix not deployed** | **1 line** | Q20.5, Q24.2 | Stops new importance mismatches from being created; compound failures converge in one reconcile pass; eliminates weekly ~5,572-mismatch accumulation cycle |
| 7 | ~~**Add reconcile audit_log entries**~~ **CLOSED by Q31.4**: `log_audit(action="reconcile")` IS deployed in both `ops.py:373-377` and `workers/reconcile.py:112-116`. 7 prior FAILURE waves were false negatives caused by querying wrong action name (`reconcile_run` vs `reconcile`). Q32.4 HEALTHY confirms reconcile cron is registered and functional. | ~~9 LOC~~ DEPLOYED | Q20.1, Q24.8 | **RESOLVED** — reconcile execution visible in audit trail under `action="reconcile"` |

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

## 25. Open Threads for Wave 37+

**Current state (post Wave 36, 2026-03-16)**: The amnesty crisis was resolved. Fix-1 (qdrant.py uid>0 guard) remains the single blocking code change. Reconcile auto-repair is the highest-urgency operational change.

### Time-sensitive priorities for Wave 37+

**CRITICAL — Deploy Fix-1 before 2026-03-21**: Without `if uid is not None and uid > 0:` in `qdrant.py:1207`, the amnesty benefit (4,173 rescued memories) will decay back to floor by ~2026-03-21 under double-decay. If Fix-1 cannot be deployed before 2026-03-21, run a second amnesty (`POST /admin/importance/amnesty?dry_run=false`) to intercept the wave of decaying memories.

**URGENT — Enable reconcile auto-repair**: Change reconcile scheduler from scan-only to `repair=true` on every run. Q33.5 confirmed ~41/hour mismatch accumulation — without this change, weekly reconcile window will see ~6,888 mismatches, covering the entire active pool.

**Q29.1-followup — Hygiene first archival verification (RUN ON OR AFTER 2026-03-17T04:00 UTC)**:
Q33.1 confirmed hygiene cron fired at 2026-03-16T04:00 UTC with 0 candidates (correct — date boundary). First real archival expected 2026-03-17T04:00 UTC when Feb 14 cohort crosses 30-day cutoff.
(a) Check `GET /admin/audit?action=hygiene_run&limit=10` after 2026-03-17T04:00 UTC.
(b) Report: `details.archived` count vs Q27.7 projection (~2 memories first batch).
(c) If archived > 0: hygiene pipeline confirmed end-to-end operational.
*Run on or after 2026-03-17T04:00 UTC.*

**Q28.4-followup — First GC-eligible cohort at 2026-03-21 (RUN ON OR AFTER 2026-03-21T19:12 UTC)**:
Q33.6 projects ~19,610 superseded memories at GC eligibility — manageable first batch. Q27.2 established: first GC-eligible date = **2026-03-21T19:12 UTC**. GC infrastructure must be confirmed operational before this window. Verify: (a) how many superseded memories have `invalid_at < (now-30d) AND superseded_by IS NOT NULL`; (b) whether any automated GC mechanism exists; (c) actual pool size vs ~19,610 projection.
*Run on or after 2026-03-21T19:12 UTC.*

**Q28.3-followup — Double-decay archival count parity verification (RUN AFTER Q28.1-followup)**:
Q28.3 was INCONCLUSIVE pending Q28.1. After Q28.1-followup confirms first batch data, verify: (a) actual first batch count vs Q27.7 Week 12 projection (18 total); (b) age distribution — any memories < 20d old in batch (would indicate floor-clamped early archival); (c) importance distribution — all near 0.05 floor? This confirms or refutes Q27.7 archival count parity assertion.
*Prerequisite: Q28.1-followup confirms hygiene cron fired.*

**Q28.7-followup — Hygiene Week 13 batch rate verification (RUN 2026-03-22 to 2026-03-28)**:
Q28.7 was INCONCLUSIVE pending Q28.1 and Week 13 dates. Q27.7 projected ~128 archives/day (898 total) for Week 13. Monitor daily archival rate and compare to projection. Key validation: does actual rate match projection within 25% (100–160/day)?
*Run starting 2026-03-22 (after Q28.1-followup confirms hygiene operational).*

### Post-deployment re-measurements (activate only after Tier 1/1b deploy)

**Q16.3a — Per-caller timeout impact**: After deploying timeout parameter to generate(), does fact_extraction p99 drop below 60,000ms? Does total interactive latency drop, or does queue wait dominate?
*Prerequisite: Q16.3 fix deployed. Note: Q19.3 finding — measure queue wait phase separately from inference phase.*

**Q16.4a — Dedup hit rate baseline**: After deploying recall_dedup_hits_total counters, what is the 24h baseline hit rate per source?
*Prerequisite: Q15.1/Q16.1 instrumentation deployed.*

**Q25.1-post — Double-decay post-fix verification**: After deploying Q22.1 fix (IS NULL filter in _user_conditions or system-run filter), verify: (a) each 6-hour slot shows exactly ONE full-corpus proc entry (system run) plus per-user entries; (b) 3-7d cohort ratio begins recovering above 0.793 baseline; (c) floor-clamped memory count begins decreasing from 673 (Q26.3 baseline).
*Prerequisite: Q22.1 fix deployed.*

**Q25.2-post — mark_superseded mismatch rate post-fix**: After removing `m.importance = 0.0` from `neo4j_store.py:391`, verify: (a) reconcile dry_run shows 0 new mismatches accumulating after the weekly repair; (b) importance_mismatches count stabilizes and does not grow between Sunday repairs.
*Prerequisite: Q21.1 fix deployed.*

**Q25.3-post — Consolidation user_id attribution propagation**: After fixing `consolidation.py:235` to pass `user_id` to merged Memory constructor, verify: (a) new merged memories have user_id set; (b) users with recently consolidated originals reappear in get_distinct_user_ids().
*Prerequisite: consolidation user_id fix deployed.*

**Q26.5-post — Ghost fix co-deployment verification**: After co-deploying Q21.5 (IS NULL filter) AND Q24.5 (consolidation user_id= propagation), verify: (a) get_distinct_user_ids() returns only user_ids with active memories; (b) no proc=0 ghost entries in next 24h of decay audit; (c) new merged memories have user_id set (Q26.5 seed pool stops growing).
*Prerequisite: BOTH Q21.5 and Q24.5 deployed together.*

### Low-priority analytical questions (proceed only if deployment gating is impractical)

**GC mechanism build — build new superseded GC endpoint**: Q25.4 confirmed the admin purge endpoint does NOT target superseded memories. Q26.6 corrected Q24.6's eligibility estimate — the first GC-eligible cohort emerges 2026-03-16. To address the backlog, a new endpoint or cron is required that calls `scroll_all(include_superseded=True)` and filters for `superseded_by IS NOT NULL AND invalid_at < (now - 30d)`. Before building, verify: (a) successor memories are still active (Q21.3 safety criterion); (b) DETACH DELETE runs atomically in both Qdrant and Neo4j. A dry_run mode is strongly recommended.
*No prerequisite. Can scope and implement independently of other fixes.*

---

## 26. Residual Risk Inventory (Current State, post Wave 36)

| Risk | Severity | Likelihood | Trigger | Status |
|------|---------|-----------|---------|--------|
| **Double-decay: ROOT CAUSE IDENTIFIED (Q33.2b) — `get_distinct_user_ids()` returns `[0]`, causing per-user loop + explicit system pass to both decay 5,043 null memories; 975 integer-0 memories never decayed; 1,049 floor-clamped; 24th consecutive FAILURE** | **CRITICAL** | **Certain (every cron slot)** | **Every 6-hour decay run** | **OPEN — Q22.1 through Q33.2c (24 consecutive FAILURE waves); Q33.2b ROOT CAUSE: three-way population split (5,043 null double-decayed, 975 int-0 never decayed, 0 user_id=1+); fix is 2 lines: (1) qdrant.py:1207 add `and uid > 0`; (2) decay.py:296 remove redundant system pass; Q33.2a refuted two-replica hypothesis; Q33.7 HEALTHY: Feb 14 cohort intact (0 floor-clamped at 30d+); damage concentrated in 7–21d mid-life; compound damage with Q24.5 confirmed** |
| Dedup hit rate completely unquantifiable — unknown volume of unique facts permanently dropped | High | Active (31,289+ creates processed without measurement) | Every store event that triggers dedup path | OPEN — 4 waves unresolved (Q15.1, Q16.1); real-time rate unmeasurable; Q20.4 confirms threshold is correct but real-time rate still unknown |
| ~~Global LLM timeout 180s~~ | ~~High~~ | ~~Active~~ | ~~Any consolidation or fact_extraction call~~ | **CLOSED by Q31.7 + Q32.6** — 17/17 callsites have explicit timeout= tiers; 180s hold eliminated; max theoretical hold = 90s (intentional); zero llm_error/llm_timeout in audit |
| Store-time dedup silent drop — unique facts in incoming write permanently lost with no audit trail | High | Active (every dedup event) | Any store that scores >0.92 against existing memory | OPEN — Q14.3 FAILURE; audit entry not deployed |
| Dedup observability matrix: 10/12 cells empty; memory.py and observer.py have zero coverage | High | Active (every dedup event) | Any dedup drop at API or observer path | OPEN — Q16.4 FAILURE |
| LLM p95 > 10s — Semaphore(1) + inference variance dominates; interactive callers can wait 89s in queue | High | Active (p95=11–17s post-semaphore; queue wait unbounded) | Any mix of long-inference (consolidation) + short (signal_detection) calls | OPEN — Q14.4 FAILURE; Q19.3 WARNING adds queue-wait gap; per-caller timeouts insufficient alone |
| Retrieval coverage structural failure — K=3 fixed vs. growing corpus; 9.5% lifetime coverage | High | Certain (coverage degrades with corpus growth) | Each new memory stored | OPEN — Q13.1, Q14.7; exploration injection from Q14.2 not deployed; note: active corpus only 5,945 (Q24.3) |
| Consolidation split-brain: Neo4j failure after Qdrant mark_superseded = divergence up to 7 days | High | Unknown (consolidation runs regularly; Neo4j transient errors possible) | Any Neo4j transient error during consolidation source-supersedure loop | OPEN — Q19.6 FAILURE; Q20.1 bounds impact (0 superseded_mismatches currently; weekly reconcile repairing); **Q21.4 confirms compensating rollback is 4 lines qdrant.py** |
| **Reconcile convergence defect: compound failures require two passes; mark_superseded overwrites Step A importance fix** | **High** | **Latent (9 entries produced historically; 0 active after Q21.2 repair)** | **Q18.1 partial gather + Q19.6 split-brain co-occurring on same memory** | **OPEN — Q20.5 FAILURE; Q21.1 collapses fix to 1-line removal of importance=0.0 from neo4j_store.py; Q24.2 confirms fix not deployed** |
| **mark_superseded importance=0.0: ~92 mismatches/day accumulating; ~5,572 accumulate weekly before Sunday repair; weekly cycle confirmed by Q25.2 and Q26.4 (3rd data point)** | **Medium** | **Certain (every consolidation event creates 1 mismatch)** | **Every consolidation supersedure** | **OPEN — Q21.1 root cause confirmed; Q24.2, Q25.2, Q26.4 confirm fix not deployed (3rd consecutive wave); weekly mismatch cycle confirmed: 3 empirical measurements; Q26.4: 124 mismatches on Sunday repair day itself (same-day re-accumulation); retrieval unaffected (find_related filters superseded)** |
| ~~**Reconcile audit invisibility**~~ | ~~Medium~~ | ~~Certain~~ | ~~Every reconcile run~~ | **CLOSED by Q31.4 + Q32.4** — `log_audit(action="reconcile")` IS deployed in both ops.py and workers/reconcile.py; 7 prior FAILURE verdicts were false negatives (wrong action name `reconcile_run` vs `reconcile`); Q32.4 confirms reconcile cron registered and functional; stores in sync (21,373/21,373) |
| 1,315 importance mismatches (6.3% corpus): Qdrant/Neo4j drift from _track_access and compound failures | Medium | Active (Q21.2 resolved to 0 after repair; will re-accumulate) | Every _track_access exception (Q18.2) and every compound failure (Q20.5) | OPERATIONALLY BOUNDED — Q21.2 confirms repair=true converges in single pass; weekly reconcile resolves 1,313 mismatches automatically; residual 2 sub-pattern-A resolved by manual repair=true |
| except:pass in importance-inheritance block — Qdrant errors silently swallowed; promotions unconfirmed | Medium | Unknown (never logged) | Any Qdrant error during dedup drop at API path | OPEN — Q16.4b FAILURE; Q19.4 provides indirect evidence this is materializing |
| decay.py gather partial write — batch abort leaves partial Qdrant writes untracked; audit log skipped | Medium | Unknown (depends on decay_user_error frequency) | Any Qdrant error during decay batch execution | OPEN — Q18.1 WARNING; Q19.1 confirms scope is bounded to decay.py only |
| retrieval.py _track_access loop early exit — N+1 memories in retrieval batch miss access reinforcement | Medium | Unknown (depends on _track_access exception frequency) | Any storage error during retrieval stat update | OPEN — Q18.2 WARNING; Q19.2 confirms scope is bounded to _track_access only |
| Importance corpus contamination: Q16.4b + Q18.2 prevent importance promotion; 1,315 importance mismatches accumulating | Medium | Active (6.3% of corpus, measurable drift; resolves weekly) | Any dedup event (Q16.4b) or retrieval event (Q18.2) where write fails silently | OPEN — Q20.1 WARNING; re-accumulates between weekly reconcile runs |
| **Superseded memory storage bloat: ~15,130 superseded Qdrant points; ~796 new/day; no scheduled GC; first GC-eligible cohort emerges 2026-03-21T19:12 UTC; NO AVAILABLE MANUAL TOOL** | **Medium** | **Certain (grows with every consolidation)** | **Every consolidation event creates superseded points that are never scheduled for deletion** | **OPEN — Q21.3 WARNING; Q28.4 INCONCLUSIVE (target date 2026-03-21T19:12 UTC is 6 days from Wave 28 measurement); Q25.4 WARNING confirms admin purge endpoint CANNOT target superseded memories; no endpoint or cron exists for bulk superseded GC; re-verify on/after 2026-03-21T19:12 UTC** |
| **Ghost users in decay: 7/10 decay_run entries/slot processed=0; overdecay ~4%/run for primary user; ghost re-accumulation path open** | **Medium** | **Certain (70% of user_id list are phantoms; grows with superseded accumulation)** | **Every cron slot; every decay run for primary user** | **OPEN — Q21.5 WARNING; Q22.2 confirms ghost identity; Q24.7, Q25.7 confirm both fixes not deployed; Q26.5 quantifies seed pool: 1,833 active consolidation-source memories with user_id=None; IS NULL-only deployment gives temporary relief but re-accumulation within weeks; co-deployment of Q21.5 + Q24.5 required for permanent fix** |
| **Consolidation user_id attribution loss: merged memories get user_id=None; consolidation-source floor-clamped 7→375 (+368) as of Wave 29 — compound effect with double-decay confirmed; user vanishes from get_distinct_user_ids() when all originals superseded** | **Medium** | **Certain (runs hourly; every system consolidation event)** | **Every consolidation of named-user memories by system run** | **OPEN — Q22.9 WARNING; Q24.5, Q25.3, Q27.5, Q28.5, Q30.4 FAILURE (fix not deployed, 6th consecutive wave); Q30.6 WARNING: floor-clamped 941 stable (same-day measurement); directly attributable to this bug; consolidation.py:235 user_id= and qdrant.py:1143 IS NULL filter confirmed absent** |
| **Hygiene cron has NEVER fired: 0 hygiene_run entries in 379,666 total audit records; 9 consecutive miss confirmations (Q26.1 through Q32.1); scheduler has never executed a hygiene job since system stood up on Feb 14; not a recent regression — standing defect** | **Critical** | **Certain (cron never fires)** | **Daily hygiene cron has never produced a single audit entry** | **OPEN — Q32.1 FAILURE (9th consecutive); 0 hygiene_run, 0 archive, 0 decay_check entries in entire audit history; only decay and reconcile crons are operational; hygiene cron task is either not registered, not in cron_jobs, or silently failing at startup; 1,049 floor-clamped memories accumulating with no drain** |
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

## 27. Waves 1�12 Baseline (summary, not modified)

Waves 1–12 produced 35 HEALTHY findings and 5 committed fixes covering: p99 search latency well under threshold at 40 concurrent users (Q1.1–Q1.4); domain isolation correct under concurrent writes (Q2.1); graph traversal guarded against cycles (Q3.4); all 4 background workers with structured exception logging (Q5.3); asyncio.Lock added to all async-mutated module-level state (Q7.1, e73858f); Pydantic v2 migration complete (Q7.2, 033ede9); datetime.utcnow() sweep complete across 23 files (Q6.7, 9cec9f4); all 4 worker test suites written and passing (Q5.7, Q7.6); embed_batch per-item fallback confirmed observable (Q6.1, 26da1aa); stdlib/structlog mismatch eliminated across all 77 src/ files (Q7.4). These findings remain confirmed holding.

**Key pre-condition**: The Waves 1–12 work addressed code quality and unit-test coverage. Wave 13 established that this well-built code is failing at its primary job — surfacing the right memories at the right time. Waves 14–25 have added numerous FAILURE/WARNING findings to the runtime behavior and documented a remediation stall pattern that has now run for fourteen consecutive waves.

**Post-Wave 36 status update**: The Wave 34 hard deadline (16.6-day window for 644 premature casualties) was resolved by the amnesty live run on 2026-03-15T15:42 UTC (Q36.1: 4,173 memories rescued). Three code fixes are now partially deployed:
- Step 0 (bulk re-score): **DONE** — amnesty rescued 4,173/5,211 floor-clamped; rehabilitate endpoint needs one-char fix (`>= 0.05` → `> 0.05`) before reuse
- Step 1 (double-decay Fix-1): **Fix-2 deployed; Fix-1 NOT deployed** — `qdrant.py:1207` still `if uid is not None:`; double-decay continues
- Step 2 (consolidation user_id): **DEPLOYED**
- Step 3 (hygiene cron): **CONFIRMED REGISTERED AND FIRING** — first archival 2026-03-17T04:00 UTC

**Remaining critical path (as of 2026-03-16):**
1. Deploy Fix-1 (`qdrant.py:1207`: `uid > 0` guard) + `docker compose restart recall-worker` — prevents amnesty benefit from decaying away by ~2026-03-21
2. Change reconcile scheduler to `repair=true` — stops ~41/hour mismatch accumulation (Q33.5 FAILURE)
3. Fix rehabilitate endpoint off-by-one (`>= 0.05` → `> 0.05`)
4. Run second amnesty before 2026-03-21 if Fix-1 not deployed



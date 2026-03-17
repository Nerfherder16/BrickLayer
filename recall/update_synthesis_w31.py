content = open(
    "C:/Users/trg16/Dev/autosearch/recall/findings/synthesis.md", "r", encoding="utf-8"
).read()

# 1. Update header line
content = content.replace(
    "# Synthesis: Recall Autoresearch — Waves 1–30",
    "# Synthesis: Recall Autoresearch — Waves 1–31",
)

# 2. Update generated line
content = content.replace(
    "**Generated**: 2026-03-15 (updated with Wave 29 findings)",
    "**Generated**: 2026-03-15 (updated with Wave 31 findings)",
)

# 3. Update questions answered list and count
content = content.replace(
    "Q27.1–Q27.7, Q28.1–Q28.7, Q29.1–Q29.7, Q30.1–Q30.7)",
    "Q27.1–Q27.7, Q28.1–Q28.7, Q29.1–Q29.7, Q30.1–Q30.7, Q31.1–Q31.7)",
)
content = content.replace(
    "**Questions answered**: 176 ", "**Questions answered**: 183 "
)

# 4. Add Wave 31 signal block in executive summary
old_exec = (
    "Wave 30 produces 3 FAILURE, 2 WARNING, 2 INCONCLUSIVE.\n\n**Overall health signal:"
)
new_exec = (
    "Wave 30 produces 3 FAILURE, 2 WARNING, 2 INCONCLUSIVE.\n\n"
    "**Wave 31 key findings**:\n"
    "- Q23.6: WARNING — Per-supersedure audit logging exists (consolidation.py:299-305); 1000+ entries; user_id always null (Q24.5 propagation); 26/1000 duplicate memory_ids from Q22.1 double-processing\n"
    "- Q27.1: INCONCLUSIVE — Hygiene archival timing-blocked; 1d 14h before 2026-03-17T04:00 UTC; auto_archive=0\n"
    "- Q31.1: FAILURE (7th+ consecutive) — hygiene_run=0; archive=0; 2026-03-15T04:00 UTC window passed with no entries; cron broken since 2026-03-09\n"
    "- Q31.2: FAILURE (20th consecutive) — double-decay fix not deployed; system pass processed=5,994/6,048 (99.1%); fix would halve to ~3,024\n"
    "- Q31.3: FAILURE — floor-clamped 1,049/6,048 (17.3%); +108 from Q30.6 baseline 941 in ~3 hours; consolidation +74; all fixes undeployed\n"
    "- Q31.4: FAILURE (7th consecutive) — reconcile_run=0 after manual trigger; fix not deployed\n"
    "- Q31.5: FAILURE — importance_mismatches grew 179→264 (+85, +47%); mark_superseded fix undeployed; ~28/hour new mismatch rate\n"
    "- Q31.6: INCONCLUSIVE — GC eligibility 6d 5h away (2026-03-21T19:12 UTC); gc_run=0; superseded pool ~15,275 (+91 from Q30.7)\n"
    "- Q31.7: FAILURE — LLM timeout tiers not deployed; 15/18 generate() callsites missing timeout=; 83.3% unprotected against 180s hangs\n\n"
    "Wave 31 produces 6 FAILURE, 1 WARNING, 2 INCONCLUSIVE.\n\n"
    "**Overall health signal:"
)
content = content.replace(old_exec, new_exec)

# 5. Update overall health signal
content = content.replace(
    "CRITICAL — 19 CONSECUTIVE CHARACTERIZATION WAVES WITH ZERO FIXES DEPLOYED. DOUBLE-DECAY HAS BEEN ACTIVE FOR 19 WAVES WITHOUT REMEDIATION. THREE ACTIVE FAILURE THREADS: Q22.1 DOUBLE-DECAY (19th), Q24.5+Q21.5 CONSOLIDATION (6th), Q21.6 RECONCILE AUDIT (6th). FLOOR-CLAMPED 941 STABLE (WARNING — same-day measurement). HYGIENE FIRST ARCHIVAL TARGET 2026-03-16T04:00 UTC: WAVE 31 IS MANDATORY FAILURE ESCALATION. GC ELIGIBILITY BEGINS: 2026-03-21T19:12 UTC (~6 DAYS). DEPLOYMENT IS THE ONLY REMAINING ACTION.**",
    "CRITICAL — 20 CONSECUTIVE CHARACTERIZATION WAVES WITH ZERO FIXES DEPLOYED. DOUBLE-DECAY ACTIVE FOR 20 WAVES. FOUR ACTIVE FAILURE THREADS: Q22.1 DOUBLE-DECAY (20th), Q24.5 CONSOLIDATION (7th), Q21.6 RECONCILE AUDIT (7th), Q31.7 LLM TIMEOUT (1st). FLOOR-CLAMPED 1,049 (FAILURE — +108 IN 3 HOURS). HYGIENE CRON BROKEN (7th miss). IMPORTANCE MISMATCHES 264 (+47%). GC ELIGIBILITY: 2026-03-21T19:12 UTC (~6 DAYS). DEPLOYMENT IS THE ONLY REMAINING ACTION.**",
)

# 6. Update Section 2 heading
content = content.replace(
    "## 2. Cumulative Findings by Verdict Tier (Waves 1–30)",
    "## 2. Cumulative Findings by Verdict Tier (Waves 1–31)",
)

# 7. Update double-decay FAILURE row
content = content.replace(
    "| **Q23.2 / Q24.1 / Q25.1 / Q26.2 / Q27.3 / Q28.2 / Q29.2** | **Double-decay FAILURE RECONFIRMED (19th consecutive wave): Q22.1 fix not deployed; `_user_conditions(None)` confirmed unchanged at `qdrant.py:114`; two full-corpus decay_run entries per slot confirmed (processed=6,002 each, Waves 28/29/30); audit schema: field is `details.processed`; active corpus 6,044 as of Wave 30** | **High** | **23/24/25/26/27/28/29/30** |",
    "| **Q23.2 / Q24.1 / Q25.1 / Q26.2 / Q27.3 / Q28.2 / Q29.2 / Q31.2** | **Double-decay FAILURE RECONFIRMED (20th consecutive wave): Q22.1 fix not deployed; `_user_conditions(None)` confirmed unchanged; two full-corpus decay_run entries per slot (processed=5,994 each, Wave 31); active corpus 6,048 as of Wave 31** | **High** | **23/24/25/26/27/28/29/30/31** |",
)

# 8. Update consolidation user_id FAILURE row
content = content.replace(
    "| **Q24.5 / Q25.3 / Q27.5 / Q28.5 / Q29.4 / Q30.4** | **Consolidation user_id attribution fix NOT deployed (6th consecutive): `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; qdrant.py:1143 IS NULL filter still absent; consolidation-source floor-clamped jumped 7→375 (+368) by Wave 29 — Q29.6 FAILURE directly attributable to this bug; co-deployment of Q21.5 + Q24.5 required for permanent fix** | **Medium** | **24/25/27/28/29/30** |",
    "| **Q24.5 / Q25.3 / Q27.5 / Q28.5 / Q29.4 / Q30.4** | **Consolidation user_id attribution fix NOT deployed (7th consecutive): `consolidation.py:235` Memory() constructor missing `user_id=` argument confirmed; consolidation-source floor-clamped 375→449 (+74) by Wave 31; total floor-clamped 1,049; co-deployment of Q21.5 + Q24.5 required for permanent fix** | **Medium** | **24/25/27/28/29/30/31** |",
)

# 9. Update reconcile audit FAILURE row
content = content.replace(
    "| **Q24.8 / Q26.7 / Q27.6 / Q28.6 / Q29.5 / Q30.5** | **Reconcile audit trail fix NOT deployed (6th consecutive): zero reconcile entries in audit_log; neither `reconcile.py` nor `ops.py` contains `log_audit()` calls; Q20.1 reconcile observability gap persists; reconcile is the ONLY scheduled maintenance worker with zero audit visibility; Wave 29: new anomaly — 179 importance mismatches (Qdrant non-zero vs Neo4j=0.0) detected by reconcile but repairs_applied=0; without audit trail, mismatch trend unknowable** | **Medium** | **24/26/27/28/29/30** |",
    "| **Q24.8 / Q26.7 / Q27.6 / Q28.6 / Q29.5 / Q30.5 / Q31.4** | **Reconcile audit trail fix NOT deployed (7th consecutive): zero reconcile entries in audit_log; neither `reconcile.py` nor `ops.py` contains `log_audit()` calls; importance mismatches grew to 264 (+47%, Wave 31); mismatch trend unknowable without audit trail** | **Medium** | **24/26/27/28/29/30/31** |",
)

# 10. Update floor-clamped FAILURE row
content = content.replace(
    "| **Q29.6** | **Floor-clamped accumulation FAILURE: 941 active memories at importance floor (≤0.051), exceeding 800 FAILURE threshold (+268, +39.8% from Q27.4 baseline of 673); consolidation-source floor-clamped 7→375 (+368, +5,257%) directly attributable to Q24.5 bug (user_id=None → invisible to user retrieval → permanently stranded at floor); system-source floor-clamped 432→547 (+115, +26.6%); 15.6% of active corpus now at floor; neither Q22.1 (double-decay) nor Q24.5 (consolidation user_id) fix deployed** | **High** | **29** |",
    "| **Q29.6 / Q31.3** | **Floor-clamped accumulation FAILURE (escalating): Q29.6 941/6,044 (15.6%); Q31.3 1,049/6,048 (17.3%); +108 in 3 hours (Wave 31); consolidation-source 375→449 (+74); system-source 547→572 (+25); pattern 16→25 (+9); rate accelerating (~864/day extrapolated); all three mitigating fixes undeployed** | **High** | **29/31** |",
)

# 11. Add new FAILURE rows for Q31.5 and Q31.7 (before Q27.3)
new_rows = (
    "| **Q31.5** | **Importance mismatches FAILURE: grew 179→264 (+85, +47%) in ~3 hours (Wave 31); mark_superseded importance=0.0 fix undeployed; reconcile cron broken; ~28 new mismatches/hour; chain reconstructable but attribution broken** | **Medium** | **31** |\n"
    "| **Q31.7** | **LLM timeout tiers NOT deployed: 15/18 generate() callsites missing timeout=; only 3/18 protected; Q15.3/Q16.3 180s semaphore hold risk remains in 83.3% of callsites; tiers spec: 15s/30s/60s/90s across 8 files** | **High** | **31** |\n"
)
content = content.replace(
    "| **Q27.3** | **Double-decay inflation queue FAILURE:",
    new_rows + "| **Q27.3** | **Double-decay inflation queue FAILURE:",
)

# 12. Add WARNING row for Q23.6 (before Q30.3)
warning_row = "| **Q23.6** | **Mark_superseded audit coverage WARNING: per-supersedure log_audit() calls exist in consolidation.py:299-305; 1000+ entries in audit trail; chain reconstructable; TWO gaps: user_id null throughout (Q24.5 propagation); 2.6% duplicate memory_ids from Q22.1 double-processing** | **Medium** | **23/31** |\n"
content = content.replace(
    "| **Q30.3** | **Importance mismatch trend WARNING:",
    warning_row + "| **Q30.3** | **Importance mismatch trend WARNING:",
)

# 13. Update INCONCLUSIVE table - hygiene chain row
content = content.replace(
    "| **Q26.1 / Q27.1 / Q28.1 / Q29.1 / Q30.1** | **Hygiene first-archival verification — TIMING (5th consecutive): Q26.1 2 days early; Q27.1 ~17h early; Q28.1 ~18h early; Q29.1 ~17.4h early; Q30.1 ~17.1h early (2026-03-15T10:50 UTC); all 5 waves before 2026-03-16T04:00 UTC target; 0 auto_archive entries at all five measurements; **Wave 31 is mandatory FAILURE escalation point**: if auto_archive=0 after 2026-03-16T04:00 UTC, verdict FAILURE** | **Info** | **26/27/28/29/30** |",
    "| **Q26.1 / Q28.1 / Q29.1 / Q30.1 / Q31.1** | **Hygiene first-archival FAILURE chain: Q26.1 INCONCLUSIVE (2 days early); Q28.1-Q29.1 FAILURE 1st-2nd; Q30.1 INCONCLUSIVE (5th); Q31.1 FAILURE (7th+): 2026-03-15T04:00 UTC window passed with 0 hygiene_run entries; last confirmed cron 2026-03-09; cron broken** | **High** | **26/28/29/30/31** |",
)

# 14. Update GC INCONCLUSIVE row
content = content.replace(
    "| **Q30.7** | **GC-eligible cohort INCONCLUSIVE: 6d 8h 18m before 2026-03-21T19:12 UTC; gc_run=0 (no automated GC cron, Q21.3); superseded 15,184 (−1 from Q29.7; flat); projected pool at eligibility: ~18,359; Wave 31 is verdict-capable on/after 2026-03-21T19:12 UTC** | **Info** | **30** |",
    "| **Q30.7 / Q31.6** | **GC-eligible cohort INCONCLUSIVE: Q30.7 6d 8h before 2026-03-21T19:12 UTC; Q31.6 6d 5h before; gc_run=0; superseded pool 15,275 (+91 from Q30.7 in 3 hours); Wave 32+ verdict-capable on/after 2026-03-21T19:12 UTC** | **Info** | **30/31** |",
)

# 15. Renumber sections (reverse order to avoid double-replacement)
for i in range(21, 2, -1):
    content = content.replace(f"## {i}. ", f"## {i + 1}. ")

# 16. Insert new §3 Wave 31 Results before §4 Wave 30 Results
wave31_section = """## 3. Wave 31 Results (Q23.6, Q27.1, Q31.1–Q31.7)

### Overview

Wave 31 continues on 2026-03-15, ~1 hour after Wave 30. Of 9 questions: 6 FAILURE, 1 WARNING, 2 INCONCLUSIVE.

The defining escalation: **Q31.3 FAILURE — floor-clamped count surged from 941 to 1,049 (+108) in approximately 3 hours** between Wave 30 and Wave 31. Extrapolated daily rate: ~864/day, far higher than prior estimates of ~10-15/day. The consolidation-source component (+74 in 3 hours) is the primary driver, consistent with active consolidation runs at the 09:48 and 12:15 UTC slots. Q31.5 (mismatches 179→264, +47%) confirms mark_superseded bug at ~28/hour. All six FAILURE results reflect undeployed fixes.

---

### Wave 31 Findings Summary

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

### Wave 31 Cross-Domain Observations

#### Observation 1: Floor-clamped accumulation rate is far higher than estimated

Q30.6 showed delta=0 (79-minute same-day window). Q31.3 shows +108 in approximately 3 hours. Extrapolated: ~864/day. The 3-hour window captured two complete consolidation cycles (09:48 and 12:15 UTC), each generating large batches of floor-clamped consolidation memories. The Q30.6 WARNING was misleading; the true rate is visible only across multi-slot windows.

#### Observation 2: Importance mismatches accelerating at 28/hour

Q31.5 shows +85 mismatches in 3 hours = ~28/hour = ~672/day. This exceeds the Q22.9/Q26.4 weekly cycle estimates. Acceleration reflects increased consolidation activity driven by Q22.1 double-decay compounding with Q24.2 mark_superseded importance=0.0. Without the reconcile audit trail (Q31.4 FAILURE, 7th consecutive), trend detection is manual only.

#### Observation 3: 20 consecutive FAILURE waves; trajectory unambiguously downward

Wave 31 marks the 20th consecutive characterization wave with zero fixes deployed. Every data-quality metric is deteriorating simultaneously: floor-clamped growing (+108 in 3 hours), importance mismatches growing (+47%), hygiene cron broken (7th miss), LLM timeout gap (15/18 callsites unprotected). Fix burden: ~19 LOC across 4 files (existing) plus ~17 callsite updates for Q31.7.

---

"""

content = content.replace(
    "## 4. Wave 30 Results", wave31_section + "## 4. Wave 30 Results"
)

open(
    "C:/Users/trg16/Dev/autosearch/recall/findings/synthesis.md", "w", encoding="utf-8"
).write(content)
print("synthesis.md updated successfully")
print(f"Total length: {len(content)} chars")

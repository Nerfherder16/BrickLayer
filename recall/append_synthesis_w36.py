wave36_section = """

---

## 27. Wave 35–36 Findings: Amnesty Execution and Crisis Triage (2026-03-15)

**Updated**: 2026-03-15 (Waves 35–36 complete — 12 additional findings)
**Questions answered this session**: Q35.1–Q35.6, Q36.1–Q36.6

### Wave 35 Summary (6 findings: 2 FAILURE, 1 WARNING×3, 1 HEALTHY)

**Q35.1 FAILURE** — The `POST /admin/importance/rehabilitate` endpoint (admin.py:1123) uses `>= 0.05` instead of `> 0.05`. This off-by-one operator causes every floor-clamped memory at exactly 0.050 to be SKIPPED. The endpoint has never been invoked (audit log: 0 entries). The 644 premature casualties would survive the scan entirely unprocessed.

**Q35.2 WARNING** — Hygiene cron is registered in WorkerSettings.cron_jobs (04:00 UTC daily). DID run once today (2026-03-15T14:47 UTC — first ever run) but produced `candidates_scanned: 0, archived: 0`.

**Q35.3 FAILURE** — 846 floor-clamped null-user_id active memories (up from 644 in Q34.7, +202). Development domain: 229 casualties (>100 FAILURE threshold). Total critical domain casualties: 413/846 (48.8%). Recall domain: 29 casualties (recursive self-knowledge loss).

**Q35.4 WARNING** — 2 of 3 code fixes deployed: Fix-2 (explicit worker.run(user_id=0) in decay.py) DEPLOYED; Fix-3 (consolidation.py user_id=cluster[0].user_id) DEPLOYED. Fix-1 (qdrant.py:1207 uid>0 guard) NOT DEPLOYED — double-decay continues.

**Q35.5 WARNING** — `POST /admin/importance/amnesty?dry_run=false` can rescue floor-clamped memories (dry-run: 4,173 of 5,202 memories would be boosted including those at importance=0.05). The dedicated rehabilitate endpoint is broken (off-by-one). Amnesty is the only actionable no-code mitigation.

**Q35.6 HEALTHY** — Floor-clamped stable at 1,049 over 2h14m since Q31.3 baseline (no consolidation run in window). Structural crisis unchanged; stability is transient.

### Wave 36 Summary (6 findings: 4 HEALTHY, 2 WARNING)

**Q36.1 HEALTHY** — Amnesty ran live at ~2026-03-15T15:42 UTC: **4,173 of 5,211 floor-clamped memories rescued (80.1% of scanned pool)**. Null-pool of 846 reduced to ~1 eligible residual (99.9% rescue rate). The 0.0–0.2 importance bucket dropped from ~23% to **3.9%** of active corpus. 899 memories skipped (ephemeral/pinned/permanent — correctly excluded). Secondary finding: amnesty writes NO audit rows (bulk operations are invisible to the audit trail — an observability gap).

**Q36.2 WARNING** — Hygiene 0-candidate result is CORRECT. The system's oldest memory was created 2026-02-14 — only 29 days ago. The hygiene cutoff is `now - 30 days = 2026-02-13`. **Zero memories are older than 30 days.** The filter implementation is logically correct. First hygiene eligibility window opens 2026-03-16.

**Q36.3 HEALTHY** — The one-char rehabilitate fix (`>= 0.05` → `> 0.05`) would rescue ~838/846 (99.1%) of the null-pool via branch-2 (durable durability). Only ~8 ephemeral ac<3 memories are permanently stranded (correct behavior). Amnesty+rehabilitate combined: ~840–843 of 846 (>99%). Over-inflation risk LOW (same gap as amnesty, smaller magnitude 0.2 vs 0.3).

**Q36.4 HEALTHY** — Post-amnesty dry_run: only **5 memories still eligible** (importance 0.37–0.40, naturally decayed post-run — not v3.2.5 victims). Null-pool residual: ~1. Active pool ~6,126. The crisis is structurally resolved by the amnesty execution.

**Q36.5 WARNING** — Fix-1 (uid>0 guard) is safe but has two edge cases: (1) **74 FamilyHub memories with user_id 53–71 exist** — these correctly remain in the per-user loop after Fix-1; (2) Three other callers of get_distinct_user_ids (patterns.py, dream_consolidation.py, consolidation.py) have no explicit system fallback blocks — pre-existing gap, not introduced by Fix-1. **Deployment requires `docker compose restart recall-worker`** (ARQ has no hot-reload).

**Q36.6 HEALTHY** — N3 (stranded, amnesty-ineligible) ≈ **8** (threshold FAILURE >500). Correction: graph strength does NOT gate amnesty eligibility — it modulates boost amount only. All durable/None memories are rescued regardless of graph connectivity. The N2 "graph-isolated stranded" segment does not exist.

### Revised Action Checklist (post-Wave 36)

The Wave 34 16.6-day urgency is now RESOLVED. Amnesty executed and rescued 4,173 memories. Updated action priority:

| Step | Action | Status | Notes |
|------|--------|--------|-------|
| Step 0 | Run amnesty endpoint | **DONE** (2026-03-15) | 4,173 rescued; 0.0-0.2 bucket: 23% → 3.9% |
| Step 0b | Fix rehabilitate filter (>= → >) | OPEN | One-char change in admin.py:1123; needed for future decay events |
| Step 1 | Deploy qdrant.py Fix-1 (uid>0 guard) | OPEN | Only remaining code fix to stop double-decay; requires container restart |
| Step 2 | Consolidation user_id fix | **DEPLOYED** | consolidation.py:250 user_id=cluster[0].user_id confirmed |
| Step 3 | Hygiene cron | **REGISTERED + RUNNING** | Ran 2026-03-15T14:47 UTC; 0 candidates (system <30 days old) |
| Step 4 | Amnesty audit trail | OPEN | Bulk operations produce no audit rows — observability gap |

**Remaining critical path**: Deploy qdrant.py Fix-1 (`if uid is not None and uid > 0:`) with `docker compose restart recall-worker`. This is the only remaining code change needed to stop double-decay. 74 FamilyHub users (uid 53–71) will correctly be processed in per-user loop after fix. Three non-decay callers (patterns.py, dream_consolidation.py, consolidation.py) have no system fallback — document as pre-existing gap.
"""

with open("C:/Users/trg16/Dev/autosearch/recall/findings/synthesis.md", "a") as f:
    f.write(wave36_section)
print("Wave 36 synthesis appended")

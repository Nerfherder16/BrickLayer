# Changelog

All notable changes documented here.
Maintained automatically by BrickLayer post-commit hook and synthesizer.

---

## [Unreleased]

---
- `fb9addf` docs(hook-audit): Wave 1 synthesis -- 25 questions, 3 FAILURE, 9 WARNING, 13 HEALTHY (2026-03-29)

## [Wave 1] -- 2026-03-29

25 questions across 13 Masonry hooks: 13 HEALTHY, 3 FAILURE, 9 WARNING. Core stop-guard chain confirmed sound; three isolated defects identified with clear fix paths.

### Found (open)
- `D1.3` [FAILURE] -- masonry-handoff.js reads session_id from argv (not stdin); de-dup guard fires once per machine lifetime (`masonry/hooks/masonry-handoff.js`)
- `A1.3` [FAILURE] -- recall-session-summary.js stale domain mapping; all session summaries land in wrong Recall domains (`masonry/hooks/recall-session-summary.js`)
- `WM1.1` [FAILURE] -- masonry-observe.js non-atomic read-modify-write race on masonry-state.json under concurrent multi-machine use (`masonry/hooks/masonry-observe.js`)
- `D1.4` [WARNING] -- Session snapshot absent on session-start timeout; mtime fallback is cross-session imprecise
- `A1.4` [WARNING] -- masonry-ui-compose-guard.js missing isResearchProject() guard
- `R1.1` [WARNING] -- masonry-guard.js archived; guard warning flush in masonry-register.js is dead code
- `R1.2` [WARNING] -- masonry-training-export.js uses spawnSync (blocks 60s) despite async:true
- `R1.3` [WARNING] -- Analytics triggers require masonry/ in cwd; never fire from project subdirs
- `A1.3-FU1` [WARNING] -- Orphaned wrong-domain Recall entries retrievable via soft-boost
- `A1.3-FU2` [WARNING] -- No shared JS domains module; three hooks maintain independent copies

### Healthy
- D1.1, D1.2, D1.5: Stop hook guard chain correct; all exit-2 paths covered
- A1.1, A1.2: stop_hook_active coverage complete; BL silence detection consistent
- R1.4, V1.2: Complementary session summaries; Recall cache outside git scope
- D1.3-FU2: masonry-session-summary.js reads stdin correctly (reference for fix)
- WD1.1, WD1.2: subagent-tracker and context-data.js both correct
- WM1.2, WM1.3: No TTL or cold-start issues; per-invocation boolean; UUID-keyed files

---
- `0991ff6` feat: complete Wave Mid findings WM1.1-WM1.3; all 27 questions done (2026-03-29)
- `c71bcf3` feat: add WD1.1, WD1.2 findings; remove stale AUDIT_REPORT (2026-03-29)
- `78570ad` feat: Wave 1 + Wave-mid findings (22 questions complete) (2026-03-29)

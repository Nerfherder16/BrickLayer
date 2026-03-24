# BrickLayer 2.0 — Evolve Survey Wave 2

**Date**: 2026-03-24
**Mode**: evolve
**Context**: Post Wave 1 — 3 IMPROVEMENTs landed, now measuring actual impact

---

## Signal Sources Scanned

### 1. Finding history — Wave 1 outcomes

| Finding | Verdict | Post-wave status |
|---------|---------|-----------------|
| E1.1 Monitor DEGRADED_TRENDING | IMPROVEMENT | ✓ Stable — mode program updated |
| E1.2 Validate FAILURE routing | IMPROVEMENT | ✓ Stable — validate.md self-contained |
| E1.3 Karen accuracy | IMPROVEMENT (projected ~0.90) | ❌ **REGRESSION** — actual score 0.30 |

**E1.3 outcome**: Score went DOWN from 0.55 to 0.30. Prompt fix confirmed applied to correct
karen.md. Model is ignoring the commit-type-first rule because conflicting signal from
`files_modified` (doc-only files) overrides it. Training data structural issue is the root cause.

### 2. Agent accuracy — updated eval

| Agent | Score | Prev | Delta | Target |
|-------|-------|------|-------|--------|
| karen | 0.30 | 0.55 | -0.25 | 0.85 |

Post-eval diagnosis (20 examples inspected):
- All 20 records have `files_modified = ["ROADMAP.md"]` or similar doc-only files
- Karen correctly reasons "docs were already written (ROADMAP.md in files_modified) → skip"
- But expected = "updated" for feat/docs commits → eval fails
- Root cause: `score_ops_agents._score_karen()` uses the KAREN OUTPUT COMMIT as training record
  - `input.files_modified` = doc files karen WROTE (e.g., ROADMAP.md)
  - Should be: doc files from the PARENT commit that TRIGGERED karen's run
- The commit-type-first rule cannot override this because the model correctly interprets
  "doc-only files_modified" as "docs already written for this commit → nothing to do"

### 3. Training data anatomy

```
scored_all.jsonl karen records: 321 total
  - 237x commit_subject = "chore: update CHANGELOG for <hash>"  ← bot commits
  - 55x feat/fix/refactor/docs                                   ← meaningful
  - 16x chore (other), 5 reverted, 6 skipped

input.files_modified distribution:
  - 252x ["CHANGELOG.md"]    ← 78% are CHANGELOG-only (karen's own writes)
  - 33x  ["ROADMAP.md"]      ← 10% are ROADMAP-only (karen's own writes)

expected distribution (from _derive_expected):
  - 310x "updated"  (doc_files_written > 0)
  - 6x   "skipped"  (doc_files_written == 0)
  - 5x   "reverted"

Key insight: For "chore: update CHANGELOG for abc123" + files=["CHANGELOG.md"]:
  - karen correctly outputs "skipped" (it IS a bot commit)
  - but expected = "updated" (doc_files_written=1) → WRONG LABEL
  → 237/321 records (73%) have INCORRECT expected labels
```

### 4. Score anatomy — why 0.30 not 0.55

The two evals selected different last-20 records:
- Wave 1 eval (0.55): happened to include ~11 "skipped/reverted" records where expected="skipped"
- Wave 2 eval (0.30): selected 15 feat/docs records with files_modified=["ROADMAP.md"] where
  all score 0.25-0.45 (below 0.5 pass threshold), plus 3 failed outputs (score=0.00),
  plus 2 revert records that scored 0.75 = 2/20 clear passes + borderline scores

### 5. Fix required: score_ops_agents.py

In `_score_karen(base_dir, all_commits)`:
```python
# CURRENT (wrong): uses karen's output commit
"input": {"commit_subject": subject[:200], "files_modified": karen_files}

# FIX: use the PARENT commit's source files
parent = all_commits[idx + 1]  # git log is newest-first
source_files = [f for f in parent.get("files", []) if Path(f).name not in _KAREN_FILES]
"input": {"commit_subject": parent["subject"][:200], "files_modified": source_files}
```

This gives karen the correct context:
- Subject = "feat(bl2): add mode dispatch" (the triggering commit)
- files_modified = ["bl/campaign.py", "bl/questions.py"] (source files)
- Expected = "updated" (doc_files_written > 0 from current commit)
→ Karen sees feat + source files → "updated" ✓

### 6. Secondary fix: build_karen_metric._derive_expected()

The 237 "chore: update CHANGELOG" records have wrong labels. After fixing the pipeline,
newly generated records will be correct. But existing records still have wrong labels.

Fix options:
a) Detect "chore: update CHANGELOG for <hash>" in commit_subject → return "skipped" as expected
b) Filter these records out of karen's training/eval set entirely
c) Regenerate training data from scratch after fixing score_ops_agents.py

Option (a) is quickest and non-destructive. Option (c) is thorough but requires
running score_all_agents.py across full git history.

---

## Candidate Ranking — Wave 2

| Rank | Candidate | Impact | Ease | ROI | Status |
|------|-----------|--------|------|-----|--------|
| 1 | Fix _derive_expected for bot commits | High | Easy | High×Easy | Wave 2 target |
| 2 | Fix score_ops_agents to use parent commit | High | Medium | High×Medium | Wave 2 target |
| 3 | Regenerate karen training data + verify | High | Easy | High×Easy | Wave 2 target |
| 4 | Multi-agent BrickLayer Phase 1 doc | Medium | Easy | Medium×Easy | Deferred |
| 5 | BrickLayer dashboard design | Medium | Hard | Medium×Hard | Deferred |

**Wave 2 questions: E2.1, E2.2, E2.3**

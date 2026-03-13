# BrickLayer Campaign Synthesis — Bricklayer
**Date**: 2026-03-13
**Questions run**: 15 (Q1.1–Q4.4)
**Waves completed**: 4

---

## Verdict Summary

| Q | Category | Verdict | Issue |
|---|----------|---------|-------|
| Q1.1 | Correctness | WARNING | Zero test files in repo |
| Q1.2 | Correctness | FAILURE | Template baseline returns FAILURE — placeholder revenue model never replaced |
| Q1.3 | Correctness | FAILURE | Dashboard parse_questions table-only; block-format questions invisible |
| Q2.1 | Quality | FAILURE | onboard.py line 241: wrong data appended silently on exception |
| Q2.2 | Quality | FAILURE | bricklayer_launcher.pyw: corrupt project.json silently dropped |
| Q2.3 | Quality | FAILURE | dashboard: hardcoded `C:/Users/trg16` path in get_projects |
| Q2.4 | Quality | INCONCLUSIVE | mypy not installed |
| Q3.1 | Security | FAILURE | Path traversal via finding_id, no guard, server on 0.0.0.0 |
| Q3.2 | Security | FAILURE | Wildcard CORS + 0.0.0.0 + no auth on mutation routes |
| Q3.3 | Correctness | FAILURE | ID collision via len(); add_question writes wrong format |
| Q3.4 | Security | WARNING | Docs injected into prompt with no XML delimiters |
| Q4.1 | Agent | HEALTHY | Security fixes applied — commit 3425225 |
| Q4.2 | Agent | HEALTHY | Silent swallows replaced — commit b2a18a3 |
| Q4.3 | Agent | HEALTHY | 19 tests written, all pass — commit ecdc767 |
| Q4.4 | Agent | HEALTHY | Type annotations migrated — commit 98f45fc |

**FAILURE: 8 | WARNING: 2 | INCONCLUSIVE: 1 | HEALTHY: 4**

---

## Fixed This Session (Q4 agents)

All four agent tasks completed successfully:

1. **Q4.1** — `dashboard/backend/main.py` hardened: path traversal guards on `get_finding`, `correct_finding`, and `get_project_path`; CORS restricted to `localhost:3100`; hardcoded base path replaced with `AUTOSEARCH_BASE` env var; also closed an unsanitized `project` query param vector that wasn't in the original finding.

2. **Q4.2** — `onboard.py` and `bricklayer_launcher.pyw`: all 4 silent swallows replaced with stderr warnings. Critical fix: line 241 no longer appends "Node.js" on JSON parse failure.

3. **Q4.3** — 19 tests created in `tests/test_core.py` covering `detect_stack`, `parse_questions`, `run_simulation`, `evaluate`. The `test_malformed_package_json_does_not_add_nodejs` test directly validates the Q2.1 fix.

4. **Q4.4** — `Optional[X]` → `X | None` migration throughout `dashboard/backend/main.py`. Legacy `from typing import Optional` removed.

---

## Still Open (not fixed this session)

### Q1.2 — Template baseline returns FAILURE
**Root cause**: `revenue = monthly_volume * 0.001` is a placeholder TODO. With 500 units × 350 volume × $0.001 = $175/mo revenue vs $30,000/mo ops cost, the baseline scenario goes bankrupt.
**Fix needed**: Replace with `revenue = ops_cost * 1.2` (or similar self-sustaining formula) in `template/simulate.py`. Clear comment directing project developers to replace with the real model.
**Risk**: High. Any new project starts from a broken baseline.

### Q1.3 — Dashboard / simulate.py format mismatch
**Root cause**: `dashboard/backend/main.py::parse_questions()` only parses pipe-table format. `add_question()` writes pipe-table rows into block-format files. The current `questions.md` format (`## Q{n}.{m} [CATEGORY]`) is completely invisible to the dashboard.
**Fix needed**: Update `parse_questions()` to support block format. Update `add_question()` to write block format. Coordinate with any simulate.py parser changes.
**Risk**: High. Dashboard is currently non-functional for question display and management on all current projects.

### Q3.3 — ID collision in add_question
**Root cause**: `next_num = len(existing_ids) + 1` collides after any deletion. Also linked to Q1.3 — the format fix must accompany the ID fix.
**Fix needed**: Replace `len()` with `max(int(id.split('.')[1].rstrip('x')) for id in existing_ids) + 1` (with empty-list guard).
**Risk**: Medium.

### Q3.4 — Prompt injection via docs content
**Root cause**: `docs_content` injected into Claude prompt with no XML delimiters.
**Fix needed**: Wrap in `<docs>\n{docs_content}\n</docs>` in `onboard.py::run_scout()`.
**Risk**: Low-medium (docs/ is human-controlled).

### Q2.4 — Type annotation completeness
**Status**: INCONCLUSIVE — mypy not installed. Q4.4 applied the `Optional` migration but full mypy validation couldn't be confirmed.
**Fix needed**: `pip install mypy` and run a clean pass.

---

## Cross-Project Observations

No cross-project changes were required. All fixes apply within the autosearch repo itself (target git = BrickLayer framework repo). No handoff documents needed.

The root simulate.py dispatcher (`autosearch/simulate.py`) referenced in `prepare.md` does not exist — questions were run manually this session. This is a gap in the framework itself: the campaign runner is documented but not implemented.

---

## Wave 5 Candidates

Based on Wave 1–4 findings, high-value Wave 5 questions:

- **Q5.1**: Does `parse_questions()` in `simulate.py` (the runner) handle the block format correctly end-to-end? (Verify against Q1.3)
- **Q5.2**: Does the missing `simulate.py` dispatcher mean `prepare.md`'s `--campaign` and `--list` flags are completely non-functional?
- **Q5.3**: Can `get_project_path()` new containment guard be bypassed via symlinks?
- **Q5.4**: Does `add_question()` writing table format into block-format files corrupt the file in a way that breaks the next simulate.py parse pass?
- **Q5.5**: Is there a race condition in `results.tsv` when two campaign runners write simultaneously?

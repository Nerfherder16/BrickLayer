# BrickLayer Campaign Questions — Bricklayer

Questions are organized in waves. Each wave targets blindspots from the prior wave.
Status is tracked in results.tsv — do not edit manually.

---

## Q1.1 [CORRECTNESS] Test suite baseline
**Mode**: correctness
**Target**: .
**Hypothesis**: The autosearch repo has no test files, meaning there is no automated correctness baseline and any refactor can silently break core functionality.
**Test**: `find C:/Users/trg16/Dev/autosearch -name "test_*.py" -o -name "*_test.py" | grep -v ".git" | head -10`; also run `python -c "import onboard; import bricklayer_launcher"` to confirm importability.
**Verdict threshold**:
- HEALTHY: At least one test file found and all imports succeed
- WARNING: No test files but all imports succeed cleanly
- FAILURE: No test files exist, OR any import raises an error

---

## Q1.2 [CORRECTNESS] Template simulate.py runs to HEALTHY verdict
**Mode**: correctness
**Target**: template/simulate.py
**Hypothesis**: The template simulate.py baseline scenario runs without error and prints `verdict: HEALTHY`, confirming the framework scaffold works before any agent touches it.
**Test**: `cd C:/Users/trg16/Dev/autosearch && python template/simulate.py 2>&1 | grep -E "^verdict:|^primary_metric:|Error|Traceback"`
**Verdict threshold**:
- HEALTHY: Output contains `verdict: HEALTHY` and no traceback
- WARNING: Output contains `verdict: WARNING` — thresholds may be misconfigured
- FAILURE: Traceback, import error, or `verdict: FAILURE` on the unmodified baseline

---

## Q1.3 [CORRECTNESS] Dashboard parse_questions handles wave-based format
**Mode**: correctness
**Target**: dashboard/backend/main.py
**Hypothesis**: `parse_questions()` in `dashboard/backend/main.py` only parses the old `| ID | Status | Question |` table format (lines 44–76) but BrickLayer's own questions.md now uses the `## Q{wave}.{num} [CATEGORY]` block format — causing `/api/questions` to return an empty list for all current projects.
**Test**: Start the dashboard backend and call `GET /api/questions?project=C:/Users/trg16/Dev/autosearch/projects/bricklayer`; compare response count against `grep -c "^## Q" C:/Users/trg16/Dev/autosearch/projects/bricklayer/questions.md`.
**Verdict threshold**:
- HEALTHY: API returns the same question count as the grep
- WARNING: API returns fewer questions than grep (partial parse)
- FAILURE: API returns 0 questions while grep finds >0

---

## Q2.1 [QUALITY] Silent swallows in onboard.py detect_stack
**Mode**: quality
**Target**: onboard.py
**Agent**: security-hardener
**Hypothesis**: `detect_stack()` in `onboard.py` has two `except Exception:` blocks (lines 241, 253) that silently swallow JSON parse errors for `package.json` and Cargo.toml read failures — in the `package.json` case it even appends "Node.js" as if detection succeeded, producing a wrong stack label with no diagnostic output.
**Test**: `grep -n "except Exception" C:/Users/trg16/Dev/autosearch/onboard.py` — then manually verify each instance has a log/print or re-raise.
**Verdict threshold**:
- HEALTHY: All except clauses either log the error or re-raise; none append fallback data silently
- WARNING: 1–2 bare swallows with no observable side-effect
- FAILURE: Any except clause that appends data to results or returns wrong output on error

---

## Q2.2 [QUALITY] Silent swallow in bricklayer_launcher load_projects
**Mode**: quality
**Target**: bricklayer_launcher.pyw
**Agent**: security-hardener
**Hypothesis**: `load_projects()` in `bricklayer_launcher.pyw` (line 53) has `except Exception: pass` — a corrupt or partially-written `project.json` causes the project to silently disappear from the launcher UI with no error shown to the user.
**Test**: `grep -n "except Exception" C:/Users/trg16/Dev/autosearch/bricklayer_launcher.pyw` — confirm each has a visible error path (messagebox or stderr).
**Verdict threshold**:
- HEALTHY: All exceptions in load_projects produce a visible error or are logged
- WARNING: Exception is caught but at least logged to stderr
- FAILURE: Exception swallowed silently with `pass`, user gets no feedback

---

## Q2.3 [QUALITY] Hardcoded absolute path in dashboard get_projects
**Mode**: quality
**Target**: dashboard/backend/main.py
**Agent**: security-hardener
**Hypothesis**: `get_projects()` in `dashboard/backend/main.py` (line 286) hardcodes `C:/Users/trg16/Dev/autosearch` — the endpoint silently returns an empty list on any other machine or if the repo is moved, with no error or config-driven fallback.
**Test**: `grep -n "C:/Users/trg16" C:/Users/trg16/Dev/autosearch/dashboard/backend/main.py` — count hardcoded paths; also check `get_project_path()` for same pattern.
**Verdict threshold**:
- HEALTHY: No hardcoded user paths; base path derived from environment variable or `__file__`
- WARNING: Hardcoded path exists but a fallback env var is documented
- FAILURE: Hardcoded path with no fallback or config mechanism

---

## Q2.4 [QUALITY] Missing type annotations in dashboard backend
**Mode**: quality
**Target**: dashboard/backend/main.py
**Agent**: type-strictener
**Hypothesis**: `dashboard/backend/main.py` uses `Optional[str]` from `typing` (old style) and several helper functions lack return type annotations — running mypy will surface annotation gaps that make the codebase harder to maintain.
**Test**: `cd C:/Users/trg16/Dev/autosearch && python -m mypy dashboard/backend/main.py --ignore-missing-imports 2>&1 | tail -20`
**Verdict threshold**:
- HEALTHY: 0 mypy errors
- WARNING: 1–5 type errors
- FAILURE: >5 type errors or any `error: Function is missing a return type annotation`

---

## Q3.1 [SECURITY] Path traversal via finding_id in correct_finding endpoint
**Mode**: quality
**Target**: dashboard/backend/main.py
**Agent**: security-hardener
**Hypothesis**: `correct_finding()` (line 256) and `get_finding()` (line 247) use `finding_id` directly as a filename (`f"{finding_id}.md"`) with no sanitization — a caller can supply `finding_id=../../onboard` to read or append to arbitrary files outside `findings/`.
**Test**: `grep -n "finding_id" C:/Users/trg16/Dev/autosearch/dashboard/backend/main.py` — check whether any `resolve()` or `is_relative_to()` guard exists before file operations.
**Verdict threshold**:
- HEALTHY: All file paths validated with `Path.resolve().is_relative_to(findings_dir)` before open
- WARNING: No traversal guard but server only binds to localhost
- FAILURE: No path validation and server can bind to non-localhost

---

## Q3.2 [SECURITY] Wildcard CORS on mutation endpoints
**Mode**: quality
**Target**: dashboard/backend/main.py
**Agent**: security-hardener
**Hypothesis**: `CORSMiddleware` is configured with `allow_origins=["*"]` (line 15) — any website can issue cross-origin POST requests to `/api/questions` and `/api/findings/{id}/correct`, silently modifying the campaign state if the dashboard is accessible on LAN.
**Test**: `grep -n "allow_origins" C:/Users/trg16/Dev/autosearch/dashboard/backend/main.py` — confirm whether wildcard is used and whether mutation routes have any auth layer.
**Verdict threshold**:
- HEALTHY: Origins restricted to `localhost` or specific trusted hosts; or mutations require a token
- WARNING: Wildcard CORS but server only binds to 127.0.0.1
- FAILURE: Wildcard CORS with server bound to 0.0.0.0 or LAN IP and no auth on mutations

---

## Q3.3 [CORRECTNESS] Question ID collision in add_question
**Mode**: correctness
**Target**: dashboard/backend/main.py
**Agent**: forge
**Hypothesis**: `add_question()` (line 213) generates new IDs as `len(existing_ids) + 1` — if any questions have been deleted, manually edited, or marked DONE and removed, the generated ID collides with an existing one, causing duplicate IDs in `questions.md` and breaking the results log.
**Test**: Manually add two questions via the API to a domain that already has 3 entries, then delete one entry from `questions.md` and add another via API — inspect the generated IDs for collision.
**Verdict threshold**:
- HEALTHY: ID generation scans existing IDs and guarantees uniqueness regardless of gaps
- WARNING: Collision only possible after manual file editing (unlikely in practice)
- FAILURE: Collision reproducible via normal API usage sequence

---

## Q3.4 [SECURITY] Prompt injection via docs content in run_scout
**Mode**: quality
**Target**: onboard.py
**Agent**: security-hardener
**Hypothesis**: `run_scout()` in `onboard.py` (lines 337–358) reads all files from `docs/` and injects up to 3000 chars per file directly into the prompt passed to `claude -p --dangerously-skip-permissions` — a malicious or accidentally crafted doc file could inject instructions that override Scout's behavior or exfiltrate other project files.
**Test**: `grep -n "docs_content" C:/Users/trg16/Dev/autosearch/onboard.py` — check whether doc content is sanitized or clearly delimited before injection into the prompt string.
**Verdict threshold**:
- HEALTHY: Doc content is wrapped in explicit delimiters (e.g. XML tags) that separate it from instructions, or content is validated before injection
- WARNING: No delimiter but docs/ is human-controlled and not externally writable
- FAILURE: No delimiter and docs/ is world-writable or populated from external sources

---

## Q4.1 [AGENT] Harden dashboard path traversal and CORS
**Mode**: agent
**Target**: dashboard/backend/main.py
**Agent**: security-hardener
**Hypothesis**: The two path traversal vectors (`finding_id` and `project` query param) and wildcard CORS together form an exploitable combination — hardening all three in one pass is the minimum viable security fix for the dashboard.
**Test**: After fix, verify: (1) `curl "http://localhost:8000/api/findings/../../onboard"` returns 404 or 400, not file content; (2) CORS origin header in response is not `*`; (3) all existing API routes still return correct data.
**Verdict threshold**:
- HEALTHY: All three checks pass
- WARNING: Two of three pass; one outstanding issue documented
- FAILURE: Any path traversal still exploitable after fix

---

## Q4.2 [AGENT] Fix silent swallows in onboard.py and launcher
**Mode**: agent
**Target**: onboard.py, bricklayer_launcher.pyw
**Agent**: security-hardener
**Hypothesis**: The five silent `except Exception: pass/fallback` blocks in `onboard.py` (lines 241, 253, 343, 602) and one in `bricklayer_launcher.pyw` (line 53) should log or surface errors so misconfigurations are visible rather than silently producing wrong output.
**Test**: After fix, `grep -n "except Exception:" C:/Users/trg16/Dev/autosearch/onboard.py` — confirm each is followed by a `print()`/`logger.warning()` or re-raise, not bare `pass`.
**Verdict threshold**:
- HEALTHY: All except blocks emit a diagnostic or re-raise; none silently swallow with wrong return value
- WARNING: All blocks emit a diagnostic but still return fallback data
- FAILURE: Any block still silently swallows without a diagnostic

---

## Q4.3 [AGENT] Add test coverage for core framework functions
**Mode**: agent
**Target**: onboard.py, dashboard/backend/main.py
**Agent**: test-writer
**Hypothesis**: The zero-test codebase means regressions in `detect_stack()`, `parse_questions()`, `run_simulation()`, and `evaluate()` are invisible — a minimum test suite covering these four functions would catch the format-mismatch bug (Q1.3) and stack-detection errors (Q2.1) automatically.
**Test**: After fix, `cd C:/Users/trg16/Dev/autosearch && python -m pytest tests/ -q 2>&1 | tail -5` — should show at least 8 passing tests covering the four functions above.
**Verdict threshold**:
- HEALTHY: ≥8 tests, all pass, covering detect_stack, parse_questions, run_simulation, evaluate
- WARNING: Tests exist but coverage <4 of the target functions
- FAILURE: No tests written, or tests exist but any fail

---

## Q4.4 [AGENT] Migrate dashboard backend to modern type annotations
**Mode**: agent
**Target**: dashboard/backend/main.py
**Agent**: type-strictener
**Hypothesis**: `dashboard/backend/main.py` imports `Optional` from `typing` (Python 3.9 legacy style) and several helper functions lack return type annotations — migrating to `X | None` syntax and adding return types will surface latent type bugs and align with Python 3.10+ standards used by the rest of the project.
**Test**: After fix, `python -m mypy dashboard/backend/main.py --ignore-missing-imports 2>&1 | grep -c "error:"` should return 0.
**Verdict threshold**:
- HEALTHY: 0 mypy errors, no `from typing import Optional` imports remaining
- WARNING: 0 mypy errors but legacy typing imports remain
- FAILURE: >0 mypy errors after migration

---

## Q5 — Wave 5 (forge-generated after Wave 4 completes)

*Leave blank. The `forge` agent generates Wave 5 questions from Wave 4 findings.*

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

## Q5.1 [CORRECTNESS] prepare.md runner path is wrong
**Mode**: correctness
**Target**: projects/bricklayer/prepare.md, recall/simulate.py
**Hypothesis**: `prepare.md` instructs `python simulate.py --project bricklayer` from autosearch root, but the actual runner is `recall/simulate.py`. A new user following prepare.md gets `No such file: simulate.py` with no guidance.
**Test**: `ls C:/Users/trg16/Dev/autosearch/simulate.py 2>&1; ls C:/Users/trg16/Dev/autosearch/recall/simulate.py 2>&1`
**Verdict threshold**:
- HEALTHY: Root simulate.py exists OR prepare.md references recall/simulate.py correctly
- WARNING: Root simulate.py missing but prepare.md has a note pointing to recall/
- FAILURE: Root simulate.py missing and prepare.md gives wrong path with no correction

---

## Q5.2 [CORRECTNESS] recall/simulate.py stdout wrapper not guarded by __main__
**Mode**: correctness
**Target**: recall/simulate.py
**Hypothesis**: Line 31 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")` runs at import time, not guarded by `if __name__ == "__main__"`. Importing simulate.py from any other module (e.g. tests) replaces sys.stdout permanently, breaking pytest capture.
**Test**: `python -c "import sys; orig = sys.stdout; import sys; sys.path.insert(0,'C:/Users/trg16/Dev/autosearch/recall'); import importlib.util; print('stdout replaced:', sys.stdout is not orig)"` — also check line 31 of recall/simulate.py for __main__ guard.
**Verdict threshold**:
- HEALTHY: sys.stdout reassignment is inside `if __name__ == "__main__":` block
- FAILURE: Reassignment is at module level with no guard

---

## Q5.3 [CORRECTNESS] analyze.py handles missing results.tsv
**Mode**: correctness
**Target**: template/analyze.py, adbp/analyze.py
**Hypothesis**: `analyze.py` reads `results.tsv` to generate the PDF report. If the file doesn't exist (new project before any runs), the script crashes with FileNotFoundError rather than printing a helpful message.
**Test**: `cd C:/Users/trg16/Dev/autosearch/template && python analyze.py 2>&1 | head -10`
**Verdict threshold**:
- HEALTHY: Script prints a helpful "no results yet" message and exits 0
- WARNING: Script exits non-zero but with a clear error message
- FAILURE: Unhandled FileNotFoundError or AttributeError traceback

---

## Q5.4 [SECURITY] get_project_path containment guard bypassable via symlinks
**Mode**: quality
**Target**: dashboard/backend/main.py
**Agent**: security-hardener
**Hypothesis**: The new `get_project_path()` containment guard uses `Path.resolve().is_relative_to()`. On Linux/Mac, a symlink inside `projects/` pointing outside it bypasses `resolve()` checks. On Windows, junction points do the same. The guard is sound on Windows without junctions but documents a known limitation.
**Test**: `grep -n "resolve\|is_relative_to\|symlink\|junction" C:/Users/trg16/Dev/autosearch/dashboard/backend/main.py`
**Verdict threshold**:
- HEALTHY: Guard uses resolve() AND documents symlink/junction limitation, or server only binds to 127.0.0.1
- WARNING: Guard uses resolve() without symlink documentation but server binds to localhost only
- FAILURE: Guard uses resolve() without symlink documentation AND server binds to 0.0.0.0

---

## Q5.5 [CORRECTNESS] results.tsv race condition on concurrent writes
**Mode**: correctness
**Target**: recall/simulate.py
**Hypothesis**: `write_result()` in `recall/simulate.py` appends to `results.tsv` with no file lock. If two runners execute simultaneously against the same project, both read-then-append without coordination, producing interleaved or partial TSV rows.
**Test**: `grep -n "results_tsv\|write_result\|open.*append\|lock\|fcntl" C:/Users/trg16/Dev/autosearch/recall/simulate.py | head -20`
**Verdict threshold**:
- HEALTHY: File write uses a lock (fcntl, msvcrt, or threading.Lock)
- WARNING: No lock but campaign runner is single-process by design (acceptable)
- FAILURE: No lock and `--campaign` mode spawns parallel workers writing to the same file

---

## Q5.6 [AGENT] Fix template/simulate.py baseline verdict
**Mode**: agent
**Target**: template/simulate.py
**Agent**: security-hardener
**Hypothesis**: The unmodified template baseline returns FAILURE because `revenue = monthly_volume * 0.001` (TODO placeholder) produces ~$175/mo revenue vs $30,000/mo ops cost. Replace with a self-sustaining formula so the baseline is HEALTHY before the agent makes any changes.
**Test**: After fix, `python template/simulate.py 2>&1 | grep "^verdict:"` should return `verdict: HEALTHY`
**Verdict threshold**:
- HEALTHY: Output contains `verdict: HEALTHY` and no traceback
- FAILURE: Still returns FAILURE or traceback

---

## Q5.7 [AGENT] Fix dashboard parse_questions + add_question format mismatch
**Mode**: agent
**Target**: dashboard/backend/main.py
**Agent**: forge
**Hypothesis**: `parse_questions()` reads only table format; `add_question()` writes table format; current questions.md uses block format. Both functions need updating to support the block format, and add_question needs max-based ID generation.
**Test**: After fix, manually verify parse_questions returns all 15 questions from projects/bricklayer/questions.md; verify add_question writes a valid block-format entry.
**Verdict threshold**:
- HEALTHY: parse_questions returns 15 questions; add_question writes block format with non-colliding ID
- WARNING: parse_questions works but add_question still has ID collision risk
- FAILURE: Either function still broken for block format

---

## Q5.8 [AGENT] Fix docs prompt injection delimiters in run_scout
**Mode**: agent
**Target**: onboard.py
**Agent**: security-hardener
**Hypothesis**: `run_scout()` injects docs content directly into the Claude prompt without XML delimiters. Wrapping in `<docs>...</docs>` is a one-line fix that prevents content injection.
**Test**: After fix, `grep -A2 "docs_content" C:/Users/trg16/Dev/autosearch/onboard.py | grep "<docs>"` should match.
**Verdict threshold**:
- HEALTHY: docs_content wrapped in `<docs>` XML tags in the prompt string
- FAILURE: No delimiter present after fix attempt

---

## Q6.6 [AGENT] Fix unbounded rglob calls in detect_stack
**Mode**: agent
**Target**: onboard.py
**Agent**: perf-optimizer
**Hypothesis**: `detect_stack()` uses 4 unbounded `rglob()` calls with no depth limit and no exclusion of `.git`, `node_modules`, `vendor`, `.venv`. On large repos this traverses the entire tree for each pattern, making onboarding slow. Adding depth limits and exclusions will bound the worst-case scan time.
**Test**: After fix, `grep -n "rglob\|glob" C:/Users/trg16/Dev/autosearch/onboard.py | head -20` — confirm exclusion dirs and/or depth limits are applied; run `python onboard.py --help 2>&1 | head -5` to confirm no import errors.
**Verdict threshold**:
- HEALTHY: All rglob calls exclude .git/node_modules/vendor/.venv and/or limit depth to ≤4 levels
- WARNING: Exclusions added but no depth limit (still unbounded on deep trees)
- FAILURE: No change made, or fix introduces import error

---

## Q6.7 [AGENT] Fix dashboard start.sh 0.0.0.0 binding
**Mode**: agent
**Target**: dashboard/start.sh
**Agent**: security-hardener
**Hypothesis**: `start.sh` hardcodes `--host 0.0.0.0` making the dashboard LAN-accessible to non-browser clients even after the CORS restriction. Changing the default to `127.0.0.1` with an opt-in `DASHBOARD_HOST` env var closes the remaining exposure for local-only use.
**Test**: After fix, `grep "uvicorn" C:/Users/trg16/Dev/autosearch/dashboard/start.sh` — should show `${DASHBOARD_HOST:-127.0.0.1}` or equivalent; confirm `DASHBOARD_HOST=0.0.0.0 bash start.sh` syntax is valid.
**Verdict threshold**:
- HEALTHY: Default host is 127.0.0.1; DASHBOARD_HOST env var documented for intentional LAN exposure
- WARNING: Default changed but no env var override path
- FAILURE: Still hardcodes 0.0.0.0 after fix attempt

---

## Q7.1 [CORRECTNESS] _bounded_glob depth limit and exclusions work correctly
**Mode**: correctness
**Target**: onboard.py
**Hypothesis**: `_bounded_glob()` added in Q6.6 uses `relative_to()` which could raise ValueError if the root path is relative; the depth limit might be off-by-one; .git/node_modules exclusions may not propagate correctly.
**Test**: `python -c "from onboard import _bounded_glob; ..."` — verify: (1) .git-only match returns False; (2) node_modules-only match returns False; (3) depth-5 file not found with max_depth=4; (4) relative root Path('.') works.
**Verdict threshold**:
- HEALTHY: All four checks pass
- WARNING: Three pass; one edge case fails but is low-risk
- FAILURE: Any check fails in normal usage

---

## Q7.2 [CORRECTNESS] _bounded_glob no-match base case
**Mode**: correctness
**Target**: onboard.py
**Hypothesis**: `_bounded_glob()` returns False on an empty directory and returns False when no files match, confirming no off-by-one or default-True bug.
**Test**: `python -c "from pathlib import Path; import tempfile; from onboard import _bounded_glob; td = tempfile.mkdtemp(); print(_bounded_glob(Path(td), '*.kt'))"` — expect False.
**Verdict threshold**:
- HEALTHY: Returns False for empty dir and non-matching dir
- FAILURE: Returns True when no match exists

---

## Q7.3 [AGENT] Add tests for _bounded_glob
**Mode**: agent
**Target**: tests/test_core.py
**Agent**: test-writer
**Hypothesis**: The `_bounded_glob()` helper added in Q6.6 has zero automated test coverage. Five tests (match found, .git excluded, node_modules excluded, depth limit, no match) would give regression protection and formally document the exclusion contract.
**Test**: After fix, `python -m pytest tests/ -q 2>&1 | tail -5` — should show ≥24 passing tests.
**Verdict threshold**:
- HEALTHY: ≥5 new tests added, all pass, covering .git exclusion, node_modules exclusion, depth limit, no-match, and basic match
- WARNING: Fewer than 5 tests but at least depth limit and exclusion covered
- FAILURE: Tests added but any fail

---

## Q7.4 [AGENT] Add TTL cache to parse_findings_index
**Mode**: agent
**Target**: dashboard/backend/main.py
**Agent**: perf-optimizer
**Hypothesis**: Q6.3 found that `parse_findings_index()` re-reads all .md files on every API call with no caching. A 5-second TTL cache keyed on project_path would eliminate redundant disk I/O during active dashboard sessions.
**Test**: After fix, `grep -n "cache\|monotonic\|time\." C:/Users/trg16/Dev/autosearch/dashboard/backend/main.py | head -10` — confirm cache logic present; verify `GET /api/findings` still returns correct data.
**Verdict threshold**:
- HEALTHY: TTL cache present; existing API behavior unchanged; no import errors
- WARNING: Cache added but TTL is very short (<1s) or very long (>60s)
- FAILURE: Cache breaks the endpoint or introduces import error

---

## Q8.1 [CORRECTNESS] mypy on dashboard backend (resolve Q2.4)
**Mode**: correctness
**Target**: dashboard/backend/main.py
**Hypothesis**: Q2.4 was INCONCLUSIVE because mypy wasn't installed. Running it now resolves whether the Q4.4 type migration was complete.
**Test**: `pip install mypy --quiet && python -m mypy dashboard/backend/main.py --ignore-missing-imports 2>&1 | tail -5`
**Verdict threshold**:
- HEALTHY: 0 mypy errors
- WARNING: 1–5 type errors
- FAILURE: >5 errors

---

## Q8.2 [CORRECTNESS] bricklayer_launcher.pyw stderr visibility
**Mode**: correctness
**Target**: bricklayer_launcher.pyw
**Hypothesis**: `.pyw` files run with pythonw.exe (no console window), silently dropping all stderr output including the Q4.2 warnings. The fixes are invisible to users.
**Test**: Read `_open_onboard()` — does it spawn onboard.py in a new console window or in the same pythonw process?
**Verdict threshold**:
- HEALTHY: onboard.py launched in a new terminal (wt.exe or cmd.exe /k) so stderr is visible
- FAILURE: onboard.py imported or run in-process with stderr suppressed

---

## Q8.3 [CORRECTNESS] correct_finding does not invalidate _findings_cache
**Mode**: correctness
**Target**: dashboard/backend/main.py
**Hypothesis**: `correct_finding()` appends a Human Correction block to a finding file but never clears `_findings_cache`. A `GET /api/findings` within 5 seconds of a correction returns stale `has_correction: false`.
**Test**: `grep -n "correct_finding\|_findings_cache" dashboard/backend/main.py | head -10` — verify no cache invalidation in correct_finding.
**Verdict threshold**:
- HEALTHY: correct_finding clears the cache entry for the affected project_path
- WARNING: No invalidation but TTL is ≤5s (acceptable lag)
- FAILURE: No invalidation AND TTL is >30s (data looks stale for a long time)

---

## Q8.4 [AGENT] Fix cache invalidation in correct_finding
**Mode**: agent
**Target**: dashboard/backend/main.py
**Agent**: forge
**Hypothesis**: `correct_finding()` should pop `str(project_path)` from `_findings_cache` after writing the correction so the next `GET /api/findings` returns fresh data with `has_correction: true`.
**Test**: After fix, `grep -A5 "def correct_finding" dashboard/backend/main.py | grep "_findings_cache"` — should match.
**Verdict threshold**:
- HEALTHY: Cache invalidated in correct_finding; existing tests still pass
- FAILURE: Fix breaks existing tests or introduces import error

---

## Q6.8 [AGENT] Add API key warning in recall/simulate.py
**Mode**: agent
**Target**: recall/simulate.py
**Agent**: security-hardener
**Hypothesis**: When `BASE_URL != "none"` and `API_KEY == "recall-admin-key-change-me"` (the default placeholder), the runner silently sends the wrong key to a live service, getting a 401 with no helpful error. A one-line stderr warning at startup would surface this misconfiguration immediately.
**Test**: After fix, `python -c "import sys; sys.argv=['simulate.py','--project','fake']; import importlib.util; spec=importlib.util.spec_from_file_location('simulate','C:/Users/trg16/Dev/autosearch/recall/simulate.py')"` should not error; verify warning logic exists with `grep -n "recall-admin-key\|Warning.*api" C:/Users/trg16/Dev/autosearch/recall/simulate.py`.
**Verdict threshold**:
- HEALTHY: Warning printed to stderr when BASE_URL != "none" and API_KEY is the default placeholder
- WARNING: Logic added but warning goes to stdout (acceptable)
- FAILURE: No warning added, or fix introduces traceback

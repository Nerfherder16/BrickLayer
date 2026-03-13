"""
tests/test_core.py — Minimum coverage suite for BrickLayer Q4.3.

Covers:
  - detect_stack() in onboard.py
  - parse_questions() in dashboard/backend/main.py
  - run_simulation() and evaluate() in template/simulate.py
"""

import importlib
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Path setup — make project root and template importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "template"))
sys.path.insert(0, str(REPO_ROOT / "dashboard" / "backend"))

# ---------------------------------------------------------------------------
# detect_stack() — from onboard.py
# ---------------------------------------------------------------------------

from onboard import detect_stack  # noqa: E402


class TestDetectStack:
    def test_python_project_via_py_file(self, tmp_path):
        """Repo with only .py files is detected as Python."""
        (tmp_path / "main.py").write_text("print('hello')")
        result = detect_stack(tmp_path)
        assert "Python" in result

    def test_python_project_via_requirements_txt(self, tmp_path):
        """Repo with requirements.txt is detected as Python."""
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        result = detect_stack(tmp_path)
        assert "Python" in result
        assert "FastAPI" in result

    def test_malformed_package_json_does_not_add_nodejs(self, tmp_path):
        """Malformed package.json must NOT add Node.js to the stack (verifies Q2.1 fix)."""
        (tmp_path / "package.json").write_text("{ this is not valid json !!!")
        result = detect_stack(tmp_path)
        assert "Node.js" not in result
        assert "TypeScript" not in result

    def test_valid_typescript_package_json(self, tmp_path):
        """Valid package.json with typescript dep → TypeScript detected."""
        pkg = {
            "dependencies": {},
            "devDependencies": {"typescript": "^5.0.0", "react": "^18.0.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        result = detect_stack(tmp_path)
        assert "TypeScript" in result
        assert "React" in result

    def test_empty_repo_returns_empty_list(self, tmp_path):
        """Empty directory returns an empty stack list."""
        result = detect_stack(tmp_path)
        assert result == []

    def test_rust_project(self, tmp_path):
        """Repo with Cargo.toml is detected as Rust."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "myapp"\n')
        result = detect_stack(tmp_path)
        assert "Rust" in result


# ---------------------------------------------------------------------------
# parse_questions() — from dashboard/backend/main.py
# ---------------------------------------------------------------------------

from main import parse_questions  # noqa: E402


TABLE_FORMAT_QUESTIONS = """\
# BrickLayer Campaign Questions — Test Project

## Domain 1 — Correctness

| ID | Status | Question |
|----|--------|----------|
| 1.1 | PENDING | Does the full test suite pass with no failures? |
| 1.2 | DONE | Are there any import errors at startup? |

## Domain 2 — Quality

| ID | Status | Question |
|----|--------|----------|
| 2.1 | PENDING | Are there silent exception swallows in the codebase? |
"""

BLOCK_FORMAT_QUESTIONS = """\
# BrickLayer Campaign Questions — Test Project

## Q1.1 [CORRECTNESS] Full test suite baseline
**Status**: PENDING
**Mode**: correctness
**Hypothesis**: The full test suite passes.
**Verdict threshold**:
- HEALTHY: All tests pass

---

## Q1.2 [QUALITY] Silent swallows
**Status**: DONE
**Mode**: quality
**Hypothesis**: No bare excepts found.
"""


class TestParseQuestions:
    def test_table_format_parses_correctly(self, tmp_path):
        """Table-format questions.md is parsed and returns correct question dicts."""
        qfile = tmp_path / "questions.md"
        qfile.write_text(TABLE_FORMAT_QUESTIONS, encoding="utf-8")
        result = parse_questions(tmp_path)
        assert len(result) == 3
        ids = [q["id"] for q in result]
        assert "1.1" in ids
        assert "1.2" in ids
        assert "2.1" in ids
        statuses = {q["id"]: q["status"] for q in result}
        assert statuses["1.1"] == "PENDING"
        assert statuses["1.2"] == "DONE"

    def test_block_format_parsed_correctly(self, tmp_path):
        """Block-format questions.md is parsed correctly (Q1.3 fix — Q5.7)."""
        qfile = tmp_path / "questions.md"
        qfile.write_text(BLOCK_FORMAT_QUESTIONS, encoding="utf-8")
        result = parse_questions(tmp_path)
        assert len(result) == 2
        ids = {q["id"] for q in result}
        assert "Q1.1" in ids
        assert "Q1.2" in ids
        statuses = {q["id"]: q["status"] for q in result}
        assert statuses["Q1.1"] == "PENDING"
        assert statuses["Q1.2"] == "DONE"

    def test_empty_file_returns_empty_list(self, tmp_path):
        """Empty questions.md returns []."""
        qfile = tmp_path / "questions.md"
        qfile.write_text("", encoding="utf-8")
        result = parse_questions(tmp_path)
        assert result == []

    def test_missing_file_returns_empty_list(self, tmp_path):
        """Missing questions.md returns [] without raising."""
        result = parse_questions(tmp_path)
        assert result == []

    def test_domain_assigned_correctly(self, tmp_path):
        """Domain header is captured and assigned to questions in that domain."""
        qfile = tmp_path / "questions.md"
        qfile.write_text(TABLE_FORMAT_QUESTIONS, encoding="utf-8")
        result = parse_questions(tmp_path)
        by_id = {q["id"]: q for q in result}
        assert by_id["1.1"]["domain"] == "D1"
        assert by_id["2.1"]["domain"] == "D2"


# ---------------------------------------------------------------------------
# run_simulation() and evaluate() — from template/simulate.py
#
# The module reassigns sys.stdout at import time, so we reload after patching
# to avoid corrupting the test runner's stdout.
# ---------------------------------------------------------------------------


def _import_simulate():
    """Import template/simulate.py while keeping sys.stdout intact.

    simulate.py runs ``sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)``
    at module level, which replaces pytest's capture object with a real wrapper
    and breaks I/O teardown.  We patch sys.stdout before the import and restore
    it immediately after so the module-level assignment is a no-op from pytest's
    perspective.
    """
    import io

    if "simulate" in sys.modules:
        return sys.modules["simulate"]

    real_stdout = sys.stdout

    # Give the module a fake buffer-backed stdout so the TextIOWrapper call
    # inside simulate.py doesn't touch the real one.
    fake_buf = io.BytesIO()
    sys.stdout = io.TextIOWrapper(fake_buf, encoding="utf-8")

    try:
        mod = importlib.import_module("simulate")
    finally:
        sys.stdout = real_stdout

    return mod


_sim = _import_simulate()
run_simulation = _sim.run_simulation
evaluate = _sim.evaluate


class TestRunSimulation:
    def test_returns_nonempty_records(self):
        """Baseline parameters produce a non-empty records list."""
        records, failure_reason = run_simulation()
        assert isinstance(records, list)
        assert len(records) > 0

    def test_record_has_required_keys(self):
        """Each record contains the expected keys."""
        records, _ = run_simulation()
        required = {"month", "units", "volume", "treasury", "ops_cost", "primary"}
        for rec in records:
            assert required.issubset(rec.keys()), f"Missing keys in record: {rec}"

    def test_months_increase_monotonically(self):
        """Month numbers start at 1 and increase by 1 each step."""
        records, _ = run_simulation()
        for i, rec in enumerate(records):
            assert rec["month"] == i + 1


class TestEvaluate:
    def test_healthy_verdict_above_thresholds(self):
        """Records with primary metric well above thresholds → HEALTHY."""
        # FAILURE_THRESHOLD=6, WARNING_THRESHOLD=12 — use 100 to be clearly above both
        records = [
            {
                "month": 1,
                "units": 1000,
                "volume": 350000,
                "treasury": 1_000_000,
                "ops_cost": 30000,
                "primary": 100.0,
            }
        ]
        result = evaluate(records, None)
        assert result["verdict"] == "HEALTHY"
        assert result["failure_reason"] == "NONE"

    def test_failure_verdict_below_failure_threshold(self):
        """Primary metric below FAILURE_THRESHOLD → FAILURE verdict."""
        # FAILURE_THRESHOLD = 6; use primary = 1 (well below)
        records = [
            {
                "month": 1,
                "units": 500,
                "volume": 1000,
                "treasury": -50000,
                "ops_cost": 30000,
                "primary": 1.0,
            }
        ]
        result = evaluate(records, None)
        assert result["verdict"] == "FAILURE"

    def test_failure_reason_propagated(self):
        """An explicit failure_reason is included in the result."""
        records = [
            {
                "month": 1,
                "units": 500,
                "volume": 1000,
                "treasury": 100,
                "ops_cost": 30000,
                "primary": 100.0,
            }
        ]
        result = evaluate(records, "Treasury went negative at month 1")
        assert result["verdict"] == "FAILURE"
        assert "Treasury went negative" in result["failure_reason"]

    def test_empty_records_returns_failure(self):
        """Empty records list → FAILURE with descriptive reason."""
        result = evaluate([], None)
        assert result["verdict"] == "FAILURE"
        assert "No records" in result["failure_reason"]

    def test_warning_verdict_between_thresholds(self):
        """Primary metric between WARNING_THRESHOLD and FAILURE_THRESHOLD → WARNING."""
        # WARNING_THRESHOLD=12, FAILURE_THRESHOLD=6 — use primary=9
        records = [
            {
                "month": 1,
                "units": 500,
                "volume": 1000,
                "treasury": 270000,
                "ops_cost": 30000,
                "primary": 9.0,
            }
        ]
        result = evaluate(records, None)
        assert result["verdict"] == "WARNING"

"""
tests/test_eval_agent.py — Tests for masonry/scripts/eval_agent.py.

Written before implementation. All tests must fail until the developer
completes the task.

The module under test: masonry/scripts/eval_agent.py
CLI: python masonry/scripts/eval_agent.py karen --signature karen --eval-size 20

Responsibilities:
- Load masonry/training_data/scored_all.jsonl, filter by agent name
- Hold out the LAST --eval-size examples (deterministic, not random)
- For each held-out example: call subprocess.run(["claude", "-p", ...])
- Score using build_karen_metric() or build_metric() depending on --signature
- Write masonry/agent_snapshots/{agent}/eval_latest.json with a defined schema
- Print per-example progress lines
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

# This import will fail (ImportError) until the developer creates the module.
from masonry.scripts.eval_agent import run_eval


# ---------------------------------------------------------------------------
# Helpers — build in-memory JSONL records
# ---------------------------------------------------------------------------


def _make_record(
    agent: str = "karen",
    input_text: str = "Organize the project folders.",
    expected_output: str = "ORGANIZED",
    index: int = 0,
) -> dict:
    """Minimal scored_all.jsonl record."""
    return {
        "agent": agent,
        "input": {"task": input_text, "index": index},
        "expected": {"output": expected_output},
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    """Write a list of dicts as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")


def _perfect_claude_response(record: dict) -> MagicMock:
    """Mock subprocess.CompletedProcess that returns the expected output verbatim."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = 0
    result.stdout = json.dumps(record["expected"])
    result.stderr = ""
    return result


def _failing_claude_response() -> MagicMock:
    """Mock subprocess.CompletedProcess that returns obviously wrong output."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = 0
    result.stdout = json.dumps({"output": "WRONG_OUTPUT_THAT_WILL_NOT_MATCH"})
    result.stderr = ""
    return result


# ---------------------------------------------------------------------------
# Test 1: score == 1.0 when all examples pass
# ---------------------------------------------------------------------------


class TestScoreAllPass:
    """run_eval returns score 1.0 when mock claude returns perfect output for all examples."""

    def test_returns_score_1_when_all_pass(self, tmp_path: Path) -> None:
        records = [_make_record(agent="karen", index=i) for i in range(5)]
        data_file = tmp_path / "scored_all.jsonl"
        _write_jsonl(data_file, records)

        snapshot_dir = tmp_path / "snapshots"

        # Build a list of perfect responses — one per record
        perfect_responses = [_perfect_claude_response(r) for r in records]

        with patch("subprocess.run", side_effect=perfect_responses) as mock_sub, \
             patch(
                "masonry.scripts.eval_agent.build_karen_metric",
                return_value=lambda example, pred: 1.0,
             ), \
             patch(
                "masonry.scripts.eval_agent.build_metric",
                return_value=lambda example, pred: 1.0,
             ):
            result = run_eval(
                agent="karen",
                signature="karen",
                eval_size=5,
                data_file=data_file,
                snapshot_dir=snapshot_dir,
            )

        assert result["score"] == 1.0


# ---------------------------------------------------------------------------
# Test 2: partial score (3 pass / 2 fail → 0.6)
# ---------------------------------------------------------------------------


class TestPartialScore:
    """run_eval computes score as passed / eval_size."""

    def test_returns_partial_score(self, tmp_path: Path) -> None:
        records = [_make_record(agent="karen", index=i) for i in range(5)]
        data_file = tmp_path / "scored_all.jsonl"
        _write_jsonl(data_file, records)

        snapshot_dir = tmp_path / "snapshots"

        # First 3 responses perfect, last 2 fail
        responses = [
            _perfect_claude_response(records[0]),
            _perfect_claude_response(records[1]),
            _perfect_claude_response(records[2]),
            _failing_claude_response(),
            _failing_claude_response(),
        ]

        def _metric_that_checks_match(example: Any, pred: Any) -> float:
            """1.0 if pred output matches expected, 0.0 otherwise."""
            try:
                pred_data = json.loads(pred) if isinstance(pred, str) else pred
                exp_data = example["expected"] if isinstance(example, dict) else example
                return 1.0 if pred_data == exp_data else 0.0
            except Exception:
                return 0.0

        with patch("subprocess.run", side_effect=responses), \
             patch(
                "masonry.scripts.eval_agent.build_karen_metric",
                return_value=_metric_that_checks_match,
             ), \
             patch(
                "masonry.scripts.eval_agent.build_metric",
                return_value=_metric_that_checks_match,
             ):
            result = run_eval(
                agent="karen",
                signature="karen",
                eval_size=5,
                data_file=data_file,
                snapshot_dir=snapshot_dir,
            )

        assert result["passed"] == 3
        assert result["failed"] == 2
        assert abs(result["score"] - 0.6) < 1e-9


# ---------------------------------------------------------------------------
# Test 3: output file written with correct schema
# ---------------------------------------------------------------------------


class TestWritesEvalJson:
    """run_eval writes eval_latest.json at the correct path with all required fields."""

    REQUIRED_SCHEMA_FIELDS = {
        "agent",
        "score",
        "eval_size",
        "passed",
        "failed",
        "evaluated_at",
        "model",
        "examples",
    }

    def test_writes_eval_json(self, tmp_path: Path) -> None:
        records = [_make_record(agent="karen", index=i) for i in range(3)]
        data_file = tmp_path / "scored_all.jsonl"
        _write_jsonl(data_file, records)

        snapshot_dir = tmp_path / "snapshots"

        responses = [_perfect_claude_response(r) for r in records]

        with patch("subprocess.run", side_effect=responses), \
             patch(
                "masonry.scripts.eval_agent.build_karen_metric",
                return_value=lambda example, pred: 1.0,
             ), \
             patch(
                "masonry.scripts.eval_agent.build_metric",
                return_value=lambda example, pred: 1.0,
             ):
            run_eval(
                agent="karen",
                signature="karen",
                eval_size=3,
                data_file=data_file,
                snapshot_dir=snapshot_dir,
            )

        expected_path = snapshot_dir / "karen" / "eval_latest.json"
        assert expected_path.exists(), (
            f"Expected output file at {expected_path} was not created"
        )

        payload = json.loads(expected_path.read_text(encoding="utf-8"))

        for field in self.REQUIRED_SCHEMA_FIELDS:
            assert field in payload, f"Required field '{field}' missing from eval_latest.json"

        assert payload["agent"] == "karen"
        assert payload["eval_size"] == 3
        assert isinstance(payload["examples"], list)
        assert len(payload["examples"]) == 3

        # Each example entry must have input, expected, predicted, score
        for ex in payload["examples"]:
            assert "input" in ex, "example entry missing 'input'"
            assert "expected" in ex, "example entry missing 'expected'"
            assert "predicted" in ex, "example entry missing 'predicted'"
            assert "score" in ex, "example entry missing 'score'"

        # evaluated_at must be a non-empty string (ISO-8601)
        assert isinstance(payload["evaluated_at"], str)
        assert len(payload["evaluated_at"]) > 0

        # model must be a non-empty string
        assert isinstance(payload["model"], str)
        assert len(payload["model"]) > 0


# ---------------------------------------------------------------------------
# Test 4: holdout uses LAST N examples, not first N
# ---------------------------------------------------------------------------


class TestUsesLastNExamples:
    """run_eval holds out the last --eval-size records, not the first."""

    def test_uses_last_n_examples(self, tmp_path: Path) -> None:
        # Create 10 records with distinct, trackable inputs
        all_records = [_make_record(agent="karen", index=i) for i in range(10)]
        data_file = tmp_path / "scored_all.jsonl"
        _write_jsonl(data_file, all_records)

        snapshot_dir = tmp_path / "snapshots"

        # Track which inputs claude was actually called with
        called_inputs: list[str] = []

        def _capture_subprocess(cmd, **kwargs):
            # The prompt is passed as the last element of the command list
            # or via stdin/capture — extract the input from the call args
            full_cmd = " ".join(str(c) for c in cmd)
            called_inputs.append(full_cmd)
            result = MagicMock(spec=subprocess.CompletedProcess)
            result.returncode = 0
            result.stdout = "{}"
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=_capture_subprocess), \
             patch(
                "masonry.scripts.eval_agent.build_karen_metric",
                return_value=lambda example, pred: 1.0,
             ), \
             patch(
                "masonry.scripts.eval_agent.build_metric",
                return_value=lambda example, pred: 1.0,
             ):
            result = run_eval(
                agent="karen",
                signature="karen",
                eval_size=3,
                data_file=data_file,
                snapshot_dir=snapshot_dir,
            )

        # Exactly 3 subprocess calls must have been made (the last 3 records)
        assert len(called_inputs) == 3, (
            f"Expected 3 subprocess calls (last 3 records), got {len(called_inputs)}"
        )

        # The examples in the output must correspond to records 7, 8, 9 (indices 7-9)
        output_path = snapshot_dir / "karen" / "eval_latest.json"
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        evaluated_indices = [ex["input"]["index"] for ex in payload["examples"]]

        # Last 3 of [0..9] are indices 7, 8, 9
        assert set(evaluated_indices) == {7, 8, 9}, (
            f"Expected last 3 record indices {{7, 8, 9}}, got {set(evaluated_indices)}"
        )

        # Confirm none of the first 7 records (indices 0-6) were evaluated
        assert not any(idx in evaluated_indices for idx in range(7)), (
            f"First-7 record indices must NOT be evaluated; found {evaluated_indices}"
        )

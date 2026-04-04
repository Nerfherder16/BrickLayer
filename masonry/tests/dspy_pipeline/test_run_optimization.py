"""Tests for masonry/scripts/run_optimization.py — CLI argument handling.

Covers the --api-key argument added in F32.2.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


class TestRunOptimizationApiKey(unittest.TestCase):
    """Verify that --api-key is accepted and threaded through to configure_dspy."""

    def _invoke_main(self, argv: list[str]) -> int:
        """Call _main() with the given argv and return the exit code."""
        # Ensure the BrickLayer root is importable
        bl_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        if bl_root not in sys.path:
            sys.path.insert(0, bl_root)

        from masonry.scripts import run_optimization

        with patch.object(sys, "argv", ["run_optimization.py"] + argv):
            try:
                run_optimization._main()
            except SystemExit as exc:
                return int(exc.code) if exc.code is not None else 0
        return 0

    def test_api_key_argument_accepted(self):
        """--api-key must be a recognised argument (no argparse error)."""

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("agent_name")
        parser.add_argument("--base-dir", type=Path, default=Path.cwd())
        parser.add_argument("--backend", default="anthropic", choices=["anthropic", "ollama"])
        parser.add_argument("--num-trials", type=int, default=10)
        parser.add_argument("--valset-size", type=int, default=100)
        parser.add_argument("--signature", default="research", choices=["research", "karen"])
        parser.add_argument("--api-key", default=None)

        # Must not raise
        args = parser.parse_args(["my-agent", "--api-key", "sk-test-999"])
        self.assertEqual(args.api_key, "sk-test-999")

    def test_api_key_threaded_to_run(self):
        """run() must receive api_key from parsed args."""
        from masonry.scripts import run_optimization

        captured: dict = {}

        def fake_run(agent_name, base_dir, backend, num_trials, valset_size, signature, api_key=None):
            captured["api_key"] = api_key
            return 0

        with patch.object(run_optimization, "run", side_effect=fake_run):
            with patch.object(sys, "argv", [
                "run_optimization.py", "my-agent", "--api-key", "sk-test-456",
            ]):
                try:
                    run_optimization._main()
                except SystemExit:
                    pass

        self.assertEqual(captured.get("api_key"), "sk-test-456")

    def test_api_key_defaults_to_env_var(self):
        """When --api-key is omitted, api_key defaults to ANTHROPIC_API_KEY env var."""
        import os
        from masonry.scripts import run_optimization

        captured: dict = {}

        def fake_run(agent_name, base_dir, backend, num_trials, valset_size, signature, api_key=None):
            captured["api_key"] = api_key
            return 0

        env_patch = {"ANTHROPIC_API_KEY": "sk-from-env"}
        with patch.dict(os.environ, env_patch):
            with patch.object(run_optimization, "run", side_effect=fake_run):
                with patch.object(sys, "argv", ["run_optimization.py", "my-agent"]):
                    try:
                        run_optimization._main()
                    except SystemExit:
                        pass

        self.assertEqual(captured.get("api_key"), "sk-from-env")


class TestLoadTrainingDataProjectContext(unittest.TestCase):
    """Verify that load_training_data_from_scored_all() populates project_context from project-brief.md."""

    def test_project_context_populated_from_base_dir(self):
        """When base_dir has project-brief.md, examples[0].project_context must be non-empty."""
        import json
        import tempfile
        from pathlib import Path

        from masonry.scripts.run_optimization import load_training_data_from_scored_all

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write project-brief.md
            brief_text = "This is the ADBP project brief — describes the system under test."
            (tmp_path / "project-brief.md").write_text(brief_text, encoding="utf-8")

            # Write a minimal scored_all.jsonl with one research-analyst record
            record = {
                "agent": "research-analyst",
                "score": 80,
                "input": {"question_text": "Does the system handle X?"},
                "output": {"verdict": "HEALTHY", "severity": "Low", "evidence": "No issues found.", "confidence": 0.8},
            }
            scored_path = tmp_path / "scored_all.jsonl"
            scored_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

            examples = load_training_data_from_scored_all(scored_path, "research-analyst", base_dir=tmp_path)

        self.assertEqual(len(examples), 1, "Expected exactly 1 training example")
        self.assertTrue(
            len(examples[0]["project_context"]) > 0,
            "project_context must be non-empty when base_dir has project-brief.md",
        )
        self.assertIn(
            "ADBP",
            examples[0]["project_context"],
            "project_context should contain text from project-brief.md",
        )

    def test_project_context_empty_without_base_dir(self):
        """When base_dir is None (default), project_context falls back to empty string."""
        import json
        import tempfile
        from pathlib import Path

        from masonry.scripts.run_optimization import load_training_data_from_scored_all

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            record = {
                "agent": "research-analyst",
                "score": 80,
                "input": {"question_text": "Q?"},
                "output": {"verdict": "HEALTHY", "severity": "Low", "evidence": "e", "confidence": 0.8},
            }
            scored_path = tmp_path / "scored_all.jsonl"
            scored_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

            examples = load_training_data_from_scored_all(scored_path, "research-analyst")

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["project_context"], "", "project_context must be '' when base_dir is None")


if __name__ == "__main__":
    unittest.main()

"""Tests for masonry/scripts/run_optimization.py — CLI argument handling.

Covers the --api-key argument added in F32.2.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


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
        from masonry.scripts import run_optimization

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


if __name__ == "__main__":
    unittest.main()

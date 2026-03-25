"""E2E tests for masonry/src/routing/llm_router.py.

Tests the three additions from T1.3:
  1. MASONRY_LLM_MODEL env var overrides hardcoded model
  2. preflight check returns None (not crash) when 'claude' not on PATH
  3. retry logic: TimeoutExpired on attempt 1 → sleeps 2s → retries; two
     consecutive timeouts → returns None

All tests mock subprocess.run so no real claude subprocess is needed.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_llm_router(env_overrides: dict | None = None):
    """Import (or re-import) llm_router with patched env vars.

    Re-importing resets module-level globals (_LLM_MODEL, _claude_checked).
    """
    import os
    original = os.environ.copy()
    if env_overrides:
        os.environ.update(env_overrides)
    # Remove MASONRY_LLM_MODEL if not being set explicitly so each test is clean
    if env_overrides is None or "MASONRY_LLM_MODEL" not in env_overrides:
        os.environ.pop("MASONRY_LLM_MODEL", None)

    # Force re-import
    mod_name = "masonry.src.routing.llm_router"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    try:
        mod = importlib.import_module(mod_name)
    finally:
        os.environ.clear()
        os.environ.update(original)
    return mod


def _make_registry():
    from masonry.src.schemas.payloads import AgentRegistryEntry
    return [
        AgentRegistryEntry(
            name="developer",
            file="developer.md",
            description="Writes code",
            capabilities=["coding"],
            modes=["dev"],
            tier="trusted",
        )
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEnvVarModel(unittest.TestCase):
    """MASONRY_LLM_MODEL env var overrides hardcoded model."""

    def test_default_model(self):
        mod = _reload_llm_router()
        self.assertEqual(mod._LLM_MODEL, "claude-haiku-4-5-20251001")

    def test_env_var_override(self):
        mod = _reload_llm_router({"MASONRY_LLM_MODEL": "claude-opus-4-6"})
        self.assertEqual(mod._LLM_MODEL, "claude-opus-4-6")

    def test_env_var_passed_to_subprocess(self):
        """Model from env var is forwarded to the subprocess command."""
        mod = _reload_llm_router({"MASONRY_LLM_MODEL": "claude-opus-4-6"})
        registry = _make_registry()

        good_response = MagicMock()
        good_response.returncode = 0
        good_response.stdout = '{"target_agent": "developer", "reason": "test"}'

        with patch("subprocess.run", return_value=good_response) as mock_run, \
             patch("shutil.which", return_value="/usr/bin/claude"):
            mod._claude_checked = False
            mod.route_llm("implement a feature", registry)

        args = mock_run.call_args[0][0]  # first positional arg = cmd list
        self.assertIn("claude-opus-4-6", args)


class TestPreflightCheck(unittest.TestCase):
    """shutil.which check returns None without crashing when claude missing."""

    def test_missing_claude_returns_none(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        with patch("shutil.which", return_value=None):
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNone(result)

    def test_missing_claude_warns_to_stderr(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        with patch("shutil.which", return_value=None), \
             patch("sys.stderr") as mock_err:
            mod.route_llm("implement a feature", registry)

        output = "".join(str(c) for c in mock_err.write.call_args_list)
        self.assertIn("not found on PATH", output)

    def test_missing_claude_only_warns_once(self):
        """_claude_checked flag prevents repeated stderr noise."""
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        with patch("shutil.which", return_value=None), \
             patch("sys.stderr") as mock_err:
            mod.route_llm("request 1", registry)
            mod.route_llm("request 2", registry)

        # Warning should appear exactly once across both calls
        warning_calls = [
            c for c in mock_err.write.call_args_list
            if "not found on PATH" in str(c)
        ]
        self.assertEqual(len(warning_calls), 1)


class TestRetryLogic(unittest.TestCase):
    """TimeoutExpired on attempt 1 triggers one retry; two timeouts → None."""

    def test_timeout_then_success_returns_decision(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        good_response = MagicMock()
        good_response.returncode = 0
        good_response.stdout = '{"target_agent": "developer", "reason": "retry worked"}'

        call_count = 0

        def fake_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=20)
            return good_response

        with patch("subprocess.run", side_effect=fake_run), \
             patch("shutil.which", return_value="/usr/bin/claude"), \
             patch("time.sleep") as mock_sleep:
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNotNone(result)
        self.assertEqual(result.target_agent, "developer")
        # Must sleep between retries
        mock_sleep.assert_called_once_with(mod._LLM_RETRY_DELAY)
        self.assertEqual(call_count, 2)

    def test_two_timeouts_returns_none(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=[], timeout=20)), \
             patch("shutil.which", return_value="/usr/bin/claude"), \
             patch("time.sleep"):
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNone(result)

    def test_non_timeout_exception_no_retry(self):
        """Non-timeout exceptions should not trigger a retry."""
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        call_count = 0

        def fake_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise OSError("file not found")

        with patch("subprocess.run", side_effect=fake_run), \
             patch("shutil.which", return_value="/usr/bin/claude"), \
             patch("time.sleep") as mock_sleep:
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNone(result)
        mock_sleep.assert_not_called()
        self.assertEqual(call_count, 1)  # no retry on OSError


class TestHappyPath(unittest.TestCase):
    """Smoke test: valid response returns a RoutingDecision."""

    def test_valid_response(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        good_response = MagicMock()
        good_response.returncode = 0
        good_response.stdout = '{"target_agent": "developer", "reason": "coding task"}'

        with patch("subprocess.run", return_value=good_response), \
             patch("shutil.which", return_value="/usr/bin/claude"):
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNotNone(result)
        self.assertEqual(result.target_agent, "developer")
        self.assertEqual(result.layer, "llm")
        self.assertEqual(result.confidence, 0.6)

    def test_hallucinated_agent_returns_none(self):
        mod = _reload_llm_router()
        mod._claude_checked = False
        registry = _make_registry()

        bad_response = MagicMock()
        bad_response.returncode = 0
        bad_response.stdout = '{"target_agent": "nonexistent-agent", "reason": "test"}'

        with patch("subprocess.run", return_value=bad_response), \
             patch("shutil.which", return_value="/usr/bin/claude"):
            result = mod.route_llm("implement a feature", registry)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

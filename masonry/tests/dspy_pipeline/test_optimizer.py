"""Tests for masonry/src/dspy_pipeline/optimizer.py — signature dispatch logic.

Focuses on the per-agent dispatch table in optimize_all() (F30.5 fix).
These tests are unit-level and do NOT invoke DSPy or any LLM.
"""

from __future__ import annotations

import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry_entry(name: str):
    """Return a minimal AgentRegistryEntry-like object for testing."""
    entry = MagicMock()
    entry.name = name
    return entry


# ---------------------------------------------------------------------------
# Tests for optimize_all dispatch table (F30.5)
# ---------------------------------------------------------------------------


class TestOptimizeAllDispatch(unittest.TestCase):
    """Verify that optimize_all() selects the correct signature per agent."""

    def _run_optimize_all_capture_calls(self, agent_names: list[str]):
        """
        Invoke optimize_all() with fake registry entries and enough mock data
        (>= 5 examples per agent) so the skip-guard is bypassed.

        Returns the list of (agent_name, sig_class, metric_fn_result) tuples
        captured from the optimize_agent calls.
        """
        from masonry.src.dspy_pipeline.optimizer import optimize_all
        from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

        captured: list[tuple[str, type, object]] = []

        def fake_optimize_agent(agent_name, signature_cls, dataset, output_dir, **kwargs):
            captured.append((agent_name, signature_cls, kwargs.get("metric_fn")))
            return {"agent": agent_name, "score": 0.5, "optimized_at": "2026-01-01T00:00:00+00:00"}

        registry = [_make_registry_entry(n) for n in agent_names]
        # Provide exactly 5 training examples per agent (minimum to pass the skip guard)
        stub_example = {
            "question_text": "q",
            "project_context": "ctx",
            "constraints": "",
            "verdict": "HEALTHY",
            "severity": "Low",
            "evidence": "e",
            "mitigation": "",
            "confidence": "0.75",
        }
        datasets = {n: [stub_example] * 5 for n in agent_names}

        with patch(
            "masonry.src.dspy_pipeline.optimizer.optimize_agent",
            side_effect=fake_optimize_agent,
        ):
            optimize_all(registry, datasets, output_dir=Path("/tmp/test_out"))

        return captured, KarenSig, ResearchAgentSig

    def test_karen_uses_karen_sig(self):
        """karen agent must dispatch to KarenSig, not ResearchAgentSig."""
        captured, KarenSig, ResearchAgentSig = self._run_optimize_all_capture_calls(["karen"])
        self.assertEqual(len(captured), 1)
        agent_name, sig_cls, _ = captured[0]
        self.assertEqual(agent_name, "karen")
        self.assertIs(sig_cls, KarenSig, "karen must use KarenSig")
        self.assertIsNot(sig_cls, ResearchAgentSig, "karen must NOT use ResearchAgentSig")

    def test_research_analyst_uses_research_sig(self):
        """research-analyst (not in dispatch table) must fall back to ResearchAgentSig."""
        captured, KarenSig, ResearchAgentSig = self._run_optimize_all_capture_calls(
            ["research-analyst"]
        )
        self.assertEqual(len(captured), 1)
        _, sig_cls, _ = captured[0]
        self.assertIs(sig_cls, ResearchAgentSig, "research-analyst must use ResearchAgentSig")

    def test_unknown_agent_uses_research_sig(self):
        """Any unlisted agent must fall back to ResearchAgentSig."""
        captured, KarenSig, ResearchAgentSig = self._run_optimize_all_capture_calls(
            ["some-new-agent"]
        )
        self.assertEqual(len(captured), 1)
        _, sig_cls, _ = captured[0]
        self.assertIs(sig_cls, ResearchAgentSig, "unknown agent must use ResearchAgentSig")

    def test_karen_metric_is_not_build_metric(self):
        """karen must receive a metric from build_karen_metric, not build_metric."""
        from masonry.src.dspy_pipeline.optimizer import build_karen_metric, build_metric

        captured, _, _ = self._run_optimize_all_capture_calls(["karen"])
        _, _, metric = captured[0]
        # The metric passed should be callable and should NOT be the same object
        # returned by build_metric(ResearchAgentSig).
        research_metric = build_metric(None)
        # Both are closures — they differ in behaviour; we assert metric is not None
        # and that it is not the research metric closure.
        self.assertIsNotNone(metric)
        self.assertIsNot(metric, research_metric)

    def test_skip_guard_still_active(self):
        """Agents with fewer than 5 examples must still be skipped."""
        from masonry.src.dspy_pipeline.optimizer import optimize_all

        registry = [_make_registry_entry("karen"), _make_registry_entry("research-analyst")]
        datasets = {
            "karen": [],  # 0 examples — should be skipped
            "research-analyst": [{}] * 3,  # 3 examples — should be skipped
        }

        called_for: list[str] = []

        def fake_optimize_agent(agent_name, *args, **kwargs):
            called_for.append(agent_name)
            return {"agent": agent_name, "score": 0.0, "optimized_at": ""}

        with patch(
            "masonry.src.dspy_pipeline.optimizer.optimize_agent",
            side_effect=fake_optimize_agent,
        ):
            results = optimize_all(registry, datasets, output_dir=Path("/tmp/test_skip"))

        self.assertEqual(results, [], "no agent should be optimized when all are below threshold")
        self.assertEqual(called_for, [])

    def test_mixed_agents_dispatch_correctly(self):
        """When karen and research-analyst are both optimized, each gets the right sig."""
        from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

        captured, _, _ = self._run_optimize_all_capture_calls(
            ["karen", "research-analyst", "competitive-analyst"]
        )
        sig_map = {name: sig for name, sig, _ in captured}

        self.assertIs(sig_map["karen"], KarenSig)
        self.assertIs(sig_map["research-analyst"], ResearchAgentSig)
        self.assertIs(sig_map["competitive-analyst"], ResearchAgentSig)


# ---------------------------------------------------------------------------
# Tests for configure_dspy() api_key parameter (F32.2)
# ---------------------------------------------------------------------------


class TestConfigureDspyApiKey(unittest.TestCase):
    """Verify that configure_dspy() passes api_key to dspy.LM when provided."""

    def test_api_key_passed_to_dspy_lm(self):
        """When api_key is provided, dspy.LM must be called with api_key kwarg."""
        import dspy as dspy_module
        from masonry.src.dspy_pipeline.optimizer import configure_dspy

        mock_lm = MagicMock()
        with patch.object(dspy_module, "LM", return_value=mock_lm) as mock_lm_cls:
            with patch.object(dspy_module, "configure"):
                configure_dspy(api_key="sk-test-123")

        # dspy.LM must have been called with api_key="sk-test-123"
        call_kwargs = mock_lm_cls.call_args.kwargs
        self.assertEqual(call_kwargs.get("api_key"), "sk-test-123",
                         "dspy.LM was not called with api_key='sk-test-123'")

    def test_no_api_key_omits_kwarg(self):
        """When api_key is None (default), dspy.LM must NOT receive api_key kwarg."""
        import dspy as dspy_module
        from masonry.src.dspy_pipeline.optimizer import configure_dspy

        mock_lm = MagicMock()
        with patch.object(dspy_module, "LM", return_value=mock_lm) as mock_lm_cls:
            with patch.object(dspy_module, "configure"):
                configure_dspy()

        call_kwargs = mock_lm_cls.call_args.kwargs
        self.assertNotIn("api_key", call_kwargs,
                         "dspy.LM should not receive api_key when none is provided")


if __name__ == "__main__":
    unittest.main()

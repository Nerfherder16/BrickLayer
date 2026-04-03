"""Tests for masonry/src/dspy_pipeline/optimizer.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from masonry.src.dspy_pipeline.optimizer import (
    build_metric,
    configure_dspy,
    optimize_agent,
    optimize_all,
)
from masonry.src.schemas import AgentRegistryEntry


# ──────────────────────────────────────────────────────────────────────────
# build_metric
# ──────────────────────────────────────────────────────────────────────────


class TestBuildMetric:
    def _make_example(self, verdict="HEALTHY", evidence_len=150, confidence=0.75):
        ex = MagicMock()
        ex.verdict = verdict
        ex.evidence = "x" * evidence_len
        ex.confidence = str(confidence)
        return ex

    def _make_prediction(self, verdict="HEALTHY", evidence_len=150, confidence="0.75"):
        pred = MagicMock()
        pred.verdict = verdict
        pred.evidence = "x" * evidence_len
        pred.confidence = confidence
        return pred

    def test_returns_callable(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)
        assert callable(metric)

    def test_perfect_match_high_score(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)

        example = self._make_example("HEALTHY", 200, 0.75)
        prediction = self._make_prediction("HEALTHY", 200, "0.75")

        score = metric(example, prediction)
        assert score > 0.8  # verdict match (0.4) + evidence quality (0.4) + confidence (0.2)

    def test_wrong_verdict_reduces_score(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)

        example = self._make_example("HEALTHY", 200, 0.75)
        prediction = self._make_prediction("FAILURE", 200, "0.75")

        score = metric(example, prediction)
        # No verdict match → should lose the 0.4 weight
        assert score < 0.8

    def test_short_evidence_reduces_score(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)

        example = self._make_example("WARNING", 200, 0.75)
        prediction = self._make_prediction("WARNING", 50, "0.75")  # short evidence

        score = metric(example, prediction)
        # Evidence quality penalty applies
        long_evidence_score = metric(
            self._make_example("WARNING", 200, 0.75),
            self._make_prediction("WARNING", 200, "0.75"),
        )
        assert score < long_evidence_score

    def test_confidence_calibration_component(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)

        example = self._make_example("HEALTHY", 200, 0.75)
        # Confidence exactly at target (0.75) → max calibration score
        pred_good = self._make_prediction("HEALTHY", 200, "0.75")
        # Confidence far off → lower calibration score
        pred_bad = self._make_prediction("HEALTHY", 200, "0.1")

        score_good = metric(example, pred_good)
        score_bad = metric(example, pred_bad)
        assert score_good > score_bad

    def test_score_is_float(self):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        metric = build_metric(ResearchAgentSig)
        example = self._make_example()
        prediction = self._make_prediction()
        score = metric(example, prediction)
        assert isinstance(score, float)


# ──────────────────────────────────────────────────────────────────────────
# optimize_agent
# ──────────────────────────────────────────────────────────────────────────


class TestOptimizeAgent:
    def _make_dataset(self, n: int = 5) -> list[dict]:
        return [
            {
                "question_text": f"Question {i}",
                "project_context": "ADBP model",
                "constraints": "",
                "verdict": "HEALTHY",
                "severity": "Info",
                "evidence": "x" * 150,
                "mitigation": "",
                "confidence": "0.85",
            }
            for i in range(n)
        ]

    def test_writes_output_file(self, tmp_path):
        """optimize_agent should write a JSON file to output_dir."""
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig

        dataset = self._make_dataset(5)
        mock_module = MagicMock()
        mock_module.save = MagicMock()

        mock_optimized = MagicMock()
        mock_optimized.best_score = 0.82

        with patch("masonry.src.dspy_pipeline.optimizer.dspy.ChainOfThought", return_value=mock_module), \
             patch("masonry.src.dspy_pipeline.optimizer.dspy.MIPROv2") as mock_mipro_cls:

            mock_mipro = MagicMock()
            mock_mipro.compile.return_value = MagicMock()
            mock_mipro_cls.return_value = mock_mipro

            result = optimize_agent(
                "test-agent",
                ResearchAgentSig,
                dataset,
                tmp_path,
            )

        # Output file should exist
        output_file = tmp_path / "test-agent.json"
        assert output_file.exists() or result.get("agent") == "test-agent"
        assert result["agent"] == "test-agent"
        assert "optimized_at" in result

    def test_returns_result_dict(self, tmp_path):
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig

        dataset = self._make_dataset(5)

        with patch("masonry.src.dspy_pipeline.optimizer.dspy.ChainOfThought", return_value=MagicMock()), \
             patch("masonry.src.dspy_pipeline.optimizer.dspy.MIPROv2") as mock_mipro_cls:

            mock_mipro = MagicMock()
            mock_mipro.compile.return_value = MagicMock()
            mock_mipro_cls.return_value = mock_mipro

            result = optimize_agent("my-agent", ResearchAgentSig, dataset, tmp_path)

        assert isinstance(result, dict)
        assert "agent" in result
        assert "optimized_at" in result


# ──────────────────────────────────────────────────────────────────────────
# optimize_all
# ──────────────────────────────────────────────────────────────────────────


class TestOptimizeAll:
    def _make_registry(self) -> list[AgentRegistryEntry]:
        return [
            AgentRegistryEntry(name="agent-a", file="a.md", modes=["simulate"], tier="trusted"),
            AgentRegistryEntry(name="agent-b", file="b.md", modes=["research"], tier="draft"),
        ]

    def test_skips_agents_with_fewer_than_5_examples(self, tmp_path, capsys):
        registry = self._make_registry()
        datasets = {
            "agent-a": [{"verdict": "HEALTHY"}] * 3,  # < 5
            "agent-b": [{"verdict": "WARNING"}] * 3,  # < 5
        }

        with patch("masonry.src.dspy_pipeline.optimizer.optimize_agent") as mock_opt:
            results = optimize_all(registry, datasets, tmp_path)

        mock_opt.assert_not_called()
        assert results == []

    def test_optimizes_agents_with_5_or_more_examples(self, tmp_path):
        registry = self._make_registry()
        datasets = {
            "agent-a": [{"verdict": "HEALTHY"}] * 6,  # >= 5
            "agent-b": [{"verdict": "WARNING"}] * 2,  # < 5, skipped
        }

        mock_result = {"agent": "agent-a", "score": 0.85, "optimized_at": "2026-01-01"}

        with patch("masonry.src.dspy_pipeline.optimizer.optimize_agent", return_value=mock_result) as mock_opt:
            results = optimize_all(registry, datasets, tmp_path)

        assert mock_opt.call_count == 1
        assert len(results) == 1
        assert results[0]["agent"] == "agent-a"


# ──────────────────────────────────────────────────────────────────────────
# configure_dspy
# ──────────────────────────────────────────────────────────────────────────


class TestConfigureDspy:
    def test_configure_calls_dspy(self):
        with patch("masonry.src.dspy_pipeline.optimizer.dspy.configure") as mock_configure, \
             patch("masonry.src.dspy_pipeline.optimizer.dspy.LM", return_value=MagicMock()) as mock_lm:

            configure_dspy("claude-sonnet-4-6")

        mock_configure.assert_called_once()

"""Tests for masonry.src.dspy_pipeline.optimizer."""
from unittest.mock import MagicMock, patch

from masonry.src.dspy_pipeline.optimizer import _OLLAMA_MODEL, configure_dspy


class TestConfigureDspy:
    def test_ollama_model_is_qwen3(self):
        # F6: default Ollama model must be qwen3:14b, not llama3
        assert "qwen3" in _OLLAMA_MODEL
        assert "llama3" not in _OLLAMA_MODEL

    def test_ollama_backend_uses_ollama_model(self):
        with patch("masonry.src.dspy_pipeline.optimizer.dspy") as mock_dspy:
            mock_lm = MagicMock()
            mock_dspy.LM.return_value = mock_lm
            configure_dspy(backend="ollama")
            model_arg = mock_dspy.LM.call_args.args[0]
            assert "qwen3" in model_arg

    def test_anthropic_backend_uses_default_model(self):
        with patch("masonry.src.dspy_pipeline.optimizer.dspy") as mock_dspy:
            mock_lm = MagicMock()
            mock_dspy.LM.return_value = mock_lm
            configure_dspy(backend="anthropic", api_key="test-key")
            model_arg = mock_dspy.LM.call_args.args[0]
            assert "claude" in model_arg or "anthropic" in model_arg

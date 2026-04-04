"""Tests for bl.runners.agent — tmux dispatch integration."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from bl.frontmatter import read_frontmatter_model, strip_frontmatter
from bl.runners.agent import (
    _parse_text_output,
    _summary_from_agent_output,
    _verdict_from_agent_output,
    build_agent_prompt,
    parse_agent_raw,
    run_agent,
    run_agent_wave,
)


# ---------------------------------------------------------------------------
# Unit tests for helpers (unchanged logic, but ensures no regressions)
# ---------------------------------------------------------------------------


class TestStripFrontmatter:
    def test_no_frontmatter(self):
        assert strip_frontmatter("hello world") == "hello world"

    def test_strips_yaml_block(self):
        text = "---\nmodel: opus\n---\nBody text"
        assert strip_frontmatter(text) == "Body text"


class TestReadFrontmatterModel:
    def test_no_frontmatter(self):
        assert read_frontmatter_model("no frontmatter") is None

    def test_reads_model(self):
        text = '---\nmodel: "opus"\n---\nbody'
        result = read_frontmatter_model(text)
        assert result == "claude-opus-4-6"

    def test_unknown_model_passthrough(self):
        text = "---\nmodel: custom-model-id\n---\nbody"
        result = read_frontmatter_model(text)
        assert result == "custom-model-id"


class TestVerdictFromAgentOutput:
    def test_empty_output(self):
        assert _verdict_from_agent_output("any", {}) == "INCONCLUSIVE"

    def test_self_verdict(self):
        assert (
            _verdict_from_agent_output("unknown-agent", {"verdict": "HEALTHY"})
            == "HEALTHY"
        )

    def test_security_hardener_fixed(self):
        assert (
            _verdict_from_agent_output("security-hardener", {"risks_fixed": 3})
            == "HEALTHY"
        )


class TestParseTextOutput:
    def test_commit_extraction(self):
        text = "committed abc1234 then committed def5678"
        result = _parse_text_output("unknown", text)
        assert result.get("changes_committed") == 2

    def test_verdict_line(self):
        text = "verdict: HEALTHY\nsummary: all good"
        result = _parse_text_output("custom-agent", text)
        assert result["verdict"] == "HEALTHY"
        assert result["summary"] == "all good"


class TestSummaryFromAgentOutput:
    def test_empty(self):
        result = _summary_from_agent_output("test", {})
        assert "no structured output" in result

    def test_summary_key(self):
        result = _summary_from_agent_output("test", {"summary": "done"})
        assert result == "done"


# ---------------------------------------------------------------------------
# Integration: run_agent uses spawn_agent/wait_for_agent
# ---------------------------------------------------------------------------


class TestRunAgentTmuxIntegration:
    """Verify run_agent dispatches through bl.tmux instead of raw subprocess."""

    def test_no_agent_name(self):
        result = run_agent({"agent_name": "", "finding": "", "source": ""})
        assert result["verdict"] == "INCONCLUSIVE"
        assert "No agent specified" in result["summary"]

    @patch("bl.runners.agent.wait_for_agent")
    @patch("bl.runners.agent.spawn_agent")
    @patch("bl.runners.agent.cfg")
    def test_calls_spawn_agent(self, mock_cfg, mock_spawn, mock_wait):
        # Set up cfg paths
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "---\nmodel: opus\n---\nDo the thing."
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.agents_dir.glob.return_value = []
        mock_cfg.project_root = Path("/tmp/test-project")
        mock_cfg.recall_src = Path("/tmp/test-project")
        mock_cfg.findings_dir = MagicMock()
        finding_md = MagicMock()
        finding_md.exists.return_value = False
        mock_cfg.findings_dir.__truediv__ = MagicMock(return_value=finding_md)

        mock_spawn.return_value = MagicMock()
        mock_wait.return_value = MagicMock(
            exit_code=0,
            stdout=json.dumps({"result": '```json\n{"verdict": "HEALTHY"}\n```'}),
        )

        run_agent({"agent_name": "test-agent", "finding": "F1", "source": ""})

        mock_spawn.assert_called_once()
        call_kwargs = mock_spawn.call_args
        assert call_kwargs.kwargs["agent_name"] == "test-agent"
        assert "allowed_tools" in call_kwargs.kwargs
        mock_wait.assert_called_once()

    @patch("bl.runners.agent.wait_for_agent")
    @patch("bl.runners.agent.spawn_agent")
    @patch("bl.runners.agent.cfg")
    def test_timeout_returns_inconclusive(self, mock_cfg, mock_spawn, mock_wait):
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "Agent body"
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.project_root = Path("/tmp/test-project")
        mock_cfg.recall_src = Path("/tmp/test-project")
        mock_cfg.findings_dir = MagicMock()
        finding_md = MagicMock()
        finding_md.exists.return_value = False
        mock_cfg.findings_dir.__truediv__ = MagicMock(return_value=finding_md)

        mock_spawn.return_value = MagicMock()
        mock_wait.return_value = MagicMock(exit_code=-1, stdout="")

        result = run_agent({"agent_name": "test-agent", "finding": "", "source": ""})
        assert result["verdict"] == "INCONCLUSIVE"
        assert "timed out" in result["summary"]

    @patch("bl.runners.agent.spawn_agent", side_effect=FileNotFoundError)
    @patch("bl.runners.agent.cfg")
    def test_missing_claude_returns_inconclusive(self, mock_cfg, mock_spawn):
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "Agent body"
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.project_root = Path("/tmp/test-project")
        mock_cfg.recall_src = Path("/tmp/test-project")
        mock_cfg.findings_dir = MagicMock()
        finding_md = MagicMock()
        finding_md.exists.return_value = False
        mock_cfg.findings_dir.__truediv__ = MagicMock(return_value=finding_md)

        result = run_agent({"agent_name": "test-agent", "finding": "", "source": ""})
        assert result["verdict"] == "INCONCLUSIVE"
        assert "not found" in result["summary"]


# ---------------------------------------------------------------------------
# Extracted helpers: build_agent_prompt, parse_agent_raw
# ---------------------------------------------------------------------------


def _mock_cfg_for_prompt():
    """Return a mock cfg suitable for build_agent_prompt tests."""
    mock_cfg = MagicMock()
    agent_md = MagicMock()
    agent_md.exists.return_value = True
    agent_md.read_text.return_value = "---\nmodel: opus\n---\nDo the thing."
    mock_cfg.agents_dir = MagicMock()
    mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=agent_md)
    mock_cfg.project_root = MagicMock()
    doctrine_path = MagicMock()
    doctrine_path.exists.return_value = False
    mock_cfg.project_root.__truediv__ = MagicMock(return_value=doctrine_path)
    mock_cfg.recall_src = Path("/tmp/test-project")
    mock_cfg.findings_dir = MagicMock()
    finding_md = MagicMock()
    finding_md.exists.return_value = False
    mock_cfg.findings_dir.__truediv__ = MagicMock(return_value=finding_md)
    return mock_cfg, agent_md


class TestBuildAgentPrompt:
    def test_raises_on_empty_agent_name(self):
        import pytest

        with pytest.raises(ValueError, match="No agent specified"):
            build_agent_prompt({"agent_name": "", "finding": "", "source": ""})

    @patch("bl.runners.agent.cfg")
    def test_raises_on_missing_agent_file(self, mock_cfg):
        import pytest

        agent_md = MagicMock()
        agent_md.exists.return_value = False
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=agent_md)

        with pytest.raises(ValueError, match="not found"):
            build_agent_prompt(
                {"agent_name": "missing-agent", "finding": "", "source": ""}
            )

    @patch("bl.runners.agent.cfg")
    def test_returns_prompt_and_model(self, mock_cfg):
        cfg_mock, _ = _mock_cfg_for_prompt()
        mock_cfg.agents_dir = cfg_mock.agents_dir
        mock_cfg.project_root = cfg_mock.project_root
        mock_cfg.recall_src = cfg_mock.recall_src
        mock_cfg.findings_dir = cfg_mock.findings_dir

        prompt, model = build_agent_prompt(
            {"agent_name": "test-agent", "finding": "F1", "source": ""}
        )
        assert "Do the thing" in prompt
        assert model == "claude-opus-4-6"

    @patch("bl.runners.agent.cfg")
    def test_includes_finding_context(self, mock_cfg):
        cfg_mock, _ = _mock_cfg_for_prompt()
        mock_cfg.agents_dir = cfg_mock.agents_dir
        mock_cfg.project_root = cfg_mock.project_root
        mock_cfg.recall_src = cfg_mock.recall_src

        finding_md = MagicMock()
        finding_md.exists.return_value = True
        finding_md.read_text.return_value = "## Finding F1\nSome issue found."
        mock_cfg.findings_dir = MagicMock()
        mock_cfg.findings_dir.__truediv__ = MagicMock(return_value=finding_md)

        prompt, _ = build_agent_prompt(
            {"agent_name": "test-agent", "finding": "F1", "source": ""}
        )
        assert "Some issue found" in prompt


class TestParseAgentRaw:
    def test_json_block_extraction(self):
        raw = json.dumps(
            {"result": '```json\n{"verdict": "HEALTHY", "summary": "all good"}\n```'}
        )
        result = parse_agent_raw("test-agent", raw)
        assert result["verdict"] == "HEALTHY"
        assert result["summary"] == "all good"

    def test_text_fallback(self):
        raw = "verdict: HEALTHY\nsummary: looks fine"
        result = parse_agent_raw("custom-agent", raw)
        assert result["verdict"] == "HEALTHY"
        assert result["summary"] == "looks fine"

    def test_empty_raw(self):
        result = parse_agent_raw("test-agent", "")
        assert result["verdict"] == "INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Batch dispatch: run_agent_wave
# ---------------------------------------------------------------------------


class TestRunAgentWave:
    @patch("bl.runners.agent.collect_wave")
    @patch("bl.runners.agent.spawn_wave")
    @patch("bl.runners.agent.cfg")
    def test_wave_dispatches_and_parses(self, mock_cfg, mock_spawn, mock_collect):
        cfg_mock, _ = _mock_cfg_for_prompt()
        mock_cfg.agents_dir = cfg_mock.agents_dir
        mock_cfg.project_root = cfg_mock.project_root
        mock_cfg.recall_src = cfg_mock.recall_src
        mock_cfg.findings_dir = cfg_mock.findings_dir

        mock_spawn.return_value = [MagicMock()]
        mock_collect.return_value = [
            MagicMock(
                exit_code=0,
                stdout=json.dumps(
                    {"result": '```json\n{"verdict": "HEALTHY"}\n```'}
                ),
                duration_ms=3000,
            )
        ]

        questions = [{"agent_name": "test-agent", "finding": "F1", "source": ""}]
        results = run_agent_wave(questions)

        assert len(results) == 1
        assert results[0]["verdict"] == "HEALTHY"
        mock_spawn.assert_called_once()
        mock_collect.assert_called_once()

    def test_invalid_question_returns_inconclusive(self):
        results = run_agent_wave(
            [{"agent_name": "", "finding": "", "source": ""}]
        )
        assert len(results) == 1
        assert results[0]["verdict"] == "INCONCLUSIVE"

    @patch("bl.runners.agent.spawn_wave", side_effect=FileNotFoundError)
    @patch("bl.runners.agent.cfg")
    def test_cli_not_found(self, mock_cfg, mock_spawn):
        cfg_mock, _ = _mock_cfg_for_prompt()
        mock_cfg.agents_dir = cfg_mock.agents_dir
        mock_cfg.project_root = cfg_mock.project_root
        mock_cfg.recall_src = cfg_mock.recall_src
        mock_cfg.findings_dir = cfg_mock.findings_dir

        results = run_agent_wave(
            [{"agent_name": "test-agent", "finding": "", "source": ""}]
        )
        assert len(results) == 1
        assert results[0]["verdict"] == "INCONCLUSIVE"
        assert "not found" in results[0]["summary"].lower()

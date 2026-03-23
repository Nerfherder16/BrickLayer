"""
tests/test_recall_hook.py — Tests for bl/recall_hook.py.

Tests written before implementation. All must fail until developer completes task.

Covers:
  - extract_recall_payload() parsing fenced JSON blocks
  - Fallback to regex **Verdict** extraction
  - None return when neither extraction path succeeds
  - Malformed JSON falls through to regex fallback
  - Correct payload structure: content, domain, tags, importance, durability
  - importance=0.9 for FAILURE_SET verdicts, 0.7 for others
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — make bl/ importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bl.recall_hook import extract_recall_payload  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers — finding text builders
# ---------------------------------------------------------------------------

def _finding_with_json(verdict: str, summary: str | None = None, use_sim_result: bool = False) -> str:
    """Build a finding string that contains a fenced JSON block."""
    payload: dict = {"verdict": verdict}
    if use_sim_result:
        payload["simulation_result"] = "sim result text"
    elif summary is not None:
        payload["summary"] = summary
    import json
    block = json.dumps(payload)
    return f"## Analysis\n\nSome prose here.\n\n```json\n{block}\n```\n\n## Conclusion\nDone."


def _finding_with_verdict_line(verdict: str, evidence: str = "Evidence body here.") -> str:
    """Build a finding string with a **Verdict** markdown line and ## Evidence section."""
    return (
        f"## Overview\n\nSome text.\n\n"
        f"**Verdict**: {verdict}\n\n"
        f"## Evidence\n\n{evidence}\n\n"
        f"## Conclusion\nFin."
    )


def _finding_no_verdict() -> str:
    """Finding with neither a JSON block nor a Verdict line."""
    return "## Overview\n\nThis finding has no verdict information at all."


def _finding_malformed_json_with_verdict(verdict: str) -> str:
    """Fenced JSON block that cannot be parsed, followed by a Verdict line."""
    return (
        "## Analysis\n\n"
        "```json\n"
        '{"verdict": FAILURE, broken json here\n'
        "```\n\n"
        f"**Verdict**: {verdict}\n\n"
        "## Evidence\n\nSome evidence.\n"
    )


# ---------------------------------------------------------------------------
# Tests — JSON block extraction (primary path)
# ---------------------------------------------------------------------------

class TestJsonBlockExtraction:
    def test_failure_verdict_returns_full_payload(self):
        """JSON block with verdict=FAILURE and summary returns a complete payload dict."""
        finding = _finding_with_json(verdict="FAILURE", summary="System collapsed under load.")
        result = extract_recall_payload(
            finding_text=finding,
            agent_name="quantitative-analyst",
            question_id="Q1",
            project="adbp",
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_failure_verdict_importance_is_0_9(self):
        """verdict=FAILURE yields importance=0.9."""
        finding = _finding_with_json(verdict="FAILURE", summary="Collapsed.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q1", "adbp")
        assert result["importance"] == 0.9

    def test_healthy_verdict_importance_is_0_7(self):
        """verdict=HEALTHY yields importance=0.7."""
        finding = _finding_with_json(verdict="HEALTHY", summary="All good.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q2", "adbp")
        assert result is not None
        assert result["importance"] == 0.7

    def test_domain_is_project_bricklayer(self):
        """domain is always '{project}-bricklayer'."""
        finding = _finding_with_json(verdict="HEALTHY", summary="Fine.")
        result = extract_recall_payload(finding, "competitive-analyst", "Q3", "myproject")
        assert result["domain"] == "myproject-bricklayer"

    def test_durability_is_always_durable(self):
        """durability is always 'durable' regardless of verdict."""
        for verdict in ("FAILURE", "HEALTHY", "INCONCLUSIVE"):
            finding = _finding_with_json(verdict=verdict, summary="Some summary.")
            result = extract_recall_payload(finding, "agent", "Q1", "proj")
            assert result["durability"] == "durable", f"failed for verdict={verdict}"

    def test_tags_contain_required_elements(self):
        """tags include 'bricklayer', 'agent:{agent_name}', 'type:finding', 'verdict:{verdict}'."""
        finding = _finding_with_json(verdict="FAILURE", summary="Bad.")
        result = extract_recall_payload(finding, "benchmark-engineer", "Q5", "adbp")
        tags = result["tags"]
        assert "bricklayer" in tags
        assert "agent:benchmark-engineer" in tags
        assert "type:finding" in tags
        assert "verdict:FAILURE" in tags

    def test_content_format(self):
        """content is '{agent_name} {question_id}: verdict={verdict}. {summary}'."""
        finding = _finding_with_json(verdict="FAILURE", summary="System failed at step 3.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q7", "adbp")
        expected_content = "quantitative-analyst Q7: verdict=FAILURE. System failed at step 3."
        assert result["content"] == expected_content

    def test_simulation_result_used_when_summary_absent(self):
        """When JSON has 'simulation_result' but no 'summary', simulation_result is used."""
        finding = _finding_with_json(verdict="HEALTHY", use_sim_result=True)
        result = extract_recall_payload(finding, "benchmark-engineer", "Q9", "adbp")
        assert result is not None
        assert "sim result text" in result["content"]

    def test_inconclusive_verdict_importance_is_0_9(self):
        """verdict=INCONCLUSIVE yields importance=0.9 (member of FAILURE_SET)."""
        finding = _finding_with_json(verdict="INCONCLUSIVE", summary="Could not determine.")
        result = extract_recall_payload(finding, "regulatory-researcher", "Q4", "adbp")
        assert result is not None
        assert result["importance"] == 0.9

    def test_warning_verdict_importance_is_0_7(self):
        """verdict=WARNING (not in FAILURE_SET) yields importance=0.7."""
        finding = _finding_with_json(verdict="WARNING", summary="Moderate risk.")
        result = extract_recall_payload(finding, "competitive-analyst", "Q6", "adbp")
        assert result is not None
        assert result["importance"] == 0.7


# ---------------------------------------------------------------------------
# Tests — Regex fallback path (no JSON block)
# ---------------------------------------------------------------------------

class TestRegexFallback:
    def test_verdict_line_only_returns_payload(self):
        """No JSON block but valid **Verdict**: FAILURE line returns a non-None payload."""
        finding = _finding_with_verdict_line(verdict="FAILURE", evidence="Stress test failed.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q10", "adbp")
        assert result is not None

    def test_verdict_line_failure_importance_is_0_9(self):
        """Fallback extraction with FAILURE verdict yields importance=0.9."""
        finding = _finding_with_verdict_line(verdict="FAILURE", evidence="Evidence text.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q10", "adbp")
        assert result["importance"] == 0.9

    def test_verdict_line_healthy_importance_is_0_7(self):
        """Fallback extraction with HEALTHY verdict yields importance=0.7."""
        finding = _finding_with_verdict_line(verdict="HEALTHY", evidence="Everything passed.")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q11", "adbp")
        assert result["importance"] == 0.7

    def test_fallback_domain_is_project_bricklayer(self):
        """Fallback path still produces domain='{project}-bricklayer'."""
        finding = _finding_with_verdict_line(verdict="FAILURE")
        result = extract_recall_payload(finding, "agent", "Q12", "testproject")
        assert result["domain"] == "testproject-bricklayer"

    def test_fallback_durability_is_durable(self):
        """Fallback path always produces durability='durable'."""
        finding = _finding_with_verdict_line(verdict="FAILURE")
        result = extract_recall_payload(finding, "agent", "Q12", "proj")
        assert result["durability"] == "durable"

    def test_fallback_tags_contain_required_elements(self):
        """Fallback path tags include all required tag strings."""
        finding = _finding_with_verdict_line(verdict="INCONCLUSIVE")
        result = extract_recall_payload(finding, "regulatory-researcher", "Q13", "adbp")
        tags = result["tags"]
        assert "bricklayer" in tags
        assert "agent:regulatory-researcher" in tags
        assert "type:finding" in tags
        assert "verdict:INCONCLUSIVE" in tags

    def test_fallback_content_format(self):
        """Fallback content string matches '{agent_name} {question_id}: verdict={verdict}. {summary}'."""
        evidence = "A" * 300  # longer than 200 chars to test truncation
        finding = _finding_with_verdict_line(verdict="FAILURE", evidence=evidence)
        result = extract_recall_payload(finding, "quantitative-analyst", "Q14", "adbp")
        # summary must be first 200 chars of evidence section
        expected_summary = evidence[:200]
        expected_content = f"quantitative-analyst Q14: verdict=FAILURE. {expected_summary}"
        assert result["content"] == expected_content

    def test_fallback_inconclusive_importance_is_0_9(self):
        """INCONCLUSIVE via fallback path yields importance=0.9."""
        finding = _finding_with_verdict_line(verdict="INCONCLUSIVE")
        result = extract_recall_payload(finding, "agent", "Q15", "proj")
        assert result["importance"] == 0.9


# ---------------------------------------------------------------------------
# Tests — None return cases
# ---------------------------------------------------------------------------

class TestNoneReturn:
    def test_no_json_no_verdict_returns_none(self):
        """Finding with neither JSON block nor Verdict line returns None."""
        finding = _finding_no_verdict()
        result = extract_recall_payload(finding, "agent", "Q1", "proj")
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty finding text returns None."""
        result = extract_recall_payload("", "agent", "Q1", "proj")
        assert result is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only finding text returns None."""
        result = extract_recall_payload("   \n\t  ", "agent", "Q1", "proj")
        assert result is None


# ---------------------------------------------------------------------------
# Tests — Malformed JSON falls back to Verdict line
# ---------------------------------------------------------------------------

class TestMalformedJsonFallback:
    def test_malformed_json_falls_back_to_verdict_line(self):
        """A fenced JSON block that fails to parse falls through to Verdict line extraction."""
        finding = _finding_malformed_json_with_verdict(verdict="FAILURE")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q20", "adbp")
        assert result is not None

    def test_malformed_json_fallback_verdict_is_correct(self):
        """After JSON parse failure, the verdict extracted from Verdict line is used."""
        finding = _finding_malformed_json_with_verdict(verdict="INCONCLUSIVE")
        result = extract_recall_payload(finding, "quantitative-analyst", "Q21", "adbp")
        assert "verdict:INCONCLUSIVE" in result["tags"]

    def test_malformed_json_no_verdict_line_returns_none(self):
        """Malformed JSON with no Verdict line fallback returns None."""
        finding = (
            "## Analysis\n\n"
            "```json\n"
            '{"verdict": BROKEN\n'
            "```\n\n"
            "## Conclusion\nNo verdict here."
        )
        result = extract_recall_payload(finding, "agent", "Q22", "proj")
        assert result is None

    def test_inconclusive_format_error_verdict_captured_in_full(self):
        """INCONCLUSIVE-FORMAT-ERROR (hyphenated verdict) is captured in full via regex fallback."""
        finding = (
            "## Overview\n\n"
            "**Verdict**: INCONCLUSIVE-FORMAT-ERROR\n\n"
            "## Evidence\n\nJSON block was missing from the finding.\n"
        )
        result = extract_recall_payload(finding, "fix-implementer", "Q23", "adbp")
        assert result is not None
        assert "verdict:INCONCLUSIVE-FORMAT-ERROR" in result["tags"]

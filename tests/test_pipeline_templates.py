"""Tests for .pipeline/ named pipeline template YAML files (Task 20)."""

from pathlib import Path

import pytest
import yaml

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

PIPELINE_DIR = PROJECT_ROOT / ".pipeline"

PIPELINE_FILES = [
    "FEATURE-DEV.yml",
    "BUG-FIX.yml",
    "SECURITY-AUDIT.yml",
]

EXPECTED_NAMES = {
    "FEATURE-DEV.yml": "FEATURE-DEV",
    "BUG-FIX.yml": "BUG-FIX",
    "SECURITY-AUDIT.yml": "SECURITY-AUDIT",
}

EXPECTED_FIRST_AGENT = {
    "FEATURE-DEV.yml": "spec-writer",
    "BUG-FIX.yml": "diagnose-analyst",
    "SECURITY-AUDIT.yml": "security",
}

EXPECTED_LAST_AGENT = {
    "FEATURE-DEV.yml": "pr-writer",
    "BUG-FIX.yml": "pr-writer",
    "SECURITY-AUDIT.yml": "pr-writer",
}

EXPECTED_ON_FAILURE = {
    "FEATURE-DEV.yml": "diagnose-analyst",
    "BUG-FIX.yml": "parallel-debugger",
    "SECURITY-AUDIT.yml": "security",
}


@pytest.fixture(params=PIPELINE_FILES)
def pipeline_data(request):
    """Load and return parsed YAML for each pipeline file."""
    fname = request.param
    fpath = PIPELINE_DIR / fname
    assert fpath.exists(), f"Pipeline file not found: {fpath}"
    data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
    return fname, data


class TestPipelineFilesExist:
    def test_pipeline_dir_exists(self):
        assert PIPELINE_DIR.is_dir(), ".pipeline/ directory must exist"

    @pytest.mark.parametrize("fname", PIPELINE_FILES)
    def test_file_exists(self, fname):
        assert (PIPELINE_DIR / fname).exists(), f"{fname} must exist in .pipeline/"


class TestPipelineStructure:
    def test_has_name(self, pipeline_data):
        fname, data = pipeline_data
        assert "name" in data, f"{fname}: missing 'name' key"
        assert isinstance(data["name"], str)
        assert data["name"] == EXPECTED_NAMES[fname]

    def test_has_description(self, pipeline_data):
        fname, data = pipeline_data
        assert "description" in data, f"{fname}: missing 'description' key"
        assert isinstance(data["description"], str)
        assert len(data["description"]) > 0

    def test_has_stages(self, pipeline_data):
        fname, data = pipeline_data
        assert "stages" in data, f"{fname}: missing 'stages' key"
        assert isinstance(data["stages"], list), f"{fname}: 'stages' must be a list"
        assert len(data["stages"]) > 0, f"{fname}: 'stages' must not be empty"

    def test_has_on_failure(self, pipeline_data):
        fname, data = pipeline_data
        assert "on_failure" in data, f"{fname}: missing 'on_failure' key"
        assert isinstance(data["on_failure"], str)
        assert data["on_failure"] == EXPECTED_ON_FAILURE[fname]

    def test_stages_have_agent(self, pipeline_data):
        fname, data = pipeline_data
        for i, stage in enumerate(data["stages"]):
            assert "agent" in stage, f"{fname}: stage[{i}] missing 'agent' key"
            assert isinstance(stage["agent"], str)
            assert len(stage["agent"]) > 0

    def test_stages_have_description(self, pipeline_data):
        fname, data = pipeline_data
        for i, stage in enumerate(data["stages"]):
            assert "description" in stage, (
                f"{fname}: stage[{i}] missing 'description' key"
            )
            assert isinstance(stage["description"], str)

    def test_first_agent(self, pipeline_data):
        fname, data = pipeline_data
        first_agent = data["stages"][0]["agent"]
        assert first_agent == EXPECTED_FIRST_AGENT[fname], (
            f"{fname}: first agent should be '{EXPECTED_FIRST_AGENT[fname]}', got '{first_agent}'"
        )

    def test_last_agent_is_pr_writer(self, pipeline_data):
        fname, data = pipeline_data
        last_agent = data["stages"][-1]["agent"]
        assert last_agent == EXPECTED_LAST_AGENT[fname], (
            f"{fname}: last agent should be '{EXPECTED_LAST_AGENT[fname]}', got '{last_agent}'"
        )


class TestFeatureDevPipeline:
    @pytest.fixture()
    def data(self):
        return yaml.safe_load(
            (PIPELINE_DIR / "FEATURE-DEV.yml").read_text(encoding="utf-8")
        )

    def test_has_five_stages(self, data):
        assert len(data["stages"]) == 5

    def test_stage_order(self, data):
        agents = [s["agent"] for s in data["stages"]]
        assert agents == [
            "spec-writer",
            "test-writer",
            "developer",
            "code-reviewer",
            "pr-writer",
        ]

    def test_spec_writer_outputs_spec(self, data):
        stage = data["stages"][0]
        assert "outputs" in stage
        assert ".autopilot/spec.md" in stage["outputs"]

    def test_test_writer_inputs_spec(self, data):
        stage = data["stages"][1]
        assert "inputs" in stage
        assert ".autopilot/spec.md" in stage["inputs"]

    def test_code_reviewer_has_on_failure(self, data):
        reviewer_stage = next(
            s for s in data["stages"] if s["agent"] == "code-reviewer"
        )
        assert "on_failure" in reviewer_stage
        assert reviewer_stage["on_failure"] == "developer"


class TestBugFixPipeline:
    @pytest.fixture()
    def data(self):
        return yaml.safe_load(
            (PIPELINE_DIR / "BUG-FIX.yml").read_text(encoding="utf-8")
        )

    def test_has_five_stages(self, data):
        assert len(data["stages"]) == 5

    def test_stage_order(self, data):
        agents = [s["agent"] for s in data["stages"]]
        assert agents == [
            "diagnose-analyst",
            "fix-implementer",
            "code-reviewer",
            "peer-reviewer",
            "pr-writer",
        ]

    def test_diagnose_analyst_outputs_diagnosis(self, data):
        stage = data["stages"][0]
        assert "outputs" in stage
        assert ".autopilot/diagnosis.md" in stage["outputs"]

    def test_fix_implementer_inputs_diagnosis(self, data):
        stage = data["stages"][1]
        assert "inputs" in stage
        assert ".autopilot/diagnosis.md" in stage["inputs"]

    def test_code_reviewer_on_failure_is_fix_implementer(self, data):
        reviewer_stage = next(
            s for s in data["stages"] if s["agent"] == "code-reviewer"
        )
        assert "on_failure" in reviewer_stage
        assert reviewer_stage["on_failure"] == "fix-implementer"


class TestSecurityAuditPipeline:
    @pytest.fixture()
    def data(self):
        return yaml.safe_load(
            (PIPELINE_DIR / "SECURITY-AUDIT.yml").read_text(encoding="utf-8")
        )

    def test_has_four_stages(self, data):
        assert len(data["stages"]) == 4

    def test_stage_order(self, data):
        agents = [s["agent"] for s in data["stages"]]
        assert agents == [
            "security",
            "code-reviewer",
            "compliance-auditor",
            "pr-writer",
        ]

    def test_security_outputs_findings(self, data):
        stage = data["stages"][0]
        assert "outputs" in stage
        assert ".autopilot/security-findings.md" in stage["outputs"]

    def test_code_reviewer_has_security_mode(self, data):
        reviewer_stage = next(
            s for s in data["stages"] if s["agent"] == "code-reviewer"
        )
        assert "mode" in reviewer_stage
        assert reviewer_stage["mode"] == "security"

    def test_code_reviewer_inputs_findings(self, data):
        reviewer_stage = next(
            s for s in data["stages"] if s["agent"] == "code-reviewer"
        )
        assert "inputs" in reviewer_stage
        assert ".autopilot/security-findings.md" in reviewer_stage["inputs"]

    def test_compliance_auditor_inputs_findings(self, data):
        auditor_stage = next(
            s for s in data["stages"] if s["agent"] == "compliance-auditor"
        )
        assert "inputs" in auditor_stage
        assert ".autopilot/security-findings.md" in auditor_stage["inputs"]

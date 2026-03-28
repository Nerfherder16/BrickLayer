"""Tests for 7 marketing skill files in ~/.claude/skills/ (Task 32)."""

from pathlib import Path

import pytest
import yaml

SKILLS_DIR = Path.home() / ".claude" / "skills"

MARKETING_SKILLS = [
    "copy-writer",
    "email-campaign",
    "seo-optimizer",
    "social-content",
    "launch-checklist",
    "competitor-teardown",
    "growth-experiment",
]

EXPECTED_TRIGGERS = {
    "copy-writer": "/copy-writer",
    "email-campaign": "/email-campaign",
    "seo-optimizer": "/seo-optimizer",
    "social-content": "/social-content",
    "launch-checklist": "/launch-checklist",
    "competitor-teardown": "/competitor-teardown",
    "growth-experiment": "/growth-experiment",
}


def _parse_frontmatter(skill_name: str):
    """Parse YAML frontmatter from a skill's SKILL.md."""
    skill_file = SKILLS_DIR / skill_name / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{skill_name}/SKILL.md must start with YAML frontmatter (---)"
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{skill_name}/SKILL.md frontmatter not properly closed"
    fm = yaml.safe_load(parts[1])
    body = parts[2]
    return fm, body


class TestSkillDirectoriesExist:
    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_skill_dir_exists(self, skill_name):
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.is_dir(), (
            f"Skill directory not found: {skill_dir}"
        )

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_skill_md_exists(self, skill_name):
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.is_file(), (
            f"SKILL.md not found: {skill_file}"
        )


class TestSkillFrontmatter:
    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_frontmatter_parseable(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        assert fm is not None, f"{skill_name}: frontmatter parsed to None"
        assert isinstance(fm, dict), f"{skill_name}: frontmatter must be a YAML mapping"

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_has_name_field(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        assert "name" in fm, f"{skill_name}: frontmatter missing 'name' field"
        assert isinstance(fm["name"], str), f"{skill_name}: 'name' must be a string"
        assert len(fm["name"]) > 0, f"{skill_name}: 'name' must not be empty"

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_has_description_field(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        assert "description" in fm, f"{skill_name}: frontmatter missing 'description' field"
        assert isinstance(fm["description"], str), f"{skill_name}: 'description' must be a string"
        assert len(fm["description"]) > 0, f"{skill_name}: 'description' must not be empty"

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_has_triggers_field(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        assert "triggers" in fm, f"{skill_name}: frontmatter missing 'triggers' field"
        triggers = fm["triggers"]
        assert isinstance(triggers, list), f"{skill_name}: 'triggers' must be a list"
        assert len(triggers) > 0, f"{skill_name}: 'triggers' must not be empty"

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_trigger_includes_slash_command(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        expected = EXPECTED_TRIGGERS[skill_name]
        triggers = fm["triggers"]
        assert expected in triggers, (
            f"{skill_name}: triggers must include '{expected}', got {triggers}"
        )

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_name_matches_skill_dir(self, skill_name):
        fm, _ = _parse_frontmatter(skill_name)
        assert fm["name"] == skill_name, (
            f"{skill_name}: 'name' field ('{fm['name']}') must match directory name ('{skill_name}')"
        )


class TestSkillBody:
    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_body_has_content(self, skill_name):
        _, body = _parse_frontmatter(skill_name)
        assert len(body.strip()) > 200, (
            f"{skill_name}: body content must be substantial (> 200 chars)"
        )

    @pytest.mark.parametrize("skill_name", MARKETING_SKILLS)
    def test_body_has_heading(self, skill_name):
        _, body = _parse_frontmatter(skill_name)
        assert "#" in body, f"{skill_name}: body must contain at least one heading"

    def test_copy_writer_has_cta_content(self):
        _, body = _parse_frontmatter("copy-writer")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["cta", "call to action", "headline", "value prop"]), (
            "copy-writer: body must reference CTAs, headlines, or value propositions"
        )

    def test_email_campaign_has_subject_line_content(self):
        _, body = _parse_frontmatter("email-campaign")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["subject line", "drip", "sequence", "a/b"]), (
            "email-campaign: body must reference subject lines, drip sequences, or A/B tests"
        )

    def test_seo_optimizer_has_keyword_content(self):
        _, body = _parse_frontmatter("seo-optimizer")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["keyword", "meta", "seo", "search"]), (
            "seo-optimizer: body must reference keywords, meta tags, or SEO"
        )

    def test_social_content_has_platform_content(self):
        _, body = _parse_frontmatter("social-content")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["twitter", "linkedin", "hashtag", "platform"]), (
            "social-content: body must reference social platforms or hashtags"
        )

    def test_launch_checklist_has_phases(self):
        _, body = _parse_frontmatter("launch-checklist")
        body_lower = body.lower()
        assert "pre-launch" in body_lower or "pre launch" in body_lower, (
            "launch-checklist: body must include pre-launch phase"
        )
        assert "launch day" in body_lower or "launch-day" in body_lower, (
            "launch-checklist: body must include launch day phase"
        )
        assert "post-launch" in body_lower or "post launch" in body_lower, (
            "launch-checklist: body must include post-launch phase"
        )

    def test_competitor_teardown_has_analysis_content(self):
        _, body = _parse_frontmatter("competitor-teardown")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["feature matrix", "positioning", "competitor", "gap"]), (
            "competitor-teardown: body must reference feature matrix, positioning, or gap analysis"
        )

    def test_growth_experiment_has_framework(self):
        _, body = _parse_frontmatter("growth-experiment")
        body_lower = body.lower()
        assert any(term in body_lower for term in ["aarrr", "hypothesis", "experiment", "growth"]), (
            "growth-experiment: body must reference AARRR, hypothesis, or experiment framework"
        )

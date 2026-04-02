"""Tests for CI/CD workflow configuration files."""

import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"

FAST_CHECK = WORKFLOWS_DIR / "fast-check.yml"
INTEGRATION = WORKFLOWS_DIR / "integration.yml"
BUILD_CHECK = WORKFLOWS_DIR / "build-check.yml"


def test_fast_check_workflow_exists():
    assert FAST_CHECK.exists(), f"Missing: {FAST_CHECK}"


def test_integration_workflow_exists():
    assert INTEGRATION.exists(), f"Missing: {INTEGRATION}"


def test_build_check_workflow_exists():
    assert BUILD_CHECK.exists(), f"Missing: {BUILD_CHECK}"


def test_fast_check_triggers_on_feat_branches():
    data = yaml.safe_load(FAST_CHECK.read_text())
    # PyYAML parses bare `on:` as boolean True; try both keys
    trigger = data.get("on") or data.get(True)
    assert trigger is not None, "fast-check.yml missing 'on' trigger block"
    branches = trigger["push"]["branches"]
    assert any("feat" in b for b in branches), (
        f"fast-check.yml push branches should include feat/**: {branches}"
    )


def test_integration_has_postgres_service():
    data = yaml.safe_load(INTEGRATION.read_text())
    services = None
    for job_name, job in data.get("jobs", {}).items():
        if "services" in job:
            services = job["services"]
            break
    assert services is not None, "integration.yml has no job with services"
    assert "postgres" in services, f"integration.yml missing postgres service: {list(services.keys())}"


def test_integration_has_redis_service():
    data = yaml.safe_load(INTEGRATION.read_text())
    services = None
    for job_name, job in data.get("jobs", {}).items():
        if "services" in job:
            services = job["services"]
            break
    assert services is not None, "integration.yml has no job with services"
    assert "redis" in services, f"integration.yml missing redis service: {list(services.keys())}"


def test_build_check_references_docker_compose_build():
    content = BUILD_CHECK.read_text()
    assert "docker compose build" in content, (
        "build-check.yml does not reference 'docker compose build'"
    )


def test_fast_check_references_bandit():
    # bandit may appear in fast-check.yml or any workflow
    for wf in [FAST_CHECK, INTEGRATION, BUILD_CHECK]:
        if wf.exists() and "bandit" in wf.read_text():
            return
    raise AssertionError("No workflow references 'bandit' security scanner")


def test_fast_check_references_trufflehog():
    for wf in [FAST_CHECK, INTEGRATION, BUILD_CHECK]:
        if wf.exists() and "trufflehog" in wf.read_text().lower():
            return
    raise AssertionError("No workflow references 'trufflehog' secret scanner")

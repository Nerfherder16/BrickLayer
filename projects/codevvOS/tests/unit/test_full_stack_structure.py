"""
Unit test: verifies the Phase 1 graduation test scaffold exists and is structurally correct.
Does NOT require Docker or a running stack.
"""
import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPOSE_TEST = os.path.join(PROJECT_ROOT, "docker-compose.test.yml")
INTEGRATION_TEST = os.path.join(PROJECT_ROOT, "tests", "integration", "test_full_stack.py")


def test_docker_compose_test_yml_exists():
    assert os.path.isfile(COMPOSE_TEST), f"Missing: {COMPOSE_TEST}"


def test_integration_test_file_exists():
    assert os.path.isfile(INTEGRATION_TEST), f"Missing: {INTEGRATION_TEST}"


def test_integration_test_contains_test_all_services_healthy():
    with open(INTEGRATION_TEST) as f:
        content = f.read()
    assert "test_all_services_healthy" in content


def test_integration_test_contains_test_login_flow():
    with open(INTEGRATION_TEST) as f:
        content = f.read()
    assert "test_login_flow" in content


def test_integration_test_contains_test_authenticated_file_tree():
    with open(INTEGRATION_TEST) as f:
        content = f.read()
    assert "test_authenticated_file_tree" in content


def test_docker_compose_test_yml_is_valid_yaml():
    with open(COMPOSE_TEST) as f:
        data = yaml.safe_load(f)
    assert data is not None, "docker-compose.test.yml parsed as empty"
    assert "services" in data, "docker-compose.test.yml missing 'services' key"

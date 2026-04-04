import sys
from pathlib import Path
import pytest

_root = Path(__file__).parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "backend"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests that require a running compose stack",
    )

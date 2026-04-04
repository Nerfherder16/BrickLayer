# TDD enforcer shim — delegates to the full schema test suite at repo root.
# Run with: python -m pytest masonry/tests/test_mas_schemas.py --capture=no -q
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.test_mas_schemas import *  # noqa: F401, F403

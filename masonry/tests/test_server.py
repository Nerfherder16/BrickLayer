# TDD enforcer shim — delegates to the full MCP server test suites at repo root.
# Run with: python -m pytest masonry/tests/test_server.py --capture=no -q
import sys
from pathlib import Path

# Ensure repo root is importable
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.test_mcp_mas_status import *  # noqa: F401, F403
from tests.test_mcp_new_tools import *   # noqa: F401, F403

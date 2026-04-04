# TDD enforcer shim — delegates to the full MCP server test suites.
# Run with: python -m pytest tests/test_server.py --capture=no -q
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import all test classes so pytest discovers them
from test_mcp_mas_status import *   # noqa: F401, F403
from test_mcp_new_tools import *    # noqa: F401, F403

# TDD enforcer shim — delegates to the full MCP server test suites.
# Run with: python -m pytest tests/test_server.py --capture=no -q
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Add tests/ dir so sibling test modules are importable
_TESTS_DIR = str(Path(__file__).parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

# Import all test classes so pytest discovers them
from test_mcp_mas_status import *   # noqa: F401, F403
from test_mcp_new_tools import *    # noqa: F401, F403

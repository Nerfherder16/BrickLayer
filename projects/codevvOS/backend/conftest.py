"""Backend-scoped test configuration — makes the project root importable as 'backend.*'."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add the project root (parent of backend/) so `backend.app.*` imports resolve
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Stub neo4j before any app module imports it (driver not installed in test env)
_neo4j_stub = MagicMock()
_neo4j_stub.AsyncGraphDatabase = MagicMock()
sys.modules.setdefault("neo4j", _neo4j_stub)

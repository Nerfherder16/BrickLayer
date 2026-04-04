"""Compute a content hash of simulate.py + constants.py for finding correlation."""
import hashlib
from pathlib import Path


def compute_model_hash(project_root) -> str:
    """SHA-256 of simulate.py + constants.py content, first 12 hex chars.
    Returns 'no-model' if neither file exists."""
    root = Path(project_root)
    content = b""
    found = False
    for f in [root / "simulate.py", root / "constants.py"]:
        if f.exists():
            content += f.read_bytes()
            found = True
    return "no-model" if not found else hashlib.sha256(content).hexdigest()[:12]


def embed_in_finding(content: str, model_hash: str) -> str:
    """Append '**Model hash**: {hash}' to finding content if not already present."""
    if "**Model hash**:" in content:
        return content
    return content.rstrip() + f"\n\n**Model hash**: {model_hash}\n"

"""onboard.py — Stack detection for BrickLayer projects."""

from __future__ import annotations

import json
from pathlib import Path


_EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def _bounded_glob(path: Path, pattern: str, max_depth: int = 4) -> bool:
    """Return True if any file matching `pattern` exists within `max_depth` levels.

    Excludes .git and node_modules directories.
    """

    def _walk(current: Path, depth: int) -> bool:
        if depth > max_depth:
            return False
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    if entry.name in _EXCLUDED_DIRS:
                        continue
                    if _walk(entry, depth + 1):
                        return True
                elif entry.is_file():
                    if entry.match(pattern):
                        return True
        except PermissionError:
            pass
        return False

    return _walk(path, 0)


def detect_stack(path: Path) -> list[str]:
    """Detect the technology stack present in `path`.

    Returns a list of technology names such as "Python", "FastAPI",
    "TypeScript", "React", "Vue", "Node.js", "Rust", "Go".
    """
    stack: list[str] = []

    # Python detection
    has_py = _bounded_glob(path, "*.py")
    req_txt = path / "requirements.txt"
    if has_py or req_txt.exists():
        stack.append("Python")
        if req_txt.exists():
            content = req_txt.read_text(encoding="utf-8", errors="replace").lower()
            if "fastapi" in content:
                stack.append("FastAPI")

    # Node.js / TypeScript / React / Vue via package.json
    pkg_json = path / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pkg = None

        if pkg is not None:
            stack.append("Node.js")
            all_deps: dict[str, str] = {}
            all_deps.update(pkg.get("dependencies") or {})
            all_deps.update(pkg.get("devDependencies") or {})
            lower_deps = {k.lower(): v for k, v in all_deps.items()}
            if "typescript" in lower_deps:
                stack.append("TypeScript")
            if "react" in lower_deps:
                stack.append("React")
            if "vue" in lower_deps:
                stack.append("Vue")

    # Rust
    if (path / "Cargo.toml").exists():
        stack.append("Rust")

    # Go
    if (path / "go.mod").exists():
        stack.append("Go")

    return stack

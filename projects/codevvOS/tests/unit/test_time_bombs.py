"""Tests for known time bomb mitigations (Task 0.13)."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_bricklayer_entrypoint_exists():
    """docker/bricklayer/entrypoint.sh must exist."""
    entrypoint = PROJECT_ROOT / "docker" / "bricklayer" / "entrypoint.sh"
    assert entrypoint.exists(), (
        "docker/bricklayer/entrypoint.sh is missing — "
        "BrickLayer needs an entrypoint that starts tmux before uvicorn"
    )


def test_bricklayer_entrypoint_starts_tmux():
    """entrypoint.sh must start a tmux session before uvicorn.

    spawn_agent() calls `tmux new-session` internally; if the tmux server
    isn't running the first call will fail silently inside the container.
    """
    entrypoint = PROJECT_ROOT / "docker" / "bricklayer" / "entrypoint.sh"
    assert entrypoint.exists(), "entrypoint.sh does not exist"
    content = entrypoint.read_text()
    assert "tmux new-session" in content, (
        "entrypoint.sh must call 'tmux new-session' to pre-start the tmux "
        "server before uvicorn launches"
    )


def test_yjs_dockerfile_uses_node22_alpine():
    """docker/yjs/Dockerfile must use node:22-alpine as base image.

    y-websocket requires Node.js 22+ for native ESM support.  Using an
    unpinned 'node:alpine' tag risks a future breaking upgrade.
    """
    dockerfile = PROJECT_ROOT / "docker" / "yjs" / "Dockerfile"
    assert dockerfile.exists(), "docker/yjs/Dockerfile is missing"
    content = dockerfile.read_text()
    # Accept node:22-alpine or node:22 (exact pin is fine either way)
    assert "node:22" in content, (
        "docker/yjs/Dockerfile must pin to node:22 (e.g. FROM node:22-alpine); "
        "found: " + content.splitlines()[0]
    )

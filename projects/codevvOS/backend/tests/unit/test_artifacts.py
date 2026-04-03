"""Unit tests for POST /api/artifacts/compile endpoint."""
from __future__ import annotations

import shutil
import subprocess
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client() -> TestClient:
    from backend.app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 400 — empty JSX
# ---------------------------------------------------------------------------


def test_compile_empty_jsx_returns_400() -> None:
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
    ) as mock_compile:
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": "", "dependencies": []},
        )
    assert response.status_code == 400
    mock_compile.assert_not_called()


def test_compile_whitespace_only_jsx_returns_400() -> None:
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
    ) as mock_compile:
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": "   \n\t  ", "dependencies": []},
        )
    assert response.status_code == 400
    mock_compile.assert_not_called()


# ---------------------------------------------------------------------------
# 413 — JSX > 50 KB
# ---------------------------------------------------------------------------


def test_compile_jsx_over_50kb_returns_413() -> None:
    big_jsx = "x" * (50 * 1024 + 1)
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
    ) as mock_compile:
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": big_jsx, "dependencies": []},
        )
    assert response.status_code == 413
    mock_compile.assert_not_called()


# ---------------------------------------------------------------------------
# 400 — dependency not in allowlist
# ---------------------------------------------------------------------------


def test_compile_disallowed_dependency_returns_400() -> None:
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
    ) as mock_compile:
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": "const x = 1;", "dependencies": ["lodash"]},
        )
    assert response.status_code == 400
    assert "lodash" in response.json()["detail"]
    mock_compile.assert_not_called()


# ---------------------------------------------------------------------------
# 200 — valid JSX → compiled output contains React.createElement
# ---------------------------------------------------------------------------


def test_compile_valid_jsx_returns_react_create_element() -> None:
    compiled_output = "React.createElement('div', null, 'hello')"
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
        return_value=(compiled_output, None),
    ):
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": "<div>hello</div>", "dependencies": ["react"]},
        )
    assert response.status_code == 200
    data = response.json()
    assert "React.createElement" in data["compiled"]
    assert data["error"] is None


# ---------------------------------------------------------------------------
# 200 — JSX syntax error → error field populated, not 500
# ---------------------------------------------------------------------------


def test_compile_jsx_syntax_error_returns_200_with_error_field() -> None:
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
        return_value=(None, "Transform failed: unexpected token"),
    ):
        client = _make_client()
        response = client.post(
            "/api/artifacts/compile",
            json={"jsx": "<div>unclosed", "dependencies": []},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["compiled"] is None
    assert data["error"] is not None
    assert len(data["error"]) > 0


# ---------------------------------------------------------------------------
# esbuild binary callable (skipped if not installed)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    shutil.which("esbuild") is None,
    reason="esbuild not in PATH",
)
def test_esbuild_binary_is_callable() -> None:
    result = subprocess.run(
        ["esbuild", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

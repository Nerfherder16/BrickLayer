"""
Task 0.2 — Security Decisions Codified as Configuration
Tests verify security constants exist and stub functions raise NotImplementedError.
Written BEFORE production stubs are created — will fail until stubs are in place.
"""

import pytest


def test_jwt_algorithm_is_hs256():
    from backend.app.core.security import JWT_ALGORITHM

    assert JWT_ALGORITHM == "HS256"


def test_db_app_role_is_codevv_app():
    from backend.app.core.security import DB_APP_ROLE

    assert DB_APP_ROLE == "codevv_app"


def test_verify_jwt_raises_on_invalid_token():
    from shared.auth import verify_jwt

    with pytest.raises(Exception):
        verify_jwt("any")


def test_verify_path_traversal_raises_http_error():
    from fastapi import HTTPException

    from backend.app.dependencies.path_security import verify_path_in_workspace

    with pytest.raises(HTTPException):
        verify_path_in_workspace("/etc/passwd", "/workspace")

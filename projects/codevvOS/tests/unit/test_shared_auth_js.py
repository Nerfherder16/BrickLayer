"""Structural tests for shared/auth.js — Node.js JWT auth library."""
import os

AUTH_JS_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'shared', 'auth.js'
)


def _read_auth_js():
    with open(AUTH_JS_PATH, 'r') as f:
        return f.read()


def test_shared_auth_js_exists():
    assert os.path.isfile(AUTH_JS_PATH), "shared/auth.js must exist"


def test_shared_auth_js_contains_create_jwt():
    assert 'createJwt' in _read_auth_js(), "shared/auth.js must export createJwt"


def test_shared_auth_js_contains_verify_jwt():
    assert 'verifyJwt' in _read_auth_js(), "shared/auth.js must export verifyJwt"


def test_shared_auth_js_contains_ws_auth_middleware():
    assert 'wsAuthMiddleware' in _read_auth_js(), \
        "shared/auth.js must export wsAuthMiddleware"


def test_shared_auth_js_contains_hs256():
    assert 'HS256' in _read_auth_js(), \
        "shared/auth.js must use HS256 algorithm"


def test_shared_auth_js_is_implemented():
    content = _read_auth_js()
    assert not (
        'createJwt' not in content and 'Not implemented' in content
    ), "shared/auth.js must be fully implemented, not just a stub"

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest


@pytest.fixture
def jwt_token():
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({
            "user_id": "test-user",
            "tenant_id": "test-tenant",
            "role": "member",
            "exp": int(time.time()) + 3600,
        }).encode()
    ).rstrip(b"=").decode()
    secret = b"test-secret"
    sig_bytes = hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


@pytest.fixture
def tmp_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def client():
    # Stub — will be wired to FastAPI app in Phase 1
    return None

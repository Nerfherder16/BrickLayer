"""
Task 0.4 — Redis Configuration
Tests that docker/redis/redis.conf exists and contains required directives.
Written BEFORE the file is created — fails until implementation is complete.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
REDIS_CONF = PROJECT_ROOT / "docker" / "redis" / "redis.conf"


@pytest.mark.unit
def test_redis_conf_exists():
    assert REDIS_CONF.exists(), f"redis.conf not found at {REDIS_CONF}"


@pytest.mark.unit
def test_redis_conf_appendonly_yes():
    content = REDIS_CONF.read_text()
    assert "appendonly yes" in content, "Missing: appendonly yes"


@pytest.mark.unit
def test_redis_conf_appendfsync_everysec():
    content = REDIS_CONF.read_text()
    assert "appendfsync everysec" in content, "Missing: appendfsync everysec"


@pytest.mark.unit
def test_redis_conf_maxmemory_policy():
    content = REDIS_CONF.read_text()
    assert "maxmemory-policy allkeys-lru" in content, "Missing: maxmemory-policy allkeys-lru"

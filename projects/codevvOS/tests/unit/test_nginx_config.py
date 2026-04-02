"""Unit tests for Nginx reverse proxy configuration (Task 1.20)."""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
NGINX_CONF = PROJECT_ROOT / "docker" / "nginx" / "nginx.conf"
NGINX_DOCKERFILE = PROJECT_ROOT / "docker" / "nginx" / "Dockerfile"


def test_nginx_conf_exists():
    assert NGINX_CONF.exists(), f"nginx.conf not found at {NGINX_CONF}"


def test_nginx_conf_contains_api_location():
    content = NGINX_CONF.read_text()
    assert "location /api/" in content, "nginx.conf missing '/api/' location block"


def test_nginx_conf_contains_yjs_location():
    content = NGINX_CONF.read_text()
    assert "location /yjs" in content, "nginx.conf missing '/yjs' location block"


def test_nginx_conf_contains_pty_location():
    content = NGINX_CONF.read_text()
    assert "location /pty" in content, "nginx.conf missing '/pty' location block"


def test_nginx_conf_contains_proxy_read_timeout():
    content = NGINX_CONF.read_text()
    assert "proxy_read_timeout 3600s" in content, "nginx.conf missing 'proxy_read_timeout 3600s'"


def test_nginx_conf_contains_proxy_buffering_off():
    content = NGINX_CONF.read_text()
    assert "proxy_buffering off" in content, "nginx.conf missing 'proxy_buffering off'"


def test_nginx_conf_contains_x_frame_options():
    content = NGINX_CONF.read_text()
    assert "X-Frame-Options" in content, "nginx.conf missing 'X-Frame-Options' header"


def test_nginx_dockerfile_contains_healthcheck():
    assert NGINX_DOCKERFILE.exists(), f"Dockerfile not found at {NGINX_DOCKERFILE}"
    content = NGINX_DOCKERFILE.read_text()
    assert "HEALTHCHECK" in content, "nginx Dockerfile missing HEALTHCHECK instruction"

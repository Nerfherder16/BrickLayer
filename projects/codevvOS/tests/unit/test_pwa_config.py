"""Tests for PWA manifest, icons, and vite-plugin-pwa configuration."""

import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
MANIFEST_FILE = PROJECT_ROOT / "frontend" / "public" / "manifest.webmanifest"
ICON_192 = PROJECT_ROOT / "frontend" / "public" / "icons" / "icon-192.png"
ICON_512 = PROJECT_ROOT / "frontend" / "public" / "icons" / "icon-512.png"
VITE_CONFIG = PROJECT_ROOT / "frontend" / "vite.config.ts"


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_FILE.exists(), f"manifest.webmanifest not found at {MANIFEST_FILE}"
    with open(MANIFEST_FILE) as f:
        return json.load(f)


def test_manifest_name(manifest):
    assert manifest["name"] == "CodeVV OS"


def test_manifest_short_name(manifest):
    assert manifest["short_name"] == "CodeVV"


def test_manifest_start_url(manifest):
    assert manifest["start_url"] == "/"


def test_manifest_display(manifest):
    assert manifest["display"] == "standalone"


def test_manifest_theme_color(manifest):
    assert manifest["theme_color"] == "#4F87B3"


def test_manifest_icons_non_empty(manifest):
    assert isinstance(manifest.get("icons"), list)
    assert len(manifest["icons"]) > 0


def test_icon_192_exists():
    assert ICON_192.exists(), f"icon-192.png not found at {ICON_192}"


def test_icon_512_exists():
    assert ICON_512.exists(), f"icon-512.png not found at {ICON_512}"


def test_vite_config_has_pwa_plugin():
    assert VITE_CONFIG.exists(), f"vite.config.ts not found at {VITE_CONFIG}"
    content = VITE_CONFIG.read_text()
    assert "vite-plugin-pwa" in content or "VitePWA" in content, (
        "vite.config.ts must import from 'vite-plugin-pwa' or use VitePWA"
    )


def test_vite_config_has_auto_update():
    content = VITE_CONFIG.read_text()
    assert "autoUpdate" in content, (
        "vite.config.ts must configure registerType: 'autoUpdate'"
    )

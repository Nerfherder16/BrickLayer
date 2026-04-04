"""
Task 0.5 — Tailwind v4 + Obsidian Shell Design Tokens
Tests that frontend/src/styles/global.css exists and contains
all required design tokens per the Obsidian Shell design system.
Written before the file exists — will fail until implemented.
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
GLOBAL_CSS = PROJECT_ROOT / "frontend" / "src" / "styles" / "global.css"


@pytest.fixture(scope="module")
def css_content() -> str:
    assert GLOBAL_CSS.exists(), f"global.css not found at {GLOBAL_CSS}"
    return GLOBAL_CSS.read_text()


# ---------------------------------------------------------------------------
# Tailwind v4 import
# ---------------------------------------------------------------------------

def test_tailwind_import(css_content):
    assert '@import "tailwindcss"' in css_content


# ---------------------------------------------------------------------------
# Layer base block
# ---------------------------------------------------------------------------

def test_layer_base(css_content):
    assert "@layer base" in css_content


# ---------------------------------------------------------------------------
# Surface tokens (section 2.1)
# ---------------------------------------------------------------------------

def test_color_base(css_content):
    assert "--color-base" in css_content


def test_color_surface_1(css_content):
    assert "--color-surface-1" in css_content


def test_color_surface_2(css_content):
    assert "--color-surface-2" in css_content


def test_color_surface_3(css_content):
    assert "--color-surface-3" in css_content


def test_color_surface_4(css_content):
    assert "--color-surface-4" in css_content


def test_color_surface_5(css_content):
    assert "--color-surface-5" in css_content


# ---------------------------------------------------------------------------
# Border tokens (section 2.2)
# ---------------------------------------------------------------------------

def test_color_border_subtle(css_content):
    assert "--color-border-subtle" in css_content


def test_color_border_muted(css_content):
    assert "--color-border-muted" in css_content


def test_color_border_default(css_content):
    assert "--color-border-default" in css_content


def test_color_border_strong(css_content):
    assert "--color-border-strong" in css_content


# ---------------------------------------------------------------------------
# Text tokens (section 2.3)
# ---------------------------------------------------------------------------

def test_color_text_primary(css_content):
    assert "--color-text-primary" in css_content


def test_color_text_secondary(css_content):
    assert "--color-text-secondary" in css_content


def test_color_text_tertiary(css_content):
    assert "--color-text-tertiary" in css_content


def test_color_text_inverse(css_content):
    assert "--color-text-inverse" in css_content


# ---------------------------------------------------------------------------
# Accent tokens (section 2.4)
# ---------------------------------------------------------------------------

def test_color_accent(css_content):
    assert "--color-accent" in css_content


def test_accent_value_steel_blue(css_content):
    assert "#4F87B3" in css_content


# ---------------------------------------------------------------------------
# Workspace accent classes (section 2.4)
# ---------------------------------------------------------------------------

def test_workspace_dev(css_content):
    assert ".workspace-dev" in css_content


def test_workspace_brainstorm(css_content):
    assert ".workspace-brainstorm" in css_content


def test_workspace_review(css_content):
    assert ".workspace-review" in css_content


def test_workspace_planning(css_content):
    assert ".workspace-planning" in css_content


def test_workspace_meeting(css_content):
    assert ".workspace-meeting" in css_content


# ---------------------------------------------------------------------------
# Light mode (section 2.6)
# ---------------------------------------------------------------------------

def test_theme_light(css_content):
    assert ".theme-light" in css_content


# ---------------------------------------------------------------------------
# Tailwind v4 @theme block
# ---------------------------------------------------------------------------

def test_theme_block(css_content):
    assert "@theme" in css_content


# ---------------------------------------------------------------------------
# Severity tokens (section 2.5)
# ---------------------------------------------------------------------------

def test_color_severity_critical(css_content):
    assert "color-severity-critical" in css_content


# ---------------------------------------------------------------------------
# Typography tokens
# ---------------------------------------------------------------------------

def test_font_sans(css_content):
    assert "--font-sans" in css_content


def test_font_mono(css_content):
    assert "--font-mono" in css_content


# ---------------------------------------------------------------------------
# Spacing tokens
# ---------------------------------------------------------------------------

def test_space_0(css_content):
    assert "--space-0" in css_content


# ---------------------------------------------------------------------------
# Border radius tokens
# ---------------------------------------------------------------------------

def test_radius_none(css_content):
    assert "--radius-none" in css_content


# ---------------------------------------------------------------------------
# Shadow tokens
# ---------------------------------------------------------------------------

def test_shadow_0(css_content):
    assert "--shadow-0" in css_content


# ---------------------------------------------------------------------------
# Terminal tokens
# ---------------------------------------------------------------------------

def test_terminal_background(css_content):
    assert "--terminal-background" in css_content

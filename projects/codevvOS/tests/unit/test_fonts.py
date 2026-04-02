"""Task 0.6 — Self-Hosted Fonts: verify font assets and CSS are in place."""
import glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FONTS_DIR = PROJECT_ROOT / "frontend" / "public" / "fonts"
FONTS_CSS = PROJECT_ROOT / "frontend" / "src" / "styles" / "fonts.css"
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"


def test_fonts_directory_exists():
    assert FONTS_DIR.exists(), f"Missing directory: {FONTS_DIR}"
    assert FONTS_DIR.is_dir(), f"Not a directory: {FONTS_DIR}"


def test_fonts_css_exists():
    assert FONTS_CSS.exists(), f"Missing file: {FONTS_CSS}"


def test_fonts_css_contains_font_face():
    content = FONTS_CSS.read_text()
    assert "@font-face" in content, "fonts.css must contain @font-face declarations"


def test_fonts_css_contains_inter():
    content = FONTS_CSS.read_text()
    assert "Inter" in content, "fonts.css must reference the Inter font family"


def test_fonts_css_contains_jetbrains_mono():
    content = FONTS_CSS.read_text()
    assert "JetBrains Mono" in content, "fonts.css must reference JetBrains Mono font family"


def test_no_google_fonts_cdn_references():
    """No file in frontend/src/ may reference fonts.googleapis.com."""
    matches = []
    for path in FRONTEND_SRC.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(errors="replace")
                if "fonts.googleapis.com" in text:
                    matches.append(str(path))
            except (OSError, PermissionError):
                pass
    assert matches == [], (
        f"Found fonts.googleapis.com references in: {matches}"
    )


def test_at_least_one_woff2_file_exists():
    woff2_files = list(FONTS_DIR.glob("*.woff2"))
    assert len(woff2_files) > 0, f"No .woff2 files found in {FONTS_DIR}"

"""Task 0.9 — Frontend Linting + Formatting Configuration tests."""
import json
from pathlib import Path

FRONTEND = Path(__file__).parent.parent.parent / "frontend"


def test_eslint_config_exists():
    assert (FRONTEND / "eslint.config.js").exists(), "frontend/eslint.config.js missing"


def test_tsconfig_exists_and_has_strict():
    tsconfig_path = FRONTEND / "tsconfig.json"
    assert tsconfig_path.exists(), "frontend/tsconfig.json missing"
    data = json.loads(tsconfig_path.read_text())
    assert data.get("compilerOptions", {}).get("strict") is True, \
        "tsconfig.json must have compilerOptions.strict: true"


def test_prettierrc_exists_and_valid_json():
    prettierrc_path = FRONTEND / ".prettierrc"
    assert prettierrc_path.exists(), "frontend/.prettierrc missing"
    data = json.loads(prettierrc_path.read_text())
    assert isinstance(data, dict), ".prettierrc must be a JSON object"

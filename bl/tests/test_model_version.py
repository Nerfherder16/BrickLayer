"""Tests for bl/model_version.py"""


def test_hash_is_12_hex_chars(tmp_path):
    from bl.model_version import compute_model_hash
    (tmp_path / "simulate.py").write_text("x = 1", encoding="utf-8")
    h = compute_model_hash(tmp_path)
    assert len(h) == 12
    assert all(c in "0123456789abcdef" for c in h)


def test_same_content_same_hash(tmp_path):
    from bl.model_version import compute_model_hash
    (tmp_path / "simulate.py").write_text("x = 1", encoding="utf-8")
    h1 = compute_model_hash(tmp_path)
    h2 = compute_model_hash(tmp_path)
    assert h1 == h2


def test_different_content_different_hash(tmp_path):
    from bl.model_version import compute_model_hash
    (tmp_path / "simulate.py").write_text("x = 1", encoding="utf-8")
    h1 = compute_model_hash(tmp_path)
    (tmp_path / "simulate.py").write_text("x = 2", encoding="utf-8")
    h2 = compute_model_hash(tmp_path)
    assert h1 != h2


def test_no_files_returns_no_model(tmp_path):
    from bl.model_version import compute_model_hash
    h = compute_model_hash(tmp_path)
    assert h == "no-model"


def test_constants_only_counts(tmp_path):
    from bl.model_version import compute_model_hash
    (tmp_path / "constants.py").write_text("LIMIT = 100", encoding="utf-8")
    h = compute_model_hash(tmp_path)
    assert len(h) == 12
    assert h != "no-model"


def test_embed_adds_marker(tmp_path):
    from bl.model_version import embed_in_finding
    result = embed_in_finding("# Finding\nSome content", "abc123def456")
    assert "**Model hash**: abc123def456" in result


def test_embed_skips_if_already_present(tmp_path):
    from bl.model_version import embed_in_finding
    content = "# Finding\n\n**Model hash**: existinghash12\n"
    result = embed_in_finding(content, "newhash123456")
    assert "existinghash12" in result
    assert result.count("**Model hash**:") == 1
    assert "newhash123456" not in result

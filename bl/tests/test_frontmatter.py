"""Tests for bl.frontmatter — YAML frontmatter parsing utilities."""

from bl.frontmatter import read_frontmatter_model, strip_frontmatter


class TestStripFrontmatter:
    def test_no_frontmatter(self):
        assert strip_frontmatter("hello world") == "hello world"

    def test_strips_yaml_block(self):
        text = "---\nmodel: opus\n---\nBody text"
        assert strip_frontmatter(text) == "Body text"

    def test_unclosed_frontmatter(self):
        text = "---\nmodel: opus\nBody text"
        assert strip_frontmatter(text) == text

    def test_empty_frontmatter(self):
        text = "---\n---\nBody text"
        assert strip_frontmatter(text) == "Body text"

    def test_multiline_body(self):
        text = "---\nkey: val\n---\nLine 1\nLine 2"
        result = strip_frontmatter(text)
        assert "Line 1" in result
        assert "Line 2" in result


class TestReadFrontmatterModel:
    def test_no_frontmatter(self):
        assert read_frontmatter_model("no frontmatter") is None

    def test_reads_model_quoted(self):
        text = '---\nmodel: "opus"\n---\nbody'
        assert read_frontmatter_model(text) == "claude-opus-4-6"

    def test_reads_model_unquoted(self):
        text = "---\nmodel: sonnet\n---\nbody"
        assert read_frontmatter_model(text) == "claude-sonnet-4-6"

    def test_unknown_model_passthrough(self):
        text = "---\nmodel: custom-model-id\n---\nbody"
        assert read_frontmatter_model(text) == "custom-model-id"

    def test_unclosed_frontmatter(self):
        text = "---\nmodel: opus\nbody"
        assert read_frontmatter_model(text) is None

    def test_no_model_field(self):
        text = "---\ntitle: test\n---\nbody"
        assert read_frontmatter_model(text) is None

"""Tests for PassAtNMetrics in masonry/scripts/improve_agent.py"""

import pytest


class TestPassAtNMetrics:
    """Tests for the PassAtNMetrics dataclass."""

    def test_import(self):
        """PassAtNMetrics must be importable from improve_agent."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        assert PassAtNMetrics is not None

    def test_from_accuracy_perfect(self):
        """accuracy=1.0 -> all metrics are 1.0."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(1.0)
        assert m.pass_at_1 == pytest.approx(1.0)
        assert m.pass_at_3 == pytest.approx(1.0)
        assert m.pass_strict_3 == pytest.approx(1.0)

    def test_from_accuracy_zero(self):
        """accuracy=0.0 -> all metrics are 0.0."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(0.0)
        assert m.pass_at_1 == pytest.approx(0.0)
        assert m.pass_at_3 == pytest.approx(0.0)
        assert m.pass_strict_3 == pytest.approx(0.0)

    def test_from_accuracy_half(self):
        """accuracy=0.5 -> pass@3 = 1-(0.5)^3 = 0.875, pass^3 = 0.125."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(0.5)
        assert m.pass_at_1 == pytest.approx(0.5)
        assert m.pass_at_3 == pytest.approx(0.875)
        assert m.pass_strict_3 == pytest.approx(0.125)

    def test_from_accuracy_clamps_above_one(self):
        """Values above 1.0 are clamped to 1.0."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(1.5)
        assert m.pass_at_1 == pytest.approx(1.0)
        assert m.pass_at_3 == pytest.approx(1.0)
        assert m.pass_strict_3 == pytest.approx(1.0)

    def test_from_accuracy_clamps_below_zero(self):
        """Values below 0.0 are clamped to 0.0."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(-0.1)
        assert m.pass_at_1 == pytest.approx(0.0)
        assert m.pass_at_3 == pytest.approx(0.0)
        assert m.pass_strict_3 == pytest.approx(0.0)

    def test_str_format(self):
        """__str__ should include pass@1, pass@3, and pass^3 labels."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        m = PassAtNMetrics.from_accuracy(0.8)
        s = str(m)
        assert "pass@1=" in s
        assert "pass@3=" in s
        assert "pass^3=" in s

    def test_pass_at_3_formula(self):
        """pass@3 = 1 - (1-p)^3 for arbitrary p."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        p = 0.7
        m = PassAtNMetrics.from_accuracy(p)
        expected = 1.0 - (1.0 - p) ** 3
        assert m.pass_at_3 == pytest.approx(expected)

    def test_pass_strict_3_formula(self):
        """pass^3 = p^3 for arbitrary p."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        p = 0.7
        m = PassAtNMetrics.from_accuracy(p)
        assert m.pass_strict_3 == pytest.approx(p ** 3)

    def test_dataclass_fields(self):
        """PassAtNMetrics must have pass_at_1, pass_at_3, pass_strict_3 fields."""
        from masonry.scripts.improve_agent import PassAtNMetrics
        import dataclasses
        fields = {f.name for f in dataclasses.fields(PassAtNMetrics)}
        assert "pass_at_1" in fields
        assert "pass_at_3" in fields
        assert "pass_strict_3" in fields

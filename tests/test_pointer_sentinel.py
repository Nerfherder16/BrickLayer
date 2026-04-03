"""Tests for bl/pointer_sentinel.py — Trowel pointer sentinel helpers.
Written before implementation. All tests must fail until developer completes the module.
"""

from pathlib import Path

from bl.pointer_sentinel import get_latest_checkpoint, should_fire_pointer


# ---------------------------------------------------------------------------
# should_fire_pointer
# ---------------------------------------------------------------------------


class TestShouldFirePointer:
    def test_fires_at_8_default_interval(self):
        assert should_fire_pointer(8) is True

    def test_fires_at_16(self):
        assert should_fire_pointer(16) is True

    def test_fires_at_24(self):
        assert should_fire_pointer(24) is True

    def test_fires_at_32(self):
        assert should_fire_pointer(32) is True

    def test_does_not_fire_at_0(self):
        assert should_fire_pointer(0) is False

    def test_does_not_fire_at_7(self):
        assert should_fire_pointer(7) is False

    def test_does_not_fire_at_9(self):
        assert should_fire_pointer(9) is False

    def test_does_not_fire_at_15(self):
        assert should_fire_pointer(15) is False

    def test_fires_at_custom_interval_first_multiple(self):
        assert should_fire_pointer(5, interval=5) is True

    def test_fires_at_custom_interval_second_multiple(self):
        assert should_fire_pointer(10, interval=5) is True

    def test_does_not_fire_at_non_multiple_with_custom_interval(self):
        assert should_fire_pointer(7, interval=5) is False

    def test_does_not_fire_at_3_with_custom_interval_5(self):
        assert should_fire_pointer(3, interval=5) is False


# ---------------------------------------------------------------------------
# get_latest_checkpoint
# ---------------------------------------------------------------------------


class TestGetLatestCheckpoint:
    def test_missing_directory_returns_none(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        result = get_latest_checkpoint(missing)
        assert result is None

    def test_empty_directory_returns_none(self, tmp_path):
        empty_dir = tmp_path / "checkpoints"
        empty_dir.mkdir()
        result = get_latest_checkpoint(empty_dir)
        assert result is None

    def test_single_file_returns_that_path(self, tmp_path):
        ckpt_dir = tmp_path / "checkpoints"
        ckpt_dir.mkdir()
        f = ckpt_dir / "wave1-q8.md"
        f.write_text("checkpoint content")
        result = get_latest_checkpoint(ckpt_dir)
        assert result == f

    def test_two_files_returns_later_by_sort(self, tmp_path):
        ckpt_dir = tmp_path / "checkpoints"
        ckpt_dir.mkdir()
        earlier = ckpt_dir / "wave1-q8.md"
        later = ckpt_dir / "wave1-q16.md"
        earlier.write_text("first")
        later.write_text("second")
        result = get_latest_checkpoint(ckpt_dir)
        assert result == later

    def test_three_files_across_waves_returns_last_by_sort(self, tmp_path):
        ckpt_dir = tmp_path / "checkpoints"
        ckpt_dir.mkdir()
        (ckpt_dir / "wave1-q8.md").write_text("w1q8")
        (ckpt_dir / "wave1-q16.md").write_text("w1q16")
        (ckpt_dir / "wave2-q8.md").write_text("w2q8")
        result = get_latest_checkpoint(ckpt_dir)
        assert result == ckpt_dir / "wave2-q8.md"

    def test_returns_path_object(self, tmp_path):
        ckpt_dir = tmp_path / "checkpoints"
        ckpt_dir.mkdir()
        f = ckpt_dir / "wave1-q8.md"
        f.write_text("content")
        result = get_latest_checkpoint(ckpt_dir)
        assert isinstance(result, Path)

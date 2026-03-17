"""Tests for bl/runners/base.py — RunnerInfo, register with info, describe, list_runners, runner_menu."""

from bl.runners.base import (
    Runner,
    RunnerInfo,
    describe,
    get,
    list_runners,
    register,
    runner_menu,
)


def _dummy_runner(question: dict) -> dict:
    return {"verdict": "HEALTHY", "summary": "ok", "data": {}, "details": ""}


def test_runner_protocol_satisfied():
    assert isinstance(_dummy_runner, Runner)


def test_register_without_info():
    register("_test_no_info", _dummy_runner)
    assert get("_test_no_info") is _dummy_runner
    assert describe("_test_no_info") is None


def test_register_with_info():
    info = RunnerInfo(
        mode="_test_with_info",
        description="A test runner",
        target_types=["test"],
        syntax_summary="nothing",
    )
    register("_test_with_info", _dummy_runner, info)
    assert get("_test_with_info") is _dummy_runner
    assert describe("_test_with_info") == info


def test_list_runners_includes_registered():
    info = RunnerInfo(mode="_test_list", description="list test runner")
    register("_test_list", _dummy_runner, info)
    modes_in_list = [r.mode for r in list_runners()]
    assert "_test_list" in modes_in_list


def test_runner_menu_contains_description():
    info = RunnerInfo(
        mode="_test_menu", description="menu test runner", syntax_summary="x: y"
    )
    register("_test_menu", _dummy_runner, info)
    menu = runner_menu()
    assert "_test_menu" in menu
    assert "menu test runner" in menu
    assert "x: y" in menu


def test_builtin_runners_have_info():
    """All built-in runners should have RunnerInfo registered."""
    # Import to trigger _register_builtins
    import bl.runners  # noqa: F401

    for mode in [
        "agent",
        "http",
        "subprocess",
        "quality",
        "correctness",
        "performance",
    ]:
        info = describe(mode)
        assert info is not None, f"Runner '{mode}' has no RunnerInfo"
        assert len(info.description) > 10, f"Runner '{mode}' description too short"
        assert len(info.target_types) > 0, f"Runner '{mode}' has no target_types"


def test_load_project_runners_no_dir(tmp_path):
    from bl.runners import load_project_runners

    result = load_project_runners(tmp_path)
    assert result == []


def test_load_project_runners_loads_module(tmp_path):
    from bl.runners import load_project_runners

    runners_dir = tmp_path / "runners"
    runners_dir.mkdir()
    (runners_dir / "my_runner.py").write_text(
        'RUNNER_MODE = "my_custom"\n\ndef run(question):\n    return {"verdict": "HEALTHY", "summary": "ok", "data": {}, "details": ""}\n'
    )
    loaded = load_project_runners(tmp_path)
    assert "my_custom" in loaded
    from bl.runners.base import get

    assert get("my_custom") is not None


def test_load_project_runners_with_info(tmp_path):
    from bl.runners import load_project_runners

    runners_dir = tmp_path / "runners"
    runners_dir.mkdir()
    (runners_dir / "info_runner.py").write_text(
        "from bl.runners.base import RunnerInfo\n"
        'RUNNER_MODE = "my_info_runner"\n'
        'RUNNER_INFO = RunnerInfo(mode="my_info_runner", description="test")\n'
        'def run(question):\n    return {"verdict": "HEALTHY", "summary": "ok", "data": {}, "details": ""}\n'
    )
    loaded = load_project_runners(tmp_path)
    assert "my_info_runner" in loaded
    from bl.runners.base import describe

    assert describe("my_info_runner") is not None

"""
Tests for the global git post-commit hook at ~/.git-hooks/post-commit.

The hook detects BL projects and appends commit entries to CHANGELOG.md.
CHANGELOG target logic:
  - Root-level BL project (simulate.py at repo root) -> repo root CHANGELOG.md
  - Changed files touch exactly one BL subdirectory -> that subdir's CHANGELOG.md
  - Changed files touch multiple BL subdirectories -> repo root CHANGELOG.md
  - No BL project detected -> no CHANGELOG created (exit 0)

Windows note: subprocess on Python 3.14 requires DEVNULL for stdout/stderr
(not capture_output=True) when running inside pytest's capture context to
avoid WinError 6 (invalid handle duplication).
"""

import datetime
import os
import re
import subprocess
import textwrap
from pathlib import Path


HOOK_PATH = Path.home() / ".git-hooks" / "post-commit"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command in the given directory. Uses DEVNULL to avoid
    Windows handle-duplication errors (WinError 6) from within pytest."""
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        check=check,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _run_capture(cmd: str, cwd: Path) -> str:
    """Run a shell command and return stdout as a string."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _setup_repo(repo: Path) -> None:
    """Initialize a git repo with user config and hook path set."""
    repo.mkdir(parents=True, exist_ok=True)
    _run("git init", repo)
    _run('git config user.email "test@test.com"', repo)
    _run('git config user.name "Test"', repo)
    hook_dir = str(HOOK_PATH.parent).replace("\\", "/")
    _run(f'git config core.hooksPath "{hook_dir}"', repo)


def _first_commit(repo: Path) -> None:
    """Stage all files and make the initial commit."""
    _run("git add .", repo)
    _run('git commit -m "chore: init"', repo)


def _make_commit(
    repo: Path, filename: str = "file.txt", message: str = "feat: test"
) -> None:
    """Add a file and commit, triggering the hook."""
    filepath = repo / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(f"content for {filename}\n")
    _run(f'git add "{filename}"', repo)
    _run(f'git commit -m "{message}"', repo)


# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------


def test_hook_file_exists():
    """The hook file must exist and be executable."""
    assert HOOK_PATH.exists(), f"Hook not found at {HOOK_PATH}"
    assert os.access(HOOK_PATH, os.X_OK), f"Hook is not executable: {HOOK_PATH}"


# ---------------------------------------------------------------------------
# Root-level BL project (simulate.py at repo root)
# ---------------------------------------------------------------------------


def test_root_bl_project_creates_root_changelog(tmp_path):
    """When repo root IS a BL project, hook writes to repo root CHANGELOG.md."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    _make_commit(repo, "data.txt", "feat: add data")

    changelog = repo / "CHANGELOG.md"
    assert changelog.exists(), "Root CHANGELOG.md must be created for root BL project"
    content = changelog.read_text()
    assert "feat: add data" in content


def test_root_bl_detection_via_questions_md(tmp_path):
    """questions.md at root counts as a BL project."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "questions.md").write_text("# questions\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    _make_commit(repo, "note.txt", "docs: add note")

    changelog = repo / "CHANGELOG.md"
    assert changelog.exists(), "CHANGELOG.md must be created when questions.md at root"
    assert "docs: add note" in changelog.read_text()


def test_root_bl_detection_via_agents_dir(tmp_path):
    """A .claude/agents/ directory at root counts as a BL project."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    agents_dir = repo / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "mortar.md").write_text("# mortar\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    _make_commit(repo, "x.txt", "feat: agents detection")

    changelog = repo / "CHANGELOG.md"
    assert changelog.exists()
    assert "feat: agents detection" in changelog.read_text()


# ---------------------------------------------------------------------------
# Project-subdirectory CHANGELOG targeting
# ---------------------------------------------------------------------------


def test_single_project_subdir_gets_own_changelog(tmp_path):
    """Commit touching only adbp/ writes to adbp/CHANGELOG.md, not root."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    # Non-BL root
    (repo / "README.md").write_text("root readme\n")
    adbp = repo / "adbp"
    adbp.mkdir()
    (adbp / "simulate.py").write_text("# adbp sim\n")
    _first_commit(repo)

    # Commit that only touches adbp/
    _make_commit(repo, "adbp/finding_01.md", "feat: first finding")

    adbp_changelog = repo / "adbp" / "CHANGELOG.md"
    root_changelog = repo / "CHANGELOG.md"
    assert adbp_changelog.exists(), "adbp/CHANGELOG.md must be created"
    assert not root_changelog.exists(), "Root CHANGELOG.md must NOT be created"
    assert "feat: first finding" in adbp_changelog.read_text()


def test_multi_project_commit_goes_to_root(tmp_path):
    """Commit touching two BL project subdirectories writes to root CHANGELOG.md."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "README.md").write_text("root\n")
    (repo / "proj_a" / "simulate.py").parent.mkdir()
    (repo / "proj_a" / "simulate.py").write_text("# a\n")
    (repo / "proj_b" / "questions.md").parent.mkdir()
    (repo / "proj_b" / "questions.md").write_text("# b\n")
    _first_commit(repo)

    # Stage files in both projects and commit
    (repo / "proj_a" / "f1.txt").write_text("a\n")
    (repo / "proj_b" / "f2.txt").write_text("b\n")
    _run("git add .", repo)
    _run('git commit -m "chore: update both projects"', repo)

    root_changelog = repo / "CHANGELOG.md"
    proj_a_changelog = repo / "proj_a" / "CHANGELOG.md"
    assert root_changelog.exists(), (
        "Root CHANGELOG.md must be created for multi-project commit"
    )
    assert "chore: update both projects" in root_changelog.read_text()
    assert not proj_a_changelog.exists(), (
        "Individual project CHANGELOG must not be created for multi-project commit"
    )


# ---------------------------------------------------------------------------
# Non-BL project — no CHANGELOG created
# ---------------------------------------------------------------------------


def test_non_bl_repo_no_changelog(tmp_path):
    """Hook must NOT create CHANGELOG.md for repos with no BL sentinels."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "main.py").write_text("print('hello')\n")
    _first_commit(repo)

    _make_commit(repo, "other.py", "fix: something")

    assert not (repo / "CHANGELOG.md").exists(), "No CHANGELOG for non-BL repo"


# ---------------------------------------------------------------------------
# CHANGELOG.md creation and format
# ---------------------------------------------------------------------------


def test_changelog_created_with_standard_header(tmp_path):
    """Created CHANGELOG.md contains the required header sections."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    changelog = repo / "CHANGELOG.md"
    if changelog.exists():
        changelog.unlink()  # force hook to recreate it

    _make_commit(repo, "c.txt", "feat: header test")

    assert changelog.exists()
    content = changelog.read_text()
    assert "# Changelog" in content
    assert "## [Unreleased]" in content
    assert "BrickLayer post-commit hook" in content
    assert "---" in content


def test_entry_format_hash_message_date(tmp_path):
    """Entry must follow the format: - `{hash}` {message} ({date})"""
    today = datetime.date.today().strftime("%Y-%m-%d")

    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    changelog = repo / "CHANGELOG.md"
    if changelog.exists():
        changelog.unlink()

    _make_commit(repo, "e.txt", "feat: format check")

    content = changelog.read_text()
    assert "feat: format check" in content
    assert today in content
    assert re.search(r"`[0-9a-f]{7}`", content), "Short hash not found in entry"


def test_entry_appears_under_unreleased_section(tmp_path):
    """New entry must appear after ## [Unreleased] in the file."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    changelog = repo / "CHANGELOG.md"
    if changelog.exists():
        changelog.unlink()

    _make_commit(repo, "f.txt", "feat: placement")

    content = changelog.read_text()
    lines = content.splitlines()
    unreleased_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"), None
    )
    assert unreleased_idx is not None, "## [Unreleased] not found"
    entry_idx = next(
        (i for i, line in enumerate(lines) if "feat: placement" in line), None
    )
    assert entry_idx is not None, "Entry not found"
    assert entry_idx > unreleased_idx, "Entry must come after ## [Unreleased]"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_two_commits_produce_two_entries(tmp_path):
    """Each commit produces its own entry; existing entries are not overwritten."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    changelog = repo / "CHANGELOG.md"
    if changelog.exists():
        changelog.unlink()

    _make_commit(repo, "g1.txt", "feat: first")
    _make_commit(repo, "g2.txt", "feat: second")

    content = changelog.read_text()
    assert "feat: first" in content
    assert "feat: second" in content
    assert content.count("- `") >= 2


def test_existing_changelog_content_is_preserved(tmp_path):
    """Hook appends to an existing CHANGELOG.md without destroying existing entries."""
    repo = tmp_path / "repo"
    _setup_repo(repo)
    (repo / "simulate.py").write_text("# stub\n")
    (repo / "README.md").write_text("init\n")
    _first_commit(repo)

    changelog = repo / "CHANGELOG.md"
    existing = textwrap.dedent("""\
        # Changelog

        All notable changes documented here.
        Maintained automatically by BrickLayer post-commit hook and synthesizer.

        ---

        ## [Unreleased]

        ---

        ## [v1.0.0] - 2026-01-01

        - Initial release
    """)
    changelog.write_text(existing)

    _make_commit(repo, "h.txt", "fix: preserve test")

    content = changelog.read_text()
    assert "## [v1.0.0]" in content, "Existing version section deleted"
    assert "Initial release" in content, "Existing entries deleted"
    assert "fix: preserve test" in content, "New entry not added"

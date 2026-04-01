"""
tests/test_findings_paths.py — Migration safety-net for wave-partitioned findings paths.

Scans agent .md files and template/program.md to catch any missed path migrations.
All tests must FAIL until the developer completes the file structure reorganization.

Written before implementation. RED state expected until task #4 is complete.
"""

import re
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "template" / ".claude" / "agents"
PROGRAM_MD = REPO_ROOT / "template" / "program.md"
TROWEL_MD = AGENTS_DIR / "trowel.md"

# Pattern that identifies an unmigrated findings path.
# Matches:  findings/{  (brace = template variable that is NOT wave-partitioned)
# A wave-partitioned equivalent would be: findings/wave{N}/{question_id}.md
UNMIGRATED_BRACE_PATTERN = re.compile(r"findings/\{")

# Pattern that identifies an old-style literal question-ID path:
# findings/Q-  findings/D-  findings/R-  findings/F-  findings/V-
# findings/E-  findings/M-  findings/P-  findings/A-
UNMIGRATED_LITERAL_PATTERN = re.compile(r"findings/[A-Z]-")

# Whitelisted files — explicitly excluded from the unmigrated-path check.
WHITELIST = {"trowel.md"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _agent_files():
    """Return all .md files in AGENTS_DIR, excluding the whitelist."""
    return [p for p in AGENTS_DIR.glob("*.md") if p.name not in WHITELIST]


def _violations_in(path: Path) -> list[tuple[int, str]]:
    """
    Return (line_number, line_text) pairs where an unmigrated pattern is found.
    Checks both brace-variable and literal question-ID patterns.
    """
    violations = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if UNMIGRATED_BRACE_PATTERN.search(line) or UNMIGRATED_LITERAL_PATTERN.search(
            line
        ):
            violations.append((lineno, line.strip()))
    return violations


# ── Test 1: No agent file contains unmigrated findings path ────────────────────


class TestNoUnmigratedPaths:
    """
    Every agent .md file (except trowel.md) must use wave-partitioned paths.
    Old-style paths like findings/{question_id}.md or findings/Q-001.md must
    not appear after migration.
    """

    def test_agents_dir_exists(self):
        """Prerequisite: the agents directory must be present to scan."""
        assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"

    def test_agents_dir_is_not_empty(self):
        """Prerequisite: at least one agent file must exist to scan."""
        files = _agent_files()
        assert len(files) > 0, (
            f"No .md files found in {AGENTS_DIR} (excluding whitelist)"
        )

    def test_no_unmigrated_brace_path_in_agent_files(self):
        """
        No non-whitelisted agent file should contain findings/{...}
        (a brace-variable path that has not been wave-partitioned).
        After migration the pattern should be findings/wave{N}/{question_id}.md.
        """
        all_violations = {}
        for agent_file in _agent_files():
            violations = [
                (ln, text)
                for ln, text in _violations_in(agent_file)
                if UNMIGRATED_BRACE_PATTERN.search(text)
            ]
            if violations:
                all_violations[agent_file.name] = violations

        assert all_violations == {}, (
            "Unmigrated findings brace-paths found in agent files:\n"
            + "\n".join(
                f"  {fname}:\n"
                + "\n".join(f"    line {ln}: {text}" for ln, text in hits)
                for fname, hits in all_violations.items()
            )
        )

    def test_no_unmigrated_literal_question_id_path_in_agent_files(self):
        """
        No non-whitelisted agent file should contain findings/[A-Z]- style paths
        (old-style literal question IDs like findings/Q-, findings/D-, findings/R-).
        """
        all_violations = {}
        for agent_file in _agent_files():
            violations = [
                (ln, text)
                for ln, text in _violations_in(agent_file)
                if UNMIGRATED_LITERAL_PATTERN.search(text)
            ]
            if violations:
                all_violations[agent_file.name] = violations

        assert all_violations == {}, (
            "Unmigrated findings literal-ID paths found in agent files:\n"
            + "\n".join(
                f"  {fname}:\n"
                + "\n".join(f"    line {ln}: {text}" for ln, text in hits)
                for fname, hits in all_violations.items()
            )
        )

    def test_zero_total_violations_across_all_agent_files(self):
        """
        Aggregate check: zero total unmigrated path occurrences across all
        non-whitelisted agent files.
        """
        total = 0
        for agent_file in _agent_files():
            total += len(_violations_in(agent_file))

        assert total == 0, (
            f"Found {total} unmigrated findings path(s) across agent files "
            f"(excluding {WHITELIST}). Run the two specific tests above for details."
        )


# ── Test 2: template/program.md contains wave-partitioned path reference ───────


class TestProgramMdWavePaths:
    """
    template/program.md must be updated to reference wave-partitioned findings.
    """

    def test_program_md_exists(self):
        """Prerequisite: program.md must exist."""
        assert PROGRAM_MD.exists(), f"program.md not found at: {PROGRAM_MD}"

    def test_program_md_contains_wave_partitioned_path(self):
        """
        program.md must contain at least one reference to findings/wave
        confirming the orchestration loop uses the new partitioned structure.
        """
        content = PROGRAM_MD.read_text(encoding="utf-8")
        assert "findings/wave" in content, (
            "program.md does not contain 'findings/wave'. "
            "The file must be updated to reference wave-partitioned paths "
            "(e.g., findings/wave{N}/ or findings/wave1/)."
        )


# ── Test 3: trowel.md contains wave directory creation ────────────────────────


class TestTrowelMdWaveAwareness:
    """
    trowel.md must demonstrate awareness of both the new wave-partitioned
    findings layout and the checkpoints directory.
    """

    def test_trowel_md_exists(self):
        """Prerequisite: trowel.md must exist."""
        assert TROWEL_MD.exists(), f"trowel.md not found at: {TROWEL_MD}"

    def test_trowel_md_references_wave_partitioned_findings(self):
        """
        trowel.md must contain 'findings/wave' confirming it knows about
        the new directory structure and routes findings to the correct subdirectory.
        """
        content = TROWEL_MD.read_text(encoding="utf-8")
        assert "findings/wave" in content, (
            "trowel.md does not contain 'findings/wave'. "
            "trowel.md must be updated to write findings into wave-partitioned "
            "subdirectories (e.g., findings/wave1/Q-001.md)."
        )

    def test_trowel_md_references_checkpoints_directory(self):
        """
        trowel.md must contain 'findings/checkpoints' confirming the checkpoint
        directory is part of the new structure.
        """
        content = TROWEL_MD.read_text(encoding="utf-8")
        assert "findings/checkpoints" in content, (
            "trowel.md does not contain 'findings/checkpoints'. "
            "trowel.md must reference the checkpoints subdirectory as part of "
            "the wave-partitioned findings layout."
        )

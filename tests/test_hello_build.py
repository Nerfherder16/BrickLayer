import subprocess
import sys


SCRIPT = "/home/nerfherder/Dev/Bricklayer2.0/scripts/hello_build.py"


def test_with_name():
    result = subprocess.run(
        [sys.executable, SCRIPT, "--name", "World"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "Hello, World! Build system works.\n"


def test_missing_name():
    result = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0

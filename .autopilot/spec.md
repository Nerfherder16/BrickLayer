# Spec: Hello Build — Pipeline Smoke Test

## Goal
Create a throwaway Python CLI script and its test to verify the plan+build pipeline
end-to-end. Will be deleted after confirming the system works.

## Success Criteria
- [ ] `python scripts/hello_build.py --name World` prints `Hello, World! Build system works.`
- [ ] `python scripts/hello_build.py` (no args) exits with a non-zero code
- [ ] `pytest tests/test_hello_build.py` passes with 2 tests, 0 failures

## Tasks

- [ ] **Task 1** [mode:python] — Create hello_build.py script and its test
  **Files:**
  - `scripts/hello_build.py` (create)
  - `tests/test_hello_build.py` (create)
  **What to build:**
  `scripts/hello_build.py` — `#!/usr/bin/env python3` script using `argparse`.
  One required `--name` argument (str). Prints exactly: `Hello, {name}! Build system works.`
  No external dependencies — stdlib only.
  `tests/test_hello_build.py` — pytest tests using `subprocess.run` to invoke the script:
  1. `test_with_name`: run with `--name World`, assert stdout == `Hello, World! Build system works.\n`, exit code 0
  2. `test_missing_name`: run with no args, assert exit code != 0
  **Tests required:** both tests above passing via `pytest tests/test_hello_build.py -v`

## Out of Scope
- Any persistence, config, or integration with other BrickLayer systems
- Click, typer, or any third-party CLI libraries

## Notes
- Project root: /home/nerfherder/Dev/Bricklayer2.0
- Source root: /home/nerfherder/Dev/Bricklayer2.0/scripts/
- Test root: /home/nerfherder/Dev/Bricklayer2.0/tests/
- Suggested strategy: /build --strategy aggressive (throwaway smoke test)
- Oversized files (do not modify): none
- This is a DELETE-AFTER-VERIFY build — once tests pass, delete both files
- masonry_route confirmed: python-specialist via deterministic layer (confidence 1.0)

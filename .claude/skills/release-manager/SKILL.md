---
name: release-manager
description: >-
  Automates semantic versioning and release notes from conventional commits.
  Reads git log + current version + CHANGELOG.md. Determines next semver bump.
  Generates CHANGELOG entry + GitHub release notes. Confirms before any writes.
---

# /release-manager — Semver + Release Notes

**Invocation**: `/release` (auto-detect bump) or `/release patch|minor|major` (override)

## What It Does

Automates the release process using conventional commits to determine the next version.
Always prints a confirmation summary before writing anything.

## Step 1 — Read State

- Read `package.json` to get the current `version` field (if the file exists)
- Read `pyproject.toml` for the version under `[project]` or `[tool.poetry]` (if exists)
- Run `git log {last-tag}..HEAD --oneline` to get commits since the last version tag
  - If no tag exists, use all commits: `git log --oneline`
- Read `CHANGELOG.md` if it exists, to understand the existing format

If neither `package.json` nor `pyproject.toml` exists: generate changelog and release notes
normally but skip the version file write, noting which file to update manually.

## Step 2 — Determine Version Bump

When no explicit level is provided, scan each commit message for conventional commit type:

| Signal | Bump |
|--------|------|
| `BREAKING CHANGE` in body OR `!` after type (e.g. `feat!:`) | **major** |
| `feat:` or `feat(scope):` | **minor** |
| `fix:`, `perf:`, `refactor:` | **patch** |
| `chore:`, `docs:`, `style:`, `test:` | no bump (unless the only type present) |

Take the **highest** severity bump across all commits since the last tag.

When an explicit level is provided (`/release patch`, `/release minor`, `/release major`),
use it unconditionally — do not infer from commits.

## Step 3 — Generate Output

**CHANGELOG.md entry** (prepend to existing file, or create if absent):

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Breaking Changes
- {commits with BREAKING CHANGE or ! suffix}

### New Features
- {feat: commits}

### Bug Fixes
- {fix: commits}

### Other Changes
- {perf:, refactor: commits — skip chore/docs/style/test}
```

Omit any section header that has no entries.

**GitHub release notes** (printed separately — formatted for copy-paste into a GitHub release):

```markdown
## What's Changed

### Breaking Changes
- {breaking commits, linked to hash}

### New Features
- {feat commits}

### Bug Fixes
- {fix commits}

**Full Changelog**: https://github.com/{owner}/{repo}/compare/{prev-tag}...v{new-version}
```

## Step 4 — Confirm Before Writing

Print all proposed changes and wait for explicit confirmation:

```
Ready to release:
  Current version:  1.2.3
  Next version:     1.3.0  (minor bump — 2 feat: commits)
  Files to update:  package.json, CHANGELOG.md
  Commits included: N

  CHANGELOG entry preview:
  {first 10 lines of generated entry}

Proceed? (yes/no)
```

Only after the user confirms with `yes` or `y`:
1. Prepend the new entry to `CHANGELOG.md` (create the file if it does not exist)
2. Update the `version` field in `package.json` and/or `pyproject.toml`
3. Print the GitHub release notes block for the user to copy

Do NOT commit, tag, or push — that is the user's decision.

## Edge Cases

- Neither `package.json` nor `pyproject.toml` found: generate output normally, skip version
  file write, print a note: "No version file found — update version manually"
- Explicit level argument provided (`patch`/`minor`/`major`): use it unconditionally
- `CHANGELOG.md` does not exist: create it with the first entry
- No commits since last tag: report "Nothing to release — no commits since {tag}" and stop
- Ambiguous conventional commits (no recognized prefix): treat as `patch` level

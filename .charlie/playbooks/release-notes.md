# Playbook: Weekly Release Notes

## Trigger

- **Schedule:** Every Friday at 16:00 (cron: `0 16 * * 5`)
- **Agent:** `synthesizer-bl2`
- **Conductor ID:** `release-notes`

## Purpose

Synthesize the week's research findings and git history into a formatted CHANGELOG draft.
Keeps the project changelog current without manual effort.

## Inputs

1. **Git log** — commits since last Monday 00:00 UTC:
   ```bash
   git log --oneline --since="last monday" --until="now"
   ```
2. **New findings** — all `*.md` files in `findings/` modified since last Monday:
   ```bash
   find findings/ -name "*.md" -newer findings/.last-release-marker 2>/dev/null
   ```
3. **Existing `CHANGELOG.md`** — read to determine last version header

## Expected Output

A block of conventional-commit-formatted entries ready to prepend to `CHANGELOG.md`:

```markdown
## [Unreleased] — YYYY-MM-DD

### feat
- Add reasoning bank with SQLite persistence and confidence-weighted queries
- Add mutation-tester agent for weekly coverage ratchet

### fix
- Correct routing fallback when semantic layer returns empty result
- Handle missing `findings/` directory gracefully in synthesizer

### chore
- Bump coverage threshold to 82% (mutation score 73.4%)
- Remove dead code: legacy router shims (weekly cleanup)

### docs
- Update ARCHITECTURE.md with three-layer model diagram
- Add playbook documentation for Charlie conductor
```

## Grouping Rules

Map conventional commit prefixes to changelog sections:

| Commit prefix | Section |
|---------------|---------|
| `feat:` / `feature:` | `### feat` |
| `fix:` | `### fix` |
| `chore:` | `### chore` |
| `docs:` | `### docs` |
| `refactor:` | `### chore` (merged) |
| `test:` | omit (internal) |
| `ci:` | omit (internal) |
| No prefix | `### chore` (fallback) |

## Append Procedure

1. Read the current `CHANGELOG.md`
2. Locate the first line that matches `## [` (existing version header)
3. Insert the new `## [Unreleased]` block immediately before it
4. If no existing header found, append at end of file
5. Write the updated file

## Commit Format

- **Message:** `docs: add weekly release notes YYYY-MM-DD`
- **Branch:** commit to current branch
- **Scope:** `CHANGELOG.md` only — do not stage other files

## Safety Rules

1. Never overwrite an existing `## [Unreleased]` section — append a new dated block instead
2. If `CHANGELOG.md` does not exist, create it with standard header before appending
3. If git log returns zero commits, log "No commits this week" and skip file write
4. Findings from prior weeks must not be included — filter strictly by modification date

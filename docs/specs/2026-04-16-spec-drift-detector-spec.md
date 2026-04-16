# Spec: Spec Drift Detector
Date: 2026-04-16
Status: DRAFT

## Problem Statement
After a /build completes, there is no automatic check to verify that what was actually built matches what the spec said would be built. Files get added or skipped without notice, making it easy for builds to silently drift from their specs. This drift accumulates across sessions with no record.

## Chosen Approach
**Approach A — Node.js hook script, runs automatically after /build and on-demand via /drift skill.** No new server needed. The PostToolUse hook fires after the build tool completes, the script runs, and results are written to `.autopilot/`. The drift summary is injected into the next session context so Claude always sees the last build's accuracy.

## Data Model

**SpecClaim** (parsed from the spec file):
```
specFile: string        // path to the spec, e.g. docs/specs/2026-04-16-hud-spec.md
claimedFiles: string[]  // file paths found in the spec (code blocks, bullet lists,
                        // "Files Changed", "Modified files" sections)
parsedAt: string        // ISO timestamp
```

**GitDiff** (from `git diff --name-only`):
```
baseCommit: string      // SHA from .autopilot/build-start-sha (written at /build start)
changedFiles: string[]  // actual files touched between baseCommit and HEAD
diffedAt: string        // ISO timestamp
```

**DriftReport** (written to `.autopilot/drift-report.md`):
```
specFile: string
matched: string[]       // files in both spec and diff — clean
onlyInSpec: string[]    // spec claimed these but they weren't touched
onlyInDiff: string[]    // these were touched but spec didn't mention them
verdict: "CLEAN" | "DRIFT_DETECTED"
generatedAt: string
```

The base commit SHA is written to `.autopilot/build-start-sha` at the moment `/build` begins (by the /build or /plan skill). The detector reads it back after the build completes.

## API / Interface Contract

The detector is a script, not a server. Interface surfaces:

**Automatic invocation** — PostToolUse hook registered in `settings.json`:
```
node masonry/src/hooks/drift-detector.js
```

**On-demand skill** — `/drift [spec-file]`
- `spec-file` is optional; defaults to most recently modified file in `docs/specs/`
- Can pass explicit path: `/drift docs/specs/2026-04-16-hud-spec.md`

**Inputs read:**
```
.autopilot/build-start-sha    — base commit SHA (written by /build at start)
.autopilot/spec-path          — path to active spec (written by /plan)
docs/specs/*.md               — fallback if spec-path missing: most recently modified
```

**Outputs written:**
```
.autopilot/drift-report.md    — full human-readable report, overwritten each run
.autopilot/drift-summary.txt  — one-line summary for session injection
                                e.g. "Drift: 2 unspecced files, 1 uncovered claim"
stdout                        — same summary, visible in terminal immediately
```

**Exit codes:**
```
0  — CLEAN
1  — DRIFT_DETECTED
2  — Error (missing inputs, git failure, unreadable spec)
```

## User / System Flow

**At /build start:**
1. `/plan` writes active spec path to `.autopilot/spec-path`
2. `/build` writes current `git HEAD` SHA to `.autopilot/build-start-sha`
   — this locks the baseline before any files are touched

**During /build:**
3. Agents write files normally; drift-detector is idle

**After /build completes:**
4. PostToolUse hook fires `drift-detector.js`
5. Script reads `.autopilot/spec-path` → loads spec file
6. Parses spec for file paths (searches code blocks, bullet lists, "Files changed" / "Modified files" sections)
7. Runs: `git diff --name-only <build-start-sha> HEAD`
8. Computes three sets: `matched` / `onlyInSpec` / `onlyInDiff`
9. Writes `.autopilot/drift-report.md`
10. Writes one-liner to `.autopilot/drift-summary.txt`
11. Prints summary to stdout:
    - `✓ CLEAN — all 7 spec files touched, no extras`
    - `⚠ DRIFT: 2 unspecced files changed, 1 spec claim untouched`

**Next session start:**
12. `masonry-session-start.js` reads `drift-summary.txt` if present
13. Injects it into the session context block — Claude sees "Last build drift: ..." before responding

**On-demand:**
- User types `/drift` → same steps 5–11, SHA already on disk
- User types `/drift path/to/spec.md` → uses specified spec instead of `.autopilot/spec-path`

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| `.autopilot/build-start-sha` missing | `fs.existsSync` | Print "No build baseline found — run /build first", exit 2 |
| `.autopilot/spec-path` missing | `fs.existsSync` | Fall back to most recently modified file in `docs/specs/` |
| No spec files found at all | glob returns empty | Print "No spec file found — skipping drift check", exit 0 (no false alarm) |
| Spec has no parseable file paths | parse returns empty list | Report 0 claimed files; all diff files appear as `onlyInDiff`; verdict DRIFT_DETECTED |
| `git diff` fails | non-zero exit from git | Print git stderr output, exit 2 |
| Spec file unreadable | `fs.readFileSync` throws | Print path + error, exit 2 |
| Hook fires when no build ran | SHA file absent | Exit 2 silently — expected state, not an error |
| `drift-report.md` unwritable | `fs.writeFileSync` throws | Warn to stderr, still print summary to stdout |

## Out of Scope
- Semantic diff (comparing what code does, not which files changed)
- Tracking drift across multiple builds over time (that's Project Chronicle)
- Modifying the spec automatically to match what was built
- Blocking the build if drift is detected (report only, no enforcement)

## Open Questions
_(none)_

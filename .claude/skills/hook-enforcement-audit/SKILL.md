---
name: hook-enforcement-audit
description: Audit a hook system for advisory-vs-enforcement gaps — find where gates exist but safety pins are still in
---

# /hook-enforcement-audit — Hook Enforcement Gap Audit

Audits a Claude Code hook system (settings.json + hook .js files) to identify where enforcement infrastructure is built but deliberately softened to advisory-only. Distilled from the inline-execution-audit campaign (A1.1, D2.1, D2.2).

## Steps

### 1. Locate hook files

Read `.claude/settings.json` (local) and `~/.claude/settings.json` (global):
- Extract all `hooks` entries (event type → command)
- Build inventory: event name, hook file path, hook file exists

Read each registered hook file. Build a two-column table:

| Hook | Enforcement Action |
|------|-------------------|
| masonry-approver.js | PreToolUse Write/Edit/Bash |
| masonry-content-guard.js | PreToolUse Write/Edit |
| ... | ... |

### 2. Classify each hook's authority

For each hook file, determine the authority tier:

| Tier | Pattern | Evidence |
|------|---------|---------|
| **HARD BLOCK** | `process.stdout.write(JSON.stringify({ permissionDecision: "deny", ... }))` | Actually denies tool use |
| **ADVISORY** | `process.stderr.write(...)` then allows | Logs warning, allows through |
| **ADVISORY + FLAG** | `if (process.env.FLAG) { deny } else { advisory }` | Hard block behind env flag, advisory by default |
| **INJECT** | `process.stdout.write(JSON.stringify({ additionalContext: ... }))` | Hint injection, no enforcement |
| **PASS-THROUGH** | `process.exit(0)` without output | No action |

Look for the pattern: **"infrastructure is complete but safety pin still in."** Signs:
- `isSomethingCompliant()` function exists and is called BUT result only writes to stderr
- Comment like `// Always allow through` or `// advisory only`
- `permissionDecision: "deny"` is referenced in comments or condition branches but never executed in the default path
- An env flag condition: the deny is present but gated behind `process.env.SOMETHING === "1"`

### 3. Check receipt/state patterns

For hooks that check compliance (e.g., Mortar routing receipt):
- Does `isMortarConsulted()` (or equivalent) return true or false in the live state file?
- Is the **writer** present? Where does the state flag get set to `true`? If nowhere — the checker is orphaned.
- Is there a per-turn reset? If not — stale state from prior sessions provides false compliance.

Read the state file the hook reads (e.g., `masonry/masonry-state.json`) and check:
- Is the compliance field present and non-stale?
- What writes it? (grep the codebase for assignments to the field)

### 4. Map enforcement vs. advisory

Produce a findings table:

```
Hook Enforcement Audit — [project]

| Hook | Event | Compliance Check | Authority | Gap |
|------|-------|-----------------|-----------|-----|
| masonry-approver.js | PreToolUse | isMortarConsulted() | ADVISORY (stderr) | Safety pin in — deny path present but behind MASONRY_ENFORCE_ROUTING=1 |
| masonry-content-guard.js | PreToolUse | secret scanner | HARD BLOCK | None |
| masonry-stop-guard.js | Stop | uncommitted files | HARD BLOCK | None |
| ... | | | | |

Summary:
  Hard-blocking hooks: N
  Advisory-only hooks: N  ← these are the gap
  Advisory-with-flag: N  ← half-gap, enable with env flag
  Orphaned checkers (writer missing): N  ← critical gap
```

### 5. Identify deployment prerequisites

For each ADVISORY-with-flag gap:
- What prerequisites must be in place before enabling the flag?
- Is the writer present? (If not — enabling the flag = 100% false-positive rate)
- Is there a per-turn reset? (If not — stale receipts allow bypass)
- Is there a trivial-task bypass? (If not — every prompt blocked)

List each prerequisite with its status: PRESENT / MISSING / UNRESOLVED.

### 6. Report and recommend

Output:
```
ENFORCEMENT GAPS FOUND: N

Critical (writer missing, checker orphaned):
  - [hook]: [compliance field] has no writer in the codebase

High (advisory gate, flag not set):
  - [hook]: [env flag] would enable hard block — verify N prerequisites first

Low (flag available, prerequisites met):
  - [hook]: ready to enable [flag]
```

Suggest the exact shell command to enable any enforcement flag that has all prerequisites met.

## Notes

- Never modify any hook files — read-only audit
- If settings.json has no hooks, report "No hooks registered — enforcement audit not applicable"
- The pattern "isMortarConsulted() returns false on every call because nothing writes the field" is the most common enforcement gap in BrickLayer systems

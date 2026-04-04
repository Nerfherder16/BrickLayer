---
name: debug
description: >-
  Diagnose broken code or failing tests using an 8-step structured investigation loop.
  Each technique is tried in order until root cause is found or all 8 are exhausted.
---

# /debug — Structured Diagnosis Loop

**Invocation**: `/debug <error description, failing test, or file path>`

## When to Use

When something is broken and the root cause is unknown. Not for known fixes — use /fix for that.

If a file path is provided rather than an error description, read that file first to understand the failure before starting the loop.

## Pre-Loop: Input Handling

- If the argument is a file path: read the file contents first to extract the error or failure description.
- If the file does not exist: report `File not found: {path}. Correct the path and retry.` Do not start the loop.
- A technique is complete only when the agent can state what it ruled in or ruled out — not just that it was attempted.

## The 8-Step Investigation Loop

Work through each technique in order. Stop as soon as root cause is confirmed.

---

### Step 1 — Binary Search

Bisect the failing code path: identify the midpoint between "last known working" and "currently broken". Narrow by halving the search space each iteration. Git bisect, commenting out half the code, or testing at the midpoint all count.

After this step: state what the bisect ruled in or ruled out.

---

### Step 2 — Differential Analysis

Compare a working version against the broken version. What changed? Files, inputs, environment, dependencies. The bug lives in the delta. Check git diff, dependency changelogs, environment variable differences.

After this step: state what changed between working and broken.

---

### Step 3 — Minimal Reproduction

Strip the failing case to its smallest form. Remove all code that is not directly involved in the failure. If you cannot reproduce with minimal code, the bug is in the parts you removed — restore them one at a time.

After this step: state whether minimal repro was achieved and what it revealed.

---

### Step 4 — Forward Trace

Follow execution from the entry point to the failure. Trace the data: what goes in, what transforms occur at each step, where does it diverge from expected? Add log statements or assertions at each stage.

After this step: state where the execution path diverges from expected.

---

### Step 5 — Pattern Search

Search the codebase for similar patterns. Has this class of failure appeared before? Check: related tests, comments, git log entries, open issues, TODO markers near the failure site.

After this step: state whether a matching prior failure or known pattern was found.

---

### Step 6 — Backward Trace

Work from the error backward. What caused the error message? What state produced that cause? What produced that state? Follow the chain to its origin. Stack traces, assertion messages, and error logs are your starting points.

After this step: state how far back the chain was traced and where it terminates.

---

### Step 7 — Rubber Duck

Narrate the code path aloud as if explaining it to someone who has never seen it. State every assumption explicitly. Do not skip steps that seem obvious. The bug is often in an assumption that could not possibly be wrong.

After this step: list every assumption that was stated, and flag any that were not verified.

---

### Step 8 — Hypothesis Log

Write down every hypothesis that was formed during steps 1-7, and why each was ruled out. Review the full list for logical gaps, overlooked interactions, or hypotheses that were dismissed too quickly.

After this step: the hypothesis log is complete.

---

## Loop Control

After each step:
- State whether root cause is confirmed: **FOUND** or **CONTINUE**
- If **FOUND**: write the root cause report (see Output Format below) and stop
- If **CONTINUE**: proceed to the next step
- If all 8 steps are exhausted without finding root cause: write `DIAGNOSIS_FAILED.md` and escalate

## Escalation on Exhaustion

If all 8 techniques are exhausted without confirming root cause, write `DIAGNOSIS_FAILED.md` in the current working directory containing:

```markdown
# DIAGNOSIS_FAILED

## Error / Symptom
{original error description or file content}

## Techniques Attempted

### Step 1 — Binary Search
{what was tried, what was ruled in/out}

### Step 2 — Differential Analysis
{what was tried, what was ruled in/out}

### Step 3 — Minimal Reproduction
{what was tried, what was ruled in/out}

### Step 4 — Forward Trace
{what was tried, what was ruled in/out}

### Step 5 — Pattern Search
{what was tried, what was ruled in/out}

### Step 6 — Backward Trace
{what was tried, what was ruled in/out}

### Step 7 — Rubber Duck
{assumptions stated, any flagged as unverified}

### Step 8 — Hypothesis Log
{full list of hypotheses and why each was ruled out}

## Working Hypotheses (Unconfirmed)
{any hypotheses that could not be definitively confirmed or ruled out}

## Recommended Next Steps
- Add logging at {specific location} to capture {specific state}
- Write a characterization test that asserts {observable behavior}
- Ask the author about {specific assumption or design decision}
- Check {external system/dependency} for changes since last known working state
```

Then surface to the user:

```
All 8 techniques exhausted. Root cause not confirmed.
See DIAGNOSIS_FAILED.md for full investigation log.
Human input needed — recommended next steps are listed in that file.
```

## Output Format

On root cause found:

```
ROOT CAUSE FOUND (Step N — {technique name})

{clear description of the bug — what it is, why it causes the observed failure}

Evidence: {specific file:line, test output, or state that confirms the root cause}

Fix: {recommended fix in one or two sentences, or "use /fix to implement"}
```

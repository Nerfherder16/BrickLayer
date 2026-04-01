# Fix Mode — Program

**Purpose**: Implement a specific `DIAGNOSIS_COMPLETE` finding and verify the fix worked.
This is targeted surgical repair — not exploration, not root cause analysis.
The diagnosis is already done. Fix mode executes it.

**Input**: A `DIAGNOSIS_COMPLETE` finding file (required — refuse to run without it)
**Verdict vocabulary**: FIXED | FIX_FAILED | INCONCLUSIVE
**Evidence sources**: Source code edits, test suite, live system verification

---

## Loop Instructions

### Pre-flight (required before running)

1. Read the specified `DIAGNOSIS_COMPLETE` finding
2. Confirm the Fix Specification passes the **specificity gate** — all four required:
   - [ ] **Target file**: exact path (not "somewhere in bl/")
   - [ ] **Target location**: line number OR function/method name
   - [ ] **Concrete edit**: diff-level description ("change `x == 1` to `x >= 1`", not "improve the logic")
   - [ ] **Verification command**: runnable, produces pass/fail (e.g., `python -m pytest tests/test_foo.py::test_bar`)
   If ANY of the four are missing → output `FIX_FAILED` with reason "Underspecified finding — return to Diagnose mode with specificity requirements."
3. Read the target file to understand surrounding context
4. Check test coverage for the affected area

### Per-question (Fix mode uses questions differently)

Fix mode questions are not discovery questions. They are verification checkpoints:
- Q1: "Has the specified change been implemented correctly?"
- Q2: "Do all existing tests pass?"
- Q3: "Does the specific failure condition that triggered the DIAGNOSIS_COMPLETE now pass?"
- Q4: "Are there any observable side effects in adjacent components?"

### Implementation sequence

1. **Read** the target file completely before editing
2. **Implement** the specified change exactly as described in the Fix Specification
3. **Run tests** — all must pass, not just the targeted test
4. **Verify** using the method specified in the finding's "Verification" field
5. **Check adjacent components** — run the 1-2 most likely regression surfaces

### Verdict assignment

- `FIXED` — change implemented, all tests pass, verification confirms the failure condition is resolved
- `FIX_FAILED` — change implemented but verification fails OR tests regress
  - Write finding with: what was tried, what failed, and a **Root Cause Update** section:
    - Original hypothesis: [what the DIAGNOSIS_COMPLETE finding said]
    - Why it was wrong: [what the implementation revealed]
    - Updated hypothesis: [what is now believed to be the actual root cause]
  - Do NOT attempt a second fix variation — return to Diagnose mode with the updated hypothesis
- `INCONCLUSIVE` — verification method is timing-dependent or requires external event
  - Add `resume_after:` to re-verify when condition is met

### Session end

Write to `findings/{original_finding_id}_fix.md`:
- Original `DIAGNOSIS_COMPLETE` finding reference
- Exact change made (diff or description)
- Test results before and after
- Verification evidence
- `FIXED` or `FIX_FAILED` verdict

Update the original finding's status from `DIAGNOSIS_COMPLETE` to `FIXED` or `FIX_FAILED`.

### Anti-patterns — NEVER do these in Fix mode

- Do not expand scope beyond the specified fix
- Do not refactor surrounding code
- Do not add features or improvements
- Do not attempt a second fix approach if the first fails (that's Diagnose's job)
- Do not skip the pre-flight check

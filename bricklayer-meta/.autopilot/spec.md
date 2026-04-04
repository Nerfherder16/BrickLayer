# Build Spec — Bricklayer-Meta Synthesis Implementation

## Overview

Implement four READY priorities from the bricklayer-meta Wave 4 synthesis (findings/synthesis.md). These are well-specified changes derived from Q7.5, Q7.6, Q8.2, and Q8.5 findings.

## Constraints

- template/program.md is the canonical loop instructions — all program.md changes go here
- bricklayer-meta does NOT have its own program.md (uses template)
- simulate.py engine section (below SCENARIO PARAMETERS) is editable per Q8.5 spec
- No new files required — all changes are inserts/edits to existing files

## Tasks

### Task 1: Session-Start Self-Check (Priority 3, Q7.6)

**File**: `template/program.md`
**Location**: Replace the existing step 8 "Session-start self-check" with the Q7.6 enhanced version

**Specification** (from Q7.6 finding):
The self-check verifies three format-invariant markers are present in program.md:
1. `spawn peer-reviewer` (marker A)
2. `spawn forge-check` (marker B)
3. `agent-auditor` (marker C)

If any marker is absent: re-read from disk, re-check, and if still absent write `findings/SELF_CHECK_FAILURE.md` and halt.

The existing step 8 already has a basic version. Enhance it with the full Q7.6 spec while preserving the existing baseline run check and peer-review gap check.

**Acceptance**: Step 8 contains the three-marker check, halt-and-reread procedure, and failure file creation.

---

### Task 2: HHI Severity-Exemption Gate (Priority 4, Q7.5)

**File**: `template/program.md`
**Location**: Wave-start sentinel check, item 4 (HHI diversity sentinel)

**Specification** (from Q7.5 finding):
Replace the basic HHI sentinel with the full gate:

1. **CRITICAL FAILURE definition**: Verdict FAILURE + severity phrase match (never surfaced, data loss, regression, silently drops, split-brain confirmed, 0 hits, memory never, hit rate [0-9]\.)
2. **Per-category exemption window**: N=5 waves from CRITICAL FAILURE discovery
3. **Early expiry**: clears if category transitions to WARNING/HEALTHY in 3 consecutive findings AND no new FAILURE in 2 waves AND restricted-HHI < 0.40
4. **HHI computation on restricted set**: excludes exempt categories from denominator
5. **Multi-CRITICAL degradation**: 0 non-exempt → suspend HHI; 1 non-exempt → advisory only
6. **Tie-breaking**: fewer questions asked, then alphabetical
7. **Minimum corpus gate**: skip HHI until >= 10 WARNING/FAILURE findings exist

**Acceptance**: Item 4 contains the full gate spec with CRITICAL FAILURE definition, exemption window, early expiry, and multi-CRITICAL handling.

---

### Task 3: Novelty Cliff Fix (Priority 5, Q8.5)

**File**: `bricklayer-meta/simulate.py`
**Location**: `_peer_correction()` function, novelty_discount line

**Change**:
```python
# Before:
novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 0.90)

# After:
novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 1.20)
```

Also update:
- The SCENARIO PARAMETERS comment for `RECALIBRATED_PEER_REVIEW_CORRECTION_RATE` (change 2 note)
- The docstring in `_peer_correction()` to reference the Q8.5 fix

**Acceptance**: `python simulate.py` produces verdict HEALTHY at baseline (DN=0.35). The novelty cliff moves from DN≈0.857 to DN≈0.780.

---

### Task 4: SUBJECTIVE Verdict Queue (Priority 10, Q8.2)

**File**: `template/program.md`
**Location**: After the "Wave-start sentinel check" section, before "Output Format"

**Specification** (from Q8.2 finding, 17-line insert):

```markdown
### SUBJECTIVE Verdict Handling (Model B Queue)

A finding with `**Verdict**: SUBJECTIVE` means sufficient evidence was gathered but only
a human can resolve the verdict. Mark the question DONE and annotate the Status line:

  **Status**: DONE  <!-- SUBJECTIVE: awaiting human resolution -->

**At each wave-start sentinel check**, count unresolved SUBJECTIVE annotations in the
current wave. If backlog > 5, output a list of unresolved IDs to the terminal before
continuing. If backlog > 10, append `<!-- ESCALATION: review debt >10 -->` to the wave
header. Do not halt the campaign on either condition.

**Resolution (Tim's action)**: Read the finding. Update `**Verdict**` to the actual
verdict. Add `## Human Resolution` section (1-3 sentences). Remove the SUBJECTIVE
annotation from the Status line. Campaign target: resolve >= 70% of SUBJECTIVE findings
per wave before the next wave-start check.

**SUBJECTIVE is not INCONCLUSIVE.** INCONCLUSIVE = insufficient evidence.
SUBJECTIVE = evidence gathered, human judgment required to weigh it.
```

**Acceptance**: Section is inserted after the wave-start sentinel check and before the Output Format section.

## Verification

After all 4 tasks:
1. `python bricklayer-meta/simulate.py` → verdict HEALTHY
2. template/program.md is coherent — no duplicate sections, logical flow
3. All inserted text matches the finding specifications

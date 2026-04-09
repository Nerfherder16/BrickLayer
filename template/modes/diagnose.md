# Diagnose Mode — Program

**Purpose**: Find unknown failures in a system and trace each to its exact root cause.
Produce `DIAGNOSIS_COMPLETE` findings with precise fix specifications. Do not re-check
known unfixed failures — that is Monitor's job.

**Verdict vocabulary**: HEALTHY | WARNING | FAILURE | DIAGNOSIS_COMPLETE | INCONCLUSIVE | PENDING_EXTERNAL
**Evidence sources**: Source code, test results, live system queries, log analysis
**Terminal finding**: `DIAGNOSIS_COMPLETE` — root cause identified at code level with exact fix spec

---

## Loop Instructions

### Per-question

1. Read the question. It targets a specific suspected failure:
   - "Does X produce Y under condition Z?"
   - "Is the failure rate of component A above threshold?"
   - "What is the root cause of the observed behavior?"

2. Gather evidence from the actual system:
   - Read relevant source files (don't assume — read the actual code)
   - Run correctness or subprocess checks
   - Query live system endpoints if available
   - Check `docs/` and `project-brief.md` for expected behavior

3. Assign verdict:
   - `HEALTHY` — no failure found, system behaves as specified
   - `WARNING` — behavior is degraded but within recoverable range
   - `FAILURE` — failure confirmed, root cause partially identified
   - `DIAGNOSIS_COMPLETE` — root cause identified at code level; finding includes exact file, line, fix
   - `INCONCLUSIVE` — cannot determine without more data; add `requires:` field
   - `PENDING_EXTERNAL` — blocked by external condition; add `resume_after:` field

4. **`DIAGNOSIS_COMPLETE` requirements** — the finding MUST include:
   ```
   ## Fix Specification
   - File: path/to/file.py
   - Line: 123
   - Change: [exact description or diff]
   - Verification: [how to confirm it worked]
   - Risk: [regression surface, if any]
   ```

5. **Do NOT add re-check questions** for `DIAGNOSIS_COMPLETE` findings.
   These are suppressed until the human signals the fix was deployed.

### Wave structure

- 5-7 questions per wave
- Hypothesis generator reads prior findings and asks: "What failure modes haven't we tested yet? What does this finding imply about adjacent components?"
- Adaptive expansion: FAILURE findings should generate follow-up questions narrowing to root cause
- Stop condition: `WAVE_NOVELTY_FLOOR_FAILURE` — if last wave signal < 0.15, campaign is saturated

### Session end

Synthesis must include:
- **Open failures table**: all FAILURE/WARNING findings with status
- **DIAGNOSIS_COMPLETE queue**: all findings ready for Fix mode, in priority order
- **Suppressed re-checks**: list of questions suppressed pending deployment
- **Coverage map**: which failure categories have been explored vs. untested

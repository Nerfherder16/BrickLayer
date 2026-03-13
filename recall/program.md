# Recall Autoresearch Program

This is a live-system stress-testing experiment. An AI agent (Claude Code) works through
the question bank in `questions.md`, dispatches each question to `simulate.py`, evaluates
the result, writes a finding, and loops autonomously.

The goal is to **map the failure boundary** of the Recall memory system — to discover
which conditions cause the system to fail, misbehave, or have latent quality bugs.

---

## Setup

To begin a research session:

1. **Agree on a run tag**: propose a tag based on today's date (e.g., `mar12`).
2. **Read context files** (do not modify them):
   - `project-brief.md` — what Recall is and what we're testing
   - `questions.md` — the full question bank (15 questions, 3 modes)
   - `docs/architecture.md` — Recall system architecture reference
3. **Verify the API is up**: `curl http://192.168.50.19:8200/health`
   - If down: mark all Performance questions INCONCLUSIVE and proceed to Correctness/Quality
4. **List questions**: `python simulate.py --list`
5. **Confirm and go.**

---

## What You CAN Do

- Run `simulate.py` — do not modify it (it is the fixed runner, not a parameter file)
- Write findings to `findings/{qid}.md`
- Update `results.tsv` (simulate.py does this automatically)
- Add follow-up questions to `questions.md` after Critical/High findings
- Read Recall source files at `C:/Users/trg16/Dev/Recall/src/` for quality analysis

## What You CANNOT Do

- Modify `simulate.py`
- Modify `program.md`
- Modify `project-brief.md` or `docs/architecture.md`
- Install new packages
- Write to the Recall source at `C:/Users/trg16/Dev/Recall/` — this is read-only

---

## The Research Loop

Work through questions in order: Q1 (Performance) → Q2 (Correctness) → Q3 (Quality).

### For each question:

1. **Pick the next PENDING question** from `questions.md`
2. **Run simulate.py**: `python simulate.py`
   - Or target a specific question: `python simulate.py --question Q1.1`
3. **Read the JSON result** from stdout
4. **Read the finding** written to `findings/{qid}.md`
5. **Evaluate the verdict**:
   - `FAILURE` → **High severity finding**. Enrich the finding with your analysis. Add follow-up questions to `questions.md`.
   - `WARNING` → **Medium severity finding**. Enrich the finding. Consider a follow-up if the warning is close to the failure boundary.
   - `HEALTHY` → **Info finding**. Log it and move on.
   - `INCONCLUSIVE` → Log the reason. Continue to next question.
6. **For quality mode questions** (Q3.x): `simulate.py` reads and emits source files. You do the analysis. Read the `details` field in the JSON output, apply your judgment, then overwrite `findings/{qid}.md` with your analysis, verdict, and specific line references.
7. **Log to results.tsv** (simulate.py does this automatically — verify it happened)
8. **Continue to next question**

### If the Recall API is down (Performance questions):

Do NOT pause or wait. Self-recover immediately:
1. Record verdict `INCONCLUSIVE` with reason "API unreachable" — simulate.py does this automatically
2. Skip remaining Performance questions for this session
3. Proceed directly to Correctness questions (Q2.x)
4. Note in program log that Performance questions need a re-run when API is restored

### If pytest fails to find test files (Correctness questions):

simulate.py retries once with auto-detected paths. If it still returns INCONCLUSIVE:
1. Check actual file locations: `ls C:/Users/trg16/Dev/Recall/tests/integration/` and `ls C:/Users/trg16/Dev/Recall/tests/core/`
2. Run the corrected pytest command manually via Bash
3. Write the finding manually based on the output

### If a quality question has missing source files:

1. Check `C:/Users/trg16/Dev/Recall/src/` for the correct path
2. Read the file directly using your Read tool
3. Perform the analysis and write the finding manually

---

## Output Format

`simulate.py` prints JSON to stdout:
```json
{
  "question_id": "Q1.1",
  "mode": "performance",
  "verdict": "FAILURE|WARNING|HEALTHY|INCONCLUSIVE",
  "summary": "one line summary",
  "data": {...},
  "details": "full output text"
}
```

And writes to:
- `findings/{qid}.md` — structured finding file
- `results.tsv` — updated automatically

---

## Logging to results.tsv

Tab-separated. Updated automatically by simulate.py. Format:
```
question_id	verdict	summary	timestamp
Q1.1	FAILURE	5 users: p99=340ms | 10 users: p99=890ms | 20 users: p99=2340ms	2026-03-12T15:00:00Z
```

Verify each row was written. If simulate.py failed to write it, add manually.

---

## Finding Format

`simulate.py` creates the skeleton. You must enrich it:

```markdown
# Finding: {qid} — {title}

**Question**: [hypothesis from questions.md]
**Verdict**: FAILURE | WARNING | HEALTHY | INCONCLUSIVE
**Severity**: Critical | High | Medium | Low | Info

## Summary
[one line from simulate.py output]

## Evidence
[Specific numbers, latency measurements, test output, or code analysis.
For quality mode: quote specific line numbers and explain the issue.]

## Mitigation Recommendation
[What should change in Recall source code, configuration, or test coverage]

## Open Follow-up Questions
[Required for Critical/High. Each is a falsifiable hypothesis — add to questions.md immediately.]
- [follow-up question 1]
- [follow-up question 2]
```

---

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| Critical | System cannot serve load or data integrity is broken. Requires immediate fix. |
| High | System degrades under realistic load or guarantee violated under concurrency. Requires mitigation. |
| Medium | System healthy but closer to failure boundary than expected. Monitor and tune. |
| Low | Edge case, unlikely in practice. Document and move on. |
| Info | System behaves as expected. No risk found. |

---

## Quality Mode — Agent Analysis Protocol

For Q3.x questions, `simulate.py` reads source files and returns them in `details`.
The agent (you) must:

1. Read the `details` field — it contains the full source file content
2. Apply the specific analysis from the question's `Test` field
3. Look for the patterns described in `Verdict threshold`
4. Write your verdict (FAILURE/WARNING/HEALTHY) with specific evidence
5. Reference specific line numbers and code patterns in the finding

Do not mark a quality question INCONCLUSIVE unless the file genuinely doesn't exist.
If you can read the file, you can analyze it.

---

## After FAILURE Findings — Follow-up Protocol

When you write a finding with verdict FAILURE or severity Critical/High:

1. Immediately append follow-up questions to the finding under `## Open Follow-up Questions`
2. Add those questions to `questions.md` as new PENDING entries
3. Place them immediately after the current wave (before the next unrelated question)
4. Label them with the parent question ID (e.g., `Q1.1a`, `Q1.1b`)
5. Continue with the next question — do not stop to investigate the follow-up immediately

---

## Agent Tag Convention

Store findings and intermediate work in Recall under `domain="recall-autoresearch"`:

| Agent | Tag | What it stores |
|-------|-----|----------------|
| This session | `agent:stress-tester` | Per-question findings summary |
| Performance analysis | `agent:perf-analyst` | Latency curves, failure boundaries |
| Code review | `agent:code-reviewer` | Quality findings with line refs |

---

## NEVER STOP

Once the loop has begun, do NOT pause to ask if you should continue.
The researcher may be away from their computer and expects autonomous work.

If you run out of questions in the question bank, generate new ones based on findings
so far — each failure state raises new hypotheses. The loop runs until the researcher
interrupts you, period.

When you discover a Critical or High severity finding, write the finding immediately,
then continue to the next question. Do not stop to report.

# BrickLayer 2.0 — Parallel Worker Loop

This is the parallel-mode variant of `program.md`. Use this when multiple Claude
workers are running simultaneously against the same project.

Your worker ID is set via the `BL_WORKER_ID` environment variable (1, 2, 3, ...).
Read it at startup: `echo $BL_WORKER_ID`

---

## Setup (same as program.md, but claim-aware)

1. Check your worker ID: `echo $BL_WORKER_ID` — if unset, treat as worker-1
2. Create or confirm the branch exists (lead worker creates it; others checkout)
3. Read `constants.py`, `questions.md`, `simulate.py` for context
4. Verify the simulation runs: `python simulate.py` → expect `verdict: HEALTHY`
5. **Do NOT create or reset results.tsv** — another worker may have started it

---

## Claim Protocol — MANDATORY

Before working ANY question, you must claim it atomically:

```bash
# Try to claim
python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py claim . {question_id} worker-{BL_WORKER_ID}
```

**Responses:**
- `CLAIMED` → the question is yours. Proceed.
- `TAKEN` → another worker already has it. Skip and try the next PENDING question.
- `LOCK_FAILED` → retry after 2 seconds.

After completing a question (finding written, questions.md updated):

```bash
python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py complete . {question_id} {verdict}
```

---

## The Research Loop (Parallel Variant)

Maintain a counter `questions_this_worker = 0` — incremented after each completed finding.

### Each iteration:

**0. Wave-start sentinel check (worker-1 ONLY — all other workers skip this step)**

Before picking the next question, check for pending background-agent outputs:

1. **`.claude/agents/FORGE_NEEDED.md` exists?**
   → Invoke forge-check **synchronously** (blocking) to create missing agents, then delete the file.
   New agents may be needed for the next question — this must complete before proceeding.

2. **`.claude/agents/AUDIT_REPORT.md` exists?**
   → Read it. Apply RETIRE, PROMOTE, and UPDATE TRIGGERS recommendations immediately.
   Delete `AUDIT_REPORT.md` when done. Non-blocking — continue to next question.

3. **Any finding in `findings/` contains `**Verdict**: OVERRIDE` inside a `## Peer Review` section?**
   → Insert a new PENDING re-examination question at the top of the next wave in `questions.md`.
   Do not revert any commit without human confirmation. Non-blocking.

---

**1. Get next claimable question**
```bash
python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py pending .
```
If this returns empty → you're done. Go to Shutdown.

Take the first ID from the list.

**2. Claim it**
```bash
python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py claim . {question_id} worker-{BL_WORKER_ID}
```
If TAKEN → go back to step 1.

**3. Work the question** (same as normal program.md loop)
- Investigate using simulation, web search, or whatever the question requires
- Follow the domain-specific agent pattern (quantitative, regulatory, competitive, etc.)
- Write finding to `findings/{question_id}.md`
- Update `questions.md`: change status from `PENDING` → `DONE` (or `INCONCLUSIVE`)

**4. Record completion**
```bash
python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py complete . {question_id} {HEALTHY|FAILURE|INCONCLUSIVE}
```

**5. Commit this finding**
```bash
git add findings/{question_id}.md questions.md claims.json
git commit -m "finding({question_id}): {one-line summary} [worker-{BL_WORKER_ID}]"
```

**6. Spawn peer-reviewer in background (every worker, every finding)**

Immediately after the commit — do NOT wait for it:
```
Spawn background agent — peer-reviewer:
  "Act as peer-reviewer per .claude/agents/peer-reviewer.md.
   primary_finding=findings/{question_id}.md, target_git=., agents_dir=.claude/agents/.
   Re-run the original test independently, append ## Peer Review section with verdict
   CONFIRMED | CONCERNS | OVERRIDE."
```

**7. Increment counter and fire sentinels (worker-1 ONLY — all other workers skip to step 8)**

`questions_this_worker += 1`

At `questions_this_worker % 5 == 0` — spawn hypothesis-generator-bl2 then forge-check in background:
```
Spawn background agent — hypothesis-generator-bl2:
  "Act as hypothesis-generator-bl2 per .claude/agents/hypothesis-generator-bl2.md.
   Read the 3 most recent findings in findings/. Add up to 5 new PENDING questions
   to questions.md. Label them Wave-mid."

Spawn background agent — forge-check:
  "Act as forge-check per .claude/agents/forge-check.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, questions_md=questions.md.
   Write .claude/agents/FORGE_NEEDED.md if gaps found, otherwise output FLEET COMPLETE."
```

At `questions_this_worker % 10 == 0` — additionally spawn agent-auditor in background:
```
Spawn background agent — agent-auditor:
  "Act as agent-auditor per .claude/agents/agent-auditor.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, results_tsv=results.tsv.
   Write the audit report to .claude/agents/AUDIT_REPORT.md."
```

Continue to the next question immediately. All background agents run concurrently.

**8. Back to step 0**

---

## Shutdown

When `pending` returns empty:

1. Check claims status: `python C:/Users/trg16/Dev/Bricklayer2.0/bl/claim.py status .`
2. If any questions show IN_PROGRESS from other workers, those are still running — you're done, they'll finish
3. Do a final commit of anything uncommitted

**Worker-1 only — final wave audit before stopping:**
```
Invoke agent-auditor (foreground — must complete before stopping):
  "Act as agent-auditor per .claude/agents/agent-auditor.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, results_tsv=results.tsv.
   Write the final audit report to .claude/agents/AUDIT_REPORT.md."

Invoke forge-check (foreground):
  "Act as forge-check per .claude/agents/forge-check.md.
   Inputs: agents_dir=.claude/agents/, findings_dir=findings/, questions_md=questions.md."

Invoke skill-forge (foreground):
  "Act as skill-forge per .claude/agents/skill-forge.md (if it exists).
   Distill reusable patterns from this campaign's findings into ~/.claude/skills/."
```

4. Print: `Worker {BL_WORKER_ID} complete. All pending questions claimed.`
5. Stop.

---

## What You CAN Do (same as program.md)

- Modify `simulate.py` SCENARIO PARAMETERS section only
- Write findings to `findings/`
- Update question status in `questions.md`
- Write to `claims.json` via `claim.py` only (never directly)

## What You CANNOT Do

- Modify `constants.py`
- Change question text in `questions.md`
- Modify another worker's in-progress finding
- Edit `claims.json` directly — always use `claim.py`

---

## Self-Recovery

If a `simulate.py` edit fails:
1. `git status` → check for dirty state
2. `git reset --hard HEAD` → clear stuck state
3. Re-attempt the edit
4. If fails again → rewrite full file preserving all logic, only changing SCENARIO PARAMETERS
5. Continue the loop

If `claim.py` returns `LOCK_FAILED` repeatedly:
1. Check for stale lock: `ls claims.lock` in project dir
2. If older than 60 seconds, it's abandoned: `rm claims.lock`
3. Retry the claim

---

## Git Discipline

Workers commit per-finding (not in batches) to minimize merge conflicts.
Use `git pull --rebase` before each commit if another worker may have pushed.

If merge conflict in `questions.md`:
- Accept both changes (both workers' status updates are valid)
- Resolve manually, keeping the more complete status

If merge conflict in `claims.json`:
- The version with more entries is authoritative — merge by union, not by overwrite

---

## Notes

- Each worker runs independently. No IPC. Coordination is file-only via `claims.json`.
- If a worker crashes mid-question, its claim stays IN_PROGRESS. The lead can release it:
  `python claim.py release . {question_id}`
- `claims.json` is committed with each finding — provides a full audit trail of who worked what

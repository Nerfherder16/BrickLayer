# Masonry Self-Research Campaign — Program

This is a code analysis and architectural research campaign. There is no `simulate.py`.
Questions are answered by reading source code, tracing logic, and building evidence-based findings.

**IMPORTANT:** This is a BrickLayer research campaign running *inside* the Masonry software project.
`CHANGELOG.md`, `ARCHITECTURE.md`, and `ROADMAP.md` at this folder root are **Masonry software project docs** —
maintained by karen as code evolves. Do NOT overwrite them with campaign synthesis output.
All campaign output goes to `findings/`.

---

## Setup

1. **Read these files before starting** (do not modify):
   - `project-brief.md` — ground truth, two research domains, key invariants
   - `questions.md` — question bank (18 questions, Wave 1)
   - `docs/` — routing architecture, hook inventory, source code copies
2. **No simulation to run.** Questions are answered by reading `src/`, `hooks.json`, `agent_registry.yml`.
3. **Confirm and go.**

---

## What You CAN Do

- Read any file in this project
- Write findings to `findings/<question_id>.md`
- Append PENDING questions to `questions.md`
- Write `findings/synthesis.md` at wave-end

## What You CANNOT Do

- Modify any file in `src/`, `mcp_server/`, `hooks/`, `skills/`, `packs/`, `scripts/`, `bin/`
- Modify `agent_registry.yml`, `hooks.json`, `package.json`, `requirements.txt`
- Modify `CHANGELOG.md`, `ARCHITECTURE.md`, `ROADMAP.md` — these are Masonry software project docs
- Modify `project-brief.md` or files in `docs/`

---

## The Research Loop

Each question is answered via code analysis. Work through questions in the order listed in `questions.md`.

### For every question:

1. Pick the next PENDING question from `questions.md`
2. Read the relevant source files listed in `project-brief.md` under "Key code locations"
3. Trace the logic, identify the failure mode or behavioral property being investigated
4. Write the finding to `findings/<question_id>.md` using the format below
5. Mark the question DONE (or INCONCLUSIVE) in `questions.md`
6. **Check for follow-ups** (see Live Discovery below)

---

## Live Discovery

### After every Critical or High severity finding

Append to the finding file:
```markdown
## Suggested Follow-ups
- [Falsifiable follow-up question this finding directly implies]
```
Then insert those questions into `questions.md` as PENDING, before any remaining lower-priority questions.

### Every 5 completed questions

Invoke `hypothesis-generator-bl2` with the 3 most recent findings as context:
```
Read the 3 most recent findings in findings/. Identify failure modes or cross-domain risks
not covered by remaining PENDING questions. Add up to 5 new PENDING questions to questions.md.
Label them Wave-mid.
```

**Immediately after**, spawn as **background agents** (do NOT wait):
```
# Always at N % 5 == 0:
Spawn background — forge-check:
  "Act as forge-check per agents/forge-check.md.
   Inputs: agents_dir=~/.claude/agents/, findings_dir=findings/, questions_md=questions.md.
   Write FORGE_NEEDED.md if gaps found."

# Additionally at N % 10 == 0:
Spawn background — agent-auditor:
  "Act as agent-auditor per agents/agent-auditor.md.
   Inputs: agents_dir=~/.claude/agents/, findings_dir=findings/.
   Write AUDIT_REPORT.md."
```

### After writing each finding — spawn peer-reviewer in background

```
Spawn background — peer-reviewer:
  "Act as peer-reviewer per agents/peer-reviewer.md.
   primary_finding=findings/<question_id>.md
   Re-examine the code evidence independently. Append ## Peer Review with CONFIRMED | CONCERNS | OVERRIDE."
```

### Wave-start sentinel check (before EVERY question)

1. **`FORGE_NEEDED.md` exists?** → Invoke forge synchronously, delete file, then continue.
2. **`AUDIT_REPORT.md` exists?** → Apply RETIRE/PROMOTE recommendations, delete file, continue.
3. **Any finding has `Verdict: OVERRIDE` in Peer Review?** → Insert re-examination question at top of queue.

---

## Finding Format

Write each finding to `findings/<question_id>.md`:

```markdown
# Finding: <question_id> — <short title>

**Question**: [copy from questions.md]
**Agent**: [specialist agent name]
**Verdict**: CONFIRMED | WARNING | INCONCLUSIVE | CLEARED
**Severity**: Critical | High | Medium | Low | Info

## Evidence
[Specific file paths, line numbers, code quotes. No hand-waving.]

## Analysis
[What this means for Masonry's correctness or reliability.]

## Mitigation Recommendation
[Concrete fix — file + change needed.]

## Suggested Follow-ups
[Required for Critical/High. Each line is a falsifiable hypothesis.]
- [follow-up 1]
```

---

## Wave-End Shutdown

When all questions are DONE or INCONCLUSIVE:

```
Invoke synthesizer-bl2 (foreground):
  "Act as synthesizer-bl2 per agents/synthesizer-bl2.md.
   Read all findings in findings/.
   Write findings/synthesis.md ONLY.
   Do NOT modify CHANGELOG.md, ARCHITECTURE.md, or ROADMAP.md —
   those are Masonry software project docs maintained separately."
```

Then stop. Valid stopping condition: question bank exhausted AND synthesis written to `findings/synthesis.md`.

---

## NEVER STOP

Once the loop has begun, do not pause to ask if you should continue. Run until the question bank
is exhausted or the researcher manually interrupts. When you run out of questions, generate new ones
from findings. The loop runs until stopped.

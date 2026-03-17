# BrickLayer 2.0 — Project Brief

**Authority**: Tier 1 — Human only. This document overrides all agent findings.
**Status**: Active design phase
**Owner**: Tim (trg16)

---

## What BrickLayer 2.0 Is

A **universal project lifecycle framework** that applies structured AI-driven investigation to any complex project — from first idea to running production system. Every mode addresses a distinct type of work that occurs at a specific stage of a project's life.

The name is literal: **it lays every brick**. From conception through maintenance, BrickLayer provides the right tool for the current stage of any project.

This is not a rewrite of BrickLayer — it is an extension. The existing `bl/` engine, `campaign.py`, `questions.md` format, `findings/`, `results.tsv`, and `synthesis.md` remain the foundation. BrickLayer 2.0 adds **modes** on top of this foundation.

---

## The Mode System

Each mode is a distinct operational posture with its own:
- `program.md` — loop instructions for that mode
- Agent roster — which specialized agents run
- Verdict vocabulary — what constitutes PASS/FAIL in this context
- Question domain — what kind of questions get asked
- Runner preference — how evidence is collected

### The 9 Modes

| Mode | Stage | Question Being Answered |
|------|-------|------------------------|
| **Frontier** | Conception | What should this even be? What's possible? |
| **Research** | Validation | Is this idea grounded? What does evidence say? |
| **Validate** | Pre-build | Is this design correct before we build it? |
| **Benchmark** | Baseline | What are the measurable starting conditions? |
| **Diagnose** | Discovery | What's broken? Why? Where exactly? |
| **Fix** | Repair | Implement a diagnosed fix and verify it worked |
| **Audit** | Compliance | Does this meet a known standard? |
| **Evolve** | Improvement | How do we improve what's healthy? |
| **Predict** | Foresight | What will fail next given current trajectory? |
| **Monitor** | Continuity | Is the system still healthy? Alert on drift. |

---

## The Lifecycle Flow

A project moves through modes in roughly this sequence. Not all modes are required for every project — the human chooses which apply.

```
CONCEPTION
  └─ Frontier ──────────────────────────────── "What could this be?"
       ↓
VALIDATION
  └─ Research ──────────────────────────────── "Does this hold up?"
       ↓
PRE-BUILD
  └─ Validate ──────────────────────────────── "Is the design right?"
  └─ Benchmark ─────────────────────────────── "What's the baseline?"
       ↓
BUILD (Claude Code / autopilot — outside BrickLayer)
       ↓
POST-BUILD QUALITY
  └─ Audit ─────────────────────────────────── "Does it meet standards?"
  └─ Diagnose ──────────────────────────────── "What's broken?"
       ↓ (on DIAGNOSIS_COMPLETE finding)
  └─ Fix ───────────────────────────────────── "Implement + verify"
       ↓
ONGOING
  └─ Evolve ────────────────────────────────── "Make healthy things better"
  └─ Predict ───────────────────────────────── "What breaks next?"
  └─ Monitor ───────────────────────────────── "Still healthy? Alert."
```

Modes can also cycle back. A Diagnose finding seeds a Fix. A Fix produces a Benchmark delta. An Evolve run can create new Diagnose questions.

---

## The Projects This Covers

| Project | Starting Mode | Current Stage |
|---------|--------------|---------------|
| **Recall** | Already in Diagnose/Fix | Ongoing — 5 deployment blockers open |
| **ADBP** | TBD | TBD based on current state |
| **Legal** | Research | Pre-build — need regulatory landscape |
| **Uncreated App** | Frontier | Conception — doesn't exist yet |
| **UI/UX Development** | Validate + Audit | Design compliance against known standards |
| **Simulation Creation** | Validate | Does the simulation match empirical reality? |

---

## Key Invariants (Never Violate)

1. **One `project-brief.md` per project** — human authority, never modified by agents
2. **`findings/` accumulates across all modes** — a Frontier finding can inform a Diagnose question 3 months later
3. **`synthesis.md` is living** — updated at the end of every mode session
4. **Mode is declared in the question**, not globally — a single questions.md can mix modes
5. **DIAGNOSIS_COMPLETE is a terminal state** — once root cause is identified at code level, stop re-checking. Do not re-add the question until code changes.
6. **Fix mode requires a DIAGNOSIS_COMPLETE finding as input** — never fix blind
7. **Frontier produces ideas, not verdicts** — HEALTHY/FAILURE don't apply; output is `PROMISING`, `WEAK`, `BLOCKED`
8. **Monitor never modifies findings** — it only reads, measures, and alerts

---

## Extended Verdict Vocabulary

The existing HEALTHY / WARNING / FAILURE / INCONCLUSIVE remain. Additional verdicts for specific modes:

| Verdict | Mode | Meaning |
|---------|------|---------|
| `PROMISING` | Frontier | Idea has signal worth pursuing |
| `WEAK` | Frontier | Idea has fundamental problems |
| `BLOCKED` | Frontier | Idea requires a prerequisite not yet met |
| `CALIBRATED` | Benchmark | Baseline captured successfully |
| `DIAGNOSIS_COMPLETE` | Diagnose | Root cause identified at code level; fix is specified |
| `PENDING_EXTERNAL` | Any | Blocked by an external event (cron window, deploy, date) |
| `FIXED` | Fix | Fix deployed and verified |
| `FIX_FAILED` | Fix | Fix attempted but verification failed |
| `COMPLIANT` | Audit | Meets the standard |
| `NON_COMPLIANT` | Audit | Violates the standard |
| `SUBJECTIVE` | Any | Requires human judgment; campaign pauses for input |

---

## Architecture Changes from BrickLayer 1.x

### What Changes

1. **`mode:` field in questions.md** — extended from runner type to operational mode. Two sub-fields:
   - `mode:` — operational mode (diagnose, fix, research, frontier, etc.)
   - `runner:` — evidence collection method (agent, subprocess, http, correctness, etc.)

2. **`modes/` directory per project** — contains per-mode `program.md` files. The campaign loop reads the question's `mode:` field and loads the corresponding `modes/{mode}.md` as loop instructions.

3. **New verdict types** — `DIAGNOSIS_COMPLETE`, `PENDING_EXTERNAL`, `FIXED`, `PROMISING`, `WEAK`, `BLOCKED`, `COMPLIANT`, `NON_COMPLIANT`, `SUBJECTIVE`, `CALIBRATED`

4. **`DIAGNOSIS_COMPLETE` suppression** — when a finding is marked `DIAGNOSIS_COMPLETE`, it is automatically suppressed from future wave generation until a relevant commit is detected or the human re-activates it.

5. **`PENDING_EXTERNAL` with `resume_after:`** — questions with external blockers are parked with a `resume_after: ISO-8601` timestamp. They rejoin the active question bank when the timestamp passes.

6. **Fix mode takes `--finding=` input** — `fix` mode requires a `DIAGNOSIS_COMPLETE` finding file as input. It reads the finding's specified fix, implements it, and runs verification.

7. **Frontier mode produces `ideas.md`** — in addition to findings, Frontier mode outputs `ideas.md` — a structured list of concepts, connections, and hypotheses for human review.

### What Does NOT Change

- `campaign.py` core loop — unchanged
- `questions.md` format — additive only (new fields, not replacing old ones)
- `findings/` format — additive (new verdict types, same structure)
- `results.tsv` — additive (new verdict values)
- `synthesis.md` — unchanged
- `bl/runners/` — additive (new runners for new modes, existing runners untouched)
- `constants.py` per project — unchanged
- `program.md` still exists at project root — becomes the default mode program (diagnose)

---

## What Misunderstandings to Avoid

- **BrickLayer 2.0 is not a rewrite** — it extends what exists. Every existing project still works.
- **Modes are not sequential requirements** — a project can skip modes, run them out of order, or loop back.
- **Fix mode is not a magic button** — it implements what Diagnose already fully specified. It still requires code access and test verification.
- **Frontier is not brainstorming** — it is structured hypothesis generation with explicit `PROMISING`/`WEAK`/`BLOCKED` verdicts. It produces grounded ideas, not wishes.
- **Monitor is not Diagnose** — Monitor checks known metrics against thresholds. Diagnose finds unknown failures. They are complementary, not duplicates.
- **The `mode:` field in questions.md was always the runner type** — the new `mode:` is the operational mode. Rename the runner field to `runner:` in the question spec to avoid confusion.

---

## Ground Truth Numbers (from bricklayer-meta Wave 1)

- Real novelty curve is J-shaped: early 15% signal → mid 65% signal (not monotonic decay)
- True question redundancy: 8.5% re-checks, not 15% assumed
- Synthesis coherence in real campaign: ~0.87 (well above 0.35 failure threshold)
- Fix convergence: ~8% — BrickLayer diagnoses; humans deploy
- Peer review coverage in Recall: 6.7% (only waves 13-16 active)
- DIAGNOSIS_COMPLETE needed to suppress 18-wave re-check loops
- Universal portability: 4 changes, ~9 days engineering

---

## Open Questions (for Wave 1 research)

These are the questions BrickLayer 2.0 will investigate about itself:
- What is the minimal `program.md` change to support mode dispatch?
- How does the question bank represent mixed-mode campaigns?
- What does a Frontier session actually look like in practice?
- How does Fix mode integrate with the existing `fixloop.py`?
- What is the right `resume_after:` mechanism for PENDING_EXTERNAL questions?
- How does Monitor differ from running Diagnose on a cron?
- Should modes share one `findings/` directory or have separate subdirectories?
- How does a project graduate from Frontier → Research → Validate without losing context?

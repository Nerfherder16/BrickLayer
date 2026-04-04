# Frontier Mode — Program

**Purpose**: Unconstrained idea generation. No failure thresholds. No prior assumptions.
Produce grounded, structured ideas that can seed Research or Validate mode.

**Verdict vocabulary**: PROMISING | WEAK | BLOCKED (not HEALTHY/FAILURE)
**Output**: `findings/` entries + `ideas.md` — a living idea registry
**Tone**: Expansive, speculative, non-judgmental. Every question is "what if?" or "what could?"

---

## Loop Instructions

### Per-question

1. Read the question. It will be in one of these forms:
   - "What could X become if Y constraint were removed?"
   - "What analogues exist for this problem in other domains?"
   - "What is the most ambitious version of this idea?"
   - "What prerequisite must exist before this is possible?"

2. **Do not run simulations.** Evidence is gathered via:
   - Web search (Exa, Firecrawl) for analogues, prior art, market signals
   - Reading existing project docs and findings for context
   - Agent reasoning grounded in known facts

3. **Produce a structured idea**, not a verdict on existing reality. Ask:
   - What is the core mechanism of this idea?
   - What does it require to work? (prerequisites)
   - What is the failure mode of this idea? (not the system — the idea itself)
   - What is the most interesting version of this?

4. **Score the idea on two feasibility axes** (both required):
   - `F_principle` (0.0–1.0): Can this work in a system like this in principle? Score against the mechanism, not the current codebase.
   - `F_now` (0.0–1.0): Does the current codebase have the prerequisites to build this today? Score against what exists right now.
   - Report both in the finding. A high F_principle + low F_now = sound idea with prerequisite gap.

5. **Assign one verdict**:
   - `PROMISING` — F_principle ≥ 0.6 and F_now ≥ 0.3 (viable and buildable near-term)
   - `WEAK` — F_principle < 0.5 (fundamental problem with the idea itself)
   - `BLOCKED` — F_principle ≥ 0.6 but F_now < 0.3 (sound idea, prerequisites missing — name them explicitly)

   **Expected distribution**: PROMISING 40–60%, WEAK 20–30%, BLOCKED 20–30%.
   If PROMISING > 80%, your F_principle threshold is too loose — tighten novelty criteria.

6. **Before designing, verify existence**: Run an absence check (grep/Glob) to confirm the mechanism doesn't already exist in the codebase. An absence proof is a valid finding that often outranks a full architectural design in practical value.

   Example: "Does the codebase contain any use of SimHash?" → grep exhaustively → "SimHash absent from entire repo" is a concrete Frontier finding.

7. **Frontier findings that don't map to the current codebase are NOT failures.** The gap between the frontier ideal and the current system IS the roadmap. Evaluate on quality of the target architecture, not on immediate buildability.

8. Write finding to `findings/{ID}.md` with standard format.
   Also append to `ideas.md` — one line per idea: `[ID] [verdict] [F_principle/F_now] [one-sentence idea summary]`

### Wave structure

- 4-6 questions per wave, all speculative
- Hypothesis generator should be prompted: "Generate questions that explore what this system COULD be, not what it IS. Focus on expansion, analogy, and removal of constraints."
- No saturation floor — Frontier waves can run indefinitely (ideas don't saturate)
- Stop condition: human signals "enough ideas, move to Research"

### Handoff criteria

| Frontier verdict | Handoff condition | Target mode |
|---|---|---|
| PROMISING (F_now ≥ 0.3) | Human approves | Research — stress-test the idea's assumptions |
| PROMISING (F_now < 0.3) | Human approves | Validate — confirm design before building prerequisites |
| WEAK | Fundamental flaw identified | Archive — revisit only if constraints change |
| BLOCKED | Prerequisite identified | Diagnose — trace exactly what is missing and how to build it |

### Session end

Update `ideas.md` with a **Top 3** section — the three most promising ideas from this session, with F_principle/F_now scores and the reasoning for each. These become the seed questions for Research mode.

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

4. **Assign one verdict**:
   - `PROMISING` — the idea has a viable mechanism and no fatal prerequisite gaps
   - `WEAK` — the idea has a fundamental problem (market doesn't exist, prerequisite impossible, etc.)
   - `BLOCKED` — the idea is sound but requires X to happen first (name X explicitly)

5. Write finding to `findings/{ID}.md` with standard format.
   Also append to `ideas.md` — one line per idea: `[ID] [verdict] [one-sentence idea summary]`

### Wave structure

- 4-6 questions per wave, all speculative
- Hypothesis generator should be prompted: "Generate questions that explore what this system COULD be, not what it IS. Focus on expansion, analogy, and removal of constraints."
- No saturation floor — Frontier waves can run indefinitely (ideas don't saturate)
- Stop condition: human signals "enough ideas, move to Research"

### Session end

Update `ideas.md` with a **Top 3** section — the three most promising ideas from this session, with the reasoning for each. These become the seed questions for Research mode.

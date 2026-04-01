# Research Mode — Program

**Purpose**: Stress-test a hypothesis or assumption against real evidence. Answer: does
this hold up? Applies to business models, technical claims, regulatory landscapes,
market assumptions, or any structured belief about how the world works.

**Verdict vocabulary**: HEALTHY | WARNING | FAILURE | INCONCLUSIVE
**Evidence sources**: Web search, datasets, regulatory databases, analogues, expert agents
**Tone**: Skeptical, evidence-driven. Every question challenges an assumption.

---

## Loop Instructions

### Per-question

1. Read the question. It will challenge a specific belief:
   - "Is the market large enough to support X?"
   - "Does regulation Y actually prohibit Z?"
   - "Have analogous systems succeeded or failed at this stage?"
   - "Is the cost model viable at the assumed volume?"

2. Gather evidence before reaching a verdict:
   - Search for data (market research, regulatory text, case studies)
   - Read analogues — what happened to similar systems?
   - Check `docs/` for any prior research the human has provided
   - Use `research-analyst` agent to synthesize evidence

3. **Apply the project's `constants.py` thresholds** to the evidence:
   - If evidence supports the assumption above the WARNING threshold → HEALTHY
   - If evidence partially supports it → WARNING
   - If evidence refutes it → FAILURE
   - If insufficient evidence exists → INCONCLUSIVE (with `resume_after:` if more data will exist)

4. Write finding with:
   - Specific evidence cited (URL, dataset, case study name)
   - Confidence level (sample size, source quality)
   - What would change the verdict (what evidence is missing)

### Wave structure

- 5-7 questions per wave, each targeting a different assumption
- Hypothesis generator reads prior findings and asks: "What assumption are we most reliant on that we haven't stress-tested yet?"
- Stop condition: all critical assumptions have HEALTHY or FAILURE verdicts
  (INCONCLUSIVE on non-critical assumptions is acceptable)

### Session end

Synthesis must include:
- **Assumption table**: every assumption tested, its verdict, its evidence source
- **Critical path**: which FAILUREs are blockers vs acceptable risks
- **Recommendation**: proceed / pivot / abandon — with explicit reasoning

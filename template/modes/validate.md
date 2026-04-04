# Validate Mode — Program

**Purpose**: Review a proposed design, architecture, or plan BEFORE it is built.
Catch problems at the design stage — the cheapest point to fix them.
Input is a spec, proposal, or design doc. Output is a structured critique.

**Input**: A design document, architecture proposal, API spec, or plan
**Verdict vocabulary**: HEALTHY | WARNING | FAILURE | SUBJECTIVE
**Evidence sources**: The design doc itself, analogues, constraints from project-brief.md

---

## Loop Instructions

### Pre-flight

1. Read the design document (required input)
2. Read `project-brief.md` for constraints, invariants, and known failure modes
3. Read any prior `findings/` that are relevant to this design area
4. Identify the design's claims — what does it promise to do?

### Per-question

Questions in Validate mode challenge specific claims or assumptions in the design:
- "Does this API contract handle the edge case where X is null?"
- "Is the proposed data model consistent with the stated performance requirement?"
- "Does this architecture avoid the failure mode identified in finding Q13.1?"
- "Is this naming convention consistent with the existing codebase?"

Evidence gathering:
- Check the design against `project-brief.md` invariants
- Check for analogues — have similar designs failed in prior findings?
- Check mathematical consistency (does the model actually produce what it claims?)
- For UI/UX designs: check against `figma-designer-guide.md` constraints

Verdict assignment:
- `HEALTHY` — claim is valid, design is consistent with constraints
- `WARNING` — design works but has a risk or a missing consideration
- `FAILURE` — design has a fundamental problem that will cause a real failure
- `SUBJECTIVE` — verdict requires human judgment (aesthetic, strategic, preference)
  For SUBJECTIVE: write the question + evidence, then PAUSE and ask the human

### Special: SUBJECTIVE verdict handling

When a question requires human judgment:
1. Write the finding with `SUBJECTIVE` verdict
2. Include the evidence and framing: "Here is what I found. Here are the options. I can't decide this for you."
3. STOP the loop and output the question to the terminal
4. Wait for human input, then resume with the human's verdict recorded

### Wave structure

- Questions are derived from the design document's claims, not hypothesis-generated
- Work through the design systematically (section by section)
- FAILURE findings generate follow-up questions to understand severity
- Stop condition: all design claims validated or flagged

### Session end

Produce `validation-report.md`:
- Table of all design claims and their verdicts
- All FAILURE findings with exact location in the design doc
- All SUBJECTIVE items awaiting human decision
- Go/No-Go recommendation with reasoning

# Agent Meta-Campaign — Project Brief

## What This Campaign Is

A BrickLayer 2.0 campaign that stress-tests the BrickLayer 2.0 agent fleet itself. The system under investigation is the set of agent definition files in `../../template/.claude/agents/`. The goal is to find gaps, inconsistencies, prompt weaknesses, and coordination failures in the agent architecture.

## What "Failure" Means Here

An agent is FAILING if:
- Its prompt produces vague or unfalsifiable verdicts
- Its output format doesn't match what downstream agents expect (interface mismatch)
- Its scoring criteria are uncalibrated (HEALTHY when it shouldn't be)
- It has responsibilities that overlap significantly with another agent (duplication)
- It references tools or recall_store patterns inconsistently with other agents
- It is called by program.md or mortar but has no .md definition (phantom agent)
- Its description in frontmatter is too vague for forge-check to match it to a mode

## Key Invariants

1. Every agent called in `program.md` must have a corresponding `.md` file in `template/.claude/agents/`
2. Every agent that writes a finding must include a `## Evidence` section with concrete outputs
3. Every agent that runs code must have a verification step
4. No two agents should have identical primary responsibilities
5. Mortar's routing table must cover all `**Mode**:` values that appear in questions.md
6. All agents must have a `## Recall` section and use consistent `domain="{project}-bricklayer"` format
7. Background agents must output a JSON output contract block

## Known Past Issues (from BL 2.0 self-audit)

- Wave 15: crucible.py used BL 1.x field names — agents may have similar version-skew issues
- Wave 14: synthesizer.md had outdated verdict taxonomy — only listed 4 verdicts, not 26+
- Wave 13: followup.py sub-question quality was poor
- Wave 12: regression detection was unreliable

## Human Authority

This project-brief is Tier 1 authority. Agent findings that contradict this brief must note the conflict explicitly.

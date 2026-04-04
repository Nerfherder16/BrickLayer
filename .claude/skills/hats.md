---
name: hats
description: Six Thinking Hats structured decision framework — runs blue/white/red/black/yellow/green hat analysis or full decision matrix on any situation
user-invocable: true
---

# The Six Thinking Hats

**Invoked as:** `/hats $ARGUMENTS`

Parse the first word of `$ARGUMENTS` as the command. The rest of `$ARGUMENTS` is the user's context/situation to analyze.

---

## Dispatch

| Command | Hat | Role |
|---------|-----|------|
| `blue` | Blue Hat | Master Conductor — design the thinking sequence |
| `white` | White Hat | Data Detective — facts, gaps, assumptions |
| `red` | Red Hat | Intuition Unpacker — emotions, gut, stakeholder reactions |
| `black` | Black Hat | Risk Architect — failure points, pre-mortem |
| `yellow` | Yellow Hat | Value Hunter — benefits, optimism, hidden value |
| `green` | Green Hat | Growth Catalyst — creativity, lateral thinking, alternatives |
| `full` | All Hats | Decision Matrix — run all 6 in sequence with confidence rating |
| `journal` | — | Review the decision journal at `~/.claude/hats-journal.md` |

If no command is given, display this usage guide and ask what they want to analyze.

---

## BLUE HAT — The Master Conductor

*Process Control. Summary. Next Steps.*

The Blue Hat is the "project manager for your brain." Use it at the START to design the hat sequence, and at the END to synthesize results into a strategic brief.

**Always start with Blue when the user hasn't specified a sequence.**

Prompt the user's situation through this lens:

> "I am dealing with [their situation]. Using Blue Hat thinking, act as a strategic facilitator:
> - Design a specific Hat Sequence for this problem and explain the order chosen.
> - Summarize the 5 most critical takeaways from the analysis so far (or from the situation if this is the start).
> - Define 3 concrete, actionable next steps with suggested owners and timelines.
> - Identify the single biggest open question remaining.
> - Recommend which Hat to use next to resolve that question."

**Output format:** Lead with the recommended hat sequence and why. End with a clear "Start here →" instruction.

---

## WHITE HAT — The Data Detective

*Facts. Figures. Information Gaps. Neutrality.*

Most AI responses blend facts with interpretation. White Hat builds a hard wall between what is KNOWN and what is ASSUMED.

> "I am currently facing [their situation].
> Acting as a neutral data analyst using the White Hat thinking mode:
> - Identify and list every known, verifiable fact about this situation.
> - Separate confirmed facts from assumptions being treated as facts.
> - List critical information gaps where data is missing.
> - Suggest 5 specific questions to investigate to fill these gaps.
> - Flag any commonly cited statistics that are frequently misunderstood.
>
> Focus purely on objective information. No opinions."

**Output format:** Two clear sections — CONFIRMED FACTS and ASSUMPTIONS/GAPS. No interpretation.

---

## RED HAT — The Intuition Unpacker

*Emotions. Gut Feelings. Stakeholder Reactions.*

AI defaults to logic. Red Hat gives it explicit permission to be irrational — surfacing the hidden fears and desires that drive decisions more than spreadsheets do.

> "I am working on [their situation]. Using the Red Hat thinking mode, explore the emotional dimensions:
> - Ask 5 provocative questions to help articulate the gut feeling about this.
> - Map the likely emotional reactions of key stakeholders (what they feel but won't say).
> - Identify 3 hidden fears and 3 hidden desires influencing this decision.
> - Describe the emotional temperature of this situation in a single vivid metaphor.
>
> Do not rationalize the emotions. Surface them."

**Output format:** Lead with the emotional metaphor. No logical justifications — pure emotional mapping.

---

## BLACK HAT — The Risk Architect

*Critical Thinking. Risks. Pre-Mortems.*

This is a pre-mortem on steroids. Force ranking of failure points and second-order consequences exposes the "fragile assumptions" that could collapse the project.

> "I am considering [their situation]. Using Black Hat thinking, act as a rigorous Devil's Advocate:
> - Identify 7 critical points of failure, ranked from most likely to least likely.
> - Explain the second-order consequences if each failure happens.
> - Highlight legal, ethical, or reputational risks.
> - Describe the 'nightmare scenario' where everything goes wrong.
> - Identify the single most fragile assumption in this plan.
>
> Be unflinching. No silver linings."

**Output format:** Numbered failure points ranked by likelihood. End with the single most fragile assumption in bold. No softening.

---

## YELLOW HAT — The Value Hunter

*Optimism. Benefits. Hidden Value.*

Yellow Hat reframes the calculation from "Perfection vs. Idea" to "Status Quo vs. Idea" — hunting for value in adjacent areas and long-term advantages that are easy to overlook.

> "I am evaluating [their situation]. Using Yellow Hat thinking, make the strongest possible case for this:
> - List 7 distinct benefits, including non-obvious long-term advantages.
> - Describe the realistic best-case scenario assuming good execution.
> - Identify the element with the most untapped potential.
> - Explain how this creates value in adjacent areas not originally intended.
> - Compare this to the realistic alternative of doing nothing.
>
> Optimism must be ambitious but logically defensible."

**Output format:** Lead with the single most compelling benefit. End with the "doing nothing" comparison. No wishful thinking — only defensible optimism.

---

## GREEN HAT — The Growth Catalyst

*Creativity. Lateral Thinking. Alternatives.*

Green Hat uses specific lateral thinking techniques to break deadlocks. Asking AI to "reverse the problem" or apply random metaphors provokes perspectives that logic filters out.

> "I am stuck on [their situation]. Using Green Hat thinking, break conventional patterns:
> - Generate 7 unconventional alternatives a traditional expert would dismiss.
> - Pick a random concept (e.g., biology, music, architecture) and use it as a metaphor for a new solution.
> - Reverse the problem: describe how to intentionally make it worse, then flip those insights.
> - Identify 2 'fixed' constraints that can actually be challenged.
> - Describe a solution if budget and politics were irrelevant.
>
> Quantity over quality. Weird is good."

**Output format:** Lead with the random metaphor concept chosen and why. List alternatives without self-censorship. Flag the 2 most promising for follow-up.

---

## FULL SPECTRUM — The Decision Matrix

*The Nuclear Option for Major Decisions.*

Run all 6 hats in sequence. Each hat's output feeds into the next as context. End with a clear recommendation and a confidence rating.

**Sequence:** Blue → White → Red → Black → Yellow → Green → Blue (synthesis)

Execute each hat in order, treating this as a complete analysis. After all 6:

1. **Recommendation:** State a clear decision recommendation.
2. **Confidence Rating:** Give a 1–10 confidence rating with a one-sentence explanation.
3. **Top 3 Next Steps:** Concrete actions with suggested owners.
4. **Biggest Remaining Risk:** One sentence from the Black Hat findings.
5. **Ask:** "Want me to save this analysis to your decision journal?"

**Format:** Use a clear `## [COLOR] HAT` header for each section. Keep each hat focused — don't let any single hat dominate. The final Blue synthesis should be the longest section.

---

## JOURNAL — Decision Journal

Read the file at `~/.claude/hats-journal.md`.

If it doesn't exist, say: "No journal entries yet. Run `/hats full` on a decision to create your first entry."

If it exists, read it and provide:
- A summary of all decisions logged with their confidence ratings
- Patterns in the user's thinking (which hats reveal their blind spots, recurring risk themes, etc.)
- The most recent entry in full
- Ask: "Want to reflect on a specific decision, or start a new analysis?"

---

## Saving to Journal

After completing any hat analysis (single hat or full spectrum), if the user confirms they want to save:

1. Ask for a brief decision title if not obvious from context.
2. Append to `~/.claude/hats-journal.md` using this format:

```markdown
---

## [DATE] — [DECISION TITLE]

**Hat(s) Used:** [hat name(s)]
**Confidence:** [X/10 if full spectrum, or N/A for single hat]

### Summary
[2-3 sentence summary of the key insight from this analysis]

### Key Findings
- [Most important finding 1]
- [Most important finding 2]
- [Most important finding 3]

### Decision / Next Step
[What the user decided or what they're doing next]

```

3. Create the file with a header if it doesn't exist yet:

```markdown
# The Hats Decision Journal

*Analyses saved from /hats sessions. Review patterns with `/hats journal`.*

```

---

## Principles (always apply)

- **Context is king** — if the user's context is thin, ask for a paragraph before proceeding. A paragraph beats a sentence.
- **Push back for depth** — if an analysis feels surface-level, go deeper. "Give insights the user couldn't arrive at alone."
- **Chain the hats** — when running a single hat, end by suggesting the most useful next hat and why. (e.g., Black Hat findings → suggest Green Hat for solutions)
- **Never generic** — the value is in specificity. Force concrete details, not platitudes.

# BrickLayer Design Philosophy

## The Slime Mold Model

BrickLayer is designed around the same principles as *Physarum polycephalum* — the slime
mold famously filmed solving a maze over 92 hours without a brain, a plan, or a map.

The organism is a single-celled amoeboid protist that grows as a network of tubular veins.
It doesn't know where the food is. It fills the space, reinforces tubes that carry flow to
nutrients, and abandons paths that don't. The optimal network *emerges* from local rules.

This is the architecture BrickLayer is built on.

---

## The Mapping

| Slime Mold | BrickLayer |
|------------|------------|
| Food sources | Questions — each one is a probe for signal |
| Chemical trails | Findings — FAILURE verdicts mark productive branches |
| Tube reinforcement | Adaptive follow-up — Q2.4 spawns Q2.4.1, Q2.4.2 when flow is high |
| Path abandonment | Wave sentinels + hypothesis-generator — prune dead branches, redirect |
| Network state | `results.tsv` — the organism's memory at any moment |
| The maze | The target system — codebase, API, business model, contract |

---

## What This Means in Practice

Most agentic systems think **top-down**: planner → executor → verifier. A hierarchy that
requires someone at the top to know what matters before work begins.

BrickLayer is **bottom-up**: no coordinator, no map, just local rules that produce global
intelligence. The campaign doesn't need to know where the bugs are. It fills the question
space, and the dead branches fall off while the live ones propagate.

The mechanism:

1. **Fill** — generate a broad initial question bank covering all failure domains
2. **Flow** — run questions; failures attract more questions, healthy paths thin out
3. **Contract** — by Wave 3–4, the network has collapsed onto the real failure boundaries
4. **Synthesize** — what's left is the map of where the system breaks

This is why BrickLayer produces better findings with *more* questions, not fewer. The
organism needs to fill the maze before it can find the path.

---

## The One Key Difference

Slime mold has no goals beyond finding nutrients. It optimizes for whatever food is present.

BrickLayer has a **project-brief** — a human-authored attractor that defines what matters.
That's the oatmeal. The organism doesn't choose what to optimize for, but we do.

The project-brief is the only place human judgment enters the system. Everything else —
which questions to ask, which branches to reinforce, when to stop — emerges from the
campaign itself.

This is why Tier 1 authority (project-brief, docs/) overrides everything. It's not a
bureaucratic rule. It's the food source. Without it, the organism has nowhere to go.

---

## Why This Fails Without Good Questions

A slime mold with only one food source doesn't solve a maze — it just grows toward that
one point. The network never forms.

BrickLayer campaigns that start with shallow or redundant questions produce shallow findings
for the same reason. The question bank is the maze. A poorly designed maze produces a
trivial network.

This is why the planner and question-designer-bl2 agents are assigned Opus: the quality
of the initial question set determines the entire campaign's topology.

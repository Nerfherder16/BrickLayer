# Frontier Discovery Program

This research loop maps **unexplored territory** — mechanisms, architectures, and approaches
that have no current production implementation but are validated in adjacent fields.

The goal is NOT competitive benchmarking. The goal is to find things no one has built yet
and score them by novelty × evidence × feasibility.

---

## Setup

1. `git checkout -b {project}-frontier/$(date +%b%d | tr '[:upper:]' '[:lower:]')`
2. Read `project-brief.md` — what problem does this project solve at its core?
3. Read `questions.md` — the question bank (waves by research method)
4. Verify baseline: `python simulate.py` → should print `verdict: FAILURE` (no ideas yet)
5. Go.

---

## The Research Loop

Each question produces one or more **IDEAS**. Every idea gets scored and added to `IDEAS`
in `simulate.py`. The loop continues until the question bank is exhausted.

### Step-by-step

1. Pick the next PENDING question
2. Route to the correct agent based on question type (see Question Types below)
3. Agent produces a finding in `findings/<question_id>.md`
4. Extract IDEAS from the finding — each idea gets a `(novelty, evidence, feasibility)` tuple
5. Add each idea to `IDEAS` in `simulate.py`
6. `python simulate.py` — read the new scores
7. Log to `results.tsv`
8. Mark question DONE
9. Check for follow-ups (see Live Discovery)

---

## Question Types → Agent Routing

| Question tag | Agent | What it does | Pre-step |
|---|---|---|---|
| `[ADJACENT]` | `adjacent-field-researcher` | Mines a specific non-AI field for memory mechanisms | **Run web search first** — see below |
| `[ABSENCE]` | `absence-mapper` | Verifies a candidate idea has no production implementation | **Run web search first** — see below |
| `[TABOO]` | `taboo-architect` | Designs from first principles with forbidden word list | None — external anchoring defeats the constraint |
| `[ADVERSARIAL]` | `adversarial-pair` | Two agents with opposing priors, synthesizes the middle | None |
| `[PHYSICS]` | `physics-ceiling` | Calculates theoretical minimums, maps gap to current impl | Run Python benchmark — see below |
| `[TIMESHIFTED]` | `time-shifted` | 2032 retrospective — what decisions look right/wrong in hindsight | None |
| `[CONVERGENCE]` | `convergence-analyst` | Filters all findings through current stack, ranks buildable ideas | Read findings/synthesis.md first |

### Pre-step: Web search for [ADJACENT] and [ABSENCE] questions

Before invoking the agent, run 2-3 targeted searches using available MCP tools:

```
mcp__exa__web_search_exa(query="<specific mechanism from question rationale>", num_results=5)
```

Or use firecrawl for specific papers/implementations:
```
mcp__firecrawl-mcp__firecrawl_search(query="<mechanism> production implementation site:arxiv.org OR site:github.com", limit=5)
```

Include the search results as evidence context when invoking the agent. This grounds the finding in current literature rather than training-data priors alone. Do NOT use web search for [TABOO] questions — external anchoring to named systems defeats the constraint.

### Pre-step: Python benchmark for [PHYSICS] questions

When the question asks for latency or throughput at a specific corpus size, run a synthetic benchmark before or alongside the analytical estimate:

```
mcp__plugin_oh-my-claudecode_t__python_repl
```

Use it to run the specific operation (linear scan, ANN search, SIMD dot product) at the stated corpus size with synthetic data matching the real dimensions. Report both the analytical floor AND the empirical measurement. If they diverge by more than 2×, investigate why before scoring.

---

## Idea Scoring Guide

When extracting an idea from a finding, assign three scores:

**NOVELTY** — does any production system implement this?
- `1.0` = searched exhaustively, zero production implementations found
- `0.7` = exists in research papers only, no shipping product
- `0.5` = one obscure implementation exists, not mainstream
- `0.2` = a few systems do this
- `0.0` = table stakes, everyone does it

**EVIDENCE** — validated in the source adjacent field?
- `1.0` = peer-reviewed, replicated, well-established in the field
- `0.7` = strong practitioner consensus, widely used in source field
- `0.5` = credible theory, limited formal study
- `0.2` = one paper, not replicated
- `0.0` = intuition only

**FEASIBILITY** — buildable with the current stack?
- `1.0` = 1-2 week implementation, no new infrastructure
- `0.7` = 2-4 weeks, one new library
- `0.5` = 1-3 months, new component required
- `0.2` = 6+ months, significant new infrastructure
- `0.0` = requires new hardware or years of research

---

## Finding Format

```markdown
# Finding: <question_id> — <short title>

**Question**: [copy from questions.md]
**Question Type**: [ADJACENT | ABSENCE | TABOO | ADVERSARIAL | PHYSICS | TIMESHIFTED | CONVERGENCE]
**Verdict**: BREAKTHROUGH | PROMISING | SPECULATIVE | INCREMENTAL | INCONCLUSIVE
**Severity**: Critical | High | Medium | Low | Info
**Source field**: [e.g. "database systems", "cognitive neuroscience", "CPU architecture"]

## Evidence
[What the adjacent field does. Cite sources. Quote specific studies or mechanisms.]

## Ideas Extracted
[For each idea this finding generates:]

### Idea: <slug>
- **Novelty**: 0.X — [reason: who has/hasn't built this]
- **Evidence**: 0.X — [reason: what validates this in the source field]
- **Feasibility**: 0.X — [reason: what's needed to build it]
- **Description**: [what this would look like in the product]

## Suggested Follow-ups
- [follow-up as falsifiable hypothesis, label with question type]
```

---

## Live Discovery

### After every BREAKTHROUGH finding
Immediately insert follow-up questions at top of next wave. Don't wait.

### Every 5 completed questions
Invoke `hypothesis-generator` with the last 3 findings as context. Add Wave-mid questions.

### At convergence wave start
Invoke `convergence-analyst` with ALL findings as context. It produces a ranked
"build now" list filtered to the current stack. This becomes the final deliverable.

---

## results.tsv format

```
commit	question_id	verdict	primary_metric	key_finding	scenario_name
```

Use `N/A` for primary_metric on questions that don't add new IDEAS.

---

## Recall storage

Store each BREAKTHROUGH or PROMISING idea to Recall:

```
recall_store(
    content="[idea slug]: [description]. N=[novelty] E=[evidence] F=[feasibility]. Source: [field].",
    domain="{project}-frontier",
    tags=["frontier", "agent:{agent-name}", "class:{BREAKTHROUGH|PROMISING}"],
    importance=0.85,
)
```

---

## NEVER STOP

Once started, do not pause to ask permission to continue.
If the question bank is exhausted, invoke `hypothesis-generator` and keep going.
The loop runs until manually interrupted.

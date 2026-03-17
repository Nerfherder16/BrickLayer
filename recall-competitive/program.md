# Recall Competitive Analysis — Research Program

This session maps Recall's competitive position against the market for AI memory systems.
Unlike simulation-focused sessions, **most questions here are research questions** answered
via web search, documentation review, and architectural analysis — not parameter sweeps.

The agent still updates `simulate.py` SCENARIO_PARAMETERS after each finding to reflect
the corrected understanding. This keeps the verdict current as a rolling health indicator.

---

## Setup

1. Agree on a run tag based on today's date (e.g., `mar15`).
2. `git checkout -b recall-competitive/<tag>`
3. Read these files (do not modify):
   - `constants.py` — scoring thresholds and competitor baselines
   - `questions.md` — the question bank
   - `project-brief.md` — Recall architecture and known strengths/weaknesses
4. Read the editable file: `simulate.py`
5. Verify baseline: `python simulate.py` → should show `verdict: FAILURE` with 4 critical gaps
   (this is expected — we're starting from honest pre-research estimates)
6. Initialize `results.tsv` with header row.
7. Go.

---

## What You CAN Do

- Modify `simulate.py` SCENARIO PARAMETERS as findings update your understanding
- Use WebSearch, WebFetch, Exa, Firecrawl to get current competitor data
- Write findings to `findings/<question_id>.md`
- Add follow-up questions to `questions.md`

## What You CANNOT Do

- Modify `constants.py`
- Modify `program.md`
- Change scoring thresholds to make verdicts look better — scores must reflect reality

---

## Research Loop

### For each PENDING question:

1. **Pick the next PENDING question** from `questions.md`
2. **Research it** — use web tools to get current data; do NOT rely solely on training data
   for competitor features (they ship fast; your training data may be stale)
3. **Write the finding** to `findings/<question_id>.md`
4. **Update SCENARIO_PARAMETERS** in `simulate.py` — adjust any scores this finding confirms
   or refutes. Keep changes minimal and focused on what the finding directly addresses.
5. Run `python simulate.py > run.log 2>&1` and grep the verdict
6. **Log to `results.tsv`**
7. **Mark DONE** in `questions.md`
8. If severity is Critical or High, append `## Suggested Follow-ups` and insert into questions.md

### For score updates in simulate.py:

When a finding reveals Recall is STRONGER than initially estimated → raise the score toward 1.0
When a finding reveals Recall is WEAKER or missing a capability → lower the score
When a finding is INCONCLUSIVE → leave the score unchanged
Always update SCENARIO_NAME to describe what changed: "Q1.1: mem0 SDK analysis — updated sdk_ecosystem"

---

## Live Discovery

### After every Critical or High severity finding

Append to the finding file:
```markdown
## Suggested Follow-ups
- [Specific falsifiable question this finding raises]
```
Then insert those as PENDING questions in `questions.md` before the next lower-priority question.

### Every 5 completed questions

Invoke `hypothesis-generator`:
```
Read the 3 most recent findings in findings/. Identify competitive gaps or advantages not
covered by remaining PENDING questions. Add up to 5 new PENDING questions to questions.md.
Label them Wave-mid.
```

---

## Finding Format

```markdown
# Finding: <question_id> — <short title>

**Question**: [copy from questions.md]
**Verdict**: FAILURE | WARNING | HEALTHY | INCONCLUSIVE
**Severity**: Critical | High | Medium | Low | Info

## Evidence
[Specific data points, URLs, version numbers, feature comparisons. Quote sources.]

## Recall vs Competitor Comparison
| Dimension | Recall | [Competitor] | Gap |
|-----------|--------|--------------|-----|
| [feature] | [status] | [status] | [delta] |

## Score Updates
[List which SCENARIO_PARAMETERS were updated and why]
- `sdk_ecosystem`: 0.20 → 0.20 (confirmed, no change)
- `hybrid_retrieval`: 0.10 → 0.10 (confirmed missing)

## Mitigation Recommendation
[What Recall should build, adopt, or restructure — specific and actionable]

## Suggested Follow-ups
[For Critical/High severity only]
- [follow-up hypothesis]
```

---

## Logging to results.tsv

Tab-separated. Header:
```
commit	question_id	verdict	primary_metric	key_finding	scenario_name
```

Use `N/A` for commit hash on pure research questions (no sim parameter change).
Use the post-update `primary_metric` value from simulate.py output.

---

## Severity Definitions

| Severity | Meaning for competitive research |
|----------|----------------------------------|
| Critical | Recall is completely missing a capability that every competitor has. Blocking adoption. |
| High | Recall is significantly behind on a dimension that users explicitly choose competitors for. |
| Medium | Recall is behind but the gap is narrow or the dimension is not decision-critical. |
| Low | Minor gap; unlikely to drive competitor switching. |
| Info | Recall confirmed competitive or ahead; no action needed. |

---

## Research Tools Priority

For current competitor data, prefer this order:
1. **Exa** (semantic search) — best for finding recent technical blog posts, changelogs, comparisons
2. **Firecrawl** — scrape official docs, GitHub READMEs, feature comparison pages
3. **WebFetch** — pull specific URLs (GitHub releases, docs pages)
4. **WebSearch** — fallback for broad queries

Always cite sources with URLs. Flag anything from training data as "(training data — verify)".

---

## NEVER STOP

Once started, run autonomously until all questions are DONE or INCONCLUSIVE.
Generate new questions from findings as needed. Do not pause to ask for permission.

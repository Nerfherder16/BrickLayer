# Evolve Survey — Wave 3
**Date**: 2026-03-24
**Prior waves**: Wave 1 (mode spec improvements), Wave 2 (karen training data fix)

---

## Signal Source 1 — Finding History

| Wave | Questions | Outcomes |
|------|-----------|----------|
| Wave 1 | E1.1, E1.2, E1.3 | 3x IMPROVEMENT |
| Wave 2 | E2.1, E2.2, E2.3 | WARNING + 2x IMPROVEMENT |

No FAILURE findings. No INCONCLUSIVE findings. No recurring WARNING categories.

Wave 2 exposed a systemic eval infrastructure problem (training data self-reference + Windows
encoding) that was deeper than the original E1.3 symptom. The fix produced a 0.30 → 1.00 jump.

**Implication**: eval infrastructure quality is a force multiplier. Broken evals block all future
agent improvement work. Wave 3 should validate the eval pipeline works end-to-end for agents
beyond karen.

---

## Signal Source 2 — Agent Accuracy

| Agent | Records (scored_all.jsonl) | Records (wave13.jsonl) | Eval Score | Target Gap |
|-------|---------------------------|------------------------|------------|------------|
| karen | 379 | 1 | **1.00** (20/20) | **AT TARGET** |
| quantitative-analyst | 45 | 35 | No snapshot | Unknown |
| regulatory-researcher | 7 | 5 | No snapshot | Unknown |
| git-nerd | 4 | 1 | No snapshot | Unknown |
| mortar | 4 | 1 | No snapshot | Unknown |
| research-analyst | 0 | **5** | 0/0 (no data) | Unknown |
| competitive-analyst | 1 | 6 | No snapshot | Unknown |
| synthesizer-bl2 | 0 | 6 | No snapshot | Unknown |
| developer | 2 | 2 | No snapshot | Unknown |
| test-writer | 2 | 2 | No snapshot | Unknown |

**Key observations:**
- `research-analyst` has 0 records in `scored_all.jsonl` — the primary training file. It exists only
  in `scored_all_wave13.jsonl` with 5 records (all HEALTHY verdicts). No eval baseline exists.
- `quantitative-analyst` has 80 records total (45 + 35) but no eval snapshot. It is the second
  most-recorded agent and a core research-loop component.
- The two training files (`scored_all.jsonl` and `scored_all_wave13.jsonl`) are not merged — agents
  recorded in wave13 are invisible to the primary eval pipeline.
- `synthesizer-bl2` has 6 records in wave13 only — also invisible to the primary pipeline.

---

## Signal Source 3 — Git Hotspots (30 days)

| File | Commits | Significance |
|------|---------|--------------|
| CHANGELOG.md | 358 | Automated — expected |
| masonry/questions.md | 71 | Campaign activity churn |
| masonry/src/dspy_pipeline/optimizer.py | 25 | High structural instability |
| masonry/src/hooks/masonry-stop-guard.js | 23 | Behavioral iteration |
| masonry/scripts/run_optimization.py | 18 | Frequent adjustments |
| masonry/agent_registry.yml | 16 | Agent fleet management |
| template/.claude/agents/karen.md | 12 | MIPROv2 overwrite incident (Wave 2) |
| template-frontier/.claude/agents/karen.md | 12 | Same incident |

**Key observations:**
- `optimizer.py` at 25 commits is a structural instability signal. This is the script that overwrote
  karen.md in Wave 2. The MIPROv2 write-back mechanism should be audited.
- `masonry-stop-guard.js` at 23 commits suggests ongoing behavioral tuning without stabilizing.

---

## Signal Source 4 — Recall Signal

Not queried (no structural recall MCP call needed — the finding history and git hotspots provide
sufficient signal).

---

## Candidate Ranking

| # | Candidate | Impact | Ease | ROI | Wave 3? |
|---|-----------|--------|------|-----|---------|
| 1 | **Merge wave13 records into scored_all.jsonl** | High — makes 6 agents eval-able | Easy (file merge + dedup) | HIGH | YES |
| 2 | **research-analyst eval baseline** | High — most-used research agent, currently blind | Medium (need more records or use wave13) | HIGH | YES |
| 3 | **quantitative-analyst eval baseline** | High — 80 records available, never evaled | Easy (run eval_agent.py) | HIGH | YES |
| 4 | **DSPy optimizer write-back audit** | High — caused Wave 2 incident | Medium (read optimizer.py) | HIGH | YES |
| 5 | eval_agent.py "research" signature correctness | Medium — does non-karen eval actually work? | Medium | MEDIUM | YES |
| 6 | masonry-stop-guard.js stability | Low — behavioral, not accuracy | Hard | LOW | BACKLOG |

---

## Wave 3 Questions

| ID | Hypothesis |
|----|------------|
| E3.1 | Merging `scored_all_wave13.jsonl` into `scored_all.jsonl` (with dedup) should make research-analyst, synthesizer-bl2, and 4 other agents eval-able for the first time, enabling baseline score measurement. |
| E3.2 | Running eval on `quantitative-analyst` with the current 80 records should produce a baseline score ≥0.50. If score <0.50, the metric signature is wrong. |
| E3.3 | Running eval on `research-analyst` after the wave13 merge should produce a first baseline score. With only 5 records all labeled HEALTHY, the score may be artificially high — probe with adversarial inputs. |
| E3.4 | The `optimizer.py` write-back mechanism that overwrote `karen.md` in Wave 2 should be audited. Does it have a guard that prevents overwriting non-optimizer content? Is the overwrite scope limited to the DSPy section only? |

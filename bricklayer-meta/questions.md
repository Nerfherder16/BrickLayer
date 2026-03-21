# BrickLayer Meta — Research Questions

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

Research goal: stress-test BrickLayer's campaign quality properties.
Primary metric: campaign_yield (unique actionable findings / total questions run).
Three failure modes under investigation: Verdict Drift, Coverage Collapse, Fix Loop Divergence.

Source of truth for all analysis: `C:/Users/trg16/Dev/autosearch/recall/` (36 waves, real campaign data).
Simulation: `C:/Users/trg16/Dev/autosearch/bricklayer-meta/simulate.py`

---

## Wave 1 — Simulation Calibration (Q1.x)

*Does the simulation's quality model match observable BrickLayer behavior?
These questions run simulate.py at specific parameter values and verify the model
is internally consistent before trusting it for boundary-finding.*

---

## Q1.1 [SIMULATION] Baseline sanity: nominal config produces HEALTHY
**Mode**: subprocess
**Status**: DONE
**Hypothesis**: simulate.py with default parameters produces verdict: HEALTHY and campaign_yield >= 0.70
**Test**:
```
python C:/Users/trg16/Dev/autosearch/bricklayer-meta/simulate.py
```
expect_stdout: verdict: HEALTHY
expect_not_stdout: verdict: FAILURE
timeout: 30
**Verdict threshold**:
- FAILURE: simulate.py exits non-zero, verdict is not HEALTHY, or yield < 0.70
- WARNING: simulate.py runs but wave 4 yield < 0.30 (saturation starts too early)
- HEALTHY: verdict: HEALTHY, campaign_yield >= 0.70, wave breakdown shows smooth decay

---

## Q1.2 [SIMULATION] Novelty cliff: find the DOMAIN_NOVELTY threshold that crosses WARNING
**Mode**: agent
**Agent**: simulation-analyst
**Status**: DONE
**Hypothesis**: There is a specific DOMAIN_NOVELTY value (estimated 0.60–0.75) where campaign_yield crosses below the WARNING threshold of 0.45, even with full peer review. Above this point, peer review cannot compensate because the reviewer faces the same domain blindspot.
**Test**: Modify DOMAIN_NOVELTY in simulate.py from 0.50 to 1.00 in steps of 0.05, keeping all other parameters at default (AGENT_SPECIALIZATION_RATIO=0.65, PEER_REVIEW_RATE=1.0). Record campaign_yield and verdict at each step. Find the exact crossing point. Then repeat the sweep with PEER_REVIEW_RATE=0.0 to measure peer review's correction value at each novelty level.
**Verdict threshold**:
- FAILURE: no crossing point exists (model is miscalibrated — high novelty never causes WARNING)
- WARNING: crossing point exists but is above 0.85 (model is too forgiving of novelty)
- HEALTHY: crossing point found between 0.55 and 0.80, peer review correction is measurable

---

## Q1.3 [SIMULATION] Specialization floor: minimum agent coverage before yield collapses
**Mode**: agent
**Agent**: simulation-analyst
**Status**: DONE
**Hypothesis**: There is a minimum AGENT_SPECIALIZATION_RATIO below which campaign yield degrades faster than linear — a cliff below which generalist fallback accuracy is too low to recover from. Estimated to be around 0.30 (below 30% specialist coverage, yield drops sharply).
**Test**: Sweep AGENT_SPECIALIZATION_RATIO from 0.0 to 1.0 in steps of 0.10. Keep DOMAIN_NOVELTY=0.35 (nominal). Record campaign_yield at each step. Compute the second derivative to find the inflection point where degradation accelerates. Compare to the 0.65 default — how much margin exists before collapse?
**Verdict threshold**:
- FAILURE: yield is linear across the full range (no cliff — model has no nonlinear dynamics)
- WARNING: cliff exists but is below 0.10 (model allows very low specialization)
- HEALTHY: inflection point found between 0.20 and 0.50, consistent with the 65% default having margin

---

## Q1.4 [SIMULATION] Wave count ceiling: when do additional waves hurt more than help?
**Mode**: agent
**Agent**: simulation-analyst
**Status**: DONE
**Hypothesis**: After a certain wave count (estimated 6–8 at 7 questions/wave), additional waves produce more noise than signal — the marginal campaign_yield per wave drops below the WAVE_NOVELTY_FLOOR_FAILURE threshold of 0.15. The campaign should stop before this point.
**Test**: Run simulate.py at WAVE_COUNT = 4, 5, 6, 7, 8, 10, 12 with QUESTIONS_PER_WAVE=7. Record overall campaign_yield AND the final wave's individual wave_yield. Find the wave count where wave_yield_final < 0.15. Then determine: does the overall campaign_yield compensate (averaged over all waves), or does the saturated wave drag the synthesis coherence below threshold?
**Verdict threshold**:
- FAILURE: no ceiling exists — wave_yield never drops below 0.15 regardless of wave count (model doesn't saturate)
- WARNING: ceiling found but only at wave count >= 12 (saturation is unrealistically slow)
- HEALTHY: ceiling found at wave count 6–9, overall yield stays above WARNING until wave count >= 10

---

## Q1.5 [SIMULATION] Questions-per-wave optimum: redundancy vs. coverage tradeoff
**Mode**: agent
**Agent**: simulation-analyst
**Status**: DONE
**Hypothesis**: There is an optimal QUESTIONS_PER_WAVE that maximizes total actionable findings before redundancy dominates. Too few questions = underexploration. Too many = saturation acceleration and diminishing returns. Estimated optimum: 7–10 questions/wave for a 4-wave campaign.
**Test**: Fix WAVE_COUNT=4. Sweep QUESTIONS_PER_WAVE = 3, 5, 7, 10, 12, 15, 20. For each, compute total_actionable (not yield — raw count). Find the QUESTIONS_PER_WAVE that maximizes total_actionable. Then compute the efficiency ratio: total_actionable / total_questions at each point. Report both the maximizing count and the most efficient count (these may differ).
**Verdict threshold**:
- FAILURE: total_actionable increases monotonically (no diminishing returns — model is broken)
- WARNING: optimum is at QUESTIONS_PER_WAVE <= 5 (too restrictive) or >= 15 (too permissive)
- HEALTHY: maximum total_actionable at 6–12 q/wave, efficiency peaks at lower count (7–9)

---

## Wave 1 — Verdict Drift Detection (Q2.x)

*Measure real verdict drift in the existing Recall campaign data.
Does the campaign accurately classify what it finds, or does it produce
confident verdicts for things it can't actually assess?*

---

## Q2.1 [CORRECTNESS] Peer review OVERRIDE rate: calibrate the constants
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The simulation uses BASE_SPECIALIST_ACCURACY=0.875 and BASE_GENERALIST_ACCURACY=0.625, derived from estimated OVERRIDE rates of ~12.5% and ~37.5%. The actual OVERRIDE rate in recall/findings/ may differ. If it does, the simulation constants need recalibration.
**Test**: Read all finding files in `C:/Users/trg16/Dev/autosearch/recall/findings/`. Count files containing `## Peer Review` section with verdict `OVERRIDE` vs `CONFIRMED` vs `CONCERNS`. Separate counts by whether the question had a specialist agent (agent name in question header) vs. fell back to a generalist. Report: specialist OVERRIDE rate, generalist OVERRIDE rate, total sample size, and comparison to constants.py values (0.125 vs 0.375).
**Verdict threshold**:
- FAILURE: actual OVERRIDE rates differ from constants.py by more than 15 percentage points — simulation is miscalibrated
- WARNING: rates differ by 8–15 points — simulation is approximately right but constants should be updated
- HEALTHY: rates within 8 points of constants.py values — simulation is well-calibrated

---

## Q2.2 [CORRECTNESS] Confident-wrong pattern: classify what OVERRIDE verdicts were actually catching
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: Peer reviewer OVERRIDEs split into two types: (A) the primary agent was factually wrong (drift), vs (B) the primary agent was right but incomplete or the situation changed. Type A represents true verdict drift. Type B represents legitimate update. The simulation only models Type A drift — if Type B is dominant, the model overstates true drift.
**Test**: Read all finding files in `C:/Users/trg16/Dev/autosearch/recall/findings/` that contain `## Peer Review` with verdict `OVERRIDE`. For each, read the Peer Review section and classify: did the reviewer override because (A) the primary verdict was factually wrong, (B) the fix was incomplete/wrong, or (C) new evidence emerged after the primary run? Report counts per category. Quote representative examples of each.
**Verdict threshold**:
- FAILURE: Type A (factually wrong) accounts for > 60% of OVERRIDEs — true drift rate is dangerously high
- WARNING: Type A accounts for 30–60% — moderate drift, simulation constants may be slightly high
- HEALTHY: Type A < 30% — most OVERRIDEs are Type B/C (legitimate updates, not drift)

---

## Q2.3 [CORRECTNESS] Synthesis recommendation accuracy: did STOP/PIVOT/CONTINUE prove correct?
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The synthesizer's STOP/PIVOT/CONTINUE recommendations are based on saturated signal. If the synthesizer said CONTINUE but the next wave found nothing new, it was wrong. If it said STOP but real failures remained, it was wrong. Measuring recommendation accuracy is the ultimate test of synthesis coherence.
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/findings/synthesis.md`. Find each STOP/PIVOT/CONTINUE recommendation and the wave it was made in. Then check: for CONTINUE recommendations, did the subsequent wave produce at least 2 new non-redundant findings? For STOP recommendations, were there any open FAILUREs or WARNINGs at the time that had not been addressed? Report accuracy rate for each recommendation type.
**Verdict threshold**:
- FAILURE: CONTINUE accuracy < 60% (synthesizer kept the campaign running past usefulness) OR STOP accuracy < 70% (synthesizer terminated with unresolved failures)
- WARNING: either metric between threshold and 75%
- HEALTHY: CONTINUE accuracy >= 75% and STOP accuracy >= 80%

---

## Q2.4 [CORRECTNESS] False-HEALTHY detection: questions that were marked HEALTHY but had latent failures
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: Some questions marked HEALTHY in early waves later revealed failures when re-examined in later waves. These represent verdict drift that was not caught by peer review — the most dangerous failure mode.
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/results.tsv`. Find question IDs that appear multiple times (re-examined in later waves). For each, check if the initial verdict was HEALTHY and a later run found FAILURE or WARNING. Also check for any `.R` re-examination questions injected by OVERRIDE processing — these are definitional verdict drifts. Report: how many questions had HEALTHY→FAILURE/WARNING reversals, and what the failure categories were.
**Verdict threshold**:
- FAILURE: > 10% of re-examined questions showed HEALTHY→FAILURE reversal (systemic drift)
- WARNING: 5–10% reversal rate
- HEALTHY: < 5% reversal rate — drift is rare and non-systemic

---

## Wave 1 — Coverage & Saturation (Q3.x)

*Does the hypothesis generator actually saturate? Where is the coverage frontier?
What failure modes have no specialist agent?*

---

## Q3.1 [COVERAGE] Wave novelty curve: measure real yield decay across 36 waves
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The simulation models wave yield decaying by WAVE_SATURATION_RATE=0.15 per wave. The real Recall campaign should show a similar decay curve. If the real curve decays faster or slower, the constant needs adjustment. The curve should also show whether "yield" in the simulation (unique actionable / total) maps cleanly onto (FAILURE + WARNING) / total in the real campaign.
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/results.tsv`. Group results by wave number (Q1.x = wave 1, Q2.x = wave 2, etc.). For each wave, compute: total questions run, HEALTHY count, WARNING count, FAILURE count, INCONCLUSIVE count. Compute wave_yield_proxy = (FAILURE + WARNING) / total (findings that produced actionable signal). Plot the decay curve across all 36 waves. Find: wave where yield_proxy first drops below 0.45 (WARNING threshold), and wave where it drops below 0.25 (FAILURE threshold).
**Verdict threshold**:
- FAILURE: yield_proxy shows no decay (flat across waves) — saturation model is wrong
- WARNING: yield_proxy decays but the first drop below 0.45 occurs after wave 15 (saturation unrealistically slow)
- HEALTHY: measurable decay with first WARNING crossing between wave 5 and wave 12

---

## Q3.2 [COVERAGE] Hypothesis generator semantic drift: do late waves recycle early wave questions?
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: After wave 8, the qwen2.5:7b hypothesis generator begins generating questions that are semantically equivalent to Wave 1-3 questions — the same failure modes rephrased. This is the "coverage collapse" pattern. It is measurable by comparing hypothesis fields across waves.
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/questions.md`. For each question, extract the **Hypothesis** field. Group by wave. For waves 1–5 vs. waves 15–20 vs. waves 30–36, identify the distinct failure categories being probed (semantic clustering by topic: dedup, decay, latency, concurrency, etc.). Report: how many distinct failure categories appear in early waves vs. late waves? Is there evidence of recycling (same category, different phrasing) in late waves?
**Verdict threshold**:
- FAILURE: late waves (30+) introduce zero new failure categories — pure recycling
- WARNING: late waves introduce 1–2 new categories (significant recycling, some novelty)
- HEALTHY: each wave cluster introduces at least 3 new failure categories through wave 20

---

## Q3.3 [COVERAGE] Coverage dark matter: failure modes with no specialist agent
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The current agent fleet covers the most common failure categories (performance, correctness, security) but has gaps in emergent/cross-system failure modes. These gaps are visible as INCONCLUSIVE verdicts or questions that consistently use the generalist fallback (fix-agent or probe-runner) rather than a specialist.
**Test**: Read all files in `C:/Users/trg16/Dev/autosearch/agents/`. Extract the stated specialization domain of each agent (what failure category does it handle?). Then read `C:/Users/trg16/Dev/autosearch/recall/results.tsv` and `C:/Users/trg16/Dev/autosearch/recall/questions.md`. For each INCONCLUSIVE verdict, identify what the question was trying to test — is there a matching specialist agent? For FAILURE and WARNING findings, which agent produced the verdict? Report: coverage ratio (questions with specialist / total), and a ranked list of uncovered failure categories by frequency.
**Verdict threshold**:
- FAILURE: coverage ratio < 40% (most questions are running without a specialist — Forge is falling behind)
- WARNING: coverage ratio 40–65%
- HEALTHY: coverage ratio >= 65% (consistent with the 0.65 default in simulate.py constants)

---

## Q3.4 [COVERAGE] Forge effectiveness: do forged agents outperform generalist fallbacks?
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: Forge-created agents should produce lower OVERRIDE rates than generalist fallbacks (they were purpose-built for the failure category). If forged agents perform at generalist-level, the Forge process is creating agents that are too generic to be useful.
**Test**: Read `C:/Users/trg16/Dev/autosearch/agents/`. Identify which agents were created by Forge (look for FORGE_LOG.md or metadata in agent files indicating automated creation). Compare: (a) peer-review OVERRIDE rate for questions run by forged agents vs. (b) OVERRIDE rate for questions run by original human-authored agents vs. (c) OVERRIDE rate for questions that fell back to generalist. Use recall/findings/ peer review sections as the data source.
**Verdict threshold**:
- FAILURE: forged agents have OVERRIDE rate >= generalist fallback (Forge creates useless agents)
- WARNING: forged agents improve on generalist by < 10 percentage points (marginal value)
- HEALTHY: forged agents OVERRIDE rate is 15+ points lower than generalist fallback

---

## Wave 1 — Fix Loop Behavior (Q4.x)

*What does the fix loop actually do to campaign quality?
Does it converge, or does it move failures around?*

---

## Q4.1 [FIX-LOOP] Fix loop convergence: do fixed failures stay fixed?
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: Questions that received a fix-loop repair and were re-classified HEALTHY should not reappear as FAILURE in later waves. If they do, the fix was superficial — it patched the symptom (test passes) without removing the root cause (bug still present, just not triggered by this test).
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/findings/`. Find all finding files that contain `## Fix Attempt` sections (indicates fix-loop ran). For each, note: (a) was the fix resolution RESOLVED or EXHAUSTED? (b) What wave was this? (c) Did any later wave test the same subsystem and find a new FAILURE? Report: fix resolution rate (RESOLVED / total attempts), and recurrence rate (same subsystem fails again within 5 waves of a fix).
**Verdict threshold**:
- FAILURE: recurrence rate > 30% (fixes are cosmetic — root causes remain)
- WARNING: recurrence rate 15–30% (some systemic issues not addressed by fixes)
- HEALTHY: recurrence rate < 15% and RESOLVED rate > 60%

---

## Q4.2 [FIX-LOOP] Fix loop regression risk: identify silent regressions in campaign history
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The fix loop modifies the target system's source code. These modifications can break previously-HEALTHY tests. Since BrickLayer only re-runs the fixed question (not all prior HEALTHY questions), regressions accumulate silently. The regression detection in bl/history.py (verdict flip detection) is the only guard. Measure whether it catches all regressions or misses some.
**Test**: Read `C:/Users/trg16/Dev/autosearch/recall/results.tsv`. Look for any question where the same question ID appears multiple times with verdicts in the pattern HEALTHY → FAILURE (a regression). Cross-reference with findings that contain `## Fix Attempt` sections to determine if the regression was temporally near a fix operation. Report: how many regressions were detected, how many may have been caused by fix-loop operations, and whether the history regression detection was the mechanism that surfaced them.
**Verdict threshold**:
- FAILURE: regressions found that correlate with fix-loop operations AND were not caught by history regression detection (silent regressions)
- WARNING: regressions found but all were eventually caught (delayed detection, not silent)
- HEALTHY: no regressions correlate with fix-loop operations, OR no fix-loop was active in this campaign

---

## Q4.3 [FIX-LOOP] Fix loop net value: total quality impact across the campaign
**Mode**: agent
**Agent**: campaign-historian
**Status**: DONE
**Hypothesis**: The fix loop's value should be measurable as: (bugs actually resolved and not recurring) - (regressions introduced). If this net value is positive, fix loop is worth the risk. If negative or near-zero, the campaign should always run without it. This is the definitive question for whether FIX_LOOP_ENABLED should default to True or False.
**Test**: Synthesize findings from Q4.1 and Q4.2 (if available) OR perform the analysis fresh. Count: (a) total FAILURE verdicts that were resolved by fix-loop and did not recur, (b) total regressions attributable to fix-loop operations. Compute net_value = (a) - (b). Also compute the risk ratio: regressions / fixes_attempted. Compare the FIX_LOOP_REGRESSION_PROBABILITY constant in constants.py (0.08) against the observed rate.
**Verdict threshold**:
- FAILURE: net_value <= 0 (fix loop destroys as much as it creates) OR observed regression rate > 0.20
- WARNING: net_value positive but small (< 2 net resolved bugs) OR observed rate > constants.py value by 5+ points
- HEALTHY: net_value >= 3 resolved bugs, observed regression rate within 5 points of 0.08

---

## Wave 1 — Evolution Potential (Q5.x)

*Which BrickLayer mechanisms are domain-general?
What would porting to code/research/creation require?*

---

## Q5.1 [EVOLUTION] Verdict taxonomy portability: does HEALTHY/WARNING/FAILURE transfer cleanly to code quality?
**Mode**: agent
**Agent**: evolution-architect
**Status**: DONE
**Hypothesis**: The four verdict states (HEALTHY, WARNING, FAILURE, INCONCLUSIVE) map naturally onto code quality outcomes, but the mapping may require new intermediate states. Specifically: a codebase that compiles but has 40% test failure rate is clearly FAILURE; one with 5% is WARNING; one with 0% is HEALTHY. But what about a codebase with passing tests but known security vulnerabilities? The current taxonomy has no "SECURE/INSECURE" axis — it conflates all quality dimensions into one verdict.
**Test**: For each of the three evolution domains (code, research methodology, creative output), write out a concrete verdict mapping table: what observable conditions map to HEALTHY, WARNING, FAILURE, INCONCLUSIVE in that domain? Identify: (a) which mappings are clean (obvious, unambiguous), (b) which require a new verdict state not in the current taxonomy, (c) which force a single verdict to cover two orthogonal quality dimensions. Report a "taxonomy portability score": fraction of mappings that are clean vs. require new states.
**Verdict threshold**:
- FAILURE: taxonomy portability score < 50% — the HEALTHY/WARNING/FAILURE system needs a fundamental redesign for new domains
- WARNING: 50–70% — usable but requires domain-specific verdict extensions
- HEALTHY: > 70% clean mappings — the taxonomy is domain-general with minor extensions

---

## Q5.2 [EVOLUTION] Hypothesis generator domain transfer: can qwen2.5:7b generate sound code-quality questions?
**Mode**: agent
**Agent**: evolution-architect
**Status**: DONE
**Hypothesis**: The qwen2.5:7b model used for hypothesis generation is general-purpose. Given a findings summary from a code quality campaign, it should generate valid next-wave questions. But it may show "business-model contamination" — framing code questions in financial terms (treasury, revenue, churn) because that's what it has seen in BrickLayer's prompt templates.
**Test**: Construct a synthetic findings summary as if from a code-quality campaign (3 findings: one about test coverage gaps, one about a type error in an async function, one about a missing error boundary). Format it exactly as bl/hypothesis.py formats findings summaries for the real Ollama call. Call the Ollama endpoint at `http://192.168.50.62:11434/api/generate` with model `qwen2.5:7b`, using the hypothesis generation prompt from bl/hypothesis.py but with "code quality" context instead of "memory system". Report: do the generated questions look like valid code quality questions? Or do they use financial/memory-system vocabulary? Quote 3 generated questions.
**Verdict threshold**:
- FAILURE: generated questions use business-model vocabulary (treasury, churn, velocity) or Recall-specific terms (vector, embedding, dedup)
- WARNING: questions are generic/vague (no specific test commands, no measurable thresholds)
- HEALTHY: questions are specific code-quality hypotheses with concrete test commands

---

## Q5.3 [EVOLUTION] Simulation portability: draft simulate.py for a code stress-testing project
**Mode**: agent
**Agent**: evolution-architect
**Status**: DONE
**Hypothesis**: The bricklayer-meta simulate.py (three-gate model: well-formed? novel? accurate?) is more domain-general than the financial simulate.py template. The three gates apply to any research campaign. However, the constants (BASE_SPECIALIST_ACCURACY, WAVE_SATURATION_RATE, etc.) are calibrated for the current BrickLayer agent fleet and may need recalibration for a code-quality fleet. The scenario parameters are fully domain-general — they describe the campaign configuration, not the target domain.
**Test**: Draft a `simulate.py` outline for a hypothetical `code-quality` project that stress-tests a Python codebase. Identify: (a) which parts of bricklayer-meta/simulate.py can be copied without change, (b) which constants need recalibration (with reasoning about what the new values should be), (c) which scenario parameters need renaming or replacement, (d) what new scenario parameters are needed that don't exist in the current simulation. The output should be a structured analysis, not necessarily runnable code.
**Verdict threshold**:
- FAILURE: more than 50% of simulate.py requires fundamental redesign for code domain (not portable)
- WARNING: 30–50% requires redesign (partially portable, significant adaptation needed)
- HEALTHY: < 30% requires fundamental change — the three-gate model and parameter structure are portable, only constants need recalibration

---

## Q5.4 [EVOLUTION] Agent fleet transferability: classify each agent as domain-general, domain-specific, or adaptable
**Mode**: agent
**Agent**: evolution-architect
**Status**: DONE
**Hypothesis**: The current agent fleet mixes domain-general agents (peer-reviewer, forge, agent-auditor, retrospective — these work in any campaign) with domain-specific agents (quantitative-analyst, probe-runner for Recall HTTP endpoints — these only work for the current target). The ratio of general to specific determines the "porting cost" for a new domain. A fleet that is mostly domain-general means a new project needs to forge only the domain-specific agents.
**Test**: Read all agent files in `C:/Users/trg16/Dev/autosearch/agents/`. For each agent, classify as: (A) domain-general — works unchanged in any BrickLayer campaign, (B) domain-specific — requires the Recall/ADBP target system or HTTP endpoints, (C) adaptable — mostly general, needs prompt edits for a new domain. Report: counts per category, overall portability ratio = (A + C) / total, and specifically name the agents in category B (these are the blockers for evolution). Estimate how many new agents a code-quality project would need to forge.
**Verdict threshold**:
- FAILURE: domain-general + adaptable ratio < 40% (fleet is mostly domain-specific, evolution is very costly)
- WARNING: ratio 40–65% (moderate porting cost, need to forge 5+ new agents for a new domain)
- HEALTHY: ratio >= 65% (fleet is mostly portable, new domain needs < 5 new domain-specific agents)

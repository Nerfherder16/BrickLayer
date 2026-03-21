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

---

## Wave 2 — Simulation Recalibration + Mechanism Design (Q6.x)

*Wave 2 probes the actionable changes surfaced in Wave 1 synthesis.
Priority: fix the two structural inversions in simulate.py, design the
DIAGNOSIS_COMPLETE suppression mechanism, and validate the evolution roadmap.*

---

## Q6.1 [SIMULATION] Recalibrated baseline: do all four Q1/Q3 fixes together produce HEALTHY and restore the novelty cliff?
**Mode**: agent
**Agent**: simulation-analyst
**Status**: IN_PROGRESS
**Hypothesis**: Applying the four recalibration changes from the Wave 1 synthesis simultaneously should (a) still produce verdict HEALTHY at nominal parameters, (b) produce a novelty cliff at DOMAIN_NOVELTY 0.65–0.75 (Q1.2 finding), and (c) produce a specialization floor at AGENT_SPECIALIZATION_RATIO ~0.20–0.35 (Q1.3 finding). All three behaviors should emerge together; if any is absent, the four changes interact in a way the individual-fix analysis didn't predict.
**Test**: In a copy of simulate.py, apply all four recalibrations from the synthesis table simultaneously: (1) `PEER_REVIEW_CORRECTION_RATE` 0.55 → 0.40; (2) novelty discount formula `max(0.20, 1 - N*0.60)` → `max(0.05, 1 - N*0.90)`; (3) `BASE_GENERALIST_ACCURACY` 0.625 → 0.50; (4) `_wave_uniqueness()` inverted to start at 0.20, rise to 0.80 by wave 10, plateau at 0.70. Run the recalibrated model at: (a) nominal parameters (DOMAIN_NOVELTY=0.35, AGENT_SPECIALIZATION_RATIO=0.65) — expect HEALTHY; (b) DOMAIN_NOVELTY sweep 0.50–1.00 in steps of 0.05 — find the cliff crossing WARNING threshold; (c) AGENT_SPECIALIZATION_RATIO sweep 0.0–0.5 in steps of 0.05 — find the inflection point. Report: baseline verdict, cliff location, floor location. Compare to Q1.2 and Q1.3 findings.
**Verdict threshold**:
- FAILURE: recalibrated model fails to produce HEALTHY at nominal parameters, OR no novelty cliff appears between 0.50 and 0.85, OR no specialization floor appears between 0.0 and 0.50 — changes interact destructively
- WARNING: baseline is HEALTHY but cliff or floor is outside the Q1.2/Q1.3 expected ranges (cliff > 0.85 or floor < 0.10) — model is better but still miscalibrated
- HEALTHY: baseline HEALTHY, cliff between 0.60 and 0.80, floor between 0.15 and 0.40 — recalibration is self-consistent and matches empirical findings
**Derived from**: Q1.2, Q1.3, Q3.1 — all four recalibrations needed simultaneously; interaction effects untested

---

## Q6.2 [SIMULATION] J-curve model: implement and validate the inverted _wave_uniqueness() against the empirical Recall curve
**Mode**: agent
**Agent**: simulation-analyst
**Status**: IN_PROGRESS
**Hypothesis**: The Q3.1 finding established that the real Recall campaign has a three-phase novelty curve: Phase 1 (waves 1-7) mean signal 0.150, Phase 2 (waves 13-24) mean signal 0.642, Phase 3 (waves 31-36) mean signal 0.665. An S-curve `_wave_uniqueness()` starting at 0.20, rising through an inflection near wave 8-10, and plateauing at 0.70-0.80 should reproduce this profile. A monotonic-decay model cannot reproduce it under any parameterization.
**Test**: Implement two alternative `_wave_uniqueness()` models as standalone Python functions: (A) S-curve: `0.20 + 0.60 * (1 / (1 + exp(-0.5 * (wave - 8))))` — sigmoid centered at wave 8; (B) Piecewise: 0.20 for waves 1-7, linear rise from 0.20 to 0.75 for waves 8-15, plateau at 0.75 for waves 16+. For each model, compute the per-wave uniqueness value for waves 1–36. Compute the mean uniqueness for the three empirical phase bands (waves 1-7, waves 13-24, waves 31-36). Compare to empirical means (0.150, 0.642, 0.665). Report root-mean-square error for each model. Also test that neither model produces a FAILURE verdict at nominal parameters (WAVE_COUNT=36, QUESTIONS_PER_WAVE=7).
**Verdict threshold**:
- FAILURE: neither model reduces RMSE below the current decay model's RMSE vs. empirical — J-curve hypothesis is wrong about mechanism
- WARNING: one model reduces RMSE but still misses one phase by more than 0.15 (mean) — better but not validated
- HEALTHY: at least one model achieves RMSE < 0.10 across all three phases and produces HEALTHY at nominal parameters
**Derived from**: Q3.1 — three-phase empirical structure; Q1.4 — current ceiling at wave 7 is an artifact of the decay model

---

## Q6.3 [FIX-LOOP] DIAGNOSIS_COMPLETE design: define the exact mechanism to suppress deployment-blocked re-check questions
**Mode**: agent
**Agent**: evolution-architect
**Status**: IN_PROGRESS
**Hypothesis**: The Q2.4 finding showed that BrickLayer re-checked the double-decay bug for 18 consecutive waves after diagnosis, wasting ~30% of wave capacity. The fix is a new question state — either a new status value (`DEPLOYMENT_BLOCKED`) or a new verdict (`DIAGNOSIS_COMPLETE`) — that halts re-checking until the target code changes. The design must be compatible with the current questions.md flat-file format and must not require changes to constants.py (immutable).
**Test**: Design the state machine extension as a concrete specification: (1) Define the trigger condition — after how many consecutive FAILURE re-checks with no code change detected should a question enter DEPLOYMENT_BLOCKED? (2) Define the questions.md entry format — what fields does a DEPLOYMENT_BLOCKED entry need that a DONE/PENDING entry does not? (3) Define the unblocking condition — what event causes the question to re-enter PENDING (code change detected via git diff, human override, timer)? (4) Check for conflicts with the existing status values (PENDING/IN_PROGRESS/DONE/INCONCLUSIVE) — does this require a 5th status or is it a sub-state of INCONCLUSIVE? (5) Estimate the capacity saving: in the Recall campaign, how many wave-question slots would DEPLOYMENT_BLOCKED have freed in waves 22-30?
**Verdict threshold**:
- FAILURE: the design requires changes to constants.py or program.md (breaking the immutable contract), OR the trigger condition is ambiguous (no way to detect "code not changed" without external tooling not present in BrickLayer)
- WARNING: design is valid but requires a new question status value that would break existing results.tsv parsers — migration work needed
- HEALTHY: design is compatible with the existing questions.md format (adds metadata fields to existing entries), trigger condition is detectable, and capacity saving estimate is >= 10 question slots across the Recall campaign
**Derived from**: Q2.4 — 18 consecutive re-checks, ~30% wave capacity waste; Q4.1 — fix convergence rate 8%

---

## Q6.4 [COVERAGE] Category diversity sentinel: define a measurable metric and test whether it would have fired in the Recall campaign
**Mode**: agent
**Agent**: campaign-historian
**Status**: IN_PROGRESS
**Hypothesis**: The Q3.2 finding showed that retrieval (55.3%) and decay (27.7%) dominated 83% of WARNING/FAILURE findings across 36 waves, with 6+ failure categories near zero coverage. A category diversity metric — defined as a Herfindahl-Hirschman Index (HHI) over finding categories — would have detected this concentration. An HHI above a threshold (e.g., 0.40) should trigger the Forge sentinel to generate questions in underrepresented categories. The question is whether this metric is computable from data already present in findings files, and at what wave the threshold would have fired in the Recall campaign.
**Test**: (1) Define a category taxonomy with 8-12 categories based on the Q3.2 finding (retrieval, decay, auth, write-path, cold-start, Neo4j correctness, rate-limiting, backup, cross-service, etc.). (2) Classify a sample of 40 findings from the Recall campaign (waves 1-20) into these categories using the finding title and hypothesis fields. (3) Compute per-wave cumulative HHI: after wave N, what fraction of WARNING/FAILURE findings falls in each category? Plot HHI over waves. (4) Identify the wave where HHI first exceeds 0.40 (proposed sentinel threshold). (5) Verify that the 6 near-zero categories from Q3.2 correspond to the same categories that are missing from the sample. Report: the wave at which the sentinel would have first fired, and the estimated coverage gain if the sentinel had redirected 2 questions per wave toward underrepresented categories starting at that wave.
**Verdict threshold**:
- FAILURE: HHI never exceeds 0.40 across all waves (retrieval/decay concentration is not captured by this metric), OR categories are not distinguishable from finding text alone (requires running the simulation, not just reading files)
- WARNING: sentinel would have fired after wave 20 (too late to affect the campaign meaningfully) OR the estimated coverage gain is < 5 questions
- HEALTHY: sentinel fires between wave 8 and wave 16, estimated coverage gain >= 10 questions across the campaign, and the metric is computable from existing findings file text
**Derived from**: Q3.2 — 83% concentration in two categories; Q3.3 — 6+ categories with near-zero coverage

---

## Q6.5 [CORRECTNESS] Peer review collapse root cause: what caused peer review to stop after wave 16?
**Mode**: agent
**Agent**: campaign-historian
**Status**: PENDING
**Hypothesis**: The Q2.3 finding confirmed peer review ran only in waves 13-16 of 36, then stopped entirely. Three plausible root causes exist: (A) a code bug in the peer-reviewer spawn logic — the async spawn silently failed starting at wave 17; (B) a configuration change — a human disabled peer review or the Forge retired the peer-reviewer agent between waves 16 and 17; (C) a capacity sentinel — peer review was suppressed because wave 16 had a high INCONCLUSIVE count (5 of 9 findings), triggering some auto-disable logic. Identifying the root cause determines whether this is a bug to fix or a design decision to document.
**Test**: (1) Read all finding files from waves 13-20 in `C:/Users/trg16/Dev/autosearch/recall/findings/`. Identify any finding that mentions the peer-reviewer agent being spawned, timing out, or being explicitly disabled. (2) Check for a FORGE_LOG.md or agent audit log in `C:/Users/trg16/Dev/autosearch/recall/` that records when agents were added or retired. (3) Read `C:/Users/trg16/Dev/autosearch/bl/` for any sentinel or auto-disable logic that would suppress the peer-reviewer after a high INCONCLUSIVE wave. (4) Check `C:/Users/trg16/Dev/autosearch/recall/questions.md` waves 17-20 — do any questions reference peer review or mention it being disabled? (5) Report: which root cause is most consistent with the available evidence, and what the observable signature of that cause would be in the findings files.
**Verdict threshold**:
- FAILURE: no evidence is available to distinguish among root causes A/B/C — the collapse is undiagnosable from the available data, indicating a monitoring gap in BrickLayer
- WARNING: one root cause can be ruled out but the remaining two are indistinguishable — partial diagnosis
- HEALTHY: root cause is identified with supporting evidence from findings files or source code, and the fix or documentation needed is clear
**Derived from**: Q2.3 — peer review active waves 13-16 only, 0 peer-reviewed findings in waves 17-36

---

## Q6.6 [FIX-LOOP] PENDING_EXTERNAL state machine: specify the fields, trigger, and resume_after protocol
**Mode**: agent
**Agent**: evolution-architect
**Status**: PENDING
**Hypothesis**: The Q4.3 finding showed 32 INCONCLUSIVE findings (15.4%) blocked by external timing constraints — cron windows, GC eligibility dates, deployment prerequisites. These are structurally different from INCONCLUSIVE findings caused by insufficient evidence: they have a known future unblocking time. A PENDING_EXTERNAL state (with a `resume_after` timestamp field in questions.md) would park these questions out of the active wave pool until the unblocking condition is met, recovering wave capacity. The hygiene cron chain alone (waves 29-31) would have freed 3 question slots.
**Test**: Specify the state machine extension in full: (1) Define `PENDING_EXTERNAL` as a new Status value or as a metadata annotation on INCONCLUSIVE — which is architecturally cleaner given the current questions.md flat-file format? (2) Define required fields: `resume_after` (ISO-8601 timestamp or event description), `blocking_condition` (human-readable), `wave_last_checked` (to detect the broken-prerequisite case). (3) Define the broken-prerequisite escalation rule from Q4.3 mitigation: if `resume_after` is in the past and the question is still blocked, how many waves before it escalates to FAILURE? (3 consecutive waves? configurable?) (4) Construct two concrete example entries from the Recall campaign — the hygiene cron wait and the GC eligibility wait — showing exactly what they would look like in questions.md format with the new fields. (5) Estimate total wave slots recovered in the Recall campaign if PENDING_EXTERNAL had been active from wave 26.
**Verdict threshold**:
- FAILURE: the design requires the research loop (program.md) to make network calls or read system clocks to evaluate resume_after — incompatible with the current loop's capabilities, or the design conflicts with the existing Status values in a way that breaks the results.tsv schema
- WARNING: design is valid but the broken-prerequisite escalation rule is ambiguous (no clear threshold for "this condition is itself broken"), leaving the hygiene-cron-type failure unhandled
- HEALTHY: design is fully specified with both example entries, broken-prerequisite rule has a clear numeric threshold, total recovered wave slots >= 8 across the Recall campaign
**Derived from**: Q4.3 — 15.4% INCONCLUSIVE rate, hygiene cron chain, GC eligibility chain; Q2.4 — deployment-blocked re-checks

---

## Q6.7 [EVOLUTION] Universal framework yield test: do the four roadmap changes each independently improve campaign yield in simulation?
**Mode**: agent
**Agent**: evolution-architect
**Status**: PENDING
**Hypothesis**: The Q5.4 finding identified four changes needed to make BrickLayer fully domain-agnostic: (1) SUBJECTIVE verdict type, (2) runner output contract standardization, (3) pluggable evaluate.py interface, (4) diagnosis/deployment split. Each change addresses a specific gap. In the recalibrated simulation (Q6.1), each change should independently improve campaign_yield by at least 0.03 when modeled as a parameter adjustment — otherwise the change is cosmetic (useful for architecture but not yield-affecting).
**Test**: Using the recalibrated simulate.py from Q6.1 as the baseline, model each of the four roadmap changes as a parameter perturbation and measure campaign_yield delta: (1) SUBJECTIVE verdict: add a `SUBJECTIVE_VERDICT_RATE` parameter (fraction of questions that produce a SUBJECTIVE verdict rather than HEALTHY/WARNING/FAILURE); model SUBJECTIVE findings as half-actionable (they need human resolution before they produce a concrete finding); test at 0%, 20%, 40% SUBJECTIVE rates — does yield degrade gracefully or collapse? (2) Runner output contract: model as a reduction in `BASE_GENERALIST_ACCURACY` variance — a tighter contract reduces the spread of wrong verdicts; test the effect of reducing generalist variance by 20%. (3) Pluggable evaluate.py: model as an increase in `AGENT_SPECIALIZATION_RATIO` (a pluggable evaluator means domain-specific logic can be injected); test AGENT_SPECIALIZATION_RATIO going from 0.65 to 0.80. (4) Diagnosis/deployment split: model as removing DEPLOYMENT_BLOCKED re-checks from the wave pool (equivalent to the Q6.3 mechanism); test with 15% of wave slots freed. Report: yield delta for each change, and yield delta when all four are combined.
**Verdict threshold**:
- FAILURE: three or more of the four changes produce yield delta < 0.01 in the recalibrated simulation — the roadmap changes are architecturally useful but not yield-affecting, and the simulation cannot validate them
- WARNING: two changes produce yield delta >= 0.03, two do not — partial validation; the non-impacting changes need a different evaluation path
- HEALTHY: at least three of the four changes produce yield delta >= 0.03 individually, and the combined delta is >= 0.10 — the roadmap is yield-validated
**Derived from**: Q5.4 — four-change universal framework; Q2.4 — deployment suppression; Q6.1 — recalibrated baseline needed first

# Project Brief — BrickLayer Meta-Research

<!-- HIGHEST AUTHORITY SOURCE. Every statement here is ground truth for research agents.
     Written to correct someone who almost understands BrickLayer but has key things wrong. -->

---

## What this system actually does

BrickLayer is an autonomous research campaign engine. It runs a loop: pull the next PENDING
question from `questions.md`, dispatch it to a specialist agent or test runner, classify the
verdict (HEALTHY / WARNING / FAILURE / INCONCLUSIVE), write a structured finding, and repeat.
Between waves, a local LLM (qwen2.5:7b via Ollama) reads the findings and generates the next
batch of questions. The campaign ends when the synthesizer says STOP, or the human does.

This meta-project uses BrickLayer to stress-test **BrickLayer itself** — specifically its
campaign quality properties: verdict accuracy, coverage completeness, synthesis coherence across
waves, fix-loop effectiveness, and hypothesis generator quality.

---

## The key invariants — things that cannot be wrong

1. **BrickLayer does not write code by default.** The research loop produces findings (`.md` files)
   and updates `results.tsv`. The fix loop (`bl/fixloop.py`) is opt-in (`--fix-loop` flag) and
   only activates on FAILURE verdicts. Most campaigns run without it.

2. **Hypothesis generation is local inference, not Claude.** `bl/hypothesis.py` calls
   `qwen2.5:7b` at `192.168.50.62:11434` (Ollama). It produces 4–5 questions per wave when the
   question bank is exhausted. The quality of Wave N+1 questions is bounded by the model's ability
   to reason about Wave N findings — it does not consult the internet or any external source.

3. **The fix loop has a hard cap of 2 attempts.** After 2 failed attempts, the question stays
   FAILURE and the finding is annotated `EXHAUSTED`. There is no escalation beyond this — human
   intervention is required. The fix loop cannot fix itself.

4. **Sentinels run at the start of each question, not at the end.** FORGE_NEEDED blocks the
   campaign (synchronous). AUDIT_REPORT is advisory (printed, not blocking). OVERRIDE verdicts
   from peer-reviewer inject re-examination questions into `questions.md` for the next iteration.

5. **Peer review is asynchronous and non-blocking.** The peer-reviewer agent is spawned as a
   background subprocess after every question. It may not complete before the next question
   starts. Its findings are injected via OVERRIDE, not inline.

6. **The campaign loop has no circuit breaker for verdict drift.** If an agent consistently
   reports HEALTHY when the system is failing, the campaign does not self-detect this. The only
   correction mechanisms are: peer-reviewer OVERRIDE, human annotation, and re-examination
   questions injected manually.

7. **Wave numbering is driven by question IDs, not an explicit counter.** Wave N is defined as
   all questions with prefix `QN.`. If questions from different waves are interleaved in
   `questions.md`, the hypothesis generator may miscalculate the next wave number.

---

## What has been misunderstood before

- **Misunderstanding**: The synthesizer decides what to fix.
  **Correct understanding**: The synthesizer produces a STOP/PIVOT/CONTINUE recommendation and
  a synthesis document. It does not produce fix instructions, does not write code, and does not
  re-queue questions. It is read-only analysis.

- **Misunderstanding**: Forge creates agents on demand during a question run.
  **Correct understanding**: Forge runs at the start of each question (sentinel check) and only
  when `FORGE_NEEDED.md` exists in the agents directory. It is not triggered by a question
  failing — it is triggered by a forge-check agent that scans for gaps every 5 questions and
  writes `FORGE_NEEDED.md` if it finds any.

- **Misunderstanding**: Higher `domain_novelty` always produces better findings.
  **Correct understanding**: There is a quality cliff. At low novelty, agents have strong priors
  and produce reliable verdicts. At high novelty, agents produce confident but potentially wrong
  verdicts (hallucinated APIs, assumed behaviors). The hypothesis generator compounds this — it
  will generate follow-up questions based on the wrong findings, propagating errors forward.

- **Misunderstanding**: BrickLayer is a static test runner.
  **Correct understanding**: BrickLayer is adaptive. The question bank grows via hypothesis
  generation, new agents are created via Forge, and fix attempts modify the target system.
  A campaign running long enough will materially change both the question bank and the agent
  fleet — and potentially the target system itself if fix-loop is enabled.

- **Misunderstanding**: The meta-project tests BrickLayer's code quality.
  **Correct understanding**: The meta-project tests BrickLayer's **campaign quality** — the
  information-theoretic properties of the research loop. Code quality of `bl/` is a separate
  concern. Campaign quality means: are the questions the right questions? Are the verdicts
  trustworthy? Does synthesis add information across waves? Does the fix loop converge?

---

## What this system is NOT

- It is not a financial model. The standard `simulate.py` template uses treasury / ops-cost as
  its primary metric. This project does not. Campaign quality is the primary metric.
- It is not a static benchmark. The campaign evolves its own question bank and agent fleet.
  Baselines measured in Wave 1 may not be comparable to Wave 5 without accounting for drift.
- It is not a code coverage tool. BrickLayer measures research coverage — how much of the failure
  space has been explored — not line or branch coverage of source code.
- It is not self-healing. The fix loop attempts repairs, but BrickLayer has no mechanism to
  detect whether a fix introduced a regression in a previously-HEALTHY question. Regression
  detection is handled by `bl/history.py` across runs, not within a single campaign.

---

## The numbers that cannot be wrong

| Fact | Value | Source |
|------|-------|--------|
| Fix loop max attempts | 2 | `bl/fixloop.py` — `max_attempts=2` default |
| Fix loop timeout per attempt | 600 seconds | `bl/fixloop.py` — subprocess timeout |
| Hypothesis generator questions per wave | 4 (wave ≥ 8) or 5 | `bl/hypothesis.py` line 101 |
| Hypothesis LLM temperature | 0.3 | `bl/hypothesis.py` — `options.temperature` |
| Forge-check interval | every 5 questions | `bl/campaign.py` — `questions_done % 5` |
| Agent-auditor interval | every 10 questions | `bl/campaign.py` — `questions_done % 10` |
| Peer-reviewer frequency | every question | `bl/campaign.py` — spawned after every `run_and_record` |
| Hypothesis LLM | qwen2.5:7b at 192.168.50.62:11434 | `bl/config.py` / `bl/hypothesis.py` |
| Primary campaign LLM | Claude (claude subprocess) | `bl/runners/agent.py` |

---

## The three failure modes this research targets

### 1. Verdict Drift
The campaign produces confident verdicts (HEALTHY) for questions where the system is actually
at or near a failure boundary. This is the most dangerous failure because it is invisible —
the campaign completes, synthesis says STOP, and the real failure is never discovered.

**Indicators**: High HEALTHY rate + low fix-loop activation + synthesis saying STOP early.

### 2. Coverage Collapse
The question bank converges on the same failure modes across waves. Wave 5 finds the same
things as Wave 2 in different words. The hypothesis generator (qwen2.5:7b) is locally optimal
on what it has seen, making it blind to unexplored regions of the failure space.

**Indicators**: High finding overlap across waves, synthesis noting "consistent with prior
findings" across multiple waves, no new failure categories discovered after wave 3.

### 3. Fix Loop Divergence
The fix loop resolves the immediate FAILURE but introduces changes that break other questions.
Because the campaign only re-runs the fixed question (not all prior HEALTHY questions), regressions
accumulate silently across a long campaign with fix-loop enabled.

**Indicators**: `bl/history.py` showing verdict flips (HEALTHY → FAILURE) on questions that
were not recently re-run. Increasing FAILURE rate in later waves despite fix-loop being active.

---

## Research scope

**In scope**:
- Campaign yield: what fraction of questions produce unique, non-redundant actionable findings?
- Wave coherence: does Wave N meaningfully extend Wave N-1 or repeat it?
- Verdict trustworthiness: how often does the peer-reviewer issue OVERRIDE vs CONFIRMED?
- Fix loop convergence: does fix-loop resolve FAILUREs or push them around?
- Hypothesis generator saturation: at what wave does qwen2.5:7b stop generating novel questions?
- Agent coverage: what fraction of question types have a specialized agent vs. falling back to
  a generalist?
- Evolution potential: which BrickLayer mechanisms could generalize from stress-testing business
  models to stress-testing code, research methodology, and creative output?

**Out of scope**:
- Line-level code quality of `bl/` — that is a separate autoresearch project if needed
- Performance benchmarking of the campaign loop (latency, token cost) — that is infrastructure
- Recall system quality — that is covered by the `recall/` autoresearch project
- Whether individual findings about the target system (Recall, ADBP, etc.) are correct

---

## The simulation model

`simulate.py` models a BrickLayer campaign as a quality-decay function across waves.
The primary metric is **campaign yield** — the fraction of questions that produce
unique, actionable findings (not redundant, not INCONCLUSIVE, not verdict-drifted).

**Primary metric**: `campaign_yield = unique_actionable_findings / total_questions_run`

**Failure threshold**: `campaign_yield < 0.25` (less than 1 in 4 questions adds new information)

**Warning threshold**: `campaign_yield < 0.45` (less than half of questions are productive)

**Key scenario parameters to vary**:
- `WAVE_COUNT` — number of research waves (affects synthesis saturation and hypothesis drift)
- `QUESTIONS_PER_WAVE` — depth per wave (more questions = more coverage but more redundancy)
- `AGENT_SPECIALIZATION_RATIO` — fraction of questions with a specialist agent (0.0 = all
  generalist, 1.0 = all specialist). Specialist agents have higher verdict accuracy but
  limited coverage. Generalist fallbacks have broader coverage but higher drift rate.
- `DOMAIN_NOVELTY` — how far outside the agent fleet's training the questions push (0.0–1.0).
  At high novelty, confident-but-wrong verdicts increase.
- `FIX_LOOP_ENABLED` — whether the fix loop is active. Affects regression accumulation rate.
- `HYPOTHESIS_TEMPERATURE` — creativity of the local LLM (0.0–1.0). Higher temperature
  increases novel question generation but also increases malformed/unsound questions.
- `PEER_REVIEW_RATE` — fraction of questions that receive a peer-review (0.0–1.0).
  Lower rates allow drift to propagate unchecked.

---

## Evolution hypothesis

BrickLayer's current form is specialized for business model stress-testing. The question is
whether its core loop — iterate parameters, run, classify verdict, synthesize, generate next
questions — is a general-purpose research engine that can evolve into:

1. **Code stress-testing**: Questions probe code quality dimensions (test coverage, type safety,
   security surface). Agents are linters, test runners, static analyzers. Verdicts map to pass/fail
   on automated gates. The "scenario parameters" are code complexity, dependency age, and spec
   ambiguity.

2. **Research methodology validation**: Questions probe the research process itself — source
   quality, claim confidence, contradiction handling, synthesis coherence. The simulation models
   an evidence pipeline, not a financial model. Primary metric: claim reliability under increasing
   source contradiction.

3. **Creative output stress-testing**: Questions probe generative output quality — coherence over
   long form, constraint compliance, style consistency. Verdicts require rubric-based evaluation.
   The simulation models a generation process with varying constraint density and coherence horizon.

The meta-research loop should discover: which of BrickLayer's mechanisms are domain-general
(verdict classification, synthesis, hypothesis generation, Forge) and which are domain-specific
(the financial `simulate.py`, the economic constants), and what would need to change to port
the campaign engine to a new domain.

---

## Documents in docs/ and their authority

| File | Authoritative for |
|------|------------------|
| `bl_architecture.md` | BrickLayer source code structure and module responsibilities |
| `campaign_mechanics.md` | Exact flow of `campaign.py` — sentinel order, spawn timing, wave transitions |
| `verdict_taxonomy.md` | What HEALTHY/WARNING/FAILURE/INCONCLUSIVE mean across question modes |
| `agent_fleet.md` | Current agent roster, their specializations, known gaps |
| `evolution_examples.md` | Concrete examples of BrickLayer applied to coding, research, creation domains |

*(These files should be populated before the research loop starts. Until populated, agents
should derive understanding from reading `bl/` source and `agents/*.md` directly.)*

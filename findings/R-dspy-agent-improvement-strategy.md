# R-dspy-agent-improvement-strategy: Best practices for improving AI agent performance — DSPy optimization vs. data flywheel strategies

**Status**: HEALTHY (campaign-based accumulation is valid; corpus sizes are viable; key gaps identified)
**Date**: 2026-03-23
**Agent**: research-analyst

---

## Hypothesis Under Test

The BrickLayer 2.0 assumption: "running structured research campaigns → collecting scored findings → using those findings as DSPy training examples" is the correct flywheel for improving agent performance. Specifically:

1. Campaign-based data accumulation is the right strategy (not synthetic data generation or self-play)
2. The current corpus sizes (~77 research-analyst records, ~300+ karen records) are adequate for reliable MIPROv2 optimization
3. MIPROv2/BootstrapFewShot is the right optimizer choice vs. fine-tuning or Constitutional AI

---

## Evidence

### Supporting evidence

**On corpus size minimums for DSPy:**

- [DSPy Data Quarry tutorial, Oct 2025](https://thedataquarry.com/blog/learning-dspy-3-working-with-optimizers/): "Anywhere from 10 to a few hundred examples that can be split into train and test sets. Different optimizers have different requirements for the number of examples needed, but for modifying prompts, **a few dozen examples is usually sufficient as a starting point**." Also: "all you need is a few dozen examples, so it's not too onerous to hand-curate."

- [DSPy playbooks skill documentation, Jan 2026](https://playbooks.com/skills/omidzamani/dspy-skills/dspy-bootstrap-fewshot): BootstrapFewShot is "designed for small labeled sets — typically **10–50 examples**; quality matters more than quantity." For MIPROv2: "200+ examples" recommended for longer intensive runs (40+ trials). Recommendation: "For more data (200+ examples): dspy-miprov2-optimizer."

- [DSPy Azure documentation, May 2025](https://msazure.club/automated-prompt-optimization-in-dspy-mechanisms-algorithms-and-observability/): MIPROv2 "recommended for longer runs (e.g., 40+ trials) with sufficient data (e.g., **200+ examples**) to avoid overfitting."

- [Atlantic/Kruk Matias case study, Nov 2025](https://building.theatlantic.com/scaling-ai-agents-with-dspy-and-miprov2-from-manual-prompts-to-automated-optimization-6a88f993f2b2): Successfully used 46 training + 2 gold validation examples with MIPROv2 at `auto=light`. Achieved +25% relative improvement (Product Owner role), +18% (Business Analyst). Confirms small corpus can yield significant gains.

- [BrickLayer 2.0 CLAUDE.md, internal]: Documents the constraint directly: "the research-analyst corpus is ~57 records. Never set `--valset-size` above 57 or MIPROv2 will error. Use `--valset-size 27` — this leaves 30 training examples (57 - 27 = 30), which meets the DSPy minimum of ~30 required for reliable optimization."

**On MIPROv2 vs. fine-tuning economics:**

- [CXOToday / Saketh Ram Gurumurthi, Feb 2026](https://cxotoday.com/ai/dspy-changes-enterprise-genai-economics-why-prompt-optimization-trumps-fine-tuning/): "Fine-tuning is expensive, slow, brittle, and hard to govern... Prompt optimization flips that cost structure. New training examples improve system behavior **without retraining models**. Optimization runs are cheap, fast, and reproducible. Prompt versions are diffable. Rollbacks are trivial." In regulated/auditability-sensitive environments, fine-tuning is often a non-starter.

- [DSPy Review 2026, PE Collective](https://pecollective.com/tools/dspy/): "For tasks like classification, extraction, and multi-step reasoning, optimized DSPy pipelines regularly beat hand-crafted prompts by **10–20%**."

- [Data Quarry, Oct 2025]: BootstrapFewShot: <$1, <1 min. GEPA: more expensive, 30 min–1.5 hrs. MIPROv2: 2–4 hrs. Fine-tuning: hours to days + GPU infrastructure.

**On data flywheel vs. synthetic generation:**

- [Tongyi DeepResearch technical report, Oct 2025](https://arxiv.org/html/2510.24701v1): Leading production research agents (Alibaba's DeepResearch, 30.5B params) use fully automated **synthetic data generation pipelines** — not campaign-based accumulation. Key insight: "Synthesized data can provide data flywheels in training stages. After one round of the agentic training pipeline, the trained agentic model can generate synthesized data with stronger reasoning and planning patterns." However — this is for full LLM fine-tuning at scale, not prompt optimization.

- [Arena Learning / WizardLM, Microsoft, Jul 2024 / Feb 2026](https://arxiv.org/html/2407.10627v1): LLM-as-judge battle simulation ("Arena Learning") achieves data flywheel for **post-training** (SFT, DPO, PPO). Three iterative loops improved WizardLM-β significantly. But this requires model weight access (fine-tuning) and large instruction corpora — not applicable to API-only prompt optimization.

- [Self-Challenging Agents, NeurIPS 2025](https://neurips.cc/virtual/2025/poster/119495): Agent self-play (agent generates tasks, then solves them) improves Llama-3.1-8B by 2x on tool-use benchmarks using only self-generated training data. This is a fine-tuning approach requiring model weight access.

- [APIGen-MT, Apr 2025](https://paperswithcode.com/paper/apigen-mt-agentic-pipeline-for-multi-turn): Agentic pipeline for synthetic multi-turn data generation — again targeting fine-tuning of open-weight models, not prompt optimization of closed API models.

**On LLM-as-judge for agent evaluation:**

- [LLM-as-a-judge survey, EMNLP 2025, ACL Anthology](https://aclanthology.org/2025.emnlp-main.138.pdf): Comprehensive survey. LLM-as-judge is mature and widely used for agent evaluation. Key challenges: position bias, length bias, self-preference. Best practices: rubric-based criteria, multiple judges (committee), calibrate against human ground truth.

- [Getmaxim AI, Sep 2025](https://getmaxim.ai/articles/llm-as-a-judge-a-practical-reliable-path-to-evaluating-ai-systems-at-scale): "Judges are especially useful for safety and policy adherence, where rules can be encoded in rubric checks." Production pattern: define rubric per task family, 1–2 examples per criterion, human-calibrate periodically.

- [Generate, Evaluate, Iterate (IBM Research), Nov 2025](https://arxiv.org/pdf/2511.04478): Synthetic data generation integrated into LLM-as-judge workflow improves criterion refinement. 83% of users found it improved evaluation quality. Key finding: **generate diverse synthetic test cases (including borderline cases) to surface blind spots in judge criteria**.

- [RLAIF vs. RLHF (Bai et al., 2022/2024 ICML)]: RLAIF achieves comparable or superior performance to RLHF. Constitutional AI (Anthropic) uses explicit principle sets to guide AI-generated preference labels. Cost: <$0.01 per sample vs. $1–10+ for human RLHF. But requires: access to model weights, RL training infrastructure, reward model training.

**On the optimize → evaluate → generate more data loop:**

- [Engineering Notes / muthu.co, Feb 2026](https://notes.muthu.co/2026/02/automatic-prompt-optimization-with-dspy-building-self-tuning-agent-pipelines/): DSPy team's documented loop: "Use `dspy.Evaluate` for quick loops; log failures and turn them into new examples for the next compile." Open research problem identified by community: "Continual optimization. As production data shifts, how do you re-optimize without starting from scratch? Warm-starting optimization from previous compilation checkpoints is an active research area."

- [DSPy 3 guide, Amir Teymoori, Nov 2025](https://amirteymoori.com/dspy-3-build-evaluate-optimize-llm-pipelines/): Recommended loop: measure → compile → evaluate → log failures → add failures to trainset → re-compile. The key source of new training data is **production failures**, not synthetic generation.

- [Statsig DSPy guide, Oct 2025](https://www.statsig.com/perspectives/dspy-vs-prompt-tuning): "Pick metrics that reflect reality: correctness, refusal rate, latency, and cost. Run DSPy compilers to re-tune after a model update or provider switch."

### Contradicting evidence

- The case for **synthetic data generation over campaign-based accumulation**: Tongyi DeepResearch shows synthetic generation scales faster, costs less per example (~$0.15 for 500 examples with GPT-4o-mini), and can target specific failure modes. A synthetic approach could generate 10x more training examples than campaigns produce organically.

- **Campaign data has distribution risk**: Findings generated by campaigns reflect the questions Tim chose to ask and the failure modes the project happened to surface. This is not the same as a diverse, well-distributed training set. A corpus biased toward certain question types may produce an optimizer that overfits on those types and underperforms on novel questions.

- **77 records for research-analyst is below the MIPROv2 "optimal" threshold**: The DSPy documentation recommends 200+ examples for intensive MIPROv2 runs. The current 77-record corpus (with 30 usable training examples after valset split) sits in the "BootstrapFewShot" range, not the full MIPROv2 power zone.

### Analogues

- **The Atlantic / AGNOSTIC AI PIPELINE**: Used 46 training + 2 validation examples for MIPROv2 at `auto=light`, achieved +25% quality. Comparable corpus size to BrickLayer's research-analyst situation. Verdict: viable.

- **Tongyi DeepResearch**: Uses automated synthetic generation + RL fine-tuning. Performance state-of-the-art (beats OpenAI o3 on some benchmarks). But: 30.5B parameter open-weight model, GPU clusters, months of training. Not applicable to a prompt optimization framework against closed API models.

- **WizardLM Arena Learning**: Data flywheel via LLM battle simulation for post-training. Shows iterative improvement across 3 loops. Requires model weight access. Not directly applicable but the **LLM-as-judge scoring pattern** is directly transferable to BrickLayer's peer-reviewer agent.

---

## Threshold Analysis

No direct constants.py threshold applies to this meta-question (it is about the BrickLayer system itself, not a specific project simulation). The relevant benchmarks from the evidence:

| Parameter | Evidence Floor | Evidence Optimum | BrickLayer Status |
|---|---|---|---|
| BootstrapFewShot minimum trainset | 10–50 examples | 20–50 high quality | research-analyst: ~30 usable → MEETS FLOOR |
| MIPROv2 `auto=light` minimum | ~20–30 examples | 50–100 | research-analyst: ~30 → MEETS LIGHT THRESHOLD |
| MIPROv2 `auto=medium/heavy` recommended | 100–200 examples | 200+ | research-analyst: 77 total → BELOW OPTIMAL for heavy runs |
| karen corpus | 300+ records | 200+ for medium | karen: ~300+ → ABOVE OPTIMAL |
| Expected improvement from optimization | baseline | +10–25% | Comparable cases: +10–25% on classification/structured tasks |

**research-analyst gap**: Current 77 total records (30 usable training) is adequate for `auto=light` runs but falls below the 200+ threshold recommended for intensive `auto=heavy` runs. Each additional campaign wave of ~7 questions adds ~7 records. To reach 100 usable training examples requires approximately 10 more campaign waves (70 additional records), assuming the 30/77 usable ratio holds.

**karen gap**: karen at 300+ records is in the MIPROv2 "optimal" zone. Re-optimization of karen is recommended.

---

## Confidence

Evidence quality: **HIGH** for corpus size thresholds (direct DSPy documentation + practitioner case studies with specific numbers). **MEDIUM** for the campaign-vs-synthetic comparison (no direct head-to-head study in a BrickLayer-equivalent context). **HIGH** for the fine-tuning vs. prompt optimization economics comparison.

---

## Synthesis: Is Campaign-Based Accumulation the Right Flywheel?

**Short answer**: Yes, for the current architecture (closed API models, prompt optimization target), but with one key augmentation: **add targeted synthetic generation for distribution diversity**.

The reasoning:

1. **Campaign-based data is the right format for DSPy**: Campaigns produce (input, output, verdict) triples — exactly the structure DSPy needs. Each finding is a labeled example. The scoring pipeline (score_findings.py) provides the metric signal. This is the correct data primitive.

2. **The flywheel is correct but slow**: Campaigns generate ~7 records per wave. At this rate, reaching the MIPROv2 optimal zone (200+ training records) for research-analyst requires ~20+ more campaign waves. This is achievable but slow.

3. **The right augmentation is targeted synthetic generation for gaps**: Rather than replacing campaign data, use GPT-4o-mini to generate synthetic training examples for question types that campaigns have underrepresented. Cost: ~$0.15 for 500 examples. Filter by the same scoring metric. This can accelerate corpus growth from 77 → 300+ without changing the DSPy pipeline.

4. **Fine-tuning (LoRA/QLoRA) is wrong for this context**: BrickLayer runs against closed API models (Claude Sonnet). Fine-tuning requires open-weight model access. Additionally, fine-tuning locks behavior into opaque weights, creates governance overhead, and is economically worse than prompt optimization for the corpus sizes involved.

5. **Constitutional AI / RLAIF is wrong for this context**: RLAIF requires reward model training and RL infrastructure. It is appropriate at foundation model scale (Anthropic's internal use case). For a 77-record corpus optimizing prompt instructions, it is massively over-engineered.

6. **LLM-as-judge (peer-reviewer pattern) is correctly placed**: BrickLayer's peer-reviewer agent already implements the core LLM-as-judge pattern. The evidence shows this is the right mechanism. The EMNLP 2025 survey confirms rubric-based criteria + committee approach improves reliability — a possible future upgrade to peer-reviewer.

7. **The missing piece is the re-optimization trigger**: The community identifies "continual optimization" as an open problem. The current BrickLayer approach (manual trigger from Kiln UI) is correct but should be augmented with a drift detection → auto re-optimization pipeline. The DSPy community's recommendation: log failures from production runs → add to trainset → re-compile on a schedule or drift threshold.

---

## What Would Change This Verdict

- **Evidence that campaign data distribution is systematically biased** (e.g., all research-analyst findings cluster around 3 question types out of 10, producing an optimizer that fails on question types 4–10) would flip the assessment from HEALTHY to WARNING on the flywheel strategy.

- **Evidence that BootstrapFewShot at 30 training examples produces statistically unreliable optimization** (high variance across runs, no consistent improvement over baseline) would flip the corpus size verdict from HEALTHY to FAILURE.

- **A production case study showing synthetic-only generation outperforms campaign-generated data** for a comparable structured-research agent would flip the "campaign is right" verdict to WARNING.

- **DSPy team shipping warm-start / continual optimization** would change the re-optimization strategy recommendation.

---

## Actionable Recommendations

### Immediate (corpus size and optimization)
1. **research-analyst**: Current 30 usable training examples support `auto=light` MIPROv2 runs. Continue accumulating via campaigns. Do not attempt `auto=heavy` until corpus reaches ~100 usable training examples (~140 total).
2. **karen**: At 300+ records, karen is in the MIPROv2 optimal zone. Run a medium or heavy optimization pass (the `--valset-size 25` setting documented in CLAUDE.md is correct).
3. **Synthetic augmentation**: Generate 100–150 synthetic training examples for research-analyst using GPT-4o-mini + the existing scoring metric as filter. Cost: <$0.15. This would unlock `auto=medium` runs immediately.

### Medium-term (flywheel improvement)
4. **Distribution audit**: Run a clustering analysis on the existing 77 research-analyst records to verify they cover diverse question types. If 3+ question types are underrepresented, target synthetic generation at those gaps.
5. **LLM-as-judge rubric upgrade**: Add rubric-based criteria to peer-reviewer (currently scoring by verdict matching). Add positional debiasing (randomize response order). This directly implements the EMNLP 2025 best practices.
6. **Production failure logging**: Implement a failure logging hook that captures questions where peer-reviewer issues OVERRIDE verdicts and automatically queues those (input, failed_output) pairs for the next training batch.

### Not recommended
7. **Fine-tuning (LoRA/QLoRA)**: Wrong tool for this architecture. Revisit only if BrickLayer moves to self-hosted open-weight models.
8. **Constitutional AI / RLAIF**: Massively over-engineered for current scale. Revisit at 10,000+ examples.
9. **Pure self-play / agent self-generation without human-validated scoring**: Without a reliable automated metric, self-generated data risks reward hacking. The scoring metric must be validated against human judgment first.

---

## resume_after

Not applicable — sufficient evidence gathered to reach a verdict.

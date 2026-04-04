# Repo Research: K-Dense-AI/claude-scientific-skills
**Repo**: https://github.com/K-Dense-AI/claude-scientific-skills
**Researched**: 2026-03-28
**Stars**: 16,500+ | **Forks**: 1,800+ | **Version**: v2.31.0

---

## Verdict Summary

This is a large, well-structured collection of 170+ agent skills for scientific research. For BrickLayer's purposes, the relevance is **high but targeted** — roughly 15-20 of the 177 skill directories contain methods directly applicable to improving BL's research loop quality. The core BL loop (question → simulate → find → synthesize) maps closely to scientific hypothesis generation workflows, and this repo has mature, detailed methodology for exactly that. The biggest gains for BL are: (1) structured hypothesis templates with null/alternative/prediction triads, (2) a formal evidence quality hierarchy with GRADE-style confidence degradation, (3) the What-If Oracle's 6-branch scenario analysis pattern, and (4) the Consciousness Council's adversarial multi-perspective deliberation which BL currently lacks entirely.

The repo does NOT contain simulation-specific code or business model stress-testing logic — it is general scientific research methodology. The harvest value is methodological patterns and prompt templates, not runnable code.

---

## File Inventory

| Path | Type | Size | Relevance |
|------|------|------|-----------|
| `README.md` | Documentation | 43KB | High — full catalog overview |
| `docs/scientific-skills.md` | Documentation | 113KB | High — complete skill catalog |
| `docs/examples.md` | Documentation | 113KB | Medium — workflow examples |
| `.claude-plugin/marketplace.json` | Config | 8KB | Medium — machine-readable catalog |
| `scientific-skills/` | Directory | — | 177 skill subdirectories |
| `scientific-skills/hypothesis-generation/SKILL.md` | Skill | 13.8KB | **Critical** |
| `scientific-skills/scientific-critical-thinking/SKILL.md` | Skill | 23.7KB | **Critical** |
| `scientific-skills/literature-review/SKILL.md` | Skill | 23.8KB | **Critical** |
| `scientific-skills/statistical-analysis/SKILL.md` | Skill | 19.8KB | **Critical** |
| `scientific-skills/what-if-oracle/SKILL.md` | Skill | 9.5KB | **Critical** |
| `scientific-skills/consciousness-council/SKILL.md` | Skill | 8.7KB | **Critical** |
| `scientific-skills/peer-review/SKILL.md` | Skill | 23.1KB | High |
| `scientific-skills/scientific-brainstorming/SKILL.md` | Skill | 8.2KB | High |
| `scientific-skills/scholar-evaluation/SKILL.md` | Skill | ~8KB | High |
| `scientific-skills/exploratory-data-analysis/SKILL.md` | Skill | ~6KB | High |
| `scientific-skills/hypogenic/SKILL.md` | Skill | ~5KB | High — LLM hypothesis automation |
| `scientific-skills/pymc/SKILL.md` | Skill | ~5KB | Medium — Bayesian workflow |
| `scientific-skills/dhdna-profiler/SKILL.md` | Skill | ~6KB | Low-Medium |
| `scientific-skills/denario/SKILL.md` | Skill | ~4KB | Medium — multiagent research |
| `scientific-skills/scientific-writing/SKILL.md` | Skill | ~7KB | Low (BL already has synthesizer) |
| `scientific-skills/research-lookup/SKILL.md` | Skill | ~4KB | Low |
| `scientific-skills/bgpt-paper-search/SKILL.md` | Skill | ~3KB | Low |
| `scientific-skills/market-research-reports/SKILL.md` | Skill | ~6KB | Low |
| 155+ remaining skills | Various | — | Mostly domain-specific (biology, chemistry, etc.) — not directly applicable to BL |

Each skill directory follows the `Agent Skills` standard: `SKILL.md` + optional `references/`, `assets/`, `scripts/` subdirectories.

---

## Skill/Method Catalog

### 1. Hypothesis Generation (`scientific-skills/hypothesis-generation/`)

**Purpose**: Structured framework for developing testable scientific hypotheses from observations and data.

**Methodology**: Eight-phase sequential workflow:
1. Clarify the phenomenon — define observation, scope, knowledge gaps
2. Search existing literature — PubMed and domain databases
3. Synthesize evidence — integrate findings, identify gaps
4. **Generate competing hypotheses** — develop 3–5 distinct mechanistic explanations
5. **Evaluate quality** — testability, falsifiability, explanatory power
6. **Design experiments** — specific studies to test each hypothesis
7. **Formulate predictions** — specific, measurable expected outcomes
8. Present findings — structured LaTeX report with appendices

**Unique Techniques**:
- Forces generation of competing hypotheses (pluralism, not convergence)
- Explicit falsifiability gate — hypothesis must specify conditions under which it fails
- Output format: concise main text ≤4 pages + comprehensive appendix with full experimental protocols
- Mandatory visual schematic using scientific-schematics skill

**Key quality criteria**: evidence-based, testable, mechanistically explained, considers alternatives, rigorous experimental design.

---

### 2. Scientific Critical Thinking (`scientific-skills/scientific-critical-thinking/`)

**Purpose**: Systematic evaluation of scientific claims and research quality — the skeptic agent role.

**Methodology**: Six evaluation frameworks:

1. **Methodology Critique**: Study design validity, internal/external validity, control procedures, measurement quality
2. **Bias Detection**: Cognitive biases (HARKing, confirmation bias), selection biases, measurement biases, analysis biases (p-hacking, outcome switching), confounding
3. **Statistical Analysis**: Sample adequacy, test appropriateness, multiple comparison corrections, p-value interpretation, effect sizes + confidence intervals, regression assumptions
4. **Evidence Quality Assessment**: Design hierarchy (systematic reviews → RCTs → cohort → case studies) + GRADE methodology — downgrades for bias/inconsistency/imprecision; upgrades for large effects and dose-response
5. **Logical Fallacy Identification**: Correlation-causation confusion, hasty generalization, appeal to authority, base rate neglect, Galileo gambit
6. **Research Design Guidance**: Question refinement, design selection, bias minimization, analysis pre-registration

**Unique Techniques**:
- GRADE confidence system (High/Moderate/Low/Very Low) with explicit downgrade/upgrade rules
- Distinguishes data from interpretation, correlation from causation, statistical from practical significance
- Constructive critique standard: identify strengths alongside weaknesses
- Evidence design hierarchy as a formal decision tree

---

### 3. Literature Review (`scientific-skills/literature-review/`)

**Purpose**: Systematic literature reviews across biomedical, scientific, and technical domains.

**Methodology**: Seven mandatory phases:
1. Planning with PICO framework (Population, Intervention, Comparison, Outcome)
2. Systematic searching across minimum 3 databases
3. Rigorous screening: title → abstract → full-text cascade with deduplication
4. Data extraction with quality assessment
5. **Thematic synthesis** — group by themes, NOT by individual studies
6. Citation verification (all citations verified before submission)
7. Final document generation with PRISMA compliance

**Unique Techniques**:
- PICO framework for question scoping — forces operationalization of vague research questions
- Citation count thresholds to identify influential papers
- Venue tier prioritization: Nature, Science, Cell, NEJM, top AI conferences (NeurIPS, ICML)
- Anti-pattern documentation: single-database searches, unverified citations, study-by-study summaries, publication bias without acknowledgment
- Mandatory PRISMA flow diagram generation

---

### 4. Statistical Analysis (`scientific-skills/statistical-analysis/`)

**Purpose**: Correct test selection, assumption checking, and APA-formatted statistical reporting.

**Methodology**: Four-phase systematic approach:
1. Test selection via decision tree (data characteristics → appropriate method)
2. Assumption verification with automated diagnostic visualizations (Q-Q plots, residual plots, box plots)
3. Analysis execution — t-tests, ANOVA, regression, correlations, Bayesian alternatives
4. Results reporting — APA-style with effect sizes, CIs, and interpretation

**Unique Techniques**:
- Decision tree for test selection removes ambiguity
- Effect size calculation mandatory for all analyses (not just p-values)
- Power analysis as a design step (pre-analysis, not post-hoc rationalization)
- Distinguishes statistical significance from practical importance explicitly
- Automated assumption checking scripts with visualizations
- Comprehensive Bayesian alternative coverage (PyMC integration)

---

### 5. What-If Oracle (`scientific-skills/what-if-oracle/`)

**Purpose**: Multi-branch scenario analysis for exploring uncertain futures before committing to decisions.

**Methodology**: 6-branch scenario mapping using the "0·IF·1" model (potential → conditional → expressed reality):

| Branch | Symbol | Description |
|--------|--------|-------------|
| Best Case | Ω | Everything validates positively |
| Likely Case | α | Most probable path given current evidence |
| Worst Case | Δ | Key assumptions fail simultaneously |
| Wild Card | Ψ | Unexpected variables emerge |
| Contrarian | Φ | Consensus assumptions prove false |
| Second Order | ∞ | Cascading, unanticipated ripple effects |

Each branch receives: probability, narrative, assumptions, trigger conditions, time-horizon consequences, required responses, non-obvious insights.

**Synthesis outputs**:
- Robust actions (beneficial across multiple branches)
- Hedge actions (protective preparations)
- Decision triggers (observable signals to update probabilities)
- "The 1% insight" — the overlooked pattern most analyses miss

**Unique Techniques**: The contrarian and second-order branches are the differentiators — they force consideration of cascade effects and inversion of consensus assumptions. The "0·IF·1" framing makes the conditional explicit. Author: AHK Strategies.

---

### 6. Consciousness Council (`scientific-skills/consciousness-council/`)

**Purpose**: Multi-perspective deliberation on complex questions via simulated expert archetypes — "the cognitive equivalent of a boardroom, philosophy seminar, and war room simultaneously."

**Methodology**: Three-phase process:
1. Summon council of 4–6 archetypes from 12 types: Architect, Contrarian, Empiricist, Ethicist, Futurist, Pragmatist, Historian, Empath, Outsider, Strategist, Minimalist, Creator
2. Each member presents position with reasoning, identifies risks others miss, offers non-obvious insights
3. Synthesis: convergence points, core tensions, blind spots, actionable recommendations

**Critical Principle**: "Productive disagreement, not consensus" — each member MUST genuinely disagree with at least one other. Universal agreement = Council failure.

**Unique Techniques**:
- Mandatory Contrarian and Outsider archetypes force adversarial critique
- Blind spot identification as a first-class output (not an afterthought)
- Works best on genuine uncertainty, high stakes, situations where user bias may be limiting
- Explicitly fails on already-decided questions — honest about scope limits

---

### 7. Peer Review (`scientific-skills/peer-review/`)

**Purpose**: Structured scientific manuscript and grant proposal evaluation across seven stages.

**Methodology**: Seven evaluation stages:
1. Initial assessment (scope, appropriateness, prior publication)
2. Section-by-section analysis (Abstract, Intro, Methods, Results, Discussion)
3. Methodological rigor (design validity, controls, reproducibility)
4. Reproducibility assessment (code, data, materials availability)
5. Figure/data presentation review
6. Ethical considerations (IRB, consent, dual-use)
7. Writing quality evaluation

**Standards**: CONSORT (trials), PRISMA (systematic reviews), ARRIVE (animal studies), STROBE (observational)

**Unique Techniques**:
- Hierarchical feedback structure: summary → major comments (fundamental flaws) → minor → line-by-line
- Explicit reproducibility checklist (code availability, data sharing, materials)
- Never text-parse presentation PDFs — convert to images first (prevents technical errors)

---

### 8. Scientific Brainstorming (`scientific-skills/scientific-brainstorming/`)

**Purpose**: Creative ideation framework for early-stage research planning — distinct from hypothesis generation (which starts from data).

**Methodology**: Five phases:
1. Context establishment via open-ended dialogue
2. Divergent exploration using cross-domain analogies and assumption reversal
3. Connection identification among ideas
4. Critical evaluation of promising directions
5. Synthesis into concrete next steps

**Techniques**: SCAMPER framework, scale-shifting analysis, constraint manipulation, technology speculation.

**Key rule**: "The scientist should be doing at least 50% of the talking" — conversational balance prevents AI domination of the ideation process.

---

### 9. Scholar Evaluation (`scientific-skills/scholar-evaluation/`)

**Purpose**: ScholarEval framework for assessing academic work quality across 8 dimensions.

**Dimensions**: Problem formulation, literature review quality, research methodology, data collection, analytical rigor, results presentation, scholarly writing, citation practices.

**Scoring**: 5-point scale (Excellent → Poor) per dimension, with synthesis.

**Workflow**: Scope definition → dimension assessment → scoring → synthesis → actionable feedback → contextual adjustment.

---

### 10. HypoGeniC / Hypogenic (`scientific-skills/hypogenic/`)

**Purpose**: Automated hypothesis generation and testing on tabular datasets using LLMs.

**Three approaches**:
- **HypoGeniC**: Pure data-driven, iteratively refines hypotheses based on validation performance
- **HypoRefine**: Combines literature insights with empirical patterns via agentic system
- **Union Methods**: Mechanistically combines literature-only and data-driven hypotheses

**Performance**: 8.97% improvement over few-shot baselines; 15.75% improvement over literature-only approaches; 80–84% hypothesis diversity.

**Technical**: Redis caching, parallel processing, template-based prompt engineering with variable injection. Supports OpenAI, Anthropic, local LLMs.

---

### 11. Exploratory Data Analysis (`scientific-skills/exploratory-data-analysis/`)

**Purpose**: Automated EDA across 200+ scientific file formats — detects format, generates markdown report, recommends downstream analysis.

**Six format categories**: Chemistry/Molecular (60+ extensions), Bioinformatics/Genomics (50+), Microscopy/Imaging (45+), Spectroscopy/Analytics (35+), Proteomics/Metabolomics (30+), General Scientific Data (30+).

---

### 12. PyMC Bayesian Modeling (`scientific-skills/pymc/`)

**Purpose**: Bayesian modeling and probabilistic programming with structured convergence validation.

**8-step Bayesian workflow**: Data prep → Model building → Prior predictive check → MCMC sampling → Convergence diagnostics (R-hat < 1.01, ESS > 400) → Posterior predictive check → Analyze results → Predictions with uncertainty intervals.

**Unique**: Prior predictive check before fitting — validates prior distributions generate plausible data before touching real data.

---

### 13. Denario (`scientific-skills/denario/`)

**Purpose**: Multiagent scientific research automation from data analysis to publication.

**Five stages**: Data description → Idea generation → Methodology development → Results generation → Paper generation (LaTeX).

**Frameworks**: AG2 + LangGraph for agent coordination. Supports APS journal formatting.

---

### 14. DHDNA Profiler (`scientific-skills/dhdna-profiler/`)

**Purpose**: Extract cognitive fingerprint from text — 12 dimensions scored 1–10 from textual evidence.

**12 Dimensions**: Analytical Depth, Creative Range, Emotional Processing, Linguistic Precision, Ethical Reasoning, Strategic Thinking, Memory Integration, Social Intelligence, Domain Expertise, Intuitive Reasoning, Temporal Orientation, Metacognition.

**6 Tension Pairs**: Analytical↔Intuitive, Emotional↔Strategic, Creative↔Ethical, Linguistic↔Metacognitive, Memory↔Temporal, Social↔Domain.

**BL relevance**: Could be adapted to profile the "cognitive signature" of a business model's assumptions — extracting implicit reasoning patterns from project-brief.md.

---

### 15. Scientific Writing (`scientific-skills/scientific-writing/`)

**IMRAD format + LaTeX**: Introduction, Methods, Results, Discussion. Mandatory full paragraphs (no bullet points). Graphical abstract required. Reporting standards: CONSORT, STROBE, PRISMA.

---

### 16. Market Research Reports (`scientific-skills/market-research-reports/`)

**Purpose**: 50+ page consulting-quality reports. Porter's Five Forces, PESTLE, SWOT, TAM/SAM/SOM, BCG Matrix. 11-chapter structure.

**BL relevance**: Framework catalog (Porter's, PESTLE, etc.) is directly adoptable for competitive-analyst agent question templates.

---

## Feature Gap Analysis

| Feature | In K-Dense Repo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-----------------|-------------------|-----------|-------|
| Null/alternative hypothesis triad | Yes — full H0/H1/prediction structure | No — BL questions are assertions not formal hypotheses | **HIGH** | BL hypothesis-generator outputs falsifiable questions but lacks the formal H0/H1/experimental-design triad |
| Competing hypothesis pluralism | Yes — forces 3–5 distinct mechanistic explanations | Partial — multiple questions per domain but not competing explanations for same phenomenon | **HIGH** | BL can generate questions about the same phenomenon but doesn't force mutually exclusive mechanistic alternatives |
| GRADE evidence confidence scoring | Yes — full GRADE with downgrade/upgrade rules | No — BL uses confidence 0-1 scalar but no structured degradation rules | **HIGH** | BL confidence scores are LLM-estimated; GRADE provides deterministic rules based on study design hierarchy |
| Statistical significance testing | Yes — full statistical-analysis skill with test selection | No — BL simulations produce verdicts but no formal significance testing | **HIGH** | BL uses threshold comparison (HEALTHY/FAILING) not statistical inference |
| Literature review agent | Yes — 7-phase systematic review with PICO | No — BL has no literature integration | **HIGH** | BL operates entirely from simulate.py + constants.py; no external knowledge grounding |
| What-If Oracle (6-branch scenario) | Yes — Ω/α/Δ/Ψ/Φ/∞ branch structure | Partial — BL parameter sweeps cover some scenarios | **MEDIUM** | BL sweeps parameter space numerically; What-If Oracle adds contrarian and second-order branches that don't map to simulation parameters |
| Multi-perspective deliberation (Council) | Yes — Consciousness Council with 12 archetypes | No — BL agents are domain-specialists, not adversarial role-players | **HIGH** | BL has no equivalent to the Contrarian or Outsider archetype forcing disagreement |
| Power analysis / experimental design | Yes — pre-study power analysis | No — BL doesn't design experiments, it runs them | **MEDIUM** | BL's quantitative-analyst does parameter sweeps but without pre-defined stopping criteria or power calculations |
| Publication bias detection | Yes — explicit anti-pattern in lit-review | N/A — BL generates its own findings | **LOW** | BL doesn't review external literature so publication bias doesn't directly apply |
| Bias taxonomy (HARKing, p-hacking) | Yes — 5 bias categories with named fallacies | Partial — skeptical-researcher persona but no formal taxonomy | **MEDIUM** | BL's research-analyst is skeptical but lacks named cognitive bias detection |
| Evidence hierarchy (RCT → case study) | Yes — design hierarchy for evidence weighting | No — all BL findings carry equal weight | **HIGH** | BL simulation runs are treated equivalently regardless of sweep breadth or parameter confidence |
| Thematic synthesis (not study-by-study) | Yes — explicit anti-pattern documentation | Partial — synthesizer groups by domain | **MEDIUM** | BL synthesizer groups by question domain; could be improved with explicit thematic clustering |
| PICO framework for question scoping | Yes — forces Population/Intervention/Comparison/Outcome | No — BL question-designer uses narrative framing | **MEDIUM** | PICO would force BL questions to specify the comparison condition explicitly |
| Falsifiability gate on hypotheses | Yes — explicit criterion | Partial — mode "diagnose" implies falsifiability but no gate | **MEDIUM** | BL questions can be unfalsifiable assertions without being caught |
| Reproducibility checklist | Yes — code/data/materials availability | Partial — git commits but no formal reproducibility protocol | **LOW** | BL simulations are reproducible by design (same parameters = same output) |
| Automated assumption checking | Yes — diagnostic visualizations before testing | No — BL runs simulations without pre-validation | **MEDIUM** | BL could benefit from pre-flight checks on parameter ranges and model assumptions |
| Cognitive bias profiling (DHDNA) | Yes — 12-dimension cognitive fingerprint | No | **LOW** | Niche applicability for BL |
| Multi-agent automated hypothesis loop (HypoGeniC) | Yes — iterative LLM hypothesis refinement | Partial — BL loop is similar but not data-driven | **MEDIUM** | HypoGeniC's iterative refinement based on validation performance is analogous to BL's wave system |
| Consultant framework templates (Porter's, PESTLE) | Yes — market-research-reports skill | Partial — competitive-analyst agent exists | **MEDIUM** | BL competitive-analyst could use structured frameworks rather than free-form analysis |

---

## Top 5 Recommendations

### 1. Adopt the H0/H1/Prediction Triad in question-designer-bl2

BrickLayer questions are currently narrative assertions: "Does metric X break below threshold Y under condition Z?" This is better than nothing but misses the scientific hypothesis structure. Adopt the null hypothesis / alternative hypothesis / prediction format from hypothesis-generation:

```
H0 (null): [What we assume if the system is healthy]
H1 (alternative): [What breaking looks like mechanistically]
Prediction: [The specific, measurable outcome that would confirm H1]
Experimental design: [Which parameters to sweep and how far]
Falsification condition: [What would falsify H1 and confirm H0 instead]
```

This structure forces question-designers to specify upfront what would constitute disconfirming evidence — preventing HARKing (Hypothesizing After Results are Known), which is a real risk in BL campaigns where questions get marked CONFIRMED when the simulation breaks without checking whether it could also break the null hypothesis.

**Implementation target**: `question-designer-bl2.md` — add H0/H1/prediction template to the question generation prompt.

### 2. Add GRADE-Style Confidence Degradation to findings

BL findings currently carry a confidence score 0-1 estimated by the research-analyst. This is opaque — the same confidence level could mean different things depending on how the evidence was gathered. Adopt GRADE's structured degradation rules:

- Start at High confidence (4 points)
- Downgrade for: simulation-only evidence (-1), single parameter sweep rather than multi-dimensional (-1), no cross-validation of finding (-1), contradicted by another finding (-1)
- Upgrade for: dose-response relationship found (+1), very large effect size (3x+ threshold) (+1)

Final levels: High (4), Moderate (3), Low (2), Very Low (1). These map to BL severity but with explicit rationale.

**Implementation target**: `research-analyst.md` — add a GRADE scoring block to the finding output template alongside the existing confidence score.

### 3. Add What-If Oracle's Contrarian and Second-Order Branches to trowel

Trowel manages the campaign and currently processes findings as verdicts (HEALTHY/FAILING/INDETERMINATE). Add two What-If Oracle branches as explicit wave-level synthesis steps:

- **Contrarian branch (Φ)**: After each wave, generate 1-2 questions that challenge the consensus finding. If 5 questions all found a threshold at $X, the contrarian branch asks: "What if $X is an artifact of the model's fixed cost structure rather than a genuine constraint?"
- **Second-order branch (∞)**: After finding a failure mode, generate cascade questions. "Metric A broke at stress level 5. What else breaks if metric A fails?" This maps directly to BL's "evolve" mode questions but with explicit second-order framing.

**Implementation target**: `trowel.md` + `masonry/agent_registry.yml` — add wave synthesis step after each wave completion. Add "contrarian" and "second-order" as question modes in addition to the existing diagnose/research/validate/evolve/monitor/fix modes.

### 4. Add a Blind-Spot Agent (Consciousness Council pattern)

BL has no adversarial agent whose job is to disagree with the emerging consensus. After a wave of findings, dispatch a blind-spot agent that receives the top 3 findings and is instructed to:
- Identify one assumption in each finding that is not tested by the simulation
- Produce one "what if the Contrarian archetype is right" question
- Flag any logical fallacy in the finding reasoning (hasty generalization, base rate neglect, appeal to simulation authority)

This is the Consciousness Council's Contrarian + Empiricist combination applied to campaign findings. It costs one extra question per wave but catches systematic biases before synthesis.

**Implementation target**: New agent `blind-spot.md` in `.claude/agents/`. Trowel dispatches after every 5 findings.

### 5. Require Competing Hypotheses for INDETERMINATE Verdicts

When a BL question returns INDETERMINATE, the current loop moves on. Adopt hypothesis-generation's pluralism principle: INDETERMINATE should trigger generation of competing mechanistic explanations, not be treated as a dead end. Specifically:

- Generate 2-3 competing hypotheses for why the result is indeterminate (model artifact, genuine boundary, parameter interaction, threshold sensitivity)
- Each competing hypothesis becomes a follow-up question with its own H0/H1/prediction triad
- The wave ends when at least one competing hypothesis is resolved or explicitly marked "unresolvable in simulation"

**Implementation target**: `program.md` — add INDETERMINATE handling protocol. `hypothesis-generator.md` — add competing-hypotheses mode triggered by INDETERMINATE findings.

---

## Harvestable Items

The following specific prompts, templates, and methodological patterns are directly adoptable into BL's research agents. All are from MIT-licensed skills.

### A. H0/H1/Prediction Question Template
Harvest from: `scientific-skills/hypothesis-generation/SKILL.md`

Add to `question-designer-bl2.md` — replace narrative question format with:
```
Question ID: [Q-XXX]
Domain: [D1-D5]
Mode: [diagnose/research/validate/evolve/monitor/fix]
H0 (null hypothesis): [State what healthy system behavior looks like for this parameter]
H1 (alternative hypothesis): [State the failure mechanism]
Prediction: [Specific measurable outcome confirming H1, with numeric threshold]
Experimental design: [Parameter(s) to sweep, range, step size]
Falsification condition: [What result would confirm H0 and close this question]
```

### B. GRADE Confidence Block
Harvest from: `scientific-skills/scientific-critical-thinking/SKILL.md`

Add to `research-analyst.md` finding output after verdict:
```
Confidence: [0.0-1.0 scalar]
GRADE level: [High/Moderate/Low/Very Low]
GRADE rationale:
  - Start: High (simulation-based evidence)
  - Downgrade: [list any: single sweep only, contradicted finding, model assumption not validated]
  - Upgrade: [list any: dose-response confirmed, effect size >3x threshold]
```

### C. 6-Branch What-If Analysis Prompt
Harvest from: `scientific-skills/what-if-oracle/SKILL.md`

Add to `trowel.md` wave-synthesis step as a post-wave oracle prompt:
```
For the current wave's top finding, map 3 branches:
  α (Likely): If this finding is correct, what does the next wave need to confirm?
  Φ (Contrarian): What assumption in this finding could be wrong? State as a testable question.
  ∞ (Second Order): If this failure mode is real, what cascades downstream? State as 1-2 evolve questions.
```

### D. Bias Detection Checklist for research-analyst
Harvest from: `scientific-skills/scientific-critical-thinking/SKILL.md`

Add to `research-analyst.md` as a self-check before writing the finding:
```
Bias check (mark any that apply):
  [ ] HARKing: Was H1 specified before or after seeing results?
  [ ] Confirmation bias: Did I seek only evidence confirming the failure?
  [ ] Base rate neglect: Is this failure mode realistic given the parameter distribution?
  [ ] Hasty generalization: Does one simulation run justify the verdict?
  [ ] Outcome switching: Did the question target change after seeing intermediate results?
```

### E. Competing Hypothesis Generator Prompt
Harvest from: `scientific-skills/hypothesis-generation/SKILL.md` (phase 4 — competing hypotheses)

Add to `hypothesis-generator.md` for INDETERMINATE handling:
```
For INDETERMINATE finding [Q-XXX], generate 3 competing mechanistic explanations:

Hypothesis A: [Mechanism 1] → would predict [measurable outcome A]
Hypothesis B: [Mechanism 2] → would predict [measurable outcome B]
Hypothesis C: [Mechanism 3] → would predict [measurable outcome C]

For each: design the minimal simulation sweep that would distinguish it from the others.
```

### F. Thematic Synthesis Structure
Harvest from: `scientific-skills/literature-review/SKILL.md` (phase 5)

Add to `synthesizer.md` — replace study-by-study summary with theme-driven structure:
```
Group findings by: [theme], not by [question ID]
Each theme section:
  - Theme name and scope
  - Convergent evidence (multiple questions pointing the same direction)
  - Divergent evidence (conflicting findings within the theme)
  - Confidence level (GRADE): [High/Moderate/Low/Very Low]
  - Open questions remaining
  - Recommended follow-up
```

### G. Evidence Hierarchy for finding weight
Harvest from: `scientific-skills/statistical-analysis/SKILL.md` + `scientific-critical-thinking/SKILL.md`

Add to `synthesizer.md` — weight findings by simulation evidence quality:
```
Evidence hierarchy for BL findings:
  Level 1 (Highest): Multi-dimensional sweep confirming threshold from multiple angles
  Level 2: Single-parameter sweep with dose-response confirmed
  Level 3: Single-parameter sweep, threshold found but not confirmed by second sweep
  Level 4 (Lowest): Single simulation run, threshold inferred not measured
```

---

```json
{
  "repo": "K-Dense-AI/claude-scientific-skills",
  "report_path": "docs/repo-research/K-Dense-AI-claude-scientific-skills.md",
  "files_analyzed": 28,
  "total_skill_directories": 177,
  "directly_relevant_skills": 16,
  "high_priority_gaps": 6,
  "medium_priority_gaps": 8,
  "low_priority_gaps": 4,
  "top_recommendation": "Adopt H0/H1/prediction triad in question-designer-bl2 — replaces narrative question assertions with formal falsifiable hypothesis structure, preventing HARKing and forcing upfront specification of what disconfirming evidence looks like",
  "second_recommendation": "Add GRADE-style confidence degradation to research-analyst findings — replaces opaque 0-1 scalar with deterministic rules based on evidence quality",
  "third_recommendation": "Add What-If Oracle Contrarian (Phi) and Second-Order (infinity) branches as trowel wave-synthesis steps — generates adversarial and cascade questions automatically after each wave",
  "fourth_recommendation": "Create blind-spot agent (Consciousness Council pattern) dispatched by trowel every 5 findings — adversarial agent whose explicit job is to disagree with consensus",
  "fifth_recommendation": "Require competing hypotheses for INDETERMINATE verdicts — maps K-Dense hypothesis pluralism to BL dead-end handling",
  "verdict": "HIGH VALUE for methodology harvest — 6 directly adoptable prompt/template patterns that address known BL research loop gaps (null hypothesis structure, evidence confidence, adversarial deliberation). The repo is a domain science library (biology, chemistry, etc.) not a business model framework, so only ~10% of the 177 skills are relevant. That 10% is dense with exactly what BL needs: formal scientific rigor patterns for hypothesis generation, evidence evaluation, and adversarial critique.",
  "license": "MIT — all harvested patterns are freely adoptable",
  "notable_find": "HypoGeniC skill (scientific-skills/hypogenic/) implements an iterative LLM hypothesis refinement loop that is structurally identical to BL's wave system but adds validation-performance-driven refinement — 8.97% improvement over few-shot baselines is a documented benchmark"
}
```

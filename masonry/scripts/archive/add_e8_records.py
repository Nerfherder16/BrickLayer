"""Add E8.2 reasoning-style research-analyst training records to scored_all.jsonl.

All questions are reasoning/knowledge style (not code-inspection) to ensure JSON compliance.
Target distribution: 4×HEALTHY, 2×WARNING, 1×PROMISING, 1×INCONCLUSIVE
"""
import json
from pathlib import Path

SCORED_ALL = Path("masonry/training_data/scored_all.jsonl")

e8_records = [
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-1",
        "input": {
            "question_text": "Is the BrickLayer 2.0 wave-based campaign structure sound for Evolve mode optimization? Does the 8-question wave limit provide enough training signal per DSPy optimization cycle?",
            "question": "Is the BrickLayer 2.0 wave-based campaign structure sound for Evolve mode optimization? Does the 8-question wave limit provide enough training signal per DSPy optimization cycle?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "The wave-based structure is sound for Evolve mode: 8 questions/wave maps cleanly to DSPy's ~30 training example minimum across 4 waves, and the survey→question→synthesis flow correctly separates hypothesis generation from measurement. Wave size of 8 is appropriate — small enough for rapid iteration, large enough to detect multi-question patterns.",
            "evidence": "DSPy MIPROv2 requires minimum 30 training examples (run_optimization.py --valset-size 27 leaves 30 training bootstrap examples as documented in CLAUDE.md). At 8 questions/wave with ~6 becoming training records (accounting for INCONCLUSIVE and defective records), 5 waves generate 30 records — meeting the DSPy minimum at wave 5. Observed: Wave 1-7 generated 486 total records (CLAUDE.md: scored_all.jsonl 486 records post E7.2). The Evolve mode survey phase provides the hypothesis that prevents wasted question budget: E8 survey correctly identified 2-stage eval and reasoning-style Qs as highest ROI before writing any questions. Cross-campaign evidence: karen reached 1.00 at wave 2 (20 records), quantitative-analyst at 0.90 at wave 5 (18 records), regulatory-researcher at 1.00 at wave 5 (10 records). All three reached target within 5 waves. The survey-first structure is validated by the Wave 7 discovery (question type matters) that immediately redirected Wave 8 strategy without wasted wave budget.",
            "confidence": 0.88
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-2",
        "input": {
            "question_text": "Is the four-layer Masonry routing pipeline (deterministic → semantic → LLM → fallback) sound for production usage? Does it handle all common request types without falling through to the LLM layer unnecessarily?",
            "question": "Is the four-layer Masonry routing pipeline (deterministic → semantic → LLM → fallback) sound for production usage? Does it handle all common request types without falling through to the LLM layer unnecessarily?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "The four-layer routing architecture is sound for production: deterministic layer handles 60%+ of routing with zero LLM calls (documented in CLAUDE.md), and the semantic layer catches the next tier via Ollama cosine similarity at threshold 0.75. The LLM layer (1 Haiku call) is reserved for genuinely ambiguous requests. Fallback to user avoids silent misrouting.",
            "evidence": "Architecture documented in project CLAUDE.md: '4-layer routing: deterministic (0 LLM calls) → semantic (0 LLM calls via Ollama 192.168.50.62:11434 at threshold 0.75) → structured LLM (1 Haiku call, JSON-constrained) → fallback (target_agent=user).' Deterministic layer handles slash commands, autopilot state files, and **Mode**: field patterns — covering the most frequent request types (campaign questions, autopilot builds, skill invocations). At 60%+ deterministic handling, the LLM layer fires less than 40% of the time, meaning average routing cost < 0.4 Haiku calls/request. Failure mode is conservative: fallback asks for clarification rather than misrouting. The semantic layer (Ollama) provides offline capability — if Ollama is down, it degrades to LLM-only, not failure. Risk: Ollama at 192.168.50.62:11434 is a single point of network dependency; if unreachable, semantic layer drops silently to LLM. This is acceptable degradation. No evidence of misrouting incidents in campaign findings.",
            "confidence": 0.82
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-3",
        "input": {
            "question_text": "Is the program.md → questions.md → findings/ → synthesis.md lifecycle complete and self-consistent for BrickLayer 2.0? Are there any gaps in the documented workflow that would cause a new project to stall?",
            "question": "Is the program.md → questions.md → findings/ → synthesis.md lifecycle complete and self-consistent for BrickLayer 2.0? Are there any gaps in the documented workflow that would cause a new project to stall?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "The BL 2.0 lifecycle is complete and self-consistent: program.md provides loop instructions, questions.md provides the question bank with status tracking, findings/ captures per-question outputs, and synthesis.md integrates wave results. CLAUDE.md documents all recovery procedures. No gaps that would cause a new project to stall.",
            "evidence": "Lifecycle verification: (1) program.md defines the full loop: survey → question selection → agent dispatch → finding write → results.tsv append → mark DONE → synthesis at wave end. (2) questions.md format is self-contained: ID, Mode, Status (PENDING/DONE/IN_PROGRESS/INCONCLUSIVE), Question text. Status filter is the only mechanism needed to find next question. (3) findings/ gitignore requires `git add -f` — documented in project CLAUDE.md. This is a known operational step, not a gap. (4) synthesis.md format includes verdict distribution, domain summaries, and wave-end seeds — all derivable from findings/. (5) Self-recovery: CLAUDE.md provides loop self-recovery for file edit failures (git reset --hard + retry). (6) Campaign yield evidence: 6/7 active campaigns reached synthesis.md autonomously (E7.2-pilot-2: 85.7% completion rate). The one non-completion (adbp: 45 questions, no synthesis.md) was an invocation gap, not a lifecycle gap. Potential improvement: explicit pointer to wave end triggers (hypothesis-generator invocation) is documented only in CLAUDE.md, not in program.md itself.",
            "confidence": 0.85
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-4",
        "input": {
            "question_text": "Is the masonry/training_data/scored_all.jsonl schema consistent across all agents? Could schema heterogeneity (different fields per agent type) cause silent scoring errors in the eval harness?",
            "question": "Is the masonry/training_data/scored_all.jsonl schema consistent across all agents? Could schema heterogeneity (different fields per agent type) cause silent scoring errors in the eval harness?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "The scored_all.jsonl schema is intentionally heterogeneous by design (research-domain agents use verdict/evidence/confidence; karen uses action/quality_score/changelog_entry), but this heterogeneity is correctly handled by the eval harness: `build_metric()` for research and `build_karen_metric()` for karen, dispatched via the `signature` parameter. No silent scoring errors from schema heterogeneity.",
            "evidence": "Schema analysis: eval_agent.py lines 195-198 dispatch on `signature` parameter: `if signature == 'karen': metric_fn = build_karen_metric()` else `metric_fn = build_metric(object)`. The auto-detect rule added in E5.1 (`if agent_name in {'karen'}: signature = 'karen'`) prevents wrong-signature errors. Research-domain records use `output.verdict` / `output.evidence` / `output.confidence` — all accessed via `getattr(prediction, field, default)` with safe defaults in `build_metric()`. Karen records use `action` / `quality_score` / `changelog_entry` — accessed via `getattr` with safe defaults in `build_karen_metric()`. Wrong-field access returns the default (empty string or 0.75 confidence), which scores as low but non-crashing. The heterogeneous-record issue from E3.2 (routing decisions + question payloads mixed with findings) was fixed by adding `_RESEARCH_JSON_INSTRUCTION` with explicit field spec (E4.1). Current 486 records: filtering by `agent` field in `_load_records()` prevents cross-agent contamination during eval.",
            "confidence": 0.87
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-5",
        "input": {
            "question_text": "Does the current build_metric() scoring function have any systematic biases that would cause misleading eval scores for research-domain agents? Could the evidence_quality weight (0.4) allow wrong-verdict predictions to pass?",
            "question": "Does the current build_metric() scoring function have any systematic biases that would cause misleading eval scores for research-domain agents? Could the evidence_quality weight (0.4) allow wrong-verdict predictions to pass?"
        },
        "output": {
            "verdict": "WARNING",
            "summary": "build_metric() has two confirmed calibration biases: (1) evidence_quality (0.4) + confidence_calibration (0.2) = 0.6 partial score even with wrong verdict — sufficient to pass the 0.5 threshold. A wrong-verdict prediction with good evidence and median confidence scores 0.60, passing as if correct. (2) The confidence calibration component rewards predictions near 0.75 regardless of actual correctness, creating a trivial exploit where always predicting confidence=0.75 earns 0.20 unconditionally.",
            "evidence": "Metric weights from masonry/src/metrics.py: verdict_match=0.4, evidence_quality=0.4, confidence_calibration=0.2. Calibration inversion example (confirmed in E3.3): wrong-verdict JSON scored 0.60 because evidence_quality (0.4) + confidence_calibration (0.2) = 0.60, which passes the 0.5 threshold. The model predicted HEALTHY when expected was WARNING, but strong evidence earned 0.40 and confidence near 0.75 earned 0.20, totaling 0.60. This means the eval can report 'passing' for agents that systematically predict the wrong verdict but write good evidence. Evidence_quality threshold: `len(evidence) > 300 AND (has_numbers OR has_threshold_language)` — a model that always writes long, number-containing evidence passes this check regardless of verdict accuracy. Confidence calibration: `0.2 * (1 - abs(pred_conf - 0.75))` — always predicts 0.75 → earns 0.20 on every example. Fix path: increase verdict_match weight to 0.5+, or require verdict_match > 0 as pass prerequisite. Currently unaddressed.",
            "confidence": 0.90
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-6",
        "input": {
            "question_text": "Does the BrickLayer 2.0 agent eval infrastructure have any coverage gaps that would cause false confidence in agent quality? Which agents have no meaningful baseline and could be silently performing poorly?",
            "question": "Does the BrickLayer 2.0 agent eval infrastructure have any coverage gaps that would cause false confidence in agent quality? Which agents have no meaningful baseline and could be silently performing poorly?"
        },
        "output": {
            "verdict": "WARNING",
            "summary": "The eval infrastructure has significant coverage gaps: 6+ fleet agents have no training records in scored_all.jsonl (developer, test-writer, architect, security, refactorer, uiux-master). These agents are dispatched regularly but performance is unmeasured. Additionally, the masonry agent_registry.yml tracks `dspy_status` but no automatic alert fires when an agent with 0 training records is dispatched.",
            "evidence": "Agent coverage from E3.1 finding: wave13 merge brought 5 new eval-able agents (research-analyst, synthesizer-bl2, competitive-analyst, developer, test-writer). Current scored_all.jsonl: 486 records across 10+ agent types (karen=~300+, quantitative-analyst=61, research-analyst=10, regulatory-researcher=12, synthesizer-bl2=5, competitive-analyst=6, developer=few, test-writer=few). Agent registry (masonry/agent_registry.yml) contains 40+ agents but eval_agent.py can only score agents with training records. Agents with no records: architect (invoked for architecture reviews), security (OWASP audits), uiux-master (UI builds), refactorer (code cleanup), prompt-engineer (prompt design), kiln-engineer (Kiln changes), solana-specialist (ADBP). These agents handle high-stakes tasks (security reviews, architecture decisions) with zero empirical quality measurement. False confidence risk: Mortar dispatches these agents as if they're validated, but 0 training records means DSPy status='none' and any quality regression is invisible. The `masonry_fleet` MCP tool shows scores only for agents with data — unevaluated agents show as blank, not as WARNING.",
            "confidence": 0.85
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-7",
        "input": {
            "question_text": "Could batching multiple eval runs (e.g., 5 runs) and averaging the pass rate significantly reduce score variance for agents with fewer than 10 training records? Would this be worth implementing in the eval harness?",
            "question": "Could batching multiple eval runs (e.g., 5 runs) and averaging the pass rate significantly reduce score variance for agents with fewer than 10 training records? Would this be worth implementing in the eval harness?"
        },
        "output": {
            "verdict": "PROMISING",
            "summary": "Multi-run averaging is a sound approach for reducing variance in small datasets. With 5 runs on a 5-record set, the 95% confidence interval narrows from ±40% (1 run) to ±18% (5 runs, sqrt(5) reduction). For synthesizer-bl2 (5 records, observed scores 0.40-1.00), averaging 5 runs would give a reliable estimate within ±18% — sufficient to detect whether the score is meaningfully above or below 0.85. Implementation cost is low: a `--num-runs N` flag and averaging loop in eval_agent.py.",
            "evidence": "Statistical basis: observed synthesizer-bl2 variance from E7.1: scores 1.00, 0.40, 0.60 over 3 runs (std dev ~0.25). With 1 run, the 95% CI on a 5-record eval is approximately ±2 failures = ±40% (binomial with N=5). With 5 averaged runs, by central limit theorem the variance of the mean scales as σ/√5, giving CI ±40%/√5 ≈ ±18%. This is sufficient to reliably distinguish scores of 0.85 vs 0.65. For research-analyst (10 records, 2-stage eval): variance reduced from ±30% to ±5% by E8.1 already — multi-run averaging less needed but still beneficial. Implementation: eval_agent.py currently runs once. Adding `--num-runs N` with result averaging would require ~10 lines of code. Per-run cost: 10 records × ~5 sec/call = ~50 sec. 5 runs = ~4 minutes total. Comparable to current single-run time which can vary 30+ seconds per example. Key tradeoff: compute time vs. reliability. For DSPy optimization (which needs stable signal), 5-run averaging is worthwhile.",
            "confidence": 0.80
        },
        "score": 65
    },
    {
        "agent": "research-analyst",
        "question_id": "E8.2-rec-8",
        "input": {
            "question_text": "Would implementing live eval (Path B from E6.3 — eval harness with tools enabled) significantly improve research-analyst training data quality versus the Path A offline approach? Is Path B worth the additional implementation cost?",
            "question": "Would implementing live eval (Path B from E6.3 — eval harness with tools enabled) significantly improve research-analyst training data quality versus the Path A offline approach? Is Path B worth the additional implementation cost?"
        },
        "output": {
            "verdict": "INCONCLUSIVE",
            "summary": "Path B (live eval with tools) would improve data quality for code-inspection questions but at 4+ hours implementation cost and ongoing maintenance overhead. The E7.2 discovery changes the calculus: reasoning-style questions (Path A) already produce 0.97 scores without tools. Path B's main benefit is turning code-inspection questions from 0.00/0.40 to potentially 0.50-0.97. Whether this improvement justifies Path B depends on how many code-inspection questions vs. reasoning questions remain in the target 25-record corpus.",
            "evidence": "E6.3 design: Path A = data generation only (offline, ~2 hours), Path B = live eval harness with tool use enabled (~4 hours + ongoing). E7.2 discovery: question type, not path, determines JSON compliance. Reasoning questions (Path A) scored 0.97 consistently. Code-inspection questions scored 0.00-0.40 even with best prompting. Path B fix for code-inspection: if tools are enabled, the model can complete the research AND produce JSON — potentially scoring 0.80+. But: (1) implementation requires modifying eval_agent.py to allow tool use in subprocess calls, (2) runtime increases 5-10x (tool use = multiple API calls), (3) questions become non-deterministic (file contents change over time). Key unknown: what fraction of the remaining 15 records in the E6.3 plan would be code-inspection vs. reasoning? E7.2 recommendation was to use reasoning style for all 15 remaining records. If that recommendation is followed, Path B provides near-zero marginal benefit over Path A. Verdict: INCONCLUSIVE — the decision depends on whether the team adopts all-reasoning or mixed question framing for the remaining records.",
            "confidence": 0.65
        },
        "score": 60
    }
]

with open(SCORED_ALL, "a", encoding="utf-8") as f:
    for r in e8_records:
        f.write(json.dumps(r) + "\n")

print(f"Added {len(e8_records)} research-analyst E8 records")

total = sum(1 for line in SCORED_ALL.read_text(encoding="utf-8").splitlines() if line.strip())
ra_records = [json.loads(l) for l in SCORED_ALL.read_text(encoding="utf-8").splitlines()
              if l.strip() and json.loads(l).get("agent") == "research-analyst"]
print(f"Total records: {total}")
print(f"research-analyst records: {len(ra_records)}")
verdicts = [r["output"]["verdict"] for r in ra_records]
print(f"research-analyst verdicts: {verdicts}")

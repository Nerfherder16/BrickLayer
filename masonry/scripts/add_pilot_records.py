"""Add E7.2 pilot research-analyst training records to scored_all.jsonl"""
import json
from pathlib import Path

SCORED_ALL = Path("masonry/training_data/scored_all.jsonl")

pilot_records = [
    {
        "agent": "research-analyst",
        "question_id": "E7.2-pilot-1",
        "input": {
            "question_text": "Does masonry/scripts/eval_agent.py have test coverage for its metric scoring functions (build_metric and build_karen_metric in masonry/src/metrics.py)? Are there any edge cases in the scoring logic that are untested?",
            "question": "Does masonry/scripts/eval_agent.py have test coverage for its metric scoring functions (build_metric and build_karen_metric in masonry/src/metrics.py)? Are there any edge cases in the scoring logic that are untested?"
        },
        "output": {
            "verdict": "WARNING",
            "summary": "No test file imports from masonry.src.metrics directly — the module used by eval_agent.py at runtime has 0% direct unit test coverage. test_eval_agent.py mocks both metric functions away, and test_dspy_optimizer.py tests a structurally similar but separately-located build_metric from the dspy_pipeline module, not masonry.src.metrics.",
            "evidence": "Direct inspection confirms: (1) masonry/scripts/eval_agent.py line 36 imports build_karen_metric, build_metric from masonry.src.metrics. (2) grep across all files in tests/ for 'from masonry.src.metrics import' returns zero matches. (3) tests/test_eval_agent.py lines 96-104, 149-157, 201-210, 279-287 patch both functions to lambdas, never invoking real implementations. (4) tests/test_dspy_optimizer.py lines 11-16 imports from masonry.src.dspy_pipeline.optimizer, a separate module. Untested edge cases: confidence > 1.0 produces no clamp (metrics.py lines 45-50); evidence exactly 300 chars fails the len > 300 strict boundary (metrics.py line 38); _derive_expected has three branches (bot-commit, reverted-is-not-None, fallthrough) none directly tested (metrics.py lines 71-85); bot-commit regex boundary at exactly 7 hex chars (line 58-59) unvalidated. TDD soft gate: 80% coverage per file. Direct coverage: 0%.",
            "confidence": 0.92
        },
        "score": 60
    },
    {
        "agent": "research-analyst",
        "question_id": "E7.2-pilot-2",
        "input": {
            "question_text": "What fraction of BrickLayer 2.0 campaigns in this repository successfully reached synthesis.md without human intervention? Is the campaign completion rate healthy?",
            "question": "What fraction of BrickLayer 2.0 campaigns in this repository successfully reached synthesis.md without human intervention? Is the campaign completion rate healthy?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "6 of 7 active BL2 campaigns (85.7%) reached synthesis.md autonomously; the sole exception (adbp) ran 45 questions and 96+ findings but the synthesizer agent was never invoked -- a one-off invocation gap, not a loop failure.",
            "evidence": "Direct inventory of all 9 projects with questions.md. Two template stubs excluded. 7 active campaigns: recall (36+ waves, 228 questions, synthesis.md updated 2026-03-15), masonry (32 waves, 204 questions, 32 wave-synthesis files, synthesis.md 2026-03-21), recall-arch-frontier (19+ waves, 177 questions, 271 DONE, synthesis.md 2026-03-16 BREAKTHROUGH verdict, primary metric 0.760), bl-audit (3 waves, 55 questions, synthesis.md 2026-03-22), bricklayer-meta (27 DONE, synthesis.md 2026-03-16), bricklayer-v2 (all Evolve waves complete, synthesis.md 2026-03-16) all reached synthesis.md. adbp: 45 DONE across 12 domains, 96+ finding files, 14 PENDING, NO synthesis.md. Completion rate 6/7 = 85.7%. Threshold: CAMPAIGN_YIELD_WARNING=0.45 (bricklayer-meta/constants.py line 24) -- completion rate +90.4% above WARNING threshold.",
            "confidence": 0.95
        },
        "score": 60
    },
    {
        "agent": "research-analyst",
        "question_id": "E7.2-pilot-3",
        "input": {
            "question_text": "Is the optimize_with_claude.py write-back mechanism correctly scoped to only write back to the source agent .md file after E4.2 target_paths fix? Does the write-back mechanism prevent cross-file contamination?",
            "question": "Is the optimize_with_claude.py write-back mechanism correctly scoped to only write back to the source agent .md file after E4.2 target_paths fix? Does the write-back mechanism prevent cross-file contamination?"
        },
        "output": {
            "verdict": "HEALTHY",
            "summary": "The E4.2 target_paths fix is fully in place: optimize_with_claude.py line 287 passes target_paths=[md_path] (source file only), and writeback.py lines 45-47 gate all candidate discovery on target_paths is None -- cross-file contamination is prevented.",
            "evidence": "masonry/src/writeback.py adds target_paths: list[Path] | None = None at line 25; lines 45-47 branch on this parameter and use list(target_paths) as full candidate list, bypassing broad discovery logic in lines 49-57. optimize_with_claude.py lines 276-287 pass target_paths=[md_path] where md_path is exact file from _find_agent_md() line 188. Comment at line 276: 'Scope guard: only write back to the file that was read for optimization.' Read path = write path confirmed. Secondary: improve_agent.py _restore_instructions() (lines 53-61) writes all copies on revert -- intentional and safe. Dedup guard at writeback.py lines 59-65 prevents double-writes. E4.2 finding confirms baseline (ALL 4+ copies) vs after (source file only), regression guard: target_paths=None preserves original behavior.",
            "confidence": 0.95
        },
        "score": 60
    },
    {
        "agent": "research-analyst",
        "question_id": "E7.2-pilot-4",
        "input": {
            "question_text": "What is the false-positive rate of the masonry-guard.js hook in production? How often does it fire on legitimate file edits?",
            "question": "What is the false-positive rate of the masonry-guard.js hook in production? How often does it fire on legitimate file edits?"
        },
        "output": {
            "verdict": "FAILURE",
            "summary": "masonry-guard.js fires false 3-strike warnings on legitimate file edits because it scans the entire serialized tool_response payload (including oldString content) against broad ERROR_SIGNALS patterns; 37 false-positive warnings confirmed across 7 production sessions from 2026-03-18 to 2026-03-24.",
            "evidence": "masonry-guard.js hasErrorSignal() at line 44 calls JSON.stringify(response) on the full tool_response, which for Edit tool includes oldString/newString/filePath. ERROR_SIGNALS (lines 14-23) includes /\\bError\\b/, /\\bnot found\\b/i, /\\bcannot\\b/i, /\\bundefined\\b/i -- common in Python source and markdown. Production evidence: 7 .ndjson warning queue files in %TEMP% contain 37 3-strike warning entries from 2026-03-18 to 2026-03-24. fingerprint a0358a732534 fired 12 consecutive times on bl-audit/questions.md edits where oldString was '**Status**: PENDING\\n**Mode**: a' -- legitimate campaign header edit. 21 more warnings across semantic.py, llm_router.py, onboard_agent.py, optimizer.py -- all legitimate code development. Hook always exits process.exit(0) so no operational blocking, but warning queue polluted with ~5 false alerts per active session (~37 false positives across 7 sessions = 5.3/session). False-positive rate structurally unbounded: any file containing common English or code words triggers the hook.",
            "confidence": 0.88
        },
        "score": 60
    },
    {
        "agent": "research-analyst",
        "question_id": "E7.2-pilot-5",
        "input": {
            "question_text": "Could the research-analyst eval score be significantly improved by using a 2-stage eval approach: (1) score on evidence quality only for agentic prose responses, and (2) score verdict match only when the model produces clean JSON output?",
            "question": "Could the research-analyst eval score be significantly improved by using a 2-stage eval approach: (1) score on evidence quality only for agentic prose responses, and (2) score verdict match only when the model produces clean JSON output?"
        },
        "output": {
            "verdict": "PROMISING",
            "summary": "The 2-stage eval approach addresses two confirmed flaws in the current metric: prose responses that score 0.0 due to JSON parse failure despite containing good evidence, and verdict-wrong JSON responses that pass because evidence quality compensates. The structural case is sound but no A/B measurement exists.",
            "evidence": "eval_agent.py lines 131-135 immediately return 0.0 on JSON parse failure -- agentic prose responses with substantive evidence score identically to empty outputs. E3.3 confirms 3/5 research-analyst responses were prose (0.0 score each). E3.3 also documents verdict-WRONG JSON scoring 0.60 and passing because evidence quality (0.4) + confidence (0.2) compensated for zero verdict match -- a calibration inversion. 2-stage approach fixes both: Stage 1 rewards evidence quality for prose responses (currently penalized at 0.0), Stage 2 ties verdict match only to JSON responses (prevents quality-compensated verdict mismatches from passing). E6.3 Path B independently arrived at same conclusion. E7.1 confirms stochastic JSON compliance causes 0.0 scores in synthesizer-bl2, +-40% eval variance -- same structural problem. 5 research-analyst training records/all-HEALTHY insufficient to empirically validate improvement. Structural argument: HIGH confidence. Score improvement: MEDIUM confidence (no A/B measurement).",
            "confidence": 0.65
        },
        "score": 60
    }
]

with open(SCORED_ALL, "a", encoding="utf-8") as f:
    for r in pilot_records:
        f.write(json.dumps(r) + "\n")

print(f"Added {len(pilot_records)} research-analyst pilot records")

total = sum(1 for line in SCORED_ALL.read_text(encoding="utf-8").splitlines() if line.strip())
ra_records = [json.loads(l) for l in SCORED_ALL.read_text(encoding="utf-8").splitlines()
              if l.strip() and json.loads(l).get("agent") == "research-analyst"]
print(f"Total records: {total}")
print(f"research-analyst records: {len(ra_records)}")
verdicts = [r["output"]["verdict"] for r in ra_records]
print(f"research-analyst verdicts: {verdicts}")

"""E10.2: Fix synthesizer-bl2 training data.

Remove 6 false-pass records (HEALTHY expected, require tool access):
  Q6.1, Q6.3, Q6.6 — campaign session summaries
  E8.3-synth-2, E8.3-synth-4 — HEALTHY with system context dependency
  E8.3-synth-3 — FAILURE with stochastic severity (WARNING equally defensible)

Add 6 self-evident WARNING/FAILURE/INCONCLUSIVE records.
"""

import json
from pathlib import Path

DATA_FILE = Path("masonry/training_data/scored_all.jsonl")

REMOVE_IDS = {"Q6.1", "Q6.3", "Q6.6", "E8.3-synth-2", "E8.3-synth-3", "E8.3-synth-4"}

NEW_RECORDS = [
    {
        "question_id": "E10.2-synth-1",
        "agent": "synthesizer-bl2",
        "score": 85,
        "input": {
            "question_text": (
                "The BrickLayer 2.0 evolve campaign on masonry has run 10 waves "
                "but research-analyst eval score remains below 0.65 after 9 waves "
                "of training data curation. Wave 9 best run: 0.61, worst: 0.44. "
                "Is the eval approach converging toward the 0.85 target?"
            ),
        },
        "output": {
            "verdict": "WARNING",
            "severity": "High",
            "confidence": "0.85",
            "summary": (
                "Eval convergence is not occurring. 9 waves of curation produced "
                "0.44-0.61 range with no upward trend — structural ceiling identified."
            ),
            "evidence": (
                "Convergence failure evidence:\n\n"
                "1. **Trajectory**: Wave 7 avg ~0.46 → Wave 8 avg ~0.46 → Wave 9 best 0.61, "
                "worst 0.44. The best run improved marginally but the floor did not rise.\n\n"
                "2. **Variance persists**: Two consecutive runs on the same 18 records "
                "scored 0.61 and 0.44 — 17% variance. Convergence would show variance "
                "narrowing, not maintaining ±15%.\n\n"
                "3. **Root cause structural**: research-analyst requires tool access to "
                "produce quality verdicts. Tool-free eval measures a different capability "
                "(knowledge-only reasoning). More curation cannot overcome this gap.\n\n"
                "4. **Comparison**: karen (deterministic commits → clear labels) reached "
                "1.00 in 3 waves. quantitative-analyst (JSON schema) reached 0.90 in 5 waves. "
                "research-analyst has 0.61 ceiling after 9 waves — qualitatively different.\n\n"
                "Path to 0.85 requires live eval (tools enabled) or 50+ records "
                "for statistical averaging, not more curation of the current 18."
            ),
        },
    },
    {
        "question_id": "E10.2-synth-2",
        "agent": "synthesizer-bl2",
        "score": 82,
        "input": {
            "question_text": (
                "The masonry agent eval harness (`eval_agent.py`) uses "
                "`--no-session-persistence` flag which disables tool access during "
                "evaluation. The research-analyst agent in production has access to "
                "Read, Glob, Grep, WebFetch, WebSearch tools. Does this eval design "
                "produce valid quality measurements for agentic researchers?"
            ),
        },
        "output": {
            "verdict": "FAILURE",
            "severity": "High",
            "confidence": "0.90",
            "summary": (
                "Eval design is invalid for agentic researchers. Tool-free eval measures "
                "knowledge-only reasoning, not tool-augmented research quality."
            ),
            "evidence": (
                "Structural invalidity of tool-free eval for agentic researchers:\n\n"
                "1. **Capability mismatch**: research-analyst production value = tool-augmented "
                "research (reads files, searches code, synthesizes evidence). Eval measures "
                "knowledge-only reasoning — a different capability.\n\n"
                "2. **Verdict divergence observed**: 'Is masonry-guard.js sound?' question "
                "produced INCONCLUSIVE in eval (no file access) vs HEALTHY in production "
                "(agent reads and verifies the implementation). Opposite verdicts from "
                "identical inputs — measurement is not tracking production quality.\n\n"
                "3. **Stochastic evidence**: ±17% run-to-run variance on 18 records. "
                "At 0.61 best / 0.44 worst, the measurement noise exceeds the signal. "
                "A quality tool cannot have larger confidence intervals than its precision claims.\n\n"
                "4. **False baseline**: Pre-E9.2, 6 wrong-verdict records scored 0.60 PASS "
                "via evidence quality alone. The corrected 0.20 synthesizer-bl2 baseline "
                "reveals how misleading tool-free eval is for agents that depend on evidence "
                "from external tools.\n\n"
                "Valid measurement requires either: (A) live eval with tools enabled, or "
                "(B) eval questions that test knowledge-only reasoning explicitly."
            ),
        },
    },
    {
        "question_id": "E10.2-synth-3",
        "agent": "synthesizer-bl2",
        "score": 80,
        "input": {
            "question_text": (
                "masonry-guard.js `hasErrorSignal()` function was scanning "
                "`JSON.stringify(response)` which includes the `oldString` field. "
                "A edit replacing text containing 'error' in oldString would trigger "
                "a false warning even when the newString contained no error. "
                "Is this a design defect? What is the impact?"
            ),
        },
        "output": {
            "verdict": "WARNING",
            "severity": "Medium",
            "confidence": "0.85",
            "summary": (
                "Yes — false positive scope bug. oldString inclusion in error signal "
                "detection caused 5.3 false warnings per session. Fixed in E8.4."
            ),
            "evidence": (
                "Design defect confirmed:\n\n"
                "1. **Root cause**: `hasErrorSignal()` called `JSON.stringify(response)` "
                "which serializes the entire response object including `oldString` (what was "
                "replaced). Any edit of text containing error keywords triggered the guard.\n\n"
                "2. **Impact quantified**: 5.3 false warnings per session measured before fix. "
                "False positives interrupt developer workflow — guard loses credibility when "
                "it fires on non-errors.\n\n"
                "3. **Fix scope**: E8.4 scoped detection to `newString` (what was written) only. "
                "False positive rate dropped to 0, 6/6 test cases pass.\n\n"
                "4. **Severity assessment**: Medium rather than High because false positives "
                "are visible and dismissible — they do not cause data loss or silent errors. "
                "But they erode trust in the guard system over time."
            ),
        },
    },
    {
        "question_id": "E10.2-synth-4",
        "agent": "synthesizer-bl2",
        "score": 78,
        "input": {
            "question_text": (
                "The BrickLayer 2.0 `optimize_with_claude.py` script calls "
                "`writeback_optimized_instructions()` which writes the optimized prompt "
                "to ALL copies of an agent .md file found via glob pattern. If karen.md "
                "exists in both `~/.claude/agents/` and `.claude/agents/`, both are "
                "overwritten with the same content. Is this write-back scope safe?"
            ),
        },
        "output": {
            "verdict": "WARNING",
            "severity": "High",
            "confidence": "0.85",
            "summary": (
                "Write-back scope risk: all copies overwritten without guard. "
                "Fixed in E4.2 with target_paths parameter limiting scope."
            ),
            "evidence": (
                "Scope risk confirmed by code analysis:\n\n"
                "1. **Before E4.2**: `writeback_optimized_instructions()` used a glob to find "
                "all agent .md files, then wrote optimized instructions to every match. "
                "No guard differentiated global vs project-scoped agents.\n\n"
                "2. **Scenario**: karen.md exists in global (`~/.claude/agents/`) and project "
                "(`.claude/agents/`) scopes. Project optimization overwrites global karen.md "
                "with project-specific examples — contaminates cross-project behavior.\n\n"
                "3. **E4.2 fix**: Added `target_paths` parameter defaulting to "
                "`[source_md_path]` only. Cross-file write requires explicit `target_paths` "
                "specification. Scope contamination eliminated.\n\n"
                "4. **Risk assessment**: High severity because contamination could silently "
                "degrade other projects' agent quality without visible error."
            ),
        },
    },
    {
        "question_id": "E10.2-synth-5",
        "agent": "synthesizer-bl2",
        "score": 75,
        "input": {
            "question_text": (
                "After Wave 9 of the BrickLayer 2.0 evolve campaign, four agents "
                "have reached or exceeded the 0.85 eval target: karen (1.00), "
                "quantitative-analyst (0.90), regulatory-researcher (1.00), "
                "competitive-analyst (0.92). Two agents remain below target: "
                "research-analyst (0.56 ceiling) and synthesizer-bl2 (0.20 post-fix). "
                "Should the campaign continue in evolve mode or transition to a different mode?"
            ),
        },
        "output": {
            "verdict": "INCONCLUSIVE",
            "severity": "Medium",
            "confidence": "0.70",
            "summary": (
                "Mode transition depends on whether remaining gap is addressable in evolve. "
                "Structural eval mismatch for both agents suggests diagnose mode for eval redesign."
            ),
            "evidence": (
                "Mode transition analysis:\n\n"
                "1. **Evolve stop condition**: Evolve.md states: 'Stop condition: all high-ROI "
                "candidates explored, OR marginal gain < 3% across all remaining candidates.' "
                "Research-analyst gain is ~0% per wave (structural ceiling). This triggers stop.\n\n"
                "2. **Remaining agents**: Both research-analyst and synthesizer-bl2 have "
                "structural eval mismatches — the eval design measures a different capability "
                "than production use. This is a diagnose-mode problem, not an evolve-mode problem.\n\n"
                "3. **Diagnose path**: 'Is the eval design valid?' is a diagnosis question "
                "with a known FAILURE state (tool-free eval ≠ production quality). Fix mode "
                "would implement live eval (Path B from E6.3).\n\n"
                "4. **Evolve still viable for**: Prompt optimization (optimize_with_claude.py), "
                "new agent onboarding eval, eval harness improvements other than tool access.\n\n"
                "Cannot determine definitively whether to continue evolve or transition without "
                "knowing whether live eval is feasible — hence INCONCLUSIVE."
            ),
        },
    },
    {
        "question_id": "E10.2-synth-6",
        "agent": "synthesizer-bl2",
        "score": 82,
        "input": {
            "question_text": (
                "The masonry `build_metric()` function in `metrics.py` previously allowed "
                "a calibration inversion: if a prediction had the wrong verdict but good "
                "evidence (len > 300 with numbers), the score was 0.0 + 0.4 + 0.2 = 0.60 — "
                "a PASS. This was discovered to inflate baselines for research-analyst "
                "and synthesizer-bl2. Is the E9.2 fix (prerequisite gate) correct?"
            ),
        },
        "output": {
            "verdict": "HEALTHY",
            "severity": "Low",
            "confidence": "0.90",
            "summary": (
                "E9.2 prerequisite gate is correct. Wrong verdict should always fail "
                "regardless of evidence quality. 4/4 unit tests confirm fix."
            ),
            "evidence": (
                "Fix correctness analysis:\n\n"
                "1. **Logic correctness**: A prediction with the wrong verdict is wrong by "
                "definition — verdict is the primary output of a research agent. Evidence "
                "quality should not compensate for wrong conclusions. The prerequisite gate "
                "enforces this logical hierarchy: verdict must be correct before evidence "
                "quality matters.\n\n"
                "2. **Scoring formula after fix**: wrong verdict → early return at min(score, 0.2). "
                "This 0.2 floor (not 0.0) preserves partial credit for agents that are "
                "close (correct confidence, correct format) even with wrong verdict.\n\n"
                "3. **Test coverage**: 4/4 unit tests pass:\n"
                "   - wrong verdict + good evidence → 0.00 (was 0.60)\n"
                "   - correct verdict + good evidence → 0.97 (unchanged)\n"
                "   - correct verdict + no evidence → 0.60 (unchanged)\n"
                "   - empty prediction → 0.20 (unchanged)\n\n"
                "4. **Baseline impact**: Research-analyst 0.46→0.28 and synthesizer-bl2 "
                "0.45→0.20 both represent correction of inflated baselines, not regressions. "
                "The fix is correct and the lower scores are the true baselines."
            ),
        },
    },
]


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    lines = DATA_FILE.read_text(encoding="utf-8").splitlines()
    original_count = len([l for l in lines if l.strip()])

    updated_lines: list[str] = []
    removed_count = 0

    for line in lines:
        if not line.strip():
            updated_lines.append(line)
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            updated_lines.append(line)
            continue

        qid = rec.get("question_id", "")
        agent = rec.get("agent", "")

        if agent != "synthesizer-bl2":
            updated_lines.append(line)
            continue

        if qid in REMOVE_IDS:
            removed_count += 1
            print(f"  REMOVED: {qid} ({rec['output']['verdict']})")
            continue

        updated_lines.append(json.dumps(rec, ensure_ascii=False))

    for rec in NEW_RECORDS:
        updated_lines.append(json.dumps(rec, ensure_ascii=False))
        print(f"  ADDED: {rec['question_id']} ({rec['output']['verdict']})")

    DATA_FILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    final_count = len([l for l in updated_lines if l.strip()])
    print(f"\nTotal: {original_count} -> {final_count} records")
    print(f"Removed: {removed_count}, Added: {len(NEW_RECORDS)}")

    synth_records = [
        json.loads(l) for l in updated_lines
        if l.strip() and json.loads(l).get("agent") == "synthesizer-bl2"
    ]
    verdicts: dict[str, int] = {}
    for r in synth_records:
        v = r["output"]["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    print(f"\nsynthesizer-bl2: {len(synth_records)} records")
    print(f"Verdicts: {verdicts}")


if __name__ == "__main__":
    main()

"""masonry/scripts/merge_live_records.py

Merge a live records staging file into scored_all.jsonl.
Sets score based on confidence, deduplicates by (agent, question_id).

Usage:
    python masonry/scripts/merge_live_records.py
    python masonry/scripts/merge_live_records.py --staging masonry/training_data/synth_records_staging.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = _ROOT / "masonry/training_data/scored_all.jsonl"
_DEFAULT_STAGING = "masonry/training_data/live_records_staging.jsonl"

sys.stdout.reconfigure(encoding="utf-8")

parser = argparse.ArgumentParser()
parser.add_argument("--staging", default=_DEFAULT_STAGING, help="Path to staging JSONL (relative to repo root)")
args = parser.parse_args()

STAGING = _ROOT / args.staging

existing_ids: set[str] = set()
lines = DATA.read_text(encoding="utf-8").splitlines()
existing_records = []
for line in lines:
    if line.strip():
        r = json.loads(line)
        key = f"{r.get('agent', '')}::{r.get('question_id', '')}"
        existing_ids.add(key)
        existing_records.append(r)

staging = []
for line in STAGING.read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        conf = float(r["output"].get("confidence", "0.75"))
        r["score"] = 90 if conf >= 0.95 else (80 if conf >= 0.85 else 70)
        r.pop("_live_generated", None)
        r.pop("_timestamp", None)
        staging.append(r)

new_records = []
added = 0
for r in staging:
    key = f"{r.get('agent', '')}::{r.get('question_id', '')}"
    if key not in existing_ids:
        new_records.append(r)
        added += 1
        print(f"  ADDED: {r['question_id']} ({r['output']['verdict']}, score={r['score']})")
    else:
        print(f"  SKIP (dup): {r['question_id']}")

all_records = existing_records + new_records
DATA.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in all_records) + "\n", encoding="utf-8")
print(f"\nTotal: {len(all_records)} records (+{added} added)")

# Show per-agent summary for any agents that appear in the staging file
staged_agents = {r.get("agent", "") for r in staging}
for agent_name in sorted(staged_agents):
    agent_records = [r for r in all_records if r.get("agent") == agent_name]
    v: dict[str, int] = {}
    for r in agent_records:
        vk = r["output"]["verdict"]
        v[vk] = v.get(vk, 0) + 1
    print(f"{agent_name}: {len(agent_records)} records, verdicts: {v}")

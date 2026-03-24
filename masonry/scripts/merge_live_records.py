"""masonry/scripts/merge_live_records.py

Merge live_records_staging.jsonl into scored_all.jsonl.
Sets score based on confidence, deduplicates by question_id.
"""
import json, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = _ROOT / "masonry/training_data/scored_all.jsonl"
STAGING = _ROOT / "masonry/training_data/live_records_staging.jsonl"

sys.stdout.reconfigure(encoding="utf-8")

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

ra = [r for r in all_records if r.get("agent") == "research-analyst"]

v: dict[str, int] = {}
for r in ra:
    vk = r["output"]["verdict"]
    v[vk] = v.get(vk, 0) + 1
print(f"research-analyst: {len(ra)} records, verdicts: {v}")

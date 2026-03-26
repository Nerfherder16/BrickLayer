# BrickLayer — Batch 2 Handoff for Claude Code

**Read this entire document before touching any file.**
**All items from MASTER_HANDOFF.md are assumed complete before starting here.**
**Work through sections in priority order — each builds on the previous.**

---

## Context: What Was Just Completed

The following are done and working:
- Mortar simplified to binary campaign/dev dispatch
- Rough-in agent created and registered
- Intra-campaign Recall feedback loop (Trowel pre-fetches prior findings)
- `recall_degraded` flag writing in recall_bridge.py
- Importance-weighted retrieval in the Recall API
- Full training system setup (Bricklayer training repo, bridge files, smoke tests)

What's missing is the **connective tissue** — the feedback paths that make the three
systems (BrickLayer, Recall, training) aware of each other's state, and the validation
infrastructure that tells you whether training is actually working.

---

## Priority Order

```
1. masonry-system-status.js       ← orientation at every session start (low effort, high value)
2. training_ready.flag watcher    ← closes the Layer 2 → Layer 3 gap (low effort, high value)
3. Rough-in state file            ← production stability (medium effort, high value)
4. Agent scores → Recall          ← connects Layer 1 to routing (medium effort, high value)
5. Held-out eval + comparison     ← training validation gate (medium effort, essential)
6. Recall → skill-forge bridge    ← institutional memory discovery (medium effort)
7. Recall enrichment decay        ← long-term hygiene (lower urgency)
```

---

## Task 1 — System Status Hook

**What:** A new Stop hook that writes a unified status snapshot to `.mas/system-status.json`
at the end of every session. Mortar reads this at session start and surfaces the relevant
parts in its opening context.

**Why:** Right now you walk into every session not knowing where things stand across the
three systems. Campaign progress, Recall health, training trace count, agent optimization
age — all of this is knowable but scattered across multiple files and never surfaced together.

**Files to read first:**
- `masonry/src/hooks/masonry-session-end.js` — understand existing Stop hook pattern
- `masonry/src/hooks/hooks.json` — understand registration format
- `masonry-state.json` / `.mas/` directory — understand existing state schema
- `template/.claude/agents/mortar.md` — understand how Mortar currently reads session context

---

**Create:** `masonry/src/hooks/masonry-system-status.js`

```javascript
#!/usr/bin/env node
/**
 * masonry-system-status.js
 * Stop hook — writes unified system status to .mas/system-status.json.
 * Mortar reads this at session start to orient itself.
 * Never blocks session end — all failures are silent.
 */

const fs = require("fs");
const path = require("path");
const { execSync, spawnSync } = require("child_process");

const BL_ROOT = process.env.CLAUDE_PLUGIN_ROOT || process.cwd();
const STATUS_FILE = path.join(BL_ROOT, ".mas", "system-status.json");
const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB;
const MASONRY_STATE = path.join(BL_ROOT, ".mas", "masonry-state.json");

function safeRead(filepath) {
  try { return JSON.parse(fs.readFileSync(filepath, "utf8")); }
  catch { return {}; }
}

function getCampaignStatus() {
  try {
    const state = safeRead(MASONRY_STATE);
    return {
      active: state.campaign_active || false,
      project: state.current_project || null,
      wave: state.current_wave || null,
      pending: state.questions_pending || null,
      complete: state.questions_complete || null,
    };
  } catch { return {}; }
}

function getRecallStatus() {
  try {
    const state = safeRead(MASONRY_STATE);
    return {
      degraded: state.recall_degraded || false,
      host: "100.70.195.84:8200",
    };
  } catch { return {}; }
}

function getTrainingStatus() {
  if (!TRAINING_DB) return { configured: false };
  try {
    const result = spawnSync("python3", [
      "-c",
      [
        "import sqlite3, json",
        `db = sqlite3.connect('${TRAINING_DB}')`,
        "total = db.execute('SELECT COUNT(*) FROM traces').fetchone()[0]",
        "eligible = db.execute('SELECT COUNT(*) FROM traces WHERE sft_eligible=1').fetchone()[0]",
        "print(json.dumps({'total': total, 'eligible': eligible}))",
      ].join(";"),
    ], { encoding: "utf8", timeout: 5000 });
    if (result.status === 0) {
      const data = JSON.parse(result.stdout.trim());
      return {
        configured: true,
        total_traces: data.total,
        eligible_traces: data.eligible,
        threshold: 500,
        ready: data.eligible >= 500,
      };
    }
  } catch {}
  return { configured: true, error: "could not query db" };
}

function getAgentStatus() {
  try {
    const registryPath = path.join(BL_ROOT, "masonry", "agent_registry.yml");
    if (!fs.existsSync(registryPath)) return {};
    // Find agents with last_score below 0.6 — these need attention
    const content = fs.readFileSync(registryPath, "utf8");
    const lowScoreMatches = [...content.matchAll(/name:\s*(\S+)[\s\S]*?last_score:\s*([\d.]+)/g)];
    const belowThreshold = lowScoreMatches
      .filter(m => parseFloat(m[2]) < 0.6)
      .map(m => ({ agent: m[1], score: parseFloat(m[2]) }));
    // Find last optimization timestamp from any snapshot
    const snapshotDir = path.join(BL_ROOT, "masonry", "agent_snapshots");
    let lastOptimized = null;
    if (fs.existsSync(snapshotDir)) {
      const timestamps = fs.readdirSync(snapshotDir)
        .map(agent => {
          const evalFile = path.join(snapshotDir, agent, "eval_latest.json");
          try {
            const data = JSON.parse(fs.readFileSync(evalFile, "utf8"));
            return data.timestamp || null;
          } catch { return null; }
        })
        .filter(Boolean)
        .sort()
        .reverse();
      lastOptimized = timestamps[0] || null;
    }
    return { below_threshold: belowThreshold, last_optimized: lastOptimized };
  } catch { return {}; }
}

function getRoughInStatus() {
  try {
    const stateFile = path.join(BL_ROOT, ".autopilot", "rough-in-state.json");
    if (!fs.existsSync(stateFile)) return { active_task: null };
    const state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    const pending = (state.tasks || []).filter(t => t.status !== "complete");
    return {
      active_task: state.task_id || null,
      pending_steps: pending.length,
      last_updated: state.last_updated || null,
    };
  } catch { return { active_task: null }; }
}

// Build status object
const status = {
  generated_at: new Date().toISOString(),
  campaign: getCampaignStatus(),
  recall: getRecallStatus(),
  training: getTrainingStatus(),
  agents: getAgentStatus(),
  rough_in: getRoughInStatus(),
};

// Write
try {
  const dir = path.dirname(STATUS_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2), "utf8");
  process.stdout.write("[masonry-system-status] status written\n");
} catch (e) {
  process.stderr.write(`[masonry-system-status] write failed: ${e.message}\n`);
}

process.exit(0);
```

**Register in `masonry/src/hooks/hooks.json`** — add to the Stop event block alongside
the other Stop hooks:

```json
{
  "matcher": {"type": "Stop"},
  "hooks": [
    {
      "type": "command",
      "command": "node ${CLAUDE_PLUGIN_ROOT}/masonry/src/hooks/masonry-system-status.js"
    }
  ]
}
```

**Update Mortar's prompt** — add a session-start step:

```
SESSION START:
1. Read .mas/system-status.json if it exists
2. Surface any of the following that are true:
   - training.ready = true → "Training threshold reached ({eligible} traces). 
     Run: bricklayer run-round --round-id N"
   - recall.degraded = true → "Recall is degraded. Check 100.70.195.84:8200"
   - agents.below_threshold non-empty → "Agents below 0.6 score: {list}. 
     Run: python masonry/scripts/improve_agent.py {name}"
   - rough_in.active_task non-null → "Rough-in has incomplete task {id}. 
     Resume or clear .autopilot/rough-in-state.json"
3. If campaign.active = true, confirm with Trowel before accepting new non-campaign work
```

**Verify:**
```bash
node --check masonry/src/hooks/masonry-system-status.js
# Trigger manually:
BRICKLAYER_TRAINING_DB=~/.bricklayer/training.db \
  node masonry/src/hooks/masonry-system-status.js
cat .mas/system-status.json | python3 -m json.tool
```

---

## Task 2 — Training Ready Flag Watcher

**What:** Extend `masonry-score-trigger.js` (already fires at session end after scoring)
to check the training trace count and write `.mas/training_ready.flag` when the threshold
is reached. The system status hook from Task 1 will surface this via Mortar.

**Why:** The 500-trace threshold for Layer 3 (DPO fine-tuning) is currently invisible.
You have to manually query the DB to know when it's reached. This makes it automatic.

**Files to read first:**
- `masonry/src/hooks/masonry-score-trigger.js` — full current implementation
- `.mas/system-status.json` (after Task 1) — understand where `training.ready` is written

**What to add to `masonry-score-trigger.js`** — append after the existing scoring logic:

```javascript
// ── Training readiness check ─────────────────────────────────────────────────

const TRAINING_DB = process.env.BRICKLAYER_TRAINING_DB;
const TRAINING_THRESHOLD = parseInt(process.env.TRAINING_THRESHOLD || "500", 10);
const TRAINING_FLAG = path.join(BL_ROOT, ".mas", "training_ready.flag");

if (TRAINING_DB) {
  const check = spawnSync("python3", [
    "-c",
    [
      "import sqlite3",
      `db = sqlite3.connect('${TRAINING_DB}')`,
      "n = db.execute('SELECT COUNT(*) FROM traces WHERE sft_eligible=1').fetchone()[0]",
      "print(n)",
    ].join(";"),
  ], { encoding: "utf8", timeout: 5000 });

  if (check.status === 0) {
    const eligible = parseInt(check.stdout.trim(), 10);
    if (eligible >= TRAINING_THRESHOLD) {
      fs.writeFileSync(TRAINING_FLAG, String(eligible), "utf8");
      process.stdout.write(
        `[masonry-score-trigger] training ready: ${eligible} eligible traces ` +
        `(threshold: ${TRAINING_THRESHOLD})\n`
      );
    } else {
      // Remove stale flag if count dropped below threshold (e.g. DB reset)
      if (fs.existsSync(TRAINING_FLAG)) fs.unlinkSync(TRAINING_FLAG);
      process.stdout.write(
        `[masonry-score-trigger] training progress: ${eligible}/${TRAINING_THRESHOLD} traces\n`
      );
    }
  }
}
```

**Verify:**
```bash
node --check masonry/src/hooks/masonry-score-trigger.js

# Simulate threshold reached:
BRICKLAYER_TRAINING_DB=~/.bricklayer/training.db \
TRAINING_THRESHOLD=1 \
  node masonry/src/hooks/masonry-score-trigger.js

ls -la .mas/training_ready.flag   # should exist
cat .mas/training_ready.flag      # should show trace count
```

---

## Task 3 — Rough-in State File and Resumability

**What:** Add a state file to Rough-in so interrupted dev tasks can resume from the
last incomplete step rather than restarting from scratch.

**Why:** Trowel survives context compaction. Rough-in currently doesn't. A long dev task
(spec → developer → test-writer → code-reviewer → git-nerd) that gets interrupted at
step 3 will either restart expensively or fail silently.

**Files to read first:**
- `template/.claude/agents/rough-in.md` — the agent you just created
- `template/.claude/agents/trowel.md` — specifically how it reads questions.md for resumption
- `.autopilot/` directory — understand existing autopilot state structure

**Create state schema:** `.autopilot/rough-in-state.json` (written by Rough-in, never
by humans):

```json
{
  "task_id": "uuid-v4",
  "description": "one-line summary of the task",
  "spec_path": ".autopilot/spec.md",
  "tasks": [
    {
      "id": "t1",
      "agent": "spec-writer",
      "description": "write spec from brief",
      "status": "complete",
      "completed_at": "2026-03-26T10:00:00Z"
    },
    {
      "id": "t2",
      "agent": "developer",
      "description": "implement feature X",
      "status": "in_progress",
      "started_at": "2026-03-26T10:05:00Z"
    },
    {
      "id": "t3",
      "agent": "test-writer",
      "description": "write tests for feature X",
      "status": "pending"
    },
    {
      "id": "t4",
      "agent": "code-reviewer",
      "description": "review implementation",
      "status": "pending"
    },
    {
      "id": "t5",
      "agent": "git-nerd",
      "description": "commit changes",
      "status": "pending"
    }
  ],
  "started_at": "2026-03-26T09:58:00Z",
  "last_updated": "2026-03-26T10:05:00Z",
  "retry_count": 0
}
```

**Update `rough-in.md`** to add these two behaviours:

**On task start:**
```
TASK START:
1. Generate a task_id (uuid)
2. Write rough-in-state.json with all planned steps at status "pending"
3. Mark each step "in_progress" as you dispatch it, "complete" when it reports success
4. Update last_updated on every status change
5. On any agent failure: increment retry_count, re-dispatch same step (max 3 retries)
6. On retry_count >= 3: set step status "failed", write error to state, surface to user
```

**On session start (resumption):**
```
SESSION RESUME CHECK:
1. Check if .autopilot/rough-in-state.json exists
2. If it does: read it and find the first task where status is "in_progress" or "pending"
3. Resume from that task — do not re-run completed tasks
4. If all tasks are complete but git-nerd step is missing: run git-nerd then clean up state file
5. If state file is stale (last_updated > 24h ago): surface to user, ask to resume or clear
```

**Add to Mortar's session-start check** (alongside Task 1's status surface):
```
If rough_in.active_task is not null in system-status.json:
  "Rough-in has incomplete task from last session: {description}
   Resume with: Act as rough-in agent. Resume from rough-in-state.json.
   Clear with: rm .autopilot/rough-in-state.json"
```

**Verify:**
- Start a dev task, interrupt it mid-way (kill the session)
- Start a new session
- Confirm Mortar surfaces the incomplete task
- Confirm Rough-in resumes from the interrupted step, not from the beginning

---

## Task 4 — Agent Scores into Recall

**What:** After each agent optimization cycle in `improve_agent.py`, write the result
to Recall so Trowel can query agent performance history when choosing which specialist
to dispatch.

**Why:** Layer 1 (prompt optimization) runs independently of the routing system. Agent
performance history lives in `agent_snapshots/` and `agent_registry.yml` but is never
queryable by Trowel. This connects them.

**Files to read first:**
- `masonry/scripts/improve_agent.py` — find where the new score is computed and
  the "keep or revert" decision is made
- `bl/recall_bridge.py` — `store_finding()` signature and behavior
- `template/.claude/agents/trowel.md` — where agent selection happens

**What to add to `improve_agent.py`** — after the "keep if improved" decision block:

```python
# After deciding to keep or revert the new instructions:
try:
    from bl.recall_bridge import store_finding
    verdict = "IMPROVEMENT" if new_score > baseline_score else "REGRESSION"
    summary = (
        f"{agent_name}: {baseline_score:.3f} → {new_score:.3f} "
        f"({'kept' if new_score > baseline_score else 'reverted'})"
    )
    store_finding(
        question_id=f"agent_eval_{agent_name}_{int(time.time())}",
        verdict=verdict,
        summary=summary,
        project="bricklayer-meta",
        tags=["bricklayer", f"agent:{agent_name}", "agent-eval", f"tier:{agent_tier}"],
        domain="agent-performance",
        importance=0.7 if verdict == "IMPROVEMENT" else 0.5,
    )
except Exception:
    pass  # never block optimization on Recall write
```

Note: `store_finding()` may not currently accept an `importance` parameter. Check the
signature in `recall_bridge.py` and add it if missing — it should pass through to the
`/memory/store` endpoint payload.

**What to add to Trowel's prompt** — in the agent selection section, before dispatching
a question to a specialist:

```
AGENT SELECTION:
Before dispatching to {specialist}, optionally query:
  get_campaign_context(project_name="bricklayer-meta", current_qid="{qid}")
  filtered by tags: ["agent:{specialist_name}", "agent-eval"]

If results show recent REGRESSION verdict for this agent:
  - Note it in the dispatch context
  - Consider dispatching to backup agent if one exists for this mode
  - Never block dispatch on missing Recall data
```

**Verify:**
```bash
# Run a single optimization cycle
cd ~/BrickLayer
python masonry/scripts/improve_agent.py research-analyst --dry-run

# Check Recall for the write (query via bridge)
python3 - << 'EOF'
import sys; sys.path.insert(0, ".")
from bl.recall_bridge import search_prior_findings
results = search_prior_findings(
    query="research-analyst agent eval performance",
    domain="agent-performance",
    limit=3
)
for r in results:
    print(r.get("summary"), r.get("tags"))
EOF
```

---

## Task 5 — Held-Out Eval Set and Training Comparison

**What:** Create a held-out eval task set that is never used for training collection,
and add a CLI command that compares model performance before and after a training round.

**Why:** Without this you cannot know if fine-tuning is helping or hurting. The smoke test
(does it return an answer) is not sufficient. This is the validation gate for promoting
a new adapter to production use in Ollama.

**Files to read first:**
- `configs/tasks/` — understand current task JSON format
- `bricklayer/tasks/bank.py` — understand TaskBank loading
- `bricklayer/training/eval.py` — understand EvalRunner and pass@k metrics
- `bricklayer/cli.py` — understand how to add a new CLI command

---

**Step 5a — Create eval task directory:**

```bash
mkdir -p ~/bricklayer/configs/eval_tasks/
```

Create `configs/eval_tasks/code.json`, `configs/eval_tasks/math.json`,
`configs/eval_tasks/tool_use.json`, `configs/eval_tasks/reasoning.json`.

Each file follows the same JSON format as `configs/tasks/` but contains **different tasks**
that have never appeared in the training task bank. Target: 20 tasks per domain.

If you need to generate them, use the Claude API (pattern from the planned
`scripts/generate_tasks.py` in the known gaps):

```python
# Rough pattern — create scripts/generate_eval_tasks.py
import anthropic, json
from pathlib import Path

client = anthropic.Anthropic()
domains = {
    "code": 20,
    "math": 20,
    "tool_use": 20,
    "reasoning": 20,
}

for domain, count in domains.items():
    # Generate tasks with explicit instruction that they must differ
    # from any tasks in configs/tasks/{domain}.json
    ...
    # Validate with appropriate verifier before saving
    ...
    Path(f"configs/eval_tasks/{domain}.json").write_text(json.dumps(tasks, indent=2))
```

**Step 5b — Add eval comparison CLI command:**

In `bricklayer/cli.py`, add a new command `eval-compare`:

```python
@cli.command("eval-compare")
@click.option("--baseline-model", default=None,
              help="Ollama model for baseline (default: AGENT_MODEL from .env)")
@click.option("--candidate-model", required=True,
              help="Ollama model to evaluate (e.g. bricklayer-sft-r1)")
@click.option("--tasks-dir", default="configs/eval_tasks/",
              help="Held-out eval task directory")
@click.option("--n-samples", default=5,
              help="Samples per task for pass@k estimation")
@click.option("--output", default=None,
              help="Output JSON path (default: data/eval_compare_{timestamp}.json)")
def eval_compare(baseline_model, candidate_model, tasks_dir, n_samples, output):
    """
    Compare two Ollama models on held-out eval tasks.
    Writes pass@1 and pass@5 for each domain and overall.
    Exits with code 1 if candidate does not improve on baseline.
    """
    ...
```

The comparison output should include:
```json
{
  "baseline_model": "qwen2.5:7b-instruct",
  "candidate_model": "bricklayer-sft-r1",
  "overall": {
    "baseline_pass_at_1": 0.51,
    "candidate_pass_at_1": 0.63,
    "delta": "+0.12",
    "verdict": "IMPROVEMENT"
  },
  "by_domain": {
    "code":      {"baseline": 0.48, "candidate": 0.61, "delta": "+0.13"},
    "math":      {"baseline": 0.55, "candidate": 0.67, "delta": "+0.12"},
    "tool_use":  {"baseline": 0.50, "candidate": 0.59, "delta": "+0.09"},
    "reasoning": {"baseline": 0.52, "candidate": 0.64, "delta": "+0.12"}
  },
  "recommendation": "PROMOTE"
}
```

**Step 5c — Add promotion gate to adapter loading:**

In `scripts/load_adapter.sh` (from the known gaps task), before running `ollama create`,
add:

```bash
# Run eval comparison — exit if candidate doesn't beat baseline
python3 -m bricklayer eval-compare \
  --candidate-model bricklayer-sft-r1 \
  --output data/round_${ROUND_ID}/eval_compare.json

VERDICT=$(python3 -c "
import json
d = json.load(open('data/round_${ROUND_ID}/eval_compare.json'))
print(d['recommendation'])
")

if [ "$VERDICT" != "PROMOTE" ]; then
  echo "Candidate did not beat baseline. Not promoting to Ollama."
  exit 1
fi

# Proceed with ollama create only if PROMOTE
```

**Verify:**
```bash
cd ~/bricklayer && source .venv/bin/activate

# Run the comparison (requires both models in Ollama)
bricklayer eval-compare \
  --baseline-model qwen2.5:7b-instruct \
  --candidate-model bricklayer-sft-r1 \
  --tasks-dir configs/eval_tasks/ \
  --n-samples 3

# Check output
cat data/eval_compare_*.json | python3 -m json.tool
```

---

## Task 6 — Recall to Skill-Forge Bridge

**What:** A script that queries Recall for high-frequency high-importance patterns and
surfaces them as skill candidates. Skill creation still goes through skill-forge — this
is just the discovery pipeline.

**Why:** Skill-forge currently operates on what you manually tell it. Recall contains
patterns that have appeared repeatedly across campaigns but will never surface as skills
unless someone notices them. This automates the discovery step.

**Files to read first:**
- `bl/recall_bridge.py` — available query functions
- `~/.claude/skills/` — understand skill format (how skills are structured)
- `masonry/scripts/improve_agent.py` — understand skill-forge invocation pattern
- `template/.claude/agents/skill-forge.md` — understand what skill-forge expects as input

**Create:** `masonry/scripts/discover_skill_candidates.py`

```python
"""
discover_skill_candidates.py

Queries Recall for high-frequency, high-importance patterns that may warrant
formalization as skills. Outputs candidates to .mas/skill_candidates.json.
Skill creation still goes through skill-forge — this is discovery only.

Usage:
    python masonry/scripts/discover_skill_candidates.py
    python masonry/scripts/discover_skill_candidates.py --min-importance 0.75 --min-count 3
"""
import sys, json, argparse
from pathlib import Path
from collections import Counter

# Add BL root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from bl.recall_bridge import search_prior_findings

CANDIDATE_FILE = Path(".mas/skill_candidates.json")

def discover_candidates(min_importance: float = 0.7, min_count: int = 3) -> list[dict]:
    """
    Find patterns in Recall that appear >= min_count times with >= min_importance.
    Returns ranked list of candidate skill descriptions.
    """
    candidates = []

    # Query for high-importance successful patterns across domains
    for domain in ["autoresearch", "agent-performance", "bricklayer-trace"]:
        results = search_prior_findings(
            query="successful pattern high confidence repeated",
            domain=domain,
            limit=50,
        )
        high_importance = [
            r for r in results
            if r.get("importance", 0) >= min_importance
            and r.get("verdict") not in ("FAILURE", "REGRESSION", "INCONCLUSIVE")
        ]
        candidates.extend(high_importance)

    # Cluster by summary similarity (simple word-overlap for now)
    # Group findings whose summaries share 3+ significant words
    clusters = []
    used = set()
    for i, c in enumerate(candidates):
        if i in used:
            continue
        words_i = set(c.get("summary", "").lower().split())
        cluster = [c]
        for j, d in enumerate(candidates[i+1:], i+1):
            words_j = set(d.get("summary", "").lower().split())
            overlap = len(words_i & words_j - {"the", "a", "is", "in", "of", "to", "and"})
            if overlap >= 3:
                cluster.append(d)
                used.add(j)
        if len(cluster) >= min_count:
            clusters.append(cluster)

    # Format as skill candidates
    skill_candidates = []
    for cluster in sorted(clusters, key=len, reverse=True):
        skill_candidates.append({
            "frequency": len(cluster),
            "avg_importance": round(
                sum(r.get("importance", 0.5) for r in cluster) / len(cluster), 3
            ),
            "representative_summary": cluster[0].get("summary", ""),
            "sample_verdicts": list({r.get("verdict") for r in cluster[:5]}),
            "suggested_skill_name": None,  # skill-forge names it
            "source_qids": [r.get("question_id") for r in cluster[:5]],
        })

    return skill_candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-importance", type=float, default=0.7)
    parser.add_argument("--min-count", type=int, default=3)
    args = parser.parse_args()

    candidates = discover_candidates(args.min_importance, args.min_count)

    CANDIDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_FILE.write_text(json.dumps(candidates, indent=2))

    print(f"[discover_skill_candidates] {len(candidates)} candidates → {CANDIDATE_FILE}")
    for c in candidates[:5]:
        print(f"  freq={c['frequency']} importance={c['avg_importance']:.2f} "
              f"summary={c['representative_summary'][:80]}")
```

**Wire into session-end:** Add to `masonry-session-end.js` (after the session summary
is written), rate-limited to once per 24h:

```javascript
// Rate-limited skill candidate discovery
const CANDIDATES_LOCK = path.join(BL_ROOT, ".mas", "skill_discovery_last_run");
const DISCOVER_SCRIPT = path.join(BL_ROOT, "masonry", "scripts", "discover_skill_candidates.py");

function shouldRunDiscovery() {
  if (!fs.existsSync(CANDIDATES_LOCK)) return true;
  try {
    const last = parseInt(fs.readFileSync(CANDIDATES_LOCK, "utf8").trim(), 10);
    return (Date.now() - last) > 24 * 60 * 60 * 1000;
  } catch { return true; }
}

if (fs.existsSync(DISCOVER_SCRIPT) && shouldRunDiscovery()) {
  spawnSync("python3", [DISCOVER_SCRIPT], {
    cwd: BL_ROOT, encoding: "utf8", timeout: 30_000,
    env: { ...process.env }
  });
  fs.writeFileSync(CANDIDATES_LOCK, String(Date.now()), "utf8");
}
```

**Add to Mortar's session-start check:**
```
If .mas/skill_candidates.json exists and has entries:
  "Recall has identified {N} skill candidates from recent campaign patterns.
   Review: cat .mas/skill_candidates.json
   Create skills: Act as skill-forge agent."
```

**Verify:**
```bash
python3 masonry/scripts/discover_skill_candidates.py --min-count 1
cat .mas/skill_candidates.json | python3 -m json.tool
```

---

## Task 7 — Recall Enrichment Decay (Lower Urgency)

**What:** A lightweight mechanism to decay the importance of Recall memories that
get injected as context but turn out to be wrong — detected by comparing injected
verdicts against the session's actual findings.

**Why:** As Recall grows, semantic false positives increase. A memory that predicted
HEALTHY but the session found FAILURE is actively harmful context. Decaying its importance
over time prevents it from repeatedly polluting future prompts.

**Files to read first:**
- `masonry/src/hooks/masonry-recall.js` — the UserPromptSubmit hook that does enrichment
- `masonry/src/hooks/masonry-session-end.js` — the Stop hook that writes session summary
- `bl/recall_bridge.py` — look for or add an `update_importance()` function

**What to add to `bl/recall_bridge.py`:**

```python
def decay_conflicting_memories(
    injected_memory_ids: list[str],
    session_findings: list[dict],
    decay_factor: float = 0.8,
) -> int:
    """
    For each injected memory whose verdict conflicts with actual session findings,
    reduce its importance by decay_factor.
    Returns count of decayed memories.
    Never blocks — returns 0 on any failure.
    """
    if not injected_memory_ids or not session_findings:
        return 0

    actual_pass_verdicts = {
        f.get("verdict") for f in session_findings
        if f.get("verdict") in ("HEALTHY", "FIXED", "VALIDATED", "COMPLIANT")
    }
    actual_fail_verdicts = {
        f.get("verdict") for f in session_findings
        if f.get("verdict") in ("FAILURE", "NON_COMPLIANT", "REGRESSION")
    }

    decayed = 0
    for memory_id in injected_memory_ids:
        try:
            # Fetch the memory to check its verdict tag
            resp = httpx.get(
                f"{RECALL_HOST}/memory/{memory_id}",
                timeout=RECALL_TIMEOUT,
            )
            if resp.status_code != 200:
                continue
            memory = resp.json()
            tags = memory.get("tags", [])
            memory_verdict = next(
                (t.split(":")[1] for t in tags if t.startswith("verdict:")), None
            )
            if not memory_verdict:
                continue
            # Conflict: memory predicted pass but session found fail (or vice versa)
            conflict = (
                memory_verdict in ("HEALTHY", "VALIDATED") and actual_fail_verdicts
            ) or (
                memory_verdict in ("FAILURE", "REGRESSION") and actual_pass_verdicts
                and not actual_fail_verdicts
            )
            if conflict:
                new_importance = round(memory.get("importance", 0.5) * decay_factor, 3)
                httpx.patch(
                    f"{RECALL_HOST}/memory/{memory_id}",
                    json={"importance": new_importance},
                    timeout=RECALL_TIMEOUT,
                )
                decayed += 1
        except Exception:
            continue

    return decayed
```

**Wire into `masonry-session-end.js`:**

The session-end hook already writes a session summary. After that write, call
`decay_conflicting_memories()` using:
- The memory IDs that were injected at session start (store them in `.mas/session-injected-memories.json`
  from `masonry-recall.js` at UserPromptSubmit time)
- The verdicts from findings written during the session

Note: This requires `masonry-recall.js` to write the injected memory IDs somewhere
readable at session end. Add to `masonry-recall.js`:

```javascript
// After Recall returns enrichment results, persist the IDs:
const injectedIds = (recallResults || []).map(r => r.id).filter(Boolean);
if (injectedIds.length > 0) {
  fs.writeFileSync(
    path.join(BL_ROOT, ".mas", "session-injected-memories.json"),
    JSON.stringify(injectedIds),
    "utf8"
  );
}
```

**Verify:**
- Write a HEALTHY memory to Recall
- Run a session that produces a FAILURE verdict
- After session end, query Recall for that memory and confirm its importance decreased

---

## File Writing Rules (Repeat — Important)

1. `create_file` for every new file. No heredocs or shell redirects.
2. `view` tool before editing any existing file.
3. No multi-line f-strings with `\n` inside. Use `"\n".join([...])`.
4. No nested f-strings with mixed quotes. Extract key first.
5. `node --check` after every hook file change.
6. `python3 -m pytest tests/ -v` after any change to core bricklayer modules.
7. Do not rewrite files not listed in a task above.

---

## Success Checklist

- [ ] Task 1: `.mas/system-status.json` written at session end, all 5 fields populated
- [ ] Task 1: Mortar surfaces relevant flags at session start
- [ ] Task 2: `.mas/training_ready.flag` created when eligible traces >= 500
- [ ] Task 2: Progress line printed at each session end showing current count
- [ ] Task 3: `.autopilot/rough-in-state.json` written on task start
- [ ] Task 3: Interrupted task resumes from correct step on next session
- [ ] Task 4: Recall contains `agent-performance` domain entries after optimize run
- [ ] Task 4: Trowel references recent REGRESSION verdicts during agent selection
- [ ] Task 5: `configs/eval_tasks/` has 20 tasks per domain, none overlapping training set
- [ ] Task 5: `bricklayer eval-compare` runs and produces comparison JSON
- [ ] Task 5: `load_adapter.sh` gates on PROMOTE verdict before `ollama create`
- [ ] Task 6: `discover_skill_candidates.py` runs and writes `.mas/skill_candidates.json`
- [ ] Task 6: Mortar surfaces candidate count at session start
- [ ] Task 7: Memory importance decays after conflicting session findings
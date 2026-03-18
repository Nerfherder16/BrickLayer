# Spec: Phase 6 — Campaign Quality Intelligence

## Goal

Make BrickLayer's research loop self-aware about output quality, not just volume. Six coordinated
improvements: numeric confidence on every finding, LLM-as-judge quality scoring via peer-reviewer,
a feedback sharpener that narrows PENDING questions based on INCONCLUSIVE findings, shared campaign
context injected into every agent spawn, time-series performance tracking per agent, and a canonical
tool manifest for the fleet. End result: verdicts are trustworthy, campaigns self-correct, and
underperforming agents are caught before they waste waves.

## Architecture

```
  findings.py          — adds confidence_float + needs_human to every .md finding
       ↓
  agent_db.py          — records runs[] time-series per agent
       ↓
  question_weights.py  — quality_score factor in INCONCLUSIVE weight bump
       ↓
  question_sharpener.py — narrows PENDING questions from INCONCLUSIVE signals
       ↓
  agent .md patches     — peer-reviewer emits quality_score; mortar re-queues low-quality INCONCLUSIVEs;
                          synthesizer calls sharpener; auditor detects trends; forge checks manifest
       ↓
  dashboard backend     — exposes confidence + sharpened fields via API
       ↓
  dashboard frontend    — confidence badge/filter, sharpened question badge
  Kiln                  — verdict sparkline in AgentBriefModal
```

## Tasks

### Task 1 — bl/findings.py: numeric confidence + needs_human in frontmatter
**Parallel: yes (independent of T2–T4)**

The existing `classify_confidence()` returns `"high"|"medium"|"low"|"uncertain"`. The numeric value
is never written to the finding file. This task maps it to float and writes it.

Add this **above the `## Summary` section** in the finding markdown template inside `write_finding()`:

```
**Confidence**: {confidence_float}
**Needs Human**: {needs_human}
```

Mapping (add as module-level constant `_CONFIDENCE_FLOAT`):
```python
_CONFIDENCE_FLOAT = {"high": 0.9, "medium": 0.6, "low": 0.3, "uncertain": 0.1}
```

Logic to add inside `write_finding()` (after C-30 constraint block, before building `content`):
```python
conf_str = result.get("confidence", "uncertain")
confidence_float = _CONFIDENCE_FLOAT.get(conf_str, 0.1)
needs_human = confidence_float < 0.35
```

**File**: `bl/findings.py`

**Test** (`tests/test_findings_confidence.py`):
- `write_finding()` with `confidence="high"` → file contains `**Confidence**: 0.9` and `**Needs Human**: False`
- `write_finding()` with `confidence="uncertain"` → file contains `**Confidence**: 0.1` and `**Needs Human**: True`
- `write_finding()` with `confidence="low"` → `**Needs Human**: True` (0.3 < 0.35)
- `write_finding()` with `confidence="medium"` → `**Needs Human**: False` (0.6 >= 0.35)
- C-30 path: `code_audit` question with `confidence="high"` → confidence capped to `"medium"` → `**Confidence**: 0.6`

---

### Task 2 — bl/agent_db.py: runs[] time-series
**Parallel: yes (independent of T1, T3, T4)**

Extend `record_run()` signature and storage to track per-run history:

```python
def record_run(
    project_root: Path | str,
    agent_name: str,
    verdict: str,
    duration_ms: int = 0,
    quality_score: float | None = None,
) -> float:
```

Append to `runs[]` list in the agent's JSON entry:
```json
{"timestamp": "ISO-8601", "verdict": "FAILURE", "duration_ms": 123, "quality_score": 0.7}
```

Backward compat: agents already in agent_db.json without `runs` key -> default to `[]`.
Cap `runs[]` at 100 entries (drop oldest when over limit).

Add new function:
```python
def get_trend(
    project_root: Path | str,
    agent_name: str,
    window: int = 5,
) -> dict:
    """
    Returns:
      {
        "score_recent": float,   # accuracy over last `window` runs
        "score_prior": float,    # accuracy over prior `window` runs (or None if < 2*window total)
        "trending": "up" | "down" | "stable" | "insufficient_data",
        "recent_runs": int,
      }
    Accuracy = fraction of SUCCESS verdicts in the window.
    "up" if recent > prior + 0.1, "down" if recent < prior - 0.1, else "stable".
    """
```

**File**: `bl/agent_db.py`

**Test** (`tests/test_agent_db_timeseries.py`):
- `record_run()` with `duration_ms=150, quality_score=0.8` -> run appears in `runs[]`
- `record_run()` on existing agent without `runs` key -> backward compat, no KeyError
- `record_run()` 101 times -> `runs[]` length == 100 (oldest dropped)
- `get_trend()` with 6 runs (3 SUCCESS + 3 FAILURE, interleaved) -> returns dict with all keys
- `get_trend()` with < 5 runs -> `trending == "insufficient_data"`
- `get_trend()` 10 runs: last 5 all SUCCESS, prior 5 all FAILURE -> `trending == "up"`

---

### Task 3 — bl/question_weights.py: quality_score in weight formula
**Parallel: yes (independent of T1, T2, T4)**

Extend `record_result()`:
```python
def record_result(
    project_dir: Path | str,
    question_id: str,
    verdict: str,
    quality_score: float | None = None,
) -> QuestionWeight:
```

Add to weight computation: if `verdict == "INCONCLUSIVE"` and
`quality_score is not None` and `quality_score < 0.4` -> add `+0.3` to weight after base computation
(signals: this INCONCLUSIVE had low quality -> worth retrying with sharper scope, not just pruning).

Add field to `QuestionWeight` dataclass:
```python
last_quality_score: float | None = None   # most recent peer-reviewer quality_score
```

Persist `last_quality_score` to `.bl-weights.json`.

**File**: `bl/question_weights.py`

**Test** (`tests/test_question_weights_quality.py`):
- `record_result(id, "INCONCLUSIVE", quality_score=0.2)` -> weight gets +0.3 bump vs plain INCONCLUSIVE
- `record_result(id, "INCONCLUSIVE", quality_score=0.8)` -> NO extra bump (quality_score >= 0.4)
- `record_result(id, "HEALTHY", quality_score=0.2)` -> no bump (only INCONCLUSIVE triggers it)
- `last_quality_score` persisted and loaded from `.bl-weights.json`
- Backward compat: load existing `.bl-weights.json` without `last_quality_score` -> no error

---

### Task 4 — bl/question_sharpener.py: new feedback loop module
**Parallel: yes (independent of T1, T2, T3)**

New module. The sharpener reads INCONCLUSIVE findings and narrows broad PENDING questions.

```python
def sharpen_pending_questions(
    project_dir: Path | str,
    max_sharpen: int = 5,
    dry_run: bool = False,
) -> list[str]:
    """
    1. Load all INCONCLUSIVE findings from findings/*.md (check **Verdict**: line)
    2. For each INCONCLUSIVE finding, extract its mode/domain (**Mode**: line)
    3. Load PENDING questions from questions.md
    4. For each INCONCLUSIVE finding, find PENDING questions with same mode
       that do NOT already have **Sharpened**: true
    5. For each matched question (up to max_sharpen total):
       - Append [narrowed: {3-word keyword from finding summary}] to question title
       - Add **Sharpened**: true on new line after **Status**: in questions.md
    6. Write updated questions.md atomically (write temp file, then rename)
    7. Return list of sharpened question IDs
    """
```

Helper functions:
```python
def _extract_finding_mode(content: str) -> str | None:
    """Parse **Mode**: line from finding .md, return mode string e.g. 'diagnose'"""

def _finding_keyword(content: str) -> str:
    """Return first 3 words from ## Summary section, joined by '-'"""
```

**File**: `bl/question_sharpener.py`

**Test** (`tests/test_question_sharpener.py`):
- Fixture: tmp questions.md with 3 PENDING questions (modes: diagnose, benchmark, audit)
  + tmp findings/ with 1 INCONCLUSIVE finding (mode: diagnose)
- `sharpen_pending_questions(tmp_dir)` -> returns list containing the diagnose question ID
- The diagnose question in questions.md has `**Sharpened**: true`
- `dry_run=True` -> returns list but does NOT modify questions.md
- Already-sharpened question -> not re-sharpened (idempotent)
- No INCONCLUSIVE findings -> returns empty list

---

### Task 5 — Agent .md patches
**Parallel: yes (independent of T1–T4)**

Targeted, minimal additions to 5 agent instruction files. Do NOT rewrite agents.

**5a. template/.claude/agents/peer-reviewer.md**

Find the output JSON contract section. Add `quality_score` field to the JSON schema:
```
"quality_score": 0.0,  // 0.0-1.0: how well-evidenced is the primary finding?
```
Add scoring rubric immediately after the JSON block:
```markdown
## quality_score Rubric
- 0.9-1.0: Finding has reproduction steps, exact error output, line numbers, confirmed fix
- 0.7-0.8: Finding has evidence but missing one of: steps, output, or line numbers
- 0.5-0.6: Finding is partially evidenced — summary exists but details are thin
- 0.3-0.4: Finding is speculative — no test rerun possible, assertion-only
- 0.0-0.2: Finding cannot be evaluated at all (missing file, 404, timeout)
```

**5b. template/.claude/agents/mortar.md**

Find the wave-start or startup section. Add campaign-context.md write procedure:
```markdown
**Campaign Context (write at wave start, refresh every 10 findings):**
Write `campaign-context.md` in project root:
- "# Campaign Context — {project} (Wave {N})"
- ## Project: first paragraph of project-brief.md
- ## Top Findings: ID, verdict, one-line summary of 5 highest-severity findings
- ## Open Hypotheses: PENDING questions with weight > 1.5 from .bl-weights.json
Prepend "Read campaign-context.md before proceeding." to every specialist agent spawn prompt.
```

Add INCONCLUSIVE re-queue trigger to finding-receipt logic:
```markdown
**INCONCLUSIVE Re-queue Rule:**
When receiving a finding with verdict INCONCLUSIVE AND peer-reviewer quality_score < 0.4:
- Set question status back to PENDING in questions.md
- Append [retry: narrow scope] to question title
- Log: "Re-queued {qid} — INCONCLUSIVE quality_score {score:.2f} < 0.4"
Otherwise: accept INCONCLUSIVE normally.
```

**5c. template/.claude/agents/synthesizer-bl2.md**

Find the synthesis procedure steps. Insert before the synthesis.md write step:
```markdown
**Before writing synthesis.md, run question sharpener (non-fatal if unavailable):**
```python
python -c "
from bl.question_sharpener import sharpen_pending_questions
from pathlib import Path
try:
    ids = sharpen_pending_questions(Path('.'))
    print(f'Sharpened {len(ids)} questions: {ids}')
except Exception as e:
    print(f'Sharpener skipped: {e}')
"
```
```

**5d. template/.claude/agents/agent-auditor.md**

Find the scoring methodology section. Add after definitive rate calculation:
```markdown
## Trend Detection
For each agent that has `runs[]` data in agent_db.json:
  Import and call: `from bl.agent_db import get_trend`
  `trend = get_trend(project_root, agent_name, window=5)`
  If `trending == "down"`: flag in AUDIT_REPORT.md with prefix "TRENDING DOWN"
  If `trending == "up"`: note in report with prefix "IMPROVING"
  Skip agents without runs[] (backward compat).
```

**5e. template/.claude/agents/forge-check.md**

Find the fleet completeness checks section. Add:
```markdown
## Tools Manifest Check
- Look for `template/.claude/agents/tools-manifest.md`
- If absent: add entry to FORGE_NEEDED.md: "tools-manifest.md missing — agents cannot discover available tools"
- If present: verify it contains at least 5 tool entries (lines starting with `- \``)
```

---

### Task 6 — tools-manifest.md: canonical tool catalog
**Parallel: yes (no dependencies)**

Create `template/.claude/agents/tools-manifest.md`:

```markdown
---
name: tools-manifest
description: Canonical catalog of all MCP tools available to BrickLayer agents. Reference when writing new agents.
type: reference
---

# BrickLayer Tools Manifest

## recall
Memory system at 100.70.195.84:8200. Cross-session fact storage and retrieval.
- `recall_search(query, domain, limit)` — semantic similarity search
- `recall_store(content, domain, tags, importance)` — persist a fact
- `recall_timeline(domain, limit)` — chronological retrieval

## simulate
Python subprocess for quantitative testing.
- `python simulate.py` — run scenario parameters, returns verdict JSON
- Edit SCENARIO PARAMETERS section only; never touch constants.py

## filesystem
Standard Claude Code file tools. Always available.
- `Read`, `Write`, `Edit` — file I/O
- `Glob`, `Grep` — file and content search
- `Bash` — shell commands (git, python, curl)

## github
GitHub MCP server for repo operations.
- `mcp__github__create_pull_request` — open PR from current branch
- `mcp__github__create_issue` — file a bug or finding as an issue
- `mcp__github__push_files` — push file changes to remote

## masonry
Masonry MCP server (masonry-mcp.js). Campaign state and operations.
- `masonry_status` — current campaign state and progress
- `masonry_findings` — recent findings with verdicts
- `masonry_questions` — question bank query
- `masonry_weights` — priority weight report from .bl-weights.json
- `masonry_fleet` — agent registry with performance scores
- `masonry_git_hypothesis` — generate questions from recent git diffs
- `masonry_nl_generate` — NL description to research questions
- `masonry_run_question` — run a single question by ID

## exa
Exa MCP for web research and documentation retrieval.
- `mcp__exa__web_search_exa` — semantic web search
- `mcp__exa__get_code_context_exa` — fetch code examples for a library
- `mcp__exa__crawling_exa` — fetch full page content from a URL
```

**File**: `template/.claude/agents/tools-manifest.md`

---

### Task 7 — Dashboard backend: expose confidence + sharpened via API
**Parallel: run after Tasks 1–4 complete**

**File**: `masonry/dashboard/backend/main.py`

In the finding-parsing section (around line 148), add after existing field extraction:
```python
import re

# Confidence float
conf_match = re.search(r'\*\*Confidence\*\*:\s*([\d.]+)', content)
confidence = float(conf_match.group(1)) if conf_match else None

# Needs human flag
nh_match = re.search(r'\*\*Needs Human\*\*:\s*(True|False)', content, re.IGNORECASE)
needs_human = nh_match.group(1).lower() == "true" if nh_match else False
```

Include in the finding dict returned to client: `"confidence": confidence, "needs_human": needs_human`

In the question-parsing section, add sharpened detection:
```python
sharpened = bool(re.search(r'\*\*Sharpened\*\*:\s*true', block, re.IGNORECASE))
```

Include in question dict: `"sharpened": sharpened`

Add confidence filter query params to the findings endpoint:
```python
@app.get("/api/findings")
async def get_findings(
    confidence_min: float = 0.0,
    confidence_max: float = 1.0,
    needs_human: bool | None = None,
):
    findings = _get_findings_cached()
    if confidence_min > 0.0 or confidence_max < 1.0:
        findings = [f for f in findings
                    if f.get("confidence") is None or
                    confidence_min <= f["confidence"] <= confidence_max]
    if needs_human is not None:
        findings = [f for f in findings if f.get("needs_human") == needs_human]
    return findings
```

**File**: `masonry/dashboard/frontend/src/lib/api.ts`

Extend the Finding and Question interfaces:
```typescript
export interface Finding {
  id: string;
  title: string;
  verdict: string;
  severity: string;
  has_correction: boolean;
  modified: string;
  confidence: number | null;   // NEW — 0.0-1.0 or null for pre-Phase-6 findings
  needs_human: boolean;        // NEW
}

export interface Question {
  id: string;
  title: string;
  status: string;
  domain: string;
  hypothesis: string | null;
  sharpened: boolean;          // NEW
}
```

---

### Task 8 — Dashboard UI: confidence badge + sharpened badge
**Parallel: after Task 7**

**File**: `masonry/dashboard/frontend/src/components/FindingFeed.tsx`

1. Add confidence filter state at component top:
```typescript
const [confFilter, setConfFilter] = useState<string>("all");
```

2. Add filter dropdown next to the existing verdict filter:
```tsx
<select value={confFilter} onChange={e => setConfFilter(e.target.value)}
  style={{background:'#1e1b2e', border:'1px solid rgba(255,255,255,0.1)',
          color:'#9ca3af', borderRadius:6, padding:'4px 8px', fontSize:13}}>
  <option value="all">All Confidence</option>
  <option value="high">High (≥0.7)</option>
  <option value="med">Medium (0.4–0.7)</option>
  <option value="low">Low (&lt;0.4)</option>
  <option value="human">Needs Human</option>
</select>
```

3. Apply filter in displayedFindings derivation:
```typescript
const displayedFindings = findings
  .filter(f => verdictFilter === "all" || f.verdict === verdictFilter)
  .filter(f => {
    if (confFilter === "all") return true;
    if (confFilter === "human") return f.needs_human;
    if (confFilter === "high") return f.confidence !== null && f.confidence >= 0.7;
    if (confFilter === "med") return f.confidence !== null && f.confidence >= 0.4 && f.confidence < 0.7;
    if (confFilter === "low") return f.confidence !== null && f.confidence < 0.4;
    return true;
  });
```

4. Add confidence badge inside each FindingCard, next to verdict badge:
```tsx
{finding.confidence !== null && (
  <span style={{
    background: finding.confidence >= 0.7 ? 'rgba(52,211,153,0.15)' :
                finding.confidence >= 0.4 ? 'rgba(56,189,248,0.15)' :
                                            'rgba(245,158,11,0.15)',
    color: finding.confidence >= 0.7 ? '#34d399' :
           finding.confidence >= 0.4 ? '#38bdf8' : '#f59e0b',
    padding: '1px 6px', borderRadius: 4, fontSize: 11, fontWeight: 600
  }}>
    {finding.confidence >= 0.7 ? '◆ high' :
     finding.confidence >= 0.4 ? '◆ med' : '◆ low'}
  </span>
)}
{finding.needs_human && (
  <span title="Needs human review"
    style={{color:'#f59e0b', fontSize:13, marginLeft:4}}>⚑</span>
)}
```

**File**: `masonry/dashboard/frontend/src/components/QuestionQueue.tsx`

Add sharpened badge next to question ID in the table row:
```tsx
{question.sharpened && (
  <span style={{
    background: 'rgba(139,92,246,0.15)', color: '#8b5cf6',
    padding: '1px 5px', borderRadius: 3, fontSize: 10, fontWeight: 600,
    marginLeft: 4
  }}>✦ sharpened</span>
)}
```

---

### Task 9 — Kiln: verdict run history dots in AgentBriefModal
**Parallel: after Task 2 completes**

**File 1**: `C:\Users\trg16\Dev\BrickLayerHub\src\main\agentReader.ts`

Add `runs` to the `Agent` interface:
```typescript
export interface Agent {
  name: string;
  file: string;
  slug: string;
  score: number;
  mode: string;
  description: string;
  model: string;
  lastVerdicts: string[];
  status: "active" | "underperforming" | "idle";
  project?: string;
  runs: Array<{ timestamp: string; verdict: string; quality_score: number | null }>;  // NEW
}
```

In `readAgentDb()`, update the return type to include runs:
```typescript
function readAgentDb(
  blRoot: string,
): Record<string, { score?: number; verdicts?: string[]; runs?: Array<{timestamp: string; verdict: string; quality_score: number | null}> }> {
```

In `readAgents()`, after extracting `dbEntry`:
```typescript
const runs = (dbEntry.runs || []).slice(-20); // last 20 only
```

Include in `agents.push({..., runs, ...})`.

**File 2**: `C:\Users\trg16\Dev\BrickLayerHub\src\renderer\src\components\common\AgentBriefModal.tsx`

Add run history dots section above the lastVerdicts section. Use these verdict-to-color mappings
(aligned with existing Kiln color palette):
```typescript
const SUCCESS_VERDICTS = new Set(["HEALTHY","FIXED","COMPLIANT","CALIBRATED","IMPROVEMENT","OK","PROMISING","DIAGNOSIS_COMPLETE","NOT_APPLICABLE","DONE"]);
const PARTIAL_VERDICTS = new Set(["WARNING","PARTIAL","WEAK","DEGRADED","FIX_FAILED","SUBJECTIVE","IMMINENT","PROBABLE","POSSIBLE","UNLIKELY"]);

function runDotColor(verdict: string): string {
  if (SUCCESS_VERDICTS.has(verdict)) return "#39D353";
  if (PARTIAL_VERDICTS.has(verdict)) return "#FACC15";
  return "#F85149";
}
```

Insert JSX before the lastVerdicts display:
```tsx
{agent.runs && agent.runs.length > 0 && (
  <div style={{ marginBottom: 12 }}>
    <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 6,
                  textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      Run History ({agent.runs.length})
    </div>
    <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
      {agent.runs.map((run, i) => (
        <div
          key={i}
          title={`${run.verdict}${run.quality_score != null ? ` · q=${run.quality_score.toFixed(2)}` : ''} — ${new Date(run.timestamp).toLocaleDateString()}`}
          style={{
            width: 8, height: 8, borderRadius: 2,
            background: runDotColor(run.verdict),
            opacity: 0.85,
          }}
        />
      ))}
    </div>
  </div>
)}
```

---

## Tech Stack

- **Python 3.11+**, `pathlib.Path`, `json`, `re`, `datetime`
- **pytest** for all bl/ tests — run with `python -m pytest tests/ -q`
- **TypeScript / React** (Kiln — Electron + Vite + React 18)
- **React + inline styles** (Dashboard frontend — no Tailwind in masonry/dashboard)
- **FastAPI** (Dashboard backend)

## Agent Hints

**Critical file paths:**
- `C:/Users/trg16/Dev/Bricklayer2.0/bl/findings.py` — `write_finding()` at line 342, `_CONFIDENCE_FLOAT` goes at module level
- `C:/Users/trg16/Dev/Bricklayer2.0/bl/agent_db.py` — `record_run()`, add `get_trend()` as new function
- `C:/Users/trg16/Dev/Bricklayer2.0/bl/question_weights.py` — `QuestionWeight` dataclass + `record_result()`
- `C:/Users/trg16/Dev/Bricklayer2.0/masonry/dashboard/backend/main.py` — finding parser ~line 148, question parser ~line 38
- `C:/Users/trg16/Dev/Bricklayer2.0/masonry/dashboard/frontend/src/components/FindingFeed.tsx`
- `C:/Users/trg16/Dev/Bricklayer2.0/masonry/dashboard/frontend/src/components/QuestionQueue.tsx`
- `C:/Users/trg16/Dev/Bricklayer2.0/masonry/dashboard/frontend/src/lib/api.ts`
- `C:/Users/trg16/Dev/BrickLayerHub/src/main/agentReader.ts`
- `C:/Users/trg16/Dev/BrickLayerHub/src/renderer/src/components/common/AgentBriefModal.tsx`
- `C:/Users/trg16/Dev/Bricklayer2.0/template/.claude/agents/` — peer-reviewer.md, mortar.md, synthesizer-bl2.md, agent-auditor.md, forge-check.md

**Test command:** `cd C:/Users/trg16/Dev/Bricklayer2.0 && python -m pytest tests/ -q`
**Type check (Kiln):** `cd C:/Users/trg16/Dev/BrickLayerHub && npx tsc --noEmit`
**Existing test suite:** `tests/conftest.py`, `tests/test_core.py`, `tests/test_goal.py`, etc.

## Constraints

- Do NOT modify `constants.py` or `simulate.py`
- Do NOT rewrite entire agent .md files — surgical additions only
- `write_finding()` backward compat: callers without `confidence` in result dict get `"uncertain"` (0.1)
- `record_run()` new params `duration_ms` and `quality_score` are optional — no breaking change
- `record_result()` new param `quality_score` is optional — no breaking change
- Dashboard backend: ADD new fields to existing response shapes only — never remove existing fields
- Kiln: ADD `runs` to Agent interface — keep all existing fields

## Definition of Done

- All 4 new Python test files pass (T1, T2, T3, T4 tests)
- Full test suite passes: `python -m pytest tests/ -q` exits 0
- Kiln TypeScript compiles: `npx tsc --noEmit` exits 0
- A finding written by `write_finding()` contains `**Confidence**:` and `**Needs Human**:` lines
- `agent_db.json` grows `runs[]` array on each `record_run()` call
- `question_sharpener.py` can be imported and called without error
- Dashboard backend `/api/findings` response includes `confidence` and `needs_human` fields
- Dashboard FindingFeed shows confidence badges and confidence filter dropdown
- Kiln AgentBriefModal shows run history dots when `runs[]` is non-empty
- All 5 agent .md files have their targeted additions
- `tools-manifest.md` exists in `template/.claude/agents/`

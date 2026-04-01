# BrickLayer 2.0 — Session Context

## What BrickLayer Is

BrickLayer is a **full project lifecycle system** — from first idea to running production code to ongoing maintenance. It is NOT just a research or investigation tool. The name is literal: **it lays every brick**.

BrickLayer orchestrates the entire build through its engine (`bl/`), agent fleet, mode system, and inter-agent communication layer. Claude Code is the execution runtime; BrickLayer drives what gets built, how it's verified, and how it evolves.

**If you think BrickLayer is "just research" — you're wrong. Read this section again.**

## The Lifecycle (Build Is a First-Class Phase)

```
CONCEPTION     Frontier mode — structured hypothesis generation
VALIDATION     Research mode — evidence-based stress testing
PRE-BUILD      Validate + Benchmark — design verification + baselines
BUILD          Agent orchestration, swarm runners, code generation, inter-agent
               coordination via Recall — BrickLayer drives the build
POST-BUILD     Audit + Diagnose — compliance and fault detection
REPAIR         Fix mode + heal loop — automated diagnose→fix→verify cycles
ONGOING        Evolve + Predict + Monitor — continuous improvement
```

Every phase is BrickLayer. There is no handoff to an external system.

## Engine Architecture (`bl/`)

The engine is Python, orchestrated via tmux for parallel agent dispatch.

### Core Systems

| Module | Purpose |
|--------|---------|
| `bl/tmux/` | Agent orchestration — pane spawn, wave dispatch, signal coordination |
| `bl/runners/` | 15 evidence-collection runners (agent, swarm, benchmark, contract, browser, etc.) |
| `bl/healloop.py` | Self-healing: diagnose → fix → verify, up to N cycles |
| `bl/recall_bridge.py` | Inter-agent memory — agents share context through Recall |
| `bl/recall_hook.py` | Recall event hooks for agent coordination |
| `bl/crucible.py` | Agent benchmarking — promote/flag/retire based on eval scores |
| `bl/nl_entry.py` | Natural language → research questions from plain English |
| `bl/skill_forge.py` | Skill generation and management |
| `bl/training_export.py` | Training data extraction from campaign runs |
| `bl/git_hypothesis.py` | Hypothesis generation from git diffs |
| `bl/campaign_context.py` | Campaign state and cross-question context |
| `bl/findings.py` | Finding storage, verdict tracking, results.tsv management |
| `bl/questions.py` | Question bank parsing, weighting, status sync |
| `bl/synthesizer.py` | Cross-finding synthesis |
| `bl/goal.py` | Goal tracking and decomposition |
| `bl/sweep.py` | Sweep operations across question banks |
| `bl/config.py` | Project configuration |

### Runner Types

| Runner | What It Does |
|--------|-------------|
| `agent` | Single-agent evidence collection via tmux |
| `swarm` | Multi-agent parallel dispatch with verdict aggregation |
| `benchmark` | Quantitative baseline measurement |
| `contract` | Static analysis for smart contracts (Solana/Anchor) |
| `browser` | Browser-based verification |
| `performance` | Performance profiling and measurement |
| `document` | Documentation generation and verification |
| `scout` | Reconnaissance/exploration runner |
| `simulate` | Simulation-based evidence collection |
| `subprocess` | Shell command execution and output capture |
| `http` | HTTP endpoint verification |
| `correctness` | Correctness proof verification |
| `quality` | Code quality assessment |
| `baseline_check` | Baseline comparison |

## Mode System (9 Modes)

Each mode has its own `program.md`, agent roster, verdict vocabulary, and runner preferences.

| Mode | Verdicts |
|------|----------|
| Frontier | PROMISING, WEAK, BLOCKED |
| Research | HEALTHY, WARNING, FAILURE |
| Validate | HEALTHY, WARNING, FAILURE |
| Benchmark | CALIBRATED, UNCALIBRATED, NOT_MEASURABLE |
| Diagnose | DIAGNOSIS_COMPLETE, HEALTHY, WARNING, FAILURE |
| Fix | FIXED, FIX_FAILED |
| Audit | COMPLIANT, NON_COMPLIANT, PARTIAL |
| Evolve | IMPROVEMENT, REGRESSION, WARNING |
| Predict | IMMINENT, PROBABLE, POSSIBLE, UNLIKELY |
| Monitor | OK, DEGRADED, ALERT |

## Project Structure

```
Bricklayer2.0/
  bl/                    -- The engine (Python)
    runners/             -- 15 evidence-collection runners
    tmux/                -- Agent orchestration layer
    cli/                 -- CLI commands
    tests/               -- Engine tests
    ci/                  -- CI integration
  projects/              -- Active projects managed by BrickLayer
    recall/              -- Recall 1.0
    recall2/             -- Recall 2.0 (Rust rewrite, driven by frontier research)
    ADBP/                -- ADBP project
    adbp2/               -- ADBP v2
    ADBP3/               -- ADBP v3
    bl2/                 -- BrickLayer self-audit
    bricklayer/          -- BrickLayer meta-campaign
    agent-meta/          -- Agent fleet meta-analysis
    kiln-os/             -- Kiln OS
    MarchMadness/        -- March Madness project
    passive-frontend-v2/ -- Passive Frontend v2
  bricklayer-v2/         -- BL2 self-audit campaign (14+ waves)
  bricklayer-meta/       -- Meta-analysis of BrickLayer itself
  recall-arch-frontier/  -- 256-question frontier research → Recall 2.0 architecture
  masonry/               -- Masonry orchestration system
  template-frontier/     -- Template for new frontier projects
  docs/                  -- Documentation and repo research
  findings/              -- Cross-project findings
```

## Key Concepts

- **Campaign**: A run of the BrickLayer loop against a question bank. Produces findings and verdicts.
- **Wave**: A batch of questions processed in one campaign cycle. Waves accumulate over time.
- **Finding**: Evidence-backed conclusion with a verdict. Stored in `findings/` per project.
- **Verdict**: Classification of a finding (HEALTHY, WARNING, FAILURE, FIXED, etc.)
- **Synthesis**: Cross-finding summary updated after each wave.
- **Agent fleet**: Specialized agents (karen, research-analyst, git-nerd, etc.) with eval scores tracked in crucible.
- **Heal loop**: Automated diagnose→fix→verify cycle without human intervention.
- **Swarm**: Parallel multi-agent dispatch with configurable aggregation (worst/majority/any_failure).

## Authority Hierarchy

| Tier | Source | Who Edits |
|------|--------|-----------|
| Tier 1 | `project-brief.md`, `ARCHITECTURE.md` | Human only — ground truth |
| Tier 2 | `program.md`, `modes/*.md`, config | Human + agent |
| Tier 3 | `bl/` engine code, `findings/`, agents | Agent — implementation |

## MANDATORY: Agent Delegation via BrickLayer tmux Dispatch

**You are an orchestrator. You do NOT work alone.**

All agent dispatch goes through BrickLayer's tmux layer (`bl/tmux/core.py`). This spawns agents in visible tmux panes with `stream-json` output piped through `stream_format.py` — the user watches agents work in real time. When not in tmux, it falls back to subprocess.

**NEVER use Claude Code's built-in `Task` tool for agent work.** It spawns invisible child processes with no tmux panes, no signal files, no lifecycle hooks, and no masonry tracking.

### How to Spawn Agents

```python
from bl.tmux.core import spawn_agent, wait_for_agent

handle = spawn_agent(
    "rough-in",
    "Task: <user request>\nProject root: /path/to/project",
    cwd="/path/to/project",
    dangerously_skip_permissions=True,
)
result = wait_for_agent(handle)
```

This opens a tmux pane where the agent streams live. The user sees every step as it happens.

For parallel dispatch (multiple agents at once), use `bl/tmux/wave.py:spawn_wave()`.

### Delegation Rules

1. **Dev tasks** (build, fix, refactor, add feature): Spawn `rough-in`. It decomposes and dispatches to specialists. You do NOT write production code directly.
2. **Research/investigation** (why is X broken, explore Z): Spawn `mortar`. It routes to the right specialist.
3. **Planning** (design, architect, plan): Spawn `planner` or `design-reviewer`.
4. **Documentation** (changelog, docs, roadmap): Spawn `karen`.
5. **Code review**: Spawn `code-reviewer` after code changes.
6. **Bug diagnosis**: Spawn `diagnose-analyst`. Do NOT guess at fixes.

### When You May Work Directly (Exceptions)

- Simple questions (< 1 paragraph, no code changes)
- Reading files to understand context before delegating
- Read-only git operations (status, log, diff)
- Trivial one-line fixes the user explicitly dictates verbatim

### Available Core Agents

| Agent | When to Use |
|-------|------------|
| `rough-in` | Any dev task — owns the full build workflow |
| `mortar` | Session routing — decides which specialist handles a request |
| `developer` | Implementation (spawned by rough-in, not directly) |
| `code-reviewer` | Post-implementation review |
| `planner` | Design and planning |
| `design-reviewer` | Validate architecture before building |
| `fix-implementer` | Apply a known fix (after diagnosis) |
| `diagnose-analyst` | Root cause analysis |
| `tdd-orchestrator` | Test-driven development enforcement |
| `karen` | Documentation maintenance |
| `trowel` | Campaign conductor (research loops) |
| `spec-reviewer` | Spec compliance checking |
| `verifier` | Post-build verification |

83+ agents available globally in `~/.claude/agents/`.

## What NOT to Assume

- BrickLayer is NOT just research — it orchestrates builds, fixes, and maintenance
- Modes are NOT sequential requirements — projects skip, reorder, and loop back
- The agent fleet is NOT static — agents are benchmarked, promoted, and retired by crucible
- Inter-agent communication happens through Recall — agents share memory and context
- The build phase is NOT external — BrickLayer drives it through runners and agent orchestration

# Repo Research: forrestchang/andrej-karpathy-skills

**Repo**: https://github.com/forrestchang/andrej-karpathy-skills
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

This is a focused, minimal repo (7 files, ~20KB total) that distills Andrej Karpathy's public critique of LLM coding behavior into four behavioral rules delivered as a Claude Code `CLAUDE.md` / plugin. It does not beat BrickLayer on infrastructure, agent fleet, or research capabilities — BrickLayer is massively more sophisticated. Where it beats BrickLayer is in the *quality of behavioral constraints injected into developer agents*: it has the sharpest articulation of the "Surgical Changes" principle and a uniquely valuable example-driven format for teaching LLMs via concrete before/after code patterns. The core insight — transform imperative tasks into verifiable goals with step-by-step verification plans — partially maps to BrickLayer's TDD enforcement but lacks the depth of articulation needed to actually change agent behavior at inference time.

---

## File Inventory

### Root
| File | Category | Description |
|------|----------|-------------|
| `README.md` | docs | Full explainer of the four principles with install instructions. 5.5KB. |
| `CLAUDE.md` | prompt | The distilled behavioral guidelines — the actual CLAUDE.md to use/merge. 2.4KB. |
| `EXAMPLES.md` | docs | Before/after code examples for all four principles. 14.8KB — the most valuable file. |

### `.claude-plugin/`
| File | Category | Description |
|------|----------|-------------|
| `plugin.json` | config | Claude Code plugin manifest. Names the plugin, points skills to `./skills/karpathy-guidelines`. |
| `marketplace.json` | config | Claude Code marketplace registry. Allows `/plugin marketplace add forrestchang/andrej-karpathy-skills`. |

### `skills/karpathy-guidelines/`
| File | Category | Description |
|------|----------|-------------|
| `SKILL.md` | agent | The actual skill definition. Frontmatter + copy of CLAUDE.md content. Invoked as a slash command context injection. |

**Total: 6 substantive files + 1 directory listing. No code, no hooks, no workflows, no tests, no CI.**

---

## Architecture Overview

This repo is not a system — it is a behavioral prompt library packaged as a Claude Code plugin.

The architecture is flat:

```
CLAUDE.md (source of truth)
    ↓ copied into
skills/karpathy-guidelines/SKILL.md (plugin-accessible version)
    ↓ registered by
.claude-plugin/plugin.json (points to ./skills/karpathy-guidelines directory)
    ↓ discoverable via
.claude-plugin/marketplace.json (enables /plugin marketplace add)
```

Installation options:
1. **Plugin install** — `/plugin marketplace add` then `/plugin install` — installs globally across all Claude Code projects
2. **CLAUDE.md merge** — curl the raw CLAUDE.md and append to project CLAUDE.md — per-project override

There are no hooks, no MCP servers, no agent fleet, no workflows, no CI/CD, no data pipelines. This is pure prompt engineering — a curated set of behavioral constraints expressed as natural language rules.

---

## Agent Catalog

### karpathy-guidelines (SKILL.md)

**Purpose**: Inject four behavioral constraints into Claude Code at session start or on demand.

**Tools**: None (pure context injection, no tool use).

**Invocation**: Via Claude Code plugin system — automatically injected when installed, or invoked explicitly.

**Key unique capabilities**:

1. **Think Before Coding** — Explicit pre-implementation checklist:
   - State assumptions before writing code
   - Present multiple interpretations instead of picking silently
   - Push back if a simpler approach exists
   - Stop and ask when confused rather than guessing

2. **Simplicity First** — Anti-overengineering manifesto:
   - No features beyond what was asked
   - No abstractions for single-use code
   - No speculative "flexibility" or "configurability"
   - Self-test: "Would a senior engineer call this overcomplicated?"

3. **Surgical Changes** — Minimum-diff discipline:
   - Touch only what the task requires
   - Don't improve adjacent code, formatting, or comments
   - Match existing style even if you'd do it differently
   - Remove only imports/variables YOUR changes made unused — not pre-existing dead code
   - Self-test: "Every changed line traces directly to the user's request"

4. **Goal-Driven Execution** — Imperative→declarative transformation:
   - Reframe vague tasks as verifiable success criteria
   - For multi-step tasks, produce a numbered plan with per-step verification checks
   - Loop until verified rather than asking "is this ok?"

**Prompt engineering technique**: Rules are paired with concrete self-test questions ("Would a senior engineer say this is overcomplicated?", "Does every changed line trace to the user's request?"). This is more actionable than abstract guidelines because it gives the model a specific check to execute.

**Output format**: Behavioral modifier — no structured output artifacts.

---

## The EXAMPLES.md: Why It Matters

`EXAMPLES.md` (14.8KB) is the most technically valuable file in the repo. It contains before/after Python diffs for each of the four principles, showing:

- **Hidden assumptions** — LLM silently exports all users with hardcoded fields vs. surfacing 4 clarifying questions first
- **Over-abstraction** — Strategy pattern + abstract base class for a single discount calculation vs. one 3-line function
- **Drive-by refactoring** — Adding type hints, docstrings, and reformatting while fixing an email validation bug vs. surgical 2-line fix
- **Style drift** — Changing quote style and reformatting while adding logging vs. matching existing single-quote style exactly
- **Vague goals** — "I'll review and improve" vs. numbered plan with per-step verification
- **Test-first reproduction** — Jumping to fix vs. writing a test that reproduces the bug first

The format is: user request → bad LLM response (annotated with specific problems) → correct LLM response.

This examples-driven format is a prompt engineering pattern BrickLayer does not currently use in its developer agents. Examples at inference time are more effective than abstract rules for changing model behavior.

---

## Feature Gap Analysis

| Feature | In forrestchang/andrej-karpathy-skills | In BrickLayer 2.0 | Gap Level | Notes |
|---------|---------------------------------------|-------------------|-----------|-------|
| "Surgical Changes" principle — explicit rule against touching adjacent code | Yes — core rule with self-test | Partial — developer.md has "no speculative features" but no explicit anti-adjacent-edit rule | HIGH | BL developer agent doesn't explicitly prohibit improving adjacent code, reformatting, or style drift |
| "Think Before Coding" — surface assumptions before implementing | Yes — structured as pre-implementation checklist | Partial — overseer.md and verification.md check outputs but no agent explicitly requires surfacing assumptions *before* writing | HIGH | Prevents class of bugs where LLM picks an interpretation silently and writes 200 lines of wrong code |
| Example-driven behavioral rules (before/after code diffs) | Yes — EXAMPLES.md has 8 full before/after examples | No — BL rules are abstract prose, no inline examples | HIGH | Before/after examples in agent prompts measurably improve adherence; BL quality-standards.md uses this for Python/TS patterns but not for behavioral constraints |
| Simplicity First — explicit anti-overengineering checklist | Yes — 5 specific prohibitions + senior-engineer self-test | Partial — developer.md says "no speculative features, no over-engineering" | MEDIUM | BL has the rule but lacks the specific self-test question and the 5-item checklist format |
| Goal-Driven Execution — imperative→declarative task reframing | Yes — explicit transformation table + numbered plan format | Partial — TDD enforcement + verification checklist cover this implicitly | MEDIUM | BL enforces verification outcomes but doesn't teach agents to *reframe* vague tasks into verifiable goals before starting |
| Claude Code plugin packaging (`.claude-plugin/` + marketplace.json) | Yes — installable via `/plugin marketplace add` | No — BL distributes via CLAUDE.md and agent .md files | LOW | Different distribution model; BL's approach is more powerful (hooks, MCP, registry) but plugin format is simpler for sharing |
| Tradeoff note (calibrate rigor to task complexity) | Yes — explicit: "for trivial tasks, use judgment" | No — BL rules are always-on without task-complexity calibration | MEDIUM | BL's 3-strike rule and verification-checklist apply equally to all tasks; trivial tasks shouldn't require full TDD + code review overhead |
| Karpathy's original source citation | Yes — links to @karpathy tweet | No | LOW | Not a capability gap; informational only |
| "Success criteria loop" — explicit autonomy enablement | Yes — "strong criteria let you loop independently" | Partial — build/verify/fix cycle handles this structurally | MEDIUM | The *framing* matters: telling agents they can loop independently on well-defined tasks changes their behavior even without structural enforcement |
| Pre-implementation assumption surfacing as a required step | Yes — named explicit step before coding | No — spec-writer does this for plans, but individual developer/fix agents don't require it | HIGH | Developer agent jumps straight to GREEN phase without a "surface ambiguity" gate |
| Dead code ownership rule — only remove what YOUR changes orphaned | Yes — explicit distinction | Partial — developer.md REFACTOR phase says "remove dead code" without this ownership qualifier | MEDIUM | BL developer can incorrectly remove pre-existing dead code during refactor phase, creating unintended diffs |

---

## Top 5 Recommendations

### 1. Add "Surgical Changes" Constraint to Developer and Fix-Implementer Agents [2h, HIGH]

**What to build**: Add an explicit section to `developer.md`, `fix-implementer.md`, and `senior-developer.md`:

```
## Surgical Changes Constraint

Touch only what the task requires. Every changed line must trace directly to the task description.

NEVER:
- Improve adjacent code, comments, or formatting not related to the task
- Refactor things that aren't broken
- Change quote style, whitespace, or imports you didn't create
- Add docstrings, type hints, or other "improvements" not requested

ALWAYS:
- Match the existing codebase style, even if you'd do it differently
- If you notice unrelated dead code or issues, mention them in your report — don't change them

Ownership rule for dead code cleanup (REFACTOR phase only):
- Remove imports/variables/functions that YOUR GREEN phase changes made unused
- Do NOT remove pre-existing dead code or unused items — that's economizer's job
```

**Why it matters**: The current developer agent's REFACTOR phase says "remove dead code" without qualifying *whose* dead code. This creates diffs that include unrelated cleanup, making PRs noisy and risking conflicts with other sessions.

**Implementation sketch**: Edit `C:/Users/trg16/.claude/agents/developer.md`, `fix-implementer.md`, `senior-developer.md`. Add the section above to each. Takes ~30 mins per file.

---

### 2. Add Pre-Implementation Ambiguity Gate to Developer and Fix Agents [3h, HIGH]

**What to build**: Before the RED phase in developer.md, add a required "Assumption Surface" step:

```
## Step 0: Surface Ambiguities (NEW — before RED)

Before running tests or writing code:

1. Re-read the task description. Are there any ambiguities about:
   - Which files to touch (multiple could satisfy the description)?
   - What "done" looks like (could be interpreted multiple ways)?
   - Whether you're extending vs. replacing existing behavior?

2. If ambiguity exists that would lead to different code paths:
   - State the ambiguity explicitly in your response
   - Pick the most conservative interpretation (fewest changes, existing behavior preserved)
   - Flag it: "ASSUMPTION: I'm treating this as X. If you meant Y, redirect me."

3. If the task is unambiguous, proceed to RED without pausing.
```

**Why it matters**: The current developer agent starts at RED immediately, which means ambiguous tasks get 200 lines of wrong code that must be thrown out. The spec-writer covers ambiguity at plan time, but individual fix tasks arrive without this gate, leading to the failure mode Karpathy describes: "The model picks an interpretation silently and runs with it."

**Implementation sketch**: Edit `developer.md` and `fix-implementer.md`. Also add to `diagnose-analyst.md` — diagnosers also benefit from surfacing assumptions before root-cause analysis.

---

### 3. Port EXAMPLES.md Pattern into Key Agent Prompts [4h, HIGH]

**What to build**: Add concrete before/after examples to the behavioral sections of `developer.md`, `code-reviewer.md`, and `typescript-specialist.md`/`python-specialist.md`.

The pattern: show a bad LLM output, annotate the specific failure, show the correct output.

Priority examples to add:
1. **Drive-by refactoring** (for developer.md) — Show the diff where the agent added type hints and reformatted while fixing a bug; show the surgical 2-line diff that's correct
2. **Over-abstraction** (for developer.md) — Show Strategy pattern being built for a one-off calculation; show the 3-line function
3. **Vague vs. verifiable plan** (for spec-writer.md) — Show "I'll review and improve" vs. numbered plan with per-step verification

**Why it matters**: BrickLayer's quality-standards.md already uses this format for error handling patterns (Python/TS). The research literature on few-shot prompting is clear: concrete examples in the system prompt outperform abstract rules. The Karpathy examples in EXAMPLES.md are specifically calibrated to the failure modes BrickLayer faces in its developer agent.

**Implementation sketch**: Extract the most relevant examples from EXAMPLES.md (the surgical changes + simplicity examples are directly applicable). Embed them as `## ❌ Anti-pattern` / `## ✅ Correct` pairs inside the relevant agent sections.

---

### 4. Add Task-Complexity Calibration to Verification Checklist [1h, MEDIUM]

**What to build**: Add a tiered bypass to `verification-checklist.md` and the `/verify` workflow:

```
## Task Complexity Tiers

Before applying the full checklist, classify the task:

- **Trivial** (typo fix, constant change, 1-3 line change): Skip TDD requirement. Still check types and lint.
- **Standard** (feature addition, bug fix, refactor): Full checklist applies.
- **Critical** (auth, payments, data migration, public API): Full checklist + security review.
```

**Why it matters**: BrickLayer currently applies full TDD + verification overhead to every task regardless of complexity. This creates friction on trivial fixes and trains agents to treat all tasks as equal, which is wrong. The Karpathy repo explicitly notes this tradeoff: "For trivial tasks, use judgment." Adding a tier system reduces overhead on simple tasks and reserves rigor for complex ones.

---

### 5. Formalize "Goal-Driven Execution" as a Required Pre-Build Step [2h, MEDIUM]

**What to build**: Add a "transform to verifiable goals" step to spec-writer.md and mortar.md routing:

When a vague request like "fix authentication" or "improve performance" arrives:
1. The spec-writer (or mortar, for ad-hoc requests) must transform it to a numbered plan with per-step verification before dispatching work
2. Each step must specify: what to build + how to verify + what constitutes passing

This is partially covered by the `/plan` workflow, but mortar currently dispatches developer agents on vague tasks without requiring this reframing.

**Why it matters**: The Karpathy insight is precise: "LLMs are exceptionally good at looping until they meet specific goals. Don't tell it what to do, give it success criteria and watch it go." BrickLayer's `/build` workflow does this structurally, but ad-hoc tasks dispatched through mortar don't require goal reframing first.

---

## Novel Patterns to Incorporate (Future)

### Self-Test Questions as Behavioral Checks
The Karpathy guidelines use a specific format: end each principle with a self-test question the agent can actually execute. Examples:
- "Would a senior engineer call this overcomplicated?" (Simplicity First)
- "Does every changed line trace directly to the user's request?" (Surgical Changes)

BrickLayer agents use abstract rules. Adding self-test questions at the end of key behavioral sections gives agents a concrete action they can perform as a final check before returning results. This is worth adding to developer.md, fix-implementer.md, and code-reviewer.md.

### Plugin Marketplace Distribution
The `.claude-plugin/` structure (plugin.json + marketplace.json) enables sharing via `/plugin marketplace add owner/repo`. BrickLayer distributes skills via curl/copy, which requires knowing the URL. If BrickLayer skills are intended to be shared externally, packaging them with this structure would make distribution easier. Not urgent — BrickLayer is a private system.

### Tradeoff Calibration Comment Pattern
The CLAUDE.md opens with: `**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.` This meta-comment about the tradeoff the guidelines make is a useful UX pattern — it tells engineers when NOT to apply the rules. BrickLayer's rules (tdd-enforcement.md, verification-checklist.md) don't include this calibration signal, making them feel like hard mandates even for 2-line fixes.

### Implicit Commitment to "No Ratchet" Style Enforcement
The surgical changes principle includes "match existing style, even if you'd do it differently." This is an anti-ratchet rule — it prevents agents from gradually drifting the codebase toward their own stylistic preferences over many edits. BrickLayer's masonry-lint-check.js enforces formatting rules but doesn't prevent an agent from adding type hints, docstrings, or other style upgrades the user didn't request.

---

## Source: Original Karpathy Post

The repo cites: https://x.com/karpathy/status/2015883857489522876

Key quotes extracted from README:
> "The models make wrong assumptions on your behalf and just run along with them without checking. They don't manage their confusion, don't seek clarifications, don't surface inconsistencies, don't present tradeoffs, don't push back when they should."

> "They really like to overcomplicate code and APIs, bloat abstractions, don't clean up dead code... implement a bloated construction over 1000 lines when 100 would do."

> "They still sometimes change/remove comments and code they don't sufficiently understand as side effects, even if orthogonal to the task."

> "LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."

These quotes directly map to failure modes BrickLayer has encountered in the developer agent, particularly the third (orthogonal edits creating noisy diffs) and the first (silent assumption selection on ambiguous tasks).

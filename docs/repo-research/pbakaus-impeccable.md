# Repo Research: pbakaus/impeccable

**Repo**: https://github.com/pbakaus/impeccable
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

Impeccable is a multi-provider AI skills library laser-focused on frontend design quality — 20 slash commands backed by a deeply opinionated framework with quantitative scoring rubrics, persona-based UX testing, and explicit anti-pattern detection (the "AI Slop Test"). It beats BrickLayer in UI/UX command depth and formalized quality gates, with methodologies that are immediately portable to BrickLayer's agent fleet. BrickLayer beats it in everything else: it has no hooks system, no research campaigns, no MCP integration, no memory/recall, no TDD enforcement, no multi-agent orchestration — it is purely a skills library.

---

## File Inventory

### Root
- `README.md` — User-facing docs: 20 commands, installation for 10 providers, anti-pattern philosophy
- `AGENTS.md` — Architecture guide for AI assistants: source/build/dist pattern, provider transformation details
- `CLAUDE.md` — Project instructions: CSS build (Tailwind via Bun), versioning checklist, adding new skills checklist
- `DEVELOP.md` — Contributor guide: factory architecture, source format spec, how to add a new provider
- `HARNESSES.md` — Capability matrix: which frontmatter fields each provider supports, cross-reading rules
- `package.json` — v1.6.0, Bun runtime, archiver/motion/playwright dependencies
- `biome.json` — Code formatter/linter config
- `wrangler.toml` — Cloudflare Pages deployment config
- `.gitignore` — Ignores node_modules, dist (then un-ignores it for commit), build artifacts

### source/skills/ (21 skills, each a SKILL.md file)
- `frontend-design/SKILL.md` — Core skill: Context Gathering Protocol, Design Direction framework, DO/DON'T guidelines, AI Slop Test
- `audit/SKILL.md` — Technical quality checker: 5-dimension scoring (0-20), P0-P3 severity, WCAG/performance/theming
- `critique/SKILL.md` — UX design review: Nielsen's 10 heuristics (0-40 score), persona selection, 4-phase workflow
- `teach-impeccable/SKILL.md` — One-time setup: explores codebase, asks questions, writes `.impeccable.md` context file
- `overdrive/SKILL.md` — Technically extraordinary effects: View Transitions API, WebGL, scroll-driven animations, propose-before-build gate
- `polish/SKILL.md` — Comprehensive final pass: 12 categories, all 8 interaction states, full checkbox list
- `normalize/SKILL.md` — Design system alignment: discover deviations, create plan, execute across 8 dimensions
- `bolder/SKILL.md` — Amplify boring designs: typography extremes, dominant color strategy, spatial drama
- `harden/SKILL.md` — Production resilience: text overflow, i18n (30-40% expansion budget, RTL via CSS logical properties), error handling
- `delight/SKILL.md` — Joy and personality: micro-interactions, anti-AI-slop copy guidelines, spring physics, sound design
- `optimize/SKILL.md` — Performance: Core Web Vitals, bundle splitting, `content-visibility: auto`, React-specific patterns
- `motion/SKILL.md` — Animation systems: spring physics, reduced motion compliance, View Transitions API
- `theme/SKILL.md` — Theming: CSS custom properties, dark/light mode, semantic token layers
- `responsive/SKILL.md` — Responsive design: breakpoint strategy, fluid typography, container queries
- `typefix/SKILL.md` — Typography fixes: scale, rhythm, hierarchy corrections
- `colorfix/SKILL.md` — Color system fixes: contrast auditing, palette harmonization
- `accessibility/SKILL.md` — a11y: WCAG AA/AAA, ARIA, keyboard navigation, screen reader testing
- `copyfix/SKILL.md` — UX writing: error messages, empty states, button labels, microcopy
- `forms/SKILL.md` — Form UX: validation, error handling, progressive disclosure, accessibility
- `darkmode/SKILL.md` — Dark mode implementation: semantic tokens, OS preference detection, color science
- `components/SKILL.md` — Component library patterns: composition, variant APIs, documentation

### source/skills/frontend-design/reference/ (7 files)
- `anti-patterns.md` — Canonical anti-pattern list with explanations: Inter font, glassmorphism, purple-to-blue gradients, hero metrics, identical card grids, gradient text
- `design-direction.md` — Design decision framework: aesthetic vocabulary, direction selection process
- `do-dont.md` — Comprehensive DO/DON'T guidelines across all design dimensions
- `motion-guide.md` — Motion principles: spring physics defaults, timing scale, GPU rules
- `responsive.md` — Responsive strategy: breakpoints, fluid scales, touch targets
- `typography.md` — Typography system: scale, weights, pairing rules, OKLCH color for type
- `color.md` — Color system: OKLCH space, palette generation, semantic layering

### source/skills/critique/reference/ (3 files)
- `personas.md` — 5 user archetypes: Alex (Power User), Jordan (First-Timer), Sam (Accessibility-Dependent), Riley (Stress Tester), Casey (Mobile). Selection table by interface type.
- `heuristics-scoring.md` — Nielsen's 10 heuristics with 0-4 rubrics per heuristic; score bands (36-40 Excellent → 0-11 Critical); P0-P3 definitions with "Would a user contact support?" decision heuristic
- `cognitive-load.md` — Cognitive load theory applied to UI: chunking, progressive disclosure, recognition vs recall

### scripts/ (build system)
- `build.js` — Main build orchestrator: iterates providers × skills, calls transformer, writes dist files
- `lib/utils.js` — Shared utilities: `PROVIDER_PLACEHOLDERS` map, `parseFrontmatter()`, `replacePlaceholders()`, `prefixSkillReferences()`
- `lib/transformers/factory.js` — `createTransformer()` factory: provider config → transformer instance
- `lib/transformers/providers.js` — 10 provider definitions: frontmatterFields arrays, placeholderProvider overrides, comment syntax
- `lib/transformers/index.js` — Transformer registry and export
- `lib/zip.js` — ZIP archive generation for distribution packages

### tests/
- `build.test.js` — Integration tests for build output correctness
- `lib/` — Unit tests for transformers, frontmatter parsing, placeholder replacement
- `server/` — Test server for preview functionality

### .claude-plugin/
- `plugin.json` — Claude Code plugin manifest: name "impeccable", v1.6.0, skills path "./.claude/skills"
- `marketplace.json` — Marketplace metadata: categories, screenshots, install instructions

### dist/ (generated, committed)
- Per-provider generated files for all 21 skills (210+ files total — sampled)
- Provider directories: `claude-code/`, `cursor/`, `gemini/`, `codex/`, `copilot/`, `kiro/`, `opencode/`, `pi/`, `trae/`, `trae-cn/`

---

## Architecture Overview

Impeccable is a **build-time multi-provider skills distribution system** with a single source of truth:

```
source/skills/{skill-name}/SKILL.md  ←  canonical skill definition
        ↓ (build.js)
scripts/lib/transformers/providers.js  ←  10 provider configs
        ↓ (createTransformer per provider)
dist/{provider}/skills/{skill-name}/SKILL.md  ←  provider-specific output
        ↓ (committed to git)
user install → provider reads from appropriate location
```

**The Context Gathering Protocol** gates all skill execution:
1. Check if context is already loaded (prior instruction/session)
2. Read `.impeccable.md` if it exists in the project
3. Invoke `{{command_prefix}}teach-impeccable` to create it

This ensures skills never operate on inferred context — they always have explicit design direction.

**Skill composition** is explicit: every skill (e.g., `/audit`, `/critique`) opens with `MANDATORY PREPARATION: Run {{command_prefix}}frontend-design first` and treats that invocation as a hard prerequisite. Skills also cross-recommend via `{{available_commands}}` auto-injection at the end of each skill's output.

**The transformer factory** handles provider differences at build time:
- Cursor: strips all frontmatter (uses plain markdown)
- Claude Code: preserves all frontmatter, adds `allowed-tools`
- Gemini CLI: converts YAML frontmatter to TOML
- Codex CLI: wraps in custom prompt format
- GitHub Copilot: uses `.github/copilot-instructions.md` format

---

## Agent Catalog

Impeccable uses the **Agent Skills Specification** (agentskills.io). Skills are not autonomous agents — they are structured slash commands invoked on-demand. There is no fleet, no routing, no autonomous execution.

### Core Skill (foundation for all others)
**frontend-design**
- Purpose: Establish design context and direction; mandatory pre-execution for all other skills
- Tools: File reads (`.impeccable.md`, project config), codebase exploration
- Invocation: `/frontend-design` or as prerequisite step in other skills
- Key capabilities: Context Gathering Protocol (`.impeccable.md`), Design Direction framework, AI Slop Test quality gate, OKLCH color guidance, anti-pattern vocabulary

### Quality Gate Skills
**audit** — Technical scoring (0-20, 5 dimensions): Accessibility/WCAG, Performance, Theming/tokens, Responsive, Anti-Patterns. P0-P3 severity tagging. Re-auditable to track improvement.

**critique** — UX scoring (0-40, Nielsen's 10 heuristics). 4-phase workflow: critique → present → adaptive follow-up questions → action plan. Persona-driven (5 archetypes).

**polish** — Comprehensive final pass. 12 categories, all 8 interaction states (default/hover/focus/active/disabled/loading/error/success). Full checkbox methodology.

### Enhancement Skills
**overdrive** — Technically extraordinary effects (View Transitions API, WebGL, spring physics, WASM). Mandatory propose-before-build gate: 2-3 directions with trade-offs required before any code is written.

**bolder** — Amplify boring designs. Explicit AI Slop Trap warning. Typography extremes (3x-5x size jumps), dominant color (60%), spatial drama.

**delight** — Joy and personality. Anti-AI-slop loading message guide. Spring physics for micro-interactions. Sound design with opt-out.

**motion** — Animation systems. Spring physics defaults. `prefers-reduced-motion` compliance as non-negotiable.

### Fix Skills
**normalize** — Design system alignment across 8 dimensions.
**harden** — Production resilience: text overflow, i18n, error handling, edge cases.
**optimize** — Core Web Vitals, bundle optimization, layout thrashing prevention.
**typefix** / **colorfix** / **copyfix** — Targeted fixes for typography, color, and UX copy.

### Setup Skill
**teach-impeccable** — One-time project setup. Explores codebase, asks minimal targeted questions, writes `.impeccable.md`. Offers to append to main config file.

### Domain Skills
**accessibility** — WCAG AA/AAA, ARIA, keyboard navigation.
**responsive** — Breakpoint strategy, fluid typography, container queries.
**theme** — CSS custom properties, dark/light mode, semantic tokens.
**darkmode** — Dark mode implementation with OS preference detection.
**forms** — Form UX, validation, progressive disclosure.
**components** — Component library patterns, variant APIs.

---

## Feature Gap Analysis

| Feature | In pbakaus/impeccable | In BrickLayer 2.0 | Gap Level | Notes |
|---------|----------------------|-------------------|-----------|-------|
| Project context file (`.impeccable.md`) | Yes — one-time setup via `/teach-impeccable`, gating all skills | No — design context not persisted in a structured file per project | **HIGH** | BrickLayer has `project-brief.md` for campaign context but no equivalent structured design/UX context file that gates agent behavior |
| Quantitative scoring rubrics for quality | Yes — audit (0-20, 5 dimensions) and critique (0-40, 10 heuristics) with P0-P3 severity | No — agents produce qualitative findings without numeric scoring or severity tiers | **HIGH** | code-reviewer and design-reviewer produce prose; no standardized severity taxonomy |
| Persona-based UX testing framework | Yes — 5 archetypes with specific test questions and red flags, interface-type selection matrix | No | **HIGH** | uiux-master has no structured persona methodology |
| Anti-pattern detection with named vocabulary | Yes — "AI Slop Test", canonical anti-pattern list with names (Inter trap, glassmorphism trap, hero metric layout) | No — design-reviewer may catch patterns but without named vocabulary or systematic list | **HIGH** | Named patterns enable precise communication and training signal |
| Skill composition (prerequisite invocation) | Yes — every skill invokes `{{command_prefix}}frontend-design` as mandatory prep; explicit chain of skills | Partial — agents can spawn sub-agents but no `run_this_first` prerequisite contract | **HIGH** | BrickLayer sub-agent spawning is ad-hoc; no formal prerequisite declaration |
| `{{available_commands}}` auto-injection | Yes — skills inject current command list at end, enabling dynamic cross-skill recommendation | No — agents don't auto-recommend other agents using a dynamic list | **MEDIUM** | `masonry_route` exists but agents don't self-reference the fleet dynamically in their output |
| Propose-before-build gate for high-risk operations | Yes — `/overdrive` requires 2-3 directions with trade-offs confirmed before any code written | Partial — spec-writer does this at plan level; no per-skill gate | **HIGH** | No equivalent gate for high-risk coding tasks below the /plan level |
| Modular reference file architecture for skills | Yes — `reference/` subdirectory with domain `.md` files loaded alongside SKILL.md | Partial — agents can read docs/ but no standardized reference file convention per agent | **MEDIUM** | BrickLayer agents are monolithic .md files; no structured per-agent reference library |
| Structured interaction state checklist | Yes — `/polish` covers all 8 states: default/hover/focus/active/disabled/loading/error/success | No — design-reviewer has no systematic checklist of interaction states | **HIGH** | Common source of UI bugs is incomplete state coverage |
| Claude Code plugin marketplace integration | Yes — `.claude-plugin/plugin.json` + `marketplace.json` for one-click install | No | **MEDIUM** | BrickLayer could publish its skills/agents as a Claude Code plugin |
| Multi-provider build/distribution system | Yes — 10 providers, factory-based transformer, single source → multiple dist | No — BrickLayer agents are Claude-Code-specific | **LOW** | BrickLayer is intentionally Claude-specific; but the factory pattern is reusable for other purposes |
| Provider capability matrix (HARNESSES.md) | Yes — systematic documentation of frontmatter field support per provider | No — no equivalent compatibility documentation for BrickLayer agents across Claude versions | **MEDIUM** | Useful pattern for documenting which BrickLayer features work in which modes/contexts |
| Browser automation for visual verification in skills | Yes — `/overdrive` mandates using browser automation to visually verify and iterate | Partial — playwright hook exists; uiux-master can use it but no skill mandates it | **MEDIUM** | Making visual verification mandatory in UI skills would catch more regressions |
| One-time project context setup skill | Yes — `/teach-impeccable`: discovers existing context, asks only what can't be inferred, writes structured file | Partial — `/plan` writes spec.md but it's task-specific, not persistent design context | **HIGH** | A `teach-bricklayer` equivalent would initialize project-brief.md via guided questions |
| Scoring rubrics with specific level criteria | Yes — heuristics-scoring.md defines exact criteria at each score level (0-4) per heuristic | No — agents use qualitative verdicts (HEALTHY/SICK/CRITICAL) without rubric | **HIGH** | Standardized rubrics reduce inter-agent variance and enable training signal |
| i18n resilience patterns (30-40% expansion budget) | Yes — `/harden` includes RTL via CSS logical properties, 30-40% text expansion budget | No — no i18n-aware review in any BrickLayer agent | **LOW** | BrickLayer projects are primarily English-only |
| OKLCH color space guidance | Yes — throughout frontend-design and color reference files | No — design system uses hex colors throughout | **MEDIUM** | Tim's frontend philosophy doc already references OKLCH; formalizing in agents would improve output |
| Bun runtime for tooling | Yes — build system uses Bun for 2-4x speed vs Node | No — BrickLayer build tooling uses Node | **LOW** | Not urgent; BrickLayer build scripts are minimal |
| Anti-AI-slop copy guidelines for loading messages | Yes — `/delight` explicitly lists forbidden AI-cliché loading messages ("Herding pixels") | No | **MEDIUM** | BrickLayer UI agents generate generic messages; this pattern improves output quality |

---

## Top 5 Recommendations

### 1. Formalize Scoring Rubrics for Code Review and Design Review [8h, P1]

**What to build**: Extract Impeccable's P0-P3 severity taxonomy and quantitative scoring approach into BrickLayer's `code-reviewer` and `design-reviewer` agents. Specifically:
- P0 Blocking: CI fails, no merge. P1 Major: must fix before release. P2 Minor: fix in follow-up. P3 Polish: optional improvement.
- Numeric dimension scores (e.g., Security 0-4, Test Coverage 0-4, API Design 0-4, Error Handling 0-4, Performance 0-4) summing to an overall score.
- Score bands: 16-20 Excellent, 12-15 Good, 8-11 Acceptable, 4-7 Poor, 0-3 Critical.

**Why it matters**: BrickLayer's code-reviewer currently produces prose with qualitative findings. Structured severity tiers enable the claims board to route P0s to immediate human escalation, enable masonry_verify_7point to produce numeric scores, and create training signal for EMA. Rubrics reduce inter-agent variance in multi-agent consensus votes.

**Implementation sketch**: Add a `reference/severity-rubric.md` to `code-reviewer` and `design-reviewer`. Update agent prompts to score each dimension before writing prose findings. masonry_consensus_check can then aggregate numeric scores across agents rather than just verdict strings.

---

### 2. Add a Project Design Context File Pattern (`.bricklayer-design.md`) [4h, P1]

**What to build**: A `teach-bricklayer` skill that:
1. Explores the codebase for existing context (reads CLAUDE.md, project-brief.md, any existing design docs)
2. Asks 5-7 UX-focused questions about what couldn't be inferred (users, brand personality, aesthetic direction, design principles)
3. Writes structured output to `.bricklayer-design.md` in the project root
4. The `uiux-master` agent reads this file at the start of every UI task (Context Gathering Protocol)

**Why it matters**: Currently `uiux-master` infers design direction from the codebase. This produces inconsistent output across sessions — different fonts, different color choices, different aesthetic directions. The `.impeccable.md` pattern from Impeccable solves this with a one-time setup that persists across sessions. Tim's `figma-designer-guide.md` already specifies a design philosophy; the missing piece is a per-project binding of that philosophy to each specific project's brand, users, and constraints.

**Implementation sketch**: New agent `~/.claude/agents/teach-bricklayer.md`. Routing keyword: "set up design context for this project". Writes to `.bricklayer-design.md`. Update `uiux-master` to check for this file at task start.

---

### 3. Add Propose-Before-Build Gate to `/overdrive`-Equivalent Operations [3h, P2]

**What to build**: Add a "direction proposal" step to BrickLayer's `/build` workflow for tasks flagged as "high-risk implementation" (complex animations, major refactors, new architectural components). Before any code is written:
1. Developer agent presents 2-3 implementation directions with trade-offs and time estimates
2. User selects direction (or approves default)
3. Build proceeds

**Why it matters**: Impeccable's `/overdrive` gate prevents expensive misfires on technically complex features. BrickLayer's `/plan` does this at the spec level, but once `/build` starts there's no equivalent gate for individual high-risk tasks within the build. This is particularly valuable for animation/transition work where the wrong approach means a full rewrite.

**Implementation sketch**: In `spec.md` task definitions, add an optional `require_direction_approval: true` flag. The orchestrator, before spawning the developer worker for such tasks, spawns a `direction-proposer` agent that generates 2-3 options and pauses for user input via the claims board.

---

### 4. Formalize Interaction State Coverage Checklist in `uiux-master` and `code-reviewer` [2h, P2]

**What to build**: Extract Impeccable's `/polish` interaction state checklist into BrickLayer. Every UI component review must verify all 8 states are handled:
- default, hover, focus, active, disabled, loading, error, success

Add this as a verification step in:
- `code-reviewer` agent (check that each state has CSS/class coverage)
- `uiux-master` agent (check that each state has been designed)
- `masonry-tdd-enforcer.js` hook (warn if a new UI component file lacks test coverage for interaction states)

**Why it matters**: Missing interaction states are the most common source of UI bugs that pass code review. A `disabled` button that looks like an active button, a `loading` state that uses a spinner but doesn't prevent double-submission, a `focus` state that's invisible — these are caught by Impeccable's `/polish` systematically. BrickLayer's code-reviewer doesn't currently check for state completeness.

**Implementation sketch**: Add a `reference/interaction-states-checklist.md` to `uiux-master`. Update code-reviewer to include a "Interaction States" dimension in its scoring rubric (from recommendation 1). Add to masonry-tdd-enforcer.js a check: if file matches `*.tsx` and contains `<button|<input|<select`, check that test file covers focus/disabled/loading states.

---

### 5. Publish BrickLayer Agents as a Claude Code Plugin [4h, P3]

**What to build**: Create a `.claude-plugin/` directory in the BrickLayer repo with:
- `plugin.json`: maps BrickLayer's key skills (the ~20 Masonry slash commands) to the Claude Code plugin format
- `marketplace.json`: description, categories, screenshots, installation instructions
- A subset of BrickLayer agents packaged as installable skills (not the full fleet — just the most broadly useful: `/plan`, `/build`, `/verify`, `/fix`, `/ui-compose`, `/masonry-code-review`)

**Why it matters**: Impeccable has 14k GitHub stars largely because it's discoverable as a Claude Code plugin and available for one-click install. BrickLayer's slash commands are more powerful than Impeccable's skills for development workflows, but they're locked in Tim's local setup. A plugin package would make BrickLayer's development skills available to other Claude Code users, creating community feedback and contributions.

**Implementation sketch**: Use Impeccable's `.claude-plugin/` structure directly as the template. The factory/transformer pattern from Impeccable's build system could generate provider-specific versions of BrickLayer's skill files (currently Claude-Code-only). Start with plugin.json pointing to the existing `~/.claude/agents/` files.

---

## Novel Patterns to Incorporate (Future)

**HARNESSES.md / capability matrix**: A systematic document tracking which features work in which agent modes, context sizes, or Claude versions. BrickLayer could use this pattern to document: which agents work in headless (`--dangerously-skip-permissions`) mode vs interactive, which agents require MCP tools, which hooks fire in which modes.

**OKLCH for color generation in agents**: When BrickLayer's uiux-master generates color palettes, suggesting OKLCH calculations rather than hex manipulation would produce perceptually uniform scales. The color.md reference file from Impeccable is directly portable.

**Anti-pattern named vocabulary for agents**: Impeccable's named anti-patterns ("Inter trap", "hero metric layout") create a shared vocabulary that makes agent output more precise and trainable. BrickLayer could develop equivalent named patterns for common code anti-patterns that agents should catch by name rather than description.

**Cognitive load reference for UX agents**: Impeccable's `cognitive-load.md` (chunking, progressive disclosure, recognition vs recall) is a clean, portable reference that could be added to BrickLayer's uiux-master as a reference file.

**Build-time placeholder injection for multi-context agents**: Impeccable's `{{available_commands}}` placeholder injects a dynamic list at build/load time. BrickLayer's Mortar could use a similar pattern to inject the current active agent fleet list into routing prompts dynamically, rather than hardcoding agent names in prompts.

**Versioning checklist in CLAUDE.md**: Impeccable's CLAUDE.md includes a mandatory versioning checklist (4 locations that must be updated together). BrickLayer's CLAUDE.md could include equivalent checklists for operations that touch multiple synchronized files (e.g., adding a new agent requires: `agent_registry.yml` + `masonry-state.json` + skills list in Kiln + CHANGELOG.md).

# Repo Research: nicobailon/visual-explainer

**Repo**: https://github.com/nicobailon/visual-explainer
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

visual-explainer is a Claude Code / Pi / OpenAI Codex agent skill (7k stars, 479 forks) that converts AI agent output into styled, self-contained HTML pages instead of ASCII art and markdown tables. It operates entirely through prompt engineering — no server, no build step, browser-only runtime. Where it beats BrickLayer: it has a complete, battle-tested visual output layer (Mermaid diagrams with zoom/pan, magazine-quality slide decks, interactive data tables, one-click Vercel sharing, surf-cli AI image generation) that BrickLayer currently lacks entirely. Where BrickLayer beats it: BrickLayer has actual agent orchestration, a research campaign engine, memory/recall, routing infrastructure, hooks, TDD enforcement, and production-grade workflows. visual-explainer is a presentation skin; BrickLayer is an AI operating system. The gap to close: BrickLayer's research findings, synthesis reports, build summaries, and `/verify` reports are all plain markdown — this skill provides the exact templates and design system to make them browser-viewable, navigable, and beautiful.

---

## File Inventory

### Root
- `.gitignore` — ignores `node_modules/`
- `CHANGELOG.md` — full version history from v0.1.0 to v0.6.3 (37 commits, ~6 weeks of development)
- `LICENSE` — MIT
- `README.md` — installation guide, command table, architecture diagram, slide deck mode explanation
- `banner.png` — marketing banner image (1.1MB)
- `install-pi.sh` — one-command Pi installation; patches `{{skill_dir}}` to actual path, copies skill + prompts
- `package.json` — v0.6.3, `claude-code-plugin` keyword, no dependencies

### .claude-plugin/ (marketplace identity)
- `.claude-plugin/marketplace.json` — catalog for Claude Code marketplace: name, version, plugin listing, keywords, category: "visualization"
- `.claude-plugin/plugin.json` — top-level plugin: `visual-explainer-marketplace` v1.0.0

### plugins/visual-explainer/ (the actual skill)
- `plugins/visual-explainer/.claude-plugin/plugin.json` — plugin manifest: `visual-explainer` v0.6.2
- `plugins/visual-explainer/SKILL.md` — **core agent instruction file** (36KB). Contains: workflow (Think→Structure→Style→Deliver), proactive table rendering rule, 11 diagram type routing table, aesthetic palette system, anti-slop guardrails, quality checks. This is the system prompt agents read.

### plugins/visual-explainer/commands/ (8 slash commands)
- `commands/diff-review.md` — visual diff review: scope detection (branch/hash/PR/range), data gathering phase, verification checkpoint, 10-section page structure (executive summary, KPI dashboard, module architecture, feature comparisons, flow diagrams, file map, test coverage, code review, decision log, re-entry context)
- `commands/plan-review.md` — plan vs. codebase: reads plan file + all referenced files, blast radius mapping, 9-section structure (summary, impact dashboard, current architecture, planned architecture, change breakdown, ripple analysis, risk assessment, plan review, understanding gaps)
- `commands/project-recap.md` — mental model rebuild: git log + status + architecture scan, 8-section structure (identity, architecture snapshot, recent activity, decision log, state of things, mental model essentials, cognitive debt hotspots, next steps)
- `commands/fact-check.md` — claim extractor + verifier: reads HTML/markdown output, extracts quantitative/naming/behavioral/structural claims, verifies each against source code, corrects in place, adds verification summary
- `commands/generate-visual-plan.md` — implementation spec generator: parses feature request, reads codebase, designs state/API/integration/edge cases, outputs 10-section spec page
- `commands/generate-web-diagram.md` — generic HTML diagram generator: any topic, aesthetic variety, optional surf-cli image
- `commands/generate-slides.md` — slide deck generator: 4 presets, narrative arc structure, proactive surf-cli imagery, compositional variety
- `commands/share.md` — Vercel deployment: documentation for `/share` command

### plugins/visual-explainer/references/ (design system docs for agents)
- `references/css-patterns.md` — **44KB design system reference**. Covers: theme setup (CSS custom properties, light/dark), background atmosphere patterns (gradients, dot grids, diagonal lines), link styling, section/card components (`.ve-card` with 4 depth tiers: elevated/recessed/hero/glass), code blocks (with/without headers, implementation plan guidance), directory trees, overflow protection (global rules, `display:flex` on `<li>` anti-pattern), Mermaid containers (centering, scaling, zoom controls, full JS pattern with drag/pan/click-to-expand), generated image containers, status badges, KPI cards, before/after panels, SVG flow connectors, animation patterns (fadeUp, fadeScale, drawIn, countUp), collapsible sections, prose page elements
- `references/libraries.md` — **21KB library reference**. Covers: Mermaid.js (CDN, ELK layout, deep theming with `theme: 'base'`, CSS override recipes, classDef gotchas, node label special characters, layout direction TD vs LR, valid Mermaid writing rules, diagram type examples for all 7 types), Chart.js (dark/light theming, canvas wrapper), anime.js (staggered choreography, prefers-reduced-motion), Google Fonts (13 curated pairings with use-case guidance, forbidden fonts list, Typography by Content Voice table)
- `references/responsive-nav.md` — **5.8KB responsive navigation**. Sticky sidebar TOC on desktop (CSS grid 170px + 1fr), horizontal scrollable bar on mobile, IntersectionObserver scroll-spy JS, scroll-margin-top for heading offset
- `references/slide-patterns.md` — **45KB slide deck system**. Covers: planning process (source inventory → slide mapping → layout assignment), slide engine base (scroll-snap container), typography scale (2-3× larger than pages), cinematic transitions (IntersectionObserver + staggered reveals), navigation chrome (progress bar, nav dots, counter, keyboard hints), SlideEngine JavaScript class (keyboard + touch + scroll navigation, Home/End keys, event delegation to avoid conflicting with Mermaid zoom), autoFit() function (Mermaid SVG sizing, KPI overflow, blockquote font scaling), 10 slide types (Title, Section Divider, Content, Split, Diagram, CSS Pipeline, Dashboard, Table, Code, Quote, Full-Bleed), decorative SVG patterns, proactive imagery workflow (surf-cli), compositional variety rules, readability guidelines, content density limits per slide type, responsive height breakpoints (700/600/500px), 4 curated presets (Midnight Editorial, Warm Signal, Terminal Mono, Swiss Clean)

### plugins/visual-explainer/templates/ (reference HTML files)
- `templates/architecture.html` — CSS Grid card layout (17KB), terracotta/sage palette, depth tiers, flow arrows
- `templates/data-table.html` — HTML tables with KPI cards, status badges, collapsible details, rose/cranberry palette (16KB)
- `templates/mermaid-flowchart.html` — full Mermaid flowchart with zoom/pan engine, teal palette (21KB)
- `templates/slide-deck.html` — all 10 slide types in Midnight Editorial preset (35KB, the most complex template)

### plugins/visual-explainer/scripts/
- `scripts/share.sh` — deploys HTML to Vercel via `vercel-deploy` skill; extracts preview+claim URLs; outputs JSON for programmatic use

---

## Architecture Overview

The system is entirely prompt-driven. There are no servers, no MCP tools, no hooks, no compiled code.

**How it works:**
1. Agent (Claude Code, Pi, Codex) loads `SKILL.md` as a skill/context document
2. User invokes a slash command (e.g. `/diff-review`) or the skill activates proactively on complex tables
3. The agent follows SKILL.md's Think→Structure→Style→Deliver workflow:
   - **Think**: pick aesthetic direction, determine content type, identify audience
   - **Structure**: read the appropriate reference template and CSS/library docs
   - **Style**: apply font pairing + color palette + depth hierarchy
   - **Deliver**: write HTML to `~/.agent/diagrams/`, open in browser, tell user path
4. Each command `.md` file is a detailed prompt template with data-gathering, verification checkpoint, and page structure instructions
5. Reference docs (`css-patterns.md`, `libraries.md`, etc.) are read by the agent during generation — not pre-compiled
6. Output: single self-contained `.html` file (CDN-only external dependencies)
7. Optional: `share.sh` deploys to Vercel (no auth needed via vercel-deploy skill)

**Key design principles:**
- **Proactive activation**: agent intercepts would-be ASCII tables (4+ rows or 3+ columns) and renders HTML instead
- **Verification checkpoint**: every data-heavy command (diff-review, plan-review, project-recap) requires a "fact sheet" — enumerate every claim before writing HTML, cite sources, mark uncertain items
- **Anti-slop guardrails**: explicit forbidden patterns (Inter font, violet accents, gradient text, glowing shadows, emoji headers) with a 7-point "Slop Test" checklist
- **Content completeness**: slide decks require full source inventory before writing any HTML; every item must map to a slide
- **No Node.js/Python runtime**: purely HTML+CSS+JS written by the LLM at generation time

---

## Agent Catalog

### SKILL.md (the core agent instruction)
- **Purpose**: Master workflow document the LLM reads to understand how to generate visual HTML
- **Tools**: Write (file output), Bash (`open`/`xdg-open`, `which surf`, optional `git` in command files)
- **Invocation**: Loaded as a skill file; activates proactively on complex table output
- **Key unique capabilities**:
  - Aesthetic routing system: constrained (Blueprint, Editorial, Paper/ink, Terminal) vs. flexible (IDE-inspired) with explicit forbidden aesthetics
  - Diagram type routing table: 12 content types mapped to rendering approaches (Mermaid vs CSS Grid vs HTML table vs Chart.js)
  - Depth tier system: hero/elevated/default/recessed cards signaling importance hierarchy
  - Anti-slop enforcement with specific forbidden values (exact hex codes, font names)
  - Quality checks: squint test, swap test, both-themes test, no-overflow test

### diff-review.md (command)
- **Purpose**: Visual code review of git diffs
- **Key unique capabilities**:
  - Scope detection: branch, hash, HEAD, PR#, range, default-to-main
  - Verification checkpoint: fact-sheet before HTML generation
  - Decision log with confidence tiers (green=sourced, blue=inferred, amber=not recoverable) — explicit cognitive debt surfacing
  - Re-entry context section: invariants, non-obvious coupling, gotchas, follow-ups
  - Housekeeping indicators: CHANGELOG updated? docs need changes?
  - Code review: structured Good/Bad/Ugly/Questions analysis

### plan-review.md (command)
- **Purpose**: Spec/RFC review against actual codebase
- **Key unique capabilities**:
  - Blast radius mapping: what imports files being changed
  - Cross-reference plan claims vs. actual code behavior
  - Understanding gaps dashboard: count changes with/without rationale, flag pre-implementation cognitive debt
  - Current vs planned architecture Mermaid diagrams using same node names for visual diff

### project-recap.md (command)
- **Purpose**: Mental model rebuild for context-switching
- **Key unique capabilities**:
  - Time window parsing: `2w`, `30d`, `3m` → git `--since` format
  - Cognitive debt hotspots with severity indicators
  - State-of-things KPI dashboard (working/in-progress/broken/blocked counts)
  - Mental model essentials: key invariants, non-obvious coupling, gotchas, naming conventions

### fact-check.md (command)
- **Purpose**: Post-hoc accuracy verification of generated HTML/MD files
- **Key unique capabilities**:
  - Auto-detects target: most recent `.html` in `~/.agent/diagrams/` if no argument
  - 5-phase pipeline: extract → verify → correct-in-place → add-summary → report
  - Classifies claims as Confirmed/Corrected/Unverifiable
  - Corrects the file in place (surgical replacements, not regeneration)
  - Adds verification banner to HTML or `## Verification Summary` to markdown

### generate-visual-plan.md (command)
- **Purpose**: Visual implementation spec for features before coding
- **Key unique capabilities**:
  - Reads extension points: hooks, event systems, plugin architectures
  - Design phase: state machine, API design, integration design, edge cases
  - 10-section spec page with state variables, modified functions, commands/API table, edge case table, test requirements, implementation notes (callout boxes with color-coded severity)

### generate-slides.md (command)
- **Purpose**: Magazine-quality slide deck from any content
- **Key unique capabilities**:
  - Source inventory → slide mapping process prevents content dropout
  - SlideEngine.js: keyboard (Arrow/Space/PageDown/Home/End), touch swipe, scroll-snap
  - 4 curated presets with full CSS token systems
  - autoFit() for Mermaid, KPI, and blockquote overflow
  - Proactive surf-cli image generation for title/full-bleed slides

---

## Feature Gap Analysis

| Feature | In visual-explainer | In BrickLayer 2.0 | Gap Level | Notes |
|---------|--------------------|--------------------|-----------|-------|
| HTML synthesis reports for research findings | Yes — full design system with Mermaid, tables, KPIs | No — synthesis.md is plain markdown | **HIGH** | BL findings/synthesis.md are the highest-value output. Making them navigable HTML would dramatically improve readability |
| Visual diff review (before/after architecture, decision log, re-entry context) | Yes — `diff-review.md` with 10 sections, verification checkpoint, decision confidence tiers | No — no visual diff capability | **HIGH** | The decision log with confidence tiers (sourced/inferred/not-recoverable) is novel and directly applicable to BL build summaries |
| Magazine slide deck from research/spec content | Yes — `generate-slides.md`, `slide-deck.html`, SlideEngine.js, 4 presets | No | **HIGH** | BL synthesis reports and `/plan` specs could be presented as slide decks for stakeholder communication |
| Plan review (spec vs. codebase, blast radius, understanding gaps dashboard) | Yes — `plan-review.md` | BL has `/verify` but output is text | **HIGH** | Visual plan review with current/planned architecture diagrams is directly applicable to BL's `/plan` output |
| Proactive table rendering (auto-convert ASCII tables to HTML) | Yes — any 4+ row or 3+ column table triggers HTML render | No — all output is terminal text | **HIGH** | BL agents output many tables (question bank status, findings summaries, agent scores). HTML rendering would be dramatically more readable |
| Project recap / mental model snapshot | Yes — `project-recap.md` with cognitive debt hotspots | No equivalent | **MEDIUM** | Useful for BL project onboarding and session handoffs, could complement Recall |
| Fact-check / claim verification pass | Yes — `fact-check.md` corrects-in-place | BL has `/verify` but doesn't verify its own generated documents | **MEDIUM** | Running fact-check against BL's synthesis.md or build summaries would catch hallucinated findings |
| Self-contained HTML output (no server needed) | Yes — single `.html` file, CDN-only | No | **HIGH** | BL could write findings as `.html` files alongside `.md` files; browser opens immediately |
| Instant sharing via Vercel | Yes — `share.sh` + `vercel-deploy` skill | No | **MEDIUM** | Sharing BL research findings with stakeholders as a live URL is high-value |
| Visual implementation plan (feature spec page) | Yes — `generate-visual-plan.md` | `/plan` writes spec.md | **MEDIUM** | BL's autopilot spec.md could optionally generate a visual plan page |
| Mermaid diagram system (zoom/pan, multi-diagram, dark/light themes) | Yes — complete system with 200-line JS engine | No — any Mermaid in BL output is in markdown (not rendered) | **HIGH** | BL architecture docs, campaign flow diagrams, routing diagrams could be interactive HTML |
| Anti-slop design guardrails | Yes — explicit forbidden patterns with exact hex codes, 7-point slop test | No — BL has UI design standards in CLAUDE.md but not for agent-generated reports | **MEDIUM** | BL's visual output quality (when built) benefits from these constraints |
| Depth tier system (hero/elevated/default/recessed) | Yes — CSS depth tiers signaling importance | No | **LOW** | Component-level pattern; useful when building BL HTML output layer |
| Font pairing library with anti-slop enforcement | Yes — 13 curated pairings, forbidden list | No | **LOW** | Reference material for BL's HTML output |
| surf-cli AI image generation integration | Yes — `which surf`, base64 embed workflow | No | **LOW** | Nice-to-have for hero banners on BL reports |
| Responsive navigation (sticky TOC + mobile horizontal bar) | Yes — `responsive-nav.md` | No | **LOW** | For multi-section BL reports |
| Slide engine JavaScript (SlideEngine class) | Yes — complete with keyboard, touch, scroll-snap | No | **MEDIUM** | `/generate-slides` equivalent for BL specs/findings |
| Cognitive debt surfacing in reviews | Yes — decision confidence tiers, understanding gaps dashboard, hotspots | No | **HIGH** | BL `/verify` and code-reviewer agent could adopt this pattern |
| Content completeness enforcement (inventory → slide mapping) | Yes — structured pre-generation process | No | **MEDIUM** | Prevents BL synthesis from silently dropping findings |
| Verification checkpoint before output generation | Yes — fact-sheet before HTML generation | Partial — `/verify` reads spec | **MEDIUM** | BL agents could adopt the "enumerate every claim, cite source" checkpoint before writing findings |

---

## Top 5 Recommendations

### 1. BrickLayer HTML Synthesis Reports [8h, HIGH PRIORITY]

**What to build:** A `synthesizer-html` variant (or `--html` flag on the synthesizer agent) that produces a self-contained HTML synthesis report alongside `findings/synthesis.md`. Use visual-explainer's template patterns: hero executive summary section, KPI dashboard (questions answered/verdicts/confidence distribution), per-finding cards organized by verdict (FAIL/WARN/HEALTHY), Mermaid failure boundary map, and cognitive debt hotspots for low-confidence findings.

**Why it matters:** `synthesis.md` is the highest-value BL output and currently the hardest to read — it's a wall of markdown headers. An HTML version with sticky navigation, collapsible sections, status badges, and a Mermaid diagram of the failure boundary map would be dramatically more useful for Tim and stakeholders. This is also the most direct lift from visual-explainer: the templates are already designed for exactly this use case.

**Implementation sketch:**
- Add `--html` flag to the `synthesizer` agent
- Write `masonry/agents/synthesizer-html.md` that follows visual-explainer's SKILL.md workflow
- Reference templates: `data-table.html` for findings table, `architecture.html` for failure boundary map, `mermaid-flowchart.html` for verdict distribution
- Output: `findings/synthesis.html` alongside `findings/synthesis.md`
- Auto-open in browser after campaign completes

### 2. Visual Diff Review for Build Summaries [6h, HIGH PRIORITY]

**What to build:** Port `diff-review.md` as a Masonry skill (`/masonry-diff-review`) that runs automatically after each `/build` task completion. The decision log with confidence tiers is the most novel pattern — sourced rationale (green, from spec/commit), inferred (blue), or not recoverable (amber = cognitive debt warning). The re-entry context section (invariants, non-obvious coupling, gotchas) maps directly to what BL's code-reviewer agent should surface.

**Why it matters:** BL's build summaries are currently just task completion status. A visual diff review page per build cycle would make every commit's "why" traceable — exactly what the decision log pattern provides. The "re-entry context" section solves a real BL problem: long campaigns generate cognitive debt as earlier decisions get buried.

**Implementation sketch:**
- Add a `diff-review-html` post-commit hook or add as an optional step in the build orchestrator
- Adapt `diff-review.md`'s scope detection to BL's branch convention (`autopilot/project-name-YYYYMMDD`)
- Add decision confidence tier system to `code-reviewer` agent output schema
- Write to `reports/diff-review-TASK_ID.html`

### 3. Plan Review Visual Output for /plan [4h, HIGH PRIORITY]

**What to build:** After `spec-writer` writes `.autopilot/spec.md`, run a visual plan review that generates a `.autopilot/spec-review.html` showing: current architecture Mermaid diagram of affected subsystem, planned architecture Mermaid diagram with new/changed nodes highlighted, blast radius table (what imports affected files), understanding gaps dashboard (changes with/without rationale), and risk assessment cards.

**Why it matters:** BL's `.autopilot/spec.md` is approved by Tim before `/build` runs. Currently Tim reads raw markdown to find gaps. A visual plan review surfaces missing rationale and blast radius issues before the build starts — when they're cheapest to fix. The "understanding gaps dashboard" from `plan-review.md` is novel: count changes where the plan explains WHY vs. just WHAT.

**Implementation sketch:**
- Add optional `--visual` flag to `/plan`
- After `spec-writer` completes, run a `plan-reviewer-html` agent
- Use `plan-review.md`'s structure directly, adapted to BL's spec.md format
- Output: `.autopilot/spec-review.html`

### 4. Proactive HTML Table Rendering in Agent Output [3h, MEDIUM PRIORITY]

**What to build:** Add a `masonry-table-renderer.js` PostToolUse hook (fires after Write/Edit to `questions.md`, `findings/`, `masonry-state.json`) that detects markdown tables in agent output and auto-generates an HTML companion. Threshold: 4+ rows or 3+ columns. Write to `~/.agent/diagrams/{source-filename}-table.html` and print the path.

**Why it matters:** BL agents produce many complex tables: question bank status (dozens of rows × multiple status columns), agent performance scores (fleet × metrics), findings comparison matrices. These are currently only readable in a text editor. This is the lightest-weight win — a hook that intercepts table output costs 2-3 hours and immediately improves every campaign's readability.

**Implementation sketch:**
- Port visual-explainer's proactive table rendering threshold (4+ rows or 3+ columns)
- Reference `data-table.html` template for output format
- Hook fires on PostToolUse for `questions.md` and `results.tsv` writes
- Status badges: PENDING=gray, IN_PROGRESS=amber, DONE=green, FAILED=red (maps directly to BL's status values)

### 5. `/bl-slides` Skill for Campaign Findings Presentations [5h, MEDIUM PRIORITY]

**What to build:** A `/bl-slides` skill that takes a `synthesis.md` or `spec.md` and generates a magazine-quality slide deck using visual-explainer's SlideEngine + slide-patterns system. Targeted at presenting BL research findings to stakeholders (Tim sharing ADBP findings, campaign summaries for the team, etc.).

**Why it matters:** BL campaigns produce valuable findings that are hard to communicate outside a technical context. A slide deck from synthesis.md — with verdict dashboard, failure boundary diagram, key findings per domain, and risk heat map — would make BL's research output presentable to non-technical stakeholders. The slide patterns (Terminal Mono preset fits BL's aesthetic) are directly usable.

**Implementation sketch:**
- Write `masonry/skills/bl-slides.md` following visual-explainer's `generate-slides.md` pattern
- Adapt to BL content: Title (campaign name + question count), Verdict Dashboard (FAIL/WARN/HEALTHY counts), Domain sections (one divider + content slides per domain), Key Findings (split slides with evidence), Failure Boundary Map (Mermaid diagram slide), Risk Assessment (dashboard slide), Recommendations (content slides)
- 4 slide presets map well to BL contexts: Terminal Mono (technical), Midnight Editorial (stakeholder), Swiss Clean (analytical)
- Write to `reports/{project}-findings.html`

---

## Novel Patterns to Incorporate (Future)

**Decision confidence tiers in code review.** The three-tier system (green=sourced from conversation/docs, blue=inferred from code, amber=not recoverable) for labeling design rationale is elegant and directly applicable to BL's `code-reviewer` and `synthesizer` agents. Amber cards are explicit cognitive debt: "document the reasoning before committing." This pattern could be incorporated into BL's findings schema (`FindingPayload`) as a `rationale_confidence` field.

**Verification checkpoint before report generation.** The "fact sheet" pattern from `diff-review.md` and `plan-review.md` — enumerate every claim you will make, cite the source, mark uncertain items — is a low-cost hallucination reduction technique applicable to all BL agents that write findings. The quantitative-analyst and regulatory-researcher agents would benefit most.

**Content completeness enforcement.** The slide deck planning process (Step 1: inventory, Step 2: map every item, Step 3: verify nothing unmapped) prevents silent content dropout. BL's synthesizer could adopt the same pattern: "enumerate all N findings before writing synthesis.md, verify all N appear in the output."

**autoFit() for dynamic content.** The unified post-render function that handles Mermaid SVG sizing, KPI overflow, and blockquote font scaling is a useful pattern for any BL HTML output that includes dynamically-sized content. Particularly relevant if BL's Kiln dashboard ever renders agent-generated HTML inline.

**CSS Pipeline Slide pattern.** The CSS-based pipeline visualization (flex steps with arrow connectors) is a cleaner alternative to Mermaid for simple linear flows. BL's campaign wave progression (Wave 1 → questions → synthesis → Wave 2) and the SPARC pipeline (/plan → /pseudocode → /architecture → /build → /verify → /fix) would render beautifully as CSS pipeline slides without Mermaid's sizing issues.

**Aesthetic rotation discipline.** The explicit rule "if the last diagram was dark and technical, make the next one light and editorial" prevents visual monotony across multiple generated pages. BL could adopt this for its HTML report output — vary the preset per report type (synthesis=Midnight Editorial, diff-review=Terminal Mono, plan-review=Swiss Clean).

**`{{skill_dir}}` template variable pattern.** The install script that patches `{{skill_dir}}` to the actual path at install time is a clean way to handle self-referential skill paths. BL's agents that reference their own files could use the same pattern.

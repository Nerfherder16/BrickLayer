# Visual + UI Design Tools Analysis

**Repos Researched**:
- https://github.com/nicobailon/visual-explainer (6.9K stars)
- https://github.com/Dammyjay93/interface-design (4.3K stars)
- https://github.com/pbakaus/impeccable (13.4K stars)

**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and prompt patterns for BrickLayer 2.0's uiux-master agent and /ui-* skills

---

## nicobailon/visual-explainer

### What it does (exact skill implementation)

visual-explainer is a Claude Code plugin/skill that replaces terminal ASCII output with self-contained HTML pages. It has two core behaviors:

1. **Proactive table rendering**: When the agent is about to print a table with 4+ rows or 3+ columns, it silently generates an HTML page instead and tells the user the file path. No user prompt needed.
2. **On-demand visualization**: 8 slash commands that produce architecture diagrams, diff reviews, plan audits, slide decks, project recaps, and fact-checks — all as browser-openable HTML files written to `~/.agent/diagrams/`.

The SKILL.md is 36,895 bytes — by far the most detailed skill file of the three repos. It is effectively a design system for AI-generated documentation pages.

**File structure**:
```
plugins/visual-explainer/
  SKILL.md                  — 37KB master skill (workflows, aesthetics, diagram type routing)
  commands/
    diff-review.md          — 8.5KB: git diff → HTML review with KPIs, Mermaid, code review sections
    plan-review.md          — 9.4KB: spec file vs. codebase → HTML audit with risk assessment
    project-recap.md        — 7.2KB: git log + codebase → HTML mental model snapshot
    generate-visual-plan.md — 7.0KB: feature → HTML implementation plan
    fact-check.md           — 4.7KB: document vs. code → accuracy verification
    generate-slides.md      — 2.0KB: slide deck mode entry point
    generate-web-diagram.md — 0.9KB: generic diagram
    share.md                — 1.4KB: Vercel deploy
  references/
    css-patterns.md         — 44KB: layout patterns, animations, SVG connectors
    libraries.md            — 21KB: Mermaid theming, Chart.js, font pairings, CDN imports
    slide-patterns.md       — 45KB: slide engine, 4 presets, 10 slide types
    responsive-nav.md       — 5.8KB: sticky TOC pattern for multi-section pages
  templates/
    architecture.html       — CSS Grid card layout reference
    mermaid-flowchart.html  — Mermaid with zoom/pan/expand controls
    data-table.html         — Sticky-header table reference
    slide-deck.html         — 35KB: full slide engine reference
```

### HTML generation patterns

The skill enforces a precise decision tree for every diagram:

**Diagram type routing** (hardcoded):
- Flowchart/pipeline/sequence/ER/state machine/mind map/class diagram → Mermaid
- Architecture with rich card content (descriptions, code, tool lists) → CSS Grid cards
- Architecture 15+ elements → Hybrid (Mermaid overview + CSS Grid detail cards)
- Data tables → `<table>` with sticky `<thead>`, alternating rows, status indicator spans (never emoji)
- Dashboard → CSS Grid + Chart.js
- Timeline → CSS pseudo-element line + cards

**Mermaid discipline** (specific, load-bearing rules):
- Always `theme: 'base'` with custom `themeVariables` — never use default themes
- Always `layout: 'elk'` for complex graphs
- Never bare `<pre class="mermaid">` — always use the full `diagram-shell` pattern with zoom/pan/fit/expand controls (~200 lines of JS)
- Prefer `graph TD` (top-down) over `graph LR` — LR breaks at many nodes
- Use `<br/>` for line breaks in labels, never `\n`
- Never define `.node` as a page-level CSS class — Mermaid uses it internally

**Self-containment rules**: All output is a single `.html` file. No external assets except CDN fonts. CSS custom properties for the full palette. All scripts inline.

**Forbidden aesthetics** (explicitly blacklisted in the SKILL.md):
- Neon dashboard (cyan + magenta + purple on dark) — called "always produces AI slop"
- Gradient mesh (pink/purple/cyan blobs)
- Inter font + violet/indigo accents + gradient text
- Emoji in section headers
- Three-dot window chrome on code blocks
- Animated glowing box-shadows (`@keyframes glow`)
- Gradient text on headings (`background-clip: text`)

**Required aesthetics** (constrained, specific):
- Blueprint: technical drawing feel, deep slate/blue, monospace labels
- Editorial: Instrument Serif or Crimson Pro, generous whitespace, muted earth tones
- Paper/ink: warm cream `#faf7f5`, terracotta/sage accents
- Monochrome terminal: green/amber on near-black
- IDE-inspired: must use a real named scheme (Dracula, Nord, Catppuccin, Solarized, Gruvbox) — no approximations

**Good accent palettes** (explicitly curated):
- Terracotta + sage (`#c2410c`, `#65a30d`)
- Teal + slate (`#0891b2`, `#0369a1`)
- Rose + cranberry (`#be123c`, `#881337`)
- Amber + emerald (`#d97706`, `#059669`)
- Deep blue + gold (`#1e3a5f`, `#d4a73a`)

Forbidden accent colors: `#8b5cf6`, `#7c3aed`, `#a78bfa` (Tailwind purple range), `#d946ef` (fuchsia), the cyan-magenta-pink neon combo.

**The slop test** (7 telltale AI-generated signals to check before shipping):
1. Inter or Roboto font with purple/violet gradient accents
2. Every heading has `background-clip: text` gradient
3. Emoji icons leading every section
4. Glowing cards with animated shadows
5. Cyan-magenta-pink color scheme on dark background
6. Perfectly uniform card grid with no visual hierarchy
7. Three-dot code block chrome

If two or more are present, regenerate with a constrained aesthetic.

**The swap test**: "If you replaced your styling with a generic dark theme and nobody would notice the difference, you haven't designed anything."

### diff-review command in detail

The diff-review command is the most sophisticated. Its workflow:

1. **Scope detection**: Parses `$1` as branch name, commit hash, `HEAD`, PR number (`#42`), range (`abc..def`), or defaults to `main`
2. **Data gathering**: Runs `git diff --stat`, `--name-status`, line counts, grepped API surface (exported symbols), feature inventory
3. **Verification checkpoint**: Before generating HTML, produces a fact sheet of every quantitative claim with source citations. Marks uncertain claims rather than stating as fact.
4. **10-section HTML page**:
   - Executive summary (hero depth, larger type, accent-tinted background)
   - KPI dashboard (lines added/removed, CHANGELOG.md update badge, docs badge)
   - Module architecture (Mermaid dependency graph with full zoom/pan controls)
   - Major feature comparisons (before/after side-by-side)
   - Flow diagrams
   - File map (collapsible)
   - Test coverage
   - Code review — Good/Bad/Ugly/Questions with styled cards
   - Decision log — each decision tagged High/Medium/Low confidence (sourced vs. inferred vs. not recoverable)
   - Re-entry context — invariants, non-obvious coupling, gotchas, follow-up work

**The decision log with confidence tagging is the most novel pattern**: High confidence (green border) = rationale sourced from conversation/docs. Medium (blue, "inferred") = inferred from code structure. Low (amber) = "rationale not recoverable — document before committing." Low-confidence entries are called "cognitive debt hotspots."

### plan-review command in detail

Compares a spec file (`$1`) against the actual codebase:
- Cross-references every file the plan mentions against actual code
- Maps "blast radius" — what imports the files being changed, what tests exist
- Produces a "understanding gaps" dashboard: count of changes with clear rationale vs. missing rationale, cognitive complexity flags, explicit pre-implementation recommendations
- Risk assessment cards with severity indicators: edge cases, ordering risks, rollback complexity, cognitive complexity (distinct from bug risk — "you'll forget how this works in a month" risks)

### project-recap command in detail

Time-windowed mental model snapshot (`/project-recap 2w`):
- Parses time shorthand (`2w`, `30d`, `3m`) to git `--since` format
- 8-section page: project identity, architecture snapshot, recent activity (narrative grouped by theme, not raw git log), decision log, state-of-things KPI dashboard, mental model essentials (5-10 things to hold in head), cognitive debt hotspots, next steps
- Cognitive debt hotspots section: amber-tinted cards with severity indicators, specific suggestions like "add a doc comment to `buildCoordinationInstructions` explaining the 4 coordination levels"

### Specific skills to add to BrickLayer (/visual-report, /visual-diff)

**HIGH PRIORITY**:

`/visual-diff` — a BrickLayer command that wraps the diff-review workflow. Trigger: after any `/build` or `/fix` completes, or on demand. Output: HTML page at `~/.agent/diagrams/` opened in browser. Includes the decision log with confidence tagging, which would directly serve BrickLayer's synthesis/findings use case.

`/visual-plan` — wraps the plan-review workflow. Trigger: after `/plan` generates `.autopilot/spec.md`, offer to generate a visual audit of the spec against the codebase. The "understanding gaps" dashboard would catch missing rationale before the build starts.

`/visual-recap` — wraps the project-recap workflow. Trigger: at session start when resuming a project, or on demand. The cognitive debt hotspot tracking would complement BrickLayer's existing EMA training pipeline.

**MEDIUM PRIORITY**:

Auto-table-to-HTML: When the research loop or synthesizer would render a large table in findings, render HTML instead. This is the "proactive table rendering" behavior — threshold 4+ rows or 3+ columns.

### Exact prompt text worth adopting

**The verification checkpoint pattern** (from diff-review.md) — use this before any HTML generation or any claims-heavy output:
> "Before generating HTML, produce a structured fact sheet of every claim you will present: every quantitative figure, every function/module name, every behavior description. For each, cite the source. Verify each claim against the code. If something cannot be verified, mark it as uncertain rather than stating it as fact."

**The decision log confidence tagging pattern**:
> "For each significant design choice: Decision (one-line), Rationale (why — pull from conversation if available, infer from code structure if not), Alternatives considered, Confidence: High (sourced from conversation/docs, green border), Medium (inferred from code, blue border labeled 'inferred'), Low (not recoverable, amber border, 'rationale not recoverable — document before committing' warning)."

**The re-entry context pattern** (from diff-review.md):
> "Include a 'note from present-you to future-you' covering: key invariants (assumptions the changed code relies on that aren't enforced by types or tests), non-obvious coupling (files or behaviors connected in ways not visible from imports), gotchas (things that would surprise someone modifying this code in two weeks), don't forget (follow-up work required)."

**The aesthetic forcing function**:
> "Vary the choice each time. If the last diagram was dark and technical, make the next one light and editorial. The swap test: if you replaced your styling with a generic dark theme and nobody would notice the difference, you haven't designed anything."

---

## Dammyjay93/interface-design

### Core mechanism (how it enforces UI consistency)

interface-design is a Claude Code skill + 5 commands that enforces UI consistency through a persistent `.interface-design/system.md` file. The mechanism:

**Session 1 (no system.md)**:
1. Skill reads SKILL.md and principles.md
2. Agent explores project domain (5+ concepts, 5+ colors from the domain's physical world, one signature element unique to this product, 3 obvious defaults to reject)
3. Agent proposes direction, gets confirmation
4. States design choices before each component (Intent, Palette, Depth, Surfaces, Typography, Spacing — all with explicit WHY)
5. Builds with consistent principles
6. Offers to save: "Want me to save these patterns to `.interface-design/system.md`?"

**Session 2+ (system.md exists)**:
1. Loads system.md automatically
2. Applies established patterns without re-asking
3. Checks all new code against system rules
4. Offers to save any new patterns discovered

The system.md file captures: direction/personality, spacing base, color tokens (as CSS variable names, not hex), depth strategy, specific component patterns (Button: 36px h / 12px 16px padding / 6px radius, Card: 1px border / 16px padding).

**Commands**:
- `/interface-design:init` — build UI with craft (reads skill, checks system.md, suggests direction)
- `/interface-design:audit <path>` — check code against system.md for spacing/depth/color/pattern violations
- `/interface-design:extract` — scan existing code, count repeated spacing/radius/button/card patterns by frequency, propose system.md from actual usage
- `/interface-design:status` — show current system state
- `/interface-design:critique` — post-build craft review (see below)

**The audit command** checks specifically:
- Spacing values not on the defined grid (e.g., 17px when base is 4px)
- Depth strategy violations (shadow found when system is borders-only)
- Color violations (colors not in defined palette)
- Pattern drift (Button height 38px when pattern specifies 36px)

**The extract command** is reverse-engineering: scans all `.tsx/.jsx/.css/.scss` files, counts repeated values, proposes system.md based on frequency. "Found: 4px (12x), 8px (23x), 16px (31x) → Suggests: Base 4px." This is zero-config onboarding for existing codebases.

### What's novel vs BrickLayer's existing UI rules

**What BrickLayer has**: `frontend-design-philosophy.md` covers color system, typography, surfaces, layout, components, spacing, motion, accessibility. It is a static rule file read by the uiux-master agent. `tokens.json` stores the design tokens. `/ui-review` does design compliance checking.

**What interface-design adds that BrickLayer lacks**:

1. **Domain exploration before any code**: The skill explicitly requires producing domain concepts, color world, signature element, and defaults-to-reject before proposing any direction. The "color world" question is unique: "What colors exist naturally in this product's domain? Not 'warm' or 'cool' — go to the actual world. If this product were a physical space, what would you see?" This generates palette concepts from the product's world, not from aesthetic preferences.

2. **Mandatory WHY justification for every choice**: Before writing each component, the agent states Intent/Palette/Depth/Surfaces/Typography/Spacing with explicit WHY for each. "Why this color temperature?" "Why this typeface?" If the answer is "it's common" or "it works," that signals a default, not a decision.

3. **The four critique checks** (run before showing user):
   - Swap test: If you swapped the typeface for your usual one, would anyone notice?
   - Squint test: Blur your eyes. Can you still perceive hierarchy?
   - Signature test: Can you point to five specific elements where your signature appears?
   - Token test: Read your CSS variables out loud — do they sound like they belong to this product?

4. **Persistent design system memory across sessions** via `.interface-design/system.md` — BrickLayer has `tokens.json` and `.ui/design-brief.md` but no equivalent of the session-to-session decision persistence with rationale tracking.

5. **The `/extract` command** — reverse-engineering design patterns from existing code by frequency counting. BrickLayer has no equivalent.

6. **"Be invisible" communication rule**: "Never say: 'I'm in ESTABLISH MODE.' Instead: jump into work. State suggestions with reasoning." BrickLayer's uiux-master could drift into narrating its process.

7. **Sidebar grounding insight** (from principles.md): "Sidebars should use the same background as the canvas, not different. Different colors fragment the visual space into 'sidebar world' and 'content world.' A subtle border is enough separation." — This directly contradicts some common patterns and is worth explicit codification.

8. **The sameness failure test**: "If another AI, given a similar prompt, would produce substantially the same output — you have failed." This is a stronger constraint than "avoid generic templates."

9. **Control token separation**: "Form controls have specific needs. Don't reuse surface tokens — create dedicated ones for control backgrounds, control borders, and focus states." BrickLayer's token system doesn't distinguish control tokens from surface tokens.

### Items to adopt

**HIGH PRIORITY**:

1. **Domain exploration protocol** — add to uiux-master's init flow. Before any design work: produce 5+ domain concepts, 5+ domain colors (from the physical world of the product), one signature element, 3 defaults to explicitly reject. Format matches interface-design's proposal structure.

2. **Mandatory WHY checkpoint before each component** — uiux-master should state Intent/Palette/Depth/Surfaces/Typography/Spacing with WHY before writing code. This is a lightweight discipline that catches defaulting before it reaches the output.

3. **The four post-build checks** (swap, squint, signature, token) — add to `/ui-review` as a structured checklist that runs before the review report is generated.

4. **Persistent system.md** — BrickLayer already has `.ui/design-brief.md` and `tokens.json`. The gap is that interface-design's system.md captures specific component patterns with exact measurements (Button: 36px h / 12px 16px padding / 6px radius) and decision rationale. BrickLayer's `tokens.json` only captures values, not decisions.

5. **"Be invisible" directive** — explicitly prohibit uiux-master from narrating mode transitions ("I'm now in design phase..."). The skill should jump to work.

**MEDIUM PRIORITY**:

6. **Extract command** — `/ui-extract` that scans existing code by frequency to bootstrap a design system from a legacy codebase.

7. **Sidebar same-background rule** — add to `frontend-design-philosophy.md` explicitly.

8. **Control token separation** — add to `tokens.json` schema: dedicated `control.bg`, `control.border`, `control.focus` tokens distinct from surface tokens.

---

## pbakaus/impeccable

### Design language rules

impeccable (13.4K stars) is the most popular of the three. It builds on Anthropic's official frontend-design skill with 7 domain-specific reference files and 20 steering commands. It targets all major AI harnesses (Claude Code, Cursor, Gemini CLI, Codex, Kiro, OpenCode, Trae, Pi, VS Code Copilot).

**Architecture**: Source files in `source/` with YAML frontmatter, build system (Bun) transforms to provider-specific formats in `dist/`. Claude Code gets full YAML frontmatter. Cursor gets stripped frontmatter (no args support). Gemini gets TOML. Codex gets custom prompt format. This multi-provider architecture is its most distinctive engineering contribution.

**The frontend-design SKILL.md** (9.6KB) is the foundation:

Key additions over Anthropic's original:
- **Context Gathering Protocol**: Check loaded instructions for Design Context section → check `.impeccable.md` → run `teach-impeccable`. MUST have confirmed design context before any design work. "You cannot infer this context by reading the codebase — code tells you what was built, not who it's for or what it should feel like."
- **The AI Slop Test**: "If you showed this interface to someone and said 'AI made this,' would they believe you immediately? If yes, that's the problem."
- **Anti-pattern catalog** with DO/DON'T pairs organized by domain (Typography, Color, Layout, Visual Details, Motion, Interaction, Responsive, UX Writing)
- **Explicit forbidden patterns not in BrickLayer's rules**:
  - "Don't wrap everything in cards — not everything needs a container"
  - "Don't nest cards inside cards — visual noise, flatten the hierarchy"
  - "Don't use the hero metric layout template — big number, small label, supporting stats, gradient accent" (this pattern is explicitly in BrickLayer's design philosophy as a KPI card pattern)
  - "Don't center everything — left-aligned text with asymmetric layouts feels more designed"
  - "Don't use glassmorphism everywhere — blur effects, glass cards, glow borders used decoratively rather than purposefully"
  - "Don't use rounded rectangles with generic drop shadows — safe, forgettable, could be any AI output"
  - "Don't put large icons with rounded corners above every heading — makes sites look templated"
  - "Don't default to dark mode with glowing accents — it looks 'cool' without requiring actual design decisions"
  - "Don't use gray text on colored backgrounds — use a shade of the background color instead"
  - "Don't use pure black (#000) or pure white (#fff) — always tint"

**The teach-impeccable skill**: One-time setup that scans the codebase (README, package.json, existing components, design tokens) then asks UX-focused questions (users, brand personality, aesthetic preferences, accessibility). Saves a `## Design Context` section to `.impeccable.md` and optionally to `CLAUDE.md`. Every other skill checks for this context before proceeding.

**The critique skill** (10.9KB) — most sophisticated of any critique command across the three repos:

10-dimension evaluation framework:
1. AI Slop Detection (CRITICAL — first check)
2. Visual Hierarchy
3. Information Architecture & Cognitive Load (includes cognitive load 8-item checklist, >4 choices at a decision point = flag)
4. Emotional Journey (peak-end rule, emotional valleys, interventions at negative moments like payment/delete)
5. Discoverability & Affordance
6. Composition & Balance
7. Typography as Communication
8. Color with Purpose
9. States & Edge Cases
10. Microcopy & Voice

**Nielsen's 10 heuristics scoring table** (0-4 per heuristic, presented as a table, "most real interfaces score 20-32"):
```
| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | ? | ... |
...
| Total | | ??/40 | [Rating band] |
```

**Persona-based testing**: Auto-selects 2-3 relevant personas, generates 1-2 project-specific personas from teach-impeccable context. Each persona walks through primary user action with specific red flags ("Alex (Power User): No keyboard shortcuts detected. Form requires 8 clicks for primary action. High abandonment risk.").

**The polish skill** (8.1KB): Systematic final pass with 9 dimensions (visual alignment, typography, color/contrast, interaction states, micro-interactions, content/copy, icons/images, forms/inputs, edge cases/error states) and a 20-item checklist. Key constraint: "Polish before it's functionally complete" is explicitly forbidden.

**The overdrive skill** (9.7KB): Pushes interfaces with technically ambitious implementations — WebGL shaders, View Transitions API morphing, scroll-driven animations, spring physics, WebGPU, virtual scrolling for 100k+ rows, Web Workers, OffscreenCanvas, WASM. **Must propose 2-3 directions before any code** (highest misfire potential). Progressive enhancement is non-negotiable — every technique needs a fallback. The "wow test" / "removal test" / "device test" / "accessibility test" / "context test" before shipping.

**The 7 reference files** in `source/skills/frontend-design/reference/`:

- `typography.md`: OKLCH-aware, vertical rhythm as base unit for ALL vertical spacing, modular scale with 5 sizes (xs/sm/base/lg/xl+), fluid type via `clamp()` for marketing pages only (NOT for app UIs/dashboards — fixed rem scales), OpenType features (`tabular-nums`, `diagonal-fractions`, `all-small-caps`), fallback font metrics via `size-adjust`/`ascent-override`/`descent-override`
- `color-and-contrast.md`: Stop using HSL — use OKLCH. Tinted neutral trap (add 0.01 chroma to all grays toward brand hue). The 60-30-10 rule applied correctly (about visual weight, not pixel count). "Alpha is a design smell" — heavy transparency use means an incomplete palette.
- `spatial-design.md`: Container queries `@container` for component-level responsiveness
- `motion-design.md`: Exponential easing (ease-out-quart/quint/expo), never bounce/elastic easing in professional interfaces, grid-template-rows transitions for height animations instead of animating height directly
- `responsive-design.md`: Container queries, fluid design
- `interaction-design.md`: Progressive disclosure pattern, optimistic UI
- `ux-writing.md`: Empty states that teach the interface, not just "nothing here"

### Specific patterns to add to uiux-master or frontend-design-philosophy.md

**Priority: HIGH**

1. **OKLCH color space** — Replace HSL with OKLCH in `frontend-design-philosophy.md`. Current rules use hex values (`#0f0d1a`, `#38bdf8`). OKLCH is perceptually uniform — equal steps in lightness look equal. The key insight: "As you move toward white or black, reduce chroma. High chroma at extreme lightness looks garish." Add the tinted neutral rule: always add `oklch(... 0.01 [brand-hue])` chroma to all neutral grays — even 0.01 creates subconscious brand cohesion. `BrickLayer.frontend-design-philosophy.md` currently uses pure hex and doesn't address OKLCH at all.

2. **Fluid type only for marketing** — Current `frontend-design-philosophy.md` doesn't distinguish when to use `clamp()` vs fixed rem scales. Add: use fluid type (`clamp()`) for marketing/content pages where text dominates. Use fixed rem for app UIs, dashboards, data-dense interfaces — "no major design system (Material, Polaris, Primer, Carbon) uses fluid type in product UI."

3. **AI slop detection as a named, structured check** — The "slop test" should be a required self-check in uiux-master before any output is shown. The specific 7 tells (Inter + purple gradient, background-clip text, emoji section headers, glowing cards, cyan-magenta-pink, uniform grid, three-dot chrome) should be named. BrickLayer's anti-patterns section exists but isn't framed as a pre-delivery gate.

4. **Forbidden patterns missing from BrickLayer's rules**:
   - "Don't use gray text on colored backgrounds — use a shade of the background color or transparency instead"
   - "Don't nest cards inside cards"
   - "Don't center everything — left-aligned text with asymmetric layouts feels more designed"
   - "Don't use gradient text on headings — decorative rather than meaningful"
   - "Don't use pure black (#000) — always tint; pure black never appears in nature"
   - "Don't use glassmorphism decoratively" (BrickLayer actively promotes glass cards — this is in tension)

5. **Emotional valley design** — From critique.md's "Emotional Journey" dimension: "Check for onboarding frustration, error cliffs, feature discovery gaps, or anxiety spikes at high-stakes moments (payment, delete, commit). Are there design interventions where users are likely to feel frustrated or anxious?" Add to uiux-master's review checklist.

6. **Context Gathering Protocol** — Mirror impeccable's teach-impeccable workflow. Before any design work, uiux-master must have: target audience, use cases, brand personality/tone. Currently BrickLayer's `/ui-init` is interactive but not gated on context acquisition.

**Priority: MEDIUM**

7. **Nielsen heuristics scoring** — Add to `/ui-review` output format. The 0-4 score per heuristic with a total table is a concrete, auditable quality signal that BrickLayer currently lacks. "Most real interfaces score 20-32" sets realistic expectations.

8. **Persona-based critique** — When running `/ui-review`, auto-select 2-3 personas (Power User, First-Timer, Accessibility User, Mobile User, etc.) and walk through their primary action, listing specific red flags per persona.

9. **Overdrive capability** — BrickLayer has no equivalent of `/overdrive`. The pattern of "propose 2-3 directions before building, require progressive enhancement, test with wow/removal/device/accessibility/context tests" is worth adding for advanced UI requests. Relevant techniques: View Transitions API morphing, scroll-driven animations, virtual scrolling for large datasets, `@property` for animating CSS custom properties.

10. **OpenType features reference** — Add to `frontend-design-philosophy.md`: `tabular-nums` for data columns, `diagonal-fractions` for recipes/ratios, `all-small-caps` for abbreviations, disable ligatures in code blocks. Currently absent from BrickLayer's rules.

11. **Grid-template-rows for height animations** — Currently BrickLayer's motion rules say to avoid animating height. Add the specific fix: animate `grid-template-rows: 0fr` → `1fr` instead, which is GPU-compositable.

12. **Multi-provider skill distribution** — impeccable's build system compiling one source to Claude Code, Cursor, Gemini, Codex, etc. is worth tracking. BrickLayer skills are Claude Code-specific. If BrickLayer ever wants to support other harnesses, this architecture is the reference implementation.

**Priority: LOW**

13. **Fallback font metrics** — `size-adjust`/`ascent-override`/`descent-override` to eliminate FOUT layout shift. Highly technical, low visual impact for BrickLayer's typical dashboards.

14. **Web Audio API / Device APIs** — from overdrive.md. Not relevant to BrickLayer's primary use case.

---

## Gap Analysis: All Three Repos vs BrickLayer 2.0

| Feature | In Repos | In BrickLayer 2.0 | Gap Level | Notes |
|---------|----------|-------------------|-----------|-------|
| HTML visualization of code artifacts (diffs, plans, recaps) | visual-explainer (full) | None | HIGH | BrickLayer has no HTML output capability at all — everything is markdown/terminal |
| Auto-convert tables to HTML | visual-explainer | None | HIGH | Proactive pattern — fires before the user asks |
| Decision log with confidence tagging | visual-explainer | None | HIGH | High/Medium/Low confidence on design rationale — directly serves BrickLayer's cognitive debt tracking |
| Domain exploration before design | interface-design | None | HIGH | "Color world" question (physical-world-derived palette) vs. starting from preferences |
| Mandatory WHY for every design choice | interface-design | None | HIGH | BrickLayer states what to do, not how to force the WHY discipline |
| Persistent design system memory | interface-design (.interface-design/system.md) | Partial (.ui/design-brief.md, tokens.json) | MEDIUM | BrickLayer has token storage but not decision rationale or component patterns |
| OKLCH color space | impeccable | None (hex only) | HIGH | Perceptually uniform, tinted neutrals, scientifically superior to HSL/hex |
| AI slop detection as structured pre-delivery gate | all three | None | HIGH | BrickLayer anti-patterns list exists but isn't a required self-check before output |
| Nielsen heuristics scoring table | impeccable/critique | None | MEDIUM | Concrete 0-40 score adds auditability to /ui-review |
| Persona-based critique | impeccable/critique | None | MEDIUM | Walks through primary user action per persona, lists specific red flags |
| Emotional valley design | impeccable/critique | None | MEDIUM | Peak-end rule, anxiety spikes at high-stakes moments |
| Overdrive / technically ambitious effects | impeccable/overdrive | None | MEDIUM | View Transitions, scroll-driven animations, virtual scrolling |
| Extract patterns from existing code | interface-design | None | MEDIUM | Reverse-engineer design system by frequency counting |
| Context Gathering Protocol (gated) | impeccable/teach-impeccable | Partial (/ui-init wizard) | MEDIUM | impeccable gates ALL design work on confirmed context |
| Multi-provider skill distribution | impeccable (build system) | None | LOW | Claude Code-only for BrickLayer's purposes |
| Fluid type marketing vs fixed app UI distinction | impeccable | None | MEDIUM | BrickLayer doesn't distinguish when to use clamp() vs fixed rem |
| Forbidden: gradient text, gray on colored bg, nested cards | impeccable | Partial | MEDIUM | BrickLayer bans some AI slop patterns but not all impeccable identifies |
| "Don't center everything" rule | impeccable | None | MEDIUM | BrickLayer actively centers some patterns |
| OpenType features (tabular-nums, fractions) | impeccable | Partial (tabular-nums mentioned) | LOW | Good reference, minimal practical gap |
| Fallback font metrics (size-adjust) | impeccable | None | LOW | Technical FOUT prevention |
| Slide deck output format | visual-explainer | None | MEDIUM | 10 slide types, 4 presets, full slide engine — useful for presenting BL research findings |
| Fact-check command (doc vs. code accuracy) | visual-explainer | None | MEDIUM | Verify that READMEs/specs match actual code |

---

## Top 5 Recommendations

### 1. HTML Visualization Commands (/visual-diff, /visual-plan, /visual-recap) [HIGH]

BrickLayer has zero HTML output capability. Every artifact is markdown. The visual-explainer commands produce browser-openable HTML pages that are dramatically more scannable for large diffs, plan audits, and session recaps.

**What to build**:
- `/visual-diff` — post-build HTML review: KPI dashboard (lines added/removed, test counts, CHANGELOG updated badge), Mermaid architecture diagram, before/after code panels, decision log with High/Medium/Low confidence tagging, re-entry context (invariants, non-obvious coupling, gotchas)
- `/visual-plan` — HTML audit of `.autopilot/spec.md` against the codebase: blast radius analysis, understanding gaps dashboard, risk assessment cards
- `/visual-recap` — time-windowed HTML project snapshot: architecture diagram, recent activity by theme, cognitive debt hotspots

**Implementation sketch**: Add three command files to `template/.claude/commands/`. Each follows the visual-explainer SKILL.md pattern: read references before generating, pick a non-generic aesthetic, write to `~/.agent/diagrams/`, open in browser. The SKILL.md can be adapted from visual-explainer's 37KB master file — BrickLayer doesn't need to replicate the slide engine, but needs the diagram routing rules, Mermaid discipline (always `theme: 'base'`, always zoom controls, never bare `<pre class="mermaid">`), and the slop test.

**Why it matters**: BrickLayer runs long campaigns. The cognitive debt patterns — decision log with confidence tagging, re-entry context, cognitive debt hotspots — directly address the problem of losing context between sessions. This is a research tool problem, not just a UI problem.

### 2. Domain Exploration + WHY Discipline for uiux-master [HIGH]

The interface-design SKILL.md identified a gap that BrickLayer's `frontend-design-philosophy.md` doesn't address: the LLM will default to generic output unless forced to explore the product's domain before any visual decisions.

**What to add to uiux-master**:

Before any design work, produce (not skip):
```
Domain: [5+ concepts from this product's world — not features, territory]
Color world: [5+ colors that exist in this domain's physical space]
Signature: [one element unique to THIS product that can't exist in a generic dashboard]
Rejecting: [3 obvious defaults for this interface type and what replaces each]
```

Then, before writing each component:
```
Intent: [who, what they need to accomplish, how it should feel]
Palette: [colors from domain exploration — WHY these fit this product]
Depth: [borders/shadows/layered — WHY this fits the intent]
Typography: [typeface — WHY it fits the intent]
Spacing: [base unit]
```

If the WHY answer is "it's common" or "it works," that is a flag to stop and think.

Post-build self-checks before showing: swap test, squint test, signature test (can you point to 5 specific elements), token test (read CSS variable names out loud — do they sound like this product?).

### 3. AI Slop Detection as a Required Pre-Delivery Gate [HIGH]

Currently BrickLayer's anti-patterns are in `frontend-design-philosophy.md` as rules to follow, but there's no structured self-check that the agent must run before showing output.

**What to add**: A named "slop gate" in uiux-master that runs before any UI is shown. Checks the 7 telltale signals from visual-explainer's slop test, plus impeccable's expanded list:
- Inter/Roboto + purple/violet gradient accents
- `background-clip: text` gradient on headings
- Emoji leading section headers
- Animated glowing box-shadows
- Cyan-magenta-pink color scheme
- Perfectly uniform card grid (no visual hierarchy)
- Three-dot window chrome on code blocks
- Gray text on colored backgrounds
- Nested cards inside cards
- "Don't default to dark mode with glowing accents" (relevant given BrickLayer's dark-first philosophy)

If two or more are present, regenerate with a constrained aesthetic (Blueprint, Editorial, Paper/ink) before showing.

**Why it matters**: BrickLayer's uiux-master produces output on first try. Without a gate, defaults accumulate. The slop test is a 5-second discipline that catches the most common failures.

### 4. OKLCH Color Space + Tinted Neutrals in frontend-design-philosophy.md [HIGH]

BrickLayer's `frontend-design-philosophy.md` uses hardcoded hex values throughout. This has two problems: hex doesn't communicate perceptual uniformity relationships, and all the neutral grays (`#E5E7EB`, `#9CA3AF`) are pure gray — no brand tint.

**What to add**:

OKLCH section in `frontend-design-philosophy.md`:
```
Use OKLCH, not HSL or hex. Equal steps in lightness look equal in OKLCH.
Format: oklch(lightness% chroma hue)

Background darks: oklch(12% 0.02 280) — slightly purple-tinted, not pure gray
Tinted neutrals: Always add 0.005-0.01 chroma toward brand hue
  Pure gray (dead): oklch(50% 0 0)
  Tinted gray (alive): oklch(50% 0.01 250)  ← tiny hue toward brand blue

As lightness approaches white/black, reduce chroma:
  Base accent: oklch(60% 0.15 250)
  Light variant: oklch(85% 0.08 250)  ← same hue, reduced chroma
```

Fluid type rule:
```
Use clamp() for: marketing/content pages where text dominates
Use fixed rem for: dashboards, app UIs, data-dense interfaces
No major design system (Material, Polaris, Primer, Carbon) uses fluid type in product UI.
```

### 5. Persistent Design System Memory with Decision Rationale (.ui/system.md) [MEDIUM]

BrickLayer's `.ui/design-brief.md` captures the brief. `tokens.json` captures values. But neither captures the decision rationale or specific component measurements, and neither is designed to be checked at the start of every subsequent session.

**What to build**: Add `.ui/system.md` as a new artifact to the `/ui-init` → `/ui-compose` workflow:
```markdown
# Design System — [Project Name]

## Direction
Personality: [chosen from: Precision & Density | Warmth | Sophistication | Boldness | Utility | Data & Analysis]
Foundation: [cool | warm | neutral | tinted]
Depth: [borders-only | subtle-shadows | layered-shadows]

## Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| Borders-only depth | Dashboard tool, users want density | 2026-03-28 |
| 4px spacing base | Tight enough for data tables | 2026-03-28 |

## Component Patterns
### Button Primary
- Height: 36px, Padding: 12px 16px, Radius: 6px
### Card Default
- Border: rgba(255,255,255,0.06), Padding: 16px, Radius: 6px
```

The masonry-session-start.js hook should load `.ui/system.md` when it exists, and `/ui-review` should audit against its rules (height 38px when pattern says 36px = violation). This closes the session continuity gap — decisions made in session 1 enforce themselves in session 7.

---

## Novel Patterns to Incorporate (Future)

**Cognitive debt hotspot visualization**: visual-explainer's project-recap command segments cognitive debt by category (undocumented rationale, complex modules without tests, overlapping changes) and assigns severity with concrete fix suggestions. This pattern could be applied to BrickLayer's synthesis workflow — after a campaign, produce a cognitive debt report alongside the findings.

**The "understanding gaps" dashboard**: From visual-explainer's plan-review. Count of changes with clear rationale vs. missing rationale, visualized as a progress bar. Applied to BrickLayer: after `/plan` generates `.autopilot/spec.md`, automatically count tasks with explicit acceptance criteria vs. tasks with vague definitions. Flag before `/build` starts.

**Emotional valley mapping**: From impeccable's critique skill. Applied to any UI that involves high-stakes user actions (payments, deletes, irreversible operations). The peak-end rule — if the most intense moment is negative (a confusing error) the whole experience feels bad, even if everything else works.

**View Transitions API morphing** (from impeccable/overdrive): When a list item expands into a detail view, or a button morphs into a dialog, View Transitions makes this cinematic with 2-3 lines of CSS. Not in BrickLayer's motion guidelines.

**Scroll-driven animations** (`animation-timeline: scroll()`): CSS-only parallax, progress bars, reveal sequences. Chrome/Edge/Safari. Always provide a static fallback for Firefox.

**The "propose before building" discipline for high-risk work**: From impeccable/overdrive. "This skill has the highest potential to misfire. You MUST think through 2-3 different directions, ask the user, only proceed with the direction confirmed." Applied to BrickLayer: any `/ui-compose` task flagged as "technically ambitious" should follow this pattern before touching code.

---

## Output Summary

```json
{
  "repos_researched": [
    "nicobailon/visual-explainer",
    "Dammyjay93/interface-design",
    "pbakaus/impeccable"
  ],
  "report_path": "docs/repo-research/visual-ui-design.md",
  "files_analyzed": 67,
  "agents_found": 0,
  "hooks_found": 0,
  "high_priority_gaps": 5,
  "medium_priority_gaps": 9,
  "low_priority_gaps": 4,
  "top_recommendation": "Add /visual-diff, /visual-plan, /visual-recap commands that generate browser-openable HTML pages with decision logs, cognitive debt hotspots, and Mermaid diagrams — BrickLayer currently has zero HTML output capability and this directly addresses the session continuity problem for long research campaigns",
  "verdict": "All three repos are narrower than BrickLayer in scope (research campaigns, routing, EMA training, agent fleet) but each is deeper than BrickLayer in its specific niche: visual-explainer has the most complete HTML generation discipline with decision log confidence tagging and cognitive debt tracking; interface-design has the strongest 'design intent before code' enforcement with domain exploration and persistent memory; impeccable has the most rigorous quality gates (Nielsen scoring, persona testing, slop detection) and the only OKLCH-aware color guidance — none of these capabilities exist in BrickLayer today."
}
```

# Repo Research: nextlevelbuilder/ui-ux-pro-max-skill
**Repo**: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
**Researched**: 2026-03-28
**Version analyzed**: 2.5.0

---

## Verdict Summary

This repo is a well-engineered, data-driven UI/UX design intelligence skill for AI coding assistants. Its primary value is a **BM25-powered search engine over large CSV databases** (161 industry-specific reasoning rules, 67 UI styles, 57 typography pairings, 161 color palettes, 25 chart types, 99 UX guidelines) plus a **design system generator** that synthesizes multi-domain searches into a project-ready design brief in seconds. BrickLayer's `uiux-master` already covers similar territory with opinionated rules baked into markdown, but this repo offers a fundamentally different architecture: **structured, queryable, externalized knowledge** rather than static prompts. The `design-system/MASTER.md + pages/ override` persistence pattern and the **161-row `ui-reasoning.csv`** (mapping product type to style+color+typography+anti-patterns with JSON decision rules per row) are the highest-value items to harvest.

---

## File Inventory

### Root
| File/Dir | Description |
|----------|-------------|
| `README.md` | Full documentation — 67 styles, 161 rules, install, CLI, usage, design system workflow |
| `CLAUDE.md` | Dev guide — architecture, sync rules, search commands, git workflow |
| `skill.json` | Claude Marketplace skill metadata (v2.5.0, 18 platforms) |
| `LICENSE` | MIT |
| `.gitignore` | Standard |

### `.claude-plugin/`
| File | Description |
|------|-------------|
| `marketplace.json` | Claude Marketplace publish config — plugin registration |
| `plugin.json` | Plugin descriptor — skill path pointer, keyword list, version |

### `.claude/skills/`
Seven skill subdirectories, each with a `SKILL.md` and optional data/scripts/references:

| Skill | Size | Description |
|-------|------|-------------|
| `ui-ux-pro-max/SKILL.md` | 44KB | Main skill — full ruleset: 10 priority categories, pre-delivery checklists, workflow, domain search guide |
| `ui-ux-pro-max/data` | symlink | Points to `src/ui-ux-pro-max/data/` |
| `ui-ux-pro-max/scripts` | symlink | Points to `src/ui-ux-pro-max/scripts/` |
| `banner-design/SKILL.md` | 8KB | Banner creation workflow — 14 art styles, Chrome DevTools export |
| `banner-design/references/banner-sizes-and-styles.md` | 5KB | Platform dimensions reference |
| `brand/SKILL.md` | 3KB | Brand identity — voice, tokens, asset validation, color extraction |
| `brand/scripts/` | Python scripts | Context injection, design token sync, asset validation, color extraction |
| `brand/templates/` | Templates | Brand guidelines output |
| `design-system/SKILL.md` | 7KB | 3-tier token architecture, slide generation, token validation |
| `design-system/data/` | 8 CSV files | Slide-specific data: layouts, strategies, charts, copy, typography, backgrounds, color-logic, layout-logic |
| `design/SKILL.md` | 12KB | Master router — logo, CIP, slides, banners, icons, social photos, brand, design-system |
| `design/references/` | 17 MD files | Logo design, CIP deliverables, banner sizes, icon design, slides templates, copywriting formulas, social photo design, logo prompt engineering |
| `slides/SKILL.md` | 1KB | Minimal slides skill — routes to design-system for slides work |
| `ui-styling/SKILL.md` | 10KB | shadcn/ui + Tailwind + canvas-based visual design |
| `ui-styling/canvas-fonts/` | Font assets | Canvas font rendering |
| `ui-styling/scripts/` | Python | Component install, config generation automation |

### `src/ui-ux-pro-max/` (Source of Truth)

**data/** — 16 CSV/script files:

| File | Size | Description |
|------|------|-------------|
| `ui-reasoning.csv` | 53KB | **161 rows** — product type → pattern+style+color+typography+effects+decision rules+anti-patterns per industry |
| `styles.csv` | 142KB | **67 UI styles** — keywords, colors, effects, AI prompt, CSS keywords, implementation checklist, design system variables |
| `products.csv` | 58KB | 161 product type recommendations — style priority, UX considerations |
| `typography.csv` | 50KB | 57 font pairings — mood, Google Fonts import URL, best for |
| `colors.csv` | 32KB | 161 color palettes — hex values, industry match |
| `design.csv` | 106KB | Expanded design knowledge base |
| `draft.csv` | 106KB | Extended draft dataset |
| `landing.csv` | 17KB | 24+ landing page patterns — CTA strategies, section order |
| `charts.csv` | 19KB | 25 chart types — library recommendations, use cases |
| `ux-guidelines.csv` | 19KB | 99 UX best practices and anti-patterns |
| `app-interface.csv` | 10KB | Mobile/native interface guidelines |
| `icons.csv` | 21KB | Icon library recommendations by style |
| `react-performance.csv` | 15KB | React/Next.js performance patterns |
| `google-fonts.csv` | 745KB | Full Google Fonts catalog — searchable |
| `_sync_all.py` | 22KB | Sync script for keeping cli/assets in sync with src |

**data/stacks/** — 16 stack-specific CSVs:
`angular, astro, flutter, html-tailwind, jetpack-compose, laravel, nextjs, nuxt-ui, nuxtjs, react, react-native, shadcn, svelte, swiftui, threejs, vue`

**scripts/**:

| File | Size | Description |
|------|------|-------------|
| `core.py` | 12KB | BM25 search engine — tokenize, IDF calculation, domain auto-detection, 15+ stack configs |
| `design_system.py` | 44KB | Design system generator — multi-domain parallel search, reasoning rule application, ASCII/markdown output, persist to MASTER.md + pages/ |
| `search.py` | 6KB | CLI entry point — arg parsing, UTF-8 handling, result formatting |

**templates/**:
- `base/skill-content.md` (19KB) — Platform-agnostic skill content template
- `base/quick-reference.md` (24KB) — Quick reference section for Claude
- `platforms/` — 17 platform-specific JSON configs (claude, cursor, windsurf, copilot, kiro, roocode, kilocode, codex, qoder, gemini, trae, opencode, continue, codebuddy, droid, warp, augment)

### `cli/` — npm package `uipro-cli`
| File/Dir | Description |
|----------|-------------|
| `src/commands/init.ts` | Install command — platform detection, template rendering, file generation |
| `src/commands/uninstall.ts` | Clean removal per platform |
| `src/commands/update.ts` | Version update |
| `src/commands/versions.ts` | Version listing from GitHub releases |
| `assets/data/` | Bundled copy of src data |
| `assets/scripts/` | Bundled copy of src scripts |
| `assets/templates/` | Bundled copy of templates |

### `docs/`
| File | Description |
|------|-------------|
| `三个 data-scripts-templates 的区别.md` | Chinese: explains the 3-tier architecture (data=knowledge, scripts=engine, templates=output) |

### `preview/`
| File | Description |
|------|-------------|
| `xiaomaomi-app.html` | Example HTML preview of a generated mobile app UI |

---

## Skill/Component Catalog

### 1. Main UI/UX Skill (`ui-ux-pro-max`)
**Purpose**: Comprehensive design intelligence — style selection, color, typography, UX rules, chart recommendations, stack-specific guidance.

**Unique techniques**:
- **10-priority rule table** (Accessibility→Touch→Performance→Style→Layout→Typography→Animation→Forms→Navigation→Charts) with precise levels (CRITICAL/HIGH/MEDIUM/LOW) — enforces a clear decision hierarchy
- **Pre-delivery checklist** in SKILL.md — 6 categories: Visual Quality, Interaction, Light/Dark Mode, Layout, Accessibility — each with specific binary checkboxes
- **Decision criteria trigger**: "Use this skill if the task will change how a feature looks, feels, moves, or is interacted with."
- **Skip criteria** explicitly listed (backend logic, API design, infrastructure)
- **Common sticking points table**: problem → quick-reference section to check

### 2. Design System Generator (`design_system.py`)
**Purpose**: Auto-generate a complete design system from a plain-English product description.

**Unique techniques**:
- **5 parallel domain searches** (product, style, color, landing, typography) then applies reasoning rules from `ui-reasoning.csv`
- **Keyword scoring** for best-match selection among search results
- **ASCII box output** for terminal visibility — shows pattern, style, colors, typography, key effects, anti-patterns, pre-delivery checklist all in one box
- **Master + Overrides persistence pattern**: `design-system/MASTER.md` (global) + `design-system/pages/{page}.md` (page-specific overrides) — page rules win over master
- **Intelligent override generation**: uses existing search infrastructure to extract page-specific guidance rather than hardcoded logic
- **Page type detection**: pattern-matches keywords (dashboard, checkout, auth) to classify and apply appropriate guidance

### 3. `ui-reasoning.csv` — 161 Industry Rules
**Purpose**: Map any product category to a complete design system recommendation.

**Structure** (per row):
- `UI_Category` — product type (e.g., "Beauty/Spa/Wellness Service")
- `Recommended_Pattern` — landing page structure (e.g., "Hero-Centric + Social Proof")
- `Style_Priority` — ordered list of UI styles (e.g., "Soft UI Evolution + Neumorphism")
- `Color_Mood` — palette description with hex values
- `Typography_Mood` — font personality
- `Key_Effects` — specific animations with timing (e.g., "Soft shadows + Smooth transitions (200-300ms) + Gentle hover")
- `Decision_Rules` — JSON conditions (e.g., `{"must_have": "booking-system", "if_luxury": "add-gold-accents"}`)
- `Anti_Patterns` — what NOT to use (e.g., "Bright neon colors + Harsh animations + Dark mode" for beauty/spa)
- `Severity` — HIGH/MEDIUM/LOW

### 4. `styles.csv` — 67 Style Definitions
**Per-style fields**: Keywords, Primary Colors, Secondary Colors, Effects & Animation, Best For, Do Not Use For, Light Mode support, Dark Mode support, Performance rating, Accessibility rating, Mobile-Friendly, Conversion-Focused, Framework Compatibility, Era/Origin, Complexity, AI Prompt Keywords, CSS/Technical Keywords, Implementation Checklist, Design System Variables

**Standout**: Each style has ready-to-use CSS technical keywords AND a complete design system variables block (CSS custom properties) AND an AI prompt that can be given verbatim to generate that style.

### 5. BM25 Search Engine (`core.py`)
**Purpose**: Query all CSV databases with relevance ranking.

**Unique techniques**:
- BM25 with k1=1.5, b=0.75 — tuned for short design queries
- Domain auto-detection: analyzes query against keyword maps to infer correct domain without user specifying `--domain`
- Truncates output to 300 chars per value — token optimization for LLM consumption
- 15 stack configs with file paths and column specs
- Result formatting designed for LLM context injection

### 6. Banner Design Skill
**Techniques**: 14 art direction styles, Chrome DevTools screenshot export workflow, platform dimension reference (social, ads, web, print), researches Pinterest for references before generating.

### 7. Brand Skill
**Techniques**: `docs/brand-guidelines.md` as authoritative source, propagates changes to design tokens (JSON + CSS) via scripts, asset validation (naming, dimensions, formats), color extraction and palette comparison.

### 8. Design-System Skill (Presentation-focused)
**Techniques**: 3-tier token model (primitive→semantic→component), slide generation with Chart.js, Duarte methodology (emotion-arc pattern-breaking), BM25 search over slide-specific CSVs (layouts, strategies, copy formulas, chart types, typography, color logic).

### 9. UI-Styling Skill
**Stack**: shadcn/ui + Radix UI + Tailwind CSS + canvas-based visual design. Emphasizes "copy-paste distribution model" (shadcn) + utility-first (Tailwind) + canvas compositions. Python automation for component installation and config generation.

### 10. Design Skill (Master Router)
**Purpose**: Routes to sub-skills (brand, design-system, ui-styling) for specialized tasks, handles logo/CIP/slides/banners/icons/social-photos natively.
**Unique**: Uses Gemini 3.1 Pro for logo/icon SVG generation. Has full Corporate Identity Program (CIP) workflow with 50+ deliverable types.

---

## Feature Gap Analysis

| Feature | In this repo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------|-------------------|-----------|-------|
| **Industry-specific reasoning rules (product→design system)** | 161 rules in `ui-reasoning.csv` with JSON decision conditions, anti-patterns, effects timing | Not present — BL has general dark-dashboard philosophy only | **CRITICAL** | This is the biggest gap. BL has no concept of "for a healthcare app, use neumorphism + calm blue, avoid neon" |
| **BM25 search over style/color/typography databases** | Full Python BM25 engine, auto-detection, 15 stack configs | Not present | **HIGH** | BL's `uiux-master` holds knowledge statically in CLAUDE.md rules, not queryable at runtime |
| **Queryable styles DB (67 entries)** | `styles.csv` — per style: AI prompt, CSS keywords, implementation checklist, design system variables | BL has ~10 styles named in `frontend-design-philosophy.md` | **HIGH** | BL's style coverage is a fraction of this repo's; no per-style CSS variable blocks |
| **Design system generator** | Python script, ASCII/MD output, persist to MASTER.md + pages/ | No equivalent | **HIGH** | BL's `/ui-init` generates `tokens.json` interactively; this auto-generates from product description |
| **Master + Overrides persistence pattern** | `design-system/MASTER.md` + `pages/{page}.md` — page overrides global | No equivalent | **MEDIUM** | BL has `tokens.json` (global) with no page-level override system |
| **Pre-delivery checklist** | 6-category checklist baked into SKILL.md (Visual Quality, Interaction, L/D Mode, Layout, Accessibility) | Partial — BL's CLAUDE.md has general quality standards | **MEDIUM** | BL's check is not UI-delivery specific |
| **99 UX guidelines database** | `ux-guidelines.csv` — searchable best practices and anti-patterns | BL has ~20 rules in `frontend-design-philosophy.md` | **MEDIUM** | Coverage gap — especially for touch, mobile, animation, forms |
| **57 typography pairings** | `typography.csv` with mood, Google Fonts URL | BL has 3-4 approved fonts listed | **MEDIUM** | BL specifies fonts but gives no pairing logic or mood mapping |
| **161 color palettes (industry-specific)** | `colors.csv` — aligned 1:1 with product types | BL has default "retro sunset" + manual per-app | **MEDIUM** | BL has no concept of industry-appropriate palette selection |
| **25 chart type recommendations** | `charts.csv` — library recommendations per use case | BL mentions Nivo only (area, donut, bar, sparkline) | **MEDIUM** | BL is narrower — only covers own dashboard chart patterns |
| **Stack-specific guidelines** | 16 stack CSVs (React, Next.js, Vue, Flutter, SwiftUI, Jetpack Compose, Three.js, Laravel, etc.) | BL targets React 19 + Tailwind v4 exclusively | **LOW** | BL is intentionally opinionated; not a gap for BL's use case |
| **Claude Marketplace plugin publishing** | `.claude-plugin/` with `plugin.json` + `marketplace.json` | No equivalent | **LOW** | BL is a private system, not marketplace-bound |
| **10-tier priority system (accessibility first)** | Priority 1–10 table in SKILL.md with CRITICAL/HIGH/MEDIUM/LOW levels | BL has accessibility rules scattered in `frontend-design-philosophy.md` | **MEDIUM** | BL lacks explicit priority ordering — critical rules not marked critical |
| **Animation timing codified** | 150–300ms micro-interactions, exit 60–70% of enter, spring physics, stagger 30–50ms | BL has similar but less precise — "hover: 150ms, enter: 200ms" | **LOW** | BL covers this well in `frontend-design-philosophy.md` |
| **Form UX guidelines** | 30+ form rules (inline validation, blur timing, autofill, error recovery, multi-step) | BL has minimal form guidance | **MEDIUM** | Forms are underspecified in BL's current rules |
| **Navigation pattern rules** | 25+ navigation rules (back behavior, state preservation, gesture nav, deep linking) | BL has basic sidebar pattern | **MEDIUM** | BL's navigation coverage is dashboard-centric, not generalized |
| **Three.js stack guidelines** | `threejs.csv` (44KB) — largest stack file | Not present | **LOW** | BL doesn't target 3D/WebGL work currently |
| **Google Fonts full catalog** | `google-fonts.csv` (745KB) — full catalog searchable | BL specifies 5-6 fonts explicitly | **LOW** | BL's explicit font choices are sufficient for its use case |
| **Dark mode (OLED / purple-black)** | `styles.csv` row 7 — Dark Mode (OLED) as a named style | BL's `frontend-design-philosophy.md` is entirely dark-first | **NONE** | BL's dark philosophy is more opinionated and specific to its aesthetic |
| **Bento grid pattern** | Listed as style #21 and #35, referenced in products.csv | BL has detailed bento grid specs in `frontend-design-philosophy.md` | **NONE** | BL has stronger bento implementation guidance |
| **Figma MCP integration** | Not present — no Figma tooling | BL has full Figma MCP workflow | **N/A** | BL exceeds this repo here |
| **cva component variants** | Not mentioned — uses shadcn defaults | BL uses cva explicitly | **N/A** | BL exceeds this repo here |
| **3-tier token architecture** | `design-system/SKILL.md` covers primitive→semantic→component | BL's `tokens.json` implements same 3-tier model | **NONE** | Both cover this; BL's implementation is equally strong |
| **React 19 + Tailwind v4 specifics** | Not covered — targets HTML+Tailwind default | BL's `react-tailwind-standards.md` is comprehensive | **N/A** | BL exceeds this repo here |

---

## Top 5 Recommendations

### 1. Add `ui-reasoning.csv` logic to `uiux-master` agent
The 161-row industry reasoning table is the single highest-value item. Currently `uiux-master` applies uniform dark-dashboard aesthetics regardless of product type. For a healthcare app it should recommend neumorphism + calm blue; for fintech it should flag "AI purple/pink gradients" as an anti-pattern; for beauty/spa it should default to soft pastels, NOT dark mode.

**Implementation**: Either bundle a condensed version of `ui-reasoning.csv` into `uiux-master`'s agent prompt as a lookup table, or add a Python search script similar to `search.py` that `uiux-master` can call via Bash to query industry-specific recommendations before generating any UI.

**Impact**: `uiux-master` would produce industry-appropriate designs instead of defaulting everything to purple-black dashboards.

### 2. Adopt the Master + Overrides persistence pattern for `/ui-compose`
This repo's `design-system/MASTER.md` + `design-system/pages/{page}.md` pattern is superior to BL's current single `tokens.json`. Page-specific rules (dashboard uses dense data layout; checkout uses conversion-optimized; auth uses minimal & direct) should override global token decisions without modifying the master.

**Implementation**: In `/ui-compose`, after writing `tokens.json`, also write `design-system/MASTER.md`. When a worker agent builds a specific page, check for `design-system/pages/{page}.md` first and inject its rules into the worker prompt with higher priority.

**Impact**: Multi-page applications get coherent but differentiated design — the checkout page behaves differently from the dashboard without manual intervention.

### 3. Extract and adopt the 10-priority rule framework into BL's `uiux-master`
The SKILL.md's priority table (Priority 1=Accessibility CRITICAL → Priority 10=Charts LOW) provides a structured way for the agent to sequence its decisions. BL's current `frontend-design-philosophy.md` has rules but no explicit priority ordering — there's no concept of "check accessibility before choosing style."

**Implementation**: Add a priority block to `uiux-master`'s agent definition that mirrors this table. Include the "Must check §1–§3 before delivery" rule as an explicit step in the agent's workflow.

**Impact**: `uiux-master` will reliably check contrast ratios and touch targets before shipping, not after.

### 4. Add the pre-delivery checklist to `/ui-review`
The SKILL.md pre-delivery checklist (Visual Quality, Interaction, Light/Dark Mode, Layout, Accessibility — 30+ binary checks) maps directly to what BL's `/ui-review` should validate. BL's current `/ui-review` uses Playwright screenshots to check visual fidelity but has no structured checklist for these UX-quality items.

**Implementation**: Embed the checklist into the `/ui-review` skill's SKILL.md as the structured output format. The review agent runs through each checkbox and reports pass/fail per item.

**Impact**: `/ui-review` outputs become actionable — "Touch targets: FAIL (icon at 32px, minimum 44px)" rather than vague feedback.

### 5. Harvest `styles.csv` AI prompt keywords and CSS technical keywords into `typescript-specialist`
Each of the 67 styles has:
1. An **AI prompt** (ready-to-use text for generating that style)
2. **CSS/Technical keywords** (specific properties and values)
3. An **implementation checklist**
4. **Design system CSS variables**

BL's `typescript-specialist` doesn't have style-specific implementation guidance. When it receives a request to "build a glassmorphism card", it has to infer all the details.

**Implementation**: Add a style quick-reference section to `typescript-specialist`'s agent prompt that maps style name → CSS technical keywords (the one-liners from `styles.csv`). For the 10-15 styles most relevant to dark dashboards (glassmorphism, dark mode OLED, bento grid, aurora UI, minimalism, soft UI evolution, neumorphism, AI-native UI, cyberpunk, neubrutalism), include the full CSS keyword block.

**Impact**: `typescript-specialist` produces correct glassmorphism (backdrop-filter: blur(15px), rgba(255,255,255,0.15), etc.) without needing extra prompting.

---

## Harvestable Items

### Direct data to adapt/adopt:

1. **`ui-reasoning.csv` top 40 rows** — the highest-traffic product categories (SaaS, E-commerce, Dashboard, Healthcare, Fintech, Portfolio, AI Platform, Beauty/Spa, Restaurant, Real Estate) — compress into a table in `uiux-master`'s agent MD

2. **Glassmorphism CSS block** from `styles.csv` row 3:
   - `backdrop-filter: blur(15px)`, `background: rgba(255,255,255,0.15)`, `border: 1px solid rgba(255,255,255,0.2)`, `-webkit-backdrop-filter: blur(15px)`, z-index layering
   - Design variables: `--blur-amount: 15px`, `--glass-opacity: 0.15`, `--border-color: rgba(255,255,255,0.2)`

3. **Animation timing precision** from SKILL.md §7:
   - Exit animations = 60–70% of enter duration
   - Stagger: 30–50ms per list item
   - Modal/sheet: animate from trigger source for spatial context
   - "Animations must be interruptible" — user tap cancels in-progress animation

4. **Form UX rules** (currently absent from BL) from SKILL.md §8:
   - Validate on blur (not keystroke)
   - Auto-focus first invalid field on submit error
   - Provide show/hide toggle on password fields
   - Multi-step flows: show step indicator, allow back navigation
   - Auto-save long form drafts

5. **Navigation rules** from SKILL.md §9:
   - Back navigation must restore scroll position + filter state + input
   - Never silently reset navigation stack
   - Bottom nav for top-level screens only — never nest sub-nav inside it
   - After route change, move focus to main content region (screen readers)

6. **Anti-pattern list for BL's dark-first philosophy** — from `ui-reasoning.csv`:
   - "AI purple/pink gradients" is an anti-pattern for: banking, insurance, fintech, legal, government, healthcare, logistics, pharmacy, senior care, construction, medical — add this to BL's enforcer
   - "Dark mode by default" is an anti-pattern for: beauty/spa, healthcare, restaurant, childcare, florist, bakery, mental health

7. **Pre-delivery checklist structure** (6-category, 30+ checkboxes) — adapt for BL's `/ui-review` output format

8. **Master + Overrides persistence pattern** — add to BL's `/ui-compose` workflow

9. **Design system generator prompt template** (the context-aware retrieval prompt):
   ```
   I am building the [Page Name] page. Please read design-system/MASTER.md.
   Also check if design-system/pages/[page-name].md exists.
   If the page file exists, prioritize its rules.
   If not, use the Master rules exclusively.
   ```

10. **10-priority rule framework** for `uiux-master` — priority 1 (Accessibility CRITICAL) through 10 (Charts LOW), with explicit "must check priority 1-3 before delivery" gate

11. **Style-specific design system variable blocks** (CSS custom properties per style) — especially for glassmorphism, bento grid, dark mode OLED, soft UI evolution, neumorphism — add to `typescript-specialist`

12. **`ui-reasoning.csv` Decision Rules JSON format** — each row has a `Decision_Rules` column with JSON conditions like `{"if_luxury": "switch-to-liquid-glass", "if_conversion_focused": "add-urgency-colors"}` — this conditional design logic concept is worth adopting in `uiux-master`'s reasoning loop

---

## What BrickLayer Already Does Better

- Figma MCP integration (get_design_context, get_screenshot, get_variable_defs) — not present in this repo
- React 19 / Tailwind v4 specifics — this repo targets HTML+Tailwind as default
- cva (class-variance-authority) component variant system
- Purple-black dark-first aesthetic — opinionated and consistent
- Bento grid implementation detail — BL's guidance is more specific
- Glass card pattern — BL has more implementation detail
- KPI stat card + sparkline pattern — BL-specific
- Icon sidebar pattern — BL-specific
- Nivo chart integration — BL-specific
- tokens.json 3-tier architecture — BL's is equally strong
- `/build` TDD pipeline for UI components — not present in this repo

---

```json
{
  "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
  "report_path": "docs/repo-research/nextlevelbuilder-ui-ux-pro-max-skill.md",
  "files_analyzed": 87,
  "skills_found": 7,
  "high_priority_gaps": 4,
  "top_recommendation": "Adopt ui-reasoning.csv logic in uiux-master — 161 industry-specific rules mapping product type to style+color+anti-patterns with JSON decision conditions. Currently uiux-master applies uniform dark-dashboard aesthetics regardless of product type.",
  "verdict": "High-value harvest target. The BM25-over-CSV architecture, 161 industry reasoning rules, Master+Overrides persistence pattern, and pre-delivery checklist structure are all directly actionable for BrickLayer. Does not replace BrickLayer's existing UI workflow but provides substantial knowledge database that BrickLayer's agents currently lack."
}
```

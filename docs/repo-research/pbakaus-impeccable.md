# Repository Research: pbakaus/impeccable

**URL:** https://github.com/pbakaus/impeccable
**Stars:** 15k | **Forks:** 641 | **Contributors:** 17
**License:** Apache 2.0
**Version:** 1.6.0
**Last researched:** 2026-03-31

---

## Executive Summary

**Impeccable** is a production-quality, cross-provider design skill library that delivers 21 skills (20 user-invocable slash commands + 1 passive frontend-design skill) for AI coding harnesses. It is the most sophisticated public example of multi-provider skill distribution for Claude Code and its peers. The project includes:

- A **factory-based build system** (Bun) that generates provider-specific skill outputs from a single source format
- **11 provider targets** (Claude Code, Cursor, Gemini CLI, Codex CLI, Kiro, OpenCode, Pi, Trae China, Trae International, Rovo Dev, VS Code Copilot/Agents)
- A **companion website** (impeccable.style, Cloudflare Pages) serving ZIP bundles via Cloudflare Pages Functions
- A **Claude Code Marketplace plugin** definition (`.claude-plugin/`)
- Prefixed and unprefixed skill variants for conflict-free universal bundles

This is directly relevant to BrickLayer 2.0 as a reference implementation for: skill packaging/distribution, multi-provider support, the Agent Skills spec, build system patterns, and skill-as-plugin architecture.

---

## File Inventory

### Root Files
| File | Purpose |
|------|---------|
| `README.md` | End-user installation and command reference |
| `AGENTS.md` | Architecture context for AI assistants (acts as CLAUDE.md equivalent) |
| `CLAUDE.md` | Project instructions for Claude Code: CSS build, versioning, adding skills |
| `DEVELOP.md` | Contributor guide: source format, build system, adding providers |
| `HARNESSES.md` | Provider capabilities matrix (frontmatter fields, skill directories, placeholders) |
| `package.json` | Bun scripts: build, rebuild, dev, deploy, test, screenshot, og-image |
| `biome.json` | Biome linter/formatter config |
| `wrangler.toml` | Cloudflare Pages deployment config |
| `bun.lock` | Lock file (Bun package manager) |
| `NOTICE.md` | Apache 2.0 attribution (Anthropic's original frontend-design skill) |

### Source Skills (`source/skills/`)
21 skill directories, each with `SKILL.md` and optional `reference/` subdirectory:

| Skill | Invocable | Purpose |
|-------|-----------|---------|
| `frontend-design` | No (passive) | Core design skill with 7 reference files; loaded by all other skills |
| `teach-impeccable` | Yes | One-time project setup: gather design context, save to `.impeccable.md` |
| `audit` | Yes | Technical quality checks: a11y, perf, theming, responsive, anti-patterns; scored 0-20 |
| `critique` | Yes | UX design review: hierarchy, IA, emotional resonance, personas; Nielsen heuristics 0-40 |
| `polish` | Yes | Final pre-ship quality pass across all design dimensions |
| `normalize` | Yes | Realign UI to design system standards, tokens, and patterns |
| `distill` | Yes | Strip designs to essence; remove unnecessary complexity |
| `animate` | Yes | Add purposeful animations and micro-interactions |
| `colorize` | Yes | Add strategic color to monochromatic designs |
| `bolder` | Yes | Amplify safe/boring designs for more visual impact |
| `quieter` | Yes | Tone down overly bold designs |
| `delight` | Yes | Add moments of joy and delight |
| `extract` | Yes | Pull repeated UI into reusable components/tokens |
| `clarify` | Yes | Improve unclear UX copy |
| `optimize` | Yes | Performance improvements |
| `harden` | Yes | Error handling, i18n, edge cases, production resilience |
| `adapt` | Yes | Adapt for different devices |
| `onboard` | Yes | Design onboarding flows |
| `typeset` | Yes | Fix font choices, hierarchy, sizing |
| `arrange` | Yes | Fix layout, spacing, visual rhythm |
| `overdrive` | Yes | Add technically extraordinary effects (WebGPU, scroll-driven, spring physics) |

### `frontend-design` Reference Files
7 domain reference files loaded contextually by skills:

| File | Content |
|------|---------|
| `reference/typography.md` | Type systems, font pairing, modular scales, OpenType |
| `reference/color-and-contrast.md` | OKLCH, tinted neutrals, dark mode, accessibility |
| `reference/spatial-design.md` | Spacing systems, grids, visual hierarchy |
| `reference/motion-design.md` | Easing curves, staggering, reduced motion |
| `reference/interaction-design.md` | Forms, focus states, loading patterns |
| `reference/responsive-design.md` | Mobile-first, fluid design, container queries |
| `reference/ux-writing.md` | Button labels, error messages, empty states |

### `critique` Reference Files
3 domain reference files (unique to the critique skill):
- `reference/cognitive-load.md` — Working memory rule, 8-item checklist
- `reference/heuristics-scoring.md` — Nielsen heuristics scoring rubric
- `reference/personas.md` — Pre-built UX personas with selection table

### Build System (`scripts/`)
| File | Purpose |
|------|---------|
| `build.js` | Main orchestrator: Tailwind CSS, static site, skill transforms, ZIPs, CF Pages config |
| `lib/utils.js` | `parseFrontmatter`, `readSourceFiles`, `readPatterns`, `replacePlaceholders`, `generateYamlFrontmatter`, `prefixSkillReferences`, `PROVIDER_PLACEHOLDERS` |
| `lib/zip.js` | ZIP bundle generation using `archiver` npm package |
| `lib/transformers/factory.js` | `createTransformer(config)` — factory that generates provider-specific transformer functions |
| `lib/transformers/providers.js` | `PROVIDERS` config map — one entry per supported provider |
| `lib/transformers/index.js` | Re-exports factory-generated transformers and PROVIDERS |
| `screenshot-antipatterns.js` | Playwright-based screenshot utility |
| `generate-og-image.js` | OG image generator |

### Claude Code Plugin (`.claude-plugin/`)
| File | Purpose |
|------|---------|
| `plugin.json` | Plugin metadata: name, description, version 1.6.0, skills path |
| `marketplace.json` | Claude Code Marketplace schema: name, owner, plugins array, category "design" |

### Website (`public/` + `server/` + `functions/`)
- `public/index.html` — Main landing page
- `public/cheatsheet.html` — Command reference cheatsheet
- `public/css/` — Modular CSS: `main.css` (Tailwind entry), `styles.css` (compiled), `tokens.css`, `workflow.css`, etc.
- `public/js/` — Vanilla JS app, component files, demos per command
- `server/index.js` — Bun dev server
- `server/lib/api-handlers.js` — Shared API logic (used by both dev server and CF Functions)
- `functions/api/download/` — Cloudflare Pages Functions for ZIP file downloads

### Tests (`tests/`)
- `tests/build.test.js` — Bun test suite for build system
- `tests/lib/` — Lib utility tests
- `tests/server/` — Server API tests

### Provider Output Directories (committed to repo)
These live at the **root level** and are committed, not gitignored:
`.agents/`, `.claude/`, `.claude-plugin/`, `.codex/`, `.cursor/`, `.gemini/`, `.kiro/`, `.opencode/`, `.pi/`, `.trae-cn/`, `.trae/`

Each has a `skills/` subdirectory containing all 21 skills in provider-specific format.

---

## Architecture Overview

### "Option A" Feature-Rich Source Pattern

Impeccable uses what the AGENTS.md calls "Option A": author skills once in a rich source format (YAML frontmatter + body), then compile down to provider-specific formats. This avoids the "lowest common denominator" trap where you'd limit everything to what Cursor supports (no frontmatter, no args).

```
source/skills/{name}/SKILL.md  →  [factory]  →  dist/{provider}/{configDir}/skills/{name}/SKILL.md
                    reference/*.md               dist/{provider}/{configDir}/skills/{name}/reference/*.md
```

### Source Skill Format

Every skill is a single `SKILL.md` with YAML frontmatter:

```yaml
---
name: audit
description: "Run technical quality checks..."
argument-hint: "[area (feature, page, component...)]"
user-invocable: true
---
Body content with {{placeholder}} tokens...
```

Supported frontmatter fields (per Agent Skills spec + extensions):
- `name` (required)
- `description` (required)
- `user-invocable` — enables slash command autocomplete
- `argument-hint` — autocomplete hint text
- `license` — attribution info
- `compatibility` — environment requirements
- `metadata` — arbitrary key-value pairs
- `allowed-tools` — pre-approved tools list (experimental)

### Body Placeholders

Source files use `{{placeholder}}` tokens that get replaced per-provider at build time:

| Placeholder | Example Replacement |
|-------------|---------------------|
| `{{model}}` | Claude / Gemini / GPT / the model |
| `{{config_file}}` | CLAUDE.md / .cursorrules / GEMINI.md |
| `{{ask_instruction}}` | "STOP and call the AskUserQuestion tool" (Claude Code) |
| `{{command_prefix}}` | `/` for most providers, `$` for Codex |
| `{{available_commands}}` | Comma-separated list of user-invocable skill names |

### Provider Config System

Each provider is a config object in `scripts/lib/transformers/providers.js`:

```javascript
'claude-code': {
  provider: 'claude-code',
  configDir: '.claude',
  displayName: 'Claude Code',
  frontmatterFields: ['user-invocable', 'argument-hint', 'license', 'compatibility', 'metadata', 'allowed-tools'],
}
```

The `createTransformer(config)` factory in `factory.js` takes this config and returns a fully-configured transform function. Adding a new provider is 2 steps:
1. Add placeholder config to `PROVIDER_PLACEHOLDERS` in `utils.js`
2. Add provider config to `PROVIDERS` in `providers.js`

### Prefixed Variants

Every provider generates two output variants:
- **Unprefixed**: `/audit`, `/polish`, etc. (default)
- **Prefixed** (`i-`): `/i-audit`, `/i-polish`, etc. (for conflict-free installation alongside other skill packs)

The `prefixSkillReferences()` utility rewrites cross-skill references (e.g., `{{command_prefix}}frontend-design`) to their prefixed equivalents.

### Universal Bundle

The build assembles a "universal" directory containing all 11 providers' output directories merged into one folder. Users can install from a single ZIP and pick the relevant `.claude/`, `.cursor/`, etc. folders.

### Build Pipeline

```
bun run build
  1. buildTailwindCSS()      — bunx @tailwindcss/cli
  2. buildStaticSite()       — Bun.build() (HTML + JS + CSS bundling)
  3. readSourceFiles()       — Parse all source/skills/**
  4. Per-provider transform  — createTransformer(config)(skills, distDir)
                               × 11 providers × 2 variants (prefixed/unprefixed)
  5. assembleUniversal()     — Merge all provider dirs
  6. createAllZips()         — Per-provider + universal ZIPs
  7. generateApiData()       — Static JSON for CF Pages API
  8. copyDistToBuild()       — Make dist accessible to CF Pages Functions
  9. generateCFConfig()      — _headers, _redirects, _routes.json
 10. Sync to root .claude/, .cursor/, etc.  — For local testing
```

### Website Architecture

- **Tech**: Vanilla JS + Modern CSS (no frameworks), Tailwind v4
- **Local dev**: Bun server (`server/index.js`)
- **Production**: Cloudflare Pages + Pages Functions
- **Shared API logic**: `server/lib/api-handlers.js` imported by both server and CF Functions
- **Static API**: JSON files pre-generated at build time (`build/_data/api/`), served via `_redirects` rewrites (no function overhead for reads)
- **Downloads**: CF Pages Functions (`functions/api/download/`) serve ZIP files from `build/_data/dist/`
- **Design**: Cormorant Garamond (display) + Instrument Sans (body), OKLCH colors, editorial sidebar layout

---

## Skill Design Patterns

### Mandatory Preparation Pattern

Every invocable skill opens with a mandatory invocation of `frontend-design`:

```
## MANDATORY PREPARATION

Invoke {{command_prefix}}frontend-design — it contains design principles, anti-patterns, and the **Context Gathering Protocol**. Follow the protocol before proceeding — if no design context exists yet, you MUST run {{command_prefix}}teach-impeccable first.
```

This ensures design principles are always loaded before any design action. The `frontend-design` skill itself has a **Context Gathering Protocol** that defines the 3-step order: (1) check loaded instructions for Design Context section, (2) check `.impeccable.md`, (3) run `teach-impeccable` if neither exists.

### Context Persistence Pattern

`teach-impeccable` gathers design context via structured questions and writes a `## Design Context` section to `.impeccable.md` in the project root. This persists across sessions without cluttering CLAUDE.md unless the user opts in.

### DO/DON'T Anti-Pattern Encoding

The `frontend-design` skill encodes design anti-patterns as explicit `**DO**:` and `**DON'T**:` lines by section. These are:
1. Embedded in the skill for LLM consumption
2. **Parsed by `readPatterns()`** in `utils.js` and served via `/api/patterns` for the website's anti-patterns section

This dual-use pattern is elegant: the skill content is also the data source.

### Scoring Rubrics

Two skills use formal scoring:
- **`/audit`**: Scores 5 dimensions 0-4 (total 0-20), with named rating bands
- **`/critique`**: Scores Nielsen's 10 heuristics 0-4 (total 0-40), with "most real interfaces score 20-32"

### Persona-Based Testing in `/critique`

The critique skill uses a `reference/personas.md` file with pre-built personas and a selection table. It:
1. Auto-selects 2-3 relevant personas based on interface type
2. Generates project-specific personas from `teach-impeccable` context
3. Walks through primary user actions per persona, reporting specific failures

### 4-Phase Critique Workflow

`/critique` uses a structured 4-phase flow:
1. **Phase 1**: Systematic design evaluation across 10 dimensions
2. **Phase 2**: Present findings (scores, anti-patterns verdict, priority issues)
3. **Phase 3**: Ask targeted questions based on findings (not generic)
4. **Phase 4**: Recommended actions after receiving user answers

This is a notably sophisticated pattern — asking questions only *after* analysis, tailored to what was found.

### Command Composition

Skills explicitly recommend other skills via `{{available_commands}}` and chain naturally:
```
/audit /normalize /polish blog    # audit → fix → polish
/critique /harden checkout        # UX review + add error handling
```

---

## Provider Support Matrix (from HARNESSES.md)

| Provider | Dir | `user-invocable` | `argument-hint` | Frontmatter | Notes |
|----------|-----|:---:|:---:|:---:|-------|
| Claude Code | `.claude/skills/` | Yes | Yes | Full | Most features; `$ARGUMENTS` runtime substitution |
| Cursor | `.cursor/skills/` | No | No | Partial | No frontmatter/args; reads `.agents/`, `.claude/`, `.codex/` too |
| Gemini CLI | `.gemini/skills/` | No | No | name+desc only | `.agents/` fallback |
| Codex CLI | `.codex/skills/` (via `.agents/`) | No | No | `argument-hint`+`license` | `$ARGNAME` syntax |
| VS Code Copilot | `.github/skills/` | Yes | Yes | Full | `.agents/`, `.claude/` fallback |
| Kiro | `.kiro/skills/` | Undoc. | Undoc. | Partial | Community reports only |
| OpenCode | `.opencode/skills/` | Yes | Yes | Full | `question` tool for asking |
| Pi | `.pi/skills/` | No | No | Partial | `.agents/` fallback |
| Trae China | `.trae-cn/skills/` | Yes | Yes | Partial | Shares placeholder config with Trae |
| Trae International | `.trae/skills/` | Yes | Yes | Partial | `RULES.md` as config file |
| Rovo Dev | `.rovodev/skills/` | Yes | Yes | Full | User-level: `~/.rovodev/skills/` |

---

## Key Technical Details

### PROVIDER_PLACEHOLDERS (from utils.js)

```javascript
'claude-code': {
  model: 'Claude',
  config_file: 'CLAUDE.md',
  ask_instruction: 'STOP and call the AskUserQuestion tool to clarify.',
  command_prefix: '/'
}
// + cursor, gemini, codex, agents, kiro, opencode, pi, trae, rovo-dev
```

### Frontmatter YAML Generation

Custom minimal YAML serializer (`generateYamlFrontmatter()`) — no external YAML library. Auto-quotes values starting with `[` or `{` to avoid YAML parsing ambiguity.

### Source Parsing

Custom minimal YAML frontmatter parser (`parseFrontmatter()`) — no external YAML library. Handles top-level key-value pairs, arrays, and nested objects.

### Skill Cross-Reference Prefixing

`prefixSkillReferences()` rewrites `/skillname` invocations and "the skillname skill" text references to their prefixed equivalents when generating the `i-` prefixed variants. Sorts skill names by length descending to avoid partial-match collisions.

### Dependencies

```json
"dependencies": {
  "archiver": "^7.0.1",      // ZIP generation
  "motion": "^12.23.26",     // Animation library (website)
  "playwright": "^1.57.0"    // Screenshot utility
},
"devDependencies": {
  "wrangler": "^4.71.0"      // Cloudflare deployment
}
```

Runtime: **Bun** (not Node.js). All scripts use `bun run`, `bun test`, `Bun.build()`.

---

## Claude Code Plugin Architecture

Impeccable registers as a Claude Code Marketplace plugin via `.claude-plugin/`:

**`plugin.json`:**
```json
{
  "name": "impeccable",
  "description": "Design vocabulary and skills for frontend development. Includes 21 skills...",
  "version": "1.6.0",
  "author": { "name": "Paul Bakaus" },
  "homepage": "https://impeccable.style",
  "repository": "https://github.com/pbakaus/impeccable",
  "skills": "./.claude/skills"
}
```

**`marketplace.json`** follows `https://anthropic.com/claude-code/marketplace.schema.json` with:
- `$schema` declaration
- `metadata.description`
- `owner` object
- `plugins[]` array with `category: "design"` and `tags[]`

---

## Anti-Patterns Vocabulary (from frontend-design SKILL.md)

The skill encodes these as machine-readable `**DON'T**:` lines by category:

**Typography DON'Ts:** Inter, Roboto, Arial, system defaults; monospace for "dev vibes"; large rounded icons above every heading

**Color DON'Ts:** Gray text on colored backgrounds; pure black/white; AI color palette (cyan-on-dark, purple-to-blue gradients, neon accents); gradient text for impact; dark mode with glowing accents

**Layout DON'Ts:** Wrap everything in cards; nest cards in cards; identical card grids; hero metric layout (big number + stats + gradient); center everything; same spacing everywhere

**Visual Detail DON'Ts:** Glassmorphism everywhere; rounded rectangles with thick colored border on one side; sparklines as decoration; generic drop shadows on rounded rectangles; modals as default

**Motion DON'Ts:** Animate layout properties; bounce/elastic easing

**Interaction DON'Ts:** Repeat same information; make every button primary; redundant headers

---

## Feature Gap Analysis vs BrickLayer 2.0

### Patterns BrickLayer Should Consider Adopting

#### 1. Context Gathering Protocol
**What they do:** The `frontend-design` passive skill defines a 3-step protocol: check instructions → check `.impeccable.md` → run `teach-impeccable`. Every other skill mandates loading this protocol first.

**BrickLayer gap:** Skills don't have a formalized context-check protocol. Relevant for any BrickLayer skill that needs project-specific context before acting.

**How to adopt:** Add a project context skill (e.g., `teach-bl`) that writes context to a project file, and add a "Mandatory Preparation" block to all relevant skills.

#### 2. `{{placeholder}}` System for Cross-Provider Skills
**What they do:** Build-time placeholder replacement for `{{model}}`, `{{config_file}}`, `{{ask_instruction}}`, `{{command_prefix}}`, `{{available_commands}}` per provider.

**BrickLayer gap:** If BrickLayer supports multiple providers, this pattern prevents hardcoded Claude-specific instructions from breaking on other platforms.

**How to adopt:** Minimal lift — define provider configs and a `replacePlaceholders()` function. Could integrate with sx's vault distribution.

#### 3. Prefixed Variants for Conflict-Free Installation
**What they do:** Generate `/audit` and `/i-audit` as separate skill variants so users can install multiple skill packs without name collisions.

**BrickLayer gap:** BrickLayer skills don't have a conflict-free naming strategy. If BrickLayer skills are distributed alongside other packs (e.g., impeccable), clashes are possible.

**How to adopt:** Add a `prefix` option to BrickLayer's build/distribution, generate both `/skillname` and `/bl-skillname` variants.

#### 4. Formal Scoring Rubrics in Skills
**What they do:** `/audit` produces a 0-20 score across 5 dimensions; `/critique` produces a 0-40 score across 10 Nielsen heuristics. Both define rating bands ("18-20 Excellent", etc.).

**BrickLayer gap:** BrickLayer skills don't use scored rubrics. This makes quality assessments more objective and comparable over time.

**How to adopt:** Define rubrics for BrickLayer's own quality dimensions (code quality, architecture, test coverage).

#### 5. Multi-Phase Skill Workflows with User Checkpoints
**What they do:** `/critique` uses 4 phases where Phase 3 asks targeted questions based on Phase 2 findings, then Phase 4 generates recommendations based on user answers. Questions are always tied to specific findings, never generic.

**BrickLayer gap:** BrickLayer skills tend to be single-pass (analyze → act). A phase-gate pattern with AskUserQuestion checkpoints improves output relevance.

**How to adopt:** Structure complex BrickLayer skills (e.g., refactoring, architecture review) as multi-phase workflows with mid-skill checkpoints.

#### 6. Anti-Patterns as Parseable DO/DON'T Lines
**What they do:** The `frontend-design` skill embeds anti-patterns as `**DO**:` and `**DON'T**:` lines that are both LLM instructions AND parsed by `readPatterns()` for the website API.

**BrickLayer gap:** BrickLayer coding standards exist as prose rules (`.claude/rules/`) but aren't in a machine-parseable format usable by both the LLM and tooling.

**How to adopt:** Consider encoding key rules in a DO/DON'T format within relevant skills for dual use.

#### 7. `.claude-plugin/` Marketplace Registration
**What they do:** Two JSON files (`plugin.json`, `marketplace.json`) that register the skill pack with Claude Code's marketplace system using the official schema.

**BrickLayer gap:** BrickLayer 2.0 isn't registered as a marketplace plugin. This blocks discovery via the Claude Code plugin browser.

**How to adopt:** Create `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` following Anthropic's schema.

#### 8. Passive + Active Skill Pairing
**What they do:** `frontend-design` is a passive skill (no `user-invocable`) that all other skills invoke explicitly. This separates domain knowledge (the "library") from executable commands (the "verbs").

**BrickLayer gap:** BrickLayer could benefit from a `coding-standards` or `bl-context` passive skill that all active skills invoke, loading shared project context without cluttering the slash command list.

**How to adopt:** Designate existing rule files (TDD, systematic debugging, etc.) as passive skills that active skills reference by name.

#### 9. Universal Bundle with README.txt
**What they do:** The universal ZIP includes a `README.txt` explaining which folder serves which provider, and notes that all folders are dotfiles (hidden on macOS).

**BrickLayer gap:** BrickLayer's sx-based distribution doesn't produce a universal bundle with discovery guidance for non-sx users.

#### 10. Minimal Custom YAML Parser (No External Deps)
**What they do:** `utils.js` includes a custom YAML frontmatter parser and serializer to avoid adding `js-yaml` as a dependency.

**BrickLayer gap:** If BrickLayer needs to parse skill frontmatter in JS build tooling, this is a clean pattern to copy rather than adding a YAML dep.

---

## Architecture Patterns Worth Extracting

### Pattern 1: Config-Driven Transformer Factory

```javascript
// providers.js — data-only, no logic
export const PROVIDERS = {
  'claude-code': { provider, configDir, displayName, frontmatterFields },
  'cursor': { ... },
}

// factory.js — all logic, no config
export function createTransformer(config) {
  return function transform(skills, distDir, options) { ... }
}

// index.js — re-exports both
export { createTransformer, PROVIDERS }
```

This pattern makes adding a new provider a config-only change with zero new code. Extremely clean.

### Pattern 2: Context File Hierarchy

`.impeccable.md` (project root) > CLAUDE.md Design Context section > prompted gathering

This is a non-intrusive way to persist AI context: a dedicated file that doesn't pollute the main instructions file, but optionally syncs to it if the user wants.

### Pattern 3: Build-Time vs Runtime Placeholder Resolution

Build-time (`{{model}}` → "Claude") for static content that varies per provider.
Runtime (`$ARGUMENTS`) for dynamic content that varies per invocation.

Clear separation of concerns between what's known at build time (provider identity) vs what's known at invocation time (user's specific target).

### Pattern 4: Dual API Architecture

`server/lib/api-handlers.js` contains shared logic imported by both:
- `server/index.js` (Bun dev server)
- `functions/api/*.js` (CF Pages Functions)

Zero duplication between local dev and production. Same handlers, different transport layers.

### Pattern 5: Static API Pre-Generation

JSON API responses are pre-generated at build time into `build/_data/api/`. CF `_redirects` rewrites `/api/skills` → `/_data/api/skills.json` as a 200 rewrite (not a 301 redirect). Only file downloads require actual Functions. This eliminates cold-start latency for read APIs.

---

## Recommendations for BrickLayer 2.0

### High Priority

1. **Add `.claude-plugin/` registration** — Create `plugin.json` and `marketplace.json` to register BrickLayer 2.0 with the Claude Code Marketplace. 2-file addition, immediate discoverability gain.

2. **Adopt the Mandatory Preparation pattern** — Add a "load shared context first" block to BrickLayer's most important skills. Point to BrickLayer's own context/rules skill.

3. **Add `{{placeholder}}` support** if BrickLayer plans multi-provider distribution — The build-time replacement system in `utils.js` is self-contained, ~30 lines of code, and eliminates provider-specific forks.

4. **Implement Context Persistence** — A `teach-bl` or `.bricklayer.md` pattern for persisting project-specific context (tech stack, team conventions, quality bar) that all BrickLayer skills load first. Directly parallels `teach-impeccable` + `.impeccable.md`.

### Medium Priority

5. **Consider prefixed variants** — If BrickLayer skills might clash with impeccable or other packs, a `/bl-` prefix variant prevents conflicts.

6. **Add scoring rubrics** to assessment skills — Code review, architecture review, and quality check skills become more useful with explicit 0-N scoring and named bands.

7. **Phase-gate complex skills with user checkpoints** — For BrickLayer skills that make significant decisions (refactoring strategy, architecture choices), adopt a multi-phase pattern with AskUserQuestion between analysis and action.

### Lower Priority / FYI

8. **Study the passive/active skill separation** — Consider designating BrickLayer's existing rule files as passive skills loadable by active skills via explicit invocation.

9. **Copy the DO/DON'T encoding pattern** — If BrickLayer ever needs to surface coding standards in a UI or API, encoding them as `**DO**:`/`**DON'T**:` lines in the relevant skill enables dual-use (LLM instruction + parseable data).

10. **The universal bundle pattern** — For BrickLayer distribution, consider assembling a single ZIP with all provider variants and a `README.txt` explaining the folder structure.

---

## Notable Implementation Details

- **`.gitignore` includes `.impeccable.md`** — The generated context file is gitignored so it doesn't pollute repos. Smart default.
- **`wrangler.toml` project name** — Was a bug (wrong project name) fixed in commit `7310d521`. Notes: Cloudflare Pages project name matters.
- **Trae has two separate directories** — `.trae-cn/` (China domestic) and `.trae/` (International) because they're different apps with different paths.
- **Gemini only validates `name` and `description`** — All other spec fields are parsed but silently ignored. Good to know for skill compatibility.
- **Codex uses `$` as command prefix** — Not `/`. The `replacePlaceholders()` function rewrites all `/skillname` references to `$skillname` for Codex outputs.
- **`prefers-reduced-motion` is a NEVER-ignore requirement** — Explicitly called out in `/animate`, `/overdrive`, `/polish`, and `/bolder` as accessibility requirement, not suggestion.
- **OpenCode uses a `question` tool** — The `ask_instruction` for OpenCode is "STOP and call the `question` tool to clarify." — not AskUserQuestion (which is Claude Code-specific).
- **Version coordination across 6+ files** — CLAUDE.md explicitly lists all places that need updating on version bump: `package.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `public/index.html`, plus command count in 8 additional locations when adding skills.

---

*Research completed 2026-03-31. Repository at commit `db1add7` (main branch). 240 commits total, 15k stars, Apache 2.0.*

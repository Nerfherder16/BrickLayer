# Repo Research: HKUDS/CLI-Anything
**Repo**: https://github.com/HKUDS/CLI-Anything
**Researched**: 2026-03-28

---

## Verdict Summary

CLI-Anything is a framework from HKUDS (Hong Kong University of Data Science) that automatically transforms GUI applications into agent-native, stateful command-line interfaces. The core innovation is a 7-phase automated pipeline (analyze → design → implement → test → document → generate SKILL.md → package) that produces installable Python CLIs backed by the real software engine — not reimplementations. As of March 2026 it ships 26 production harnesses with 1,917 passing tests and a Claude Code plugin that drives the whole build loop autonomously.

---

## File Inventory

### Root Level
| File/Dir | Description |
|----------|-------------|
| `README.md` (45KB) | Full framework documentation, methodology, supported platforms |
| `README_CN.md` / `README_JA.md` | Chinese and Japanese translations |
| `registry.json` (17KB) | Machine-readable catalog of all 26 CLIs with install commands, skill_md paths, categories |
| `CONTRIBUTING.md` | Contribution guide, registry update process |
| `SECURITY.md` | Security policy |
| `.claude-plugin/marketplace.json` | Claude Code marketplace metadata |
| `.github/` | CI/CD workflows |
| `.gitignore` | Standard ignore file |

### Core Plugin (`cli-anything-plugin/`)
| File | Description |
|------|-------------|
| `HARNESS.md` (37KB) | The canonical methodology doc — architecture, test framework, REPL integration, distribution |
| `README.md` (15KB) | Plugin overview, all commands, success stories, version history |
| `QUICKSTART.md` | Fast-path setup guide |
| `PUBLISHING.md` | PyPI publishing workflow |
| `repl_skin.py` (19KB) | Unified REPL terminal skin — branded banner, colored prompts, table display, prompt_toolkit integration |
| `skill_generator.py` (17KB) | Auto-generates SKILL.md files by extracting metadata from CLI packages |
| `verify-plugin.sh` | Plugin verification script |
| `commands/cli-anything.md` | Primary build command spec (7-phase pipeline) |
| `commands/refine.md` | Gap-analysis and iterative expansion command |
| `commands/test.md` | Test runner command spec |
| `commands/validate.md` | Harness validation against HARNESS.md standards |
| `commands/list.md` | Discovery command — finds all installed/generated CLIs |
| `templates/SKILL.md.template` | Jinja2 template for SKILL.md generation |
| `.claude-plugin/` | Claude Code plugin manifest |
| `scripts/` | Build scripts |

### AnyGen (`anygen/`)
| File | Description |
|------|-------------|
| `agent-harness/ANYGEN.md` | Architecture doc for AnyGen (docs/slides/website generation cloud API) |
| `agent-harness/setup.py` | Namespace package setup |
| `agent-harness/cli_anything/anygen/` | Full CLI harness with skills/SKILL.md |

### Skill-Only Directories (no harness, just SKILL.md for agent integration)
| Dir | Description |
|-----|-------------|
| `cli-hub-meta-skill/SKILL.md` | Meta-skill: teaches agents to use the hub catalog |
| `codex-skill/SKILL.md` | Skill for GitHub Copilot Codex — build/refine/test/validate modes |
| `openclaw-skill/SKILL.md` | Skill for OpenClaw — same 4-mode pattern |
| `codex-skill/agents/` | Agent definitions for Codex integration |
| `codex-skill/scripts/` | Helper scripts |

### Multi-Platform Command Sets
| Dir | Description |
|-----|-------------|
| `opencode-commands/` | 5 .md command files for OpenCode AI coding agent |
| `qoder-plugin/setup-qodercli.sh` | Setup script for Qodercli integration |

### Hub Documentation (`docs/hub/`)
| File | Description |
|------|-------------|
| `SKILL.md` / `SKILL.txt` | Hosted catalog skill — agents fetch https://hkuds.github.io/CLI-Anything/SKILL.txt to discover all available tools |
| `index.html` (24KB) | GitHub Pages hub website |
| `_config.yml` | Jekyll config |

### Production Harnesses (26 total — each `<software>/agent-harness/` contains full implementation)
| Directory | Category | Backend |
|-----------|----------|---------|
| `adguardhome/` | network | REST API |
| `audacity/` | audio | sox |
| `blender/` | 3D | blender --background --python |
| `browser/` | web | DOMShell MCP (Chrome Accessibility Tree → virtual filesystem) |
| `comfyui/` | AI | ComfyUI REST API |
| `drawio/` | diagrams | draw.io CLI |
| `freecad/` | 3D CAD | FreeCAD CLI (258 commands) |
| `gimp/` | image | Pillow/GEGL |
| `inkscape/` | image | inkscape --export-filename |
| `iterm2/` | devops | iTerm2 Python API |
| `kdenlive/` | video | melt (MLT) |
| `krita/` | image | Krita CLI export |
| `libreoffice/` | office | headless LibreOffice |
| `mermaid/` | diagrams | Mermaid Live Editor state |
| `mubu/` | office | Mubu desktop data |
| `musescore/` | music | MuseScore 4 CLI |
| `notebooklm/` | AI | notebooklm-py CLI |
| `novita/` | AI | OpenAI-compatible API |
| `obs-studio/` | streaming | OBS Studio CLI |
| `ollama/` | AI | Ollama REST API |
| `renderdoc/` | graphics | RenderDoc Python bindings |
| `rms/` | network | Teltonika RMS REST API |
| `shotcut/` | video | melt + ffmpeg |
| `sketch/` | design | sketch-constructor (Node.js) |
| `zoom/` | communication | Zoom REST API OAuth2 |

### Test Infrastructure
| File | Description |
|------|-------------|
| `skill_generation/tests/test_skill_path.py` (7KB) | Tests SKILL.md auto-detection after pip install, tests all 18 harnesses for YAML frontmatter + command group presence |

---

## Architecture Overview

### Core Design Philosophy

"The CLI MUST call the actual software for rendering and export — not reimplement the software's functionality." Every harness is a thin wrapper that generates native project formats (MLT XML for Kdenlive/Shotcut, ODF ZIP for LibreOffice, .blend scripts for Blender) then invokes the real software binary for rendering/export.

### 7-Phase Build Pipeline

```
Phase 0: Source Acquisition (local path or git clone from GitHub URL)
Phase 1: Codebase Analysis → SOFTWARE.md (backend engine, data model, GUI-API mapping)
Phase 2: CLI Architecture Design → command groups, state model, output formats
Phase 3: Implementation → Click CLI + REPL + JSON mode + session state
Phase 4: Test Planning → TEST.md Part 1 (plan)
Phase 5: Test Implementation → test_core.py + test_full_e2e.py + subprocess tests
Phase 6: Test Documentation → TEST.md Part 2 (results, pytest output)
Phase 6.5: SKILL.md Generation → skill_generator.py extracts metadata, writes SKILL.md
Phase 7: PyPI Packaging → find_namespace_packages, console_scripts, pip install -e .
```

### Standard Harness Structure

```
<software>/agent-harness/
├── <SOFTWARE>.md              # Architecture analysis SOP
├── setup.py                   # PEP 420 namespace package
└── cli_anything/              # NO __init__.py (namespace root)
    └── <software>/            # HAS __init__.py
        ├── <software>_cli.py  # Click CLI entry point
        ├── __init__.py
        ├── __main__.py        # python -m cli_anything.<software>
        ├── core/
        │   ├── project.py     # Project management
        │   ├── session.py     # Undo/redo (50-level stack)
        │   └── export.py      # Rendering pipeline
        ├── skills/
        │   └── SKILL.md       # Agent-discoverable skill definition
        ├── utils/
        │   └── repl_skin.py   # Branded REPL terminal (copied from plugin)
        └── tests/
            ├── TEST.md        # Plan + results
            ├── test_core.py   # Unit tests (synthetic data)
            └── test_full_e2e.py # E2E tests (real files)
```

### REPL Loop Pattern

The CLI defaults to REPL mode when invoked without subcommands (`invoke_without_command=True`). The REPL loop uses `shlex.split()` to parse input, calls `cli.main(args, standalone_mode=False)`, catches `SystemExit` to keep the loop alive. Uses `prompt_toolkit` with `FileHistory` for persistent history and auto-suggest. The `ReplSkin` class provides branded banner, colored prompts, status messages, and tables via a unified interface with per-software accent colors.

### Session State / Undo-Redo

State is maintained in a global `Session` object with deep-copy snapshots at 50-level depth. Commands call `sess.snapshot("operation description")` before mutation. `session undo` and `session redo` commands are standard in every harness.

### Dual Output Mode

Every command checks `_json_output` flag. `--json` on the root CLI group sets it globally; all subcommands branch on this flag. JSON output uses `json.dumps(data, indent=2, default=str)`. Human output uses ReplSkin helpers (`success()`, `error()`, `warning()`, `table()`).

### SKILL.md Discoverability System

SKILL.md files have YAML frontmatter (`name`, `description`) that agent platforms use as triggers. `skill_generator.py` auto-generates them from the CLI package by: (1) finding the `cli_anything/<software>/` dir, (2) extracting intro from README.md, (3) extracting version from setup.py, (4) parsing Click group/command decorators with regex to build command groups, (5) generating examples. The `ReplSkin` banner auto-detects and displays the SKILL.md path at startup so agents can read it.

### Hub Catalog Pattern

`registry.json` is the machine-readable catalog. `docs/hub/SKILL.txt` is a hosted catalog that agents fetch to discover all available tools without knowing the repo structure. The hub is published at https://hkuds.github.io/CLI-Anything/.

### Multi-Platform Plugin System

The same methodology is packaged as plugins/skills for multiple AI coding agents:
- **Claude Code**: `.claude-plugin/` + `commands/*.md` slash commands
- **OpenCode**: `opencode-commands/*.md`
- **Codex**: `codex-skill/SKILL.md` + agents/
- **OpenClaw**: `openclaw-skill/SKILL.md`
- **Qodercli**: `qoder-plugin/setup-qodercli.sh`

### Test Framework: Four Layers

1. **Unit tests** (`test_core.py`) — synthetic data, no external deps
2. **Native E2E tests** — validate project file format (XML structure, ZIP integrity)
3. **Real backend E2E tests** — invoke actual software, verify output via magic bytes
4. **Subprocess tests** (`TestCLISubprocess`) — test installed CLI command via `_resolve_cli()`, fall back to `python -m` in dev. `CLI_ANYTHING_FORCE_INSTALLED=1` env var forces installed path for release validation. No graceful degradation: real software must be installed or tests fail.

---

## Key Innovations

### 1. Agent-Native CLI as First-Class Artifact

Not "scripts to run software" but "installable Python packages with SKILL.md that agents discover and use autonomously." The package installs to PATH, the SKILL.md installs with the package data, the REPL banner shows the SKILL.md path — end-to-end designed for agent consumption.

### 2. SKILL.md as Agent Capability Advertisement

YAML frontmatter (`name`, `description`) acts as a trigger specification. Agents search `~/.local/lib/python*/site-packages/cli_anything/*/skills/SKILL.md` or use `which cli-anything-*` to discover capabilities. The `skill_generator.py` auto-extracts this from source code structure — no manual authoring needed.

### 3. PEP 420 Namespace Package Strategy for Tool Isolation

Using `find_namespace_packages(include=["cli_anything.*"])` with no `__init__.py` in the `cli_anything/` root allows dozens of separately-installed CLI packages to coexist in the same Python environment without conflicts. Each tool is `pip install cli-anything-<software>` independently.

### 4. "Real Software Backend" Principle

Explicitly forbids reimplementing software functionality. The CLI generates valid native format files (MLT XML, ODF ZIP, bpy scripts) then shells out to the real binary. This is architecturally sound: agents get full software capability, not a subset.

### 5. Rendering Gap Awareness

Documents the "rendering gap" problem explicitly: naive approaches (calling ffmpeg directly on raw media) miss project-level effects because they bypass the application's compositor. Solutions: use native renderer, build filter translation layers, or generate scripts. This is a non-obvious failure mode that the framework explicitly addresses.

### 6. `_resolve_cli()` Test Pattern

Subprocess tests use a resolver that finds the installed CLI command by name, falling back to `python -m cli_anything.<software>` in dev mode. `CLI_ANYTHING_FORCE_INSTALLED=1` forces the installed path. This cleanly separates dev and release test modes.

### 7. Gap Analysis Refinement Loop

The `/cli-anything:refine` command formalizes iterative capability expansion: inventory current coverage → re-scan software source → gap analysis with priority tiers (high-impact, easy wins, composability) → user confirmation → implement → test → document. This is a structured Karpathy-style iterative refinement loop for CLI capability.

### 8. Browser CLI via Accessibility Tree

The `browser` harness maps Chrome's Accessibility Tree to a virtual filesystem via DOMShell MCP. This is a novel agent-native browser control pattern that avoids fragile CSS selectors.

### 9. Multi-Agent Platform Distribution

Same methodology packaged as native plugins for 5+ AI coding platforms (Claude Code, OpenCode, Codex, OpenClaw, Qodercli). Platform-agnostic methodology with platform-specific packaging.

### 10. Validation as Automated Quality Gate

`/cli-anything:validate` checks 8 categories: directory structure, required files, CLI standards, core modules, testing requirements, documentation, PyPI packaging, code quality. Produces pass/fail per category before merge.

---

## Feature Gap Analysis

| Feature | In CLI-Anything | In BrickLayer 2.0 | Gap Level | Notes |
|---------|----------------|-------------------|-----------|-------|
| SKILL.md agent capability advertisement | Yes — YAML frontmatter, auto-generated, bundled with package | Partial — agent_registry.yml covers internal fleet, no external discovery format | MEDIUM | BL agents aren't discoverable by external agent platforms; SKILL.md format is a standard |
| Hosted tool catalog (SKILL.txt) | Yes — https://hkuds.github.io/CLI-Anything/SKILL.txt | No — no hosted discovery endpoint | LOW | Would matter if BL tools needed to be shared externally |
| PEP 420 namespace package strategy | Yes — all harnesses under `cli_anything.*` | N/A — BL doesn't publish Python packages | N/A | Different scope |
| REPL with undo/redo + prompt_toolkit | Yes — 50-level deep-copy stack, FileHistory, auto-suggest | No — agent interactions are stateless prompt-response | HIGH | BL coding agents could benefit from stateful session tracking across tool calls |
| Dual output mode (human + JSON --flag) | Yes — `--json` flag on every CLI command | Partial — findings use TSV/markdown, no machine-JSON mode | MEDIUM | BL research output could benefit from structured JSON alongside markdown |
| Gap analysis refinement loop | Yes — `/refine` with priority tiers + user confirmation | Partial — hypothesis-generator creates Wave 2 questions, but no structured gap analysis by domain | HIGH | The refine pattern (inventory → gap → prioritize → confirm → implement) is more rigorous than BL's hypothesis approach |
| 4-layer test framework (unit/native-e2e/real-backend-e2e/subprocess) | Yes — explicit layering with HARNESS.md standards | Partial — TDD enforcement exists but no explicit 4-layer taxonomy | MEDIUM | BL's TDD hook enforces tests exist but doesn't enforce the layer structure |
| Subprocess test with installed command verification | Yes — `_resolve_cli()` + `CLI_ANYTHING_FORCE_INSTALLED=1` | No | MEDIUM | BL's developer agent tests modules, not installed CLI endpoints |
| `_resolve_cli()` dev/release mode switching | Yes | No | LOW | Useful pattern for any installed tool testing |
| Architecture SOP per target (SOFTWARE.md) | Yes — per-harness architecture analysis before implementation | Partial — project-brief.md is similar but human-authored, not agent-generated | HIGH | CLI-Anything auto-generates architecture docs from source code; BL requires human authoring |
| Rendering gap documentation | Yes — explicit pitfall with solutions | No formal equivalent | MEDIUM | BL research campaigns don't model this specific class of failure |
| Validation command (automated quality gate) | Yes — 8-category validation | Partial — /verify exists but is post-build, not pre-merge quality gate | MEDIUM | BL's /verify is post-build; CLI-Anything's validate can run at any point |
| Multi-platform plugin packaging | Yes — Claude Code, OpenCode, Codex, OpenClaw, Qodercli | No — BL is Claude Code only | LOW | Not a priority unless BL needs to run in other agents |
| Registry.json machine-readable catalog | Yes | Partial — agent_registry.yml covers internal agents only | MEDIUM | BL could benefit from a machine-readable external tool catalog |
| Per-software accent colors in REPL | Yes — each software gets unique ANSI color in ReplSkin | No — Kiln is the UI, not REPL | N/A | Different UI model |
| Browser CLI via Accessibility Tree | Yes — DOMShell MCP mapping | No equivalent | HIGH | Playwright covers browser automation but not via accessibility-tree-as-filesystem |
| Iterative refinement with focus argument | Yes — `/refine /software "particle systems"` | Partial — hypothesis-generator, but no natural language focus narrowing | MEDIUM | BL could allow question generation to be scoped to a domain focus |
| Auto-generate architecture docs from source | Yes — Phase 1 analysis produces SOFTWARE.md | No — project-brief.md is human-authored | HIGH | This is a significant automation win for the developer workflow |
| Karpathy-style iterative loop | Implicit — build → refine → test → validate cycles | Explicit — wave-based research loop with synthesis | BL STRONGER | BL's wave loop is more rigorous for research; CLI-Anything's is more rigorous for code |
| Wave-based research with findings | No | Yes — BL's core capability | BL UNIQUE | |
| DSPy prompt optimization | No | Yes — improve_agent.py loop | BL UNIQUE | |
| Semantic + LLM routing (4-layer) | No | Yes — Mortar 4-layer routing | BL UNIQUE | |
| PageRank pattern scoring | No | Yes — masonry-pagerank | BL UNIQUE | |
| HNSW reasoning bank | No | Yes | BL UNIQUE | |
| Claims-based human escalation | No | Yes — .autopilot/claims.json | BL UNIQUE | |

---

## Top 5 Recommendations

### 1. Adopt the SKILL.md Capability Advertisement Format

BrickLayer agents (mortar, trowel, developer, etc.) should each have a SKILL.md file with YAML frontmatter that external platforms can discover. This makes BL's specialist fleet accessible to Codex, OpenCode, and other agents. The `skill_generator.py` pattern — auto-extracting metadata from agent source code — is directly applicable to BL's `.claude/agents/*.md` files.

**Implementation**: Write a `masonry/scripts/generate_skill_mds.py` that reads each agent `.md` file, extracts the frontmatter and capability description, and outputs a `skills/` directory with SKILL.md per agent plus a catalog SKILL.txt.

### 2. Adopt the Gap Analysis Refinement Pattern for Research Campaigns

CLI-Anything's `/refine` command formalizes: inventory current coverage → re-scan source → gap analysis with priority tiers (high-impact, easy wins, composability) → user confirmation → implement → document. BL's hypothesis-generator is ad hoc by comparison. Adding a structured gap analysis step between waves — comparing what's been answered against what domains haven't been covered — would improve campaign quality.

**Implementation**: Add a `gap-analyst` agent that reads `findings/` + `questions.md`, maps coverage by domain, identifies uncovered high-impact areas, and produces a prioritized Wave N+1 question set with explicit gap reasoning.

### 3. Adopt the Architecture SOP Auto-Generation Pattern

CLI-Anything's Phase 1 auto-generates a `SOFTWARE.md` architecture doc by analyzing source code before implementation. BL's project-brief.md is human-authored. For developer workflows, the BL developer agent could auto-generate a codebase architecture doc (`CODEBASE.md`) before starting a build task by analyzing the repo structure, key files, and existing patterns — then inject this into the worker agent context.

**Implementation**: Add a `codebase-analyst` agent that runs pre-/build to analyze the target codebase and write `.autopilot/codebase-analysis.md`. The developer agent reads this instead of exploring blindly.

### 4. Adopt the 4-Layer Test Taxonomy and `_resolve_cli()` Pattern

BL's TDD hook enforces test file existence but not test layer structure. CLI-Anything's 4 layers (unit/native-e2e/real-backend-e2e/subprocess) are worth formalizing in BL's TDD enforcement. The `_resolve_cli()` pattern — finding installed command by name, falling back to module invocation, switchable via env var — is a clean pattern for any BL agent that produces installed tools.

**Implementation**: Update `masonry-tdd-enforcer.js` to check for both `test_core.py` (unit) and `test_full_e2e.py` (integration) rather than just any test file. Add `_resolve_cli()` as a standard utility in BL's template for developer agents building CLIs.

### 5. Adopt Browser CLI via Accessibility Tree (DOMShell Pattern)

The `browser` harness maps Chrome's Accessibility Tree to a virtual filesystem via DOMShell MCP. This is architecturally superior to CSS-selector-based Playwright for agents: the tree is stable, semantic, and doesn't break on style changes. BL's research campaigns that require web data collection could use this instead of Playwright scraping.

**Implementation**: Add `cli-anything-browser` to BL's available tools. Create a `web-researcher` agent variant that uses DOMShell CLI for structured web navigation rather than Playwright.

---

## Harvestable Items

### Directly Adoptable Code/Patterns
1. **`repl_skin.py`** — Copy verbatim into any BL Python tool that needs an interactive REPL. The `ReplSkin` class is self-contained, zero-external-dependency for core styling, optional `prompt_toolkit` integration.
2. **`skill_generator.py`** — Adapt to auto-generate SKILL.md files for BL agents from their `.md` files.
3. **`SKILL.md.template`** (Jinja2) — Use as template for BL agent capability documents.
4. **YAML frontmatter format** for skills:
   ```yaml
   ---
   name: "agent-name"
   description: "One-line capability description for agent platform triggering"
   ---
   ```
5. **`_resolve_cli()` pattern** for subprocess tests — useful in any BL tool that installs a CLI.
6. **`CLI_ANYTHING_FORCE_INSTALLED=1`** env var pattern for dev/release mode switching in tests.
7. **50-level deep-copy undo/redo stack** (`session.py` pattern) — useful for BL's stateful agent sessions.
8. **`--json` flag on root CLI group** propagated globally — clean pattern for dual-mode output.

### Process Patterns to Adopt
9. **Gap analysis with priority tiers** (high-impact / easy wins / composability) — formalize this in BL's hypothesis-generator.
10. **Pre-implementation architecture SOP auto-generation** (Phase 1 analysis → SOFTWARE.md) — add to BL's /build pre-flight.
11. **Validation command as quality gate** — expand BL's /verify to include a pre-merge validate pass.
12. **4-layer test taxonomy** — formalize in BL's TDD enforcement hook.
13. **TEST.md pattern** (plan first, append results after) — BL could adopt this for build task documentation.
14. **No graceful degradation principle for required dependencies** — BL tests should fail hard when required tools are absent, not silently skip.
15. **Rendering gap documentation** — BL's developer agent should be aware of this class of failure when building any pipeline that involves external rendering tools.
16. **"Focus" argument on refinement** — `/refine /path "particle systems"` narrows scope. BL could add `/masonry-run --focus "pricing model"` to scope a wave to a specific domain.

### Structural Patterns
17. **PEP 420 namespace packages** — if BL ever packages its tools for distribution, use `find_namespace_packages(include=["bricklayer.*"])`.
18. **Registry.json catalog pattern** — BL should maintain a machine-readable `masonry/tool-catalog.json` of all available masonry tools with their capabilities, install commands, and skill paths.
19. **Hosted SKILL.txt catalog** — publish BL's agent capabilities to a hosted endpoint so external platforms can discover them.
20. **Per-agent architecture docs** — each BL agent `.md` should have an "Architecture" section auto-generated from its behavior patterns.

---

## Assessment Notes

### What CLI-Anything Does Better Than BrickLayer
- **Developer agent workflow**: The 7-phase build pipeline is more rigorous and produces higher-quality installable artifacts than BL's current developer agent.
- **Test layer structure**: 4 explicit layers with no graceful degradation is stricter than BL's current TDD enforcement.
- **External discoverability**: SKILL.md + hosted catalog makes tools findable by any agent platform; BL's agent registry is internal only.
- **Iterative refinement formalization**: The refine loop with user confirmation is more structured than BL's ad hoc wave generation.

### What BrickLayer Does Better
- **Research depth**: Wave-based campaigns with EMA training, PageRank pattern scoring, and HNSW reasoning bank are far beyond CLI-Anything's scope.
- **Routing intelligence**: Mortar's 4-layer routing (deterministic → semantic → LLM → fallback) has no equivalent in CLI-Anything.
- **Prompt optimization**: DSPy improve_agent.py loop is unique to BL.
- **Human escalation**: Claims-based escalation via `.autopilot/claims.json` + HUD indicator has no equivalent.
- **Multi-agent orchestration**: BL's fleet with scoring, telemetry, and EMA training is a more sophisticated agent management system.

### Overall Verdict
CLI-Anything is a mature, production-tested framework for a specific problem (GUI-to-CLI for agents) that BL doesn't cover well. The SKILL.md discoverability pattern and the 4-layer test taxonomy are the highest-value direct imports. The gap analysis refinement loop and pre-build architecture SOP auto-generation are the highest-value process patterns. BL should harvest these without duplicating CLI-Anything's core mission.

---

```json
{
  "repo": "HKUDS/CLI-Anything",
  "report_path": "docs/repo-research/HKUDS-CLI-Anything.md",
  "files_analyzed": 62,
  "high_priority_gaps": 5,
  "top_recommendation": "Adopt SKILL.md capability advertisement format for BL agents + implement gap-analyst agent for structured wave refinement",
  "verdict": "Production-grade CLI-for-agents framework. Not a research system — BL shouldn't replicate it. Harvest: SKILL.md format, skill_generator.py, repl_skin.py, 4-layer test taxonomy, gap-analysis refinement loop, and pre-build architecture SOP auto-generation."
}
```

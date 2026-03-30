# Repo Research: anthropics/skills

**Repo**: https://github.com/anthropics/skills
**Researched**: 2026-03-30
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

The anthropics/skills repo is Anthropic's official collection of "Agent Skills" -- self-contained, metadata-driven instruction packages that Claude loads dynamically based on task context. It is fundamentally different from BrickLayer's agent system: BrickLayer has 100+ specialist agents with a multi-layer routing engine and campaign orchestration, while this repo defines a formal standard for portable, sharable skill packages with YAML frontmatter, progressive disclosure (metadata -> body -> bundled resources), and a plugin marketplace system. BrickLayer beats it in agent orchestration depth, research campaigns, and autonomous workflows, but the Agent Skills standard introduces a formal skill packaging format, a description-optimization eval loop (skill-creator), and a Claude Code plugin marketplace integration that BrickLayer should adopt for its own skill distribution.

---

## File Inventory

### Root Level
| File | Description |
|------|-------------|
| `.gitignore` | Standard ignores (.DS_Store, __pycache__, .idea/, .vscode/) |
| `README.md` | Top-level README: explains skills concept, installation via Claude Code plugins, skill structure |
| `THIRD_PARTY_NOTICES.md` | License attributions for bundled dependencies |

### `.claude-plugin/`
| File | Description |
|------|-------------|
| `marketplace.json` | Claude Code Plugin marketplace manifest -- defines 3 plugin bundles (document-skills, example-skills, claude-api) with skill path references |

### `spec/`
| File | Description |
|------|-------------|
| `agent-skills-spec.md` | Redirect to https://agentskills.io/specification (the formal Agent Skills specification) |

### `template/`
| File | Description |
|------|-------------|
| `SKILL.md` | Minimal skill template: YAML frontmatter (name, description) + placeholder body |

### `skills/algorithmic-art/`
| File | Description |
|------|-------------|
| `SKILL.md` | Generative art skill: philosophy creation -> p5.js implementation with seeded randomness, interactive parameters |
| `LICENSE.txt` | Apache 2.0 |
| `templates/` | Contains viewer.html template and generator_template.js reference |

### `skills/brand-guidelines/`
| File | Description |
|------|-------------|
| `SKILL.md` | Anthropic brand color/typography application guidelines |
| `LICENSE.txt` | Apache 2.0 |

### `skills/canvas-design/`
| File | Description |
|------|-------------|
| `SKILL.md` | Visual art creation: design philosophy -> canvas rendering (PDF/PNG). Emphasis on museum-quality craftsmanship |
| `LICENSE.txt` | Apache 2.0 |
| `canvas-fonts/` | Font files for design work |

### `skills/claude-api/`
| File | Description |
|------|-------------|
| `SKILL.md` | Comprehensive Claude API/SDK documentation skill. Language detection, surface selection (API vs Agent SDK), model catalog, thinking/effort reference |
| `LICENSE.txt` | Apache 2.0 |
| `python/` | Python-specific API docs |
| `typescript/` | TypeScript-specific API docs |
| `java/` | Java SDK docs |
| `go/` | Go SDK docs |
| `ruby/` | Ruby SDK docs |
| `csharp/` | C# SDK docs |
| `php/` | PHP SDK docs |
| `curl/` | cURL/raw HTTP examples |
| `shared/` | Cross-language docs (tool-use-concepts, error-codes, prompt-caching, models, live-sources) |

### `skills/doc-coauthoring/`
| File | Description |
|------|-------------|
| `SKILL.md` | 3-stage document co-authoring workflow: Context Gathering -> Refinement/Structure -> Reader Testing (uses sub-agent for fresh-eyes validation) |

### `skills/docx/`
| File | Description |
|------|-------------|
| `SKILL.md` | Word document creation/editing skill. Uses docx-js for creation, XML manipulation for editing, pandoc for reading. Comprehensive XML reference for tracked changes, comments, images |
| `LICENSE.txt` | Proprietary/source-available |
| `scripts/` | Helper scripts (unpack.py, pack.py, validate.py, accept_changes.py, comment.py, office/soffice.py) |

### `skills/frontend-design/`
| File | Description |
|------|-------------|
| `SKILL.md` | Frontend design skill emphasizing distinctive aesthetics. Anti "AI slop" guidelines, bold typography choices, spatial composition, animation patterns |
| `LICENSE.txt` | Apache 2.0 (variant) |

### `skills/internal-comms/`
| File | Description |
|------|-------------|
| `SKILL.md` | Internal communications writing skill. Routes to format-specific guidelines (3P updates, newsletters, FAQs) |
| `LICENSE.txt` | Apache 2.0 |
| `examples/` | Example templates for different communication types |

### `skills/mcp-builder/`
| File | Description |
|------|-------------|
| `SKILL.md` | MCP server development guide: 4-phase workflow (Research/Plan -> Implement -> Review/Test -> Create Evals). Recommends TypeScript, covers both Python and TS SDKs |
| `LICENSE.txt` | Apache 2.0 |
| `reference/` | Contains mcp_best_practices.md, node_mcp_server.md, python_mcp_server.md, evaluation.md |
| `scripts/` | Testing/eval scripts |

### `skills/pdf/`
| File | Description |
|------|-------------|
| `SKILL.md` | PDF processing skill using pypdf, pdfplumber, reportlab, qpdf. Covers merge, split, extract, OCR, watermark, form filling |
| `LICENSE.txt` | Proprietary/source-available |
| `forms.md` | Detailed PDF form filling reference |
| `reference.md` | Extended PDF processing reference |
| `scripts/` | Helper scripts |

### `skills/pptx/`
| File | Description |
|------|-------------|
| `SKILL.md` | PowerPoint creation/editing skill. Design guidelines with color palettes, typography pairings, QA workflow using subagents for visual inspection |
| `LICENSE.txt` | Proprietary/source-available |
| `editing.md` | Template-based editing guide |
| `pptxgenjs.md` | From-scratch creation with pptxgenjs |
| `scripts/` | thumbnail.py, office helpers |

### `skills/skill-creator/`
| File | Description |
|------|-------------|
| `SKILL.md` | Meta-skill for creating and optimizing other skills. Full eval loop: draft -> test -> grade -> benchmark -> iterate. Description optimization via train/test split. 33KB -- the largest and most complex skill |
| `LICENSE.txt` | Apache 2.0 |
| `agents/analyzer.md` | Sub-agent for analyzing benchmark results (pattern detection, variance analysis) |
| `agents/comparator.md` | Sub-agent for blind A/B comparison between skill versions |
| `agents/grader.md` | Sub-agent for evaluating assertions against outputs |
| `references/schemas.md` | JSON schemas for evals.json, grading.json, benchmark.json |
| `scripts/__init__.py` | Package marker |
| `scripts/aggregate_benchmark.py` | Aggregates grading results into benchmark.json with mean +/- stddev |
| `scripts/generate_report.py` | Generates HTML report from benchmark data |
| `scripts/improve_description.py` | Optimizes skill description for better triggering accuracy |
| `scripts/package_skill.py` | Packages skill folder into .skill distributable |
| `scripts/quick_validate.py` | Quick validation of skill structure |
| `scripts/run_eval.py` | Runs skill triggering evaluation (uses `claude -p`) |
| `scripts/run_loop.py` | Full optimization loop: eval -> optimize -> compare (train/test split, 3 runs per query for reliability) |
| `scripts/utils.py` | Shared utilities |
| `eval-viewer/generate_review.py` | Generates interactive HTML eval viewer with side-by-side output comparison |
| `eval-viewer/viewer.html` | HTML template for the eval viewer (45KB, full-featured SPA) |
| `assets/` | Contains eval_review.html template for trigger eval review |

### `skills/slack-gif-creator/`
| File | Description |
|------|-------------|
| `SKILL.md` | Animated GIF creation for Slack. PIL-based workflow, GIFBuilder utility, easing functions, animation concepts |
| `LICENSE.txt` | Apache 2.0 |
| `core/` | Python modules: gif_builder.py, validators.py, easing.py, frame_composer.py |
| `requirements.txt` | pillow, imageio, numpy |

### `skills/theme-factory/`
| File | Description |
|------|-------------|
| `SKILL.md` | Styling toolkit with 10 pre-set color/font themes. Includes theme showcase PDF |
| `LICENSE.txt` | Apache 2.0 |
| `theme-showcase.pdf` | Visual preview of all 10 themes |
| `themes/` | Individual theme definition files |

### `skills/web-artifacts-builder/`
| File | Description |
|------|-------------|
| `SKILL.md` | React+TypeScript+Tailwind artifact builder for claude.ai. Init script -> develop -> bundle to single HTML |
| `LICENSE.txt` | Apache 2.0 |
| `scripts/` | init-artifact.sh, bundle-artifact.sh |

### `skills/webapp-testing/`
| File | Description |
|------|-------------|
| `SKILL.md` | Playwright-based webapp testing. Decision tree: static vs dynamic, with_server.py helper, reconnaissance-then-action pattern |
| `LICENSE.txt` | Apache 2.0 |
| `examples/` | element_discovery.py, static_html_automation.py, console_logging.py |
| `scripts/` | with_server.py and helpers |

### `skills/xlsx/`
| File | Description |
|------|-------------|
| `SKILL.md` | Excel creation/editing skill. Financial model standards (color coding, formula rules), openpyxl patterns, pandas integration, formula recalculation via LibreOffice |
| `LICENSE.txt` | Proprietary/source-available |
| `scripts/` | recalc.py, office helpers |

**Total files analyzed**: ~90+ (including all SKILL.md files, sub-directory listings, scripts directories, agent definitions, and reference files)

---

## Architecture Overview

### Core Concept: Skills as Portable Instruction Packages

The Agent Skills system is architecturally simple but strategically significant:

1. **A skill = a directory with a SKILL.md file** (YAML frontmatter + markdown instructions)
2. **Three-level progressive disclosure**:
   - Level 1: `name` + `description` (~100 tokens) -- always in context for all skills
   - Level 2: SKILL.md body (recommended <5000 tokens) -- loaded when skill activates
   - Level 3: Bundled resources (scripts/, references/, assets/) -- loaded on demand
3. **Activation is description-driven**: Claude reads all skill descriptions at startup and decides which to activate based on task context. No explicit routing layer needed.
4. **Self-contained**: Each skill bundles its own scripts, references, and assets. No external dependencies between skills.

### Plugin Marketplace System

The `.claude-plugin/marketplace.json` defines a marketplace manifest:
- Named plugin bundles (e.g., "document-skills", "example-skills", "claude-api")
- Each bundle lists skill directory paths
- Users install via `/plugin marketplace add anthropics/skills` then `/plugin install document-skills@anthropic-agent-skills`
- Skills activate automatically based on description matching

### Skill-Creator: The Meta-Skill

The `skill-creator` skill is the most architecturally sophisticated component:
- **Eval framework**: Structured test case definition, parallel subagent execution (with-skill vs baseline), timing capture
- **Grading system**: Assertion-based grading with sub-agent graders, benchmark aggregation (mean +/- stddev)
- **Description optimization loop**: Train/test split (60/40), 3 runs per query for reliability, iterative improvement via `claude -p` subprocess
- **HTML eval viewer**: Full SPA for side-by-side output comparison, benchmark visualization, feedback collection
- **Blind A/B comparison**: Independent agent compares outputs without knowing which version produced them

### How Skills Differ from BrickLayer Agents

| Aspect | Agent Skills | BrickLayer Agents |
|--------|-------------|-------------------|
| Format | YAML frontmatter + markdown (SKILL.md) | Markdown files (.md) with structured sections |
| Activation | Description-based matching by Claude | 4-layer routing (deterministic -> semantic -> LLM -> fallback) |
| Scope | Single-task instruction packages | Specialist identities with tools, capabilities, modes |
| Orchestration | None (Claude decides) | Mortar session router, Trowel campaign conductor |
| Distribution | .skill files, plugin marketplace | sx vault, agent_registry.yml |
| Optimization | skill-creator eval loop, description tuning | improve_agent.py (eval -> optimize -> compare) |
| Progressive loading | 3-tier (metadata -> body -> resources) | All-or-nothing agent .md loading |

---

## Agent Catalog

The repo does not contain "agents" in the BrickLayer sense. It contains **skills** (instruction packages) and **sub-agents** (within skill-creator only).

### Sub-Agents in skill-creator

| Agent | Purpose | Invocation |
|-------|---------|------------|
| `grader` | Evaluates assertions against skill outputs using structured criteria | Spawned by skill-creator during Step 4 of eval |
| `comparator` | Blind A/B comparison between two skill version outputs | Optional, for rigorous comparison |
| `analyzer` | Analyzes benchmark results for patterns, variance, non-discriminating assertions | Spawned after benchmark aggregation |

### Skills as "Agents"

Each skill functions as a specialized capability package. The most agent-like skills:

1. **skill-creator** -- Full autonomous workflow: interview user, draft skill, run evals, grade, iterate, optimize descriptions
2. **doc-coauthoring** -- 3-stage guided workflow with sub-agent reader testing
3. **mcp-builder** -- 4-phase development guide with eval creation
4. **claude-api** -- Language detection, surface selection, reading guide routing

---

## Feature Gap Analysis

| Feature | In anthropics/skills | In BrickLayer 2.0 | Gap Level | Notes |
|---------|---------------------|-------------------|-----------|-------|
| **Formal skill packaging standard (SKILL.md + frontmatter)** | Yes -- YAML frontmatter with name, description, license, compatibility, metadata, allowed-tools | BrickLayer uses .md agent files with less structured metadata | **MEDIUM** | BrickLayer agent .md files lack a formal frontmatter standard. The Agent Skills spec (name, description, license, compatibility, metadata, allowed-tools) would make BrickLayer agents more portable and discoverable. |
| **Progressive disclosure (3-tier loading)** | Yes -- metadata always loaded, body on activation, resources on demand | No -- agent .md files loaded fully on spawn | **HIGH** | BrickLayer loads entire agent definitions into context. For large agents, this wastes tokens. Progressive disclosure (load description for routing, load body on activation, load references on demand) would significantly improve context efficiency. |
| **Plugin marketplace system** | Yes -- `.claude-plugin/marketplace.json` with `/plugin install` CLI | No -- agents distributed via sx vault or manual copy | **MEDIUM** | BrickLayer uses sx vault for sharing. A marketplace.json manifest could enable one-click agent/skill bundle installation. |
| **Description-driven triggering** | Yes -- Claude reads all descriptions and self-selects relevant skills | BrickLayer uses 4-layer routing (deterministic -> semantic -> LLM -> fallback) | **LOW** | BrickLayer's routing is significantly more sophisticated. However, description quality matters for the semantic and LLM routing layers. |
| **Description optimization loop** | Yes -- skill-creator's run_loop.py: train/test split, 3 runs per query, iterative improvement | BrickLayer has improve_agent.py but no description-specific optimization | **HIGH** | BrickLayer's improve_agent.py optimizes agent instructions but not routing descriptions. A dedicated description optimizer targeting the semantic routing layer (Ollama cosine similarity at threshold 0.75) would improve deterministic routing hit rates. |
| **Skill eval framework with viewer** | Yes -- structured evals, parallel with-skill vs baseline runs, HTML viewer for side-by-side comparison, grading, benchmarking | BrickLayer has scored_all.jsonl and eval_agent.py | **MEDIUM** | BrickLayer's eval system scores agent output quality but lacks: (a) side-by-side with/without comparison, (b) interactive HTML eval viewer, (c) baseline runs for A/B testing |
| **Blind A/B comparison** | Yes -- comparator.md sub-agent judges quality without knowing which version | No equivalent | **MEDIUM** | Useful for objectively comparing agent instruction versions without bias |
| **Document generation skills (docx/pdf/pptx/xlsx)** | Yes -- production-quality document creation with XML editing, formula recalculation, tracked changes | No equivalent skills | **LOW** | BrickLayer is focused on research/dev orchestration, not document generation. These skills are useful but not core to BrickLayer's mission. Could be installed as plugins if Claude Code Plugin marketplace is adopted. |
| **Claude API documentation skill** | Yes -- comprehensive, auto-synced API reference with language detection, model catalog, thinking/effort reference | No equivalent | **MEDIUM** | BrickLayer agents that interact with Claude API (e.g., improve_agent.py using `claude -p`) would benefit from having current API reference in-context. The claude-api skill is auto-synced from upstream docs. |
| **MCP builder skill** | Yes -- 4-phase MCP server development guide with TypeScript/Python patterns | BrickLayer has mcp-developer agent | **LOW** | BrickLayer already has an mcp-developer agent. The mcp-builder skill's eval creation phase (Phase 4) is a useful pattern to incorporate. |
| **Webapp testing skill (Playwright)** | Yes -- decision tree, reconnaissance-then-action pattern, with_server.py helper | BrickLayer uses Playwright via /playwright skill | **LOW** | BrickLayer already has Playwright integration. The decision tree and with_server.py patterns are nice but not novel. |
| **Frontend design anti-"AI slop" guidelines** | Yes -- detailed anti-generic aesthetics guidelines, bold typography, spatial composition | BrickLayer has extensive frontend-design-philosophy.md rules | **LOW** | BrickLayer's frontend design philosophy is significantly more detailed. The "AI slop" framing is a useful complementary perspective. |
| **Doc co-authoring workflow** | Yes -- 3-stage: Context Gathering -> Refinement -> Reader Testing with sub-agent fresh-eyes | No equivalent | **MEDIUM** | The "Reader Testing" pattern (spawning a fresh sub-agent with zero context to test if a document makes sense) is novel and valuable. Could be applied to BrickLayer's synthesis and report generation. |
| **Skill self-creation (meta-skill)** | Yes -- skill-creator creates, tests, and optimizes other skills | BrickLayer has forge-check and agent-auditor but no skill-creation workflow | **HIGH** | The skill-creator pattern -- interview user, draft, test with parallel subagents, grade with assertions, iterate, optimize description -- is directly applicable to BrickLayer's agent creation workflow. Currently, creating a new BrickLayer agent is manual. |
| **Packaging (.skill files)** | Yes -- package_skill.py bundles skill directory into distributable .skill file | No equivalent | **LOW** | Useful for distribution but BrickLayer uses sx vault which serves the same purpose differently |
| **allowed-tools frontmatter** | Yes -- pre-approved tool list in SKILL.md metadata | BrickLayer agents have capabilities in agent_registry.yml | **LOW** | BrickLayer already tracks capabilities per agent. The allowed-tools field is experimental in the spec. |

---

## Top 5 Recommendations

### 1. Agent Progressive Disclosure [8h, HIGH PRIORITY]

**What**: Implement 3-tier loading for BrickLayer agent definitions, following the Agent Skills progressive disclosure pattern.

**Why**: Currently, when Mortar spawns a sub-agent, the entire .md file is loaded into context. For large agents (e.g., the developer agent with its full instruction set), this consumes significant context budget. Progressive disclosure would:
- Load only name + description (~100 tokens) for routing decisions
- Load the full agent body only when the agent is actually dispatched
- Load reference materials (if any) only when the agent needs them

**Implementation sketch**:
1. Add YAML frontmatter to all BrickLayer agent .md files (name, description, capabilities, model)
2. Modify Mortar's routing to parse only frontmatter for routing decisions (currently reads full file)
3. Split large agents into `{agent}.md` (core instructions <500 lines) + `{agent}/references/` for extended materials
4. Update `masonry/src/routing/router.py` to use frontmatter-only for semantic similarity matching
5. Update agent spawn to load full body only after routing decision is made

**Impact**: Reduces context consumption during routing by ~90%, enables larger agent fleets without context bloat.

### 2. Agent Creation Workflow (Forge Skill) [12h, HIGH PRIORITY]

**What**: Build a `/forge` skill modeled on the skill-creator pattern: interview -> draft -> parallel test -> grade -> iterate -> optimize routing description.

**Why**: Creating a new BrickLayer agent is currently manual: write an .md file, add to registry, run a campaign to generate training data, then optimize. The skill-creator shows a complete automated workflow that catches issues early through eval and baseline comparison.

**Implementation sketch**:
1. Create `.claude/skills/forge/SKILL.md` with the forge workflow
2. Interview phase: capture intent, target questions, expected behavior
3. Draft phase: generate agent .md with frontmatter, instructions, examples
4. Test phase: spawn test cases in parallel (with-agent vs without-agent), capture timing
5. Grade phase: assertion-based grading + benchmark aggregation
6. Iterate phase: read feedback, improve agent, re-test
7. Description optimization: dedicated loop for routing description using `masonry_route` to test semantic matching accuracy
8. Auto-onboard: integrate with existing `masonry-agent-onboard.js` hook

**Impact**: Reduces agent creation from hours of manual iteration to a guided 30-minute workflow with quantitative quality assurance.

### 3. Routing Description Optimizer [6h, HIGH PRIORITY]

**What**: A dedicated optimization loop for agent routing descriptions, targeting BrickLayer's semantic routing layer.

**Why**: The skill-creator's `run_loop.py` optimizes skill descriptions for triggering accuracy using train/test splits and multiple runs per query. BrickLayer's semantic routing layer (Ollama cosine similarity at threshold 0.75) depends heavily on agent description quality. Currently, descriptions are written manually and never tested against the routing engine.

**Implementation sketch**:
1. Port `skill-creator/scripts/run_loop.py` pattern to `masonry/scripts/optimize_routing.py`
2. For each agent, generate 20 test queries (10 should-route, 10 should-not-route)
3. Use `masonry_route` MCP tool (not `claude -p`) to test routing accuracy
4. Split 60/40 train/test, run 3x per query for reliability
5. Use Claude to propose improved descriptions based on failures
6. Iterate until test accuracy plateaus
7. Update agent_registry.yml with optimized descriptions

**Impact**: Could increase deterministic + semantic routing hit rate from estimated 60% to 80%+, reducing expensive LLM routing calls.

### 4. Fresh-Eyes Verification Pattern [4h, MEDIUM PRIORITY]

**What**: Implement the "Reader Testing" pattern from doc-coauthoring as a verification step in BrickLayer's synthesis and report generation.

**Why**: The doc-coauthoring skill's Stage 3 spawns a fresh Claude instance with zero prior context, gives it only the document, and asks test questions. If the fresh instance misunderstands the document, it reveals blind spots the author missed. This is directly applicable to:
- Campaign synthesis: does the synthesis make sense without seeing the findings?
- Verification reports: does the verify report accurately capture the code state?
- Agent-generated specs: does the spec make sense to a developer who wasn't in the planning session?

**Implementation sketch**:
1. After synthesizer produces `synthesis.md`, spawn a fresh sub-agent with ONLY the synthesis
2. Ask it 5-10 questions that a reader should be able to answer
3. Compare answers against known campaign findings
4. If the fresh agent misanswers, flag specific sections for revision
5. Integrate as optional step in Trowel's campaign conclusion phase

**Impact**: Catches "curse of knowledge" blind spots in BrickLayer's generated reports, improving report quality for human consumption.

### 5. YAML Frontmatter Standard for Agent Files [3h, MEDIUM PRIORITY]

**What**: Adopt YAML frontmatter as a standard for all BrickLayer agent .md files, aligned with the Agent Skills specification.

**Why**: BrickLayer agent files currently use ad-hoc markdown structure. Adding YAML frontmatter would:
- Enable machine-readable metadata extraction (no more regex parsing)
- Align with the emerging Agent Skills standard (106k stars, Anthropic-backed)
- Support future progressive disclosure (recommendation 1)
- Enable auto-generation of agent_registry.yml entries from frontmatter

**Implementation sketch**:
1. Define BrickLayer frontmatter schema: `name`, `description`, `model`, `tier`, `modes`, `capabilities`, `tools`
2. Add frontmatter to all 100+ agent .md files (scriptable -- extract from existing content)
3. Update `masonry/scripts/onboard_agent.py` to read frontmatter instead of regex extraction
4. Update routing to use frontmatter description field
5. Validate frontmatter on agent file save via `masonry-agent-onboard.js` hook

**Impact**: Standardizes agent metadata, enables programmatic agent fleet management, aligns with industry standard.

---

## Novel Patterns to Incorporate (Future)

### 1. Parallel With/Without Baseline Testing
The skill-creator spawns both "with-skill" and "without-skill" (or "old-skill") test runs in the same turn, enabling rigorous A/B comparison. BrickLayer could apply this pattern to agent optimization: run the same question through the optimized and unoptimized agent prompts simultaneously, then compare.

### 2. HTML Eval Viewer for Human Review
The skill-creator's eval-viewer (45KB SPA) renders side-by-side outputs with inline feedback collection. BrickLayer's Kiln could incorporate a similar comparison view for agent optimization cycles, showing "before" and "after" outputs with grading details.

### 3. Timing/Token Budget Capture on Subagent Completion
The skill-creator captures `total_tokens` and `duration_ms` from subagent completion notifications. BrickLayer's `masonry-subagent-tracker.js` hook tracks active agents but does not capture completion metrics. Adding token/time capture would enable cost optimization analysis per agent.

### 4. Description "Pushiness" for Undertriggering
The skill-creator explicitly notes that Claude tends to "undertrigger" skills and recommends making descriptions "a little bit pushy" -- including more trigger conditions than strictly necessary. BrickLayer's semantic routing layer likely has the same undertriggering problem. When writing agent descriptions, include edge-case trigger phrases.

### 5. Script Bundling Detection
The skill-creator observes test runs and notices when all subagents independently write similar helper scripts. It recommends bundling commonly-reinvented scripts into the skill. BrickLayer could apply this to campaign runs: if multiple research agents all write similar analysis scripts, extract and bundle them as shared utilities.

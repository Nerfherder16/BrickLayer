# Repo Research: yamadashy/repomix
**Repo**: https://github.com/yamadashy/repomix
**Researched**: 2026-03-28
**Version analyzed**: 1.13.1

---

## Verdict Summary

**Repomix is a high-value integration target for BrickLayer 2.0.** It solves the exact problem BL agents face daily — feeding entire codebases to LLMs — with a mature, battle-tested pipeline that includes token counting, Tree-sitter compression (70% reduction), security scanning, git history injection, and a full MCP server. The most immediately actionable item is the `generate_skill` MCP tool, which produces structured Claude Agent Skills from any codebase directly into `.claude/skills/` — this is purpose-built for BL's research agents.

**High-priority gaps**: BL lacks (1) Tree-sitter code compression for context reduction, (2) the `grep_repomix_output` incremental-read pattern for large packed codebases, (3) git-history-weighted file sorting, and (4) the `generate_skill` pipeline for structured codebase onboarding.

---

## File Inventory

| Path | Type | Purpose |
|------|------|---------|
| `src/index.ts` | Entry | Public API — exports all core functions |
| `src/cli/` | CLI | Argument parsing, command routing, interactive prompts |
| `src/config/configSchema.ts` | Config | Zod schema for all config options |
| `src/config/defaultIgnore.ts` | Config | 100+ default ignore patterns (all major ecosystems) |
| `src/config/configLoad.ts` | Config | Config file loading with JSON5 support |
| `src/core/packager.ts` | Core | Main orchestrator — coordinates the full pack pipeline |
| `src/core/packager/produceOutput.ts` | Core | Output writing and clipboard copy |
| `src/core/file/fileSearch.ts` | Core | Globby-based file discovery with .gitignore/.ignore support |
| `src/core/file/fileCollect.ts` | Core | Parallel file reading with encoding detection |
| `src/core/file/fileProcess.ts` | Core | Comment removal, empty line stripping, Tree-sitter compression |
| `src/core/file/fileStdin.ts` | Core | stdin pipe support for file path lists |
| `src/core/file/fileTreeGenerate.ts` | Core | Directory tree string generation |
| `src/core/file/truncateBase64.ts` | Core | Base64 content truncation (for binary files) |
| `src/core/output/outputGenerate.ts` | Core | Handlebars-based output rendering (XML/MD/plain/JSON) |
| `src/core/output/outputSplit.ts` | Core | Split large output across multiple files |
| `src/core/output/outputSort.ts` | Core | Git-change-count-weighted file ordering |
| `src/core/git/gitCommand.ts` | Git | Raw git command execution |
| `src/core/git/gitDiffHandle.ts` | Git | Work tree and staged diff injection |
| `src/core/git/gitLogHandle.ts` | Git | Commit log injection |
| `src/core/git/gitHubArchive.ts` | Git | Remote repo download via GitHub API tarball |
| `src/core/git/gitRemoteParse.ts` | Git | Parse remote URLs, branch/tag/commit refs |
| `src/core/security/securityCheck.ts` | Security | Secretlint-based secret detection |
| `src/core/metrics/calculateMetrics.ts` | Metrics | Token + char count per file and total |
| `src/core/tokenCount/` | Token | Tiktoken-based token counting (worker thread) |
| `src/core/treeSitter/languageConfig.ts` | Compress | 16-language Tree-sitter config registry |
| `src/core/treeSitter/parseFile.ts` | Compress | AST extraction for code compression |
| `src/core/treeSitter/queries/` | Compress | Per-language Tree-sitter query files |
| `src/core/skill/packSkill.ts` | Skill | Claude Agent Skill generation pipeline |
| `src/core/skill/skillTechStack.ts` | Skill | Tech stack detection from processed files |
| `src/core/skill/skillStyle.ts` | Skill | SKILL.md template generation |
| `src/mcp/mcpServer.ts` | MCP | MCP server bootstrap + tool registration |
| `src/mcp/tools/packCodebaseTool.ts` | MCP | `pack_codebase` tool |
| `src/mcp/tools/packRemoteRepositoryTool.ts` | MCP | `pack_remote_repository` tool |
| `src/mcp/tools/generateSkillTool.ts` | MCP | `generate_skill` tool |
| `src/mcp/tools/attachPackedOutputTool.ts` | MCP | `attach_packed_output` tool |
| `src/mcp/tools/readRepomixOutputTool.ts` | MCP | `read_repomix_output` tool (paginated) |
| `src/mcp/tools/grepRepomixOutputTool.ts` | MCP | `grep_repomix_output` tool (regex search) |
| `src/mcp/tools/fileSystemReadFileTool.ts` | MCP | `file_system_read_file` with secret scan |
| `src/mcp/tools/fileSystemReadDirectoryTool.ts` | MCP | `file_system_read_directory` listing |
| `browser/` | Extension | Chrome/Firefox extension via WXT framework |
| `.claude/plugins/repomix-mcp/` | Plugin | Claude Code plugin: registers repomix MCP server |
| `.claude/plugins/repomix-commands/` | Plugin | Claude Code plugin: `/pack-local`, `/pack-remote` slash commands |
| `.claude-plugin/marketplace.json` | Plugin | Claude plugin marketplace manifest |
| `repomix.config.json` | Config | Repomix's own config (self-referential example) |
| `repomix-instruction.md` | Docs | AI instruction file injected into packed output |
| `llms-install.md` | Docs | Full MCP server installation guide for AI agents |

---

## Architecture Overview

### Core Pack Pipeline

```
repomix [options] [dirs]
    ↓
fileSearch.ts        — Discover files (globby, .gitignore, .repomixignore, custom patterns)
    ↓
fileCollect.ts       — Parallel read with encoding detection (iconv-lite, jschardet)
    ↓
sortPaths.ts         — Sort by git change frequency (sortByChanges option)
    ↓
validateFileSafety   — Secretlint scan: flag/remove files with API keys, passwords, etc.
    ↓
fileProcess.ts       — Transform: remove comments, empty lines, Tree-sitter compress
    ↓
getGitDiffs/Logs     — Optional: inject staged diffs + commit history
    ↓
produceOutput.ts     — Generate output (Handlebars templates for xml/md/plain, JSON builder)
    ↓
calculateMetrics.ts  — Token count (Tiktoken worker pool, overlapped with pipeline)
    ↓
[optional] packSkill — Generate Claude Agent Skill package
```

### Output Formats

| Format | Flag | Notes |
|--------|------|-------|
| XML | `--style xml` (default) | Handlebars template OR fast-xml-parser (parsableStyle mode) |
| Markdown | `--style markdown` | Handlebars template, adaptive code fence delimiter |
| Plain text | `--style plain` | Handlebars template |
| JSON | `--style json` | Structured JSON, always parsable |

XML is the default and recommended for Claude — it uses semantic tags (`<file_summary>`, `<directory_structure>`, `<files>`, `<file path="...">`) that Claude's training treats specially.

### Key Performance Features

- **Parallel file reading** via `tinypool` worker threads (29x faster on facebook/react, 58x on next.js)
- **Tiktoken WASM warm-up** overlapped with security check + file processing (hides latency)
- **Handlebars template caching** — compiled once, reused per run
- **O(1) extension-to-language lookup** — lazy-built Map for Tree-sitter dispatch
- **50MB file size limit** — hard guard against memory issues

---

## Feature Catalog

### Input / File Selection

| Feature | CLI Flag | Config Key | Notes |
|---------|----------|-----------|-------|
| Include glob patterns | `--include` | `include[]` | fast-glob syntax, comma-separated |
| Ignore glob patterns | `--ignore` | `ignore.customPatterns[]` | supplements .gitignore |
| Respect .gitignore | default on | `ignore.useGitignore` | |
| Respect .ignore / .repomixignore | default on | `ignore.useDotIgnore` | |
| Respect default patterns | default on | `ignore.useDefaultPatterns` | 100+ patterns across all ecosystems |
| stdin file list | `--stdin` | — | pipe `find`/`git ls-files`/`fzf` output |
| Max file size | — | `input.maxFileSize` | default 50MB |
| Remote repo | `--remote <url>` | — | GitHub URL, shorthand, branch/tag/commit |
| Remote branch | `--remote-branch` | — | branch name, tag, or commit hash |
| Empty directories | `--include-empty-directories` | `output.includeEmptyDirectories` | |
| Full tree mode | `--include-full-directory-structure` | `output.includeFullDirectoryStructure` | shows all files even if not packed |

### Output Control

| Feature | CLI Flag | Config Key | Notes |
|---------|----------|-----------|-------|
| Output style | `--style` | `output.style` | xml/markdown/plain/json |
| Parsable style | `--parsable-style` | `output.parsableStyle` | strictly spec-compliant XML/MD |
| Output file path | `--output` | `output.filePath` | |
| Stdout mode | `--stdout` | `output.stdout` | pipe output directly, no file |
| Copy to clipboard | `--copy` | `output.copyToClipboard` | |
| Header text | `--header-text` | `output.headerText` | prepended to output |
| Instruction file | `--instruction-file-path` | `output.instructionFilePath` | injected as AI instructions |
| File summary section | `--no-file-summary` | `output.fileSummary` | on by default |
| Directory tree | `--no-directory-structure` | `output.directoryStructure` | on by default |
| Files section | — | `output.files` | can disable to get tree-only output |
| Remove comments | `--remove-comments` | `output.removeComments` | |
| Remove empty lines | `--remove-empty-lines` | `output.removeEmptyLines` | |
| Show line numbers | `--show-line-numbers` | `output.showLineNumbers` | |
| Truncate base64 | `--truncate-base64` | `output.truncateBase64` | trim embedded images in code |
| Top files count | `--top-files-length` | `output.topFilesLength` | largest files in summary (default 5) |
| Split output | — | `output.splitOutput` | N chunks for context window management |
| Token count tree | — | `output.tokenCountTree` | per-file token count in directory tree |

### Tree-sitter Code Compression

The `--compress` flag is the signature performance feature. It uses Tree-sitter ASTs to extract only semantic structure (function signatures, class declarations, type definitions) while discarding implementation bodies. Claim: **~70% token reduction** while preserving enough structure for LLM reasoning.

**Supported languages**: JavaScript, TypeScript, Python, Go, Rust, Java, C#, Ruby, PHP, Swift, C, C++, CSS, Solidity, Vue, Dart (16 total).

**Parse strategies** (language-specific behavior):
- `TypeScriptParseStrategy` — JS and TS share this (handles JSX)
- `PythonParseStrategy` — handles Python indentation
- `GoParseStrategy` — handles Go package structure
- `VueParseStrategy` — handles SFC format
- `CssParseStrategy` — handles CSS rules
- `DefaultParseStrategy` — generic for Rust, Java, C#, Ruby, PHP, Swift, C, C++, Solidity, Dart

### Git Integration

| Feature | Config Key | Notes |
|---------|-----------|-------|
| Sort files by change frequency | `output.git.sortByChanges` | Most-changed files listed first (default on) |
| Sort max commits analyzed | `output.git.sortByChangesMaxCommits` | default 100 |
| Include work tree diff | `output.git.includeDiffs` | unstaged changes injected |
| Include staged diff | `output.git.includeDiffs` | staged changes injected |
| Include commit log | `output.git.includeLogs` | recent N commits injected |
| Commit log count | `output.git.includeLogsCount` | default 50 |

The git-history-weighted sort is significant: files that change most frequently are listed first, helping the LLM focus on the most active code.

### Security

- **Secretlint integration** via `@secretlint/secretlint-rule-preset-recommend`
- Scans for API keys, passwords, private keys, tokens in file content AND git diffs/logs
- Suspicious files are excluded from output and reported separately in `PackResult.suspiciousFilesResults`
- The `file_system_read_file` MCP tool also runs Secretlint before returning file contents

### Token Counting

- Uses **Tiktoken** (OpenAI's tokenizer) in a worker thread pool
- Default encoding: `o200k_base` (GPT-4o and Claude-compatible approximation)
- Configurable encoding via `tokenCount.encoding`
- Reports: per-file char count, per-file token count, git diff token count, git log token count
- `output.tokenCountTree` option shows per-file token counts in the directory tree (threshold-configurable)

### Claude Agent Skill Generation

This is the most novel feature for BL. The `--skill-generate` flag (or `generate_skill` MCP tool) produces a structured Claude Agent Skill package:

```
.claude/skills/<skill-name>/
├── SKILL.md                    # Entry point with metadata + usage guide
└── references/
    ├── summary.md              # Stats, file format, usage guidelines
    ├── project-structure.md    # Directory tree
    ├── files.md                # All file contents (markdown format)
    └── tech-stacks.md          # Detected languages, frameworks, deps (optional)
```

`SKILL.md` contains: skill description, project name, total files, total lines, total tokens, tech stack presence, and source URL. This is placed in `.claude/skills/` and version-controlled — shared with the whole team.

**Tech stack detection** (`skillTechStack.ts`) is comprehensive — inspects file extensions, `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `requirements.txt`, `Gemfile`, `composer.json` etc. to produce a structured tech stack report.

### Output Splitting

`output.splitOutput: N` splits the packed output into N chunks. Each chunk gets its own file (`repomix-output-1.xml`, `repomix-output-2.xml`, ...). The split algorithm distributes files evenly across chunks while preserving per-chunk headers/footers. This is critical for repos that exceed a single context window.

### Remote Repository Support

```bash
repomix --remote yamadashy/repomix            # GitHub shorthand
repomix --remote https://github.com/org/repo  # Full URL
repomix --remote https://github.com/org/repo/tree/main  # Branch in URL
repomix --remote https://github.com/org/repo/commit/abc123  # Commit
```

Downloads via GitHub tarball API — no `git clone` required. Also supports direct git clone for non-GitHub remotes.

---

## MCP Integration

Repomix ships a **first-class MCP server** (`repomix --mcp`). It is production-ready, actively maintained, and listed in Claude Code's plugin marketplace.

### MCP Tools (8 total)

| Tool | Input | Output | Notes |
|------|-------|--------|-------|
| `pack_codebase` | `directory`, `compress`, `includePatterns`, `ignorePatterns`, `topFilesLength` | `outputId`, metrics, tree, files | Main local pack tool |
| `pack_remote_repository` | `remote`, `compress`, `includePatterns`, `ignorePatterns`, `topFilesLength` | `outputId`, metrics, tree, files | Fetches + packs GitHub repos |
| `generate_skill` | `directory`, `skillName`, `compress`, `includePatterns`, `ignorePatterns` | `skillPath`, `skillName`, `totalFiles`, `totalTokens` | Creates `.claude/skills/` package |
| `attach_packed_output` | `path` (file or dir) | Same as pack_codebase | Reuse existing packed output |
| `read_repomix_output` | `outputId`, `startLine`, `endLine` | Paginated content | For large packed files |
| `grep_repomix_output` | `outputId`, `pattern`, `contextLines`, `beforeLines`, `afterLines`, `ignoreCase` | Matching lines with context | Regex search in packed output |
| `file_system_read_file` | `path` (absolute) | File content | Includes Secretlint scan |
| `file_system_read_directory` | `path` (absolute) | `[FILE]`/`[DIR]` listing | Safe directory traversal |

### MCP Prompts

- `pack_remote_repository` — registered prompt template for guided remote repo packing

### Claude Code Plugin

Repomix has an **official Claude Code plugin** (`/.claude-plugin/marketplace.json`) with three sub-plugins:
1. **repomix-mcp** — registers repomix MCP server via `.mcp.json`
2. **repomix-commands** — adds `/pack-local` and `/pack-remote` slash commands
3. **repomix-explorer** — additional exploration commands

The `.mcp.json` config for Claude Code:
```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix@latest", "--mcp"]
    }
  }
}
```

### The `grep_repomix_output` Pattern

This is a key insight for BL agents: **pack once, grep many times**. Instead of re-packing to answer each question, an agent can:
1. `pack_codebase` → get `outputId`
2. `grep_repomix_output(outputId, pattern, contextLines=5)` for targeted file section retrieval
3. `read_repomix_output(outputId, startLine, endLine)` for paginated reading

This is the incremental context retrieval pattern — avoids re-packing or passing the full packed output to each agent.

---

## Feature Gap Analysis

| Feature | In repomix | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-----------|------------------|-----------|-------|
| Pack entire codebase to single file | Yes (core feature) | No native equivalent | **HIGH** | BL agents read files individually |
| Tree-sitter code compression (~70% token reduction) | Yes (`--compress`) | No | **HIGH** | Critical for large codebases |
| Token counting per file + repo total | Yes (Tiktoken) | masonry-context-monitor.js (context-level only) | **HIGH** | BL has no per-file token awareness |
| Git-history-weighted file ordering | Yes (sortByChanges) | No | **MEDIUM** | Most-changed files first is signal-rich |
| Include git diffs + logs in context | Yes | masonry_git_hypothesis (question gen only) | **MEDIUM** | BL uses git diffs for Q generation, not context injection |
| Output splitting for large repos | Yes (splitOutput: N) | context-continuation.md handoff protocol | **MEDIUM** | BL has handoff but not pre-planned splits |
| Claude Agent Skill generation | Yes (`generate_skill`) | No | **HIGH** | Purpose-built for structured codebase onboarding |
| Remote repo packing (GitHub URL) | Yes (`--remote`) | No | **MEDIUM** | BL agents only work local |
| MCP server (8 tools) | Yes (`--mcp`) | Masonry MCP (domain-specific tools) | **LOW** | BL has MCP, different domain |
| Security scan (Secretlint) | Yes (auto) | No codebase-level scan | **LOW** | BL doesn't pack codebases currently |
| XML/MD/JSON/plain output formats | Yes | No structured packing | **MEDIUM** | Would matter when BL packs codebases |
| Regex grep on packed output | Yes (`grep_repomix_output`) | masonry_pattern_search (Recall) | **MEDIUM** | Different — Recall is semantic, repomix grep is literal |
| Paginated reading of packed output | Yes (`read_repomix_output`) | No | **MEDIUM** | Needed for large packed files |
| stdin file list pipe | Yes (`--stdin`) | No | **LOW** | Useful for selective packing |
| Browser extension | Yes (Chrome/Firefox) | No | **LOW** | Not relevant to BL |
| `.repomixignore` file | Yes | No | **LOW** | BL could use a `masonry-pack-ignore` equivalent |
| Instruction file injection | Yes | program.md, project-brief.md (separate) | **LOW** | BL already has context injection |
| Token count tree visualization | Yes | No | **LOW** | Nice-to-have for campaign planning |
| Tech stack auto-detection | Yes (skillTechStack.ts) | No | **MEDIUM** | Useful for hypothesis generation |
| Clipboard copy | Yes | No | **LOW** | Convenience only |
| Parallel worker thread processing | Yes (tinypool) | No (sequential) | **MEDIUM** | Matters for large repos |
| Base64 truncation | Yes | No | **LOW** | Edge case |
| Custom instruction file per project | Yes | project-brief.md | **NONE** | BL already solved this |
| Semantic memory retrieval | No | Recall (Qdrant + Neo4j) | **NONE** | BL advantage — repomix has no memory |
| Campaign/research loop | No | Yes (full BL 2.0 loop) | **NONE** | BL advantage |
| Agent fleet + routing | No | Yes (Masonry) | **NONE** | BL advantage |

---

## Top 5 Recommendations

### 1. Add repomix MCP to BL's Claude Code settings (immediate, 5 minutes)

Add repomix to `~/.claude/settings.json` or BL project `.mcp.json`:
```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix@latest", "--mcp"]
    }
  }
}
```

This gives all BL agents immediate access to `pack_codebase`, `pack_remote_repository`, `generate_skill`, `grep_repomix_output`, and `read_repomix_output`. Zero code changes. The `grep_repomix_output` tool alone transforms how BL agents navigate large codebases — pack once, grep many.

### 2. Use `generate_skill` for BL project onboarding

When a new BL project is initialized (`bl-init`), run `generate_skill` against the project codebase to create `.claude/skills/repomix-reference-<project>/`. This gives every agent spawned in that project a structured, token-efficient reference to the full codebase without consuming context. The skill is version-controlled and shared — no per-agent re-packing.

This directly addresses the dev execution gap: agents can build features with full codebase awareness without flooding their context.

### 3. Add Tree-sitter compression to BL's context management

The `--compress` flag (70% token reduction via Tree-sitter AST extraction) should be integrated into how BL prepares codebase context for research agents. When `masonry-context-monitor.js` warns at 150K tokens, the response should not be just a handoff — it should be "repack with `--compress` and continue." This effectively extends usable context by 3-4x for code-heavy sessions.

Concrete: add a `masonry-pack-codebase` hook or MCP tool that wraps `pack_codebase` with compression enabled, and wire it into the context-warning flow.

### 4. Adopt the pack-once/grep-many pattern for campaign waves

Current BL research loop: each agent independently reads individual files. Alternative with repomix:
1. At campaign start, `pack_codebase(projectDir)` → store `outputId`
2. Store `outputId` in `masonry-state.json`
3. Each wave agent gets `outputId` and uses `grep_repomix_output` for targeted retrieval
4. No re-reading, no per-agent file discovery, no duplicated gitignore logic

This is the Karpathy-style "single document" feeding pattern. The grep tool returns context lines around matches — agents can do targeted surgery without reading the full packed file.

### 5. Use repomix's git-integration for hypothesis generation improvements

BL's `masonry_git_hypothesis` already reads recent diffs to generate questions. Repomix adds: (1) git-change-frequency weighted file ordering, (2) full commit log injection, (3) staged diff inclusion. Integrating these into BL's hypothesis generation would give the `hypothesis-generator` agent a richer signal — "here are the most actively modified files in the last 100 commits" — without manual git archaeology.

---

## Harvestable Items

### Direct Integration (copy-adapt)

**1. defaultIgnore list** — `src/config/defaultIgnore.ts` has 100+ battle-tested ignore patterns across all major ecosystems (Node, Python, Rust, PHP, Ruby, Go, Elixir, Haskell, plus VCS, editors, OS). BL's masonry agents currently have no canonical ignore list. Adopt this verbatim for any BL file discovery code.

**2. Token counting worker pattern** — The pre-initialized Tiktoken worker pool with warmup overlapped against the pipeline is a clean pattern. BL's context monitor currently relies on Claude's own context usage reporting (post-hoc). A pre-packing token count would let BL proactively decide whether to compress before sending to an agent.

**3. The `grep_repomix_output` tool design** — JavaScript RegExp, context lines (before/after separately configurable), case-insensitive flag. This is a simple but powerful pattern that should be in BL's MCP server for any large packed text (findings, synthesis, packed codebases).

**4. Skill output structure** — The `SKILL.md + references/` layout is a clean pattern for any BL "knowledge package." The BL synthesis output (`findings/synthesis.md`) could be packaged this way for handoff between sessions.

**5. Tech stack detection logic** (`skillTechStack.ts`) — Inspects package manifests and file extensions to produce structured tech stack info. BL's question-designer-bl2 could use this to generate more targeted questions without manual project-brief documentation of the stack.

**6. Output split algorithm** (`outputSplit.ts`) — Distributes files evenly across N chunks with full context (headers, tree) in each chunk. BL's context-continuation.md handoff protocol could adopt this for planned context splits rather than reactive handoffs.

### Configuration Patterns to Adopt

**repomix.config.json** — The `instructionFilePath` pattern (inject a `.md` file as AI instructions into the packed output) maps directly to how BL uses `program.md` and `project-brief.md`. BL could use this to inject project context into any repomix-packed output without modifying the core repomix call.

**`.repomixignore`** — BL projects should have a `masonry-pack-ignore` or simply `.repomixignore` that excludes `masonry-state.json`, `findings/`, `.autopilot/`, etc. from any codebase packing.

---

## Summary JSON

```json
{
  "repo": "yamadashy/repomix",
  "report_path": "docs/repo-research/yamadashy-repomix.md",
  "version": "1.13.1",
  "files_analyzed": 47,
  "high_priority_gaps": 4,
  "medium_priority_gaps": 7,
  "low_priority_gaps": 9,
  "top_recommendation": "Add repomix MCP to BL Claude Code settings immediately — zero-cost, unlocks 8 tools including generate_skill and grep_repomix_output for all BL agents",
  "verdict": "High-value integration. Repomix solves the codebase-to-LLM packaging problem that BL agents hit constantly. The MCP server, generate_skill tool, Tree-sitter compression, and grep pattern are directly harvestable. Recommend: (1) add to MCP settings today, (2) wire generate_skill into bl-init, (3) adopt compress flag in context-warning flow."
}
```

# Repo Research: HKUDS/AutoAgent

**Repo**: https://github.com/HKUDS/AutoAgent
**Researched**: 2026-04-06
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

AutoAgent (formerly MetaChain) is a self-modifying LLM agent framework whose core differentiator is that it can write new tools, compose new agents, and construct multi-agent workflows at runtime — entirely from natural language — without any human coding. It beats BrickLayer in three specific dimensions: (1) live runtime self-modification of the agent fleet via code generation into the running package, (2) a complete Docker-sandboxed execution environment for safe code execution with TCP socket command streaming, and (3) a structured non-function-calling compatibility shim that allows any model to behave as a tool-calling agent. BrickLayer beats AutoAgent in research depth (EMA training, PageRank scoring, HNSW recall, consensus voting), multi-phase lifecycle management, hook-driven quality enforcement, and operational reliability (13 active hooks vs. zero in AutoAgent).

---

## File Inventory

### Root
- `README.md` — project overview, install instructions, three operating modes
- `constant.py` — global config: model name, Docker image, function-call compatibility matrix, environment variables
- `pyproject.toml` — Python package config; CLI entry point `auto = autoagent.cli:main`
- `setup.cfg` — package setup
- `.env.template` — API key template (OpenAI, Anthropic, DeepSeek, Gemini, HuggingFace, Groq, XAI, GitHub)
- `process_tool_docs.py` — preprocesses third-party API documentation (RapidAPI) into tool_docs.csv
- `tool_docs.csv` — structured API documentation for tool retrieval
- `Communication.md` — community links (Slack, Discord, WeChat, Feishu)

### autoagent/ (core package)
- `__init__.py` — exports MetaChain, Agent, Response, Result, registry
- `cli.py` — CLI entry: `auto main` and `auto deep-research` subcommands; starts Docker container, launches REPL
- `main.py` — async and sync run loops with 3-strike retry; escalates to meta-agent on persistent failure
- `core.py` — MetaChain class: the agentic loop engine (sync + async), tool dispatch, Gemini compatibility shim, non-fn-call fallback
- `types.py` — Agent, Response, Result, AgentFunction pydantic models; Agent carries `examples`, `handle_mm_func`, `agent_teams`
- `registry.py` — singleton Registry; four namespaces: tools, agents, plugin_tools, plugin_agents, workflows; FunctionInfo dataclass stores full source body
- `fn_call_converter.py` — bidirectional converter: function-calling ↔ XML tag format for non-fn-call models; includes full in-context learning example (OpenHands-derived)
- `io_utils.py` — file I/O helpers
- `logger.py` — MetaChainLogger (Rich console) + LoggerManager singleton
- `server.py` — FastAPI HTTP server wrapper
- `tcp_server.py` — TCP socket server for Docker container communication
- `util.py` — `function_to_json`, `make_message`, `make_tool_message`, debug helpers

### autoagent/agents/
- `__init__.py` — re-exports all agent factory functions
- `dummy_agent.py` — template agent for code generation reference
- `github_agent.py` — GitHub PR/issue operations agent
- `tool_retriver_agent.py` — RAG-based tool retrieval agent

#### autoagent/agents/system_agent/
- `system_triage_agent.py` — orchestrator: routes between FileSurfer, WebSurfer, Coding; `transfer_to_*` / `transfer_back_to_triage_agent` pattern; uses `case_resolved` / `case_not_resolved` sentinel tools
- `websurfer_agent.py` — browser-use agent: click, page_down/up, web_search, input_text, visit_url, get_page_markdown; accessibility tree parsing; multimodal screenshot support via `handle_mm_func`
- `filesurfer_agent.py` — local file browsing agent; paged markdown viewport
- `programming_agent.py` — coding agent: file read/write/create, execute_command, run_python; in-context learning examples baked into agent (full Flask app debug session)

#### autoagent/agents/meta_agent/ (self-modification layer)
- `agent_editor.py` — simple agent: list/create/delete/run agents; uses dummy_agent.py as template
- `agent_creator.py` — advanced agent: parses XML agent forms, creates individual agents and orchestrator agents; full lifecycle management
- `agent_former.py` — form-based agent creation pipeline
- `form_complie.py` — XML form compilation for agent definitions
- `tool_editor.py` — creates plugin tools: checks existing, queries RapidAPI docs, searches HuggingFace for models, implements and tests tools via `run_tool`
- `workflow_creator.py` — parses XML workflow forms, creates agents, creates and executes workflows
- `workflow_former.py` — form-based workflow creation pipeline
- `worklow_form_complie.py` — XML form compilation for workflow definitions

#### autoagent/agents/math/
- (math reasoning agents — present for MATH-500 benchmark)

### autoagent/tools/
- `__init__.py` — re-exports all registered tools
- `terminal_tools.py` — read_file, write_file, create_file, list_files, create_directory, execute_command, run_python, gen_code_tree_structure; paged terminal viewport via RequestsMarkdownBrowser; base64 chunked file write for Docker
- `web_tools.py` — click, page_down/up, history_back/forward, input_text, visit_url, web_search, sleep, get_page_markdown; BrowserGym integration; accessibility tree → string flattening; markdown page conversion
- `inner.py` — `case_resolved`, `case_not_resolved` sentinel tools (force agent loop termination)
- `code_search.py` — code search utilities
- `file_surfer_tool.py` — local file browser tools
- `rag_tools.py` — vector DB query/save tools
- `rag_code.py` — code-specific RAG
- `md_obs.py` — markdown accessibility tree flattener
- `tool_utils.py` — shared tool helpers
- `dummy_tool.py` — plugin tool template for code generation
- `github_client.py` — GitHub API client
- `github_ops.py` — GitHub operations (PR, issue, clone)

#### autoagent/tools/meta/ (self-modification tools)
- `edit_agents.py` — `list_agents`, `create_agent`, `create_orchestrator_agent`, `delete_agent`, `run_agent`, `read_agent`; generates Python source code and writes it into the installed package; uses `pip show autoagent` to locate install path
- `edit_tools.py` — `list_tools`, `create_tool`, `delete_tool`, `run_tool`; protect_tools() prevents overwriting built-in tools; validates code compiles before registering
- `edit_workflow.py` — `list_workflows`, `create_workflow`, `run_workflow`
- `tool_retriever.py` — `get_api_plugin_tools_doc`; queries tool_docs.csv for RapidAPI documentation and embedded API keys
- `search_tools.py` — `search_trending_models_on_huggingface`, `get_hf_model_tools_doc`; fetches model cards

### autoagent/environment/
- `docker_env.py` — DockerConfig dataclass + DockerEnv class; launches/manages Docker containers; TCP socket `run_command` with streaming output; auto git-clones AutoAgent into container for self-modification; port detection
- `local_env.py` — LocalEnv: subprocess-based command execution (no Docker)
- `browser_env.py` — BrowserGym-based browser environment; Playwright under the hood
- `browser_cookies.py` — cookie injection into browser sessions
- `cookies_data.py` — cookie data structures
- `markdown_browser/` — RequestsMarkdownBrowser: paged text-based file/content viewer
- `mdconvert.py` — converts arbitrary file types to markdown (PDF, DOCX, PPTX, etc.)
- `tcp_server.py` — server-side TCP server running inside Docker container
- `shutdown_listener.py` — graceful shutdown
- `tenacity_stop.py` — retry stop conditions
- `utils.py` — `setup_metachain`: environment bootstrapping

### autoagent/flow/ (event-driven workflow engine)
- `core.py` — EventEngineCls: async event-driven execution engine; events declared with `@engine.make_event`; groups trigger downstream events when all dependencies resolved (`retrigger_type="all"` or `"any"`); supports GOTO and ABORT control flow; async fan-out with `max_async_events` concurrency limit
- `broker.py` — BaseBroker: event message broker
- `types.py` — BaseEvent, EventGroup, EventInput, ReturnBehavior, InvokeInterCache
- `dynamic.py` — dynamic event registration
- `utils.py` — logging, hashing, UUID generation

### evaluation/
- `gaia/` — GAIA benchmark evaluation scripts and inference runner
- `multihoprag/` — multi-hop RAG benchmark evaluation
- `math500/` — MATH-500 benchmark
- `README.md` — benchmark reproduction instructions

---

## Architecture Overview

AutoAgent operates in three modes accessible from a CLI front page:

**User Mode (Deep Research)**: Launches a `System Triage Agent` that orchestrates three sub-agents — WebSurfer, FileSurfer, and Coding — in a handoff pattern. The triage agent determines which specialist is needed based on task state, transfers via `transfer_to_*` functions that return `Result(agent=target)`, and sub-agents transfer back via `transfer_back_to_triage_agent`. The entire conversation is a single MetaChain run loop where agent handoffs are accomplished by returning a different Agent object from a tool call. The loop terminates when `case_resolved` or `case_not_resolved` sentinel tools are called.

**Agent Editor Mode**: The LLM user describes what kind of agent they want. An `Agent Former` generates an XML agent form. A `Form Compiler` validates the XML. The `Agent Creator Agent` then reads the form and calls `create_agent()`, which generates Python source code implementing the agent, writes it to `autoagent/agents/<name>.py` inside the installed package directory (located via `pip show autoagent --editable`), and validates it compiles. For multi-agent requests, it calls `create_orchestrator_agent()`, which generates orchestrator Python code with embedded handoff functions. The created agents persist and are immediately importable in subsequent runs.

**Workflow Editor Mode**: Same approach but for declarative workflows. The `Workflow Creator Agent` generates workflow Python code via `create_workflow()`, validates it, and executes it via `run_workflow()`.

**Docker Sandbox**: All code execution happens inside a Docker container. The container runs a TCP server (tcp_server.py) that accepts commands via socket, executes them, and streams output back in newline-delimited JSON. File writes use base64 encoding in chunks to avoid shell escaping issues. The local filesystem is volume-mounted into the container.

**MetaChain Core Loop** (core.py): Each turn calls `get_chat_completion()` with the active agent's system prompt + conversation history + tool definitions. Tool calls are dispatched to `handle_tool_calls()`. If a tool returns an `Agent` object (via `Result(agent=...)`), the active agent switches for the next turn. The loop continues until: no tool calls are made (for optional tool_choice agents), or `case_resolved`/`case_not_resolved` is called (for `tool_choice="required"` agents). Retry with exponential backoff (tenacity) on API errors.

**Non-Function-Call Fallback** (fn_call_converter.py): For models without native function calling (DeepSeek-R1, o1-mini, Llama, Grok-2), tool definitions are serialized as XML descriptions appended to the last user message. Model output is parsed for `<function=name>...<param_name>value</param_name>...</function>` tags and converted back to standard tool_calls format. An in-context learning example (a full Flask debugging session) is prepended to the first user message to teach the format. This is ported from OpenHands.

**Event Engine** (flow/core.py): An async dependency-tracking execution engine where events declare which other events they "listen to" (dependencies). When all events in a group complete, the dependent event fires. Supports both AND-triggering ("all" — all dependencies must complete) and OR-triggering ("any" — first dependency triggers). Supports GOTO (explicit routing to a specific event) and ABORT control flow.

---

## Agent Catalog

| Agent | Purpose | Key Tools | Unique Capability |
|---|---|---|---|
| System Triage Agent | Orchestrator for user mode; routes between specialists | `transfer_to_*`, `case_resolved`, `case_not_resolved` | Handoff routing via tool-return-agent pattern |
| Web Surfer Agent | Full browser control: navigate, click, search, scroll | `click`, `visit_url`, `web_search`, `page_down/up`, `get_page_markdown`, `input_text` | BrowserGym accessibility tree parsing; multimodal screenshots |
| File Surfer Agent | Local file browsing with paged viewport | File read tools, paged markdown browser | Paged terminal viewport for large files |
| Coding Agent | Writes and executes Python code | `create_file`, `write_file`, `run_python`, `execute_command`, `gen_code_tree_structure` | Full in-context learning example baked into agent (few-shot Flask session) |
| Agent Editor Agent | Creates/modifies agents via natural language | `list_agents`, `create_agent`, `delete_agent`, `run_agent` | Writes Python source into live package |
| Agent Creator Agent | Advanced agent creation with orchestrator support | all edit_agents tools + `create_orchestrator_agent` | Full orchestrator agent code generation with handoff functions |
| Tool Editor Agent | Creates plugin tools; fetches API docs and HF models | `list_tools`, `create_tool`, `run_tool`, `get_api_plugin_tools_doc`, `search_trending_models_on_huggingface` | Dynamic tool discovery from RapidAPI catalog and HuggingFace |
| Workflow Creator Agent | Creates multi-agent workflows from XML forms | all edit_agents tools + `create_workflow`, `run_workflow` | Generates full workflow Python code with dependency graph |
| GitHub Agent | GitHub operations (PR, issue, search) | `github_client`, `github_ops` | — |
| Tool Retriever Agent | RAG-based tool discovery from existing tools | `get_api_plugin_tools_doc` | Semantic search over tool catalog |

---

## Core Concepts and Novel Ideas

### 1. Live Runtime Self-Modification

The most distinctive capability in AutoAgent. The `create_agent()` and `create_tool()` functions locate the AutoAgent package installation path via `pip show autoagent` and write new Python files directly into that directory. After writing, they validate syntax by running `python <file>.py`. The new agents and tools become importable on the next import call. The key safety mechanism is `protect_tools()` which prevents overwriting built-in tools.

### 2. Orchestrator Agent Code Generation Pattern

When creating multi-agent systems, `create_orchestrator_agent()` generates Python code that: (a) imports each sub-agent factory, (b) instantiates them, (c) generates typed `transfer_to_<agent>()` functions that return `Result(value=input, agent=sub_agent)`, (d) generates `transfer_back_to_<orchestrator>()` functions. This creates a bidirectional handoff graph encoded entirely in closures, not configuration.

### 3. Non-Function-Calling Model Compatibility Shim

`fn_call_converter.py` provides full bidirectional translation between OpenAI function-calling format and XML tag format. An in-context learning example of a complete Flask debugging session is prepended to the first user message to teach the format. Ported from OpenHands and adapted to AutoAgent's tool schema.

### 4. Docker TCP Socket Execution with Streaming

Rather than running a shell directly, AutoAgent runs a persistent TCP server inside the Docker container. Tool calls connect via socket and receive newline-delimited JSON: `{"type": "chunk", "data": "..."}` for streaming output and `{"type": "final", "status": 0, "result": "..."}` for the final result. This allows real-time output streaming without buffering.

### 5. Paged Terminal Viewport

Long command outputs are written to a temp file and opened in a `RequestsMarkdownBrowser`. Provides a paginated view: `terminal_page_up`, `terminal_page_down`, `terminal_page_to(N)` let the agent navigate without overflowing context. Viewport metadata (current page, total pages) prepended as a header.

### 6. Sentinel Tool Termination Pattern

`case_resolved` and `case_not_resolved` are registered as regular tools. For agents with `tool_choice="required"`, the loop checks whether the most recent tool call was one of these sentinels and terminates accordingly. The `take_away_message` field in `case_not_resolved` captures what was learned even on failure — useful as training signal.

### 7. Agent Handoff via Tool Return Value

Agent transitions are encoded in tool return values. A tool that returns `Result(agent=other_agent)` switches the active agent for the next turn (inherited from OpenAI Swarm). `transfer_to_websurfer_agent(sub_task_description: str)` is a closure over the websurfer agent instance that returns `Result(value=sub_task_description, agent=websurfer_agent)`.

### 8. Few-Shot In-Context Examples in Agent Definition

The Coding Agent's `examples()` function returns a pre-built conversation history prepended to every new conversation. This is the same pattern as DSPy's few-shot demonstrations but implemented directly in the agent definition rather than through an optimizer.

### 9. Event-Driven Async Workflow Engine

The `flow/` module implements a DAG-based async event engine. Supports AND/OR trigger semantics and GOTO/ABORT control flow. The `retrigger_type="any"` mode (fire when the first dependency completes) enables speculative execution patterns.

---

## Feature Gap Analysis

| Feature | AutoAgent | BrickLayer 2.0 | Gap Level |
|---|---|---|---|
| Live runtime self-modification of agent code | YES — writes Python into installed package | NO — agents are static files | HIGH |
| Orchestrator agent code generation | YES — bidirectional handoff closures | NO — manual agent wiring | HIGH |
| Docker sandbox for code execution | YES — Docker + TCP socket streaming | NO — runs in host environment | HIGH |
| Browser-use agent (full page control) | YES — BrowserGym + Playwright, AXTree, screenshots | NO | HIGH |
| Non-function-calling model compatibility | YES — XML tag shim with in-context examples | NO — assumes fn calling | MEDIUM |
| Paged terminal viewport | YES — navigable paged output | NO — raw output truncation | MEDIUM |
| Multimodal tool result injection | YES — Result(image=base64) → image_url message | NO | MEDIUM |
| Sentinel tool termination | YES — explicit LLM-controlled loop exit | PARTIAL — external hooks | MEDIUM |
| Async run loop | YES | PARTIAL — mostly sync | MEDIUM |
| Cookie injection for browser auth | YES | NO | MEDIUM |
| RapidAPI tool catalog integration | YES | NO | MEDIUM |
| XML-form-driven agent/workflow creation | YES | NO | MEDIUM |
| Few-shot baked-in agent examples | YES — Coding Agent has Flask debug session | PARTIAL — detailed prompts | LOW |
| HuggingFace model discovery for tools | YES | NO | LOW |
| EMA training pipeline | NO | YES — telemetry.jsonl → ema_history.json | BL advantage |
| HNSW reasoning bank / semantic recall | NO | YES — hnswlib + Qdrant + Neo4j | BL advantage |
| PageRank pattern confidence | NO | YES — damping=0.85 | BL advantage |
| Consensus builder (weighted majority vote) | NO | YES | BL advantage |
| Hook system (lifecycle enforcement) | NONE | YES — 13+ hooks | BL advantage |
| Multi-phase lifecycle (SPARC) | NO | YES — 9 modes | BL advantage |
| Agent registry with 50+ specialists | NO — ~10 agents | YES — 100+ agents | BL advantage |
| Mortar 4-layer routing | NO — simple triage | YES | BL advantage |
| Kiln desktop monitoring | NO — CLI only | YES — Electron app | BL advantage |

---

## Top 5 Recommendations for BrickLayer

### 1. Docker Sandbox Execution Environment [4-6h, HIGH PRIORITY]

AutoAgent's Docker + TCP socket pattern is the cleanest approach to safe code execution in an open-source agent framework. The container runs a persistent `tcp_server.py` that accepts commands via socket and streams output as newline-delimited JSON chunks. Implement a `DockerEnv` abstraction, wire it into `execute_command` and `run_python` as an optional `code_env` context variable, and add a `masonry-docker-exec.js` hook that wraps tool calls with Docker isolation when a campaign sets `sandbox_mode: true`.

### 2. Live Agent/Tool Code Generation (Self-Extension) [6-8h, HIGH PRIORITY]

AutoAgent's `create_agent()` and `create_tool()` locate the package install path via `pip show autoagent --editable` and write Python files directly into `autoagent/agents/` and `autoagent/tools/`. The critical addition for BrickLayer is the code generation step — a `forge-agent` that generates new agent `.md` definition files AND new MCP tool implementations from natural language requirements, validates them via the existing `forge-check` agent, and registers them via `masonry-agent-onboard.js`.

### 3. Paged Terminal Viewport for Long Outputs [2-3h, MEDIUM PRIORITY]

When command outputs exceed 12,000 tokens, save to temp file and serve through a paginated markdown browser. Add tiktoken-based truncation to `execute_command` with a redirect-to-file fallback + a `terminal_page_*` tool set. The `masonry-context-monitor.js` hook already watches context size — this gives the LLM an active tool to manage it rather than just a warning.

### 4. Non-Function-Calling Model Compatibility Shim [3-4h, MEDIUM PRIORITY]

`fn_call_converter.py` is a self-contained bidirectional converter between function-calling and XML tag format. Adding this shim would allow BrickLayer to use DeepSeek-R1, o1-mini, or local Ollama models without function calling support. Also worth adopting: baking few-shot worked examples into complex agents to reduce tool-use errors.

### 5. Sentinel Tool Termination Pattern [1-2h, MEDIUM PRIORITY]

Add `case_resolved(result: str)` and `case_not_resolved(failure_reason, take_away_message)` as registered tools to BrickLayer's agent templates. Makes agent loop exit conditions explicit and LLM-controlled. The `take_away_message` field on failure maps directly onto BrickLayer's telemetry.jsonl — failures with a lesson learned are training signal.

---

## Summary

AutoAgent is narrower but deeper than BrickLayer on runtime self-modification and execution sandboxing, while BrickLayer is significantly more capable on research quality (EMA, PageRank, HNSW recall, consensus), lifecycle management (9 modes, SPARC), and operational reliability (13 hooks vs. zero in AutoAgent).

The top recommendation is the Docker sandbox execution environment — AutoAgent's TCP socket streaming pattern gives agent-generated code full isolation with real-time output, a critical safety and reliability gap in BrickLayer's current architecture.

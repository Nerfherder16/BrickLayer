# CodeVV OS — Experience Design Spec

**Session:** Superpowers Socratic Brainstorming  
**Date:** 2026-04-01  
**Method:** 9-step structured ideation with hard gate before implementation  
**Status:** APPROVED — ready for implementation planning

---

## Overview

CodeVV OS is a boot-to-browser collaborative development platform. This spec captures every UX and product decision made during the design session. It covers the full user journey from first login through brainstorming, planning, building, and team management.

This document is the ground truth for all experience decisions. The ROADMAP drives implementation sequence. This drives what gets built.

---

## 1. Team & Project Dashboard

### Entry Point
When a user logs in, they land on the **Team Dashboard** — a single unified view of the entire team's work across all projects.

### What the Dashboard Shows

**Team-wide panel (top):**
- All active projects with status indicators
- What each team member is currently working on (live presence)
- Overall health per project (tasks done, tasks in progress, tasks blocked)

**Personal panel (primary):**
- Projects the user is assigned to
- Their assigned tasks (current + upcoming)
- Their personal AI assistant quick-access
- Catch-up digest (if they've been away)

**Activity feed (side):**
- Recent commits, decisions, AI conversations, canvas changes
- Filterable by project, person, or type

### Dashboard Behavior
- Projects are not siloed — every team member sees everything by default
- Admin can restrict visibility for fractional hires (see Roles section)
- Panels open alongside the dashboard rather than replacing it — dashboard stays anchored

---

## 2. Workspace Types

Work type determines the workspace layout. Users are offered the appropriate workspace template based on what they're doing, but always pick manually.

| Workspace | Default Layout | When Used |
|-----------|---------------|-----------|
| **Brainstorm** | Canvas (primary) + AI chat | Ideation, design exploration |
| **Planning** | Task board + AI chat + canvas (secondary) | Sprint planning, spec writing |
| **Development** | Code editor + terminal + file tree + AI chat | Active coding |
| **Review** | Diff view + AI explanation panel | Code review, PR inspection |
| **Meeting** | LiveKit video + canvas + shared terminal | Pair sessions, mob programming |

### Workspace Templates
- Each template has its own default panel layout, keyboard shortcut profile, and accent color
- Users can customize any template and save it
- Admins can define team-wide templates
- Templates load into dockview — fully tiling with floating panel escape hatch

---

## 3. AI Brainstorming Sessions

### Driver Model
One user is the **driver** — they control the AI conversation. Other team members observe the session in real time (Yjs-synced) and can interject via @mention toasts. The driver decides when to acknowledge or ignore interjections.

### Canvas-First Brainstorming
- Brainstorm sessions open the canvas as the primary surface
- Canvas supports: freeform sticky notes, structured templates, AI-generated diagrams
- Claude asks before placing objects on the canvas — no surprise mutations
- Canvas persists after the session ends — it's a permanent project artifact

### The Hard Gate (Spec Before Build)
When a brainstorm session reaches a decision point:

1. Claude drafts a structured spec from the canvas and conversation
2. The spec is presented to the driver for review
3. **Hard gate:** the driver must explicitly approve the spec before any implementation begins
4. Approved spec is stored in the project's `docs/` and ingested into Recall
5. BrickLayer build is only triggered after spec approval

No code is written until a human approves the spec. This is non-negotiable.

### Brainstorm Session Flow
```
Open Brainstorm Workspace
  → Canvas opens (blank or from template)
  → AI chat panel alongside canvas
  → Team joins as observers
  → Driver leads conversation
  → Claude assists: sticky notes, clusters, diagrams (asks before placing)
  → Ideas accumulate on canvas
  → Driver signals "ready to spec"
  → Claude drafts spec from canvas + conversation
  → Driver reviews and approves
  → Spec saved → Recall ingested → BrickLayer build triggered
```

---

## 4. Task Management

### How Tasks Are Created
- Claude suggests task breakdowns after spec approval
- Humans make final assignment decisions
- Tasks can be created manually at any time
- Tasks linked to specs, canvas nodes, and git commits

### Task Completion
Tasks are completed with a mini-PR-style gate:
1. Developer marks task done
2. Tests must pass (automated check)
3. Claude reviews the implementation first
4. Team member confirms (lightweight approval, not a full code review unless flagged)

This creates accountability without bureaucratic overhead.

### Task Visibility
- All tasks visible on dashboard
- Per-user task list in personal panel
- Tasks linked to knowledge graph nodes

---

## 5. Catch-Up & Digest

When a user logs in after being away, a **pre-generated digest** is presented as a dismissable panel:

- What was decided
- What was built
- What changed on canvas
- New tasks assigned to them
- Commits and PRs merged

Claude is available on demand for deeper catch-up ("explain this decision to me"). The digest is powered by Recall + activity feed — it's accurate, not summarized from logs.

---

## 6. AI in Agent Mode (BrickLayer Build)

When BrickLayer is running an agent build inside CodeVV:

- **Live log stream** — terminal-style panel shows what agents are doing in real time
- **Live diff preview** — as agents write code, diffs appear in a side panel in real time
- **Interruptible** — any team member can pause the agent run, direct Claude, then resume
- Build status visible on dashboard (project health indicator)

The team watches the build happen. Nothing is hidden.

---

## 7. Knowledge Graph

The knowledge graph is the live brain of the project.

### What It Contains
- People (team members, their roles, contributions)
- Projects and their relationships
- Tasks (current, completed, blocked)
- Decisions (what was decided, when, in what context)
- Files and code modules
- Canvas nodes and brainstorm artifacts
- AI conversations and meeting transcripts
- Recall memories

### How It Works
- **AI-maintained:** Claude and Recall continuously update the graph as work happens
- **Navigable:** click any node to open the related item (file, canvas, task, conversation)
- **Manually editable:** team members can add nodes, draw connections, annotate relationships
- **Live:** the graph reflects the project's actual state at all times

### Where It Appears
- Dedicated Knowledge Graph panel (launchable from dock)
- Inline: when Claude references a decision, it links to the graph node
- Search: global search scoped to graph nodes

---

## 8. Personal AI Assistant (Per User)

Every user builds and owns their own AI assistant. This is not a shared tool — it is genuinely theirs.

### What It Is
- Named by the user
- Has a persistent personality and memory that grows over time
- Learns the user's working style, preferences, communication patterns, and domain knowledge
- Remembers past sessions, decisions, and things the user has taught it
- Runs through BrickLayer's routing layer — it can invoke BrickLayer agents on the user's behalf

### What It Can Do
**Development tasks:**
- Code assistance, debugging, code review
- Invoking BrickLayer agents (researcher, developer, reviewer)
- GitHub: PRs, issues, code review inside CodeVV

**Managerial & daily tasks:**
- Email: read, draft, send (Gmail + SMTP)
- Calendar management
- Task tracking
- Daily standup summaries
- Weekly digest emails

**Automation (trigger-based + scheduled):**
- New GitHub PR → draft review email
- Build failed → notify team
- Task overdue → reassignment suggestion
- Daily/weekly scheduled jobs (summaries, nudges, reports)
- Any trigger the user configures

### Tool Access
Users configure their assistant's tool loadout:
- Recall (always available — scoped to that user's memory)
- File system (CodeVV project files)
- GitHub
- Canvas
- BrickLayer agents
- Any MCP server the user connects (email, calendar, Slack, home automation, etc.)
- **Open MCP:** if an MCP server exists for it, the assistant can use it

### Persistence & Growth
The assistant builds a model of the user over time:
- Every session it learns something new about how the user works
- Preferences are stored in Recall (user-scoped)
- Personality persists across sessions, machines, and reinstalls (synced via Recall)

### Team Interaction
- **Public invocation:** owner can @mention their assistant in team contexts — team sees the response
- **Proxy mode (optional):** when the user is away, teammates can ask the assistant questions about their work
- Proxy mode is opt-in per user, toggled in settings

---

## 9. Custom Team Agents

Beyond personal assistants, teams can build specialized agents for project work.

### How They're Built
- Start from presets (researcher, coder, reviewer, security auditor, etc.) or from scratch
- Write a system prompt describing the agent's role and expertise
- Configure tool access (same MCP tool loadout system as personal assistants)
- Name the agent and assign it to the project

### Sharing
- Agents are shareable with the team or kept private
- Stored in the project (version-controlled)
- Team agents appear in the BrickLayer agent registry

### BrickLayer Integration
Custom agents run through BrickLayer's crucible:
- They are benchmarked on real tasks
- Performance scored over time
- Promoted when they perform well, flagged or retired when they don't
- The team builds a living, improving agent fleet over time

---

## 10. Git & GitHub Integration

Git is always available. GitHub features activate when a remote is connected.

### Always Available (Git)
- Git panel: status, stage, commit, push, branch management
- Diff view in Review workspace
- Commit history linked to knowledge graph

### When GitHub Remote Is Connected
- PR creation, review, and merge inside CodeVV
- Issues: view, create, link to tasks
- Code review: inline comments, approval
- `git-nerd` agent handles automation (PR summaries, review emails, issue triage)
- GitHub is optional — local-only projects work without it

---

## 11. Project Creation

### Creating a New Project
1. Name the project, set a description
2. **Import existing docs** (PDF, DOCX, Excel, etc.) — all ingested into Recall
3. Connect a GitHub repo (optional)
4. Claude drafts an initial project brief from the imported documents
5. Brief is stored in `docs/project-brief.md` and Recall

### Loading an Existing Project
- Connect a GitHub repo → project populates from the codebase
- Claude analyzes the codebase and generates a brief
- Team is onboarded via the Claude-guided tour

---

## 12. Roles & Permissions

### Core Roles
Lightweight role system — two tiers:

| Role | Capabilities |
|------|-------------|
| **Admin** | Everything: user management, permissions, project settings, data export, Recall purge |
| **Member** | Full project access: code, canvas, brainstorm, build, tasks |

Members are equal. There is no "read-only team member" — everyone can contribute.

### Fractional Hires
- Scoped access — admin defines what projects and panels they can see
- Sandboxed — limited tool access by default
- AI onboarding — Claude walks them through their scoped project context
- Admin can expand permissions as trust is established

### Workspace Templates by Role
- Role-based defaults: admins see the budget/progress/resource dashboard by default, members see development workspace
- Everyone can access all templates — defaults are just starting points
- Admin sets team-wide template defaults

---

## 13. Collaboration Features

### Real-Time Presence
- Collaborator avatars on file tree items (who has this file open)
- Collaborator cursors in code editor (CodeMirror 6 + Yjs awareness)
- "N people viewing" badges on canvas
- Who's in which terminal session
- Who's in which AI conversation
- User status: online, away, focused, in meeting, do not disturb

### Follow Mode
- Click a teammate's avatar → your panel layout mirrors theirs in real-time (Figma-style)
- Presentation mode: one driver, team follows
- Unfollow returns you to your own layout

### Shared Terminal (Mob Programming)
- Multi-user input in SharedTerminal
- Driver types, others observe with live cursor
- "Pass the keyboard" via click or shortcut
- Session recording for async review

### LiveKit Video
- Full video calls embedded in the workspace (voice + screenshare + video)
- AI meeting assistant joins as a participant
- Real-time transcription with speaker attribution
- Auto-generated meeting summaries → action items, decisions, code references → stored in Recall
- Push-to-talk AI in meetings: voice question → Claude responds in text

### Notifications
- Per-type preferences: each user configures what's urgent vs. quiet
- Urgent (build failed, @mention, task assigned) → toast (bottom corner, auto-dismiss)
- Everything else → notification drawer (bell icon, accumulates)
- Push notifications on mobile (see Mobile section)

---

## 14. Mobile Access

CodeVV OS is a desktop platform, but team members can access it remotely:

- **Responsive web app** — full CodeVV accessible from any browser via Tailscale
- Limited on small screens but functional (read code, check tasks, review diffs, chat with AI)
- **Push notifications** — @mentions and task assignments delivered to mobile

---

## 15. Global Search

One search bar, everything:

| Scope | What It Searches |
|-------|-----------------|
| This file | ripgrep-backed content search |
| This project | All files + canvas nodes + project docs |
| All projects | Cross-project file and canvas search |
| Recall memory | Semantic search across all conversations, decisions, meetings, findings |

Scoped via filter toggle. Default scope is current project.

---

## 16. Onboarding

### New User to an Existing Project
1. User logs in, lands on dashboard
2. Claude delivers a **guided tour**:
   - What the project is
   - Key decisions that have been made (cited from Recall)
   - What's currently in progress
   - Who the team members are and what they own
3. Tour is accurate — drawn from real project history in Recall, not generic copy

---

## 17. Offboarding

When a team member leaves:
1. Admin revokes access
2. Claude generates a **knowledge transfer summary**:
   - What they owned and built
   - Open tasks they had
   - Key context only they held
3. Claude suggests who should pick up their open tasks
4. **Recall purge option:** admin can remove their personal Recall memories while keeping all project contributions and attribution intact

---

## 18. Canvas & Projector

### Canvas Capabilities
- tldraw-based freeform canvas
- Structured templates (brainstorm grids, architecture diagrams, sprint boards)
- AI-generated sticky notes, clusters, and diagrams (Claude asks before placing)
- Architecture diagrams linked to actual code modules (bidirectional)
- All canvas output stored in Recall

### Wireless Projector Casting
Two modes for sharing canvas to the office projector:

1. **W3C Presentation API** — browser-native, works with any display connected to a presentation receiver
2. **Dedicated projector URL** — a stripped-down `/projector` route served from CodeVV that the projector's browser loads; mirrored live via Yjs

Admin configures which projector URL maps to which physical display.

---

## 19. BrickLayer & Masonry Integration

### Integration Approach

**Masonry** ships as an npm package — it's Node.js and that's legitimate:
```
npm install masonry-mcp
```
Installed in the CodeVV Docker image. Version-pinned in `package.json`.

**BrickLayer** is a Python engine. It runs as a **Docker sidecar service** — the same pattern as Recall. Tim adds `bl/server.py`, a thin FastAPI wrapper (~100 lines) that exposes BrickLayer's core dispatch functions over HTTP:

| Endpoint | Maps to |
|----------|---------|
| `POST /agent/spawn` | `spawn_agent(name, prompt, cwd)` |
| `GET /agent/{id}` | agent status / wait |
| `POST /wave/spawn` | parallel multi-agent dispatch |
| `GET /crucible/scores` | agent benchmark scores |
| `POST /sim/run` | simulate runner |

CodeVV's backend calls `http://bricklayer:8300/` — no direct Python import, clean separation. Version updates are a Docker image tag bump + `docker compose pull`. BrickLayer's image includes tmux + the Claude CLI so agents still dispatch into visible panes.

### What They Provide Inside CodeVV OS
- **Masonry MCP server:** agent routing, hooks, registry, Ollama embeddings for semantic routing
- **BrickLayer engine:** campaign runners, agent dispatch via tmux, crucible benchmarking, heal loop, simulation runners
- **Agent fleet:** 100+ specialized agents accessible from within any CodeVV workspace
- **Custom agents:** teams build agents that run through BrickLayer's routing and crucible

### Availability
BrickLayer features surface through the AI Agent Mode panel (live log + live diffs + interruptible). Masonry MCP is available to Claude as a tool server once the npm package is installed.

---

## 20. Settings, Keyboard Shortcuts & Theming

### Settings
- Stored in PostgreSQL — synced across all machines automatically on login
- Export/import: portable JSON config file for backup or migration
- Layered: user settings override system defaults; admin can set org-wide defaults

### Keyboard Shortcuts
- Command palette (`Cmd+K`) — access everything
- Opinionated defaults for common actions
- Fully remappable (VS Code-style)
- **Per-workspace shortcut profiles** — each workspace template can define its own shortcut set

### Theming
- Dark mode + light mode toggle
- **Per-workspace accent colors** — brainstorm workspace feels visually distinct from dev workspace
- Accent color is part of the workspace template definition

---

## 21. Export & Backup

### Manual Export
- Canvas: PNG / SVG
- Documents: PDF / Markdown
- Full project archive: code + canvas + docs + task history + AI conversation logs (zip)

### Automated Backups
- Scheduled exports to a configured location (local path, S3, or any mounted storage)
- Schedule is configurable per project
- Backup includes everything in the manual export plus database snapshots

---

## 22. Connectivity

CodeVV OS and Recall run on the same Proxmox machine. Recall calls are loopback/local — always available when the machine is up.

Claude API (external internet) is the only true external dependency:
- **Graceful degrade:** if Claude API is unreachable, local features stay fully operational (editor, terminal, git, canvas, file tree)
- **Queue pending AI requests:** buffer requests, replay automatically when connection restores

---

## 23. Artifact Panel

The Artifact Panel is a sandboxed iframe renderer that lives as a dockview panel alongside the AI chat. When Claude generates interactive content — charts, graphs, React components, data visualizations, simulations — it renders live in this panel.

### How It Works
- Claude generates HTML / JSX / React code in the chat
- Content is injected into a sandboxed iframe (CSP-restricted, postMessage communication)
- Renders immediately alongside the conversation — no copy-paste, no separate tab
- User can interact with the rendered output (click, hover, input)
- Code is editable inline — change a value, re-render instantly
- All artifacts are saved to the project and stored in Recall

### What Renders Here
- Charts and graphs (recharts, D3, Chart.js — Claude picks based on data)
- Interactive React components and UI prototypes
- Data tables and pivot views
- Simulation outputs (see Sandbox section)
- Mathematical visualizations
- Architecture diagrams generated from code analysis

---

## 24. Sandbox (Three Modes)

A unified "Sandbox" panel with three distinct modes, switchable via tab.

### Mode 1: Code Scratchpad
Isolated code execution — paste or write a snippet, run it safely, see output. Completely isolated from the main project. Supports multiple languages (Node.js, Python, bash). Results appear inline. No project files are touched.

Use cases: test a regex, prototype a function, verify an algorithm, explore an API response.

### Mode 2: Environment Clone
Spin up a full isolated copy of the current project environment. Try something risky — a major refactor, a dependency upgrade, an architectural experiment — without touching the main branch. When done: promote changes to main or discard. Backed by Docker — each clone is a container snapshot.

Use cases: test a destructive migration, experiment with replacing a library, validate a build change before committing.

### Mode 3: Artifact Sandbox (connected to Artifact Panel)
Claude generates runnable code. It executes in the sandbox and output renders in the Artifact Panel. This is the bridge between the AI chat and live interactive output. The sandbox handles execution; the Artifact Panel handles display.

---

## 25. Simulation Sandbox

Built on top of Sandbox Mode 3 and the Artifact Panel. BrickLayer's simulate runner is surfaced visually here.

### Data Simulations
Run what-if scenarios against project data:
- Feed in a dataset (CSV, JSON, database query result)
- Define variables and constraints
- Claude generates the simulation code
- Results render as interactive charts/graphs in the Artifact Panel
- Tweak inputs, re-run, compare outputs

Use cases: revenue projections, load testing projections, user growth models, A/B test outcome modeling.

### System Simulations
Model how architecture will behave before building it:
- Describe the system (components, load, interactions)
- BrickLayer's simulate runner models the behavior
- Output: latency curves, failure rates, bottleneck identification, capacity recommendations
- Results rendered as diagrams and charts in the Artifact Panel

Use cases: "How does this queue design handle 10x traffic?", "Where does this architecture break under load?", "Is this database schema going to hold up?"

Both simulation types feed results back into Recall as project findings.

---

## 26. File Viewers & Editors

All file types open as dockview panels. Documents ingested into projects (uploaded or referenced) open in the appropriate viewer.

### PDF
- PDF.js renderer in a dockview panel
- Annotation support (highlight, comment) — comments stored in Recall
- Searchable text extraction for global search indexing

### DOCX
- `docx-preview` for read-only viewing (renders to clean HTML in-browser)
- Editing: `mammoth.js` converts DOCX to rich text → editable in TipTap rich text editor → export back to DOCX
- Full ONLYOFFICE integration available as optional Docker service for teams needing native DOCX fidelity

### Excel / Spreadsheets
- **Univer** — open-source Excel-like editor, full formula support, charts, formatting
- `@univerjs/sheets-import-xlsx` for `.xlsx` import/export — **not SheetJS** (Univer has its own xlsx engine; SheetJS would conflict)
- **V1: single-user only.** Univer multi-user collab requires `univer-server` Docker service which is not in the V1 compose. Do NOT add Yjs collab for Excel — Univer does not use Yjs. Multi-user Excel collaboration is a V2 feature when `univer-server` is deployed.
- Claude can read spreadsheet data as context and generate formulas, pivot tables, or charts
- Charts from spreadsheet data render in the Artifact Panel

### All Document Types
- Imported documents are ingested into Recall on open (text extracted, semantically indexed)
- Global search finds content inside PDFs, DOCX, and spreadsheets
- Documents link to knowledge graph nodes (which project, which decision, which task)

---

## 27. Team Intelligence Features

### Ambient Terminal Watching
Claude observes the terminal alongside the editor. When an error appears, it proactively offers an explanation and fix suggestion inline — no copy-pasting required. The user can dismiss or engage. Claude already has full ambient context (open file, canvas, current task) — terminal is the final piece.

### Session Handoff
When a user ends their session, Claude writes a handoff note to Recall: what they were working on, where they stopped, what the next step is. Next login surfaces it immediately: *"Welcome back — you were in the middle of X, next step is Y."* Personal assistant picks up exactly where the session ended.

### Decision Archaeology
Before a decision is made, Claude searches Recall across all projects for similar past decisions. Surfaces relevant history: *"Six months ago on Project X you ruled out Redis pub/sub for this reason — still applies?"* Prevents repeating solved problems and learning the same lesson twice.

### Architecture Drift Detection
After a spec is approved and build begins, BrickLayer periodically diffs the actual codebase against the spec and all ADRs. Drift surfaces proactively before it compounds: *"Spec says PostgreSQL for sessions, code is using Redis."* Flagged as a task — not a blocker, but visible.

### Cross-Project Intelligence
Claude monitors patterns across all projects in Recall. When a team is solving a problem that's already been solved in another project, it surfaces the existing solution: *"This rate-limiting logic is nearly identical to what's in Project X — want to extract a shared module?"* Prevents duplicate work across projects.

### Impact Analysis ("What Would This Break?")
Before a PR merges or a task is marked complete, Claude analyzes downstream impact: files that import the changed module, tests likely affected, other projects sharing this code. Surfaces as a brief risk panel — one click to review, one click to dismiss.

### Live Module Documentation
As BrickLayer writes code, Claude maintains a living prose explanation per module — not docstrings, actual human-readable narrative: what it does, why it exists, how it connects to other parts. Stored in Recall. Updated automatically when the module changes. When you open a file you haven't touched in months, the explanation is there.

### Sprint Retrospective
At the end of each sprint or week, Claude generates a data-driven retrospective: task completion rates, git velocity, what got blocked, how long tasks actually took vs. estimates, patterns in what got deferred. Delivered as a digest panel. Stored in Recall. Informs next sprint's planning automatically.

---

## 28. Ideation Intelligence Features

### Idea Backlog
A dedicated idea bank — separate from the task board — for ideas that aren't ready to become tasks yet. Ideas captured during brainstorms land here automatically. Claude periodically resurfaces relevant ideas when project context matches: *"You brainstormed a caching approach three months ago that's directly relevant to what you're building now."* Nothing gets lost.

### Assumption Tracker
Every project runs on assumptions. Claude captures them explicitly as they surface in conversations and brainstorms. Tracks validation status: confirmed, unconfirmed, invalidated. Before a build triggers, Claude surfaces the assumption audit: *"You're building on 3 unvalidated assumptions — here they are."* Teams decide to validate or accept the risk consciously.

### Pre-Mortem Before Build
Before BrickLayer triggers a build, Claude runs a structured pre-mortem: *"Imagine this shipped and failed. What are the 3 most likely reasons?"* Five minutes of structured failure-mode thinking before the team is invested. Outputs become tracked risks in the project knowledge graph.

### Parallel Spike Dispatch
For uncertain technical decisions, BrickLayer spins up small parallel throwaway spikes — quick real implementations of each option — and reports back with actual benchmarks, not opinions. You choose the approach with data. Spikes are discarded after the decision is made; the decision and benchmark results are stored in Recall.

### Code Archaeology
"Why does this code exist?" Claude traces any piece of code back through its full lineage: the task that created it, the brainstorm session that spawned the idea, the meeting or conversation where the decision was made. Full provenance from code back to original intent, powered by Recall + git history. Surfaces in a side panel when you hover over a module or function.

### Rubber Duck Mode
A dedicated conversation mode where Claude listens and asks questions only — no suggestions, no code, no answers. Pure Socratic dialogue. Devs talk through a problem and usually solve it themselves in the process. Claude monitors the conversation and asks one clarifying question at a time. User can explicitly switch to "give me your take" when ready.

### Constraint-Aware Ideation
During brainstorming, Claude knows the team's actual constraints: stack, team size, open tasks, runway, current velocity. When ideas are generated, it surfaces the *buildable* version alongside the full vision: *"Here's the minimal version of that idea with 2 devs in 3 weeks."* Keeps ideation grounded without killing ambition.

### The Weekly Brief
Every Monday morning, a team-wide AI-generated brief appears in the dashboard digest:
- What shipped last week (git + task data)
- What's planned this week (task board)
- Active blockers
- Decisions that need to be made this week
- Team velocity trend

Pulled from real data — Recall, git, tasks. Not manually written. Keeps the team aligned without a sync meeting.

---

## Decisions Summary Table

| Area | Decision |
|------|----------|
| Dashboard | Team-wide + personal panels, all projects visible, open alongside don't replace |
| Workspace selection | Work type suggests template, user always picks manually |
| Brainstorm driver | One driver, observers interject via @mention toast |
| Spec hard gate | Claude drafts → driver approves → build triggers. No code before approval |
| Canvas | Freeform + structured + AI-generated. Claude asks before placing objects |
| Projector | Presentation API + dedicated /projector URL |
| Tasks | AI suggests breakdown, humans assign. Mini-PR gate on completion |
| Catch-up | Pre-generated digest on login + Claude on demand |
| Agent mode | Live log + live diff + interruptible by any team member |
| Knowledge graph | AI-maintained, navigable, manually editable, live |
| Personal assistant | Per-user, persistent, open MCP, trigger automation, proxy mode optional |
| Custom agents | BrickLayer crucible — benchmarked, scored, promoted/retired |
| GitHub | Optional, full when connected. git-nerd agent |
| BrickLayer | Docker sidecar + `bl/server.py`. SSE streaming + interrupt/kill endpoints. asyncio.to_thread(). |
| Masonry | `npm install masonry-mcp` in CodeVV Docker image |
| Inline AI editing | Cmd+K inline diff in CodeMirror. Accept/Reject/Regenerate. Distinct from chat. |
| Live preview | Hot-reload iframe panel proxied through Nginx. Viewport simulator. Error overlay. |
| Branch auto-environments | Auto Docker snapshot per branch (extends Sandbox Mode 2). TTL-based cleanup. |
| PR descriptions | git-nerd agent drafts from diff + tasks + Recall context. One-click accept/edit. |
| Guest links | Read-only scoped links (canvas/spec/dashboard). No account. Configurable expiry. |
| Spec gate UI | One-click Linear-style approval. Rejected spec returns to canvas with annotation. |
| Dependency scanning | npm/pip audit on save. Severity tiers. Claude suggests fix. CRITICAL/HIGH → tasks. |
| Univer collab | V1 single-user only. V2 adds univer-server. |
| tldraw sync | tldraw native sync (not Yjs). Requires tldraw-sync Docker service. |
| Artifact Panel | srcdoc null-origin iframe. allow-scripts only. Server-side compile. No unsafe-eval. |
| docker.sock | Removed from backend. sandbox-manager owns it via socket-proxy (exec scope only). |
| ARQ worker | Separate worker service. Required for all background jobs. Same backend image. |
| pgvector | Removed — no use case. Recall uses Qdrant. |
| react-window | Replaced with @tanstack/react-virtual v3 throughout. |
| Notifications | Per-type user preferences. Urgent → toast, rest → drawer |
| Connectivity | Recall is local. Claude API graceful degrade + queue |
| Keyboard | Command palette + opinionated defaults + per-workspace profiles |
| Settings | PostgreSQL sync + export/import |
| LiveKit | Full video + screenshare + AI meeting assistant |
| Mobile | Responsive web via Tailscale + push notifications |
| Global search | Files + canvas + docs + Recall, scoped |
| Onboarding | Claude-guided tour from real Recall history |
| Offboarding | Revoke + knowledge transfer + reassignment + Recall purge option |
| Export | Manual (PNG/SVG/PDF/zip) + scheduled automated backups |
| Theming | Dark/light + per-workspace accent colors |
| Roles | Admin + Member (equal). Fractional hires scoped by admin |
| Project creation | Import existing docs → Recall ingestion → Claude drafts brief |
| Artifact Panel | Sandboxed iframe + postMessage. Claude-generated charts/sims/components render live |
| Sandbox | Three modes: code scratchpad + environment clone + artifact sandbox |
| Simulation | Data simulations + system simulations, both render to Artifact Panel |
| PDF viewer | PDF.js in dockview panel + annotation stored in Recall |
| DOCX viewer/editor | docx-preview + mammoth.js/TipTap. ONLYOFFICE optional for full fidelity |
| Excel editor | Univer + `@univerjs/sheets-import-xlsx`. V1 single-user only (no univer-server, no Yjs). Claude reads data as context |
| Terminal watching | Claude observes terminal, proactively explains errors inline |
| Session handoff | Claude writes handoff note to Recall on session end. Surfaces on next login |
| Decision archaeology | Claude searches Recall across all projects before decisions are made |
| Architecture drift | BrickLayer diffs codebase vs. spec after build starts. Drift surfaced as tasks |
| Cross-project intelligence | Claude surfaces duplicate work across projects via Recall |
| Impact analysis | Claude surfaces downstream risk before PR merge / task completion |
| Live module docs | BrickLayer maintains living prose explanation per module in Recall |
| Sprint retrospective | AI-generated from real data (git, tasks, Recall). Delivered as digest |
| Idea backlog | Separate from task board. Claude resurfaces contextually relevant ideas |
| Assumption tracker | Captured explicitly. Validation status tracked. Surfaced before build |
| Pre-mortem | Structured failure-mode session before every build. Outputs → risk tracking |
| Parallel spikes | BrickLayer runs throwaway parallel implementations. Choose with real benchmarks |
| Code archaeology | Full provenance: code → task → brainstorm → meeting. Via Recall + git |
| Rubber duck mode | Claude listens and asks only. No suggestions until user switches mode |
| Constraint-aware ideation | Claude surfaces buildable version of each idea given real constraints |
| Weekly brief | Monday AI digest: shipped, planned, blockers, decisions needed, velocity |

---

*Spec opened: 2026-04-01. Last updated: 2026-04-02. All decisions made by Tim via Superpowers Socratic session.*

---

## 29. Mobile / Dockview Responsive Strategy

### Breakpoints

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Mobile | < 768px | dockview replaced by full-screen panel stack + bottom tab bar |
| Tablet | 768px–1023px | dockview active but panels are wider minimum widths; sidebar auto-collapses |
| Desktop | ≥ 1024px | Full dockview layout — default experience |

### What Happens to Each Panel at Mobile Width

dockview is not visible on mobile. The layout engine detects `window.innerWidth < 768` and switches to the `MobileShell` component, which renders a single full-screen panel at a time plus a fixed bottom tab bar.

| Panel | Mobile behavior |
|-------|----------------|
| Team Dashboard | Full-screen — this is the home screen |
| File Tree | Full-screen panel, accessed from bottom nav |
| Code Editor | Full-screen panel; toolbar collapsed to icon strip |
| Terminal | Full-screen panel with "limited keyboard" warning banner; accessible but expect mobile keyboard friction |
| AI Chat | Full-screen panel — works well on mobile |
| Canvas (tldraw) | Full-screen; touch-native (see touch model below) |
| Git panel | Full-screen |
| Knowledge Graph | Full-screen; simplified list view replaces force graph at mobile |
| BrickLayer log | Full-screen; read-only on mobile (no interrupt action) |
| Settings | Full-screen |
| Video (LiveKit) | Full-screen; joins as audio-only by default on mobile |

Panels that are purely decorative at mobile (artifact panel, live preview) are **hidden from the bottom tab bar** but remain accessible via the "More" overflow sheet.

### Bottom Tab Bar Navigation

Five primary tabs, always visible:

```
[ Dashboard ] [ Files ] [ Terminal ] [ AI Chat ] [ More ▾ ]
```

- **Dashboard** → Team Dashboard panel
- **Files** → File tree (tapping a file opens Editor panel, replacing Files)
- **Terminal** → Terminal panel
- **AI Chat** → Personal AI assistant chat
- **More ▾** → Bottom sheet listing all other panels: Canvas, Git, Knowledge Graph, Settings, BrickLayer, Notifications, Search

Active tab indicator: 2px `--color-accent` top border on the tab icon.

The bottom bar has a fixed height of 56px and sits above the OS home indicator safe area (use CSS `env(safe-area-inset-bottom)` for iOS Safari compatibility).

### Terminal Accessibility on Mobile

Terminal is accessible on mobile. A persistent yellow banner appears at the top of the terminal panel:

> *"Terminal works best with a physical keyboard. Mobile keyboard may clip input."*

This is dismissable per-session. The terminal functions — the warning exists to set expectations. No code blocks terminal access on mobile.

### Touch Interaction Model — tldraw Canvas

tldraw's native touch support covers most interactions. Explicitly supported:

- **Pan:** Two-finger drag
- **Zoom:** Pinch gesture (standard tldraw behavior)
- **Select:** Single tap a shape
- **Move shape:** Long-press (300ms) to enter drag mode, then drag
- **Context menu:** Long-press on empty canvas (300ms)
- **Text input:** Tap a text node → mobile keyboard appears, canvas shifts up using `visualViewport` resize handling

Not supported on mobile (suppressed from the toolbar):
- Freehand drawing tools (too imprecise without Apple Pencil)
- Right-click context menus (replaced by long-press)

A floating "Pencil mode" toggle appears if stylus input is detected (via Pointer Events API `pointerType === 'pen'`).

### Tablet Behavior (768px–1023px)

dockview remains active at tablet widths. Behavioral changes:
- Sidebar auto-collapses to icon-only mode (40px wide) on initial render
- Default panel minimum width reduced from 280px to 200px
- Two-panel max visible simultaneously (wider panels auto-split)
- Dock bar remains at bottom; icons slightly larger (32px)

---

## 30. OS-Style Login Screen

### Overall Visual Design

The login screen is full-viewport, rendered before the main app shell loads. It has three visual layers:

**Layer 1 — Background:** The base color (`#0D160B`) with a very subtle animated gradient. Not a screensaver, not a video — a slow-moving, low-opacity radial gradient in the workspace-default accent color (`#4F87B3` at 4% opacity), drifting across the screen at 20-second intervals. On a second monitor or projector, this looks like a lit wall. On a laptop, it reads as "powered on, waiting."

**Layer 2 — Center card:** A floating panel (480px wide, 8px radius, `--shadow-5`) centered vertically and horizontally. Background: `--color-surface-1`. Contains the user picker.

**Layer 3 — Footer:** A thin status bar at the very bottom of the screen showing: `CodeVV OS` on the left, system time (HH:MM) on the right. Font: `--font-mono`, size `--text-sm`, color `--color-text-tertiary`.

### Multi-User Picker (macOS-Style)

When multiple users exist, the login card shows a **user picker grid** — not a username field. Layout:

- User cards arranged in a centered row (up to 4 across; wraps to 2-column grid if 5+ users)
- Each card: 80px avatar circle (initials or uploaded photo) centered, display name below in `--text-sm --font-weight-medium`
- Card hover: subtle `--color-surface-3` background, 100ms transition
- Card click: selected user animates (scale 0.95 → 1.0) and transitions to the password phase

**Password phase** (after user selection):

- The user picker fades out (150ms)
- The selected user's avatar expands to 64px and moves to the top of the card
- Display name appears below the avatar
- A password input field fades in below — single field, auto-focused, `--radius-sm`, 44px height
- "Sign in" button below the password field (full-width, accent fill)
- Subtle text: "← Other user" (ghost button, goes back to picker)

If only one user exists, the picker is skipped and the card shows the single user's avatar + password field immediately.

### Error States

**Wrong password:**
- Input border turns `--color-error`
- Card shakes horizontally (CSS keyframe: 0%→4px→-4px→3px→-3px→0%, duration 400ms)
- Error message appears below input in `--color-error --text-sm`: "Incorrect password. Try again."
- Input clears and re-focuses

**Account locked (5 failed attempts):**
- Input is disabled
- Message: "Account locked. Contact your admin." in `--color-warning`
- "Sign in" button disabled

**Network/backend error:**
- Message: "Unable to reach CodeVV. Check that services are running."
- Retry button below

### Admin Edge Cases

- If no users exist (first boot), the login screen shows a "Create admin account" form instead of the picker
- If SSO is configured (future), the card shows "Sign in with [provider]" button instead of password field (V2)

---

## 31. App Dock Behavior

### Visual Design

The dock bar is a persistent horizontal bar at the bottom of the screen, 48px tall, spanning the full viewport width. It sits **outside the dockview layout tree** — it is never part of a panel arrangement and cannot be closed.

Background: `--color-surface-2`. Top border: 1px `--color-border-subtle`. No shadow (it's flush with the screen bottom). A subtle `rgba(255,255,255,0.02)` gradient from top to bottom gives the bar a very faint lift without looking like a card.

### Icon Slots

The dock has three zones, separated by 1px `--color-border-subtle` dividers:

```
[App icons — left zone] | [Workspace indicator — center] | [System icons — right zone]
```

**Left zone — App launchers:**
- Icon containers: 36px × 36px, `--radius-sm`, 6px padding around the Lucide icon (24px icon inside)
- Spacing between icons: 4px gap
- Default icon color: `--color-text-secondary`

**Center zone — Workspace switcher:**
- Shows the active workspace name + accent color chip
- Clicking opens `WorkspaceSwitcherModal`

**Right zone — System:**
- Notifications bell (with badge), Settings gear, User avatar (32px circle, opens user menu), time display

### Icon States

| State | Visual |
|-------|--------|
| Default | Icon at `--color-text-secondary`, no background |
| Hover | `--color-surface-3` background (100ms ease), icon at `--color-text-primary` |
| Active (panel open) | 3px accent dot centered below the icon, icon at `--color-accent` |
| Active + focused (panel is foreground) | Dot is solid `--color-accent`, icon fill at `--color-accent`, no background change |
| Badge/notification | Red dot (8px, `--color-error`, `--radius-full`) at top-right of icon container, count label inside if > 9 |
| Drag-over (panel drop target) | Brief `--color-accent-dim` background pulse |

Tooltip on hover: appears above the icon after 500ms hover delay. Dark tooltip (`--color-surface-5`, `--shadow-2`, `--radius-xs`), 12px font, no arrow.

### App Launcher Behavior When App Is Already Open

| Scenario | Behavior |
|----------|----------|
| App panel exists, is focused | Nothing (or brief pulse animation on the panel tab to confirm it's already foreground) |
| App panel exists, is not focused | `dockviewApi.getPanel(id).focus()` — brings panel to foreground without creating a new one |
| App panel was closed | `dockviewApi.addPanel({...})` — creates a fresh panel in the last-known position |

There is no "open a second instance" behavior. Each dock icon maps to exactly one panel ID. This is OS-style: one app, one window, always reachable.

### Dock Position

**Fixed: bottom.** Not configurable in V1. The dock is always at the bottom of the screen. This is the correct default for a horizontal-monitor dev workstation and avoids the layout complexity of a left-rail dock competing with the file tree sidebar. V2 may add a left-rail option if user feedback demands it.

---

## 32. Branch Auto-Environment UX

### Where Environments Appear

Branch auto-environments surface inside the **Git panel** (a dockview panel, launchable from the dock). The Git panel has two sections in its sidebar:

1. **Repository** — current branch, status, stage/commit/push
2. **Environments** — list of active branch environments (appears as a collapsible section below Repository)

The Environments section also shows a compact status indicator in the dock bar's git panel icon (e.g., "3 environments" badge).

### Environment List

Each branch with an active environment shows a row:

```
● feature/auth-refactor    [Running]    [Switch]  [Stop ▾]
◌ feature/payment-v2       [Creating…]  [—]       [—]
✕ hotfix/null-check        [Failed]     [Retry]   [Delete]
  main                     [—]          [Active]  [—]
```

Status dot colors:
- `●` green (`--color-success`) — environment running
- `◌` yellow spinner (`--color-warning`) — environment being created
- `●` red (`--color-error`) — creation failed
- `—` gray — no environment (main/default branch)

### In-Progress Creation State

When a new branch is created (or the user manually triggers "Create environment"):

1. A row appears immediately in the Environments list with a spinning indicator
2. Status text: "Creating environment…"
3. A thin animated progress bar below the branch name shows estimated progress (this is fake/cosmetic — the actual progress is non-deterministic, so the bar crawls from 0→80% on a 10-second ease, then stalls until completion)
4. On success: bar fills to 100%, status changes to "Running" with a brief success pulse
5. On failure: bar turns red, status shows "Failed", Retry button appears

No toast for environment creation — the Git panel is the status surface. Only show a toast if the panel is closed: "Environment for `feature/auth-refactor` is ready."

### Environment Switch Flow

Clicking "Switch" on a running environment:

1. A **confirmation modal** appears (not an inline confirm — this is a significant action):
   - Title: "Switch to `feature/auth-refactor`?"
   - Body: "Your current terminal session will be paused. Unsaved editor content will be preserved. You can switch back at any time."
   - Two buttons: `Cancel` and `Switch Environment` (accent fill)
   - If the current environment has uncommitted git changes: add warning "You have uncommitted changes in the current environment."

2. On confirm:
   - Active terminal sessions show a brief "Environment switching…" overlay (not killed — the PTY is paused on the backend)
   - The editor file tree reloads against the new environment's filesystem
   - A persistent status chip appears in the dock bar showing the active environment name: `● feature/auth-refactor`

3. The environment chip in the dock bar is the persistent indicator of which environment is active. Clicking it opens the Git panel directly.

### Environment Management

Long-press (or right-click) on an environment row opens a context menu:
- Open terminal in this environment
- View environment logs
- Promote changes to branch (commit + push what's in the environment)
- Set TTL (1h / 4h / 24h / until branch deleted)
- Delete environment

TTL expiry: a toast notification 15 minutes before expiry: "Environment `feature/auth-refactor` will stop in 15 min. Extend?" Two actions: "Extend 4h" and "Dismiss."

---

## 33. Guest / Shareable Link UX

### How an Admin Generates a Link

A "Share" button (icon: `Share2` from Lucide, 16px) appears in the header of three surfaces:
- Canvas panel header
- Spec viewer panel header
- Team Dashboard header (generates a read-only dashboard snapshot link)

The Share button is **only visible to Admin role users.** Members see no share button.

Clicking Share opens a **Share Modal** (380px wide, centered, `--shadow-4`):

```
┌─────────────────────────────────────┐
│  Share this canvas                  │
│                                     │
│  Share type                         │
│  ● Canvas (read-only)               │
│  ○ Spec (read-only)                 │
│  ○ Dashboard snapshot               │
│                                     │
│  Link expiry                        │
│  [1 hour ▾]                         │
│    Options: 1h / 24h / 7 days / Never  │
│                                     │
│  [  Generate link  ]                │
│                                     │
│  (after generation:)                │
│  https://codevv.local/g/xK9mP2...   │
│  [Copy link]  ✓ Copied!             │
└─────────────────────────────────────┘
```

The generated link is displayed in a read-only input field that selects all text on focus. "Copy link" copies to clipboard and shows a checkmark + "Copied!" for 2 seconds.

### Guest Landing Experience

The guest navigates to the link (e.g., `https://codevv.local/g/xK9mP2`). No login required.

**What they see:**

A stripped-down view with:
- **Top bar** (32px): CodeVV logo on the left, "Shared by [display name] · [project name]" in the center, "Sign in to collaborate →" ghost button on the right
- **Content area**: the shared canvas/spec/dashboard in read-only mode, full screen below the top bar
- **No dock bar, no sidebar, no panel controls** — pure read-only viewer
- Canvas is navigable (pan/zoom) but not editable
- Spec is scrollable but not approvable
- No cursor presence for guests (they're invisible to the team)

### Expired Link Screen

If the link has expired, the guest sees a centered message on the base background:

```
        🔒  (Lucide Lock icon, 48px, --color-text-tertiary)

   This link has expired

   The person who shared this link can generate a new one.
   
   [Sign in to CodeVV]  (ghost button — only useful if they have an account)
```

No background animation, no branding beyond the CodeVV wordmark in the corner.

### Link Management Panel

Admins access link management at: **Settings → Sharing**

A table showing all active and recently-expired links:

| Link | Type | Created | Expires | Views | Actions |
|------|------|---------|---------|-------|---------|
| Canvas — Sprint 3 board | Canvas | Today 2:14pm | In 6 hours | 4 | [Copy] [Revoke] |
| Spec — Auth redesign | Spec | Yesterday | Expired | 12 | [Delete] |

Columns: link label (auto-generated from the shared item's name), type badge, created timestamp, expiry (relative time while active, "Expired" after), view count, actions.

**Revoke** immediately invalidates the link — any open guest sessions see the expired link screen within 30 seconds (controlled by a polling interval on the guest page).

---

## 34. Inline AI Editing (Cmd+K) UX

### Trigger & Visual Appearance

`Cmd+K` (or `Ctrl+K` on Linux/Windows) opens the inline prompt **only when CodeMirror has focus**. If CodeMirror does not have focus, the keystroke falls through to the global `Cmd+Shift+K` command palette.

**When triggered without a selection:** A floating inline prompt bar appears centered below the cursor line.

**When triggered with a selection:** The selection is highlighted in a soft `--color-accent-dim` background, and the prompt bar appears centered above the selection.

**Prompt bar layout:**

```
┌──────────────────────────────────────────────────────┐
│ ✦  Edit with AI...                          [↑↓ History] │
└──────────────────────────────────────────────────────┘
```

- Width: 520px max, min 320px, centered horizontally over the selection
- Background: `--color-surface-4`, `--shadow-3`, `--radius-sm`
- Left icon: `Sparkles` (Lucide, 14px, `--color-accent`) — indicates AI context
- Right icon: up/down arrows for prompt history, visible on hover
- Input: auto-focused, single-line, expands to max 3 lines on overflow
- Pressing Enter submits; Shift+Enter adds a newline; Esc dismisses

### Diff Rendering

After Claude responds, the inline prompt bar is replaced by the diff view directly in the CodeMirror editor:

- **Removed lines** (`-`): red background (`#ED474A15`), red gutter marker, text in `--color-text-secondary` with strikethrough
- **Added lines** (`+`): green background (`#4DA86215`), green gutter marker, text in `--color-text-primary`
- **Unchanged context lines**: shown at normal opacity (±3 lines of context around each change)
- Gutter markers: `-` in `--color-error`, `+` in `--color-success`, both at 10px

The diff is applied in-place — the existing code shows the before/after simultaneously. The editor is read-only while the diff is active (the user cannot type until they accept or reject).

### Accept / Reject / Regenerate Action Bar

A small action bar appears floating below the last line of the diff (not in the gutter — it floats 8px below the diff region):

```
  [Tab Accept]   [Esc Reject]   [⌘↵ Regenerate]
```

- Three buttons in a row, compact (height 26px, `--radius-sm`)
- **Accept** — primary (accent fill): applies the diff, removes markup, restores editor focus. Keyboard: `Tab`
- **Reject** — ghost: discards the diff, restores original code, closes the inline UI. Keyboard: `Esc`
- **Regenerate** — ghost: re-submits the prompt (optionally with the same or modified prompt visible). Keyboard: `Cmd+Enter`

After accepting, the newly accepted lines briefly flash with a green highlight (`--color-success-muted`, 400ms fade-out) to confirm success.

### Prompt History Navigation

When the prompt bar is open and the input field is empty, pressing `↑` cycles through recent inline prompts (last 20, stored in localStorage). Pressing `↓` moves forward through history. The history is per-user and persists across sessions.

History items display in a dropdown list below the prompt bar (max 6 visible, scrollable):

```
  Recent prompts:
  • Add null checks for all parameters
  • Refactor this to use async/await
  • Add JSDoc comments
  • Extract this into a helper function
```

Clicking any history item populates the input field. History is per-file (not global) — it shows only prompts used in the current file.

---

## 35. Live Preview Panel

### Panel Header Controls

The live preview panel header (36px, `--color-surface-2`) contains:

**Left side:**
- URL bar: a read-only input showing the current preview URL (e.g., `http://localhost:5173`). Clicking selects the URL for copying. Shows a loading spinner inside on the left when the page is loading.

**Right side (icon buttons, 16px icons, 28px hit targets):**
- `RefreshCw` — hard refresh the iframe
- `Monitor` dropdown — viewport selector (see below)
- `ExternalLink` — open the preview URL in a real browser tab
- `Settings2` — configure preview (port override, path)

**Viewport Selector Dropdown:**

Clicking the `Monitor` icon opens a small dropdown (not a modal — a popover, `--color-surface-5`, `--shadow-3`, `--radius-md`):

```
  ✓ Desktop  (1280×800)
    Tablet   (768×1024)
    Mobile   (390×844)
    Custom…
```

Selecting a viewport resizes the iframe container (not the window) to the chosen dimensions. The iframe is centered in the panel with a dark grey matte around it when not at full width. The matte background is `--color-base`. A faint device-frame outline at `--color-border-subtle` wraps the iframe when at a preset viewport size (not at Desktop full-width).

### Error Overlay

When the dev server returns a compilation error (detected via the Vite error overlay protocol or via the error page returned in the iframe):

A semi-transparent overlay appears over the preview iframe:
- Background: `rgba(10, 8, 11, 0.88)`, full iframe coverage
- Centered content: `AlertTriangle` icon (24px, `--color-error`), error title in `--text-lg --color-error`, error message in `--font-mono --text-sm --color-text-secondary`
- Full error stack trace below in a scrollable monospace block (`--color-surface-2` background, `--radius-sm`, max height 200px)
- The overlay does not obscure the panel header — the user can still navigate away or refresh

### Port Detection Failure State

When the backend cannot detect an active dev server (no response on known ports):

The iframe is replaced by a centered empty state:

```
          [Monitor icon, 48px, --color-text-tertiary]

      No dev server detected

      CodeVV is looking for a server on ports
      3000, 4000, 5173, 8080, 8000.

      [Configure manually]    [Scan again]
```

"Configure manually" opens a small inline form to enter a port number. "Scan again" retries port detection immediately.

If a dev server starts while this state is showing, auto-detection fires (polled every 5 seconds while the panel is visible) and the panel transitions to the preview without user action.

---

## 36. Dependency Vulnerability Scanner Results Panel

### Visual Design

The vulnerability scanner opens as a dockview panel titled "Security: [project name]". It has three sections: summary bar, filter bar, results table.

**Summary bar** (top of panel, 40px):
```
  🔴 2 CRITICAL   🟠 5 HIGH   🟡 3 MEDIUM   ⚪ 8 LOW    [Scan now]  [18 packages]
```
Color-coded pill badges (`--radius-xs`, `--text-xs`, `--font-weight-semibold`). "Scan now" triggers a manual scan. "18 packages" shows total packages scanned.

**Filter bar** (below summary, 32px):
```
  [All ▾]  [npm ▾]  [Search packages…]                    [Last scanned: 2 min ago]
```

**Results table** — each row:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CRITICAL  │  lodash  4.17.15 → 4.17.21  │  CVE-2021-23337  │  [Fix ▾]     │
│ HIGH      │  axios   0.21.1  → 0.27.0   │  CVE-2022-1214   │  [Fix ▾]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Severity badge**: `--radius-xs`, bold monospace text, color-coded background (CRITICAL: `--color-severity-critical`/20% bg, HIGH: `--color-severity-high`/20% bg, etc.)
- **Package name + versions**: current version in `--color-error`, arrow `→`, safe version in `--color-success`
- **CVE ID**: a link to the NVD database (opens in new tab); `--color-info` underlined text
- **Fix dropdown**: "Fix ▾" ghost button opens a small menu:
  - "Run `npm update lodash`" (one-click, runs in terminal)
  - "Pin to safe version in package.json"
  - "Ask Claude about this vulnerability"
  - "Dismiss (accept risk)"

Row height: 36px. Alternating row background: odd rows `--color-surface-1`, even rows `--color-surface-2`. CRITICAL rows have a 3px left border in `--color-severity-critical`.

### "Claude Suggests Fix" Interaction

For CRITICAL and HIGH severity items, a `Sparkles` icon (14px, `--color-accent`) appears next to the Fix button — clicking it opens the AI chat panel with a pre-populated context:

> *"I have a CRITICAL vulnerability in `lodash` 4.17.15 (CVE-2021-23337). Suggest a safe update and explain if it has breaking changes for my codebase."*

Claude receives the full `package.json` and the specific files importing that package as context.

This is **not inline** in the results panel — it opens the chat. The results panel stays visible alongside chat in dockview.

### Auto-Created Task Notification

When a CRITICAL or HIGH vulnerability is detected:
- A task is auto-created in the task board: "Fix CRITICAL: [package] [CVE-ID]" assigned to the project, unassigned to a person
- A toast notification appears: "2 critical vulnerabilities found — tasks created" with a "View tasks" action
- The dock bar's task icon shows a badge with the count increase

---

## 37. Spec Gate UI (Brainstorm → Approve → Build Flow)

### "Ready to Spec" Gesture

The explicit trigger is a button that appears in the **Brainstorm workspace toolbar** (the persistent toolbar above the canvas):

```
  [New session]  [Templates ▾]  [AI: On]  ...  [Generate Spec ✦]
```

The "Generate Spec" button (accent fill, `Sparkles` icon on the left, `--text-sm`) becomes active after at least one canvas object exists AND at least 3 AI chat messages have been exchanged. Before this threshold, it's visible but disabled with tooltip "Keep brainstorming — Claude will generate a spec when there's enough context."

No hidden trigger, no ambient detection of "ready to spec." The driver explicitly clicks this button.

### Spec Review Screen

Clicking "Generate Spec" opens a **full-screen overlay** (not a modal — it covers the workspace):

**Layout — two panels side by side:**

```
┌─────────────────────────────┬──────────────────────────────────┐
│  SPEC PREVIEW               │  CANVAS (read-only reference)    │
│                             │                                  │
│  [spec content here]        │  [the brainstorm canvas,         │
│  scrollable                 │   zoomed out, non-interactive]   │
│                             │                                  │
│                             │                                  │
├─────────────────────────────┴──────────────────────────────────┤
│  [Edit spec]  [Reject ✕]                    [Approve & Build ✓]│
└────────────────────────────────────────────────────────────────┘
```

- Left panel (60% width): The Claude-generated spec, rendered as formatted markdown (headers, lists, code blocks). Scrollable. A small "Edit" pencil icon in the top-right corner enables raw markdown editing in the same panel.
- Right panel (40% width): The canvas zoomed to fit, read-only. Serves as context while reviewing the spec.
- Bottom bar: `Edit spec` (ghost), `Reject` (ghost, `--color-error` text), `Approve & Build` (accent fill, prominent). Approval timestamp and approver identity are recorded in Recall automatically when "Approve & Build" is clicked.

"Edit spec" focuses the left panel into edit mode — the markdown becomes a textarea. Saving re-renders the preview.

### Spec State Machine

Each spec has a state displayed as a pill badge in the spec's header and wherever it's referenced:

| State | Badge color | Meaning |
|-------|-------------|---------|
| **Draft** | `--color-text-tertiary` bg | Being generated by Claude; user hasn't opened review |
| **Under Review** | `--color-info` | Spec review screen is open |
| **Approved** | `--color-success` | Driver approved — build is authorized |
| **In Revision** | `--color-warning` | Rejected; canvas annotation visible; awaiting rework |
| **Building** | `--color-accent` (pulsing) | BrickLayer build in progress |
| **Built** | `--color-success` muted | Build complete |

State transitions are strict: `Draft → Under Review → Approved → Building → Built`, or `Under Review → In Revision → Under Review`.

### Rejected Spec → Canvas Annotation

When the driver clicks "Reject", a **rejection reason field** appears (a simple text area, replacing the bottom bar):

```
  Why is this spec being rejected? (optional — will appear on canvas)
  ┌──────────────────────────────────────────────────────────────┐
  │  The auth flow section is incomplete. Missing OAuth section. │
  └──────────────────────────────────────────────────────────────┘
  [Cancel]                               [Reject with note ✕]
```

On confirm:
- The full-screen overlay closes
- A sticky note is placed on the canvas at the top-left empty area (or near the most relevant existing nodes if Claude can determine relevance)
- Sticky note style: red background (`#3A1212`), white text, header "Spec rejected" in `--color-error`, body shows the rejection reason and timestamp
- The spec state changes to "In Revision" (badge visible on canvas sticky note)

### Multiple Pending Specs

When more than one spec awaits approval:

A **Spec Queue** panel (accessible from the dock, icon: `ListChecks`) shows all pending specs as cards:

```
  PENDING APPROVAL (2)
  ───────────────────────────────
  ● Auth redesign spec       [Review]
    Generated 10 min ago
  
  ● Mobile layout spec       [Review]
    Generated 2 hours ago    Under Review →
```

The queue is FIFO by default but can be manually reordered by the admin. Only one spec can be "Under Review" (spec review screen open) at a time — clicking "Review" on a second spec while the screen is open asks "Close current review and open this one?"

There is no limit on how many specs can be in Draft or In Revision simultaneously.

---

## 38. Knowledge Graph Empty / First-Run State

### What a New User Sees on First Open

On a brand-new project with an empty Recall (no brainstorm sessions, no ingested docs, no conversations), the Knowledge Graph panel opens to a seeded **three-node starter graph** — not a blank canvas:

```
    ┌──────────────┐
    │  [Project]   │  ← Project name node (always present)
    │  CodeVV OS   │
    └──────┬───────┘
           │
    ┌──────┴───────┐
    │  [You]       │  ← Current user node (always present)
    │  Tim         │
    └──────────────┘
```

Plus a floating prompt node (no border, light text, dashed outline):

```
    ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
    │  Start a brainstorm session to populate       │
    │  your knowledge graph.                        │
    │                                               │
    │  Or [Seed from codebase →]                    │
    └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

All other team members also appear as user nodes connected to the project node, if they exist. On a fresh single-user project: Project + one user + the floating prompt.

The graph visualization library shows these three nodes with gentle physics (they drift slightly and settle — the graph is "alive" but stable). No jarring animation; the nodes ease in on mount.

### "Seed from Codebase" Action UX

The "Seed from codebase" button (inside the floating prompt node, or in the panel toolbar as `Database` icon + "Seed from codebase") triggers Recall ingestion of the connected git repository.

**During ingestion:**
- The floating prompt node is replaced by a progress node:
  ```
  Analyzing codebase…
  ████████░░░░  412 / 680 files
  ```
- New nodes appear on the graph in real-time as they're ingested — files, modules, detected imports, commit authors. The graph grows visually as processing happens.
- A toast at the bottom: "Seeding knowledge graph from codebase — this takes 1-3 minutes."

**After completion:**
- A brief success state: the project node pulses with `--color-success` for 1 second
- A toast: "Knowledge graph seeded. 680 files, 24 modules, 8 decision patterns detected."
- The graph auto-fits to show all nodes

### Node Interaction Model

**Single click on any node:** Opens a small **preview tooltip** anchored to the node (not a popover floating independently — it's tethered with an arrow):

```
┌──────────────────────────────────────┐
│  📄 auth/jwt.py                      │
│  Last modified: 2h ago               │
│  12 imports · 3 contributors         │
│  "JWT token validation, Expiry..."   │
│  ───────────────────────────────     │
│  [Open]  [Find related]              │
└──────────────────────────────────────┘
```

Clicking elsewhere dismisses the tooltip. Clicking "Open" opens the related item (file in editor, task in task board, canvas in canvas panel, etc.) in a new dockview panel.

**Double click on a node:** Opens the related item directly (same as "Open" in the tooltip, skips the preview).

**Right-click (or long-press on mobile):** Opens a context menu anchored to the node:

```
  Open in panel
  Open in new panel (side by side)
  ─────────────────
  Find all related
  Show path to [Project]
  ─────────────────
  Add note
  Copy link to node
  ─────────────────
  Hide node (filter out this type)
  Pin to top
```

**Edge interaction:** Clicking an edge (the line between two nodes) shows a tooltip explaining the relationship type: "imports", "created by", "referenced in", "led to decision", etc.

**Graph controls (top-right of panel):**
- Zoom in/out buttons
- "Fit to screen" (keyboard: `F`)
- Layout selector: Force / Hierarchical / Radial (small dropdown)
- Filter chips: show/hide node types (Files, People, Decisions, Tasks, Canvas, Conversations)

---

*Spec updated: 2026-04-02. Sections 29–38 added by uiux-master agent filling design gaps identified in design-reviewer audit.*

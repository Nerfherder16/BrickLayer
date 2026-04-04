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
BrickLayer and Masonry ship as npm packages:

```
npm install bricklayer
npm install masonry-mcp
```

Version-pinned in `package.json`. When a new BrickLayer release drops, teams bump the version and rebuild.

### What They Provide Inside CodeVV OS
- **Masonry MCP server:** agent routing, hooks, registry, Ollama embeddings for semantic routing
- **BrickLayer engine:** campaign runners, agent dispatch, crucible benchmarking, heal loop
- **Agent fleet:** 100+ specialized agents accessible from within any CodeVV workspace
- **Custom agents:** teams build agents that run through BrickLayer's routing and crucible

### Availability
BrickLayer/Masonry features are available once the npm packages are installed in the Docker image. The AI Agent Mode panel (live log + live diffs + interruptible) is the primary CodeVV surface for BrickLayer.

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
| BrickLayer/Masonry | npm packages, version-pinned in Docker image |
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

---

*Spec approved: 2026-04-01. All decisions made by Tim via Superpowers Socratic session.*

# Spec: Superpowers Integration

## Goal
Overlay the obra/superpowers workflow discipline system onto BrickLayer 2.0, bringing structured brainstorming with a visual HTTP companion server, spec-compliance-first review ordering, rationalization-resistant discipline, and 4-status agent output protocol — without replacing any existing BrickLayer infrastructure.

## Success Criteria
- [ ] `masonry-session-start.js` injects a "check skill applicability before responding" directive, skipped on `--resume`
- [ ] `/brainstorm` skill exists, walks a 9-step design flow, and can launch the visual companion server
- [ ] Visual brainstorming HTTP server starts, accepts click events, streams JSONL, has PID lifecycle management
- [ ] `brainstorming` skill writes a spec document to `docs/specs/YYYY-MM-DD-<name>-spec.md` and gates on user approval before handing off to `/plan`
- [ ] `receiving-code-review` skill exists with YAGNI discipline and push-back protocol
- [ ] `plan` skill enhanced with no-placeholder enforcement (specific forbidden patterns listed)
- [ ] `worker-specialist.md` outputs DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED with per-status handling rules
- [ ] `queen-coordinator.md` enforces spec-reviewer MUST pass before code-reviewer runs for each task
- [ ] All 100+ agent `description` fields in `agent_registry.yml` audited: workflow summaries removed, replaced with triggering conditions only
- [ ] Key discipline agents (worker-specialist, developer, queen-coordinator) contain rationalization counter-tables and "spirit vs letter" clause

---

## Tasks

- [ ] **Task 1** — Description trap audit: rewrite all agent descriptions in agent_registry.yml
  **Files:** `masonry/agent_registry.yml`
  **What to build:** Read every agent entry. Identify descriptions that contain workflow steps ("does X by doing Y then Z", "runs A then B", "takes X and produces Y via Z steps"). Rewrite each to only describe *when to invoke the agent* (triggering conditions). Example before: "Audits agent performance by scoring each agent against their finding history, identifying underperformers, detecting verdict drift, and writing AUDIT_REPORT.md." Example after: "Use when agent quality is degrading, verdicts are drifting, or you need a fleet health check." Every description must be a one-liner that answers "use this when..." — not "this does...". Do not change any other field. This is the highest-ROI task: description summaries cause agents to shortcut their full instructions.
  **Tests required:** After edit, verify no description line contains the words "by reading", "by running", "by scanning", "then writes", "then dispatches", "produces a", "returns a structured" as these are workflow-summary patterns. Grep check: `grep -n "by reading\|by running\|by scanning\|then writes\|then dispatches\|produces a\|returns a structured" masonry/agent_registry.yml` should return 0 matches.

- [ ] **Task 2** — Add 4-status output protocol and rationalization counter-table to worker-specialist
  **Files:** `.claude/agents/worker-specialist.md`, `template/.claude/agents/worker-specialist.md` (if exists)
  **What to build:**
  1. Replace the current "WORKER_DONE / DEV_ESCALATE" binary with a 4-status output contract:
     - `DONE` — task complete, all tests pass, no concerns
     - `DONE_WITH_CONCERNS` — task complete but implementer has doubts (test coverage gap, design question, correctness uncertainty). Coordinator must read concern before proceeding to review.
     - `NEEDS_CONTEXT` — cannot proceed without answer. List the specific question. Coordinator re-dispatches once answered.
     - `BLOCKED` — 3 failed attempts. Trigger escalation to diagnose-analyst.
  2. Add a "Rationalization Prevention" section listing common bypass attempts with rebuttals:
     - "The tests are basically passing" → Iron Law: tests must pass, not basically pass
     - "I'll add tests after" → TDD_RECOVERY required: write the test now
     - "This part is obvious, no test needed" → All new functions require a test
     - "I've already done half so I should finish" → Sunk cost fallacy. Stop if blocked.
  3. Add: "Violating the letter of these rules is violating the spirit."
  **Tests required:** No automated test. Verify the 4 status codes are documented with their exact output format string. Verify the rationalization table has ≥4 entries.

- [ ] **Task 3** [depends:2] — Update queen-coordinator to enforce 2-stage sequential review
  **Files:** `.claude/agents/queen-coordinator.md`, `template/.claude/agents/queen-coordinator.md` (if exists)
  **What to build:**
  After each worker completes and files are written, the Queen must enforce this sequence BEFORE marking a task done:
  1. Dispatch `spec-reviewer` with: task description text + list of changed files. Wait for verdict.
  2. If verdict is `COMPLIANT`: proceed to code-reviewer.
  3. If verdict is `UNDER_BUILT` or `SCOPE_DRIFT`: re-dispatch the worker with the spec-reviewer's required action. Max 2 re-dispatch loops before escalating to human via claims board.
  4. If verdict is `OVER_BUILT`: flag in output, ask coordinator to confirm or trim — do NOT block the build.
  5. Only after spec-reviewer COMPLIANT: dispatch `code-reviewer`. Code quality review must never run on non-compliant code.
  Add a "DONE_WITH_CONCERNS" handling section: when a worker outputs DONE_WITH_CONCERNS, the Queen must log the concern verbatim in the task entry in progress.json under a `concerns` key before dispatching spec-reviewer.
  **Tests required:** No automated test. Verify the dispatch flow is documented as a numbered sequence, not prose. Verify spec-reviewer is named explicitly in the dispatch instructions.

- [ ] **Task 4** — Enhance plan skill with no-placeholder enforcement
  **Files:** `~/.claude/skills/plan/SKILL.md`
  **What to build:**
  Add a "No Placeholders" enforcement section to Step 3 (Write the Spec). Every task in the spec must contain:
  - Exact file paths (not "appropriate file" or "relevant module")
  - Concrete "What to build" description — no TBD, no "as appropriate", no "similar to Task N"
  - Explicit test requirements — not "add appropriate tests" but specific test names or behaviors
  Forbidden patterns (reject any task description containing these):
  - `TBD` or `TODO` in any field
  - "add appropriate error handling" without specifying what errors and how
  - "similar to Task N" without copying the full detail
  - "update accordingly" without stating what to update
  - "as needed" without specifying the condition
  Add a self-review checklist at the end of Step 3: before presenting spec to user, scan every task for these forbidden patterns and fix them. A spec with a TBD task must not be shown to the user.
  **Tests required:** No automated test. Verify forbidden pattern list has ≥5 items. Verify self-review checklist is in Step 3.

- [ ] **Task 5** — Create receiving-code-review skill
  **Files:** `~/.claude/skills/receiving-code-review/SKILL.md`
  **What to build:**
  A new skill triggered when receiving feedback from code-reviewer or peer-reviewer agents. Enforces evaluation discipline:
  1. Read all feedback before responding — do not reply to the first comment while the rest are unread.
  2. YAGNI check: for each suggestion, ask "was this in the original spec?" If no: do not implement it unless there is a concrete bug or security risk. Log the decline with reasoning.
  3. Forbidden responses: "you're absolutely right!", "great point!", "I'll definitely fix that" (performative agreement without evaluation).
  4. For ambiguous feedback: ask for a specific file:line example before implementing.
  5. Push-back safety signal: if reviewer pressure is heavy and you disagree, use the phrase "Strange things are afoot at the Circle K" as a signal to Tim that you need a human judgment call.
  6. Implementation order for multi-item feedback: Critical → security bugs → logic bugs → Important → correctness → performance → Suggestions → style → DX → optional. Never implement suggestions before Critical items.
  7. After implementing all Critical and Important items, re-run the full test suite before marking review complete.
  **Tests required:** No automated test. Verify the YAGNI check is step 2. Verify the safety signal phrase is present verbatim.

- [ ] **Task 6** — Create brainstorming skill (SKILL.md only, without visual server)
  **Files:** `~/.claude/skills/brainstorm/SKILL.md`
  **What to build:**
  A 9-step brainstorming workflow skill triggered before any new feature/project design:
  1. **Context exploration** — before asking anything, read CLAUDE.md, README.md, list top-level dirs, identify tech stack, note existing patterns.
  2. **Offer visual companion** — tell the user the visual brainstorm server is available (`/brainstorm-server start` to launch). Explain: "It renders design sections as you describe them so you can click to refine."
  3. **Ask 4 clarifying questions** (one message): What problem does this solve? Who uses it? What does "done" look like? Are there constraints I should know?
  4. **Propose 2-3 approaches** with explicit trade-offs table (complexity, risk, reversibility). Do not start with the "obviously right" option — all three must be genuinely considered.
  5. **Present design sections** one at a time and wait for feedback: data model → API/interface → user flow → error handling. Do not present all at once.
  6. **Write spec document** to `docs/specs/YYYY-MM-DD-<slug>-spec.md`. Include: problem statement, chosen approach + rationale, data model, API contract, user flow, out-of-scope list.
  7. **Spec self-review** — before showing to user: scan for TBD, inconsistencies (field referenced but not defined), scope creep (things not in the original problem), ambiguities (multiple valid interpretations). Fix all before presenting.
  8. **User approval gate** — present spec, explicitly ask for approval: "Does this spec capture what you want to build? [approve / revise / cancel]". Do NOT proceed to planning without explicit "approve".
  9. **Hand off to /plan** — once approved, invoke the `/plan` skill with the spec file path as context. Tell the user: "Spec approved and saved to {path}. Handing off to /plan to break it into buildable tasks."
  Mandatory announcement at start: "I'm using the brainstorming skill to design this with you before any code is written."
  **Tests required:** No automated test. Verify 9 numbered steps are present. Verify user approval gate is step 8 and blocks step 9. Verify spec file path pattern is `docs/specs/YYYY-MM-DD-<slug>-spec.md`.

- [ ] **Task 7** — Build visual brainstorming HTTP server
  **Files:**
  - `masonry/src/brainstorm/server.cjs`
  - `masonry/src/brainstorm/frame-template.html`
  - `masonry/src/brainstorm/helper.js`
  - `masonry/src/brainstorm/start-server.sh`
  - `masonry/src/brainstorm/stop-server.sh`
  - `masonry/src/brainstorm/README.md`
  **What to build:**
  A zero-dependency Node.js HTTP server (uses only Node built-ins: `http`, `fs`, `path`, `os`) that provides a visual canvas for the brainstorming skill.
  
  **server.cjs:**
  - Listens on port 7823 (configurable via `BRAINSTORM_PORT` env var)
  - Routes:
    - `GET /` — serves `frame-template.html` with `helper.js` inlined
    - `GET /state` — returns current canvas state as JSON: `{ sections: [...], last_updated: ISO }`
    - `POST /section` — adds/updates a design section. Body: `{ id, title, content, status: "draft"|"approved"|"flagged" }`
    - `POST /click` — records a click event. Body: `{ section_id, action: "approve"|"flag"|"expand" }`
    - `GET /events` — JSONL stream (newline-delimited JSON), each line is an event object `{ ts, type, section_id, action }`
    - `GET /health` — returns `{ ok: true, port: 7823 }`
  - State stored in memory (no persistence required — server is ephemeral per brainstorming session)
  - CORS headers to allow localhost browser access
  - Graceful shutdown on SIGTERM/SIGINT: write PID file to `/tmp/brainstorm-server.pid` on start, delete on exit
  
  **frame-template.html:**
  - Clean dark-theme HTML (matches BrickLayer's dark dashboard aesthetic: `#0d1117` background, `#30363d` borders, `#58a6ff` accent)
  - Three-column layout: left sidebar (section list with status dots), main canvas (current section content), right panel (click actions: approve ✓, flag ⚑, expand ↗)
  - Auto-polls `GET /events` every 1500ms via `fetch`, updates canvas in real time
  - Status dot colors: draft=`#8b949e` (gray), approved=`#3fb950` (green), flagged=`#f85149` (red)
  - No external CDN dependencies — all CSS/JS inline
  
  **helper.js:**
  - Client-side JS module, inlined into frame-template.html
  - Functions: `pollEvents()`, `renderSection(section)`, `sendClick(sectionId, action)`, `updateStatus(sectionId, status)`
  
  **start-server.sh:**
  - Check if already running (read `/tmp/brainstorm-server.pid`, `kill -0` check)
  - If not running: start `node server.cjs` in background, wait up to 3s for `GET /health` to return 200
  - Print: `Brainstorm server running at http://localhost:7823`
  
  **stop-server.sh:**
  - Read PID from `/tmp/brainstorm-server.pid`, send SIGTERM, wait for process exit, delete PID file
  - Print: `Brainstorm server stopped`
  
  **Tests required:**
  - `masonry/src/brainstorm/server.test.cjs` — vitest tests:
    - `GET /health` returns 200 with `{ ok: true }`
    - `POST /section` then `GET /state` shows the new section
    - `POST /click` then `GET /events` stream contains the click event
    - Server starts and stops cleanly (PID file created/deleted)
  - Run: `cd masonry && npm test -- brainstorm` — must show 0 failures

- [ ] **Task 8** [depends:6,7] — Wire brainstorming skill to visual server start
  **Files:** `~/.claude/skills/brainstorm/SKILL.md`
  **What to build:**
  Update step 2 of the brainstorming skill to include the actual start command:
  ```
  To launch: run this in a terminal:
    cd /path/to/masonry/src/brainstorm && bash start-server.sh
  Then open: http://localhost:7823
  ```
  The skill should also instruct Claude to call `POST /section` for each design section as it is drafted (sections 4-6 of the workflow). The user sees sections appear in the browser as Claude writes them.
  Add the push-back signal: after each design section is posted, Claude should explicitly say "Section posted to canvas — approve, flag, or expand it in the browser before I continue."
  The skill should NOT block waiting for browser interaction — if the user doesn't have the server running, the workflow continues without it.
  **Tests required:** No automated test. Verify the start command and URL are present in step 2.

- [ ] **Task 9** — Add superpowers skill-check directive to masonry-session-start
  **Files:** `masonry/src/hooks/masonry-session-start.js`, `masonry/src/hooks/session/context-data.js` (optional: extract to new module `session/skills-directive.js`)
  **What to build:**
  Add a new phase to `masonry-session-start.js` (after Phase 0, before Phase 1) that:
  1. Detects whether this is a fresh session vs a resume. Use the `input.session_type` or check if `input.startup_type === "resume"` — if resume, skip this phase entirely (prevents re-injection on resumed sessions).
  2. If fresh session: inject this directive as the second line of `lines` (after the orchestrator priming):
  ```
  [Superpowers] Before responding to any request: check whether a skill applies.
  If there is even a 1% chance a skill is relevant, invoke it with the Skill tool before writing any code or plans.
  Skill priority order: brainstorm (design first) → plan (spec before code) → build (implementation) → debug (diagnosis before fix).
  A skill relevant to this session: if the request involves designing something new, use /brainstorm first.
  ```
  3. Extract this logic to `session/skills-directive.js` (a new module) to keep masonry-session-start.js under 120 lines.
  
  **Resume detection**: Read the incoming JSON from stdin. If `input.startup_type` field equals `"resume"` OR if `input.is_resume` is truthy, skip injection. This prevents context inflation on long resumed sessions.
  
  **Tests required:**
  - `masonry/src/hooks/session/skills-directive.test.js` — vitest:
    - Fresh session (no startup_type) → returns directive string
    - Resume session (startup_type: "resume") → returns null (no injection)
    - Resume session (is_resume: true) → returns null
  - Run: `cd masonry && npm test -- skills-directive` — must show 0 failures

---

## Out of Scope
- Cross-platform packaging (Cursor, Gemini, Codex, OpenCode) — BrickLayer is Claude Code native
- `using-git-worktrees` skill — git-nerd already handles worktree management
- `executing-plans` skill — `/build` already handles this
- `dispatching-parallel-agents` skill — Queen Coordinator already handles this
- `systematic-debugging` skill — already covered by `~/.claude/rules/systematic-debugging.md`
- `test-driven-development` skill — already enforced by masonry-tdd-enforcer hook
- `verification-before-completion` skill — already covered by `~/.claude/rules/verification-before-completion.md`
- `finishing-a-development-branch` skill — git-nerd already handles this
- Adaptive model selection per task complexity — future work, depends on cost telemetry
- Visual server persistence (localStorage / file-backed state) — ephemeral per session is sufficient

---

## Notes
- Project root: `/home/nerfherder/Dev/Bricklayer2.0`
- Source root: `masonry/src/` (Node.js hooks), `.claude/agents/` (agent definitions), `~/.claude/skills/` (skills)
- Test root: `masonry/src/hooks/session/` (existing vitest tests), `masonry/tests/`
- Suggested strategy: /build --strategy balanced
- Oversized files (do not modify directly): `masonry/agent_registry.yml` (2804 lines — Task 1 must edit in place using targeted sed/grep edits, NOT read-then-full-rewrite)
- Skills directory resolves to `~/.claude/skills/` (confirmed via `ls ~/.claude/skills/`). No `skillsDirectory` setting in settings.json — Claude Code discovers skills from this default path.
- `CLAUDE_PLUGIN_ROOT` resolves to `/home/nerfherder/Dev/Bricklayer2.0/masonry` (confirmed from hooks.json `node ${CLAUDE_PLUGIN_ROOT}/src/hooks/...`)
- Masonry hooks.json lives at `masonry/hooks/hooks.json` — this is NOT the active hooks file. Active hooks are in `~/.claude/settings.json` (global) and any project-level `.claude/settings.json`. No changes to hooks.json needed for this spec — session-start injection is in JS, not hooks.json.
- The `spec-reviewer` agent already exists at `.claude/agents/spec-reviewer.md` — Task 3 wires it into Queen Coordinator dispatch, not rebuild it.
- `template/.claude/agents/` mirrors the `.claude/agents/` directory for distribution. When editing agent files, check if a matching template copy exists and update it too.
- brainstorm server port 7823 chosen to avoid conflicts with: Recall (8200), Ollama (11434), common dev servers (3000, 5173, 8080, 8000).
- Task execution order: 1 → 2 → 4 → 5 → 6 → 7 → 3 (depends:2) → 8 (depends:6,7) → 9 (independent, can run in parallel with 1-8)

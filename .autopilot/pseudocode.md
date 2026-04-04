# Pseudocode — Phase 6: Dev Execution Loop + Infrastructure + Agents + Skills + UI Quality
Generated: 2026-03-28T00:00:00Z
Source: .autopilot/spec.md

This document contains plain-English logic blueprints for each of the 23 build tasks.
Developer agents read this before writing code to reduce blind implementation and rework cycles.

---

## Task 1 — Upgrade fix-implementer: commit-before-verify+revert pattern

**Purpose:** Make every fix attempt auditable and prevent silent regression creep by committing before testing and reverting on failure.

**Flow:**
1. The agent receives a failing test or broken metric as its work order, along with the task description from the original spec.
2. Before writing any fix, the agent reads the relevant source files to understand the current state.
3. The agent applies a fix to the broken code.
4. Immediately after writing the fix, the agent commits with a message prefixed `experiment: fix attempt N` where N is the current attempt number starting at 1.
5. The agent runs the Guard check — the full test suite with `-q --tb=short` flags — and records whether it passes or fails.
6. If Guard fails, the agent runs `git revert HEAD --no-edit` to undo the commit, then moves to the next approach.
7. If Guard passes, the agent runs the Verify check — the task-specific test or metric — and records that result separately.
8. If Guard passes but Verify fails, the agent keeps the commit, logs "metric not improved" as a note, and escalates to the orchestrator rather than reverting.
9. If both Guard and Verify pass, the agent reports success and stops.
10. If three attempts have been made without a Guard+Verify pass, the agent marks the task BLOCKED and returns control to the orchestrator.

**Edge cases:**
- Attempt counter starts at 1 and increments after each revert; the cap is exactly 3 attempts before BLOCKED.
- If `git revert` itself fails (e.g., merge conflict from the revert), the agent must log the conflict and escalate immediately rather than retrying blind.
- If the Guard passes on attempt 1 but Verify fails, that counts as one attempt used; the agent retries with a new approach on attempt 2.

**Failure modes:**
- Git is not available in the working directory: log the error and escalate without attempting any fixes.
- Test runner unavailable: log the error and escalate; do not mark BLOCKED until the runner issue is resolved.

**Interfaces:**
- Reads: `~/.claude/agents/fix-implementer.md`, `template/.claude/agents/fix-implementer.md` (existing files — read before overwriting)
- Writes: same two files with the updated workflow documented
- The agent description must contain: `experiment:` prefix, Guard/Verify distinction, 3-attempt cap, revert-on-Guard-fail, keep-on-Verify-fail behavior

---

## Task 2 — Add Guard/Verify split to /build skill

**Purpose:** Split the validation step in the per-task build loop into two distinct checks so that regressions and missing goals are handled differently.

**Flow:**
1. Read the existing `~/.claude/skills/build/SKILL.md` to locate the Per-Task Loop and its current Step 4 (Validate).
2. Replace the single validation step with two sequential sub-steps labeled 4a-Guard and 4b-Verify.
3. Guard is defined as: run the full test suite with `-q --tb=short`; its job is to detect regressions introduced by this task's changes.
4. Verify is defined as: run the test file that was written specifically for this task; its job is to confirm the task's goal was achieved.
5. Document the distinct outcomes: Guard fails means spawn a fix agent before continuing; Guard passes but Verify fails means log a warning, do not spawn a fix agent, and continue to the next step.
6. Locate Step 6 (Commit) in the skill and update it: commits that achieve Guard+Verify both passing use `feat:` prefix; commits where Guard passed but Verify did not use `experiment:` prefix.
7. Write the updated file.

**Edge cases:**
- If no task-specific test file exists for Verify (e.g., the task was a config change), the Verify step is skipped and the task is treated as Guard-only.
- The Guard/Verify split applies only to the standard per-task loop; [mode:security], [mode:architect], [mode:review-only] tasks are exempt from Verify (document this explicitly).

**Failure modes:**
- The test runner exits with a non-zero code due to a setup error rather than a test failure: document that the orchestrator should distinguish runner errors from test failures before spawning a fix agent.

**Interfaces:**
- Reads: `~/.claude/skills/build/SKILL.md` (existing file — must read first)
- Writes: same file with Guard/Verify split added to Step 4 and commit message convention added to Step 6

---

## Task 3 — Create spec-reviewer agent

**Purpose:** Provide a read-only gate between the developer and code-reviewer that checks whether the implementation matches the spec task — no more, no less.

**Flow:**
1. Create the agent file content with YAML frontmatter (name, description, model: sonnet).
2. The agent's instructions describe it as read-only: it never modifies files, only reads them.
3. Document the four verdict values with precise definitions: COMPLIANT means implementation matches the spec task's scope exactly; OVER_BUILT means more was implemented than asked; UNDER_BUILT means less was implemented than asked; SCOPE_DRIFT means the implementation went in a different direction than the spec intended.
4. Document the required output block format: a markdown section headed `## Spec Review` containing three fields — Verdict, Evidence (specific file and line references), and Required action (what the developer should do if not COMPLIANT).
5. Write the file to `~/.claude/agents/spec-reviewer.md`.
6. Write the identical content to `template/.claude/agents/spec-reviewer.md`.
7. Add an entry to `masonry/agent_registry.yml` for spec-reviewer with tier: "draft", model: sonnet, modes: [build], capabilities: [spec-compliance, code-review].

**Edge cases:**
- If the spec task description is ambiguous, the agent should favor UNDER_BUILT over SCOPE_DRIFT and document the ambiguity in the Evidence field.
- If the developer changed files that are infrastructure (tests, configs) alongside the required files, those should not count against a COMPLIANT verdict.

**Failure modes:**
- Agent called without a task description: return UNDER_BUILT with evidence "No task description provided."
- Agent called without any changed files listed: return UNDER_BUILT with evidence "No files provided for review."

**Interfaces:**
- Reads: spec task description (passed as prompt context), list of files changed by the developer agent
- Writes: nothing (read-only agent)
- Registry: `masonry/agent_registry.yml` — add entry

---

## Task 4 — Wire spec-reviewer into /build skill [depends: Task 3]

**Purpose:** Insert the spec-reviewer gate into the /build pipeline after the developer and before the code-reviewer so scope violations are caught before review.

**Flow:**
1. Read the existing `~/.claude/skills/build/SKILL.md` to locate the section where the developer agent returns and the code-reviewer is spawned.
2. Insert a new step between them labeled "Step 4a — spec-reviewer gate."
3. Document that the orchestrator spawns spec-reviewer with two inputs: the original spec task description and the list of files changed by the developer.
4. If spec-reviewer returns COMPLIANT: proceed directly to code-reviewer with no interruption.
5. If spec-reviewer returns OVER_BUILT, UNDER_BUILT, or SCOPE_DRIFT: spawn the developer agent again with the spec-reviewer's Required action as additional instruction, allow one correction cycle, then proceed to code-reviewer regardless of the re-review outcome (do not loop more than once).
6. Document the skip conditions: tasks tagged [mode:security], [mode:architect], or [mode:review-only] bypass the spec-reviewer gate entirely.
7. Write the updated file.

**Edge cases:**
- If the spec-reviewer returns an unrecognized verdict, treat it as COMPLIANT and log a warning rather than blocking the pipeline.
- The correction cycle is capped at one: if the developer's second attempt still yields OVER_BUILT or similar, proceed to code-reviewer and note the persistent verdict in the build log.

**Failure modes:**
- spec-reviewer agent is unavailable: skip the gate, log a warning, and continue to code-reviewer.

**Interfaces:**
- Reads: `~/.claude/skills/build/SKILL.md` (existing file — must read first)
- Writes: same file with Step 4a inserted

---

## Task 5 — Create /debug skill as a loop

**Purpose:** Replace one-shot debugging with a structured 8-technique loop that exhausts systematic approaches before escalating.

**Flow:**
1. Create the skill file with YAML frontmatter (name: debug, description, invocation: `/debug <error description or file>`).
2. Document the loop structure: the agent works through 8 diagnostic techniques in order, stopping and reporting as soon as root cause is identified.
3. Document each technique with a one-paragraph description: (1) Binary search — narrow the failing scope by halving the problem space; (2) Differential — compare working and broken states to isolate the difference; (3) Minimal repro — strip away everything not needed to reproduce the failure; (4) Forward trace — follow execution from the entry point to where it diverges from expected; (5) Pattern search — look for similar failures in git log, test history, or codebase; (6) Backward trace — start from the observed symptom and walk backwards through call chains; (7) Rubber duck — narrate the problem aloud step by step to force explicit reasoning; (8) Hypothesis log — generate 3-5 hypotheses ranked by likelihood and test the top one.
4. Document the loop exit conditions: stop when root cause is identified with evidence, or when all 8 techniques have been exhausted without finding a root cause.
5. On exhaustion: the skill writes a `DIAGNOSIS_FAILED.md` file in the working directory, listing all 8 techniques and what each ruled out, then surfaces this to the user with a request for additional context.
6. Write to `~/.claude/skills/debug/SKILL.md`.

**Edge cases:**
- If the user provides a file path rather than an error description, the skill reads that file first to understand the failure before starting the loop.
- A technique is considered "complete" when the agent can state what it ruled in or ruled out, not just that it was attempted.

**Failure modes:**
- File path provided does not exist: report the missing file and ask the user to correct it before starting the loop.

**Interfaces:**
- Reads: error description or file path from invocation argument
- Writes: `~/.claude/skills/debug/SKILL.md` (new file), `DIAGNOSIS_FAILED.md` in working directory on exhaustion

---

## Task 6 — Create /aside skill

**Purpose:** Allow a user to ask a read-only question during an active /build without disrupting task state.

**Flow:**
1. Create the skill file with YAML frontmatter (name: aside, description, invocation: `/aside <question>`).
2. Document the pre-flight check: read `.autopilot/mode` to determine if a build is active.
3. If mode equals "build" and there is at least one task with status IN_PROGRESS: enter frozen mode. Write the current task's ID, description, and status to `.autopilot/aside-state.json` with a timestamp. Proceed to answer the question in read-only mode — no file writes, no git operations.
4. After answering, print the message: "Aside complete. Run /build to resume task N." where N is the task ID saved in aside-state.json.
5. Document that /build, on startup, checks for aside-state.json, clears it, and resumes from the task ID recorded there.
6. If mode is not "build" or no task is IN_PROGRESS: answer the question normally without saving any state.
7. Document the aside-state.json schema: fields are task_id, task_description, task_status, saved_at (ISO-8601 timestamp).
8. Write to `~/.claude/skills/aside/SKILL.md`.

**Edge cases:**
- If aside-state.json already exists when /aside is invoked, overwrite it with the current task state — a prior incomplete aside should not block a new one.
- If the question itself asks the agent to make a code change, the skill must decline and remind the user that aside is read-only.

**Failure modes:**
- `.autopilot/mode` file is not readable: treat as no active build and answer normally.

**Interfaces:**
- Reads: `.autopilot/mode`, `.autopilot/progress.json`
- Writes: `.autopilot/aside-state.json` (new file, only when build is active), `~/.claude/skills/aside/SKILL.md`

---

## Task 7 — Upgrade masonry-pre-compact.js: full build/campaign state save

**Purpose:** Extend the existing PreCompact hook to persist build state and campaign state as discrete snapshot files with stdout output, ensuring the user sees what was saved before compaction occurs.

**Flow:**
1. Read the existing `masonry/src/hooks/masonry-pre-compact.js` in full — the hook already handles autopilot build state, UI compose state, swarm inflight tasks, and campaign state using masonry-state.json. The upgrade adds snapshot files and build.log entries for the build case, and a dedicated campaign snapshot file.
2. In the autopilot build state block (where `autopilotMode` is "build" or "fix" and `progress` is loaded): after writing compact-state.json, additionally write `.autopilot/pre-compact-snapshot.json` containing the full progress.json contents plus a `snapshot_at` ISO-8601 timestamp.
3. Also append a line to `.autopilot/build.log` in the format: `[ISO-8601] PRE_COMPACT: Snapshot saved. Task N of M (STATUS). Resume with /build.` where N is the first non-DONE task's id and M is total task count.
4. In the campaign state block (where `masonry-state.json` exists and has a mode): write `masonry/pre-compact-campaign.json` containing current question id (from `campaign.q_current`), wave number, and a `snapshot_at` timestamp.
5. In both cases, add a distinct stdout line that the user will see before compaction: for build, print "PRE_COMPACT BUILD: snapshot saved to .autopilot/pre-compact-snapshot.json"; for campaign, print "PRE_COMPACT CAMPAIGN: snapshot saved to masonry/pre-compact-campaign.json".
6. The existing hookSpecificOutput JSON write to stdout already collects the `lines` array — append these new lines to that same array rather than writing a second JSON block.

**Edge cases:**
- `.autopilot/` directory may not exist if there is no active build: wrap the build.log append in a try-catch and skip silently.
- `masonry/` directory for the campaign snapshot: create it with `mkdirSync({ recursive: true })` before writing.
- If progress.json has no non-DONE tasks (build is complete but mode file not cleared): snapshot still saves; the log line should say "All tasks done."

**Failure modes:**
- File write fails due to permissions: catch the error, skip the snapshot file write, but still include the state summary in hookSpecificOutput so the user sees the state in the compacted context.

**Interfaces:**
- Reads: `masonry/src/hooks/masonry-pre-compact.js` (existing — must read first), `.autopilot/mode`, `.autopilot/progress.json`, `masonry-state.json`
- Writes: `.autopilot/pre-compact-snapshot.json` (new), `.autopilot/build.log` (append), `masonry/pre-compact-campaign.json` (new), same hook file

---

## Task 8 — Create masonry-config-protection.js hook

**Purpose:** Block accidental or automated writes to lint configuration files, preventing silent style-rule changes that invalidate existing code.

**Flow:**
1. Create the hook file at `masonry/src/hooks/masonry-config-protection.js` as a PreToolUse hook that reads its input from stdin as JSON.
2. Parse the input to extract the tool name (Write or Edit), the file path being written, and the full user message text.
3. Check the file path against the protected list: files matching `.eslintrc*`, `.prettierrc*`, `prettier.config.*`, `ruff.toml`; and files named `pyproject.toml` that contain the section header `[tool.ruff]` or `[tool.black]` in their current on-disk content.
4. If the file is not in the protected list, exit with code 0 to allow the write.
5. If the file is protected, check the user message for the override token `LINT_CONFIG_OVERRIDE`. If the token is present, exit with code 0 to allow.
6. If protected and no override token: write the block message to stdout as a JSON object with `decision: "block"` and `reason` containing the full message: "[masonry-config-protection] BLOCKED: Write to lint config requires explicit override. Add # LINT_CONFIG_OVERRIDE to your message to proceed." Exit with code 2.
7. Add the hook to `~/.claude/settings.json` in the PreToolUse section under Write and Edit events, with timeout: 3 and continueOnError: false, placed before masonry-approver.

**Edge cases:**
- The pyproject.toml check requires reading the existing file content to detect `[tool.ruff]` or `[tool.black]` sections. If the file does not yet exist on disk (new file creation), the section check is skipped and the write is blocked solely on the filename match.
- A file path that partially matches (e.g., `.eslintrc.bak`) should still be blocked because the glob `.eslintrc*` covers it.

**Failure modes:**
- stdin parsing fails: exit code 0 (allow) rather than blocking — a hook crash must never silently block legitimate writes.
- Reading pyproject.toml for section detection fails: treat as no protected section found and block only on filename match.

**Interfaces:**
- Reads: stdin (hook payload), existing pyproject.toml on disk (for section detection), `~/.claude/settings.json` (to add wiring)
- Writes: `masonry/src/hooks/masonry-config-protection.js` (new file), `~/.claude/settings.json` (add hook entry)

---

## Task 9 — Create masonry-block-no-verify.js hook

**Purpose:** Block git commands that bypass safety checks before they reach the approver hook, enforcing the principle that safety issues must be fixed, not circumvented.

**Flow:**
1. Create the hook file at `masonry/src/hooks/masonry-block-no-verify.js` as a PreToolUse Bash hook that reads its input from stdin as JSON.
2. Parse the input to extract the bash command string being executed.
3. Check if the command is a git command at all. If not, exit with code 0 immediately — this hook only concerns itself with git commands.
4. Check for `--no-verify` anywhere in the command: if found, block with the message "[masonry-block-no-verify] BLOCKED: --no-verify bypasses safety checks. Fix the underlying issue instead."
5. Check for `git push` combined with `--force` or `-f`: if the command is a git push and contains `--force` or `-f` (but not `--force-with-lease`), block with the message "[masonry-block-no-verify] BLOCKED: git push --force bypasses safety checks. Use --force-with-lease instead."
6. Allow `--force` and `-f` in non-push git commands (e.g., `git fetch --force` is acceptable).
7. Allow `--force-with-lease` in all contexts.
8. For all blocks: write a JSON object with `decision: "block"` and `reason` to stdout, then exit with code 2.
9. Add the hook to `~/.claude/settings.json` in the PreToolUse section under the Bash event, placed BEFORE masonry-approver in the hook ordering, with timeout: 3 and continueOnError: false.

**Edge cases:**
- Commands like `git push origin --force-with-lease` should pass through: the force-with-lease check must take priority over the `--force` check.
- Commands passed through shell wrappers (e.g., `bash -c "git push --force"`) should still be caught by string-matching the command text.
- `git push -f` is equivalent to `git push --force` and must be blocked.

**Failure modes:**
- stdin parsing fails: exit code 0 (allow) — never silently block.

**Interfaces:**
- Reads: stdin (hook payload), `~/.claude/settings.json` (to verify ordering)
- Writes: `masonry/src/hooks/masonry-block-no-verify.js` (new file), `~/.claude/settings.json` (add hook entry before masonry-approver in Bash PreToolUse)

---

## Task 10 — Extend masonry-context-monitor.js: semantic degradation detection

**Purpose:** Add a semantic-similarity check at Stop time that warns the user when the conversation has degraded in ways that file size alone cannot detect.

**Flow:**
1. Read the existing `masonry/src/hooks/masonry-context-monitor.js` in full. The current hook fires at Stop, checks transcript file size, blocks if over 750K tokens with uncommitted changes, and warns otherwise.
2. Add a new async function after the existing token-count logic that fetches embeddings from Ollama's nomic-embed-text model at the configured host.
3. Resolve the Ollama host from the environment variable `OLLAMA_HOST`, falling back to `http://100.70.195.84:11434`.
4. Extract up to four message samples from the parsed transcript: the first assistant message (session anchor), the most recent assistant message, and up to two consecutive pairs of recent messages. If fewer than four messages exist, run only the checks that are possible.
5. Compute cosine similarity between embedding vectors using the standard dot-product-over-magnitude formula implemented inline.
6. Run four named checks in order: Lost-in-middle compares the recent assistant message to the first assistant message and warns if similarity is below 0.3; Poisoning checks two consecutive recent messages and warns if the similarity drop between them exceeds 0.5 compared to an expected baseline; Distraction compares recent messages to the text of the current IN_PROGRESS task from progress.json and warns if similarity is below a reasonable threshold (suggest 0.25); Clash checks two very recent messages and warns if similarity is below 0.1.
7. For each pattern detected, append a warning line to stderr: "[masonry-context-monitor] WARNING: Semantic degradation detected — {pattern name}. Consider /compact."
8. Wrap all Ollama calls in try-catch: if the fetch fails for any reason (network error, timeout, model not loaded), skip the semantic checks entirely and continue.
9. The semantic check must not block the stop — it is advisory only.

**Edge cases:**
- If progress.json does not exist or has no IN_PROGRESS task, skip the Distraction check without error.
- If the transcript has fewer than two assistant messages, skip all four checks.
- Multiple patterns may fire in the same run; print a separate warning line for each.

**Failure modes:**
- Ollama returns a 404 for nomic-embed-text (model not installed): catch and skip silently.
- Ollama takes more than 5 seconds to respond: use AbortSignal.timeout(5000) and skip on timeout.

**Interfaces:**
- Reads: `masonry/src/hooks/masonry-context-monitor.js` (existing — must read first), `.autopilot/progress.json` (for Distraction check), transcript JSONL file from hook payload
- Writes: same hook file with semantic degradation logic added

---

## Task 11 — Create 5 new specialist agents [phase_end:agents]

**Purpose:** Add five specialist agents covering verification, MCP development, chaos engineering, penetration testing, and scientific literature research — all dual-written and registered.

**Flow for each agent:**
1. Create the agent file content with YAML frontmatter containing name, description, and model fields.
2. Write to `~/.claude/agents/{name}.md`.
3. Write identical content to `template/.claude/agents/{name}.md`.
4. Add entry to `masonry/agent_registry.yml` with tier: "draft", appropriate model, modes, and capabilities.

**Agent-specific content requirements:**

verification-analyst: Instructions must enumerate all six gates (Process, Reachability, Real Impact, PoC, Math Bounds, Environment) with a one-sentence definition each. Must include the 13-item Devil's Advocate checklist as a numbered list. Must include the LLM-bias warning verbatim. Output format: VERIFIED, UNVERIFIED, or INCONCLUSIVE, with per-gate evidence.

mcp-developer: Instructions must reference the MCP SDK, cover both stdio and SSE transports, include guidance on tool schema design (input schemas, error types), and describe how to write tests using the MCP test client. Must know how to scaffold a new server from scratch and how to add a tool to an existing server.

chaos-engineer: Instructions must list the five failure injection categories (service failure, network partition, resource exhaustion, clock skew, slow dependencies) and require a blast radius analysis before proposing any experiment. Must default to read-only mode and require explicit user approval before any execution. Output format: experiment proposal with scope, blast radius, and rollback plan.

penetration-tester: Instructions must list the six test categories (auth bypass, injection, privilege escalation, exposed secrets, SSRF, insecure deserialization). Must refuse to operate without an authorization context in the prompt — the refusal message should be specific about what authorization text is required. Output: CVSS-scored findings with severity, evidence, and remediation.

scientific-literature-researcher: Instructions must name all three search sources (arXiv, Semantic Scholar, PubMed). Must define the six extraction fields (citation, abstract, key claims, methodology, sample size, effect size with confidence intervals). Must define the three flags (predatory journal, unreviewed preprint, industry-funded) and explain how to apply each.

**Edge cases:**
- All five agents must have YAML frontmatter starting with `---`; the wiring test (W2c) will reject files without it.
- The registry YAML must preserve the existing list structure (YAML list under `agents:` key or root list depending on current format — read the file first to match).

**Failure modes:**
- A write to template/.claude/agents/ fails because the directory does not exist: create it with mkdir -p semantics before writing.

**Interfaces:**
- Reads: `masonry/agent_registry.yml` (to match existing YAML structure before appending)
- Writes: 10 agent .md files (5 agents × 2 paths), `masonry/agent_registry.yml` (5 new entries)

---

## Task 12 — Create /visual-diff skill

**Purpose:** Generate a self-contained HTML file that shows a before/after diff of any change, usable as a re-entry artifact after context compaction.

**Flow:**
1. Create the skill file with YAML frontmatter (name: visual-diff, description, invocation: `/visual-diff <description of what changed>`).
2. Document the output path pattern: `~/.agent/diagrams/visual-diff-{timestamp}.html` where timestamp is an ISO-8601 datetime string with colons replaced by hyphens for filesystem safety.
3. Document that the HTML file is entirely self-contained: no external CDN links, no external JavaScript, no external CSS — all styles and scripts inline.
4. Describe the required HTML structure: two side-by-side panels labeled "Before" and "After", with differences highlighted (additions in green, removals in red, unchanged in neutral), a change summary section above the panels listing what changed at a high level, a confidence-tagged decision log section listing the key decisions made and the confidence level for each, and a re-entry context note at the bottom explaining what was done, why, and what comes next.
5. Document that the re-entry context note is the critical section — it must be sufficient for a new context window to understand the state without reading the full diff.
6. Write to `~/.claude/skills/visual-diff/SKILL.md`.

**Edge cases:**
- If the user provides only a description rather than file paths, the skill generates the HTML from the description and recent git diff output.
- The `~/.agent/diagrams/` directory must be created if it does not exist.

**Interfaces:**
- Reads: git diff output (when file paths are available), user description from invocation
- Writes: `~/.claude/skills/visual-diff/SKILL.md` (new skill file), `~/.agent/diagrams/visual-diff-{timestamp}.html` (at skill invocation time)

---

## Task 13 — Create /visual-plan skill

**Purpose:** Generate a self-contained HTML dependency graph for the current build plan, color-coded by task status.

**Flow:**
1. Create the skill file with YAML frontmatter (name: visual-plan, description, invocations: `/visual-plan` and `/visual-plan <description>`).
2. Document the primary data source: when invoked without arguments, read `.autopilot/spec.md` and `.autopilot/progress.json`; when invoked with a description, use the description as the plan source.
3. Document the output path pattern: `~/.agent/diagrams/visual-plan-{timestamp}.html`, self-contained HTML with no external CDN.
4. Describe the required HTML structure: a task dependency graph where each node is a task, edges represent `[depends:N]` relationships extracted from the spec, nodes are color-coded by status (gray = PENDING, yellow = IN_PROGRESS, green = DONE, red = BLOCKED), phase markers appear as visual separators at `phase_end` boundaries, and a legend explains the color scheme.
5. Document that tasks with no explicit dependencies are shown as independent nodes, not floating elements — they connect to the phase start node.
6. Document the re-entry context note at the bottom: current phase, what task is active, how many tasks remain.
7. Write to `~/.claude/skills/visual-plan/SKILL.md`.

**Edge cases:**
- If `.autopilot/spec.md` does not exist when invoked without arguments, the skill falls back to a simple text summary of the user's description rather than failing.
- Dependency cycles in the spec (A depends on B, B depends on A) should be rendered with a visual warning marker, not silently collapsed.

**Interfaces:**
- Reads: `.autopilot/spec.md`, `.autopilot/progress.json` (optional, for status colors)
- Writes: `~/.claude/skills/visual-plan/SKILL.md` (new skill file), `~/.agent/diagrams/visual-plan-{timestamp}.html` at invocation time

---

## Task 14 — Create /visual-recap skill

**Purpose:** Generate a self-contained HTML session summary suitable as a re-entry artifact after a context handoff.

**Flow:**
1. Create the skill file with YAML frontmatter (name: visual-recap, description, invocation: `/visual-recap`).
2. Document the three data sources the skill reads at invocation time: git log for the last 10 commits (run `git log --oneline -10`), `.autopilot/build.log` for the action timeline, and Masonry session summary if available (masonry-state.json or similar campaign state).
3. Document the output path: `~/.agent/diagrams/visual-recap-{timestamp}.html`, self-contained.
4. Describe the five required sections in the HTML: action timeline (chronological list of what happened, sourced from build.log and git log), files changed (list of files modified with change type), test results (passing/failing counts from the most recent test run in build.log), open items (any BLOCKED tasks or logged warnings), and re-entry context note.
5. Document the re-entry context note structure precisely: three subsections labeled "What was done" (summary of completed work), "What's next" (first PENDING or IN_PROGRESS task), and "What's blocked" (any BLOCKED tasks with their block reason if logged).
6. Write to `~/.claude/skills/visual-recap/SKILL.md`.

**Edge cases:**
- If build.log does not exist, the action timeline section falls back to git log only.
- If no git repository is present, both git-dependent sections show "No git data available."
- If masonry-state.json has no session summary, the campaign section is omitted rather than showing an error.

**Interfaces:**
- Reads: `.autopilot/build.log`, `masonry-state.json`, git log output (via shell command at invocation time)
- Writes: `~/.claude/skills/visual-recap/SKILL.md` (new skill file), `~/.agent/diagrams/visual-recap-{timestamp}.html` at invocation time

---

## Task 15 — Create /spec-mine skill

**Purpose:** Reverse-engineer an existing codebase into a spec.md, acting as the inverse of the spec-writer agent.

**Flow:**
1. Create the skill file with YAML frontmatter (name: spec-mine, description, invocation: `/spec-mine <path or module>`).
2. Document the concept clearly: spec-mine reads code to discover what it does rather than what it should do — the output describes the current implementation, not a desired future state.
3. Document the five analysis areas the skill performs: public API surface (exported functions, endpoints, CLI commands), data models (schema definitions, types, database models), business logic flows (the key algorithms and decision paths), test coverage gaps (behaviors tested vs. untested), and undocumented behaviors (code paths with no tests and no docstrings).
4. Document the output: a `.autopilot/spec.md` file written in the standard spec format, with tasks representing the discovered behaviors, using past tense in task descriptions to signal these are descriptions not prescriptions.
5. Note that if `.autopilot/spec.md` already exists, the skill warns the user and asks for confirmation before overwriting.
6. Write to `~/.claude/skills/spec-mine/SKILL.md`.

**Edge cases:**
- If the path points to a single file, analyze only that file. If it points to a directory, analyze all non-test, non-config files within it.
- If the path does not exist, report the error and stop.
- Generated spec tasks should have no `[depends:N]` annotations since the order is inferred, not prescribed.

**Interfaces:**
- Reads: target files or directory specified in the invocation argument
- Writes: `~/.claude/skills/spec-mine/SKILL.md` (new skill file), `.autopilot/spec.md` at invocation time (with overwrite warning)

---

## Task 16 — Create /release-manager skill

**Purpose:** Automate version bumping and release note generation from conventional commits, with a confirmation step before any writes.

**Flow:**
1. Create the skill file with YAML frontmatter (name: release-manager, description, invocations: `/release [patch|minor|major]`).
2. Document the input reading step: the skill reads `git log --oneline` since the last version tag, reads the current version from `package.json` (if present) or `pyproject.toml` (if present), and reads `CHANGELOG.md` if it exists.
3. Document semver determination when no explicit level is passed: the skill scans commit messages for conventional commit prefixes — any commit with `BREAKING CHANGE` or `!` after the type means major; any commit with `feat:` means at least minor; all others mean patch. The highest-severity rule wins.
4. Document what is generated: a CHANGELOG.md entry for the new version with date and grouped commit list (Breaking Changes, Features, Fixes, Other), a GitHub release notes block formatted for copy-paste, and a version bump string showing the before and after version.
5. Document the confirmation step: print all proposed changes to stdout and ask the user to confirm before writing anything. Only after explicit confirmation: write the CHANGELOG entry, update the version field in package.json and/or pyproject.toml, and print the GitHub release notes block.
6. Document the supported version files: `package.json` (update the `version` field), `pyproject.toml` (update the `version` field under `[project]` or `[tool.poetry]`).
7. Write to `~/.claude/skills/release-manager/SKILL.md`.

**Edge cases:**
- If neither `package.json` nor `pyproject.toml` exists, the skill generates the changelog entry and release notes but skips the version bump write, noting which file to update manually.
- If the explicit level argument (patch/minor/major) is provided, use it unconditionally rather than inferring from commits.
- If CHANGELOG.md does not exist, create it with the first entry.

**Interfaces:**
- Reads: `git log` output, `package.json`, `pyproject.toml`, `CHANGELOG.md`
- Writes: `~/.claude/skills/release-manager/SKILL.md` (new skill file), `CHANGELOG.md`, `package.json` or `pyproject.toml` (at invocation time, after confirmation)

---

## Task 17 — Create /discover skill

**Purpose:** Facilitate structured product discovery using Jobs-to-be-Done framing and falsifiable experiment design.

**Flow:**
1. Create the skill file with YAML frontmatter (name: discover, description, invocation: `/discover <feature or hypothesis>`).
2. Document Phase 1 — JTBD analysis: the skill identifies who would hire this feature (the specific user persona), what job they are trying to get done (the progress they want to make), and what they are currently firing (the previous solution or workaround being replaced). Output is a JTBD statement in standard format.
3. Document Phase 2 — Assumption mapping: the skill generates exactly five assumptions about the feature, ranked by a two-axis matrix of importance (how critical is this to the feature's value) and uncertainty (how little we know about whether it is true). Output is an ordered list from highest to lowest importance × uncertainty score.
4. Document Phase 3 — Experiment design: for each of the five assumptions, the skill proposes the cheapest falsifiable test — a test that could prove the assumption false without building the full feature. Output is a structured experiment description with hypothesis, test method, success criteria, and cost estimate (time in hours).
5. Document the output path: `.discover/{slug}/discovery.md` where slug is a URL-safe version of the feature or hypothesis text, converted to lowercase with spaces replaced by hyphens.
6. Document the three sections of discovery.md: JTBD Canvas, Assumption Map, and Experiment Backlog.
7. Write to `~/.claude/skills/discover/SKILL.md`.

**Edge cases:**
- If `.discover/` directory does not exist, create it.
- If a discovery.md already exists for the same slug, append a timestamp suffix to the filename rather than overwriting.

**Interfaces:**
- Reads: feature or hypothesis description from invocation argument
- Writes: `~/.claude/skills/discover/SKILL.md` (new skill file), `.discover/{slug}/discovery.md` at invocation time

---

## Task 18 — Create /parse-prd skill [phase_end:skills]

**Purpose:** Convert a PRD document into a properly formatted `.autopilot/spec.md`, automatically annotating tasks with SPARC mode and complexity estimates.

**Flow:**
1. Create the skill file with YAML frontmatter (name: parse-prd, description, invocations: `/parse-prd <file-path>` and `/parse-prd` for stdin paste).
2. Document the extraction logic for each spec section: the goal is extracted from the PRD's objective or problem statement; user stories are converted to success criteria using "given/when/then" structure; features become tasks, one task per distinct deliverable; constraints become Notes entries; explicitly out-of-scope items populate the Out of Scope section.
3. Document the SPARC mode annotation rules: tasks involving UI components, React, TypeScript frontend, or CSS are annotated `[mode:typescript]`; tasks involving API endpoints, Python services, or database operations are annotated `[mode:python]` or `[mode:database]`; tasks involving security review are annotated `[mode:security]`; tasks involving architecture decisions are annotated `[mode:architect]`.
4. Document the complexity estimate format: each task description is followed by a comment in the format `<!-- complexity: N/10 -->` where N is 1 for trivial (config change, add a field) up to 10 for large (new subsystem). Estimates are based on: number of files likely touched, presence of new data models, external service dependencies, and test complexity.
5. Document that if `.autopilot/spec.md` already exists, the skill warns the user and asks whether to overwrite or append as additional tasks.
6. Write to `~/.claude/skills/parse-prd/SKILL.md`.

**Edge cases:**
- If the file path does not exist, report the error and stop.
- If the PRD has no identifiable user stories or feature list, the skill generates a single task per top-level PRD section as a fallback.
- If the PRD is pasted via stdin (no file path), the skill waits for EOF before processing.

**Interfaces:**
- Reads: PRD file at provided path, or stdin if no path given
- Writes: `~/.claude/skills/parse-prd/SKILL.md` (new skill file), `.autopilot/spec.md` at invocation time

---

## Task 19 — Add 7-point slop gate to uiux-master

**Purpose:** Force the agent to self-evaluate against seven common AI UI anti-patterns before producing any output, making generic choices impossible to miss.

**Flow:**
1. Read `~/.claude/agents/uiux-master.md` in full to understand its current structure and locate the appropriate insertion point — before any design output sections.
2. Add a mandatory self-evaluation section that must be executed before the agent produces any UI output. Label it clearly as the Slop Gate.
3. Document all seven checks as a numbered list: (1) Is Inter, Roboto, or Open Sans used as the primary font? (2) Is a `background-clip:text` gradient applied to a headline element? (3) Are emoji characters used as section headers or bullet points? (4) Is a glowing card effect applied to the majority of surfaces? (5) Is the color palette a cyan-magenta-pink tri-color default? (6) Does every card in a grid have identical dimensions (uniform grid)? (7) Is generic three-dot chrome (MoreHorizontal icon + dropdown) the primary interaction pattern on most cards?
4. For each check that would result in FAIL, the agent must name the specific alternative it will use instead before proceeding. This is not optional — a FAIL without an alternative is not acceptable.
5. Document the output comment the agent prints before any code: `<!-- SLOP GATE: 7/7 PASS -->` if all pass, or a list of failures with their alternatives if any fail.
6. Write the updated content back to `~/.claude/agents/uiux-master.md`.
7. Write the identical updated content to `template/.claude/agents/uiux-master.md`.

**Edge cases:**
- The slop gate applies to every UI output, including small component additions. There are no size-based exemptions.
- If the user's explicit request requires one of the blocked patterns (e.g., "use Inter"), the agent should note this in the gate output as a user-override rather than a FAIL.

**Interfaces:**
- Reads: `~/.claude/agents/uiux-master.md` (existing — must read first), `template/.claude/agents/uiux-master.md` (existing — must read first)
- Writes: both agent files with the slop gate section added

---

## Task 20 — Add domain exploration forcing function to uiux-master [depends: Task 19]

**Purpose:** Prevent the agent from making design decisions based on generic AI defaults by requiring domain-specific research before any design work begins.

**Flow:**
1. Read `~/.claude/agents/uiux-master.md` in full (after Task 19's changes are already present) to find the right insertion point.
2. Add Phase 0 — Domain Exploration as the first phase of the agent's process, before any design decisions are made.
3. Phase 0 has four mandatory steps that must all be completed and their outputs documented before Phase 1 begins: first, identify five or more concepts from the project's actual domain (e.g., for a medical app: diagnosis, treatment pathway, triage, lab result, referral); second, identify five or more colors drawn from the physical world of that domain (e.g., for a medical app: surgical blue-green, sterile white, amber warning light, cardiac monitor green, X-ray grey); third, explicitly name three default AI UI patterns being rejected for this project and state why each is rejected; fourth, write a one-sentence WHY statement for each major UI component explaining what domain truth it expresses.
4. Document that the outputs of Phase 0 constitute the Design Intent Document, which should be referenced throughout the session by name (e.g., "per the Design Intent Document: the dashboard uses cardiac monitor green because...").
5. Document the Design Intent Document length: 100-200 words. Longer documents indicate insufficient focus; shorter documents indicate insufficient thought.
6. Write both agent files.

**Edge cases:**
- If the user's request is a small component addition rather than a full design session, Phase 0 is still required but may reference a prior Design Intent Document from the same session rather than generating a new one.
- The domain concepts and colors must be genuinely domain-specific — "blue" and "modern" are not acceptable domain concepts.

**Interfaces:**
- Reads: `~/.claude/agents/uiux-master.md` (after Task 19 changes), `template/.claude/agents/uiux-master.md` (after Task 19 changes)
- Writes: both agent files with Phase 0 added before existing Phase 1

---

## Task 21 — Update masonry wiring tests to cover new agents and hooks

**Purpose:** Extend the existing test file so that all artifacts created in this phase are verified by the completeness tests, without disturbing existing passing tests.

**Flow:**
1. Read `masonry/tests/test_wiring_completeness.py` in full to understand the existing test classes, helper functions, and the REGISTRY_ONLY_PLANNED set.
2. Add a new test class or extend existing classes with the following new assertions, keeping each as a separate test method so failures are individually identifiable.
3. For the 5 new agents: add a parametrized or explicit test asserting that each of the five names (verification-analyst, mcp-developer, chaos-engineer, penetration-tester, scientific-literature-researcher) has a .md file in both `~/.claude/agents/` and `template/.claude/agents/`, and that each name appears in agent_registry.yml.
4. For the 2 new hooks: add assertions that `masonry-config-protection.js` and `masonry-block-no-verify.js` exist in `masonry/src/hooks/` and that both appear in the `_settings_hook_commands()` output.
5. For the 7 new skills: add assertions that each of the following directories has a SKILL.md: `~/.claude/skills/visual-diff/`, `~/.claude/skills/visual-plan/`, `~/.claude/skills/visual-recap/`, `~/.claude/skills/spec-mine/`, `~/.claude/skills/release-manager/`, `~/.claude/skills/discover/`, `~/.claude/skills/parse-prd/`.
6. Do not modify any existing test methods or the REGISTRY_ONLY_PLANNED set.
7. Write the updated test file.

**Edge cases:**
- The test for hook wiring must check for the hook filename in settings.json, not just the file existence — both conditions must pass independently.
- New test methods must follow the existing naming convention: `test_w{N}{letter}_description`.

**Interfaces:**
- Reads: `masonry/tests/test_wiring_completeness.py` (existing — must read first)
- Writes: same file with new test methods added

---

## Task 22 — Run wiring completeness tests and fix any failures [depends: Task 21]

**Purpose:** Verify that all wiring is correct end-to-end by running the completeness tests and fixing any gaps found.

**Flow:**
1. Run `python -m pytest masonry/tests/test_wiring_completeness.py -q --tb=short` from the repository root and capture the output.
2. Parse the output for failures. If all tests pass, report success and stop.
3. For each failure, identify the root cause: missing file, missing registry entry, missing settings.json entry, or file present but not at the expected path.
4. Fix the specific gap: create the missing file with minimal valid content if it is a new agent or skill, add the missing registry entry if it is a registry gap, or add the hook command to settings.json in the correct event section if it is a wiring gap.
5. Re-run the test suite after each fix.
6. Continue until the full suite exits with code 0.

**Edge cases:**
- If a test fails due to a missing file that was supposed to be created in an earlier task, the fix is to create that file — not to skip the test or add to REGISTRY_ONLY_PLANNED.
- The REGISTRY_ONLY_PLANNED set in the test file should never be modified by this task — it is a curated set of acknowledged gaps.

**Failure modes:**
- If the test suite itself has a syntax error after Task 21's additions, the runner will fail at collection time. Inspect the error message and fix the test file syntax before re-running.
- If pytest is not installed: install it and re-run. Do not mark this task DONE without a passing test run.

**Interfaces:**
- Reads: test output, any file that a failing test points to
- Writes: any missing files or registry entries needed to make tests pass

---

## Task 23 — Update ARCHITECTURE.md, ROADMAP.md, CHANGELOG.md for Phase 6

**Purpose:** Keep the project's three primary documentation files synchronized with the Phase 6 changes just implemented.

**Flow:**
1. Read all three files before writing anything: `ARCHITECTURE.md`, `ROADMAP.md`, and `CHANGELOG.md`. Identify the existing structure of each — section headings, phase organization, date format in CHANGELOG.
2. Update ARCHITECTURE.md: locate the agent fleet section and add the five new agents with one-line descriptions; locate the hooks section and add the two new hooks; locate the skills section and add the seven new skills; add a note under the /build pipeline description explaining the Guard/Verify split; add spec-reviewer to the build pipeline diagram or description if one exists.
3. Update ROADMAP.md: locate Phase 6 items (or create a Phase 6 section if it does not exist) and mark all 23 tasks as complete. Use whatever completion marker the existing roadmap uses for prior phases (checkmarks, strikethrough, "done" labels, etc.).
4. Update CHANGELOG.md: add a new entry at the top (most recent first) dated 2026-03-28, with a heading for Phase 6. List all 23 tasks by their task number and one-line description. Group entries by category: Dev Execution Loop (Tasks 1-4), Skills (Tasks 5-6, 12-18), Infrastructure Hooks (Tasks 7-10), Agents (Tasks 11), UI Quality (Tasks 19-20), Testing and Docs (Tasks 21-23).
5. Write all three files.

**Edge cases:**
- If ARCHITECTURE.md does not have a hooks section or skills section, add them rather than skipping.
- If ROADMAP.md has no Phase 6 section, create one before the next planned phase.
- If CHANGELOG.md is empty or does not exist, create it with only the Phase 6 entry.

**Interfaces:**
- Reads: `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md` (all existing — must read first)
- Writes: all three files with Phase 6 content added

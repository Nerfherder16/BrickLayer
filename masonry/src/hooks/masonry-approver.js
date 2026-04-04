#!/usr/bin/env node
/**
 * PreToolUse hook: Auto-approve Write, Edit, and Bash tool calls
 * when Masonry build OR UI workflow is active.
 *
 * Checks .autopilot/mode (build/fix) and .ui/mode (compose/fix).
 * Determines project root by walking up from tool_input.file_path
 * or extracting paths from tool_input.command.
 *
 * Mortar gate: advisory reminder (or hard deny when MASONRY_ENFORCE_ROUTING=1)
 * when Mortar has not written a fresh routing receipt to masonry-state.json.
 * Bash is unconditionally exempt from the Mortar gate.
 *
 * Helper functions live in masonry-approver-helpers.js.
 */
"use strict";

const { dirname } = require("path");
const {
  readStdin, isTier1Tier2, isMortarConsulted, isSubagentContext,
  findAutopilotMode, findUiMode, findResearchProjectFresh, getCandidateDirs,
} = require("./masonry-approver-helpers");

function allow(reason) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        permissionDecisionReason: reason,
      },
    })
  );
  process.exit(0);
}

function deny(reason) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    })
  );
  process.exit(0);
}

async function main() {
  const input = await readStdin();
  if (!input) process.exit(0);

  let parsed;
  try { parsed = JSON.parse(input); } catch { process.exit(0); }

  const cwd = parsed.cwd || process.cwd();
  const toolInput = parsed.tool_input || {};
  const toolName = (parsed.tool_name || "").toLowerCase();
  const filePath = toolInput.file_path || toolInput.path || "";

  // BrickLayer research campaign — approve everything, including Bash.
  // Walk up from cwd AND from the tool's target path.
  const inResearch =
    findResearchProjectFresh(cwd) ||
    (filePath && findResearchProjectFresh(dirname(filePath)));
  if (inResearch) allow("BrickLayer research campaign active");

  const candidates = getCandidateDirs(parsed);

  // ── Mode detection ────────────────────────────────────────────────────────────
  const targetToolIsActionable =
    toolName === "write" || toolName === "edit" ||
    toolName === "bash" || toolName === "multiedit";
  const mortarGateApplicable = targetToolIsActionable && !isSubagentContext();

  let autopilotMode = null;
  let uiMode = null;
  for (const dir of candidates) {
    if (!autopilotMode) autopilotMode = findAutopilotMode(dir);
    if (!uiMode) uiMode = findUiMode(dir);
    if (autopilotMode && uiMode) break;
  }

  const buildActive =
    autopilotMode === "build" || autopilotMode === "fix" ||
    uiMode === "compose" || uiMode === "fix";

  // ── Mortar gate ───────────────────────────────────────────────────────────────
  // Advisory reminder (default) or hard deny (MASONRY_ENFORCE_ROUTING=1) when
  // Mortar has not written a fresh routing receipt this turn.
  // Bash is unconditionally exempt — git ops and shell commands must not be gated.
  if (mortarGateApplicable && !buildActive && !isMortarConsulted()) {
    if (toolName !== "bash" && toolName !== "read") {
      if (process.env.MASONRY_ENFORCE_ROUTING === "1") {
        deny(
          "[Masonry] Mortar routing receipt missing or stale. " +
          "Invoke the mortar agent (subagent_type: \"mortar\") before using Write/Edit. " +
          "Bypass: set effort=low prompt or unset MASONRY_ENFORCE_ROUTING."
        );
      }
      process.stderr.write(
        "[Masonry] Heads up: Mortar hasn't been consulted this turn. " +
        "For complex multi-file work, invoke the mortar agent first. " +
        "(Set MASONRY_ENFORCE_ROUTING=1 to make this a hard block.)\n"
      );
    }
    // Allow through when enforcement flag is not set — gate is advisory only.
  }

  // ── Auto-approval for active build/compose modes ──────────────────────────────
  if (!buildActive) process.exit(0);

  // Block auto-approval for Tier 1/2 authority files — must always prompt user.
  if (isTier1Tier2(filePath)) process.exit(0);

  // Never auto-approve Bash outside research mode.
  if (toolName === "bash") process.exit(0);

  const reason = autopilotMode
    ? `Masonry build mode "${autopilotMode}" active`
    : `UI workflow mode "${uiMode}" active`;
  allow(reason);
}

main().catch(() => process.exit(0));

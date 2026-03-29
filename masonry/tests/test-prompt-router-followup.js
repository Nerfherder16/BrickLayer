#!/usr/bin/env node
/**
 * Test: last_route multi-turn inheritance in masonry-prompt-router.js
 *
 * Pipes 3 prompts through the hook binary in sequence and asserts all 3
 * produce non-empty additionalContext output containing an agent route.
 *
 * Note: the hook reads input.prompt (not tool_input.prompt), so payloads
 * are sent as { prompt: "..." } to match the hook's input contract.
 */

const { execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const HOOK = path.resolve(__dirname, "../src/hooks/masonry-prompt-router.js");
const STATE_PATH = path.resolve(__dirname, "../masonry-state.json");

// Backup and clear last_route + mortar_consulted before test
let stateBackup = null;
if (fs.existsSync(STATE_PATH)) {
  stateBackup = fs.readFileSync(STATE_PATH, "utf8");
  const st = JSON.parse(stateBackup);
  delete st.last_route;
  delete st.mortar_consulted;
  fs.writeFileSync(STATE_PATH, JSON.stringify(st, null, 2));
}

const prompts = [
  "Refactor the authentication service to extract the token validation logic into a separate TokenValidator class",
  "Now also update the tests in the integration test suite to use the new TokenValidator interface",
  "Do the same thing for the UserService module",
];

let allPassed = true;

for (let i = 0; i < prompts.length; i++) {
  const prompt = prompts[i];
  // Hook reads input.prompt directly (UserPromptSubmit hook format)
  const payload = JSON.stringify({ prompt });

  let output = "";
  try {
    output = execFileSync("node", [HOOK], {
      input: payload,
      encoding: "utf8",
      timeout: 10000,
    });
  } catch (e) {
    output = e.stdout || "";
  }

  // Parse JSON response
  let parsed = null;
  try {
    parsed = JSON.parse(output);
  } catch {
    console.error(`Turn ${i + 1}: FAIL — could not parse JSON output`);
    console.error("Raw output:", output.slice(0, 200));
    allPassed = false;
    continue;
  }

  const context = parsed?.hookSpecificOutput?.additionalContext || parsed?.additionalContext || "";
  if (!context || context.trim().length === 0) {
    console.error(`Turn ${i + 1}: FAIL — empty additionalContext`);
    console.error("Parsed:", JSON.stringify(parsed).slice(0, 300));
    allPassed = false;
  } else {
    console.log(`Turn ${i + 1}: PASS — route hint present`);
    console.log(`  Context: ${context.slice(0, 100)}...`);
  }
}

// Restore state
if (stateBackup !== null) {
  fs.writeFileSync(STATE_PATH, stateBackup);
} else if (fs.existsSync(STATE_PATH)) {
  // Remove last_route we created during test
  try {
    const st = JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
    delete st.last_route;
    fs.writeFileSync(STATE_PATH, JSON.stringify(st, null, 2));
  } catch {}
}

if (!allPassed) {
  console.error("\nSome turns failed.");
  process.exit(1);
}
console.log("\nAll 3 turns produced routing hints. PASS.");
process.exit(0);

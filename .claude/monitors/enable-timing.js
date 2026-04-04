#!/usr/bin/env node
// Wraps all hooks in settings.json with hook-timer.sh for timing.
// Run:   node ~/.claude/monitors/enable-timing.js
// Undo:  node ~/.claude/monitors/enable-timing.js --undo

const fs = require("fs");
const path = require("path");

const SETTINGS = path.join(process.env.HOME, ".claude", "settings.json");
const TIMER = "~/.claude/monitors/hook-timer.sh";
const UNDO = process.argv.includes("--undo");

const settings = JSON.parse(fs.readFileSync(SETTINGS, "utf8"));
let count = 0;

for (const [event, groups] of Object.entries(settings.hooks || {})) {
  for (const group of groups) {
    for (const hook of group.hooks || []) {
      if (hook.type !== "command") continue;

      if (UNDO) {
        // Strip the timer wrapper
        const match = hook.command.match(new RegExp(`^${TIMER.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s+\\S+\\s+(.+)$`));
        if (match) {
          hook.command = match[1];
          count++;
        }
      } else {
        // Skip if already wrapped
        if (hook.command.includes("hook-timer.sh")) continue;
        // Extract a short name from the command
        const nameMatch = hook.command.match(/([a-z-]+)\.(?:js|sh)(?:\s|$)/);
        const name = nameMatch ? nameMatch[1] : event.toLowerCase();
        hook.command = `${TIMER} ${name} ${hook.command}`;
        count++;
      }
    }
  }
}

fs.writeFileSync(SETTINGS, JSON.stringify(settings, null, 2), "utf8");
console.log(`${UNDO ? "Unwrapped" : "Wrapped"} ${count} hooks.`);
console.log(UNDO ? "Timing disabled." : "Timing enabled. View: tail -f ~/.claude/monitors/hook-times.log");

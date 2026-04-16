'use strict';
// session/skills-directive.js — Superpowers skill-check directive injection
// Injects a 'check for applicable skill before responding' directive at session start.
// Skipped on --resume sessions to prevent context inflation.

/**
 * Returns the skill-check directive string for fresh sessions, null for resumed sessions.
 * @param {object} input - Parsed JSON from stdin (session start payload)
 * @returns {string|null}
 */
function getSkillsDirective(input) {
  // Skip on resumed sessions — re-injecting inflates context without benefit
  if (!input || typeof input !== 'object') return null;
  if (input.startup_type === 'resume') return null;
  if (input.is_resume === true) return null;

  return [
    '[Superpowers] Before responding to any request: check whether a skill applies.',
    'If there is even a 1% chance a skill is relevant, invoke it with the Skill tool before writing any code or plans.',
    'Skill priority order: brainstorm (design first) → plan (spec before code) → build (implementation) → debug (diagnosis before fix).',
    'Key trigger: if the request involves designing something new, use /brainstorm first.',
  ].join('\n');
}

module.exports = { getSkillsDirective };

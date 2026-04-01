'use strict';
// engine/frontmatter.js — YAML frontmatter parsing utilities for agent files.
//
// Port of bl/frontmatter.py to Node.js.

const { MODEL_MAP } = require('./tmux/helpers');

function stripFrontmatter(text) {
  if (!text.startsWith('---')) return text;
  const end = text.indexOf('---', 3);
  if (end === -1) return text;
  return text.slice(end + 3).trim();
}

function readFrontmatterModel(text) {
  if (!text.startsWith('---')) return null;
  const end = text.indexOf('---', 3);
  if (end === -1) return null;
  const fm = text.slice(3, end);
  for (const line of fm.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('model:')) {
      const value = trimmed.split(':', 2)[1].trim().replace(/^["']|["']$/g, '');
      return MODEL_MAP[value] || value || null;
    }
  }
  return null;
}

module.exports = { stripFrontmatter, readFrontmatterModel };

#!/usr/bin/env node
/**
 * masonry-checkpoint.js — PostToolUse hook
 * Records file edits to the hot path tracker for session intelligence.
 */
'use strict';
const { recordEdit } = require('./session/hotpaths');

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input = {}, cwd = process.cwd() } = hookData;
    if (!['Write', 'Edit'].includes(tool_name)) process.exit(0);
    const filePath = tool_input.file_path || tool_input.path || '';
    if (!filePath) process.exit(0);
    try {
      recordEdit(cwd, filePath);
    } catch {}
  } catch {}
  process.exit(0);
});

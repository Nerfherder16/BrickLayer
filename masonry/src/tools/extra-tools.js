'use strict';

/**
 * extra-tools.js — overflow tool handlers for masonry-mcp.js
 * masonry_daemon  — manage background daemon workers
 * masonry_checkpoint — list recent file-edit checkpoints
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DAEMON_JS = path.join(__dirname, '../daemon/daemon.js');

const SCHEMAS = [
  {
    name: 'masonry_daemon',
    description: 'Manage background daemon workers (drift-check, testgaps, recall-consolidate). ' +
      'Actions: start — launch all workers; stop — kill all workers; status — print status table; list — list registered workers.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['start', 'stop', 'status', 'list'],
          description: "Worker lifecycle action. Defaults to 'status'.",
        },
      },
      required: [],
    },
  },
  {
    name: 'masonry_checkpoint',
    description: 'List recent file-edit checkpoints written by masonry-checkpoint.js hook. ' +
      'Each checkpoint records: ts, file, branch, diff_summary, tool, session_id.',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: {
          type: 'string',
          description: 'Absolute path to the project directory. Defaults to cwd.',
        },
        limit: {
          type: 'number',
          description: 'Max number of checkpoints to return (most recent). Defaults to 20.',
        },
      },
      required: [],
    },
  },
];

function handle(name, args = {}) {
  switch (name) {
    case 'masonry_daemon': {
      const action = args.action || 'status';
      if (!fs.existsSync(DAEMON_JS)) {
        return { success: false, error: `daemon.js not found at ${DAEMON_JS}` };
      }
      try {
        const out = execSync(`node "${DAEMON_JS}" ${action}`, { timeout: 10000, encoding: 'utf8' });
        return { success: true, action, output: out.trim() };
      } catch (e) {
        return { success: false, action, error: e.message };
      }
    }

    case 'masonry_checkpoint': {
      const projectPath = args.project_path || process.cwd();
      const limit = args.limit || 20;
      const cpFile = path.join(projectPath, '.masonry', 'checkpoints.jsonl');
      if (!fs.existsSync(cpFile)) return { success: true, checkpoints: [], total: 0 };
      try {
        const lines = fs.readFileSync(cpFile, 'utf8').trim().split('\n').filter(Boolean);
        const checkpoints = lines.slice(-limit).map((l) => JSON.parse(l));
        return { success: true, checkpoints, total: lines.length };
      } catch (e) {
        return { success: false, error: e.message };
      }
    }

    default:
      throw new Error(`extra-tools: unknown tool ${name}`);
  }
}

module.exports = { handle, schemas: SCHEMAS };

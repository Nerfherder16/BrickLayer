'use strict';
// engine/config.js — BrickLayer engine config singleton.
//
// Extends masonry core config with project-specific paths and settings.
// All engine modules import `cfg` and read its properties.
// Call `initProject(name)` before any runner runs.

const fs = require('fs');
const path = require('path');
const { loadConfig } = require('../core/config');

// API route constants (project-agnostic)
const SEARCH_ROUTE = '/search/query';
const STORE_ROUTE = '/memory/store';
const HEALTH_ROUTE = '/health';
const CONSOLIDATE_ROUTE = '/admin/consolidate';

// Resolve BrickLayer root (two levels up from this file: engine/ -> src/ -> masonry/ -> Bricklayer2.0/)
const _blRoot = path.resolve(__dirname, '..', '..', '..');

const masonryCfg = loadConfig();

const cfg = {
  baseUrl: process.env.RECALL_HOST || masonryCfg.recallHost,
  apiKey: process.env.RECALL_API_KEY || masonryCfg.recallApiKey,
  requestTimeout: 10000,
  localOllamaUrl: process.env.OLLAMA_HOST || masonryCfg.ollamaHost,
  localModel: masonryCfg.ollamaModel,
  blRoot: _blRoot,
  projectRoot: _blRoot,
  findingsDir: path.join(_blRoot, 'findings'),
  resultsTsv: path.join(_blRoot, 'results.tsv'),
  questionsMd: path.join(_blRoot, 'questions.md'),
  historyDb: path.join(_blRoot, 'history.db'),
  agentsDir: path.join(_blRoot, '.claude', 'agents'),
};

function authHeaders() {
  return {
    Authorization: `Bearer ${cfg.apiKey}`,
    'Content-Type': 'application/json',
  };
}

/**
 * Load project config from project.json and update cfg paths.
 * @param {string|null} projectName
 */
function initProject(projectName) {
  let projectDir = null;

  if (projectName) {
    const candidates = [
      path.join(_blRoot, 'projects', projectName),
      path.join(_blRoot, projectName),
    ];

    for (const candidate of candidates) {
      const pjson = path.join(candidate, 'project.json');
      if (fs.existsSync(pjson)) {
        projectDir = candidate;
        break;
      }
    }

    if (!projectDir) {
      console.error(`Error: project '${projectName}' not found.`);
      for (const c of candidates) {
        console.error(`  Checked: ${path.join(c, 'project.json')}`);
      }
      process.exit(1);
    }

    const projectCfg = JSON.parse(
      fs.readFileSync(path.join(projectDir, 'project.json'), 'utf8')
    );

    const recallSrc = projectCfg.recall_src || projectCfg.target_git;
    if (recallSrc) cfg.recallSrc = recallSrc;
    if (projectCfg.target_live_url) cfg.baseUrl = projectCfg.target_live_url;
    if (projectCfg.api_key) cfg.apiKey = projectCfg.api_key;
  } else {
    projectDir = _blRoot;
  }

  cfg.projectRoot = projectDir;
  cfg.findingsDir = path.join(projectDir, 'findings');
  cfg.resultsTsv = path.join(projectDir, 'results.tsv');
  cfg.questionsMd = path.join(projectDir, 'questions.md');
  cfg.historyDb = path.join(projectDir, 'history.db');
  cfg.agentsDir = path.join(projectDir, '.claude', 'agents');

  fs.mkdirSync(cfg.findingsDir, { recursive: true });
}

module.exports = {
  cfg,
  authHeaders,
  initProject,
  SEARCH_ROUTE,
  STORE_ROUTE,
  HEALTH_ROUTE,
  CONSOLIDATE_ROUTE,
};

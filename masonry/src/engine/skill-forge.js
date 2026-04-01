'use strict';
// engine/skill-forge.js — Skill registry and forge utilities.
//
// Port of bl/skill_forge.py to Node.js.

const fs = require('fs');
const path = require('path');
const os = require('os');

let _SKILLS_DIR = path.join(os.homedir(), '.claude', 'skills');

function _setSkillsDir(dir) { _SKILLS_DIR = dir; }

function _registryPath(projectRoot) {
  return path.join(String(projectRoot), 'skill_registry.json');
}

function _loadRegistry(projectRoot) {
  const rpath = _registryPath(projectRoot);
  if (!fs.existsSync(rpath)) return {};
  try {
    return JSON.parse(fs.readFileSync(rpath, 'utf8'));
  } catch {
    return {};
  }
}

function _saveRegistry(projectRoot, registry) {
  fs.writeFileSync(
    _registryPath(projectRoot),
    JSON.stringify(registry, null, 2),
    'utf8',
  );
}

function writeSkill(name, content, projectRoot, description = '', sourceFinding = '') {
  const skillDir = path.join(_SKILLS_DIR, name);
  fs.mkdirSync(skillDir, { recursive: true });
  const skillPath = path.join(skillDir, 'SKILL.md');
  fs.writeFileSync(skillPath, content, 'utf8');

  const registry = _loadRegistry(projectRoot);
  const now = new Date().toISOString();
  if (!(name in registry)) {
    registry[name] = {
      created: now,
      last_updated: now,
      description,
      source_finding: sourceFinding,
      campaign: path.basename(String(projectRoot)),
      repair_count: 0,
    };
  } else {
    registry[name].last_updated = now;
    registry[name].repair_count = (registry[name].repair_count || 0) + 1;
  }
  _saveRegistry(projectRoot, registry);
  return skillPath;
}

function skillExists(name) {
  return fs.existsSync(path.join(_SKILLS_DIR, name, 'SKILL.md'));
}

function readSkill(name) {
  const fpath = path.join(_SKILLS_DIR, name, 'SKILL.md');
  if (!fs.existsSync(fpath)) return null;
  return fs.readFileSync(fpath, 'utf8');
}

function listProjectSkills(projectRoot) {
  const registry = _loadRegistry(projectRoot);
  const result = [];
  for (const [name, meta] of Object.entries(registry)) {
    const fpath = path.join(_SKILLS_DIR, name, 'SKILL.md');
    result.push({
      name,
      path: fpath,
      exists: fs.existsSync(fpath),
      description: meta.description || '',
      sourceFinding: meta.source_finding || '',
      campaign: meta.campaign || '',
      created: meta.created || '',
      lastUpdated: meta.last_updated || '',
      repairCount: meta.repair_count || 0,
    });
  }
  return result.sort((a, b) => a.created.localeCompare(b.created));
}

module.exports = { writeSkill, skillExists, readSkill, listProjectSkills, _setSkillsDir };

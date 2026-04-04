import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/skill-forge', () => {
  let mod, tmpDir, skillsDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-forge-'));
    skillsDir = path.join(tmpDir, 'skills');
    fs.mkdirSync(skillsDir, { recursive: true });
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'skill-forge.js');
    delete require.cache[modPath];
    mod = require(modPath);
    mod._setSkillsDir(skillsDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('writeSkill', () => {
    it('should write skill file and register it', () => {
      const skillPath = mod.writeSkill('test-skill', '# Skill', tmpDir, 'desc', 'Q1');
      expect(fs.existsSync(skillPath)).toBe(true);
      expect(fs.readFileSync(skillPath, 'utf8')).toBe('# Skill');

      const registry = JSON.parse(fs.readFileSync(path.join(tmpDir, 'skill_registry.json'), 'utf8'));
      expect(registry['test-skill']).toBeDefined();
      expect(registry['test-skill'].description).toBe('desc');
    });

    it('should increment repair_count on update', () => {
      mod.writeSkill('test-skill', 'v1', tmpDir);
      mod.writeSkill('test-skill', 'v2', tmpDir);

      const registry = JSON.parse(fs.readFileSync(path.join(tmpDir, 'skill_registry.json'), 'utf8'));
      expect(registry['test-skill'].repair_count).toBe(1);
    });
  });

  describe('skillExists', () => {
    it('should return false for non-existent skill', () => {
      expect(mod.skillExists('nope')).toBe(false);
    });

    it('should return true for written skill', () => {
      mod.writeSkill('my-skill', 'content', tmpDir);
      expect(mod.skillExists('my-skill')).toBe(true);
    });
  });

  describe('readSkill', () => {
    it('should return null for non-existent skill', () => {
      expect(mod.readSkill('nope')).toBeNull();
    });

    it('should return content for existing skill', () => {
      mod.writeSkill('my-skill', '# Hello', tmpDir);
      expect(mod.readSkill('my-skill')).toBe('# Hello');
    });
  });

  describe('listProjectSkills', () => {
    it('should return empty for no skills', () => {
      expect(mod.listProjectSkills(tmpDir)).toEqual([]);
    });

    it('should list skills with metadata', () => {
      mod.writeSkill('skill-a', 'content a', tmpDir, 'desc a', 'Q1');
      const skills = mod.listProjectSkills(tmpDir);
      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('skill-a');
      expect(skills[0].description).toBe('desc a');
    });
  });
});

import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/frontmatter', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'frontmatter.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('stripFrontmatter', () => {
    it('should return text unchanged if no frontmatter', () => {
      expect(mod.stripFrontmatter('hello world')).toBe('hello world');
    });

    it('should strip YAML frontmatter', () => {
      const text = '---\nmodel: sonnet\n---\n# Agent\nBody here';
      expect(mod.stripFrontmatter(text)).toBe('# Agent\nBody here');
    });

    it('should return text if opening --- but no closing ---', () => {
      const text = '---\nmodel: sonnet\nno closing';
      expect(mod.stripFrontmatter(text)).toBe(text);
    });
  });

  describe('readFrontmatterModel', () => {
    it('should return null if no frontmatter', () => {
      expect(mod.readFrontmatterModel('no frontmatter')).toBeNull();
    });

    it('should extract and map model from frontmatter', () => {
      const text = '---\nmodel: sonnet\n---\nbody';
      const result = mod.readFrontmatterModel(text);
      // 'sonnet' should map through MODEL_MAP
      expect(result).toBeTruthy();
    });

    it('should return raw value for unknown model alias', () => {
      const text = '---\nmodel: custom-model-v9\n---\nbody';
      expect(mod.readFrontmatterModel(text)).toBe('custom-model-v9');
    });

    it('should return null if no model field in frontmatter', () => {
      const text = '---\ntitle: agent\n---\nbody';
      expect(mod.readFrontmatterModel(text)).toBeNull();
    });
  });
});

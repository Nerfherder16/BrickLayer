import { describe, it, expect, beforeAll } from 'vitest';

describe('engine/nl-entry', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(process.cwd(), 'src', 'engine', 'nl-entry.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('parseIntent', () => {
    it('should detect new_feature intent', () => {
      const intent = mod.parseIntent('I just added concurrent Neo4j writes');
      expect(intent.intentCategory).toBe('new_feature');
    });

    it('should detect bug_fix intent', () => {
      const intent = mod.parseIntent('I fixed the login page rendering bug');
      expect(intent.intentCategory).toBe('bug_fix');
    });

    it('should detect technologies', () => {
      const intent = mod.parseIntent('Added redis caching and neo4j queries');
      expect(intent.technologies).toContain('redis');
      expect(intent.technologies).toContain('neo4j');
    });

    it('should extract concerns from matched technologies', () => {
      const intent = mod.parseIntent('Added redis caching');
      expect(intent.concerns.length).toBeGreaterThan(0);
    });

    it('should extract nouns', () => {
      const intent = mod.parseIntent('Added session store writes');
      expect(intent.nouns.length).toBeGreaterThan(0);
    });
  });

  describe('generateFromDescription', () => {
    it('should generate questions from a description', () => {
      const questions = mod.generateFromDescription('I just added concurrent Neo4j writes to the session store');
      expect(questions.length).toBeGreaterThan(0);
      expect(questions.length).toBeLessThanOrEqual(5);
    });

    it('should generate questions with required fields', () => {
      const questions = mod.generateFromDescription('Fixed the auth token expiry bug');
      for (const q of questions) {
        expect(q.id).toBeTruthy();
        expect(q.title).toBeTruthy();
        expect(q.mode).toBeTruthy();
        expect(q.status).toBe('PENDING');
        expect(q.question).toBeTruthy();
      }
    });

    it('should respect max_questions', () => {
      const questions = mod.generateFromDescription('Added redis caching', 2);
      expect(questions.length).toBeLessThanOrEqual(2);
    });

    it('should generate tech-specific questions when tech matched', () => {
      const questions = mod.generateFromDescription('Added redis caching');
      const hasRedis = questions.some(q => q.question.toLowerCase().includes('redis'));
      expect(hasRedis).toBe(true);
    });
  });

  describe('formatPreview', () => {
    it('should format questions for display', () => {
      const questions = mod.generateFromDescription('Added Neo4j writes');
      const preview = mod.formatPreview(questions);
      expect(preview).toContain('Generated');
      expect(preview).toContain('question');
    });

    it('should handle empty list', () => {
      expect(mod.formatPreview([])).toContain('No questions generated');
    });
  });
});

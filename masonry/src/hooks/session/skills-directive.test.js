import { describe, it, expect } from 'vitest';
import { getSkillsDirective } from './skills-directive.js';

describe('getSkillsDirective', () => {
  it('returns directive string for fresh session (no startup_type)', () => {
    const result = getSkillsDirective({});
    expect(result).toBeTypeOf('string');
    expect(result).toContain('[Superpowers]');
    expect(result).toContain('brainstorm');
  });

  it('returns null for resumed session (startup_type: resume)', () => {
    const result = getSkillsDirective({ startup_type: 'resume' });
    expect(result).toBeNull();
  });

  it('returns null for resumed session (is_resume: true)', () => {
    const result = getSkillsDirective({ is_resume: true });
    expect(result).toBeNull();
  });

  it('returns null for null input', () => {
    const result = getSkillsDirective(null);
    expect(result).toBeNull();
  });

  it('returns directive for normal session input with cwd', () => {
    const result = getSkillsDirective({ cwd: '/some/project', session_id: 'abc123' });
    expect(result).toBeTypeOf('string');
    expect(result).toContain('[Superpowers]');
  });
});

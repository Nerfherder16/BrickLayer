"use strict";
// src/core/skill-surface.js — Recall Skill Retriever
// Queries Recall for skills tagged 'masonry:skill' relevant to the current context.
// Never throws — returns empty result if Recall is unavailable.

const { searchMemory } = require("./recall");

/**
 * Surface relevant skills from Recall for a given query and project.
 *
 * @param {{ query: string, projectName: string, limit?: number }} opts
 * @returns {Promise<{ skills: object[], markdown: string }>}
 */
async function surfaceSkills({ query, projectName, limit = 3 }) {
  try {
    const domain = projectName ? `${projectName}-bricklayer` : undefined;

    // Two queries: same-project first, then cross-project
    const [projectResults, globalResults] = await Promise.all([
      domain
        ? searchMemory({ query, domain, tags: ["masonry:skill"], limit })
        : Promise.resolve([]),
      searchMemory({ query, tags: ["masonry:skill"], limit }),
    ]);

    // Deduplicate: prefer project-scoped results; key by skill name
    const seen = new Map();

    for (const r of projectResults) {
      const name = extractSkillName(r);
      if (name && !seen.has(name)) seen.set(name, r);
    }
    for (const r of globalResults) {
      const name = extractSkillName(r);
      if (name && !seen.has(name)) seen.set(name, r);
    }

    // Take up to `limit` deduplicated skills
    const skills = [...seen.values()].slice(0, limit).map((r) => ({
      name: extractSkillName(r) || "unknown",
      description: extractDescription(r),
      source_finding: r.source_finding || r.metadata?.source_finding || "",
      campaign: r.domain || r.metadata?.domain || "",
    }));

    if (!skills.length) {
      return { skills: [], markdown: "" };
    }

    const lines = skills.map((s) => {
      const source = s.source_finding
        ? ` (from ${s.campaign}, finding ${s.source_finding})`
        : s.campaign
          ? ` (from ${s.campaign})`
          : "";
      return `- **${s.name}**${source}: ${s.description}`;
    });

    const markdown = `## Relevant Past Skills\n${lines.join("\n")}`;
    return { skills, markdown };
  } catch (_err) {
    return { skills: [], markdown: "" };
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function extractSkillName(result) {
  // Recall memories may store skill name in tags, metadata, or content prefix
  if (result.metadata?.skill_name) return result.metadata.skill_name;
  if (Array.isArray(result.tags)) {
    const tag = result.tags.find((t) => t.startsWith("skill:"));
    if (tag) return tag.replace("skill:", "");
  }
  // Fall back to first bolded term or first line of content
  const content = result.content || result.text || "";
  const bold = content.match(/\*\*([^*]+)\*\*/);
  if (bold) return bold[1];
  return content.split(/\n/)[0].slice(0, 40).trim() || null;
}

function extractDescription(result) {
  const content = result.content || result.text || "";
  // Return first non-empty line that isn't the skill name heading
  const lines = content
    .split(/\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.length > 1 ? lines[1] : lines[0] || "";
}

module.exports = { surfaceSkills };

'use strict';

const TOOLS_CORE = [
  {
    name: 'masonry_status',
    description: 'Get current campaign state for a Masonry project',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string', description: 'Absolute path to project directory' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_findings',
    description: 'List recent findings from a Masonry campaign',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        limit: { type: 'number', default: 10 },
        verdict_filter: { type: 'string', description: 'Filter by verdict (HEALTHY, FAILURE, etc). Optional.' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_questions',
    description: 'Query the question bank for a Masonry project',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        status_filter: { type: 'string', description: 'PENDING, DONE, BLOCKED. Optional, returns all if omitted.' },
        limit: { type: 'number', default: 20 },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_run',
    description: 'Launch or resume a Masonry campaign in a detached subprocess',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        mode: { type: 'string', enum: ['new', 'resume'], default: 'resume' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_recall',
    description: 'Search Recall memory for a Masonry project domain',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        project: { type: 'string', description: 'Project name (used as domain: {project}-bricklayer)' },
        limit: { type: 'number', default: 10 },
      },
      required: ['query', 'project'],
    },
  },
  {
    name: 'masonry_weights',
    description: 'Show question priority weight report',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string', description: 'Absolute path to project directory' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_fleet',
    description: 'List fleet agents with performance scores from registry.json and agent_db.json',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        limit: { type: 'number', default: 30 },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_git_hypothesis',
    description: 'Analyze recent git commits and generate targeted BL research questions for changed code paths',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        commits: { type: 'number', default: 5, description: 'How many recent commits to analyze' },
        max_questions: { type: 'number', default: 10 },
        dry_run: { type: 'boolean', default: true, description: 'If false, appends questions to questions.md' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_nl_generate',
    description: "Generate BrickLayer research questions from a plain English description of what changed",
    inputSchema: {
      type: 'object',
      properties: {
        description: { type: 'string' },
        project_path: { type: 'string' },
        append: { type: 'boolean', default: false },
      },
      required: ['description'],
    },
  },
  {
    name: 'masonry_run_question',
    description: 'Run a single BL question by ID and return the verdict envelope',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        question_id: { type: 'string', description: "e.g. 'Q1', 'D3', 'R1.1'" },
      },
      required: ['project_path', 'question_id'],
    },
  },
  {
    name: 'masonry_run_simulation',
    description: 'Run a single simulation with given parameters and return structured results',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string', description: 'Absolute path to the project directory (contains simulate.py)' },
        months: { type: 'integer' },
        initial_units: { type: 'number' },
        monthly_growth_rate: { type: 'number' },
        churn_rate: { type: 'number' },
        price_per_unit: { type: 'number' },
        ops_cost_base: { type: 'number' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_sweep',
    description: 'Run a parameter sweep across multiple values and optionally multiple scenarios',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        param_name: { type: 'string' },
        values: { type: 'array', items: { type: 'number' } },
        scenarios: { type: 'array', items: { type: 'string' } },
        base_params: { type: 'object' },
      },
      required: ['project_path', 'param_name', 'values'],
    },
  },
];

module.exports = { TOOLS_CORE };

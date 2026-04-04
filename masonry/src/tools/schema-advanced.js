'use strict';

const TOOLS_ADVANCED = [
  {
    name: 'masonry_route',
    description: "Route a natural-language request through Masonry's 4-layer router",
    inputSchema: {
      type: 'object',
      properties: {
        request: { type: 'string' },
        project_path: { type: 'string' },
      },
      required: ['request'],
    },
  },
  {
    name: 'masonry_pattern_store',
    description: "Store a reusable build pattern to Recall under domain 'build-patterns'",
    inputSchema: {
      type: 'object',
      properties: {
        pattern_name: { type: 'string' },
        content: { type: 'string' },
        lang: { type: 'string' },
        framework: { type: 'string' },
        layer: { type: 'string' },
      },
      required: ['pattern_name', 'content', 'lang', 'framework'],
    },
  },
  {
    name: 'masonry_pattern_search',
    description: 'Search build patterns stored in Recall',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        lang: { type: 'string' },
        framework: { type: 'string' },
        limit: { type: 'number', default: 5 },
      },
      required: ['query'],
    },
  },
  {
    name: 'masonry_worker_status',
    description: 'Query the state of Masonry background daemon workers',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_task_assign',
    description: 'Atomically claim the next PENDING task from .autopilot/progress.json',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        worker_id: { type: 'string' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_agent_health',
    description: 'Get per-agent performance metrics',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        agent_name: { type: 'string' },
        sort_by: { type: 'string', default: 'score' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_wave_validate',
    description: 'Validate that all tasks in a build wave are DONE before advancing',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        wave_task_ids: { type: 'array', items: { type: 'number' } },
      },
      required: ['project_path', 'wave_task_ids'],
    },
  },
  {
    name: 'masonry_swarm_init',
    description: 'Initialize .autopilot/progress.json for a swarm build from a spec',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        spec_path: { type: 'string' },
        project_name: { type: 'string' },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_consensus_check',
    description: 'Quorum gate for destructive operations',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        action: { type: 'string' },
        mode: { type: 'string', default: 'check' },
        approved_by: { type: 'string' },
      },
      required: ['project_path', 'action'],
    },
  },
  {
    name: 'masonry_doctor',
    description: 'System health check: Recall, daemons, hooks, registry, training data',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
      },
      required: [],
    },
  },
  {
    name: 'masonry_verify_7point',
    description: '7-point quality gate: unit tests, coverage, integration, e2e, security, perf, docker',
    inputSchema: {
      type: 'object',
      properties: {
        project_dir: { type: 'string' },
      },
      required: ['project_dir'],
    },
  },
  {
    name: 'masonry_pattern_decay',
    description: 'Apply time decay to pattern confidence scores and prune below 0.2 threshold',
    inputSchema: {
      type: 'object',
      properties: {
        project_dir: { type: 'string' },
      },
      required: ['project_dir'],
    },
  },
  {
    name: 'masonry_pattern_promote',
    description: 'Promote an agent pattern confidence (ceiling-approached: conf + 0.2 * (1 - conf))',
    inputSchema: {
      type: 'object',
      properties: {
        agent_type: { type: 'string' },
        project_dir: { type: 'string' },
      },
      required: ['agent_type', 'project_dir'],
    },
  },
  {
    name: 'masonry_pattern_demote',
    description: 'Demote an agent pattern confidence (proportional reduction: conf - 0.15 * conf, floor 0.1)',
    inputSchema: {
      type: 'object',
      properties: {
        agent_type: { type: 'string' },
        project_dir: { type: 'string' },
      },
      required: ['agent_type', 'project_dir'],
    },
  },
  {
    name: 'masonry_training_update',
    description: 'Recompute EMA strategy scores from masonry/telemetry.jsonl',
    inputSchema: {
      type: 'object',
      properties: {
        telemetry_path: { type: 'string' },
      },
    },
  },
  {
    name: 'masonry_reasoning_query',
    description: 'Query ReasoningBank for top-k patterns matching a query string',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        top_k: { type: 'number' },
        domain: { type: 'string' },
      },
      required: ['query'],
    },
  },
  {
    name: 'masonry_reasoning_store',
    description: 'Store a new pattern in ReasoningBank',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string' },
        domain: { type: 'string' },
        pattern_id: { type: 'string' },
      },
      required: ['content'],
    },
  },
  {
    name: 'masonry_graph_record',
    description: 'Record pattern co-citations as CITES edges in Neo4j after a task succeeds',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: { type: 'string' },
        pattern_ids: { type: 'array', items: { type: 'string' } },
        project: { type: 'string' },
      },
      required: ['task_id', 'pattern_ids'],
    },
  },
  {
    name: 'masonry_pagerank_run',
    description: 'Run PageRank on the pattern citation graph for a project',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string' },
        confidence_path: { type: 'string' },
      },
      required: ['project'],
    },
  },
  {
    name: 'masonry_set_strategy',
    description: 'Set the execution strategy for the active autopilot build',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        strategy: { type: 'string', enum: ['conservative', 'balanced', 'aggressive'] },
      },
      required: ['project_path', 'strategy'],
    },
  },
  {
    name: 'masonry_claim_add',
    description: 'File a human-input claim to .autopilot/claims.json and continue the build',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        question: { type: 'string' },
        task_id: { type: 'string' },
        context: { type: 'string' },
      },
      required: ['project_path', 'question'],
    },
  },
  {
    name: 'masonry_claim_resolve',
    description: 'Resolve a pending claim in .autopilot/claims.json with an answer',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        claim_id: { type: 'string' },
        answer: { type: 'string' },
      },
      required: ['project_path', 'claim_id', 'answer'],
    },
  },
  {
    name: 'masonry_claims_list',
    description: 'List claims from .autopilot/claims.json, filtered by status',
    inputSchema: {
      type: 'object',
      properties: {
        project_path: { type: 'string' },
        status: { type: 'string', enum: ['pending', 'resolved', 'all'] },
      },
      required: ['project_path'],
    },
  },
  {
    name: 'masonry_review_consensus',
    description: 'Resolve conflicting review verdicts via weighted majority vote',
    inputSchema: {
      type: 'object',
      properties: {
        votes: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              reviewer: { type: 'string' },
              verdict: { type: 'string', enum: ['APPROVED', 'BLOCKED', 'NEEDS_REVISION'] },
              confidence: { type: 'number' },
              summary: { type: 'string' },
            },
            required: ['reviewer', 'verdict', 'confidence', 'summary'],
          },
        },
        task_id: { type: 'string' },
        project_dir: { type: 'string' },
      },
      required: ['votes', 'task_id', 'project_dir'],
    },
  },
];

module.exports = { TOOLS_ADVANCED };

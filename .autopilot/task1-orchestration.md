# Ruflo Agent Orchestration Analysis

Task: Analyze Ruflo's agent orchestration.

Date: 2026-03-27  
Status: Complete

## 1. Swarm Spawning Mechanism

Ruflo spawns swarms using three-phase initialization:

Phase 1: Swarm Initialization
- Command: mcp__ruflo__swarm_init --topology <type> --max-agents <number>
- Topologies: hierarchical, mesh, ring, star
- Strategies: auto, manual, adaptive
- Output: .swarm/ directory with config.json, state.json

Phase 2: Agent Spawning
- Command: mcp__ruflo__agent_spawn <type> --task <desc> --capabilities <list>
- Creates records in agents.json with status, task assignment, capabilities
- Headless mode uses CLAUDE_ENTRYPOINT env var
- Model aliases instead of dated IDs, PID singleton for daemon

Phase 3: Coordination & Execution
- mcp__ruflo__task_create -> task_assign -> state.json update
- State persistence with real MCP calls (v3.5.43+)
- SIGKILL fallback for aggressive termination

Key Detail (v3.5.43+):
- Fixed metadata-only bug from v3.5.42
- Now spawns actual Claude subprocesses for task execution
- Syncs agent state across task lifecycle

## 2. Coordinator -> Worker Topology

Hierarchical (Queen Model):
- Central coordinator breaks down objectives into subtasks
- Specialized worker agents by type (researcher, coder, analyst, tester)
- Memory coordination protocol with cross-referenced state
- Automatic task assignment based on capability match

Memory Coordination:
- swarm/hierarchical/status: initial status
- swarm/hierarchical/progress: progress updates
- swarm/shared/hierarchy: command structure
- swarm/worker-*/status: check worker status
- swarm/hierarchical/complete: signal completion

Mesh (Peer-to-Peer):
- Direct agent-to-agent coordination
- No central bottleneck
- Gossip-protocol based
- Better for distributed scenarios

Adaptive:
- Topology adjusts based on workload
- Switches between hierarchical, mesh, ring dynamically
- Auto-optimization enabled

Coordinator Responsibilities:
1. Strategic Planning: Decompose objectives into work packages
2. Task Assignment: Match tasks to workers by capability/history/load
3. Supervision: Status check-ins, cross-team coordination, escalation
4. Resource Management: Dynamic agent pool scaling

## 3. TeammateIdle & TaskCompleted Usage

TeammateIdle Hook:
- Triggers when agent finishes task and becomes idle
- Called periodically (5000ms per swarm_monitor)
- Triggers task queue polling
- Checks for pending work assignments
- Updates agent status in agents.json
- Enables load balancing

Implementation (v3.5.42+):
- task_assign: sets agent.status=active, currentTask=taskId
- task_complete: sets agent.status=idle, currentTask=null, increments taskCount

TaskCompleted Hook:
- Triggers when task finishes
- Updates status: in_progress -> completed
- Increments agent.taskCount
- Triggers dependent tasks
- Writes completion event to memory

Cross-System Linkage (v3.5.42 fix):
- Before: task_complete wrote to tasks/store.json only, agents.json stayed out of sync
- After: Atomic sync across both files on assignment/completion

Real Metrics (v3.5.42 fix):
- Before: queen.load = 0.3 + Math.random() * 0.4
- After: queen.load = activeTaskCount / workerCount

## 4. Task Queue Data Structure

Storage: JSON-based CRUD (not traditional FIFO)

Location: .swarm/tasks/store.json

Schema:
- id: unique task ID
- description: task description
- status: pending|in_progress|completed|failed
- priority: low|medium|high|critical
- type: feature|bugfix|refactor|test
- assignedTo: array of agent IDs
- timestamps: createdAt, startedAt, completedAt
- progress: 0-100 percentage
- output: task results
- error: error message if failed
- dependencies: other task IDs
- metadata: duration, capabilities, subtasks

Task Lifecycle:
pending -> task_assign -> in_progress -> task_complete -> completed

Query/Assignment:
- v3.5.43+ uses real MCP calls + state persistence
- Queen reads task store and assigns round-robin to workers
- Workers read task description and execute via Claude CLI
- task_complete triggers next queued task

## 5. Max Concurrency Controls

Global Limits:
- Max agents per swarm: 50 (hard limit)
- Agent spawning: 100/min
- Task orchestration: 50/min
- Max task duration: 6 hours
- Max workflow complexity: 100 steps

Per-Swarm:
- --max-agents 8 (default), max 50

Per-Task:
- --max-concurrent 5 (limit parallel tasks)

Enforcement:
1. Swarm init sets maxAgents, prevents spawning beyond limit
2. Task queue throttling with max-concurrent parameter
3. Memory pool allocation with TTL per namespace
4. Load balancing considers workload, adaptive auto-scales

Topology-Specific:
- Hierarchical: Queen coordinates up to maxAgents (single point of contention)
- Mesh: O(n^2) communication complexity
- Ring: O(n) broadcast latency
- Star: Central bottleneck like hierarchical

## 6. BrickLayer Differences

BrickLayer Advantages:
1. State abstraction: .autopilot/progress.json for coordination
2. Deterministic execution: Question bank with explicit ordering
3. Explicit task assignment: masonry_task_assign() with pre-allocated pool
4. Memory system: Recall (Qdrant + Neo4j) with semantic search
5. No metadata-only bugs: Direct agent invocation via /build skill

Ruflo Gaps vs BrickLayer:
1. No execution engine until v3.5.43
2. No built-in consensus mechanism
3. Synchronous task processing (polling)
4. Lossy state checkpointing
5. Memory cross-referencing overhead

BrickLayer Could Learn:
1. Topology optimization (hierarchical, mesh, ring, star)
2. Neural pattern training with WASM SIMD
3. Hooks API design (PreToolUse/PostToolUse)

## 7. Critical Issues Fixed

Issue #1423: Agents Never Execute Work (FIXED v3.5.43)
- Problem: Spawned agents never executed tasks
- Root cause: No execution engine, only metadata
- Fix: Real MCP calls + state persistence

Issue #1392: Worker Tracking Non-Functional (FIXED v3.5.42)
- Problem: task_assign/task_complete didn't sync agents/tasks
- Root cause: Separate file systems, zero cross-references
- Fix: Atomic state sync on assignment/completion

Issue #1397: Task Lifecycle Never Syncs
- Problem: Queen load = Math.random(), workers always idle
- Root cause: No task queue to agent connection
- Fix: Real metrics (activeTaskCount / workerCount)

## Conclusion

Ruflo is topology-flexible but state-fragile. Strength: hierarchical coordinator + multi-agent specialization. Weakness: flat JSON CRUD design decoupling tasks from agents (fixed v3.5.42-43).

BrickLayer is more explicit and deterministic. Ruflo offers more topology flexibility.

Recommended: Adopt Ruflo's topology selection with BrickLayer's deterministic task model.

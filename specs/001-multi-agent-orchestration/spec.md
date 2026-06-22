# Feature Specification: Multi-Agent Orchestration

**Feature Branch**: `001-multi-agent-orchestration`

**Created**: 2026-06-21

**Status**: Implemented (Retroactive Specification)

**Input**: User description: "Documenta como spec oficial de Spec Kit la feature de orquestación multi-agente que ya existe en este repo: worktree isolation por agente, shared task queue con single-writer lock vía SQLite BEGIN IMMEDIATE, y coordinación vía tmux."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Distributed Task Processing (Priority: P1)

Multiple autonomous agents must be able to claim and process tasks from a shared queue without conflicts, enabling parallel execution of independent work items.

**Why this priority**: This is the core value proposition - parallel task execution is the fundamental capability that enables all other scenarios. Without this, the system cannot function.

**Independent Test**: Can be fully tested by spawning multiple agents, enqueuing tasks, and verifying that each task is claimed by exactly one agent and completed exactly once. Delivers immediate value by enabling concurrent work.

**Acceptance Scenarios**:

1. **Given** a shared task queue with 10 pending tasks, **When** 3 agents are spawned simultaneously, **Then** each agent claims tasks without conflicts, all 10 tasks are processed exactly once, and no task is processed by multiple agents
2. **Given** an agent has claimed a task, **When** the agent completes the task, **Then** the task status updates to "completed" with the result payload, and the task is no longer available for claiming
3. **Given** multiple agents attempting to claim the same task concurrently, **When** the claim operations execute, **Then** exactly one agent successfully claims the task, and all other agents receive no task or claim a different pending task

---

### User Story 2 - Isolated Agent Workspaces (Priority: P2)

Each agent must operate in its own isolated git worktree to prevent file system conflicts and enable independent development workflows.

**Why this priority**: Workspace isolation is essential for safe parallel execution, but depends on having a task distribution mechanism (P1) to be useful. It's the second-most critical capability for production multi-agent systems.

**Independent Test**: Can be tested by spawning agents, verifying each has a unique worktree path, and confirming that file modifications in one worktree do not affect other worktrees. Delivers value by enabling safe concurrent file operations.

**Acceptance Scenarios**:

1. **Given** a spawn request for N agents, **When** the orchestration system initializes, **Then** N separate git worktrees are created at unique paths (e.g., `worktrees/agent-1`, `worktrees/agent-2`)
2. **Given** an agent modifies files in its worktree, **When** other agents are operating, **Then** those modifications are isolated and do not appear in other agents' worktrees
3. **Given** an existing worktree for an agent, **When** the agent is respawned, **Then** the existing worktree is reused rather than creating a duplicate

---

### User Story 3 - Visual Agent Coordination (Priority: P3)

Operators must be able to monitor and interact with multiple agents simultaneously through a multiplexed terminal interface.

**Why this priority**: Visibility and debuggability are important for operational confidence, but the system can function without visual monitoring. This is a quality-of-life feature built on top of the core orchestration capabilities.

**Independent Test**: Can be tested by spawning agents with tmux coordination, verifying that each agent appears in a separate tmux pane, and confirming that operators can view all agents simultaneously. Delivers value through improved observability.

**Acceptance Scenarios**:

1. **Given** a request to spawn N agents, **When** the spawn script executes, **Then** a tmux session is created with N panes, each pane running one agent worker
2. **Given** agents are running in tmux panes, **When** an operator attaches to the session, **Then** all agent outputs are visible simultaneously in a tiled layout
3. **Given** a tmux session with running agents, **When** the operator detaches and reattaches, **Then** the session persists and agents continue running

---

### Edge Cases

- What happens when an agent crashes after claiming a task but before completing it? (Task remains in "claimed" state; requires manual intervention or timeout-based recovery)
- How does the system handle concurrent task queue initialization by multiple agents? (SQLite `CREATE TABLE IF NOT EXISTS` with isolation_level=None handles concurrent initialization safely)
- What happens if an agent attempts to claim a task when none are pending? (Agent receives `None` and can poll or wait)
- How does the system handle worktree creation race conditions when multiple spawn attempts occur? (Git worktree operations are atomic; `git worktree add` will fail if the worktree already exists)
- What happens when the SQLite database is locked during a claim operation? (Connection timeout of 30 seconds is configured; operations will retry or fail after timeout)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a shared task queue accessible to multiple concurrent agents with conflict-free task claiming
- **FR-002**: System MUST ensure that each task is claimed by at most one agent using database-level locking (SQLite `BEGIN IMMEDIATE` transactions)
- **FR-003**: System MUST support task lifecycle states: pending, claimed, completed
- **FR-004**: System MUST create isolated git worktrees for each agent to prevent file system conflicts
- **FR-005**: System MUST coordinate agent execution through tmux session management for observability
- **FR-006**: System MUST allow agents to enqueue new tasks with arbitrary JSON payloads
- **FR-007**: System MUST track which agent claimed each task and when it was last updated
- **FR-008**: System MUST support atomic task claiming operations with SELECT-UPDATE semantics within a transaction
- **FR-009**: System MUST persist task queue state across agent restarts using SQLite database
- **FR-010**: System MUST provide a mechanism to seed the task queue with initial tasks before agents start
- **FR-011**: System MUST create database indexes on (status, id) for efficient pending task queries
- **FR-012**: System MUST use UTC timestamps for all task update tracking
- **FR-013**: System MUST support configurable queue database path, session name, and agent count
- **FR-014**: System MUST synchronize agent startup using a start signal file to prevent premature task claiming

### Key Entities

- **Task**: Represents a unit of work with id, status, assigned_agent, payload (JSON), result (JSON), and updated_at timestamp
- **Agent**: An autonomous worker with a unique agent_id, isolated worktree path, and connection to the shared task queue
- **Worktree**: A git worktree instance providing file system isolation for an agent's operations
- **Queue Database**: SQLite database persisting task queue state, shared read-write by all agents

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully processes tasks in parallel with N agents claiming and completing tasks without conflicts (verified by no duplicate task completions)
- **SC-002**: Task claiming operations complete within 100ms under normal load (no contention) and within 30 seconds under high contention (connection timeout)
- **SC-003**: Zero data corruption or race conditions when 10+ agents claim tasks concurrently from a queue with 100+ tasks
- **SC-004**: Operators can spawn and monitor N agents within 5 seconds, with all agents visible in tiled tmux layout
- **SC-005**: Each agent operates in an isolated worktree with zero cross-contamination of file changes between agents
- **SC-006**: Task queue state persists across agent restarts with 100% consistency (no lost or duplicate tasks)

## Assumptions

- Agents operate on a single machine with shared file system access to the repository and queue database
- SQLite provides sufficient concurrency control for the target agent count (typically 3-10 agents)
- Tmux is available in the execution environment for visual coordination
- Git worktree support is available (Git 2.5+)
- Agents are trusted components; no adversarial agent behavior is anticipated
- Task payloads are JSON-serializable and self-contained (no external dependencies required to understand the task)
- Network file systems (NFS, etc.) are not used; local file system performance is assumed
- Task processing is idempotent or agents implement their own retry/recovery logic
- Operators have terminal access to attach to tmux sessions for monitoring

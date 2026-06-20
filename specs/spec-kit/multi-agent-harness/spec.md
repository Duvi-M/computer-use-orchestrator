# Feature Specification: Multi-Agent Harness

**Feature Branch**: `spec-kit/multi-agent-harness`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: Existing spec `specs/multi-agent-harness.md`

## User Scenarios & Testing

### Primary User Story

As a harness engineer, I want to demonstrate multiple local agents working in
parallel from isolated git worktrees while claiming tasks from a shared queue
with a single-writer lock so that agents do not overwrite each other’s files or
double-assign the same task.

### Acceptance Scenarios

1. **Given** an operator runs `scripts/spawn_agents.sh 3`, **When** no tmux
   session exists, **Then** the script creates or reuses three git worktrees and
   opens a tmux session with three panes.
2. **Given** the tmux session already exists, **When** the operator runs
   `scripts/spawn_agents.sh 3` again, **Then** the script attaches instead of
   creating a duplicate session.
3. **Given** multiple agents claim tasks concurrently, **When** the SQLite queue
   uses `BEGIN IMMEDIATE`, **Then** each pending task is claimed by at most one
   agent.
4. **Given** an agent completes a task, **When** the worker marks it complete,
   **Then** the queue records status, agent id, result, and updated timestamp.
5. **Given** an agent writes output, **When** it writes a dummy result, **Then**
   the file lands inside that agent’s own worktree.

### Edge Cases

- Existing worktree should be reused.
- Existing tmux session should be attached.
- No pending tasks should cause workers to sleep and retry.
- Concurrent claims should not double-assign a task.
- Dirty worktree should remain isolated to that agent’s directory.
- `tmux` may be unavailable in some CI/dev environments.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide `scripts/spawn_agents.sh`.
- **FR-002**: The spawn script MUST accept an optional number of agents with
  default `3`.
- **FR-003**: The spawn script MUST create or reuse git worktrees under
  `./worktrees/agent-N`.
- **FR-004**: The spawn script MUST launch one tmux pane per agent.
- **FR-005**: Each pane MUST run `scripts/agent_worker.py` with `agent_id` and
  worktree path.
- **FR-006**: The shared queue MUST be backed by SQLite at `data/task_queue.db`
  by default.
- **FR-007**: The queue MUST expose `claim_next_task(agent_id)` using
  `BEGIN IMMEDIATE`.
- **FR-008**: The queue MUST expose `complete_task(task_id, result)`.
- **FR-009**: Concurrent claims MUST NOT assign the same task twice.
- **FR-010**: Runtime/demo artifacts MUST stay out of git.

### Key Entities

- **Agent Worktree**: Isolated git checkout for one local agent.
- **Agent Worker**: Loop that claims tasks, writes a result in its worktree, and
  completes the task.
- **Shared Task Queue**: SQLite database coordinating task ownership.
- **Task**: Queue row with id, status, assigned agent, payload, result, and
  timestamp.
- **Single-Writer Lock**: SQLite transaction boundary created by
  `BEGIN IMMEDIATE`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A concurrency test with five claimers verifies no duplicate task
  assignment.
- **SC-002**: `scripts/agent_worker.py` can claim and complete a seeded task.
- **SC-003**: `scripts/spawn_agents.sh` passes shell syntax validation.
- **SC-004**: `worktrees/` is ignored by git.
- **SC-005**: The design is documented in `specs/multi-agent-harness.md` and
  this Spec Kit version.

## Assumptions

- The demo is local only and not a distributed scheduler.
- SQLite locking is sufficient for one-machine local demos.
- Production would require stronger coordination if agents run across hosts.
- Worktree branches can be named `agent/agent-N`.

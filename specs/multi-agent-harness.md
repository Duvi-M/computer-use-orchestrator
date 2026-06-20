# Multi-Agent Harness

## Problem

Parallel agents can interfere with each other if they share a working directory
or claim the same unit of work. A serious harness needs isolated execution
surfaces and a single-writer coordination point.

## Goals

- Demonstrate one git worktree per agent.
- Run several agent workers in tmux panes.
- Share tasks through a SQLite-backed queue.
- Use `BEGIN IMMEDIATE` so only one writer claims a task at a time.
- Avoid double assignment under concurrent claims.

## Non-Goals

- Distributed queue.
- Kubernetes scheduler.
- Multi-agent reasoning framework.
- Cross-agent memory graph.
- Production locking across multiple hosts.

## Architecture

- `scripts/spawn_agents.sh` creates `./worktrees/agent-N` using
  `git worktree add`.
- Each tmux pane runs `scripts/agent_worker.py` in its own worktree.
- `computer_use_demo/harness/shared_task_queue.py` stores tasks in
  `data/task_queue.db`.
- `claim_next_task(agent_id)` opens a SQLite transaction with
  `BEGIN IMMEDIATE`, selects one pending task, and marks it claimed before
  committing.

## Edge Cases

- Existing worktree: the spawn script reuses it.
- Existing tmux session: the spawn script attaches instead of creating another.
- No pending tasks: workers sleep and retry.
- Concurrent claims: SQLite serializes writers, so one task cannot be claimed
  by two agents.
- Dirty worktree: isolation prevents one agent's generated files from landing
  in another agent's directory.

## Acceptance Criteria

- N agents can be launched into N tmux panes.
- Each agent has a separate `worktrees/agent-N` working directory.
- Shared queue claims are atomic under concurrent threads.
- Completed tasks record an agent id and output path.
- Tests verify no task is claimed twice.

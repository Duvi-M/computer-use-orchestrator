# Implementation Plan: Multi-Agent Harness

**Branch**: `spec-kit/multi-agent-harness` | **Date**: 2026-06-20 | **Spec**:
`specs/spec-kit/multi-agent-harness/spec.md`

## Summary

Demonstrate parallel agent orchestration with local git worktree isolation and a
SQLite shared task queue. Each agent runs in its own tmux pane and worktree.
The queue uses `BEGIN IMMEDIATE` to serialize writers and prevent duplicate task
claims.

## Technical Context

**Language/Version**: Python 3.11 recommended; shell scripts use Bash  
**Primary Dependencies**: Python stdlib `sqlite3`, `json`, `argparse`, `tmux`,
git worktrees  
**Storage**: SQLite queue at `data/task_queue.db`; worktree-local output files  
**Testing**: `pytest`, `ruff`, `bash -n scripts/spawn_agents.sh`  
**Target Platform**: Local developer machine with git and tmux installed  
**Project Type**: Local harness demo script plus Python task queue module  
**Performance Goals**: Deterministic local demo; claim operations serialized by
SQLite  
**Constraints**: No distributed queue, Redis/Celery, Kubernetes, or production
multi-host locking  
**Scale/Scope**: Local demo with N panes/agents on one machine

## Constitution Check

- **No heavy infra**: PASS. Uses SQLite, tmux, and git worktrees.
- **No orchestrator rewrite**: PASS. FastAPI path is untouched.
- **Local demo only**: PASS. Production scheduler is explicitly non-goal.
- **Single writer**: PASS. `BEGIN IMMEDIATE` serializes claim writes.
- **Isolation**: PASS. Worktree per agent avoids shared working directory
  conflicts.

## Project Structure

```text
computer_use_demo/harness/
  shared_task_queue.py
scripts/
  spawn_agents.sh
  agent_worker.py
tests/
  test_shared_task_queue.py
worktrees/
  agent-1/        # generated, ignored
  agent-2/        # generated, ignored
data/
  task_queue.db   # generated, ignored
```

## Phase 0: Research

- Confirm git worktree commands can be run from repo root.
- Confirm tmux can create panes with per-pane working directories.
- Confirm SQLite `BEGIN IMMEDIATE` is enough for one-machine single-writer
  local coordination.

## Phase 1: Design

- Define task schema: id, status, assigned_agent, payload, result, updated_at.
- Define claim flow: begin immediate, select pending, update claimed, commit.
- Define complete flow: update completed with result payload.
- Define worker output path inside worktree.

## Phase 2: Implementation

- Implement `shared_task_queue.py`.
- Implement `agent_worker.py`.
- Implement `spawn_agents.sh`.
- Ignore generated `worktrees/`.
- Add spec documentation.

## Phase 3: Verification

- Test five concurrent claimers against the same task queue.
- Validate shell syntax with `bash -n`.
- Validate worker can claim and complete a seeded task.
- Run repository lint and test commands.

## Complexity Tracking

This feature intentionally avoids distributed execution. Any cross-host queue,
agent scheduling service, shared memory graph, or production lock manager must
be tracked as separate future work.

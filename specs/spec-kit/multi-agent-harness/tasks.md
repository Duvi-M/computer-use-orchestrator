# Tasks: Multi-Agent Harness

**Input**: `specs/spec-kit/multi-agent-harness/spec.md` and
`specs/spec-kit/multi-agent-harness/plan.md`

## Phase 1: Setup

- [x] T001 Confirm existing harness package location.
- [x] T002 Add `worktrees/` to `.gitignore`.
- [x] T003 Keep original `specs/multi-agent-harness.md` unchanged.

## Phase 2: Shared Queue

- [x] T004 Create `computer_use_demo/harness/shared_task_queue.py`.
- [x] T005 Add SQLite schema for `tasks`.
- [x] T006 Implement `enqueue_task(payload)`.
- [x] T007 Implement `claim_next_task(agent_id)` with `BEGIN IMMEDIATE`.
- [x] T008 Implement `complete_task(task_id, result)`.
- [x] T009 Implement `list_tasks()` for tests/debugging.

## Phase 3: Agent Worker

- [x] T010 Create `scripts/agent_worker.py`.
- [x] T011 Parse `agent_id`, worktree path, queue DB path, idle sleep, and
  optional max task count.
- [x] T012 Claim tasks in a loop.
- [x] T013 Write dummy output under the agent worktree.
- [x] T014 Mark task complete with agent id and output path.

## Phase 4: Worktree/Tmux Spawner

- [x] T015 Create `scripts/spawn_agents.sh`.
- [x] T016 Accept optional agent count with default `3`.
- [x] T017 Create or reuse `./worktrees/agent-N`.
- [x] T018 Create or attach tmux session.
- [x] T019 Launch one pane per agent with working directory set to its worktree.
- [x] T020 Seed demo tasks by default with `SEED_TASKS`.

## Phase 5: Tests

- [x] T021 Add concurrency test for five claimers.
- [x] T022 Verify no task id is claimed twice.
- [x] T023 Verify claimed rows have unique assigned agents.

## Phase 6: Docs & Validation

- [x] T024 Add `specs/multi-agent-harness.md`.
- [x] T025 Add this Spec Kit version under `specs/spec-kit/multi-agent-harness/`.
- [x] T026 Run `bash -n scripts/spawn_agents.sh`.
- [x] T027 Run `ruff check computer_use_demo tests scripts evals`.
- [x] T028 Run `python3 -B -m pytest -q`.

## Dependencies

- T007 depends on T005.
- T010-T014 depend on T004-T008.
- T015-T020 depend on T010-T014.
- T021-T023 depend on T004-T008.

## Parallel Example

T010-T014 and T021-T023 can be implemented in parallel after the shared queue
API is defined.

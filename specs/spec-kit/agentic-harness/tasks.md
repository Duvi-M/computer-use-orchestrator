# Tasks: Agentic Harness

**Input**: `specs/spec-kit/agentic-harness/spec.md` and
`specs/spec-kit/agentic-harness/plan.md`

## Phase 1: Setup

- [x] T001 Identify existing FastAPI orchestrator, WorkerLauncher, SSE,
  noVNC, persistence, and test boundaries.
- [x] T002 Create `computer_use_demo/harness/` package.
- [x] T003 Keep original specs under `specs/*.md` unchanged.

## Phase 2: Harness Primitives

- [x] T004 Add loop primitives in `computer_use_demo/harness/loop.py`.
- [x] T005 Add budget model in `computer_use_demo/harness/budgets.py`.
- [x] T006 Add tool grants in `computer_use_demo/harness/tool_grants.py`.
- [x] T007 Add eval gates in `computer_use_demo/harness/eval_gates.py`.
- [x] T008 Add trigger dispatcher in `computer_use_demo/harness/triggers.py`.
- [x] T009 Add execution contracts in `computer_use_demo/harness/contracts.py`.
- [x] T010 Add durable trace store in `computer_use_demo/harness/traces.py`.
- [x] T011 Add optional mem0 memory wrapper in
  `computer_use_demo/harness/memory.py`.

## Phase 3: Independent CLIs & Evals

- [x] T012 Add durable loop runner in `computer_use_demo/harness/runner.py`.
- [x] T013 Add tmux wrapper script `scripts/run_harness_tmux.sh`.
- [x] T014 Add offline eval runner under `evals/`.
- [x] T015 Add safe parallel session/workflow demos under `scripts/`.

## Phase 4: Tests

- [x] T016 Add tests for loop state transitions.
- [x] T017 Add tests for budget exceeded behavior.
- [x] T018 Add tests for tool grants allowed/denied.
- [x] T019 Add tests for eval gate pass/fail.
- [x] T020 Add tests for contract validation.
- [x] T021 Add tests for trace persistence.
- [x] T022 Add tests for runner checkpoint reload.
- [x] T023 Add tests for mem0 wrapper with mocked client.

## Phase 5: Docs

- [x] T024 Update README with “Why this is a Harness”.
- [x] T025 Add specs for agentic harness, budgets, evals, traces, workflows,
  triggers, escalation, contracts, and worker isolation.
- [x] T026 Add interview demo instructions.
- [x] T027 Document roadmap items honestly.

## Phase 6: Validation

- [x] T028 Run `ruff check computer_use_demo tests scripts evals`.
- [x] T029 Run `python3 -B -m pytest -q`.
- [x] T030 Run `node --check web/app.js`.
- [x] T031 Run `python3 -m py_compile migrations/versions/*.py`.
- [x] T032 Run `make db-migrate`.

## Dependencies

- T004-T011 depend on T002.
- T012-T015 depend on harness primitives.
- T016-T023 depend on implementation tasks.
- T024-T027 depend on feature shape being stable.
- T028-T032 depend on implementation and tests.

## Parallel Example

Tasks T005-T008 can be done in parallel because budgets, grants, eval gates, and
triggers are independent modules.

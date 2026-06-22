# Implementation Plan: Agentic Harness

**Branch**: `spec-kit/agentic-harness` | **Date**: 2026-06-20 | **Spec**:
`specs/spec-kit/agentic-harness/spec.md`

## Summary

Represent the existing Computer Use orchestrator as an agentic harness without
rewriting the system. Keep FastAPI, SSE, one Docker worker per session,
noVNC, SQLite/PostgreSQL persistence, WorkerLauncher, limits, retention, and
observability intact. Add or document harness primitives for loop state,
contracts, budgets, grants, eval gates, triggers, memory, traces, and
escalation.

## Technical Context

**Language/Version**: Python 3.11 recommended; tests also run on local newer
Python where dependencies support it  
**Primary Dependencies**: FastAPI, httpx, SQLite stdlib, Alembic, SQLAlchemy,
psycopg, Anthropic SDK, mem0ai optional/local memory  
**Storage**: SQLite local default; PostgreSQL via `DATABASE_URL`; local JSON
traces/checkpoints under `data/`  
**Testing**: `pytest`, `ruff`, `node --check web/app.js`,
`python -m py_compile migrations/versions/*.py`  
**Target Platform**: Local developer machine with Docker for live worker demo  
**Project Type**: Single Python/FastAPI service plus static frontend and worker
image  
**Performance Goals**: No added latency on existing FastAPI routes unless
harness primitives are explicitly invoked  
**Constraints**: Do not rewrite FastAPI, replace SSE, change worker execution,
add Redis/Celery/Kubernetes, or require live Anthropic/Postgres in tests  
**Scale/Scope**: Local production-style prototype; one worker per session

## Constitution Check

- **No rewrite**: PASS. The harness wraps concepts and tests around existing
  flow.
- **Preserve worker path**: PASS. Claude Computer Use stays inside worker.
- **Local demo compatibility**: PASS. Browser demo does not require new setup.
- **No heavy infra**: PASS. No queue, Kubernetes, or object storage added.
- **Evidence over claims**: PASS. Eval gates and traces support evidence-based
  completion.

## Project Structure

```text
computer_use_demo/
  api/
  harness/
    loop.py
    contracts.py
    budgets.py
    tool_grants.py
    eval_gates.py
    triggers.py
    traces.py
    memory.py
evals/
scripts/
specs/
tests/
web/
```

## Phase 0: Research

- Confirm current session lifecycle, ownership, limits, launcher, retention,
  and observability tests.
- Confirm harness primitives remain independent from FastAPI route handlers.
- Confirm memory and eval functionality can fail soft in local/CI mode.

## Phase 1: Design & Contracts

- Define loop primitives: `Goal`, `Plan`, `AgentAction`, `Observation`,
  `Evidence`, `EscalationDecision`.
- Define `ExecutionContract` for required outputs, budgets, grants,
  completion conditions, evidence paths, and escalation policy.
- Define `RawTrace` and `TraceStore` for local durable traces.
- Define `HarnessMemory` wrapper around file-backed local memory, with optional
  mem0 backend when a valid OpenAI key is present.

## Phase 2: Implementation

- Implement harness modules under `computer_use_demo/harness/`.
- Keep FastAPI and worker code path unchanged.
- Add runner/demo scripts only where they are independent CLIs.
- Update README/docs/specs to explain harness boundaries.

## Phase 3: Verification

- Unit-test loop transitions, budgets, grants, eval gates, triggers, contracts,
  traces, memory, and checkpoint reload.
- Run offline eval and demo scripts.
- Run repository test/lint/compile commands.

## Complexity Tracking

No additional complexity exceptions accepted for this feature. Any live
multi-agent runtime, distributed queue, remote launcher, object store, or
temporal knowledge graph remains roadmap work.

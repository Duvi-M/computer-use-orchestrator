# Agentic Harness

## Problem

Computer-use agents are stateful, expensive, and capable of affecting a remote
desktop. A simple API wrapper does not provide enough control for lifecycle,
evidence, safety, observability, and recovery.

## Goals

- Represent the loop: goal -> plan -> action -> observation/evidence ->
  evaluation -> next step/escalation.
- Keep one isolated worker per session.
- Persist messages, events, status, and artifacts.
- Make budgets, tool grants, eval gates, and triggers explicit.
- Preserve the current Claude Computer Use execution path.

## Non-Goals

- Build a new planner or model runtime.
- Add multi-agent scheduling yet.
- Add a production memory graph yet.
- Replace FastAPI, SSE, Docker workers, or noVNC.

## Architecture

- FastAPI orchestrator owns session APIs and ownership checks.
- WorkerLauncher owns worker lifecycle.
- Docker worker runs Claude Computer Use and desktop tooling.
- Harness primitives in `computer_use_demo/harness/` describe agent-loop,
  budget, grant, eval, trigger, and escalation concepts.

## Data Flow

1. User creates a session.
2. Orchestrator launches one worker.
3. User sends a goal/message.
4. Worker emits SSE events and screenshots.
5. Orchestrator persists events and metadata.
6. Eval gates verify evidence and status.
7. Limits or errors can trigger escalation or stop policies.

## Edge Cases

- Worker does not become ready.
- Session exceeds runtime, idle, message, or event budgets.
- noVNC access is requested by a non-owner.
- Evidence is missing or an eval gate fails.
- Orchestrator restarts while workers are active.

## Acceptance Criteria

- A session can be created, messaged, streamed, viewed, and deleted.
- Ownership checks block cross-user access.
- Budgets are represented in config and harness tests.
- Tool grants and eval gates are documented and unit-tested.
- The README explains why this is a harness, not a wrapper.

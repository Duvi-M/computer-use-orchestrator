# Feature Specification: Agentic Harness

**Feature Branch**: `spec-kit/agentic-harness`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: Existing spec `specs/agentic-harness.md`

## User Scenarios & Testing

### Primary User Story

As a harness/operator engineer, I want the Computer Use orchestration layer to
control agent execution around explicit lifecycle, evidence, budgets, tool
grants, eval gates, triggers, persistence, and escalation so that Claude
Computer Use runs inside a safe, observable harness rather than as a raw API
wrapper.

### Acceptance Scenarios

1. **Given** a user creates a session, **When** the orchestrator starts a worker,
   **Then** the session lifecycle is persisted and the worker is represented as
   one isolated worker per session.
2. **Given** a user sends a goal/message, **When** the worker emits SSE events,
   **Then** the orchestrator persists messages, events, status, and artifacts.
3. **Given** a session exceeds runtime, idle, message, or event limits, **When**
   the next operation is evaluated, **Then** the harness records a quota or
   lifecycle event and denies or stops the unsafe operation.
4. **Given** evidence is missing or an eval gate fails, **When** completion is
   evaluated, **Then** the harness does not treat the task as successfully done.
5. **Given** a non-owner requests a session, stream, message, history, or UI
   route, **When** ownership is checked, **Then** access is denied as not found.

### Edge Cases

- Worker does not become ready before timeout.
- Session exceeds runtime, idle, message, or event budgets.
- noVNC access is requested by a non-owner.
- Evidence is missing or an eval gate fails.
- Orchestrator restarts while workers are active.
- Memory/eval primitives are unavailable in local mode and must fail soft.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST preserve the existing FastAPI -> WorkerLauncher ->
  Docker worker -> Claude Computer Use -> SSE/noVNC -> persistence flow.
- **FR-002**: The system MUST represent an explicit agent loop model:
  goal, plan/action, observation/evidence, eval gate, next step/escalation.
- **FR-003**: The system MUST keep one isolated worker per session.
- **FR-004**: The system MUST persist messages, events, session status, and
  artifact metadata.
- **FR-005**: The system MUST enforce ownership for session-scoped APIs.
- **FR-006**: The system MUST represent budgets for runtime, idle time,
  messages, events, and placeholders for token/cost limits.
- **FR-007**: The system MUST expose tool grants and eval gate primitives in
  the harness layer.
- **FR-008**: The system MUST expose event trigger primitives for lifecycle,
  budget, error, eval, and completion events.
- **FR-009**: The system MUST preserve current Claude Computer Use worker
  execution behavior.
- **FR-010**: The system MUST document production limitations honestly.

### Key Entities

- **Goal**: User intent with stable `goal_id`, text, and success criteria.
- **AgentLoopState**: Current loop phase, plan, actions, observations,
  evidence, and escalations.
- **Worker**: One isolated Docker worker container per session.
- **Session**: Owned execution scope tied to user and organization.
- **Event**: Persisted worker or harness event.
- **Evidence**: Artifact-backed or text-backed proof used by eval gates.
- **Budget**: Runtime/resource/message/event/cost constraint.
- **ToolGrant**: Permission model for browser, shell, file system, desktop, and
  network capabilities.
- **EvalGate**: Deterministic check for evidence/completion.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Existing session, ownership, limits, UI token, launcher,
  observability, migration, retention, and harness tests pass.
- **SC-002**: A demo operator can explain why this is a harness and not a raw
  API wrapper in under two minutes using README/docs.
- **SC-003**: Offline eval scripts run without Anthropic, Docker, or Postgres.
- **SC-004**: Harness primitives are unit-tested without changing FastAPI worker
  execution.
- **SC-005**: The local browser demo remains unchanged.

## Assumptions

- Local Docker remains the implemented worker launcher.
- SQLite remains default persistence for tests and local demo.
- PostgreSQL/Alembic remains the production database path.
- Hosted auth, object storage, remote worker launcher, billing, and Kubernetes
  remain roadmap work.

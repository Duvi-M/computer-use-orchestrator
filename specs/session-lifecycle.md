# Session Lifecycle

## Problem

Agent sessions need deterministic states so operators can reason about worker
creation, readiness, execution, cleanup, and retained history.

## Goals

- Track created, starting, ready, running, completed, failed, stopped, expired,
  deleted, and killed states.
- Persist lifecycle events.
- Stop workers on deletion, expiration, or kill.
- Hide soft-deleted sessions from normal user access.

## Non-Goals

- Automatic worker reattachment after orchestrator restart.
- Distributed queueing.
- Cross-region session migration.

## Architecture

- FastAPI route handlers enforce ownership and lifecycle checks.
- SQLite/PostgreSQL persist session status and history.
- WorkerLauncher creates, probes, stops, and cleans workers.
- Retention cleanup later prunes expired data according to policy.

## Data Flow

1. `POST /sessions` creates a session and starts a worker.
2. Worker readiness moves the session to ready.
3. `POST /sessions/{id}/messages` runs work and records messages/events.
4. Runtime and idle checks can expire the session.
5. `DELETE /sessions/{id}` marks the session deleted and stops the worker.

## Edge Cases

- Concurrent session limit reached.
- Message arrives while session is busy.
- Worker status endpoint is unavailable.
- Delete arrives after worker has already exited.
- Retention cleanup sees an already-deleted session.

## Acceptance Criteria

- Same owner can access session history.
- Different owner receives 404 for session-scoped APIs.
- Expired/deleted sessions cannot accept new messages.
- Deleting a session records a final lifecycle event.

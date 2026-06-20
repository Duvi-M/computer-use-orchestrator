# Event Triggers

## Problem

Agentic systems need internal events that can drive metrics, evals, alerts, and
future automation without coupling every route handler to every side effect.

## Goals

- Name important harness events explicitly.
- Keep trigger dispatch lightweight and testable.
- Support future handlers for notifications, evals, queues, and audit logs.
- Preserve the existing SSE event stream.

## Non-Goals

- Add Redis, Celery, Kafka, or a durable event bus.
- Replace persisted worker events.
- Add webhook delivery guarantees.

## Architecture

- `HarnessEvent` defines internal trigger names.
- `TriggerDispatcher` records emitted events and invokes local handlers.
- Existing persisted events remain the audit/history source.
- Future production code can bridge triggers to queues or alerting.

## Data Flow

1. Session lifecycle changes occur.
2. Orchestrator or eval code emits a harness trigger.
3. Registered handlers receive event name and payload.
4. Handler may record metrics, fail an eval, or request escalation.

## Edge Cases

- Handler raises an exception.
- Trigger payload is missing session metadata.
- Duplicate lifecycle events arrive.
- Trigger is emitted after a session is already terminal.

## Acceptance Criteria

- Trigger names exist for session created, worker ready, budget exceeded, idle
  timeout, agent error, eval failed, and session finished.
- Dispatcher can register handlers and record emitted events.
- Tests verify handler invocation.
- Docs clarify this is not a durable event bus yet.
